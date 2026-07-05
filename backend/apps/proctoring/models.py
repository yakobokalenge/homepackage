"""Proctoring models: ProctoringConfig, ProctoringSession, ProctoringFlag."""
import uuid
from django.db import models
from django.conf import settings


class ProctoringConfigModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assessment = models.OneToOneField('assessments.Assessment', on_delete=models.CASCADE, related_name='proctoring_config')
    require_webcam = models.BooleanField(default=True)
    require_microphone = models.BooleanField(default=False)
    require_screen_share = models.BooleanField(default=False)
    browser_lockdown = models.BooleanField(default=True)
    block_copy_paste = models.BooleanField(default=True)
    block_right_click = models.BooleanField(default=True)
    face_detection = models.BooleanField(default=True)
    audio_detection = models.BooleanField(default=False)
    record_video = models.BooleanField(default=True)
    max_tab_switches = models.PositiveIntegerField(default=0)
    max_violations_before_auto_submit = models.PositiveIntegerField(default=5)
    auto_submit_on_violation = models.BooleanField(default=False)
    identity_verification = models.BooleanField(default=False)
    video_chunk_seconds = models.PositiveIntegerField(default=10)
    retention_days = models.PositiveIntegerField(default=30)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Proctoring Configuration'

    def __str__(self):
        return f"Proctor Config: {self.assessment.title}"


class ProctoringSession(models.Model):
    class Status(models.TextChoices):
        INITIALIZING = 'initializing', 'Initializing'
        ACTIVE = 'active', 'Active'
        PAUSED = 'paused', 'Paused'
        COMPLETED = 'completed', 'Completed'
        FLAGGED = 'flagged', 'Flagged for Review'
        REVIEWED = 'reviewed', 'Reviewed'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    attempt = models.OneToOneField('assessments.AssessmentAttempt', on_delete=models.CASCADE, related_name='proctoring_session')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.INITIALIZING)
    webcam_consent = models.BooleanField(default=False)
    identity_verified = models.BooleanField(default=False)
    video_s3_prefix = models.CharField(max_length=500, blank=True, default='')
    total_video_chunks = models.PositiveIntegerField(default=0)
    total_flags = models.PositiveIntegerField(default=0)
    teacher_review_notes = models.TextField(blank=True, default='')
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_sessions')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Session: {self.attempt} ({self.get_status_display()})"


class ProctoringFlag(models.Model):
    class FlagType(models.TextChoices):
        NO_FACE = 'no_face', 'No Face Detected'
        MULTIPLE_FACES = 'multiple_faces', 'Multiple Faces'
        LOOKING_AWAY = 'looking_away', 'Looking Away'
        TAB_SWITCH = 'tab_switch', 'Tab Switched'
        FULLSCREEN_EXIT = 'fullscreen_exit', 'Exited Fullscreen'
        AUDIO_DETECTED = 'audio_detected', 'Audio/Voice Detected'
        COPY_PASTE = 'copy_paste', 'Copy/Paste Attempted'
        DEV_TOOLS = 'dev_tools', 'Developer Tools'
        RIGHT_CLICK = 'right_click', 'Right Click'
        SCREENSHOT = 'screenshot', 'Screenshot Attempt'
        WINDOW_BLUR = 'window_blur', 'Window Lost Focus'
        SHORTCUT_BLOCKED = 'shortcut_blocked', 'Keyboard Shortcut'
        OTHER = 'other', 'Other'

    class Severity(models.TextChoices):
        LOW = 'low', 'Low'
        MEDIUM = 'medium', 'Medium'
        HIGH = 'high', 'High'
        CRITICAL = 'critical', 'Critical'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(ProctoringSession, on_delete=models.CASCADE, related_name='flags')
    flag_type = models.CharField(max_length=30, choices=FlagType.choices)
    severity = models.CharField(max_length=10, choices=Severity.choices, default=Severity.MEDIUM)
    description = models.TextField(blank=True, default='')
    timestamp = models.DateTimeField()
    confidence = models.FloatField(default=1.0)
    video_chunk_index = models.PositiveIntegerField(null=True, blank=True)
    is_dismissed = models.BooleanField(default=False)
    dismissed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='dismissed_flags')

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"[{self.get_severity_display()}] {self.get_flag_type_display()} at {self.timestamp}"
