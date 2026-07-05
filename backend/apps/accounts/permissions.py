"""
Permission classes for HomePackage.
"""
from rest_framework.permissions import BasePermission


class IsStudent(BasePermission):
    """Allow access only to students."""
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == 'student'
        )


class IsTeacher(BasePermission):
    """Allow access only to teachers."""
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == 'teacher'
        )


class IsSchoolAdmin(BasePermission):
    """Allow access only to school administrators."""
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == 'school_admin'
        )


class IsSuperAdmin(BasePermission):
    """Allow access only to super administrators."""
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == 'super_admin'
        )


class IsTeacherOrAdmin(BasePermission):
    """Allow access to teachers, school admins, and super admins."""
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in ('teacher', 'school_admin', 'super_admin')
        )


class IsOwnerOrAdmin(BasePermission):
    """Allow access to the owner of the object or admins."""
    def has_object_permission(self, request, view, obj):
        if request.user.role in ('school_admin', 'super_admin'):
            return True
        if hasattr(obj, 'user'):
            return obj.user == request.user
        return obj == request.user


class IsStudentOrTeacher(BasePermission):
    """Allow access to students and teachers."""
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in ('student', 'teacher')
        )


class IsAdminUser(BasePermission):
    """Allow access to school admins and super admins."""
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in ('school_admin', 'super_admin')
        )
