from rest_framework import serializers
from .models import Subject, Topic, Question, QuestionOption, QuestionBank, QuestionUsage


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


class QuestionUsageSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionUsage
        fields = '__all__'


class QuestionSerializer(serializers.ModelSerializer):
    options = QuestionOptionSerializer(many=True, read_only=True)
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)
    usage_stats = QuestionUsageSerializer(read_only=True, required=False)

    class Meta:
        model = Question
        fields = '__all__'
        read_only_fields = ('id', 'created_by', 'created_at', 'updated_at')

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        question = super().create(validated_data)
        QuestionUsage.objects.create(question=question)
        return question


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
        QuestionUsage.objects.create(question=question)
        return question


class QuestionBankSerializer(serializers.ModelSerializer):
    question_count = serializers.SerializerMethodField()

    class Meta:
        model = QuestionBank
        fields = '__all__'
        read_only_fields = ('id', 'created_by', 'created_at', 'updated_at')

    def get_question_count(self, obj):
        return obj.questions.count()

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # Dynamically serialize full details of linked questions for teacher UI ease of use
        representation['questions_detail'] = QuestionSerializer(
            instance.questions.all(),
            many=True,
            context=self.context
        ).data
        return representation

    def create(self, validated_data):
        # Allow populating questions during creation if supplied
        questions = validated_data.pop('questions', [])
        validated_data['created_by'] = self.context['request'].user
        instance = QuestionBank.objects.create(**validated_data)
        if questions:
            instance.questions.set(questions)
        return instance
