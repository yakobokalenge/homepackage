"""
Admin configuration for accounts app.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User, StudentProfile, TeacherProfile


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'phone', 'first_name', 'last_name', 'role', 'is_active', 'is_verified')
    list_filter = ('role', 'is_active', 'is_verified', 'auth_provider', 'date_joined')
    search_fields = ('email', 'phone', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    fieldsets = (
        (None, {'fields': ('email', 'phone', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'avatar')}),
        ('Permissions', {'fields': ('role', 'auth_provider', 'is_active', 'is_staff', 'is_superuser', 'is_verified')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
        ('Groups', {'fields': ('groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'phone', 'first_name', 'last_name', 'role', 'password1', 'password2'),
        }),
    )


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'school', 'education_level', 'grade')
    list_filter = ('education_level',)
    search_fields = ('user__email', 'user__first_name', 'user__last_name')


@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'school', 'qualification', 'is_approved')
    list_filter = ('qualification', 'is_approved')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
