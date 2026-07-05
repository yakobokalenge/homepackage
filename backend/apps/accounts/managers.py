"""
Custom user manager for HomePackage.
"""
from django.contrib.auth.models import BaseUserManager


class UserManager(BaseUserManager):
    """Custom manager for User model supporting email/phone authentication."""

    def _create_user(self, email=None, phone=None, password=None, **extra_fields):
        """Create and save a user with the given email/phone and password."""
        if not email and not phone:
            raise ValueError('Users must have either an email or phone number.')

        if email:
            email = self.normalize_email(email)

        user = self.model(email=email, phone=phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email=None, phone=None, password=None, **extra_fields):
        """Create a regular user."""
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, phone, password, **extra_fields)

    def create_superuser(self, email=None, phone=None, password=None, **extra_fields):
        """Create a superuser."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_verified', True)
        extra_fields.setdefault('role', 'super_admin')

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, phone, password, **extra_fields)

    def get_by_natural_key(self, username):
        """Allow login with either email or phone."""
        try:
            return self.get(email=username)
        except self.model.DoesNotExist:
            return self.get(phone=username)
