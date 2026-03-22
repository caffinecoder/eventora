"""
accounts/models.py
Custom User model supporting both Student and Admin roles.
"""

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', User.Role.ADMIN)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):

    class Role(models.TextChoices):
        STUDENT = 'student', 'Student'
        ADMIN   = 'admin',   'Admin'

    class Department(models.TextChoices):
        CS   = 'cs',   'Computer Science'
        EC   = 'ec',   'Electronics & Communication'
        ME   = 'me',   'Mechanical Engineering'
        BA   = 'ba',   'Business Administration'
        AH   = 'ah',   'Arts & Humanities'
        SC   = 'sc',   'Sciences'
        OTHER = 'other', 'Other'

    # Core fields
    email      = models.EmailField(unique=True)
    full_name  = models.CharField(max_length=150)
    role       = models.CharField(max_length=10, choices=Role.choices, default=Role.STUDENT)

    # Student-specific fields
    student_id = models.CharField(max_length=20, blank=True, null=True, unique=True)
    department = models.CharField(max_length=10, choices=Department.choices, blank=True, null=True)
    year       = models.PositiveSmallIntegerField(blank=True, null=True)
    phone      = models.CharField(max_length=15, blank=True, null=True)

    # Admin-specific fields
    admin_role = models.CharField(max_length=50, blank=True, null=True,
                                  help_text='e.g. Event Coordinator, Super Admin')

    # Status
    is_active  = models.BooleanField(default=True)
    is_staff   = models.BooleanField(default=False)

    date_joined = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = ['full_name']

    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return f"{self.full_name} ({self.email})"

    @property
    def is_student(self):
        return self.role == self.Role.STUDENT

    @property
    def is_admin_user(self):
        return self.role == self.Role.ADMIN
