from rest_framework import serializers
from apps.accounts.serializers import UserSerializer
from apps.assessments.serializers import AttemptListSerializer
from .models import ProctoringConfig, ProctoringSession, ProctoringFlag


class ProctoringConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProctoringConfig
        fields = '__all__'
        read_only_fields = ('id', 'assessment', 'created_at', 'updated_at')


class ProctoringFlagSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProctoringFlag
        fields = '__all__'
        read_only_fields = ('id', 'session', 'actual_time')


class ProctoringSessionSerializer(serializers.ModelSerializer):
    flags = ProctoringFlagSerializer(many=True, read_only=True)
    student = UserSerializer(source='attempt.student', read_only=True)
    assessment_title = serializers.CharField(source='attempt.assessment.title', read_only=True)
    attempt_details = AttemptListSerializer(source='attempt', read_only=True)
    total_violations = serializers.IntegerField(read_only=True)

    class Meta:
        model = ProctoringSession
        fields = '__all__'
        read_only_fields = ('id', 'attempt', 'started_at', 'ended_at')


class ProctoringSessionListSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='attempt.student.full_name', read_only=True)
    assessment_title = serializers.CharField(source='attempt.assessment.title', read_only=True)
    total_violations = serializers.IntegerField(read_only=True)

    class Meta:
        model = ProctoringSession
        fields = (
            'id', 'attempt', 'consent_given', 'consent_given_at', 'identity_verified',
            'status', 'suspicion_score', 'total_violations', 'started_at', 'ended_at',
            'student_name', 'assessment_title', 'teacher_reviewed'
        )


class ProctoringFlagReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProctoringFlag
        fields = ('flag_type', 'severity', 'timestamp', 'description', 'screenshot', 'metadata')
