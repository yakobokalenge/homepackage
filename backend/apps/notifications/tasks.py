"""Celery tasks for sending notifications via SMS and Email."""
import logging
from celery import shared_task
from django.conf import settings

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def send_sms_notification(self, phone_number, message):
    """Send SMS via Africa's Talking."""
    try:
        import africastalking
        africastalking.initialize(settings.AFRICASTALKING_USERNAME, settings.AFRICASTALKING_API_KEY)
        sms = africastalking.SMS
        response = sms.send(message, [phone_number])
        logger.info(f"SMS sent to {phone_number}: {response}")
        return response
    except Exception as exc:
        logger.error(f"SMS failed to {phone_number}: {exc}")
        self.retry(exc=exc, countdown=60)


@shared_task(bind=True, max_retries=3)
def send_email_notification(self, to_email, subject, body):
    """Send email via Django email backend."""
    try:
        from django.core.mail import send_mail
        send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [to_email])
        logger.info(f"Email sent to {to_email}")
    except Exception as exc:
        logger.error(f"Email failed to {to_email}: {exc}")
        self.retry(exc=exc, countdown=60)
