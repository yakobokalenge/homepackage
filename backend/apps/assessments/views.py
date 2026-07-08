from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from .models import Assessment, AssessmentAttempt, AnswerResponse
from .serializers import (
    AssessmentSerializer, AssessmentListSerializer,
    AttemptSerializer, AttemptResultSerializer, AnswerResponseSerializer,
)


class AssessmentViewSet(viewsets.ModelViewSet):
    queryset = Assessment.objects.select_related('subject', 'created_by').prefetch_related('assessment_questions__question')
    filterset_fields = ['assessment_type', 'subject', 'classroom', 'status', 'requires_proctoring', 'is_public']
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'start_time', 'title']

    def get_serializer_class(self):
        if self.action == 'list':
            return AssessmentListSerializer
        return AssessmentSerializer

    def perform_create(self, serializer):
        user = self.request.user
        school = None
        classroom = None
        
        if user.role == 'teacher':
            from apps.schools.models import Classroom
            teacher_class = Classroom.objects.filter(class_teacher=user).first()
            if teacher_class:
                classroom = teacher_class
                school = teacher_class.school
                
        serializer.save(created_by=user, school=school, classroom=classroom)

    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        assessment = self.get_object()
        if assessment.created_by != request.user:
            return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)
        assessment.status = Assessment.Status.PUBLISHED
        assessment.save()
        return Response({'status': 'published'})

    @action(detail=True, methods=['post'], url_path='add-questions')
    def add_questions(self, request, pk=None):
        """Manually link a list of questions to this assessment."""
        assessment = self.get_object()
        question_ids = request.data.get('question_ids', [])
        if not isinstance(question_ids, list):
            return Response({'error': 'question_ids must be a list'}, status=status.HTTP_400_BAD_REQUEST)
            
        from apps.content.models import Question
        from .models import AssessmentQuestion
        
        created_count = 0
        for q_id in question_ids:
            try:
                question = Question.objects.get(id=q_id)
                obj, created = AssessmentQuestion.objects.get_or_create(
                    assessment=assessment,
                    question=question,
                    defaults={'order': assessment.assessment_questions.count() + 1}
                )
                if created:
                    created_count += 1
            except Question.DoesNotExist:
                pass
                
        return Response({'message': f'Successfully linked {created_count} questions.'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='generate-questions-ai')
    def generate_questions_ai(self, request, pk=None):
        """Generate questions using AI (OpenAI / Gemini / Claude) and associate them with this assessment."""
        assessment = self.get_object()

        from django.conf import settings as django_settings
        from apps.content.models import Question
        from apps.content.serializers import QuestionCreateSerializer
        from apps.content.ai_generators import AIQuestionGenerator, PROVIDER_LABELS
        from .models import AssessmentQuestion

        # ── Parse request data ──────────────────────────────────────
        question_types = request.data.get('question_types', [])
        if not question_types:
            single_type = request.data.get('question_type', 'mcq')
            question_types = [single_type] if not isinstance(single_type, list) else single_type

        difficulty = request.data.get('difficulty', 'medium')
        count = int(request.data.get('count', 3))
        custom_prompt = request.data.get('prompt', '')
        provider = request.data.get('provider', getattr(django_settings, 'AI_QUESTION_PROVIDER', 'auto'))

        subject = assessment.subject
        topic_name = ''
        # If a topic id was provided, resolve its name
        topic_id = request.data.get('topic')
        if topic_id:
            from apps.content.models import Topic
            try:
                topic_name = Topic.objects.get(id=topic_id).name
            except Topic.DoesNotExist:
                pass

        # ── Generate questions via AI service ───────────────────────
        generator = AIQuestionGenerator(provider=provider)
        generated = generator.generate(
            subject_name=subject.name,
            topic_name=topic_name,
            question_types=question_types,
            difficulty=difficulty,
            count=count,
            custom_prompt=custom_prompt,
        )

        # ── Save each generated question and link to assessment ─────
        created_count = 0
        for q_data in generated:
            q_data['subject'] = subject.id
            serializer = QuestionCreateSerializer(data=q_data, context={'request': request})
            if serializer.is_valid():
                question_instance = serializer.save()
                AssessmentQuestion.objects.get_or_create(
                    assessment=assessment,
                    question=question_instance,
                    defaults={'order': assessment.assessment_questions.count() + 1},
                )
                created_count += 1
            else:
                import logging
                logging.getLogger(__name__).warning(
                    'Skipped invalid AI question: %s', serializer.errors,
                )

        provider_label = PROVIDER_LABELS.get(generator.used_provider, generator.used_provider)
        return Response(
            {
                'message': f'Successfully generated and linked {created_count} questions via {provider_label} AI.',
                'provider': generator.used_provider,
                'count': created_count,
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=['post'], url_path='convert-pdf-to-questions')
    def convert_pdf_to_questions(self, request, pk=None):
        """Extract questions from uploaded PDF/Word sheet using AI and convert to interactive assessment."""
        assessment = self.get_object()
        if not assessment.is_file_based or not assessment.file_attachment:
            return Response(
                {'error': 'This assessment is not file-based or does not have an uploaded file attachment.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        import io
        import logging
        import requests
        from pypdf import PdfReader
        from django.conf import settings as django_settings
        from apps.content.ai_generators import AIQuestionGenerator, PROVIDER_LABELS
        from apps.content.serializers import QuestionCreateSerializer
        from .models import AssessmentQuestion

        logger = logging.getLogger(__name__)

        # 1. Extract text from the PDF file
        try:
            try:
                # Local storage path
                file_path = assessment.file_attachment.path
                reader = PdfReader(file_path)
            except NotImplementedError:
                # Remote storage path (e.g. Cloudinary/S3)
                file_url = assessment.file_attachment.url
                response = requests.get(file_url, timeout=30)
                response.raise_for_status()
                pdf_file = io.BytesIO(response.content)
                reader = PdfReader(pdf_file)

            pdf_text = ""
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    pdf_text += text + "\n"

            pdf_text = pdf_text.strip()
            if not pdf_text:
                return Response(
                    {'error': 'Could not extract any text from the PDF file. It might be scanned/image-only.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            logger.exception("Failed to parse PDF file: %s", e)
            return Response(
                {'error': f'Failed to process the PDF file: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 2. Call the AI service to convert extracted text into structured questions
        provider = request.data.get('provider', getattr(django_settings, 'AI_QUESTION_PROVIDER', 'auto'))
        generator = AIQuestionGenerator(provider=provider)
        
        try:
            generated = generator.convert_pdf_text(
                pdf_text=pdf_text,
                subject_name=assessment.subject.name,
            )
        except Exception as e:
            logger.exception("AI conversion failed: %s", e)
            return Response(
                {'error': f'AI conversion failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # 3. Save questions and link them to the assessment
        created_count = 0
        for q_data in generated:
            q_data['subject'] = assessment.subject.id
            serializer = QuestionCreateSerializer(data=q_data, context={'request': request})
            if serializer.is_valid():
                question_instance = serializer.save()
                AssessmentQuestion.objects.get_or_create(
                    assessment=assessment,
                    question=question_instance,
                    defaults={'order': assessment.assessment_questions.count() + 1},
                )
                created_count += 1
            else:
                logger.warning('Skipped invalid parsed question: %s', serializer.errors)

        if created_count == 0:
            return Response(
                {'error': 'Failed to extract any valid questions from the document.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 4. Turn off is_file_based so the platform displays structured questions to the student
        assessment.is_file_based = False
        assessment.save()

        provider_label = PROVIDER_LABELS.get(generator.used_provider, generator.used_provider)
        return Response(
            {
                'message': f'Successfully parsed document and created {created_count} interactive questions via {provider_label} AI.',
                'provider': generator.used_provider,
                'count': created_count,
            },
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """Student starts an exam attempt."""
        assessment = self.get_object()
        
        # If there is an active in-progress attempt, resume it
        in_progress = AssessmentAttempt.objects.filter(
            assessment=assessment, student=request.user, status='in_progress'
        ).first()
        if in_progress:
            return Response(AttemptSerializer(in_progress).data, status=status.HTTP_200_OK)

        existing = AssessmentAttempt.objects.filter(
            assessment=assessment, student=request.user
        ).count()
        if existing >= assessment.max_attempts:
            return Response({'error': 'Max attempts reached'}, status=status.HTTP_400_BAD_REQUEST)

        attempt = AssessmentAttempt.objects.create(
            assessment=assessment,
            student=request.user,
            attempt_number=existing + 1,
            ip_address=request.META.get('REMOTE_ADDR'),
        )
        return Response(AttemptSerializer(attempt).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        """Student submits their attempt."""
        assessment = self.get_object()
        try:
            attempt = AssessmentAttempt.objects.get(
                assessment=assessment, student=request.user, status=AssessmentAttempt.Status.IN_PROGRESS
            )
        except AssessmentAttempt.DoesNotExist:
            return Response({'error': 'No active attempt'}, status=status.HTTP_404_NOT_FOUND)

        # Validate and save submission file if provided (e.g., for file-based assessments)
        if request.data:
            serializer = AttemptSerializer(attempt, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()

        attempt.submitted_at = timezone.now()
        attempt.time_spent_seconds = int((attempt.submitted_at - attempt.started_at).total_seconds())
        attempt.status = AssessmentAttempt.Status.SUBMITTED
        attempt.save()

        if not assessment.is_file_based:
            attempt.auto_grade()

        return Response(AttemptResultSerializer(attempt).data)

    @action(detail=True, methods=['get'])
    def results(self, request, pk=None):
        assessment = self.get_object()
        attempts = AssessmentAttempt.objects.filter(assessment=assessment, student=request.user)
        return Response(AttemptResultSerializer(attempts, many=True).data)

    @action(detail=True, methods=['get'])
    def questions(self, request, pk=None):
        """Get ordered questions for this assessment (applying questions_limit if set)."""
        assessment = self.get_object()
        aqs = assessment.assessment_questions.select_related('question').prefetch_related('question__options').order_by('order')
        questions = [aq.question for aq in aqs]
        
        limit = assessment.questions_limit
        if limit and len(questions) > limit:
            attempt_id = request.query_params.get('attempt_id')
            if not attempt_id and request.user.is_authenticated:
                attempt = AssessmentAttempt.objects.filter(
                    assessment=assessment, student=request.user, status=AssessmentAttempt.Status.IN_PROGRESS
                ).first()
                if attempt:
                    attempt_id = str(attempt.id)
            
            if attempt_id:
                import random
                rng = random.Random(attempt_id)
                questions = rng.sample(questions, limit)
            else:
                questions = questions[:limit]

        from apps.content.serializers import QuestionSerializer
        return Response(QuestionSerializer(questions, many=True).data)


class AttemptViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AssessmentAttempt.objects.select_related('assessment', 'student').prefetch_related(
        'responses__question__options', 'responses__selected_options'
    )
    serializer_class = AttemptSerializer
    filterset_fields = ['assessment']

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return super().get_queryset().none()
        if user.role == 'teacher':
            return super().get_queryset().filter(assessment__created_by=user)
        return super().get_queryset().filter(student=user)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['hide_correct'] = False
        return context

    @action(detail=True, methods=['post'])
    def answers(self, request, pk=None):
        """Save an answer for a question within an attempt."""
        attempt = self.get_object()
        if attempt.status != AssessmentAttempt.Status.IN_PROGRESS:
            return Response({'error': 'Attempt not in progress'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = AnswerResponseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        selected = data.pop('selected_options', [])
        response, _ = AnswerResponse.objects.update_or_create(
            attempt=attempt, question=data['question'],
            defaults={k: v for k, v in data.items() if k != 'question'}
        )
        if selected:
            response.selected_options.set(selected)
        return Response(AnswerResponseSerializer(response).data)

    @action(detail=True, methods=['post'])
    def grade(self, request, pk=None):
        """Teacher manually grades a student attempt."""
        attempt = self.get_object()
        if request.user.role != 'teacher':
            return Response({'error': 'Only teachers can grade attempts.'}, status=status.HTTP_403_FORBIDDEN)

        responses_data = request.data.get('responses', [])
        earned_points = 0

        # Loop through each submitted graded response
        for r_data in responses_data:
            try:
                response = AnswerResponse.objects.get(id=r_data['response_id'], attempt=attempt)
                response.is_correct = r_data.get('is_correct', False)
                response.points_awarded = r_data.get('points_awarded', 0)
                response.teacher_feedback = r_data.get('teacher_feedback', '')
                response.save()
            except AnswerResponse.DoesNotExist:
                continue

        # Recompute totals based on all responses
        for response in attempt.responses.all():
            earned_points += response.points_awarded or 0
            
        # Get total points from assessment questions
        total_points = 0
        for aq in attempt.assessment.assessment_questions.all():
            total_points += aq.points_override or aq.question.points or 0

        attempt.score = earned_points
        attempt.percentage = (earned_points / total_points * 100) if total_points > 0 else 0
        attempt.status = AssessmentAttempt.Status.GRADED
        attempt.save()

        return Response(AttemptSerializer(attempt).data)
