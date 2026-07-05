"""
Serializers for accounts app.
"""
from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User, StudentProfile, TeacherProfile


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)
    school = serializers.UUIDField(required=False, write_only=True, allow_null=True)
    classroom = serializers.UUIDField(required=False, write_only=True, allow_null=True)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'phone', 'first_name', 'last_name',
            'role', 'password', 'password_confirm',
            'school', 'classroom',
        ]
        read_only_fields = ['id']

    def validate(self, attrs):
        if 'email' in attrs and attrs['email'] == '':
            attrs['email'] = None
        if 'phone' in attrs and attrs['phone'] == '':
            attrs['phone'] = None

        if attrs['password'] != attrs.pop('password_confirm'):
            raise serializers.ValidationError({
                'password_confirm': 'Passwords do not match.'
            })
        if not attrs.get('email') and not attrs.get('phone'):
            raise serializers.ValidationError(
                'Either email or phone number is required.'
            )
        return attrs

    def validate_email(self, value):
        if value == '':
            return None
        if value and User.objects.filter(email=value).exists():
            raise serializers.ValidationError('A user with this email already exists.')
        return value

    def validate_phone(self, value):
        if value == '':
            return None
        if value and User.objects.filter(phone=value).exists():
            raise serializers.ValidationError('A user with this phone already exists.')
        return value

    def create(self, validated_data):
        school_id = validated_data.pop('school', None)
        classroom_id = validated_data.pop('classroom', None)
        
        user = User.objects.create_user(**validated_data)
        
        if user.role == User.Role.STUDENT:
            profile, _ = StudentProfile.objects.get_or_create(user=user)
            if school_id:
                profile.school_id = school_id
            if classroom_id:
                profile.classroom_id = classroom_id
            profile.save()
        elif user.role == User.Role.TEACHER:
            profile, _ = TeacherProfile.objects.get_or_create(user=user)
            if school_id:
                profile.school_id = school_id
            profile.save()
            
            if classroom_id:
                from apps.schools.models import Classroom
                Classroom.objects.filter(id=classroom_id).update(class_teacher=user)
        elif user.role == User.Role.SCHOOL_ADMIN:
            from apps.accounts.models import SchoolAdminProfile
            if school_id:
                SchoolAdminProfile.objects.get_or_create(user=user, school_id=school_id)
            
        return user


class UserLoginSerializer(serializers.Serializer):
    """Serializer for user login via email or phone."""
    identifier = serializers.CharField(required=False, help_text='Email or phone number')
    email = serializers.CharField(required=False)
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        identifier = attrs.get('identifier') or attrs.get('email')
        password = attrs.get('password')

        if not identifier:
            raise serializers.ValidationError('Email or phone number is required.')

        # Try to find user by email or phone
        user = None
        try:
            if '@' in identifier:
                user = User.objects.get(email=identifier)
            else:
                user = User.objects.get(phone=identifier)
        except User.DoesNotExist:
            raise serializers.ValidationError('Invalid credentials.')

        if not user.check_password(password):
            raise serializers.ValidationError('Invalid credentials.')

        if not user.is_active:
            raise serializers.ValidationError('This account has been deactivated.')

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        attrs['user'] = user
        attrs['tokens'] = {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
        return attrs


class GoogleAuthSerializer(serializers.Serializer):
    """Serializer for Google OAuth authentication."""
    token = serializers.CharField(help_text='Google OAuth2 ID token')

    def validate_token(self, value):
        from google.oauth2 import id_token as google_id_token
        from google.auth.transport import requests as google_requests
        from django.conf import settings

        try:
            idinfo = google_id_token.verify_oauth2_token(
                value,
                google_requests.Request(),
                settings.GOOGLE_CLIENT_ID
            )
            if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                raise serializers.ValidationError('Invalid token issuer.')
            return idinfo
        except Exception:
            raise serializers.ValidationError('Invalid Google token.')


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user details."""
    full_name = serializers.ReadOnlyField()
    school_id = serializers.SerializerMethodField()
    school_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'email', 'phone', 'first_name', 'last_name',
            'full_name', 'role', 'auth_provider', 'avatar',
            'is_active', 'is_verified', 'date_joined', 'last_login',
            'school_id', 'school_name'
        ]
        read_only_fields = [
            'id', 'role', 'auth_provider', 'is_active',
            'is_verified', 'date_joined', 'last_login',
        ]

    def get_school_id(self, obj):
        if hasattr(obj, 'student_profile') and obj.student_profile.school:
            return obj.student_profile.school.id
        if hasattr(obj, 'teacher_profile') and obj.teacher_profile.school:
            return obj.teacher_profile.school.id
        if hasattr(obj, 'school_admin_profile') and obj.school_admin_profile.school:
            return obj.school_admin_profile.school.id
        return None

    def get_school_name(self, obj):
        if hasattr(obj, 'student_profile') and obj.student_profile.school:
            return obj.student_profile.school.name
        if hasattr(obj, 'teacher_profile') and obj.teacher_profile.school:
            return obj.teacher_profile.school.name
        if hasattr(obj, 'school_admin_profile') and obj.school_admin_profile.school:
            return obj.school_admin_profile.school.name
        return None


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile."""

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'avatar', 'phone']

    def validate_phone(self, value):
        if value and User.objects.filter(phone=value).exclude(pk=self.instance.pk).exists():
            raise serializers.ValidationError('This phone number is already in use.')
        return value


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for changing password."""
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=8)
    new_password_confirm = serializers.CharField(required=True, min_length=8)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                'new_password_confirm': 'New passwords do not match.'
            })
        return attrs

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Current password is incorrect.')
        return value


class StudentProfileSerializer(serializers.ModelSerializer):
    """Serializer for student profile."""
    user = UserSerializer(read_only=True)

    class Meta:
        model = StudentProfile
        fields = [
            'id', 'user', 'school', 'classroom', 'education_level',
            'grade', 'date_of_birth', 'parent_phone', 'parent_email',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class StudentProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating student profile."""

    class Meta:
        model = StudentProfile
        fields = [
            'school', 'classroom', 'education_level', 'grade',
            'date_of_birth', 'parent_phone', 'parent_email',
        ]


class TeacherProfileSerializer(serializers.ModelSerializer):
    """Serializer for teacher profile."""
    user = UserSerializer(read_only=True)

    class Meta:
        model = TeacherProfile
        fields = [
            'id', 'user', 'school', 'employee_id', 'qualification',
            'specialization', 'years_of_experience', 'bio',
            'is_approved', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'is_approved', 'created_at', 'updated_at']


class TeacherProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating teacher profile."""

    class Meta:
        model = TeacherProfile
        fields = [
            'school', 'employee_id', 'qualification',
            'specialization', 'years_of_experience', 'bio',
        ]
