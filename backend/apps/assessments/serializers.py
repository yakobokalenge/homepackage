from rest_framework import serializers
from .models import Assessment, AssessmentQuestion, AssessmentAttempt, AnswerResponse
from apps.content.serializers import QuestionSerializer


class AssessmentQuestionSerializer(serializers.ModelSerializer):
    question_detail = QuestionSerializer(source='question', read_only=True)

    class Meta:
        model = AssessmentQuestion
        fields = ('id', 'question', 'question_detail', 'order', 'points_override')


class AssessmentSerializer(serializers.ModelSerializer):
    questions = AssessmentQuestionSerializer(source='assessment_questions', many=True, read_only=True)
    question_count = serializers.SerializerMethodField()
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)

    class Meta:
        model = Assessment
        fields = '__all__'
        read_only_fields = ('id', 'created_by', 'total_points', 'created_at', 'updated_at')

    def get_question_count(self, obj):
        return obj.assessment_questions.count()

    def validate_file_attachment(self, value):
        if value:
            if value.size > 50 * 1024 * 1024:
                raise serializers.ValidationError("File size cannot exceed 50MB.")
            ext = value.name.split('.')[-1].lower()
            if ext not in ['pdf', 'doc', 'docx']:
                raise serializers.ValidationError("Only PDF and Word (.doc, .docx) files are allowed.")
        return value

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class AssessmentListSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    classroom_name = serializers.CharField(source='classroom.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)
    question_count = serializers.SerializerMethodField()

    class Meta:
        model = Assessment
        fields = ('id', 'title', 'assessment_type', 'subject', 'subject_name', 'classroom', 'classroom_name', 'status',
                  'start_time', 'end_time', 'duration_minutes', 'requires_proctoring', 'questions_limit',
                  'is_file_based', 'file_attachment',
                  'question_count', 'created_by_name', 'created_at')

    def get_question_count(self, obj):
        return obj.assessment_questions.count()


class AnswerResponseSerializer(serializers.ModelSerializer):
    question_detail = QuestionSerializer(source='question', read_only=True)

    class Meta:
        model = AnswerResponse
        fields = (
            'id', 'question', 'question_detail', 'answer_text',
            'selected_options', 'answer_data', 'time_spent_seconds',
            'is_correct', 'points_awarded', 'teacher_feedback'
        )

    def create(self, validated_data):
        selected = validated_data.pop('selected_options', [])
        response = AnswerResponse.objects.create(**validated_data)
        if selected:
            response.selected_options.set(selected)
        return response


class AttemptSerializer(serializers.ModelSerializer):
    responses = AnswerResponseSerializer(many=True, read_only=True)
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    assessment_title = serializers.CharField(source='assessment.title', read_only=True)

    class Meta:
        model = AssessmentAttempt
        fields = '__all__'
        read_only_fields = ('id', 'student', 'started_at', 'submitted_at', 'score', 'percentage')

    def validate_submission_file(self, value):
        if value:
            if value.size > 15 * 1024 * 1024:
                raise serializers.ValidationError("Submission size cannot exceed 15MB.")
            ext = value.name.split('.')[-1].lower()
            if ext not in ['pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png']:
                raise serializers.ValidationError("Allowed formats: PDF, Word, or Images (JPG, PNG).")
        return value


class AttemptResultSerializer(serializers.ModelSerializer):
    assessment_title = serializers.CharField(source='assessment.title', read_only=True)

    class Meta:
        model = AssessmentAttempt
        fields = ('id', 'assessment', 'assessment_title', 'status', 'score', 'percentage',
                  'started_at', 'submitted_at', 'time_spent_seconds')
