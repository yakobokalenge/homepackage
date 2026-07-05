from rest_framework import serializers
from .models import Subject, Topic, Question, QuestionOption, QuestionBank


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = '__all__'


class TopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Topic
        fields = '__all__'


class QuestionOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionOption
        fields = ('id', 'text', 'is_correct', 'order', 'match_pair')

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')
        # If student is taking the exam, we hide is_correct to prevent inspect-element cheating
        if request and request.user.is_authenticated and request.user.role == 'student':
            if self.context.get('hide_correct', True):
                data.pop('is_correct', None)
        return data


class QuestionSerializer(serializers.ModelSerializer):
    options = QuestionOptionSerializer(many=True, read_only=True)
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)

    class Meta:
        model = Question
        fields = '__all__'
        read_only_fields = ('id', 'created_by', 'created_at', 'updated_at')

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class QuestionCreateSerializer(serializers.ModelSerializer):
    options = QuestionOptionSerializer(many=True, required=False)

    class Meta:
        model = Question
        fields = '__all__'
        read_only_fields = ('id', 'created_by', 'created_at', 'updated_at')

    def create(self, validated_data):
        options_data = validated_data.pop('options', [])
        validated_data['created_by'] = self.context['request'].user
        question = Question.objects.create(**validated_data)
        for opt in options_data:
            QuestionOption.objects.create(question=question, **opt)
        return question


class QuestionBankSerializer(serializers.ModelSerializer):
    question_count = serializers.SerializerMethodField()

    class Meta:
        model = QuestionBank
        fields = '__all__'
        read_only_fields = ('id', 'created_by', 'created_at', 'updated_at')

    def get_question_count(self, obj):
        return obj.questions.count()

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)
