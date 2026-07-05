import uuid
from django.db import models
from django.conf import settings


class Notification(models.Model):
    class Channel(models.TextChoices):
        IN_APP = 'in_app', 'In-App'
        EMAIL = 'email', 'Email'
        SMS = 'sms', 'SMS'

    class NotificationType(models.TextChoices):
        ASSESSMENT_PUBLISHED = 'assessment_published', 'Assessment Published'
        ASSESSMENT_GRADED = 'assessment_graded', 'Assessment Graded'
        SUBSCRIPTION_RENEWED = 'subscription_renewed', 'Subscription Renewed'
        SUBSCRIPTION_EXPIRING = 'subscription_expiring', 'Subscription Expiring'
        PAYMENT_RECEIVED = 'payment_received', 'Payment Received'
        SYSTEM = 'system', 'System'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=30, choices=NotificationType.choices, default=NotificationType.SYSTEM)
    channel = models.CharField(max_length=10, choices=Channel.choices, default=Channel.IN_APP)
    is_read = models.BooleanField(default=False)
    action_url = models.CharField(max_length=500, blank=True, default='')
    metadata = models.JSONField(default=dict, blank=True)
    sent_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-sent_at']

    def __str__(self):
        return f"{self.title} → {self.user}"
