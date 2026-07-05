"""
Views for accounts app.
"""
from django.contrib.auth import get_user_model
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView

from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    UserSerializer,
    UserUpdateSerializer,
    ChangePasswordSerializer,
    GoogleAuthSerializer,
    StudentProfileSerializer,
    StudentProfileUpdateSerializer,
    TeacherProfileSerializer,
    TeacherProfileUpdateSerializer,
)
from .models import StudentProfile, TeacherProfile
from .permissions import IsOwnerOrAdmin

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    """Register a new user account."""
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Generate tokens
        refresh = RefreshToken.for_user(user)
        return Response({
            'message': 'Registration successful.',
            'user': UserSerializer(user).data,
            'access_token': str(refresh.access_token),
            'refresh_token': str(refresh),
            'token_type': 'Bearer',
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """Authenticate user and return JWT tokens."""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']
        tokens = serializer.validated_data['tokens']

        return Response({
            'message': 'Login successful.',
            'user': UserSerializer(user).data,
            'access_token': tokens['access'],
            'refresh_token': tokens['refresh'],
            'token_type': 'Bearer',
        }, status=status.HTTP_200_OK)


class GoogleAuthView(APIView):
    """Authenticate via Google OAuth2."""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = GoogleAuthSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        idinfo = serializer.validated_data['token']
        email = idinfo.get('email')
        first_name = idinfo.get('given_name', '')
        last_name = idinfo.get('family_name', '')

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'first_name': first_name,
                'last_name': last_name,
                'auth_provider': User.AuthProvider.GOOGLE,
                'is_verified': True,
            }
        )

        if not created and user.auth_provider != User.AuthProvider.GOOGLE:
            return Response({
                'error': 'This email is already registered with a different method. '
                         'Please use your email and password to login.'
            }, status=status.HTTP_400_BAD_REQUEST)

        refresh = RefreshToken.for_user(user)
        return Response({
            'message': 'Google authentication successful.',
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            },
            'is_new_user': created,
        }, status=status.HTTP_200_OK)


class CustomTokenRefreshView(TokenRefreshView):
    """Refresh JWT access token."""
    def post(self, request, *args, **kwargs):
        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        if 'refresh_token' in data:
            data['refresh'] = data['refresh_token']
        serializer = self.get_serializer(data=data)
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            return Response({'detail': 'Invalid refresh token'}, status=status.HTTP_401_UNAUTHORIZED)
        
        res_data = serializer.validated_data
        return Response({
            'access_token': res_data.get('access'),
            'refresh_token': res_data.get('refresh') or data.get('refresh'),
            'token_type': 'Bearer'
        }, status=status.HTTP_200_OK)


class LogoutView(APIView):
    """Logout by blacklisting the refresh token."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if not refresh_token:
                return Response(
                    {'error': 'Refresh token is required.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(
                {'message': 'Logout successful.'},
                status=status.HTTP_200_OK
            )
        except Exception:
            return Response(
                {'error': 'Invalid or expired token.'},
                status=status.HTTP_400_BAD_REQUEST
            )


class MeView(generics.RetrieveUpdateAPIView):
    """Get or update the authenticated user's profile."""
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return UserUpdateSerializer
        return UserSerializer

    def get_object(self):
        return self.request.user


class ChangePasswordView(APIView):
    """Change authenticated user's password."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)

        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()

        return Response(
            {'message': 'Password changed successfully.'},
            status=status.HTTP_200_OK
        )


class StudentProfileView(generics.RetrieveUpdateAPIView):
    """Get or update the authenticated student's profile."""
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return StudentProfileUpdateSerializer
        return StudentProfileSerializer

    def get_object(self):
        profile, _ = StudentProfile.objects.get_or_create(user=self.request.user)
        return profile


class TeacherProfileView(generics.RetrieveUpdateAPIView):
    """Get or update the authenticated teacher's profile."""
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return TeacherProfileUpdateSerializer
        return TeacherProfileSerializer

    def get_object(self):
        profile, _ = TeacherProfile.objects.get_or_create(user=self.request.user)
        return profile


class UserListView(generics.ListAPIView):
    """List all users (admin only)."""
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['role', 'is_active', 'is_verified']
    search_fields = ['first_name', 'last_name', 'email', 'phone']
    ordering_fields = ['date_joined', 'first_name', 'last_name']

    def get_queryset(self):
        user = self.request.user
        if user.role == 'super_admin' or user.is_staff:
            return User.objects.all()
        elif user.role == 'school_admin':
            try:
                school = user.school_admin_profile.school
                from django.db.models import Q
                return User.objects.filter(
                    Q(teacher_profile__school=school) | Q(student_profile__school=school) | Q(school_admin_profile__school=school)
                ).distinct()
            except Exception:
                return User.objects.filter(id=user.id)
        return User.objects.none()


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Get, update, or delete a user (admin only)."""
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]
    queryset = User.objects.all()
    lookup_field = 'id'

    def destroy(self, request, *args, **kwargs):
        user = self.get_object()
        user.is_active = False
        user.save()
        return Response(
            {'message': 'User deactivated successfully.'},
            status=status.HTTP_200_OK
        )


class UserVerifyView(APIView):
    """Admin-only view to verify user profiles."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, id):
        if request.user.role not in ('school_admin', 'super_admin'):
            return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
        try:
            user = User.objects.get(id=id)
            user.is_verified = True
            user.save()
            return Response({'status': 'User verified successfully.'})
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
