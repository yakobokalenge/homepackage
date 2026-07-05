"""
Models for schools app.
"""
import uuid
from django.db import models
from django.conf import settings


class School(models.Model):
    """School institution model."""

    class SchoolType(models.TextChoices):
        PRIMARY = 'primary', 'Primary School'
        SECONDARY = 'secondary', 'Secondary School'
        HIGH_SCHOOL = 'high_school', 'High School'
        COLLEGE = 'college', 'College'
        UNIVERSITY = 'university', 'University'

    class Ownership(models.TextChoices):
        GOVERNMENT = 'government', 'Government'
        PRIVATE = 'private', 'Private'
        RELIGIOUS = 'religious', 'Religious'
        COMMUNITY = 'community', 'Community'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    school_type = models.CharField(
        max_length=20, choices=SchoolType.choices, default=SchoolType.SECONDARY
    )
    ownership = models.CharField(
        max_length=20, choices=Ownership.choices, default=Ownership.GOVERNMENT
    )
    registration_number = models.CharField(max_length=100, unique=True, blank=True, default='')
    email = models.EmailField(blank=True, default='')
    phone = models.CharField(max_length=20, blank=True, default='')
    website = models.URLField(blank=True, default='')
    address = models.TextField(blank=True, default='')
    city = models.CharField(max_length=100, blank=True, default='')
    district = models.CharField(max_length=100, blank=True, default='')
    ward = models.CharField(max_length=100, blank=True, default='')
    region = models.CharField(max_length=100, blank=True, default='')
    country = models.CharField(max_length=100, default='Tanzania')
    logo = models.ImageField(upload_to='school_logos/', null=True, blank=True)
    admin = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='administered_schools'
    )
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'School'
        verbose_name_plural = 'Schools'
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['region']),
            models.Index(fields=['school_type']),
        ]

    def __str__(self):
        return self.name


class Classroom(models.Model):
    """Classroom within a school."""

    class Stream(models.TextChoices):
        A = 'A', 'Stream A'
        B = 'B', 'Stream B'
        C = 'C', 'Stream C'
        D = 'D', 'Stream D'
        NONE = 'none', 'No Stream'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.ForeignKey(
        School, on_delete=models.CASCADE, related_name='classrooms'
    )
    name = models.CharField(max_length=100)
    grade_level = models.CharField(max_length=50)
    stream = models.CharField(
        max_length=10, choices=Stream.choices, default=Stream.NONE
    )
    academic_year = models.CharField(max_length=20, default='2026')
    class_teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='managed_classrooms'
    )
    max_students = models.PositiveIntegerField(default=45)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['school', 'grade_level', 'stream']
        unique_together = ['school', 'name', 'academic_year']
        verbose_name = 'Classroom'
        verbose_name_plural = 'Classrooms'

    def __str__(self):
        return f"{self.school.name} - {self.name}"

    @property
    def student_count(self):
        return self.students.count()
