"""
accounts/views.py
Authentication and user profile views.
"""

from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User
from .serializers import (
    CustomTokenObtainPairSerializer,
    StudentRegisterSerializer,
    AdminRegisterSerializer,
    UserProfileSerializer,
    ChangePasswordSerializer,
)
from .permissions import IsAdminUser


# ── Auth ──────────────────────────────────────────────────────────────────────

class LoginView(TokenObtainPairView):
    """
    POST /api/v1/auth/login/
    Returns access + refresh tokens with user info.
    Body: { "email": "...", "password": "..." }
    """
    permission_classes = [AllowAny]
    serializer_class   = CustomTokenObtainPairSerializer


class LogoutView(APIView):
    """
    POST /api/v1/auth/logout/
    Blacklists the refresh token to invalidate the session.
    Body: { "refresh": "<refresh_token>" }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            token = RefreshToken(request.data['refresh'])
            token.blacklist()
            return Response({'detail': 'Successfully logged out.'}, status=status.HTTP_200_OK)
        except Exception:
            return Response({'detail': 'Invalid or expired token.'}, status=status.HTTP_400_BAD_REQUEST)


# ── Registration ──────────────────────────────────────────────────────────────

class StudentRegisterView(generics.CreateAPIView):
    """
    POST /api/v1/auth/register/student/
    Registers a new student account.
    """
    permission_classes = [AllowAny]
    serializer_class   = StudentRegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({
            'detail': 'Student account created successfully.',
            'user': {
                'id':         user.id,
                'email':      user.email,
                'full_name':  user.full_name,
                'student_id': user.student_id,
                'department': user.department,
            }
        }, status=status.HTTP_201_CREATED)


class AdminRegisterView(generics.CreateAPIView):
    """
    POST /api/v1/auth/register/admin/
    Registers a new admin account. Only accessible by existing super admins.
    """
    permission_classes = [IsAdminUser]
    serializer_class   = AdminRegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({
            'detail': 'Admin account created successfully.',
            'user': {
                'id':        user.id,
                'email':     user.email,
                'full_name': user.full_name,
                'admin_role': user.admin_role,
            }
        }, status=status.HTTP_201_CREATED)


# ── Profile ───────────────────────────────────────────────────────────────────

class ProfileView(generics.RetrieveUpdateAPIView):
    """
    GET  /api/v1/auth/profile/   — Get logged-in user's profile
    PUT  /api/v1/auth/profile/   — Update profile
    PATCH /api/v1/auth/profile/  — Partial update
    """
    permission_classes = [IsAuthenticated]
    serializer_class   = UserProfileSerializer

    def get_object(self):
        return self.request.user


class ChangePasswordView(APIView):
    """
    POST /api/v1/auth/change-password/
    Body: { "old_password": "...", "new_password": "..." }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()
        return Response({'detail': 'Password changed successfully.'}, status=status.HTTP_200_OK)


# ── Admin: List All Users ─────────────────────────────────────────────────────

class UserListView(generics.ListAPIView):
    """
    GET /api/v1/auth/users/
    Admin only — lists all users, filterable by role.
    Query params: ?role=student | ?role=admin
    """
    permission_classes = [IsAdminUser]
    serializer_class   = UserProfileSerializer

    def get_queryset(self):
        queryset = User.objects.all().order_by('-date_joined')
        role = self.request.query_params.get('role')
        if role:
            queryset = queryset.filter(role=role)
        return queryset
