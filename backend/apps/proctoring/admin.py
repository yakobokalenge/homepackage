from django.contrib import admin
from .models import ProctoringConfigModel, ProctoringSession, ProctoringFlag

@admin.register(ProctoringConfigModel)
class ProctoringConfigAdmin(admin.ModelAdmin):
    list_display = ('assessment', 'require_webcam', 'browser_lockdown', 'face_detection', 'record_video')

class FlagInline(admin.TabularInline):
    model = ProctoringFlag
    extra = 0
    readonly_fields = ('flag_type', 'severity', 'timestamp', 'description')

@admin.register(ProctoringSession)
class SessionAdmin(admin.ModelAdmin):
    list_display = ('attempt', 'status', 'total_flags', 'started_at', 'reviewed_by')
    list_filter = ('status',)
    inlines = [FlagInline]
