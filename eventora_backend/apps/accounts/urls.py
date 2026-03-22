"""
accounts/urls.py
"""

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    LoginView,
    LogoutView,
    StudentRegisterView,
    AdminRegisterView,
    ProfileView,
    ChangePasswordView,
    UserListView,
)

urlpatterns = [
    # Auth
    path('login/',                LoginView.as_view(),          name='login'),
    path('logout/',               LogoutView.as_view(),         name='logout'),
    path('token/refresh/',        TokenRefreshView.as_view(),   name='token_refresh'),

    # Registration
    path('register/student/',     StudentRegisterView.as_view(), name='register_student'),
    path('register/admin/',       AdminRegisterView.as_view(),   name='register_admin'),

    # Profile
    path('profile/',              ProfileView.as_view(),         name='profile'),
    path('change-password/',      ChangePasswordView.as_view(),  name='change_password'),

    # Admin
    path('users/',                UserListView.as_view(),        name='user_list'),
]
