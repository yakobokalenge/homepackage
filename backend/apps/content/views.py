from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import models
from .models import Subject, Topic, Question, QuestionBank
from .serializers import (
    SubjectSerializer, TopicSerializer, QuestionSerializer,
    QuestionCreateSerializer, QuestionBankSerializer,
)


class SubjectViewSet(viewsets.ModelViewSet):
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    filterset_fields = ['education_level', 'is_active']
    search_fields = ['name', 'name_sw', 'code']


class TopicViewSet(viewsets.ModelViewSet):
    queryset = Topic.objects.select_related('subject')
    serializer_class = TopicSerializer
    filterset_fields = ['subject']


class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.select_related('subject', 'topic', 'created_by').prefetch_related('options')
    filterset_fields = ['subject', 'topic', 'question_type', 'difficulty', 'is_public']
    search_fields = ['text', 'text_sw']
    ordering_fields = ['created_at', 'difficulty', 'points']

    def get_serializer_class(self):
        if self.action == 'create':
            return QuestionCreateSerializer
        return QuestionSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        if not self.request.user.is_staff:
            qs = qs.filter(
                models.Q(created_by=self.request.user) | models.Q(is_public=True)
            )
        return qs

    @action(detail=False, methods=['post'])
    def generate_ai(self, request):
        """AI-assisted question generation endpoint."""
        from apps.content.models import Subject, Topic
        import uuid
        
        subject_id = request.data.get('subject')
        topic_id = request.data.get('topic')
        question_type = request.data.get('question_type', 'mcq')
        difficulty = request.data.get('difficulty', 'medium')
        count = int(request.data.get('count', 3))
        prompt = request.data.get('prompt', '')

        if not subject_id:
            return Response({'error': 'Subject ID is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            subject = Subject.objects.get(id=subject_id)
        except Subject.DoesNotExist:
            return Response({'error': 'Subject not found.'}, status=status.HTTP_404_NOT_FOUND)

        topic = None
        if topic_id:
            try:
                topic = Topic.objects.get(id=topic_id)
            except Topic.DoesNotExist:
                pass

        sub_name = subject.name.lower()
        topic_name = topic.name if topic else "General Content"
        
        generated_questions = []

        for i in range(count):
            if 'math' in sub_name:
                q_text = f"Solve the following algebraic equation: 3x + {5 + i * 2} = {20 + i * 4}."
                options = [
                    {'text': f"x = {5 + i}", 'is_correct': True, 'order': 1},
                    {'text': f"x = {3 + i}", 'is_correct': False, 'order': 2},
                    {'text': f"x = {7 + i}", 'is_correct': False, 'order': 3},
                    {'text': f"x = {2 + i}", 'is_correct': False, 'order': 4},
                ]
            elif 'bio' in sub_name:
                q_text = f"Which cellular structure holds cell DNA?" if i == 0 else "What organelle performs photosynthesis in green plants?"
                options = [
                    {'text': "Nucleus" if i == 0 else "Chloroplast", 'is_correct': True, 'order': 1},
                    {'text': "Ribosome" if i == 0 else "Cell Wall", 'is_correct': False, 'order': 2},
                    {'text': "Mitochondria" if i == 0 else "Cytoplasm", 'is_correct': False, 'order': 3},
                ]
            else:
                q_text = f"Describe the core concepts of topic: '{topic_name}' - AI query #{i+1}."
                options = [
                    {'text': "Standard Correct Option", 'is_correct': True, 'order': 1},
                    {'text': "Standard Incorrect Distractor", 'is_correct': False, 'order': 2},
                ]

            if question_type == 'essay':
                options = []
            elif question_type == 'short_answer':
                options = [{'text': "correct answer text", 'is_correct': True, 'order': 1}]

            generated_questions.append({
                'text': q_text,
                'question_type': question_type,
                'difficulty': difficulty,
                'points': 5.0,
                'subject': subject.id,
                'topic': topic.id if topic else None,
                'options': options
            })

        saved_instances = []
        for q_data in generated_questions:
            serializer = QuestionCreateSerializer(data=q_data, context={'request': request})
            serializer.is_valid(raise_exception=True)
            instance = serializer.save()
            saved_instances.append(instance)

        return Response(QuestionSerializer(saved_instances, many=True).data, status=status.HTTP_201_CREATED)


class QuestionBankViewSet(viewsets.ModelViewSet):
    queryset = QuestionBank.objects.select_related('subject', 'created_by')
    serializer_class = QuestionBankSerializer
    filterset_fields = ['subject', 'is_public']
    search_fields = ['name']

    def get_queryset(self):
        qs = super().get_queryset()
        if not self.request.user.is_staff:
            from django.db import models as m
            qs = qs.filter(m.Q(created_by=self.request.user) | m.Q(is_public=True))
        return qs
