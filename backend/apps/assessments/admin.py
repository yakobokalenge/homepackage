from django.contrib import admin
from .models import Assessment, AssessmentQuestion, AssessmentAttempt, AnswerResponse


class AssessmentQuestionInline(admin.TabularInline):
    model = AssessmentQuestion
    extra = 1


@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = ('title', 'assessment_type', 'status', 'subject', 'classroom', 'is_proctored', 'created_at')
    list_filter = ('assessment_type', 'status', 'is_proctored', 'subject', 'classroom')
    search_fields = ('title', 'description')
    inlines = [AssessmentQuestionInline]


@admin.register(AssessmentAttempt)
class AssessmentAttemptAdmin(admin.ModelAdmin):
    list_display = ('student', 'assessment', 'status', 'score', 'percentage', 'started_at', 'submitted_at')
    list_filter = ('status', 'assessment__subject', 'assessment__assessment_type')
    search_fields = ('student__first_name', 'student__last_name', 'student__email', 'assessment__title')


@admin.register(AnswerResponse)
class AnswerResponseAdmin(admin.ModelAdmin):
    list_display = ('attempt', 'question', 'is_correct', 'points_awarded', 'auto_graded', 'answered_at')
    list_filter = ('is_correct', 'auto_graded')
    search_fields = ('attempt__student__first_name', 'attempt__student__last_name', 'question__text')
