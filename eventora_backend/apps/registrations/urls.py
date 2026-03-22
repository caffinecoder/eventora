"""
registrations/urls.py
"""

from django.urls import path
from .views import (
    MyRegistrationsView,
    RegisterForEventView,
    CancelRegistrationView,
    RegistrationDetailView,
    AdminRegistrationListView,
    AdminUpdateRegistrationStatusView,
    AdminMarkAttendanceView,
)

urlpatterns = [
    # Student
    path('',                          RegisterForEventView.as_view(),             name='register'),
    path('my/',                       MyRegistrationsView.as_view(),              name='my_registrations'),
    path('<int:pk>/',                  RegistrationDetailView.as_view(),           name='registration_detail'),
    path('<int:pk>/cancel/',           CancelRegistrationView.as_view(),           name='cancel_registration'),

    # Admin — static paths MUST come before dynamic <int:pk> paths
    path('admin/',                    AdminRegistrationListView.as_view(),         name='admin_registrations'),
    path('admin/attendance/',         AdminMarkAttendanceView.as_view(),           name='admin_attendance'),
    path('admin/<int:pk>/status/',    AdminUpdateRegistrationStatusView.as_view(), name='admin_reg_status'),
]