from django.contrib import admin
from .models import ProctoringConfig, ProctoringSession, ProctoringFlag


class ProctoringFlagInline(admin.TabularInline):
    model = ProctoringFlag
    extra = 1


@admin.register(ProctoringConfig)
class ProctoringConfigAdmin(admin.ModelAdmin):
    list_display = ('assessment', 'require_webcam', 'require_microphone', 'require_fullscreen', 'block_copy_paste', 'max_tab_switches')
    list_filter = ('require_webcam', 'require_microphone', 'require_fullscreen')
    search_fields = ('assessment__title',)


@admin.register(ProctoringSession)
class ProctoringSessionAdmin(admin.ModelAdmin):
    list_display = ('attempt', 'consent_given', 'identity_verified', 'status', 'suspicion_score', 'teacher_reviewed')
    list_filter = ('consent_given', 'identity_verified', 'status', 'teacher_reviewed')
    search_fields = ('attempt__student__first_name', 'attempt__student__last_name', 'attempt__student__email')
    inlines = [ProctoringFlagInline]


@admin.register(ProctoringFlag)
class ProctoringFlagAdmin(admin.ModelAdmin):
    list_display = ('session', 'flag_type', 'severity', 'timestamp', 'actual_time')
    list_filter = ('flag_type', 'severity')
    search_fields = ('session__attempt__student__first_name', 'session__attempt__student__last_name', 'description')
