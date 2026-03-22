"""
registrations/views.py
"""

from rest_framework import generics, status, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone

from .models import Registration
from .serializers import (
    RegistrationCreateSerializer,
    RegistrationSerializer,
    AdminRegistrationSerializer,
)
from apps.accounts.permissions import IsStudent, IsAdminUser


# ── Student Views ─────────────────────────────────────────────────────────────

class MyRegistrationsView(generics.ListAPIView):
    """
    GET /api/v1/registrations/my/
    Returns all registrations for the logged-in student.
    Query params: ?status=confirmed | pending | cancelled | attended
    """
    permission_classes = [IsStudent]
    serializer_class   = RegistrationSerializer

    def get_queryset(self):
        qs     = Registration.objects.filter(student=self.request.user).select_related('event', 'event__category')
        status = self.request.query_params.get('status')
        if status:
            qs = qs.filter(status=status)
        return qs


class RegisterForEventView(generics.CreateAPIView):
    """
    POST /api/v1/registrations/
    Body: { "event": <event_id> }
    Registers the logged-in student for an event.
    Free events → immediately confirmed.
    Paid events → status = pending until payment is complete.
    """
    permission_classes = [IsStudent]
    serializer_class   = RegistrationCreateSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reg = serializer.save()
        return Response(
            RegistrationSerializer(reg).data,
            status=status.HTTP_201_CREATED
        )


class CancelRegistrationView(APIView):
    """
    PATCH /api/v1/registrations/<id>/cancel/
    Student cancels their own registration.
    Only allowed if the event hasn't started yet.
    """
    permission_classes = [IsStudent]

    def patch(self, request, pk):
        reg = get_object_or_404(Registration, pk=pk, student=request.user)

        if reg.status == Registration.Status.CANCELLED:
            return Response({'detail': 'Registration is already cancelled.'}, status=400)

        if reg.event.event_date < timezone.now().date():
            return Response({'detail': 'Cannot cancel a past event registration.'}, status=400)

        reg.status = Registration.Status.CANCELLED
        reg.save(update_fields=['status', 'updated_at'])
        return Response({'detail': 'Registration cancelled successfully.'})


class RegistrationDetailView(generics.RetrieveAPIView):
    """
    GET /api/v1/registrations/<id>/
    Returns a single registration (student can only see their own).
    """
    permission_classes = [IsAuthenticated]
    serializer_class   = RegistrationSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_admin_user:
            return Registration.objects.all().select_related('event', 'student')
        return Registration.objects.filter(student=user).select_related('event')


# ── Admin Views ───────────────────────────────────────────────────────────────

class AdminRegistrationListView(generics.ListAPIView):
    """
    GET /api/v1/registrations/admin/
    Lists all registrations across all events.
    Query params: ?event=<event_id> | ?status=confirmed | ?student=<student_id>
    """
    permission_classes = [IsAdminUser]
    serializer_class   = AdminRegistrationSerializer
    filter_backends    = [filters.SearchFilter, filters.OrderingFilter]
    search_fields      = ['student__full_name', 'student__email', 'registration_id']
    ordering_fields    = ['registered_at', 'status']
    ordering           = ['-registered_at']

    def get_queryset(self):
        qs     = Registration.objects.select_related('event', 'student')
        event  = self.request.query_params.get('event')
        sts    = self.request.query_params.get('status')
        student = self.request.query_params.get('student')
        if event:
            qs = qs.filter(event_id=event)
        if sts:
            qs = qs.filter(status=sts)
        if student:
            qs = qs.filter(student_id=student)
        return qs


class AdminUpdateRegistrationStatusView(APIView):
    """
    PATCH /api/v1/registrations/admin/<id>/status/
    Admin manually updates registration status.
    Body: { "status": "confirmed" | "attended" | "cancelled" }
    """
    permission_classes = [IsAdminUser]

    def patch(self, request, pk):
        reg        = get_object_or_404(Registration, pk=pk)
        new_status = request.data.get('status')
        valid      = [s[0] for s in Registration.Status.choices]
        if new_status not in valid:
            return Response({'detail': f'Invalid status. Choose from: {valid}'}, status=400)
        reg.status = new_status
        reg.save(update_fields=['status', 'updated_at'])
        return Response({'detail': f'Registration status updated to "{new_status}".'})


class AdminMarkAttendanceView(APIView):
    """
    POST /api/v1/registrations/admin/attendance/
    Mark a batch of registrations as attended.
    Body: { "registration_ids": [1, 2, 3] }
    """
    permission_classes = [IsAdminUser]

    def post(self, request):
        ids = request.data.get('registration_ids', [])
        if not ids:
            return Response({'detail': 'No registration IDs provided.'}, status=400)
        updated = Registration.objects.filter(
            pk__in=ids, status=Registration.Status.CONFIRMED
        ).update(status=Registration.Status.ATTENDED)
        return Response({'detail': f'{updated} registrations marked as attended.'})
