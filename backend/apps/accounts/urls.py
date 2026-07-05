"""
URL configuration for accounts app.
"""
from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # Authentication
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('token/refresh/', views.CustomTokenRefreshView.as_view(), name='token-refresh'),
    path('refresh/', views.CustomTokenRefreshView.as_view(), name='token-refresh-fallback'),
    path('google/', views.GoogleAuthView.as_view(), name='google-auth'),

    # Current user
    path('me/', views.MeView.as_view(), name='me'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change-password'),

    # Profiles
    path('profile/student/', views.StudentProfileView.as_view(), name='student-profile'),
    path('profile/teacher/', views.TeacherProfileView.as_view(), name='teacher-profile'),

    # Admin user management
    path('users/', views.UserListView.as_view(), name='user-list'),
    path('users/<uuid:id>/', views.UserDetailView.as_view(), name='user-detail'),
    path('users/<uuid:id>/verify/', views.UserVerifyView.as_view(), name='user-verify'),
]
