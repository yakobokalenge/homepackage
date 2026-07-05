from rest_framework.routers import DefaultRouter
from .views import AssessmentViewSet, AttemptViewSet

router = DefaultRouter()
router.register('assessments', AssessmentViewSet, basename='assessment')
router.register('attempts', AttemptViewSet, basename='attempt')

urlpatterns = router.urls
