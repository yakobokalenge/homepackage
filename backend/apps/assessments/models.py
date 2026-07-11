import uuid
from django.db import models
from django.conf import settings


class Assessment(models.Model):
    class AssessmentType(models.TextChoices):
        QUIZ = 'quiz', 'Quiz'
        TEST = 'test', 'Test'
        ASSIGNMENT = 'assignment', 'Assignment'
        EXAM = 'exam', 'Examination'
        HOME_PACKAGE = 'home_package', 'Home Package'

    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        PUBLISHED = 'published', 'Published'
        CLOSED = 'closed', 'Closed'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=300)
    description = models.TextField(blank=True, default='')
    assessment_type = models.CharField(max_length=20, choices=AssessmentType.choices)
    subject = models.ForeignKey('content.Subject', on_delete=models.CASCADE, related_name='assessments')
    classroom = models.ForeignKey('schools.Classroom', on_delete=models.SET_NULL, null=True, blank=True, related_name='assessments')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_assessments')
    school = models.ForeignKey('schools.School', on_delete=models.SET_NULL, null=True, blank=True, related_name='assessments')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    duration_minutes = models.PositiveIntegerField(null=True, blank=True)
    total_points = models.DecimalField(max_digits=7, decimal_places=2, default=0.00)
    pass_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=50.00)
    questions_limit = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.get_assessment_type_display()})"


class AssessmentQuestion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='assessment_questions')
    question = models.ForeignKey('content.Question', on_delete=models.CASCADE, related_name='assessment_links')
    order = models.PositiveIntegerField(default=0)
    points_override = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    class Meta:
        ordering = ['order']
        unique_together = ['assessment', 'question']

    def __str__(self):
        return f"Q{self.order}: {self.question}"


class AssessmentAttempt(models.Model):
    class Status(models.TextChoices):
        IN_PROGRESS = 'in_progress', 'In Progress'
        SUBMITTED = 'submitted', 'Submitted'
        GRADED = 'graded', 'Graded'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='attempts')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='assessment_attempts')
    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    score = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.IN_PROGRESS)

    class Meta:
        ordering = ['-started_at']

    def __str__(self):
        return f"{self.student} - {self.assessment.title}"


class AnswerResponse(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    attempt = models.ForeignKey(AssessmentAttempt, on_delete=models.CASCADE, related_name='responses')
    question = models.ForeignKey('content.Question', on_delete=models.CASCADE, related_name='responses')
    selected_option = models.ForeignKey('content.QuestionOption', on_delete=models.SET_NULL, null=True, blank=True)
    answer_text = models.TextField(blank=True, default='')
    points_awarded = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    is_correct = models.BooleanField(default=False)
    teacher_feedback = models.TextField(blank=True, default='')

    def __str__(self):
        return f"Response to Q: {self.question.text[:20]} by {self.attempt.student}"
