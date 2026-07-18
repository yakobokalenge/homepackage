from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProctoringViewSet

router = DefaultRouter()
router.register('sessions', ProctoringViewSet, basename='proctoring-session')

urlpatterns = [
    path('', include(router.urls)),
]
