import fitz  # PyMuPDF
import logging
from decimal import Decimal
from django.utils import timezone
from django.db import models
from django.db import transaction
from django.db.models import Avg, Max, Min, Count
from django.conf import settings
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.content.models import Subject, Topic, Question, QuestionOption
from apps.content.serializers import QuestionSerializer, QuestionCreateSerializer
from apps.content.ai_generators import AIQuestionGenerator
from .models import Assessment, AssessmentQuestion, AssessmentAttempt, AnswerResponse, StagedQuestion, ExtractionJob
from .serializers import (
    AssessmentSerializer, AssessmentListSerializer, AssessmentCreateSerializer,
    AttemptSerializer, AttemptListSerializer, AnswerResponseSerializer,
    SubmitAssessmentSerializer, GradeResponseSerializer,
    StagedQuestionSerializer, ExtractionJobSerializer
)
from .grading import grade_response

logger = logging.getLogger(__name__)



class AssessmentViewSet(viewsets.ModelViewSet):
    queryset = Assessment.objects.select_related('subject', 'classroom', 'created_by').prefetch_related('assessment_questions__question__options')
    filterset_fields = ['subject', 'classroom', 'status', 'assessment_type', 'is_proctored']
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'start_datetime']

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return AssessmentCreateSerializer
        if self.action == 'list':
            return AssessmentListSerializer
        return AssessmentSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.role == 'student':
            # Students can only see active/published assessments for their classroom (or general ones)
            classroom = getattr(user.student_profile, 'classroom', None)
            now = timezone.now()
            qs = qs.filter(
                models.Q(status=Assessment.Status.PUBLISHED) | models.Q(status=Assessment.Status.ACTIVE)
            ).filter(
                models.Q(classroom=classroom) | models.Q(classroom__isnull=True)
            )
            # Filter by scheduling window
            # If start_datetime is set, it must be in the past
            # If end_datetime is set, it must be in the future (or allow late submission)
            # For list view we show them, but in AttemptViewSet we restrict starting
        return qs

    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        assessment = self.get_object()
        if request.user.role == 'student':
            return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
        
        assessment.status = Assessment.Status.PUBLISHED
        assessment.save()
        return Response({'status': 'published', 'message': 'Assessment published successfully.'})

    @action(detail=True, methods=['post'])
    def close(self, request, pk=None):
        assessment = self.get_object()
        if request.user.role == 'student':
            return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
        
        assessment.status = Assessment.Status.CLOSED
        assessment.save()
        return Response({'status': 'closed', 'message': 'Assessment closed successfully.'})

    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        assessment = self.get_object()
        if request.user.role == 'student':
            return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
        
        with transaction.atomic():
            new_assessment = Assessment.objects.create(
                created_by=request.user,
                subject=assessment.subject,
                classroom=assessment.classroom,
                title=f"{assessment.title} (Copy)",
                description=assessment.description,
                instructions=assessment.instructions,
                assessment_type=assessment.assessment_type,
                status=Assessment.Status.DRAFT,
                difficulty=assessment.difficulty,
                time_limit_minutes=assessment.time_limit_minutes,
                max_attempts=assessment.max_attempts,
                passing_score=assessment.passing_score,
                shuffle_questions=assessment.shuffle_questions,
                shuffle_options=assessment.shuffle_options,
                show_results_immediately=assessment.show_results_immediately,
                show_correct_answers=assessment.show_correct_answers,
                is_proctored=assessment.is_proctored,
                allow_late_submission=assessment.allow_late_submission,
                start_datetime=assessment.start_datetime,
                end_datetime=assessment.end_datetime,
                attachments=assessment.attachments
            )
            
            # Copy questions
            for aq in assessment.assessment_questions.all():
                AssessmentQuestion.objects.create(
                    assessment=new_assessment,
                    question=aq.question,
                    order=aq.order,
                    points_override=aq.points_override,
                    is_required=aq.is_required
                )
        
        return Response(AssessmentSerializer(new_assessment).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def generate_ai(self, request, pk=None):
        """Generate questions using AI and add to this assessment."""
        assessment = self.get_object()
        if request.user.role == 'student':
            return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)

        topic_id = request.data.get('topic')
        question_types = request.data.get('question_types', ['mcq'])
        difficulty = request.data.get('difficulty', 'medium')
        count = int(request.data.get('count', 5))
        custom_prompt = request.data.get('prompt', '')

        topic = None
        if topic_id:
            import uuid
            # Check if topic_id is a valid UUID
            is_uuid = False
            try:
                uuid.UUID(str(topic_id))
                is_uuid = True
            except ValueError:
                is_uuid = False

            try:
                if is_uuid:
                    topic = Topic.objects.get(id=topic_id)
                else:
                    topic = Topic.objects.filter(name__icontains=topic_id).first()
            except (Topic.DoesNotExist, ValueError):
                pass
            
            if not topic and is_uuid:
                return Response({'error': 'Topic not found.'}, status=status.HTTP_404_NOT_FOUND)

        provider = request.data.get('provider', settings.AI_QUESTION_PROVIDER)
        generator = AIQuestionGenerator(provider=provider)

        # Extract grade level and assessment type for AI tailoring
        grade_level = assessment.classroom.grade_level if (assessment.classroom and assessment.classroom.grade_level) else "Form Two"
        assessment_type = assessment.get_assessment_type_display() if hasattr(assessment, 'get_assessment_type_display') else assessment.assessment_type

        questions_data = generator.generate(
            subject_name=assessment.subject.name,
            topic_name=topic.name if topic else '',
            question_types=question_types,
            difficulty=difficulty,
            count=count,
            custom_prompt=custom_prompt,
            grade_level=grade_level,
            assessment_type=assessment_type
        )

        saved_questions = []
        with transaction.atomic():
            start_order = assessment.assessment_questions.count()
            for idx, q_data in enumerate(questions_data):
                q_data['subject'] = assessment.subject.id
                q_data['topic'] = topic.id if topic else None
                q_data['is_public'] = False
                q_data['is_approved'] = False
                q_data['status'] = 'pending'
                
                # Save question
                serializer = QuestionCreateSerializer(data=q_data, context={'request': request})
                serializer.is_valid(raise_exception=True)
                question = serializer.save()
                saved_questions.append(question)
                
                # Link to assessment
                AssessmentQuestion.objects.create(
                    assessment=assessment,
                    question=question,
                    order=start_order + idx,
                    points_override=Decimal(str(q_data.get('points', 5.0))),
                    is_required=True
                )

        return Response({
            'message': f'Successfully generated and linked {len(saved_questions)} questions via {generator.used_provider}.',
            'questions': QuestionSerializer(saved_questions, many=True).data
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'])
    def extract_document(self, request):
        """Extract questions from an uploaded document (PDF/Word/CSV/Excel) and stage them."""
        if request.user.role == 'student':
            return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)

        uploaded_file = request.FILES.get('file')
        subject_id = request.data.get('subject')
        
        if not uploaded_file:
            return Response({'error': 'File is required.'}, status=status.HTTP_400_BAD_REQUEST)
        if not subject_id:
            return Response({'error': 'Subject ID is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            subject = Subject.objects.get(id=subject_id)
        except Subject.DoesNotExist:
            return Response({'error': 'Subject not found.'}, status=status.HTTP_404_NOT_FOUND)

        file_name = uploaded_file.name
        file_ext = file_name.split('.')[-1].lower() if '.' in file_name else ''
        if file_ext not in ('pdf', 'docx', 'doc', 'csv', 'xlsx', 'xls'):
            return Response({'error': f'Unsupported file format: .{file_ext}'}, status=status.HTTP_400_BAD_REQUEST)

        # Create ExtractionJob in status QUEUED
        job = ExtractionJob.objects.create(
            uploaded_by=request.user,
            subject=subject,
            original_file=uploaded_file,
            file_name=file_name,
            file_type=file_ext,
            status=ExtractionJob.Status.QUEUED,
            progress=0
        )

        # Dispatch Celery task with inline fallback if Redis/Celery is down
        from .tasks import process_extraction_job_task
        async_success = False
        try:
            process_extraction_job_task.delay(job.id)
            async_success = True
        except Exception as e:
            logger.warning(f"Failed to dispatch celery task async: {e}. Running sync.")
            async_success = False

        if not async_success:
            try:
                process_extraction_job_task(job.id)
            except Exception as e:
                logger.exception("Synchronous document parsing failed.")
                return Response({'error': f'Parsing failed: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

        # Re-fetch job
        job.refresh_from_db()
        return Response(ExtractionJobSerializer(job).data, status=status.HTTP_202_ACCEPTED)


    @action(detail=True, methods=['post'])
    def save_extracted(self, request, pk=None):
        """Save a list of previewed/modified extracted questions to this assessment."""
        assessment = self.get_object()
        if request.user.role == 'student':
            return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)

        questions_list = request.data.get('questions', [])
        if not questions_list:
            return Response({'error': 'No questions provided.'}, status=status.HTTP_400_BAD_REQUEST)

        saved_questions = []
        with transaction.atomic():
            start_order = assessment.assessment_questions.count()
            for idx, q_data in enumerate(questions_list):
                q_data['subject'] = assessment.subject.id
                q_data['is_public'] = False
                q_data['is_approved'] = True
                
                # Create question
                serializer = QuestionCreateSerializer(data=q_data, context={'request': request})
                serializer.is_valid(raise_exception=True)
                question = serializer.save()
                saved_questions.append(question)
                
                # Link to assessment
                AssessmentQuestion.objects.create(
                    assessment=assessment,
                    question=question,
                    order=start_order + idx,
                    points_override=Decimal(str(q_data.get('points', 5.0))),
                    is_required=True
                )

        return Response({
            'message': f'Successfully saved {len(saved_questions)} questions to the assessment.',
            'count': len(saved_questions)
        })

    @action(detail=True, methods=['get'])
    def results(self, request, pk=None):
        """Class results overview for teachers."""
        assessment = self.get_object()
        if request.user.role == 'student':
            return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)

        attempts = assessment.attempts.filter(status__in=[AssessmentAttempt.Status.SUBMITTED, AssessmentAttempt.Status.GRADED])
        
        agg = attempts.aggregate(
            avg_score=Avg('score'),
            max_score=Max('score'),
            min_score=Min('score'),
            avg_percentage=Avg('percentage'),
            total_submissions=Count('id')
        )
        
        # Calculate grade distribution
        passing_score = assessment.passing_score
        passed_count = attempts.filter(percentage__gte=passing_score).count()
        failed_count = attempts.filter(percentage__lt=passing_score).count()
        
        by_student = []
        for att in attempts.select_related('student'):
            by_student.append({
                'attempt_id': att.id,
                'student_id': att.student.id,
                'student_name': att.student.full_name,
                'submitted_at': att.submitted_at,
                'score': att.score,
                'percentage': att.percentage,
                'status': att.status,
                'time_spent_seconds': att.time_spent_seconds,
                'is_late': att.is_late
            })

        return Response({
            'summary': {
                'avg_score': agg['avg_score'] or 0,
                'max_score': agg['max_score'] or 0,
                'min_score': agg['min_score'] or 0,
                'avg_percentage': agg['avg_percentage'] or 0,
                'total_submissions': agg['total_submissions'] or 0,
                'passed': passed_count,
                'failed': failed_count
            },
            'results': by_student
        })


class AttemptViewSet(viewsets.ModelViewSet):
    queryset = AssessmentAttempt.objects.select_related('assessment', 'student').prefetch_related('responses__question')
    
    def get_serializer_class(self):
        if self.action == 'list':
            return AttemptListSerializer
        return AttemptSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.role == 'student':
            qs = qs.filter(student=user)
        return qs

    @action(detail=False, methods=['post'])
    def start(self, request):
        """Begin an assessment attempt."""
        assessment_id = request.data.get('assessment')
        if not assessment_id:
            return Response({'error': 'Assessment ID is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            assessment = Assessment.objects.get(id=assessment_id)
        except Assessment.DoesNotExist:
            return Response({'error': 'Assessment not found.'}, status=status.HTTP_404_NOT_FOUND)

        student = request.user
        if student.role != 'student':
            return Response({'error': 'Only students can start attempts.'}, status=status.HTTP_403_FORBIDDEN)

        # Verify scheduling window
        now = timezone.now()
        if assessment.start_datetime and now < assessment.start_datetime:
            return Response({'error': 'This assessment has not started yet.'}, status=status.HTTP_400_BAD_REQUEST)
        if assessment.end_datetime and now > assessment.end_datetime and not assessment.allow_late_submission:
            return Response({'error': 'This assessment window is closed.'}, status=status.HTTP_400_BAD_REQUEST)

        # Verify maximum attempts
        existing_attempts = AssessmentAttempt.objects.filter(assessment=assessment, student=student)
        attempts_count = existing_attempts.count()
        if attempts_count >= assessment.max_attempts:
            return Response({'error': 'You have exceeded the maximum allowed attempts.'}, status=status.HTTP_400_BAD_REQUEST)

        # Check if there is an in-progress attempt to resume
        in_progress = existing_attempts.filter(status=AssessmentAttempt.Status.IN_PROGRESS).first()
        if in_progress:
            return Response(AttemptSerializer(in_progress).data)

        # Retrieve client IP and user agent
        ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', ''))
        if ',' in ip:
            ip = ip.split(',')[0].strip()
        ua = request.META.get('HTTP_USER_AGENT', '')

        # Create new attempt
        attempt = AssessmentAttempt.objects.create(
            assessment=assessment,
            student=student,
            status=AssessmentAttempt.Status.IN_PROGRESS,
            attempt_number=attempts_count + 1,
            ip_address=ip,
            user_agent=ua,
            is_late=assessment.end_datetime is not None and now > assessment.end_datetime
        )

        return Response(AttemptSerializer(attempt).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def save_answer(self, request, pk=None):
        """Save a single question answer response (called periodically during autosave)."""
        attempt = self.get_object()
        if attempt.status != AssessmentAttempt.Status.IN_PROGRESS:
            return Response({'error': 'Cannot save answers on an attempt that is not in progress.'}, status=status.HTTP_400_BAD_REQUEST)

        question_id = request.data.get('question_id')
        if not question_id:
            return Response({'error': 'Question ID is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Verify question is linked to this assessment
            aq = attempt.assessment.assessment_questions.get(question_id=question_id)
            question = aq.question
        except AssessmentQuestion.DoesNotExist:
            return Response({'error': 'Question is not part of this assessment.'}, status=status.HTTP_400_BAD_REQUEST)

        selected_options = request.data.get('selected_options', [])
        text_answer = request.data.get('text_answer', '')
        matching_pairs = request.data.get('matching_pairs', {})
        ordering_sequence = request.data.get('ordering_sequence', [])
        uploaded_file = request.FILES.get('file_attachment')

        response, created = AnswerResponse.objects.get_or_create(
            attempt=attempt,
            question=question
        )

        response.selected_options = selected_options
        response.text_answer = text_answer
        response.matching_pairs = matching_pairs
        response.ordering_sequence = ordering_sequence
        if uploaded_file:
            response.file_attachment = uploaded_file
        
        response.save()

        # Update elapsed time spent
        delta = timezone.now() - attempt.started_at
        attempt.time_spent_seconds = int(delta.total_seconds())
        attempt.save()

        return Response(AnswerResponseSerializer(response).data)

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        """Finalize and submit the assessment attempt. Auto-grades standard questions."""
        attempt = self.get_object()
        if attempt.status != AssessmentAttempt.Status.IN_PROGRESS:
            return Response({'error': 'This attempt has already been submitted.'}, status=status.HTTP_400_BAD_REQUEST)

        # 1. Extract answers if submitted in bulk payload
        bulk_answers = request.data.get('answers', [])
        with transaction.atomic():
            for ans in bulk_answers:
                q_id = ans.get('question_id')
                if q_id:
                    try:
                        aq = attempt.assessment.assessment_questions.get(question_id=q_id)
                        resp, _ = AnswerResponse.objects.get_or_create(attempt=attempt, question=aq.question)
                        resp.selected_options = ans.get('selected_options', [])
                        resp.text_answer = ans.get('text_answer', '')
                        resp.matching_pairs = ans.get('matching_pairs', {})
                        resp.ordering_sequence = ans.get('ordering_sequence', [])
                        resp.save()
                    except AssessmentQuestion.DoesNotExist:
                        pass

            # Update final values
            attempt.status = AssessmentAttempt.Status.SUBMITTED
            attempt.submitted_at = timezone.now()
            delta = attempt.submitted_at - attempt.started_at
            attempt.time_spent_seconds = int(delta.total_seconds())
            
            # Check for late submission
            assessment = attempt.assessment
            if assessment.end_datetime and attempt.submitted_at > assessment.end_datetime:
                attempt.is_late = True
            
            # Auto-grade eligible answers
            all_auto_graded = True
            for response in attempt.responses.all():
                # Find the points override for this question
                aq = assessment.assessment_questions.filter(question=response.question).first()
                pts_override = aq.points_override if aq else None
                
                # Call autograding logic
                is_auto = grade_response(response, points_override=pts_override)
                response.save()
                
                if not is_auto:
                    all_auto_graded = False

            # Calculate score if fully auto-graded
            if all_auto_graded:
                attempt.status = AssessmentAttempt.Status.GRADED
                attempt.graded_at = timezone.now()
                
                score = Decimal('0.00')
                total_pts = Decimal('0.00')
                for response in attempt.responses.all():
                    score += response.points_awarded
                
                total_pts = Decimal(str(assessment.total_points))
                attempt.score = score
                if total_pts > 0:
                    attempt.percentage = round((score / total_pts) * 100, 2)
                else:
                    attempt.percentage = Decimal('100.00')
            
            attempt.save()
            if attempt.status == AssessmentAttempt.Status.GRADED:
                from apps.content.models import recalculate_question_stats
                q_ids = [resp.question_id for resp in attempt.responses.all()]
                recalculate_question_stats(q_ids)

        return Response(AttemptSerializer(attempt).data)

    @action(detail=True, methods=['post'])
    def grade(self, request, pk=None):
        """Teacher manual grading endpoint for essays/short answers."""
        attempt = self.get_object()
        if request.user.role == 'student':
            return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)

        grades = request.data.get('grades', {})  # Dict mapping response_id to {points_awarded, feedback}
        
        with transaction.atomic():
            for resp_id, grade_info in grades.items():
                try:
                    resp = attempt.responses.get(id=resp_id)
                    resp.points_awarded = Decimal(str(grade_info.get('points_awarded', 0.00)))
                    resp.teacher_feedback = grade_info.get('teacher_feedback', '')
                    resp.is_correct = resp.points_awarded > 0  # Simple boolean logic
                    resp.save()
                except AnswerResponse.DoesNotExist:
                    pass

            # Recalculate attempt score
            score = Decimal('0.00')
            for resp in attempt.responses.all():
                score += resp.points_awarded
            
            total_pts = Decimal(str(attempt.assessment.total_points))
            
            attempt.score = score
            if total_pts > 0:
                attempt.percentage = round((score / total_pts) * 100, 2)
            else:
                attempt.percentage = Decimal('100.00')
                
            attempt.status = AssessmentAttempt.Status.GRADED
            attempt.graded_at = timezone.now()
            attempt.graded_by = request.user
            attempt.feedback = request.data.get('feedback', attempt.feedback)
            attempt.save()
            
            from apps.content.models import recalculate_question_stats
            q_ids = [resp.question_id for resp in attempt.responses.all()]
            recalculate_question_stats(q_ids)

        return Response(AttemptSerializer(attempt).data)


class ExtractionJobViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ExtractionJobSerializer
    queryset = ExtractionJob.objects.all()

    def get_queryset(self):
        return self.queryset.filter(uploaded_by=self.request.user)


class StagedQuestionViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = StagedQuestionSerializer
    queryset = StagedQuestion.objects.all()
    pagination_class = None

    def get_queryset(self):
        qs = self.queryset.filter(uploaded_by=self.request.user)
        assessment_id = self.request.query_params.get('assessment')
        job_id = self.request.query_params.get('job')
        if assessment_id:
            qs = qs.filter(assessment_id=assessment_id)
        if job_id:
            # metadata has string key for job_id
            qs = qs.filter(metadata__job_id=str(job_id))
        return qs

    @action(detail=False, methods=['post'])
    def confirm_staged(self, request):
        """
        Promote a list of staged questions to live Question bank, and link them to an assessment (optional).
        """
        staged_ids = request.data.get('staged_ids', [])
        assessment_id = request.data.get('assessment_id')
        
        if not staged_ids:
            return Response({'error': 'No staged question IDs provided.'}, status=status.HTTP_400_BAD_REQUEST)
        
        staged_qs = StagedQuestion.objects.filter(id__in=staged_ids, uploaded_by=request.user)
        if not staged_qs.exists():
            return Response({'error': 'No matching staged questions found.'}, status=status.HTTP_400_BAD_REQUEST)

        assessment = None
        if assessment_id:
            try:
                assessment = Assessment.objects.get(id=assessment_id)
            except Assessment.DoesNotExist:
                return Response({'error': 'Assessment not found.'}, status=status.HTTP_404_NOT_FOUND)

        saved_questions = []
        with transaction.atomic():
            start_order = assessment.assessment_questions.count() if assessment else 0
            for idx, sq in enumerate(staged_qs):
                # Determine subject
                subject = None
                if sq.assessment:
                    subject = sq.assessment.subject
                elif assessment:
                    subject = assessment.subject
                else:
                    # Retrieve from metadata
                    subj_id = sq.metadata.get('subject_id')
                    if subj_id:
                        try:
                            subject = Subject.objects.get(id=subj_id)
                        except Subject.DoesNotExist:
                            pass
                
                if not subject:
                    # Fallback to first subject in DB
                    subject = Subject.objects.first()

                # 1. Create live Question
                is_user_admin = request.user.role in ('school_admin', 'super_admin') or request.user.is_staff
                question = Question.objects.create(
                    created_by=request.user,
                    subject=subject,
                    text=sq.text,
                    question_type=sq.question_type,
                    difficulty=sq.difficulty,
                    explanation=sq.explanation,
                    points=sq.points,
                    media=sq.media,
                    metadata=sq.metadata,
                    is_public=False,
                    is_approved=is_user_admin,
                    status='approved' if is_user_admin else 'pending'
                )
                
                # 2. Create Options
                for opt in sq.options:
                    QuestionOption.objects.create(
                        question=question,
                        text=opt.get('text', ''),
                        is_correct=opt.get('is_correct', False),
                        order=opt.get('order', 1),
                        match_pair=opt.get('match_pair', '')
                    )
                
                # 3. Link to assessment if provided
                if assessment:
                    AssessmentQuestion.objects.create(
                        assessment=assessment,
                        question=question,
                        order=start_order + idx,
                        points_override=sq.points,
                        is_required=True
                    )
                
                # 4. Mark staged as approved
                sq.status = StagedQuestion.Status.APPROVED
                sq.save()
                
                saved_questions.append(question)

        return Response({
            'message': f'Successfully approved and created {len(saved_questions)} questions.',
            'questions': QuestionSerializer(saved_questions, many=True).data
        })

