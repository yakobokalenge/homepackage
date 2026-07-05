"""Schools app - Serializers, Views, URLs, Admin."""
from rest_framework import serializers
from .models import School, Classroom


class SchoolSerializer(serializers.ModelSerializer):
    student_count = serializers.IntegerField(read_only=True, default=0)
    teacher_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = School
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')


class ClassroomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Classroom
        fields = '__all__'
        read_only_fields = ('id', 'created_at')
