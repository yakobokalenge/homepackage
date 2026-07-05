"""
Signals for accounts app.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from .models import StudentProfile, TeacherProfile

User = get_user_model()


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Auto-create profile based on user role when a new user is created."""
    if created:
        if instance.role == User.Role.STUDENT:
            StudentProfile.objects.get_or_create(user=instance)
        elif instance.role == User.Role.TEACHER:
            TeacherProfile.objects.get_or_create(user=instance)
