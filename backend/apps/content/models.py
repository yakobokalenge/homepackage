"""Content models: Subject, Topic, Question (8 types), QuestionOption, QuestionBank."""
import uuid
from django.db import models
from django.conf import settings


class Subject(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    name_sw = models.CharField(max_length=100, blank=True, default='')
    code = models.CharField(max_length=10, unique=True)
    education_level = models.CharField(max_length=30, blank=True, default='')
    icon = models.URLField(blank=True, default='')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.code})"


class Topic(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='topics')
    name = models.CharField(max_length=200)
    name_sw = models.CharField(max_length=200, blank=True, default='')
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return f"{self.subject.code} - {self.name}"


class Question(models.Model):
    class QuestionType(models.TextChoices):
        MCQ = 'mcq', 'Multiple Choice'
        MULTI_SELECT = 'multi_select', 'Multiple Select'
        TRUE_FALSE = 'true_false', 'True/False'
        FILL_BLANK = 'fill_blank', 'Fill in the Blank'
        SHORT_ANSWER = 'short_answer', 'Short Answer'
        ESSAY = 'essay', 'Essay'
        MATCHING = 'matching', 'Matching'
        ORDERING = 'ordering', 'Ordering'

    class Difficulty(models.TextChoices):
        EASY = 'easy', 'Easy'
        MEDIUM = 'medium', 'Medium'
        HARD = 'hard', 'Hard'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='questions')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='questions')
    topic = models.ForeignKey(Topic, on_delete=models.SET_NULL, null=True, blank=True, related_name='questions')
    question_type = models.CharField(max_length=20, choices=QuestionType.choices)
    difficulty = models.CharField(max_length=10, choices=Difficulty.choices, default=Difficulty.MEDIUM)
    text = models.TextField(help_text='Supports HTML and LaTeX')
    text_sw = models.TextField(blank=True, default='', help_text='Kiswahili version')
    explanation = models.TextField(blank=True, default='')
    points = models.DecimalField(max_digits=5, decimal_places=2, default=1.00)
    time_limit_seconds = models.PositiveIntegerField(null=True, blank=True)
    media = models.JSONField(default=list, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    is_public = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)
    class_level = models.CharField(max_length=50, blank=True, default='')
    subtopic = models.CharField(max_length=200, blank=True, default='')
    curriculum = models.CharField(max_length=100, blank=True, default='Tanzania NECTA')
    language = models.CharField(max_length=50, blank=True, default='English')
    status = models.CharField(
        max_length=20,
        choices=[
            ('draft', 'Draft'),
            ('pending', 'Pending Review'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected')
        ],
        default='pending'
    )
    author_name = models.CharField(max_length=100, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['subject', 'question_type']),
            models.Index(fields=['created_by']),
        ]

    def __str__(self):
        return f"[{self.get_question_type_display()}] {self.text[:80]}"


class QuestionOption(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='options')
    text = models.TextField()
    is_correct = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    match_pair = models.CharField(max_length=200, blank=True, default='')

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{'✓' if self.is_correct else '✗'} {self.text[:50]}"


class QuestionBank(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, default='')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='question_banks')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='question_banks')
    questions = models.ManyToManyField(Question, related_name='banks', blank=True)
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return self.name


class QuestionUsage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.OneToOneField(Question, on_delete=models.CASCADE, related_name='usage_stats')
    used_count = models.PositiveIntegerField(default=0, help_text='Number of assessments this question is featured in')
    attempts_count = models.PositiveIntegerField(default=0, help_text='Total student answers for this question')
    correct_count = models.PositiveIntegerField(default=0, help_text='Number of correct answers')
    average_time_seconds = models.FloatField(default=0.0)
    difficulty_index = models.FloatField(default=0.0, help_text='Correct Rate (0.0 to 1.0)')
    discrimination_index = models.FloatField(default=0.0, help_text='Discrimination index')
    
    def __str__(self):
        return f"Stats for {self.question_id}"


def recalculate_question_stats(question_ids):
    """Recalculates performance metrics for specific questions based on graded student attempts."""
    from apps.content.models import QuestionUsage
    from apps.assessments.models import AnswerResponse, AssessmentQuestion
    
    for q_id in question_ids:
        usage, _ = QuestionUsage.objects.get_or_create(question_id=q_id)
        
        # 1. Used count
        usage.used_count = AssessmentQuestion.objects.filter(question_id=q_id).count()
        
        # 2. Student response statistics
        responses = AnswerResponse.objects.filter(question_id=q_id, attempt__status='graded')
        usage.attempts_count = responses.count()
        
        if usage.attempts_count > 0:
            usage.correct_count = responses.filter(is_correct=True).count()
            usage.difficulty_index = round(usage.correct_count / usage.attempts_count, 2)
            usage.average_time_seconds = 45.0 # baseline average mock
            
            # Discrimination Index: Correct rate of upper scorers vs lower scorers
            attempts = list(responses.select_related('attempt'))
            attempts.sort(key=lambda x: x.attempt.percentage or 0, reverse=True)
            mid = len(attempts) // 2
            if mid > 0:
                top_group = attempts[:mid]
                bottom_group = attempts[mid:]
                top_correct = sum(1 for r in top_group if r.is_correct)
                bottom_correct = sum(1 for r in bottom_group if r.is_correct)
                top_rate = top_correct / len(top_group)
                bottom_rate = bottom_correct / len(bottom_group)
                usage.discrimination_index = round(top_rate - bottom_rate, 2)
            else:
                usage.discrimination_index = 0.0
        else:
            usage.correct_count = 0
            usage.difficulty_index = 0.0
            usage.discrimination_index = 0.0
            
        usage.save()
