from rest_framework import serializers
from .models import ProctoringConfigModel, ProctoringSession, ProctoringFlag

class ProctoringConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProctoringConfigModel
        fields = '__all__'

class ProctoringFlagSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProctoringFlag
        fields = '__all__'
        read_only_fields = ('id',)

class ProctoringSessionSerializer(serializers.ModelSerializer):
    flags = ProctoringFlagSerializer(many=True, read_only=True)
    class Meta:
        model = ProctoringSession
        fields = '__all__'
        read_only_fields = ('id', 'created_at')

class ReportFlagSerializer(serializers.Serializer):
    type = serializers.CharField()
    description = serializers.CharField()
    severity = serializers.CharField(default='medium')
    timestamp = serializers.DateTimeField()
