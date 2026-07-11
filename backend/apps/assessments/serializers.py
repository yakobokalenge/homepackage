from rest_framework import serializers
from django.contrib.auth import get_user_model
from apps.content.serializers import QuestionSerializer
from apps.schools.serializers import ClassroomSerializer
from .models import Assessment, AssessmentQuestion, AssessmentAttempt, AnswerResponse

User = get_user_model()


class AssessmentQuestionSerializer(serializers.ModelSerializer):
    question = QuestionSerializer(read_only=True)

    class Meta:
        model = AssessmentQuestion
        fields = ['id', 'question', 'order', 'points_override']


class AssessmentSerializer(serializers.ModelSerializer):
    subject_name = serializers.ReadOnlyField(source='subject.name')
    classroom_detail = ClassroomSerializer(source='classroom', read_only=True)
    questions = serializers.SerializerMethodField()

    class Meta:
        model = Assessment
        fields = [
            'id', 'title', 'description', 'assessment_type', 'subject', 
            'subject_name', 'classroom', 'classroom_detail', 'status', 
            'start_time', 'end_time', 'duration_minutes', 'total_points', 
            'pass_percentage', 'questions_limit', 'questions', 'created_at'
        ]
        read_only_fields = ['created_by', 'school', 'total_points']

    def get_questions(self, obj):
        links = obj.assessment_questions.all()
        return AssessmentQuestionSerializer(links, many=True).data


class AnswerResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnswerResponse
        fields = [
            'id', 'attempt', 'question', 'selected_option', 
            'answer_text', 'points_awarded', 'is_correct', 'teacher_feedback'
        ]


class AssessmentAttemptSerializer(serializers.ModelSerializer):
    student_name = serializers.ReadOnlyField(source='student.full_name')
    assessment_title = serializers.ReadOnlyField(source='assessment.title')
    responses = AnswerResponseSerializer(many=True, read_only=True)

    class Meta:
        model = AssessmentAttempt
        fields = [
            'id', 'assessment', 'assessment_title', 'student', 
            'student_name', 'started_at', 'submitted_at', 'score', 
            'percentage', 'status', 'responses'
        ]
        read_only_fields = ['student', 'started_at', 'submitted_at', 'score', 'percentage']
