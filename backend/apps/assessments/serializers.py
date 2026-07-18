from rest_framework import serializers
from django.db import transaction
from apps.content.serializers import SubjectSerializer, QuestionSerializer, QuestionCreateSerializer
from apps.content.models import Subject, Question, QuestionOption
from apps.schools.models import Classroom
from .models import Assessment, AssessmentQuestion, AssessmentAttempt, AnswerResponse, StagedQuestion, ExtractionJob


class AssessmentQuestionSerializer(serializers.ModelSerializer):
    question = QuestionSerializer(read_only=True)
    question_id = serializers.PrimaryKeyRelatedField(
        queryset=Question.objects.all(), source='question', write_only=True
    )

    class Meta:
        model = AssessmentQuestion
        fields = ('id', 'question', 'question_id', 'order', 'points_override', 'is_required')


class AssessmentSerializer(serializers.ModelSerializer):
    subject_details = SubjectSerializer(source='subject', read_only=True)
    classroom_name = serializers.CharField(source='classroom.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)
    assessment_questions = AssessmentQuestionSerializer(many=True, read_only=True)
    question_count = serializers.IntegerField(read_only=True)
    total_points = serializers.DecimalField(max_digits=6, decimal_places=2, read_only=True)

    class Meta:
        model = Assessment
        fields = '__all__'
        read_only_fields = ('id', 'created_by', 'created_at', 'updated_at')

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        request = self.context.get('request')
        
        # If student is retrieving the assessment, apply randomization/shuffling in a secure, consistent manner
        if request and request.user.is_authenticated and request.user.role == 'student':
            import random
            import hashlib
            
            # Generate a consistent random seed per student + assessment to survive reloads/resume
            seed_str = f"{request.user.id}-{instance.id}"
            seed_int = int(hashlib.md5(seed_str.encode('utf-8')).hexdigest(), 16)
            local_rand = random.Random(seed_int)
            
            questions_list = representation.get('assessment_questions', [])
            
            # 1. Shuffle questions if enabled
            if instance.shuffle_questions:
                local_rand.shuffle(questions_list)
                
            # 2. Shuffle options inside each question if enabled
            if instance.shuffle_options:
                for q_item in questions_list:
                    q_data = q_item.get('question')
                    if q_data and 'options' in q_data:
                        local_rand.shuffle(q_data['options'])
                        
            representation['assessment_questions'] = questions_list
            
        return representation


class AssessmentListSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    classroom_name = serializers.CharField(source='classroom.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)
    question_count = serializers.IntegerField(read_only=True)
    total_points = serializers.DecimalField(max_digits=6, decimal_places=2, read_only=True)

    class Meta:
        model = Assessment
        fields = (
            'id', 'title', 'assessment_type', 'status', 'difficulty', 'time_limit_minutes',
            'max_attempts', 'passing_score', 'is_proctored', 'start_datetime', 'end_datetime',
            'subject', 'subject_name', 'classroom', 'classroom_name', 'created_by_name',
            'question_count', 'total_points', 'created_at'
        )


class AssessmentCreateSerializer(serializers.ModelSerializer):
    questions_data = serializers.ListField(
        child=serializers.JSONField(), write_only=True, required=False,
        help_text="List of objects containing: {question_id: uuid, order: int, points_override: decimal, is_required: bool}"
    )

    class Meta:
        model = Assessment
        fields = '__all__'
        read_only_fields = ('id', 'created_by', 'created_at', 'updated_at')

    def create(self, validated_data):
        questions_data = validated_data.pop('questions_data', [])
        validated_data['created_by'] = self.context['request'].user
        
        with transaction.atomic():
            assessment = Assessment.objects.create(**validated_data)
            for idx, q_item in enumerate(questions_data):
                q_id = q_item.get('question_id')
                try:
                    question = Question.objects.get(id=q_id)
                    AssessmentQuestion.objects.create(
                        assessment=assessment,
                        question=question,
                        order=q_item.get('order', idx),
                        points_override=q_item.get('points_override'),
                        is_required=q_item.get('is_required', True)
                    )
                except Question.DoesNotExist:
                    raise serializers.ValidationError(f"Question with ID {q_id} does not exist.")
            
            return assessment

    def update(self, instance, validated_data):
        questions_data = validated_data.pop('questions_data', None)
        
        with transaction.atomic():
            instance = super().update(instance, validated_data)
            
            if questions_data is not None:
                # Replace questions
                instance.assessment_questions.all().delete()
                for idx, q_item in enumerate(questions_data):
                    q_id = q_item.get('question_id')
                    try:
                        question = Question.objects.get(id=q_id)
                        AssessmentQuestion.objects.create(
                            assessment=instance,
                            question=question,
                            order=q_item.get('order', idx),
                            points_override=q_item.get('points_override'),
                            is_required=q_item.get('is_required', True)
                        )
                    except Question.DoesNotExist:
                        raise serializers.ValidationError(f"Question with ID {q_id} does not exist.")
            
            return instance


class AnswerResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnswerResponse
        fields = '__all__'
        read_only_fields = ('id', 'attempt', 'is_correct', 'points_awarded', 'auto_graded', 'answered_at')

    def validate(self, attrs):
        # Additional validation can go here
        return attrs


class AttemptSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    assessment_title = serializers.CharField(source='assessment.title', read_only=True)
    responses = AnswerResponseSerializer(many=True, read_only=True)

    class Meta:
        model = AssessmentAttempt
        fields = '__all__'
        read_only_fields = ('id', 'student', 'started_at', 'submitted_at', 'graded_at', 'score', 'percentage', 'graded_by')


class AttemptListSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    assessment_title = serializers.CharField(source='assessment.title', read_only=True)
    assessment_type = serializers.CharField(source='assessment.assessment_type', read_only=True)
    is_proctored = serializers.BooleanField(source='assessment.is_proctored', read_only=True)

    class Meta:
        model = AssessmentAttempt
        fields = (
            'id', 'assessment', 'assessment_title', 'assessment_type', 'is_proctored',
            'student', 'student_name', 'status', 'started_at', 'submitted_at', 'score', 'percentage', 'attempt_number'
        )


class SaveAnswerSerializer(serializers.Serializer):
    question_id = serializers.PrimaryKeyRelatedField(queryset=Question.objects.all())
    selected_options = serializers.ListField(child=serializers.UUIDField(), required=False, default=list)
    text_answer = serializers.CharField(required=False, allow_blank=True, default='')
    matching_pairs = serializers.JSONField(required=False, default=dict)
    ordering_sequence = serializers.ListField(child=serializers.UUIDField(), required=False, default=list)
    # File attachment is handled separately using multipart form data upload


class SubmitAssessmentSerializer(serializers.Serializer):
    answers = serializers.ListField(child=SaveAnswerSerializer(), required=False, default=list)


class GradeResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnswerResponse
        fields = ('points_awarded', 'teacher_feedback')

    def validate_points_awarded(self, value):
        # Verify points awarded don't exceed allowed points
        # Can do validation inside views/serializers
        return value


class ExtractDocumentSerializer(serializers.Serializer):
    file = serializers.FileField()
    subject_id = serializers.PrimaryKeyRelatedField(queryset=Subject.objects.all(), source='subject')
    topic_id = serializers.PrimaryKeyRelatedField(queryset=Question.objects.all(), required=False, allow_null=True, source='topic')
    difficulty = serializers.ChoiceField(choices=Assessment.Difficulty.choices, default=Assessment.Difficulty.MEDIUM)


class StagedQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = StagedQuestion
        fields = '__all__'


class ExtractionJobSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    
    class Meta:
        model = ExtractionJob
        fields = '__all__'
        read_only_fields = ('id', 'uploaded_by', 'status', 'progress', 'error_message', 'questions_extracted', 'extraction_provider', 'created_at', 'completed_at')

