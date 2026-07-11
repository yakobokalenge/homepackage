import io
import logging
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.conf import settings
from django.utils import timezone
from apps.content.models import Subject, Question, QuestionOption
from apps.content.serializers import QuestionCreateSerializer
from .models import Assessment, AssessmentQuestion, AssessmentAttempt, AnswerResponse
from .serializers import AssessmentSerializer, AssessmentAttemptSerializer, AnswerResponseSerializer

logger = logging.getLogger(__name__)


class AssessmentViewSet(viewsets.ModelViewSet):
    queryset = Assessment.objects.all()
    serializer_class = AssessmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        user = self.request.user
        school = getattr(user, 'school', None)
        serializer.save(created_by=user, school=school)

    @action(detail=False, methods=['post'], url_path='extract-document')
    def extract_document(self, request):
        """Accepts a PDF, DOCX, or TXT file upload, extracts text, runs AI parsing, and returns draft questions."""
        uploaded_file = request.FILES.get('file')
        subject_id = request.data.get('subject')

        if not uploaded_file:
            return Response({'error': 'Please upload a document file.'}, status=status.HTTP_400_BAD_REQUEST)
        if not subject_id:
            return Response({'error': 'Subject ID is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            subject = Subject.objects.get(id=subject_id)
        except Subject.DoesNotExist:
            return Response({'error': 'Subject not found.'}, status=status.HTTP_404_NOT_FOUND)

        # 1. Extract text and images from document
        import os
        import uuid
        filename = uploaded_file.name
        ext = filename.split('.')[-1].lower()
        extracted_text = ""

        try:
            if ext == 'pdf':
                from pypdf import PdfReader
                reader = PdfReader(uploaded_file)
                for page_num, page in enumerate(reader.pages):
                    page_text = page.extract_text() or ""
                    
                    # Extract images on this page
                    page_images = []
                    for img_idx, img_obj in enumerate(page.images):
                        img_name = f"extracted_pdf_{uuid.uuid4().hex}_{page_num}_{img_idx}.png"
                        img_path = os.path.join(settings.MEDIA_ROOT, 'extracted_images', img_name)
                        os.makedirs(os.path.dirname(img_path), exist_ok=True)
                        with open(img_path, "wb") as fp:
                            fp.write(img_obj.data)
                        img_url = f"{settings.MEDIA_URL}extracted_images/{img_name}"
                        page_images.append(f"Image {chr(65 + img_idx)}: {img_url}")
                    
                    if page_images:
                        img_header = f"\n[Page {page_num + 1} Illustrations: {', '.join(page_images)}]\n"
                        extracted_text += img_header + page_text + "\n"
                    else:
                        extracted_text += page_text + "\n"

            elif ext in ('doc', 'docx'):
                import docx
                doc = docx.Document(uploaded_file)
                text_blocks = []
                for p in doc.paragraphs:
                    p_text = p.text
                    for run in p.runs:
                        r_elem = run._r
                        drawings = r_elem.findall('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}drawing')
                        for drawing in drawings:
                            blips = drawing.findall('.//{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed')
                            for blip in blips:
                                r_id = blip.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed')
                                if r_id and r_id in doc.part.rels:
                                    image_part = doc.part.rels[r_id].target_part
                                    img_name = f"extracted_word_{uuid.uuid4().hex}.png"
                                    img_path = os.path.join(settings.MEDIA_ROOT, 'extracted_images', img_name)
                                    os.makedirs(os.path.dirname(img_path), exist_ok=True)
                                    with open(img_path, "wb") as fp:
                                        fp.write(image_part.blob)
                                    img_url = f"{settings.MEDIA_URL}extracted_images/{img_name}"
                                    p_text += f"\n[IMAGE: {img_url}]\n"
                    text_blocks.append(p_text)
                extracted_text = "\n".join(text_blocks)

            elif ext == 'txt':
                extracted_text = uploaded_file.read().decode('utf-8', errors='ignore')
            else:
                return Response({'error': 'Unsupported file format. Please upload PDF, Word (.docx), or TXT.'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception("Failed to parse document file")
            return Response({'error': f'Failed to process file: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

        extracted_text = extracted_text.strip()
        if not extracted_text:
            return Response({'error': 'Could not extract any readable text from the document.'}, status=status.HTTP_400_BAD_REQUEST)

        # 2. Run AI Parsing to get Question Drafts
        from apps.content.ai_generators import AIQuestionGenerator
        provider = request.data.get('provider', getattr(settings, 'AI_QUESTION_PROVIDER', 'auto'))
        generator = AIQuestionGenerator(provider=provider)

        try:
            questions_draft = generator.convert_pdf_text(
                pdf_text=extracted_text,
                subject_name=subject.name
            )
        except Exception as e:
            logger.exception("AI Extraction failed")
            return Response({'error': f'AI Extraction failed: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({
            'questions': questions_draft,
            'provider': generator.provider
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='save-extracted')
    def save_extracted(self, request, pk=None):
        """Saves validated draft questions from teacher review screen, saving them to bank and linking to assessment."""
        assessment = self.get_object()
        questions_data = request.data.get('questions', [])

        if not questions_data or not isinstance(questions_data, list):
            return Response({'error': 'A list of validated questions is required.'}, status=status.HTTP_400_BAD_REQUEST)

        created_count = 0
        total_points = 0

        # Delete existing links first to overwrite
        assessment.assessment_questions.all().delete()

        for idx, q_data in enumerate(questions_data):
            q_data['subject'] = assessment.subject.id
            serializer = QuestionCreateSerializer(data=q_data, context={'request': request})
            if serializer.is_valid():
                question_instance = serializer.save(created_by=request.user)
                
                points = float(q_data.get('points', 5.0))
                AssessmentQuestion.objects.create(
                    assessment=assessment,
                    question=question_instance,
                    order=idx + 1,
                    points_override=points
                )
                total_points += points
                created_count += 1
            else:
                logger.warning('Skipped invalid question draft: %s', serializer.errors)

        # Update total assessment points
        assessment.total_points = total_points
        assessment.save()

        return Response({
            'message': f'Successfully saved {created_count} questions to the bank and linked them to the assessment.',
            'count': created_count,
            'total_points': total_points
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """Student starts an exam attempt."""
        assessment = self.get_object()
        student = request.user

        # Fetch or create attempt
        attempt, created = AssessmentAttempt.objects.get_or_create(
            assessment=assessment,
            student=student,
            status=AssessmentAttempt.Status.IN_PROGRESS
        )

        return Response(AssessmentAttemptSerializer(attempt).data, status=status.HTTP_201_CREATED)


class AttemptViewSet(viewsets.ModelViewSet):
    queryset = AssessmentAttempt.objects.all()
    serializer_class = AssessmentAttemptSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=['post'], url_path='save-answer')
    def save_answer(self, request, pk=None):
        """Autosave endpoint called dynamically by student client on input change or blur."""
        attempt = self.get_object()
        if attempt.status != AssessmentAttempt.Status.IN_PROGRESS:
            return Response({'error': 'Cannot save answers on a submitted or graded attempt.'}, status=status.HTTP_400_BAD_REQUEST)

        question_id = request.data.get('question_id')
        selected_option_id = request.data.get('selected_option_id')
        answer_text = request.data.get('answer_text', '')

        if not question_id:
            return Response({'error': 'question_id is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            question = Question.objects.get(id=question_id)
        except Question.DoesNotExist:
            return Response({'error': 'Question not found.'}, status=status.HTTP_404_NOT_FOUND)

        selected_option = None
        if selected_option_id:
            try:
                selected_option = QuestionOption.objects.get(id=selected_option_id)
            except QuestionOption.DoesNotExist:
                pass

        # Save or update response
        response_obj, created = AnswerResponse.objects.update_or_create(
            attempt=attempt,
            question=question,
            defaults={
                'selected_option': selected_option,
                'answer_text': answer_text
            }
        )

        return Response({
            'status': 'saved',
            'response_id': response_obj.id
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        """Finalizes exam attempt, auto-grades standard types, and redirects to results."""
        attempt = self.get_object()
        if attempt.status != AssessmentAttempt.Status.IN_PROGRESS:
            return Response({'error': 'This attempt has already been submitted.'}, status=status.HTTP_400_BAD_REQUEST)

        attempt.status = AssessmentAttempt.Status.SUBMITTED
        attempt.submitted_at = timezone.now()

        # Auto-grade standard questions (MCQ, True/False)
        total_points = 0.0
        score_obtained = 0.0

        links = attempt.assessment.assessment_questions.all()
        for link in links:
            q = link.question
            points = float(link.points_override or 5.0)
            total_points += points

            try:
                response = AnswerResponse.objects.get(attempt=attempt, question=q)
            except AnswerResponse.DoesNotExist:
                # No answer entered by student
                continue

            # Auto grade MCQs and True/False
            if q.question_type in ('mcq', 'true_false'):
                if response.selected_option and response.selected_option.is_correct:
                    response.is_correct = True
                    response.points_awarded = points
                    score_obtained += points
                else:
                    response.is_correct = False
                    response.points_awarded = 0.0
                response.save()

        attempt.score = score_obtained
        attempt.percentage = (score_obtained / total_points * 100) if total_points > 0 else 0.0
        attempt.status = AssessmentAttempt.Status.GRADED  # Mark as graded if all MCQs, otherwise we still auto-score MCQ elements
        attempt.save()

        return Response(AssessmentAttemptSerializer(attempt).data, status=status.HTTP_200_OK)
