import uuid
from django.db import models
from django.conf import settings
from apps.content.models import Subject, Question
from apps.schools.models import Classroom


class Assessment(models.Model):
    class AssessmentType(models.TextChoices):
        QUIZ = 'quiz', 'Quiz'
        TEST = 'test', 'Test'
        ASSIGNMENT = 'assignment', 'Assignment'
        EXAM = 'exam', 'Exam'
        HOME_PACKAGE = 'home_package', 'Home Package'

    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        PUBLISHED = 'published', 'Published'
        ACTIVE = 'active', 'Active'
        CLOSED = 'closed', 'Closed'
        ARCHIVED = 'archived', 'Archived'

    class Difficulty(models.TextChoices):
        EASY = 'easy', 'Easy'
        MEDIUM = 'medium', 'Medium'
        HARD = 'hard', 'Hard'
        MIXED = 'mixed', 'Mixed'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='assessments')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='assessments')
    classroom = models.ForeignKey(Classroom, on_delete=models.SET_NULL, null=True, blank=True, related_name='assessments')
    
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    instructions = models.TextField(blank=True, default='')
    
    assessment_type = models.CharField(max_length=20, choices=AssessmentType.choices, default=AssessmentType.QUIZ)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    difficulty = models.CharField(max_length=10, choices=Difficulty.choices, default=Difficulty.MEDIUM)
    
    time_limit_minutes = models.PositiveIntegerField(null=True, blank=True, help_text='Null means no limit')
    max_attempts = models.PositiveIntegerField(default=1)
    passing_score = models.DecimalField(max_digits=5, decimal_places=2, default=50.00)
    
    shuffle_questions = models.BooleanField(default=False)
    shuffle_options = models.BooleanField(default=False)
    show_results_immediately = models.BooleanField(default=True)
    show_correct_answers = models.BooleanField(default=True)
    
    is_proctored = models.BooleanField(default=False)
    allow_late_submission = models.BooleanField(default=False)
    
    start_datetime = models.DateTimeField(null=True, blank=True)
    end_datetime = models.DateTimeField(null=True, blank=True)
    
    attachments = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['subject']),
            models.Index(fields=['classroom']),
            models.Index(fields=['status']),
            models.Index(fields=['assessment_type']),
        ]

    def __str__(self):
        return f"{self.title} ({self.get_assessment_type_display()})"

    @property
    def question_count(self):
        return self.assessment_questions.count()

    @property
    def total_points(self):
        # Sum overrides if present, otherwise sum the base question points
        total = 0
        for aq in self.assessment_questions.all():
            if aq.points_override is not None:
                total += aq.points_override
            else:
                total += aq.question.points
        return total


class AssessmentQuestion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='assessment_questions')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='assessment_links')
    order = models.PositiveIntegerField(default=0)
    points_override = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    is_required = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']
        unique_together = ('assessment', 'question')

    def __str__(self):
        return f"{self.assessment.title} - Question {self.order}"


class AssessmentAttempt(models.Model):
    class Status(models.TextChoices):
        NOT_STARTED = 'not_started', 'Not Started'
        IN_PROGRESS = 'in_progress', 'In Progress'
        SUBMITTED = 'submitted', 'Submitted'
        GRADED = 'graded', 'Graded'
        TIMED_OUT = 'timed_out', 'Timed Out'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='attempts')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='assessment_attempts')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NOT_STARTED)
    
    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    graded_at = models.DateTimeField(null=True, blank=True)
    
    score = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    time_spent_seconds = models.PositiveIntegerField(default=0)
    attempt_number = models.PositiveIntegerField(default=1)
    
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, default='')
    is_late = models.BooleanField(default=False)
    
    graded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='graded_attempts')
    feedback = models.TextField(blank=True, default='')

    class Meta:
        ordering = ['-started_at']
        unique_together = ('assessment', 'student', 'attempt_number')

    def __str__(self):
        return f"{self.student.full_name} - {self.assessment.title} (Attempt {self.attempt_number})"


class AnswerResponse(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    attempt = models.ForeignKey(AssessmentAttempt, on_delete=models.CASCADE, related_name='responses')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    
    # Store dynamic answers depending on question type
    selected_options = models.JSONField(default=list, blank=True, help_text='IDs of chosen QuestionOptions')
    text_answer = models.TextField(blank=True, default='', help_text='For essay, short answer, fill in blanks')
    matching_pairs = models.JSONField(default=dict, blank=True, help_text='Matches for matching type {"option_id": "match_pair"}')
    ordering_sequence = models.JSONField(default=list, blank=True, help_text='Ordered option IDs')
    file_attachment = models.FileField(upload_to='student_submissions/', null=True, blank=True)
    
    is_correct = models.BooleanField(null=True, blank=True)
    points_awarded = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    teacher_feedback = models.TextField(blank=True, default='')
    auto_graded = models.BooleanField(default=False)
    answered_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['question__assessment_links__order']
        unique_together = ('attempt', 'question')

    def __str__(self):
        return f"Response for {self.question} in Attempt {self.attempt.id}"


class StagedQuestion(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending Review'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'
        EDITED = 'edited', 'Edited'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assessment = models.ForeignKey(Assessment, on_delete=models.SET_NULL, null=True, blank=True, related_name='staged_questions')
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    
    # Question content (mirrors Question fields)
    text = models.TextField()
    question_type = models.CharField(max_length=20)
    difficulty = models.CharField(max_length=10, default='medium')
    explanation = models.TextField(blank=True, default='')
    points = models.DecimalField(max_digits=5, decimal_places=2, default=5.00)
    options = models.JSONField(default=list)  # [{text, is_correct, order, match_pair}]
    media = models.JSONField(default=list)
    metadata = models.JSONField(default=dict, blank=True)  # {page_num, source_file, etc.}
    
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    source_file = models.CharField(max_length=500, blank=True, default='')
    extraction_provider = models.CharField(max_length=50, blank=True, default='')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Staged ({self.status}) - {self.text[:50]}"


class ExtractionJob(models.Model):
    class Status(models.TextChoices):
        QUEUED = 'queued', 'Queued'
        PROCESSING = 'processing', 'Processing'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='extraction_jobs', null=True, blank=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    
    original_file = models.FileField(upload_to='extraction_uploads/')
    file_name = models.CharField(max_length=500)
    file_type = models.CharField(max_length=20)  # pdf, docx, csv, xlsx
    
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.QUEUED)
    progress = models.PositiveIntegerField(default=0)  # 0-100
    error_message = models.TextField(blank=True, default='')
    extraction_provider = models.CharField(max_length=50, blank=True, default='')
    questions_extracted = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Job {self.file_name} - {self.status}"

