import random
from django.utils import timezone
from django.db import transaction
from django.db.models import Count
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.assessments.models import Assessment, AssessmentAttempt
from .models import ProctoringConfig, ProctoringSession, ProctoringFlag
from .serializers import (
    ProctoringConfigSerializer, ProctoringSessionSerializer,
    ProctoringSessionListSerializer, ProctoringFlagSerializer,
    ProctoringFlagReportSerializer
)


class ProctoringViewSet(viewsets.ModelViewSet):
    queryset = ProctoringSession.objects.select_related('attempt__student', 'attempt__assessment').prefetch_related('flags')
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ProctoringSessionListSerializer
        return ProctoringSessionSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.role == 'student':
            qs = qs.filter(attempt__student=user)
        return qs

    @action(detail=False, methods=['get', 'post'], url_path='config/(?P<assessment_id>[^/.]+)')
    def config(self, request, assessment_id=None):
        """Get or update proctoring configuration for an assessment."""
        try:
            assessment = Assessment.objects.get(id=assessment_id)
        except Assessment.DoesNotExist:
            return Response({'error': 'Assessment not found.'}, status=status.HTTP_404_NOT_FOUND)

        if request.method == 'GET':
            config, _ = ProctoringConfig.objects.get_or_create(assessment=assessment)
            return Response(ProctoringConfigSerializer(config).data)
        
        else:  # POST
            if request.user.role == 'student':
                return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
            config, _ = ProctoringConfig.objects.get_or_create(assessment=assessment)
            serializer = ProctoringConfigSerializer(config, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def give_consent(self, request):
        """Student grants proctoring consent for an attempt, activating proctoring session."""
        attempt_id = request.data.get('attempt')
        if not attempt_id:
            return Response({'error': 'Attempt ID is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            attempt = AssessmentAttempt.objects.get(id=attempt_id, student=request.user)
        except AssessmentAttempt.DoesNotExist:
            return Response({'error': 'Assessment attempt not found.'}, status=status.HTTP_404_NOT_FOUND)

        if attempt.status != AssessmentAttempt.Status.IN_PROGRESS:
            return Response({'error': 'Attempt is not in progress.'}, status=status.HTTP_400_BAD_REQUEST)

        session, created = ProctoringSession.objects.get_or_create(attempt=attempt)
        session.consent_given = True
        session.consent_given_at = timezone.now()
        session.status = ProctoringSession.Status.ACTIVE
        session.save()

        return Response(ProctoringSessionSerializer(session).data)

    @action(detail=True, methods=['post'])
    def verify_identity(self, request, pk=None):
        """Upload front-facing photo to verify student identity."""
        session = self.get_object()
        if session.attempt.student != request.user:
            return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)

        photo = request.FILES.get('photo')
        if not photo:
            return Response({'error': 'Photo is required.'}, status=status.HTTP_400_BAD_REQUEST)

        session.identity_photo = photo
        session.identity_verified = True
        # Simulate facial verification score match (e.g. 88.00% to 99.00%)
        session.identity_verification_score = round(random.uniform(88.0, 99.5), 2)
        session.save()

        return Response(ProctoringSessionSerializer(session).data)

    @action(detail=True, methods=['post'])
    def report_flag(self, request, pk=None):
        """Report a proctoring violation flag from the client."""
        session = self.get_object()
        
        # Verify student or automated client reporting
        if session.attempt.student != request.user and request.user.role != 'teacher' and not request.user.is_staff:
            return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)

        serializer = ProctoringFlagReportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        with transaction.atomic():
            flag = serializer.save(session=session)
            
            # Recalculate suspicion score based on type and severity of all flags
            # LOW = +5, MEDIUM = +15, HIGH = +30, CRITICAL = +50
            score = 0.00
            for f in session.flags.all():
                if f.severity == ProctoringFlag.Severity.LOW:
                    score += 5
                elif f.severity == ProctoringFlag.Severity.MEDIUM:
                    score += 15
                elif f.severity == ProctoringFlag.Severity.HIGH:
                    score += 30
                elif f.severity == ProctoringFlag.Severity.CRITICAL:
                    score += 50
            
            session.suspicion_score = min(score, 100.00)
            session.save()
            
            # Check config to see if auto-submission is required on violation count
            config = getattr(session.attempt.assessment, 'proctoring_config', None)
            if config and config.auto_submit_on_violation_count:
                critical_flags_count = session.flags.filter(severity=ProctoringFlag.Severity.CRITICAL).count()
                if critical_flags_count >= config.auto_submit_on_violation_count:
                    # Auto-terminate and submit
                    attempt = session.attempt
                    attempt.status = AssessmentAttempt.Status.SUBMITTED
                    attempt.submitted_at = timezone.now()
                    attempt.feedback = "Attempt automatically submitted due to excessive proctoring violations."
                    attempt.save()
                    
                    session.status = ProctoringSession.Status.TERMINATED
                    session.ended_at = timezone.now()
                    session.save()
                    
                    return Response({
                        'message': 'Attempt automatically terminated due to proctoring policy.',
                        'terminated': True,
                        'session': ProctoringSessionSerializer(session).data
                    })

        return Response(ProctoringSessionSerializer(session).data)

    @action(detail=True, methods=['post'])
    def upload_chunk(self, request, pk=None):
        """Upload a video/audio recording chunk."""
        session = self.get_object()
        if session.attempt.student != request.user:
            return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)

        chunk = request.FILES.get('chunk')
        if not chunk:
            return Response({'error': 'Recording chunk is required.'}, status=status.HTTP_400_BAD_REQUEST)

        # Standard file saving logic using storage
        from django.core.files.storage import default_storage
        filename = f"proctoring_recordings/{session.id}/{uuid.uuid4()}.webm"
        path = default_storage.save(filename, chunk)
        url = default_storage.url(path)
        
        # Append to URLs
        urls = list(session.recording_urls)
        urls.append(url)
        session.recording_urls = urls
        session.save()

        return Response({
            'message': 'Chunk uploaded successfully.',
            'chunk_url': url,
            'total_chunks': len(urls)
        })

    @action(detail=True, methods=['post'])
    def review(self, request, pk=None):
        """Teacher reviews proctoring session and logs approval/notes."""
        session = self.get_object()
        if request.user.role == 'student':
            return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)

        notes = request.data.get('notes', '')
        session.teacher_reviewed = True
        session.teacher_review_notes = notes
        session.reviewed_by = request.user
        session.save()

        return Response(ProctoringSessionSerializer(session).data)
