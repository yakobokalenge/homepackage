from django.urls import path
from . import views

urlpatterns = [
    path('student/', views.student_overview, name='analytics-student'),
    path('weak-topics/', views.weak_topics, name='analytics-weak-topics'),
    path('teacher/', views.teacher_class_performance, name='analytics-teacher'),
    path('admin/', views.admin_overview, name='analytics-admin'),
    path('admin/export-financial/', views.export_financial_csv, name='analytics-export-financial'),
    path('admin/export-subscriptions/', views.export_subscriptions_csv, name='analytics-export-subscriptions'),
    path('admin/export-regional/', views.export_regional_csv, name='analytics-export-regional'),
    path('ai-tutor/', views.ai_tutor_chat, name='analytics-ai-tutor'),
]
