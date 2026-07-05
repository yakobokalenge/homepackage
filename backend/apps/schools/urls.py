from rest_framework.routers import DefaultRouter
from .views import SchoolViewSet, ClassroomViewSet

router = DefaultRouter()
router.register('schools', SchoolViewSet, basename='school')
router.register('classrooms', ClassroomViewSet, basename='classroom')

urlpatterns = router.urls
