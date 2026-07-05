from rest_framework.routers import DefaultRouter
from .views import SubjectViewSet, TopicViewSet, QuestionViewSet, QuestionBankViewSet

router = DefaultRouter()
router.register('subjects', SubjectViewSet, basename='subject')
router.register('topics', TopicViewSet, basename='topic')
router.register('questions', QuestionViewSet, basename='question')
router.register('question-banks', QuestionBankViewSet, basename='question-bank')

urlpatterns = router.urls
