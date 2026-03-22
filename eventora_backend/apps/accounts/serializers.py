"""
accounts/serializers.py
Serializers for user registration, login, and profile.
"""

from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.password_validation import validate_password
from .models import User


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Adds user info to the JWT response payload."""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['full_name']  = user.full_name
        token['email']      = user.email
        token['role']       = user.role
        token['student_id'] = user.student_id or ''
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        # Append user details to the login response
        data['user'] = {
            'id':         self.user.id,
            'email':      self.user.email,
            'full_name':  self.user.full_name,
            'role':       self.user.role,
            'student_id': self.user.student_id,
            'department': self.user.department,
            'admin_role': self.user.admin_role,
        }
        return data


# ── Registration ──────────────────────────────────────────────────────────────

class StudentRegisterSerializer(serializers.ModelSerializer):
    password  = serializers.CharField(write_only=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, label='Confirm Password')

    class Meta:
        model = User
        fields = [
            'email', 'full_name', 'password', 'password2',
            'student_id', 'department', 'year', 'phone',
        ]

    def validate(self, attrs):
        if attrs['password'] != attrs.pop('password2'):
            raise serializers.ValidationError({'password': 'Passwords do not match.'})
        return attrs

    def create(self, validated_data):
        user = User.objects.create_user(
            role=User.Role.STUDENT,
            **validated_data
        )
        return user


class AdminRegisterSerializer(serializers.ModelSerializer):
    password  = serializers.CharField(write_only=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, label='Confirm Password')

    class Meta:
        model = User
        fields = ['email', 'full_name', 'password', 'password2', 'admin_role']

    def validate(self, attrs):
        if attrs['password'] != attrs.pop('password2'):
            raise serializers.ValidationError({'password': 'Passwords do not match.'})
        return attrs

    def create(self, validated_data):
        user = User.objects.create_user(
            role=User.Role.ADMIN,
            is_staff=True,
            **validated_data
        )
        return user


# ── Profile ───────────────────────────────────────────────────────────────────

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'email', 'full_name', 'role',
            'student_id', 'department', 'year', 'phone',
            'admin_role', 'date_joined',
        ]
        read_only_fields = ['id', 'email', 'role', 'date_joined']


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Old password is incorrect.')
        return value
