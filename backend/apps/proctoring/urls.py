from django.urls import path
from . import views

urlpatterns = [
    path('proctoring/start/<uuid:attempt_id>/', views.start_session, name='proctoring-start'),
    path('proctoring/consent/<uuid:session_id>/', views.consent, name='proctoring-consent'),
    path('proctoring/flag/<uuid:session_id>/', views.report_flag, name='proctoring-flag'),
    path('proctoring/upload-url/<uuid:session_id>/', views.get_upload_url, name='proctoring-upload-url'),
    path('proctoring/review/<uuid:session_id>/', views.review_session, name='proctoring-review'),
    path('proctoring/mark-reviewed/<uuid:session_id>/', views.mark_reviewed, name='proctoring-mark-reviewed'),
]
