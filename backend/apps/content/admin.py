from django.contrib import admin
from .models import Subject, Topic, Question, QuestionOption, QuestionBank


class QuestionOptionInline(admin.TabularInline):
    model = QuestionOption
    extra = 4


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'education_level', 'is_active')
    list_filter = ('education_level', 'is_active')


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ('name', 'subject', 'order')
    list_filter = ('subject',)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text_short', 'question_type', 'subject', 'difficulty', 'created_by', 'is_public')
    list_filter = ('question_type', 'difficulty', 'subject', 'is_public')
    search_fields = ('text',)
    inlines = [QuestionOptionInline]

    def text_short(self, obj):
        return obj.text[:80]
    text_short.short_description = 'Question'


@admin.register(QuestionBank)
class QuestionBankAdmin(admin.ModelAdmin):
    list_display = ('name', 'subject', 'created_by', 'is_public')
    filter_horizontal = ('questions',)
