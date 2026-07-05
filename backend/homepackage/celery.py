"""
Celery application configuration for HomePackage.
"""
import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'homepackage.settings.development')

app = Celery('homepackage')

# Load config from Django settings, using CELERY_ namespace
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in all installed apps
app.autodiscover_tasks()

# Celery Beat schedule
app.conf.beat_schedule = {
    'cleanup-expired-proctoring-sessions': {
        'task': 'apps.proctoring.tasks.cleanup_expired_sessions',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
        'options': {'queue': 'maintenance'},
    },
    'check-subscription-expiry': {
        'task': 'apps.subscriptions.tasks.check_subscription_expiry',
        'schedule': crontab(hour=0, minute=0),  # Daily at midnight
        'options': {'queue': 'maintenance'},
    },
    'send-subscription-expiry-reminders': {
        'task': 'apps.subscriptions.tasks.send_expiry_reminders',
        'schedule': crontab(hour=9, minute=0),  # Daily at 9 AM
        'options': {'queue': 'notifications'},
    },
    'cleanup-old-notifications': {
        'task': 'apps.notifications.tasks.cleanup_old_notifications',
        'schedule': crontab(hour=3, minute=0, day_of_week=0),  # Weekly on Sunday at 3 AM
        'options': {'queue': 'maintenance'},
    },
    'auto-grade-overdue-assessments': {
        'task': 'apps.assessments.tasks.auto_grade_overdue_attempts',
        'schedule': crontab(minute='*/30'),  # Every 30 minutes
        'options': {'queue': 'grading'},
    },
}


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task to verify Celery is working."""
    print(f'Request: {self.request!r}')
