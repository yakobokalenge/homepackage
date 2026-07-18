import uuid
from django.db import models
from django.conf import settings
from apps.assessments.models import Assessment, AssessmentAttempt


class ProctoringConfig(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assessment = models.OneToOneField(Assessment, on_delete=models.CASCADE, related_name='proctoring_config')
    
    require_webcam = models.BooleanField(default=True)
    require_microphone = models.BooleanField(default=True)
    require_fullscreen = models.BooleanField(default=True)
    
    block_copy_paste = models.BooleanField(default=True)
    block_right_click = models.BooleanField(default=True)
    block_devtools = models.BooleanField(default=True)
    
    require_identity_verification = models.BooleanField(default=True)
    max_tab_switches = models.PositiveIntegerField(default=0, help_text="Number of allowed tab switches before auto-submit or warning")
    allowed_urls = models.JSONField(default=list, blank=True, help_text="List of domains allowed during open-book mode")
    
    record_video = models.BooleanField(default=True)
    record_audio = models.BooleanField(default=True)
    ai_monitoring_enabled = models.BooleanField(default=True)
    
    auto_submit_on_violation_count = models.PositiveIntegerField(null=True, blank=True, help_text="Auto-submit attempt after N critical flags")
    review_period_days = models.PositiveIntegerField(default=30, help_text="Number of days to store video recordings before auto-deletion")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Proctoring Configuration'
        verbose_name_plural = 'Proctoring Configurations'

    def __str__(self):
        return f"Proctoring for: {self.assessment.title}"


class ProctoringSession(models.Model):
    class Status(models.TextChoices):
        PENDING_CONSENT = 'pending_consent', 'Pending Consent'
        ACTIVE = 'active', 'Active'
        COMPLETED = 'completed', 'Completed'
        TERMINATED = 'terminated', 'Terminated'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    attempt = models.OneToOneField(AssessmentAttempt, on_delete=models.CASCADE, related_name='proctoring_session')
    
    consent_given = models.BooleanField(default=False)
    consent_given_at = models.DateTimeField(null=True, blank=True)
    
    identity_photo = models.ImageField(upload_to='proctoring_verifications/', null=True, blank=True)
    identity_verified = models.BooleanField(default=False)
    identity_verification_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING_CONSENT)
    suspicion_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    
    # Store S3/Cloudinary URLs or local storage paths for chunk recordings
    recording_urls = models.JSONField(default=list, blank=True, help_text="List of video chunk URLs")
    
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    
    teacher_reviewed = models.BooleanField(default=False)
    teacher_review_notes = models.TextField(blank=True, default='')
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_proctor_sessions')

    class Meta:
        verbose_name = 'Proctoring Session'
        verbose_name_plural = 'Proctoring Sessions'

    def __str__(self):
        return f"Proctoring Session - Attempt: {self.attempt.id}"

    @property
    def total_violations(self):
        return self.flags.count()


class ProctoringFlag(models.Model):
    class FlagType(models.TextChoices):
        NO_FACE = 'no_face', 'No Face Detected'
        MULTIPLE_FACES = 'multiple_faces', 'Multiple Faces Detected'
        LOOKING_AWAY = 'looking_away', 'Looking Away'
        AUDIO_DETECTED = 'audio_detected', 'Suspicious Audio Detected'
        TAB_SWITCH = 'tab_switch', 'Tab Switched'
        FULLSCREEN_EXIT = 'fullscreen_exit', 'Exited Fullscreen'
        COPY_PASTE = 'copy_paste', 'Blocked Copy/Paste Attempt'
        RIGHT_CLICK = 'right_click', 'Blocked Right-Click Attempt'
        DEVTOOLS = 'devtools', 'Developer Tools Opened'
        IDENTITY_MISMATCH = 'identity_mismatch', 'Identity Verification Mismatch'
        OTHER = 'other', 'Other Violation'

    class Severity(models.TextChoices):
        LOW = 'low', 'Low'
        MEDIUM = 'medium', 'Medium'
        HIGH = 'high', 'High'
        CRITICAL = 'critical', 'Critical'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(ProctoringSession, on_delete=models.CASCADE, related_name='flags')
    flag_type = models.CharField(max_length=30, choices=FlagType.choices)
    severity = models.CharField(max_length=15, choices=Severity.choices, default=Severity.MEDIUM)
    
    timestamp = models.PositiveIntegerField(help_text="Time offset in seconds from start of exam")
    actual_time = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True, default='')
    
    screenshot = models.ImageField(upload_to='proctoring_screenshots/', null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['timestamp']
        verbose_name = 'Proctoring Flag'
        verbose_name_plural = 'Proctoring Flags'

    def __str__(self):
        return f"[{self.get_severity_display()}] {self.get_flag_type_display()} - {self.description[:40]}"
