from django.contrib import admin
from .models import School, Classroom


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ('name', 'school_type', 'region', 'district', 'is_active')
    list_filter = ('school_type', 'region', 'is_active')
    search_fields = ('name', 'registration_number')


@admin.register(Classroom)
class ClassroomAdmin(admin.ModelAdmin):
    list_display = ('name', 'school', 'grade_level', 'academic_year')
    list_filter = ('grade_level', 'academic_year')
