from django.contrib import admin
from .models import Assessment, AssessmentQuestion, AssessmentAttempt, AnswerResponse


class AssessmentQuestionInline(admin.TabularInline):
    model = AssessmentQuestion
    extra = 1


@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = ('title', 'assessment_type', 'subject', 'status', 'created_by', 'requires_proctoring')
    list_filter = ('assessment_type', 'status', 'requires_proctoring')
    search_fields = ('title',)
    inlines = [AssessmentQuestionInline]


@admin.register(AssessmentAttempt)
class AttemptAdmin(admin.ModelAdmin):
    list_display = ('student', 'assessment', 'status', 'score', 'percentage', 'started_at')
    list_filter = ('status',)


@admin.register(AnswerResponse)
class AnswerResponseAdmin(admin.ModelAdmin):
    list_display = ('attempt', 'question', 'is_correct', 'points_awarded')
