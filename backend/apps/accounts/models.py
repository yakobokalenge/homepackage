"""
Custom User model and profiles for HomePackage.
"""
import uuid
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone

from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    """Custom user model using email/phone for authentication with UUID pk."""

    class Role(models.TextChoices):
        STUDENT = 'student', 'Student'
        TEACHER = 'teacher', 'Teacher'
        SCHOOL_ADMIN = 'school_admin', 'School Administrator'
        SUPER_ADMIN = 'super_admin', 'Super Administrator'

    class AuthProvider(models.TextChoices):
        EMAIL = 'email', 'Email'
        PHONE = 'phone', 'Phone'
        GOOGLE = 'google', 'Google'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, null=True, blank=True)
    phone = models.CharField(max_length=20, unique=True, null=True, blank=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.STUDENT)
    auth_provider = models.CharField(
        max_length=20, choices=AuthProvider.choices, default=AuthProvider.EMAIL
    )
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        ordering = ['-date_joined']
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['phone']),
            models.Index(fields=['role']),
        ]

    def __str__(self):
        return f"{self.full_name} ({self.email or self.phone})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def is_student(self):
        return self.role == self.Role.STUDENT

    @property
    def is_teacher(self):
        return self.role == self.Role.TEACHER

    @property
    def is_school_admin(self):
        return self.role == self.Role.SCHOOL_ADMIN

    @property
    def is_super_admin(self):
        return self.role == self.Role.SUPER_ADMIN


class StudentProfile(models.Model):
    """Extended profile for students."""

    class EducationLevel(models.TextChoices):
        PRIMARY = 'primary', 'Primary'
        SECONDARY_O = 'secondary_o', 'O-Level Secondary'
        SECONDARY_A = 'secondary_a', 'A-Level Secondary'
        COLLEGE = 'college', 'College'
        UNIVERSITY = 'university', 'University'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='student_profile'
    )
    school = models.ForeignKey(
        'schools.School', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='students'
    )
    classroom = models.ForeignKey(
        'schools.Classroom', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='students'
    )
    education_level = models.CharField(
        max_length=20, choices=EducationLevel.choices, default=EducationLevel.SECONDARY_O
    )
    grade = models.CharField(max_length=20, blank=True, default='')
    date_of_birth = models.DateField(null=True, blank=True)
    parent_phone = models.CharField(max_length=20, blank=True, default='')
    parent_email = models.EmailField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['user__first_name']
        verbose_name = 'Student Profile'
        verbose_name_plural = 'Student Profiles'

    def __str__(self):
        return f"Student: {self.user.full_name}"


class TeacherProfile(models.Model):
    """Extended profile for teachers."""

    class Qualification(models.TextChoices):
        DIPLOMA = 'diploma', 'Diploma'
        BACHELOR = 'bachelor', 'Bachelor Degree'
        MASTER = 'master', 'Master Degree'
        PHD = 'phd', 'PhD'
        OTHER = 'other', 'Other'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='teacher_profile'
    )
    school = models.ForeignKey(
        'schools.School', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='teachers'
    )
    employee_id = models.CharField(max_length=50, blank=True, default='')
    qualification = models.CharField(
        max_length=20, choices=Qualification.choices, default=Qualification.BACHELOR
    )
    specialization = models.CharField(max_length=200, blank=True, default='')
    years_of_experience = models.PositiveIntegerField(default=0)
    bio = models.TextField(blank=True, default='')
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['user__first_name']
        verbose_name = 'Teacher Profile'
        verbose_name_plural = 'Teacher Profiles'

    def __str__(self):
        return f"Teacher: {self.user.full_name}"


class SchoolAdminProfile(models.Model):
    """Extended profile for school admins."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='school_admin_profile'
    )
    school = models.ForeignKey(
        'schools.School', on_delete=models.CASCADE, related_name='school_admins'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'School Admin Profile'
        verbose_name_plural = 'School Admin Profiles'

    def __str__(self):
        return f"School Admin: {self.user.full_name} ({self.school.name})"
