import logging
import traceback
from django.utils import timezone
from django.conf import settings
from celery import shared_task
from apps.assessments.models import ExtractionJob, StagedQuestion
from apps.content.document_extractor import DocumentExtractor
from apps.content.ai_generators import AIQuestionGenerator

logger = logging.getLogger(__name__)

@shared_task
def process_extraction_job_task(job_id):
    """
    Celery task to run document extraction in the background.
    Parses PDF, Word, CSV, or Excel files, runs them through the AI parser,
    and inserts questions into the StagedQuestion table.
    """
    try:
        job = ExtractionJob.objects.get(id=job_id)
    except ExtractionJob.DoesNotExist:
        logger.error(f"Extraction job {job_id} not found.")
        return

    try:
        # 1. Update job status to Processing
        job.status = ExtractionJob.Status.PROCESSING
        job.progress = 10
        job.save()

        # Read file bytes from storage
        file_field = job.original_file
        with file_field.open('rb') as f:
            file_bytes = f.read()

        extractor = DocumentExtractor()
        extracted_questions = []
        provider_used = 'local'

        # 2. Extract raw text/images/tables based on file type
        file_ext = job.file_type.lower()
        job.progress = 30
        job.save()

        if file_ext == 'pdf':
            pages = extractor.extract_pdf(file_bytes)
            job.progress = 50
            job.save()
            
            # Combine pages text with image markers for AI parser
            full_text = ""
            for page in pages:
                # Add page separator marker
                full_text += f"\n\n[Page {page['page_num']} Illustrations: "
                if page['images']:
                    full_text += ", ".join([f"Image: {img}" for img in page['images']])
                full_text += "]\n"
                full_text += page['text']

            # Call AI parser
            generator = AIQuestionGenerator(provider=settings.AI_QUESTION_PROVIDER)
            extracted_questions = generator.convert_pdf_text(
                pdf_text=full_text,
                subject_name=job.subject.name
            )
            provider_used = generator.used_provider

        elif file_ext in ('docx', 'doc'):
            pages = extractor.extract_docx(file_bytes)
            job.progress = 50
            job.save()

            full_text = ""
            for page in pages:
                full_text += f"\n\n[Page {page['page_num']} Illustrations: "
                if page['images']:
                    full_text += ", ".join([f"Image: {img}" for img in page['images']])
                full_text += "]\n"
                full_text += page['text']

            # Call AI parser
            generator = AIQuestionGenerator(provider=settings.AI_QUESTION_PROVIDER)
            extracted_questions = generator.convert_pdf_text(
                pdf_text=full_text,
                subject_name=job.subject.name
            )
            provider_used = generator.used_provider

        elif file_ext in ('csv', 'xlsx', 'xls'):
            is_excel = file_ext != 'csv'
            extracted_questions = extractor.extract_csv_or_excel(file_bytes, is_excel=is_excel)
            provider_used = 'spreadsheet_parser'

        else:
            raise ValueError(f"Unsupported file extension: {file_ext}")

        job.progress = 80
        job.save()

        # 3. Save extracted questions in StagedQuestion table
        staged_instances = []
        for q_data in extracted_questions:
            # Clean options matches
            options = q_data.get('options', [])
            
            meta = q_data.get('metadata', {})
            if not isinstance(meta, dict):
                meta = {}
            meta['job_id'] = str(job.id)
            meta['subject_id'] = str(job.subject.id)
            
            staged_inst = StagedQuestion(
                assessment=job.assessment,
                uploaded_by=job.uploaded_by,
                text=q_data.get('text', ''),
                question_type=q_data.get('question_type', 'mcq'),
                difficulty=q_data.get('difficulty', 'medium'),
                explanation=q_data.get('explanation', ''),
                points=q_data.get('points', 5.0),
                options=options,
                media=q_data.get('media', []),
                metadata=meta,
                status=StagedQuestion.Status.PENDING,
                source_file=job.file_name,
                extraction_provider=provider_used
            )
            staged_instances.append(staged_inst)


        if staged_instances:
            StagedQuestion.objects.bulk_create(staged_instances)

        # 4. Complete job
        job.status = ExtractionJob.Status.COMPLETED
        job.progress = 100
        job.questions_extracted = len(staged_instances)
        job.extraction_provider = provider_used
        job.completed_at = timezone.now()
        job.save()

        logger.info(f"Successfully processed extraction job {job_id}. Extracted {len(staged_instances)} staged questions.")

    except Exception as e:
        error_msg = f"Extraction failed: {str(e)}\n{traceback.format_exc()}"
        logger.error(f"Error processing extraction job {job_id}: {error_msg}")
        
        job.status = ExtractionJob.Status.FAILED
        job.error_message = str(e)
        job.progress = 100
        job.completed_at = timezone.now()
        job.save()
