import boto3
from rest_framework import status as http_status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.conf import settings
from django.utils import timezone
from .models import ProctoringSession, ProctoringFlag
from .serializers import ProctoringSessionSerializer, ReportFlagSerializer, ProctoringConfigSerializer
from apps.assessments.models import AssessmentAttempt


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def start_session(request, attempt_id):
    """Start a proctoring session for an exam attempt."""
    try:
        attempt = AssessmentAttempt.objects.get(id=attempt_id, student=request.user)
    except AssessmentAttempt.DoesNotExist:
        return Response({'error': 'Attempt not found'}, status=http_status.HTTP_404_NOT_FOUND)

    session, created = ProctoringSession.objects.get_or_create(
        attempt=attempt,
        defaults={
            'video_s3_prefix': f"proctoring/{attempt.assessment.id}/{attempt.id}/",
            'started_at': timezone.now(),
        }
    )
    # Return proctoring config
    config = getattr(attempt.assessment, 'proctoring_config', None)
    config_data = ProctoringConfigSerializer(config).data if config else {}

    return Response({
        'session_id': str(session.id),
        'config': config_data,
        'status': session.status,
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def consent(request, session_id):
    """Record webcam consent."""
    try:
        session = ProctoringSession.objects.get(id=session_id)
    except ProctoringSession.DoesNotExist:
        return Response({'error': 'Session not found'}, status=http_status.HTTP_404_NOT_FOUND)

    session.webcam_consent = True
    session.status = ProctoringSession.Status.ACTIVE
    session.save()
    return Response({'status': 'active'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def report_flag(request, session_id):
    """Report a proctoring violation flag from the client."""
    try:
        session = ProctoringSession.objects.get(id=session_id)
    except ProctoringSession.DoesNotExist:
        return Response({'error': 'Session not found'}, status=http_status.HTTP_404_NOT_FOUND)

    serializer = ReportFlagSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    d = serializer.validated_data

    ProctoringFlag.objects.create(
        session=session,
        flag_type=d['type'],
        severity=d['severity'],
        description=d['description'],
        timestamp=d['timestamp'],
    )
    session.total_flags += 1
    if session.total_flags >= 3:
        session.status = ProctoringSession.Status.FLAGGED
    session.save()
    return Response({'total_flags': session.total_flags})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def get_upload_url(request, session_id):
    """Generate a presigned S3 URL for video chunk upload."""
    try:
        session = ProctoringSession.objects.get(id=session_id)
    except ProctoringSession.DoesNotExist:
        return Response({'error': 'Session not found'}, status=http_status.HTTP_404_NOT_FOUND)

    chunk_index = request.data.get('chunk_index', 0)
    s3_key = f"{session.video_s3_prefix}chunk_{chunk_index:04d}.webm"

    try:
        s3 = boto3.client('s3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME,
        )
        url = s3.generate_presigned_url('put_object',
            Params={'Bucket': settings.AWS_STORAGE_BUCKET_NAME, 'Key': s3_key, 'ContentType': 'video/webm'},
            ExpiresIn=settings.AWS_PRESIGNED_EXPIRY,
        )
        session.total_video_chunks = max(session.total_video_chunks, chunk_index + 1)
        session.save()
        return Response({'upload_url': url, 's3_key': s3_key})
    except Exception as e:
        return Response({'error': str(e)}, status=http_status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def review_session(request, session_id):
    """Teacher reviews a proctoring session."""
    try:
        session = ProctoringSession.objects.prefetch_related('flags').get(id=session_id)
    except ProctoringSession.DoesNotExist:
        return Response({'error': 'Session not found'}, status=http_status.HTTP_404_NOT_FOUND)

    return Response(ProctoringSessionSerializer(session).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_reviewed(request, session_id):
    """Teacher marks session as reviewed."""
    try:
        session = ProctoringSession.objects.get(id=session_id)
    except ProctoringSession.DoesNotExist:
        return Response({'error': 'Session not found'}, status=http_status.HTTP_404_NOT_FOUND)

    session.status = ProctoringSession.Status.REVIEWED
    session.reviewed_by = request.user
    session.reviewed_at = timezone.now()
    session.teacher_review_notes = request.data.get('notes', '')
    session.save()
    return Response({'status': 'reviewed'})
