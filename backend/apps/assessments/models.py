"""Assessment models: Assessment, AssessmentQuestion, AssessmentAttempt, AnswerResponse."""
import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone


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
        ACTIVE = 'active', 'Active'
        CLOSED = 'closed', 'Closed'
        ARCHIVED = 'archived', 'Archived'

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
    total_points = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    pass_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=50.00)
    show_results_immediately = models.BooleanField(default=True)
    allow_review = models.BooleanField(default=True)
    is_public = models.BooleanField(default=False)
    access_code = models.CharField(max_length=20, blank=True, default='')
    shuffle_questions = models.BooleanField(default=False)
    shuffle_options = models.BooleanField(default=False)
    max_attempts = models.PositiveIntegerField(default=1)
    questions_limit = models.PositiveIntegerField(null=True, blank=True, help_text='Number of questions to be done by the student')
    requires_proctoring = models.BooleanField(default=False)
    file_attachment = models.FileField(upload_to='assessments/', null=True, blank=True)
    is_file_based = models.BooleanField(default=False)
    week_number = models.PositiveIntegerField(null=True, blank=True)
    month = models.CharField(max_length=20, blank=True, default='')
    academic_year = models.CharField(max_length=10, blank=True, default='')
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
        TIMED_OUT = 'timed_out', 'Timed Out'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='attempts')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='assessment_attempts')
    attempt_number = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.IN_PROGRESS)
    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    score = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    time_spent_seconds = models.PositiveIntegerField(default=0)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    submission_file = models.FileField(upload_to='submissions/', null=True, blank=True)

    class Meta:
        ordering = ['-started_at']

    def __str__(self):
        return f"{self.student} - {self.assessment.title} (Attempt {self.attempt_number})"

    def auto_grade(self):
        """Auto-grade MCQ, true/false, multi-select questions."""
        total = 0
        earned = 0
        for response in self.responses.select_related('question').prefetch_related('question__options'):
            q = response.question
            pts = response.assessment_question_points or q.points
            total += pts
            if q.question_type in ('mcq', 'true_false', 'multi_select', 'fill_blank'):
                correct_ids = set(q.options.filter(is_correct=True).values_list('id', flat=True))
                selected_ids = set(response.selected_options.values_list('id', flat=True))
                if q.question_type == 'fill_blank':
                    correct_texts = [o.text.strip().lower() for o in q.options.filter(is_correct=True)]
                    if response.answer_text.strip().lower() in correct_texts:
                        response.is_correct = True
                        response.points_awarded = pts
                        earned += pts
                    else:
                        response.is_correct = False
                        response.points_awarded = 0
                elif correct_ids == selected_ids:
                    response.is_correct = True
                    response.points_awarded = pts
                    earned += pts
                else:
                    response.is_correct = False
                    response.points_awarded = 0
                response.save()
        self.score = earned
        self.percentage = (earned / total * 100) if total > 0 else 0
        self.status = self.Status.GRADED
        self.submitted_at = timezone.now()
        self.save()


class AnswerResponse(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    attempt = models.ForeignKey(AssessmentAttempt, on_delete=models.CASCADE, related_name='responses')
    question = models.ForeignKey('content.Question', on_delete=models.CASCADE, related_name='responses')
    answer_text = models.TextField(blank=True, default='')
    selected_options = models.ManyToManyField('content.QuestionOption', blank=True, related_name='responses')
    answer_data = models.JSONField(default=dict, blank=True)
    is_correct = models.BooleanField(null=True)
    points_awarded = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    teacher_feedback = models.TextField(blank=True, default='')
    answered_at = models.DateTimeField(auto_now=True)
    time_spent_seconds = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ['attempt', 'question']

    def __str__(self):
        return f"Response: {self.question} by {self.attempt.student}"

    @property
    def assessment_question_points(self):
        try:
            aq = AssessmentQuestion.objects.get(assessment=self.attempt.assessment, question=self.question)
            return aq.points_override or self.question.points
        except AssessmentQuestion.DoesNotExist:
            return self.question.points
