from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AssessmentViewSet, AttemptViewSet, ExtractionJobViewSet, StagedQuestionViewSet

router = DefaultRouter()
router.register('assessments', AssessmentViewSet, basename='assessment')
router.register('attempts', AttemptViewSet, basename='attempt')
router.register('extraction-jobs', ExtractionJobViewSet, basename='extraction-job')
router.register('staged-questions', StagedQuestionViewSet, basename='staged-question')

urlpatterns = [
    path('', include(router.urls)),
]

