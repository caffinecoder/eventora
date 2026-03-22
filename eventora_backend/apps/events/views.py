"""
events/views.py
Event CRUD + category listing.
"""

from rest_framework import generics, filters, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404

from .models import Event, Category
from .serializers import EventListSerializer, EventDetailSerializer, CategorySerializer
from apps.accounts.permissions import IsAdminUser, IsAdminOrReadOnly


# ── Categories ────────────────────────────────────────────────────────────────

class CategoryListView(generics.ListCreateAPIView):
    """
    GET  /api/v1/events/categories/   — List all categories (public)
    POST /api/v1/events/categories/   — Create category (admin only)
    """
    queryset           = Category.objects.all()
    serializer_class   = CategorySerializer

    def get_permissions(self):
        # GET is public so the dropdown loads for everyone
        # POST requires admin
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAdminUser()]


# ── Events ────────────────────────────────────────────────────────────────────

class EventListView(generics.ListAPIView):
    serializer_class   = EventListSerializer
    permission_classes = [AllowAny]
    filter_backends    = [filters.SearchFilter, filters.OrderingFilter]
    search_fields      = ['title', 'description', 'venue']
    ordering_fields    = ['event_date', 'registration_fee', 'created_at']
    ordering           = ['event_date']

    def get_queryset(self):
        queryset = Event.objects.filter(status=Event.Status.OPEN).select_related('category')
        category = self.request.query_params.get('category')
        dept     = self.request.query_params.get('department')
        if category:
            queryset = queryset.filter(category__slug=category)
        if dept:
            queryset = queryset.filter(department__iexact=dept)
        return queryset


class EventDetailView(generics.RetrieveAPIView):
    serializer_class   = EventDetailSerializer
    permission_classes = [AllowAny]
    lookup_field       = 'slug'
    queryset           = Event.objects.select_related('category', 'created_by')


# ── Admin Event CRUD ──────────────────────────────────────────────────────────

class AdminEventListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAdminUser]
    filter_backends    = [filters.SearchFilter, filters.OrderingFilter]
    search_fields      = ['title', 'venue', 'department']
    ordering_fields    = ['event_date', 'created_at', 'status']
    ordering           = ['-created_at']

    def get_queryset(self):
        queryset = Event.objects.select_related('category', 'created_by')
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        return queryset

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return EventListSerializer
        return EventDetailSerializer


class AdminEventDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAdminUser]
    serializer_class   = EventDetailSerializer
    queryset           = Event.objects.select_related('category', 'created_by')


class AdminEventStatusView(APIView):
    permission_classes = [IsAdminUser]

    def patch(self, request, pk):
        event      = get_object_or_404(Event, pk=pk)
        new_status = request.data.get('status')
        valid      = [s[0] for s in Event.Status.choices]
        if new_status not in valid:
            return Response(
                {'detail': f'Invalid status. Choose from: {valid}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        event.status = new_status
        event.save(update_fields=['status', 'updated_at'])
        return Response({'detail': f'Event status updated to "{new_status}".'})


class AdminDashboardStatsView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        from apps.registrations.models import Registration
        from apps.payments.models import Payment
        from django.db.models import Sum

        return Response({
            'total_events':        Event.objects.count(),
            'open_events':         Event.objects.filter(status='open').count(),
            'total_registrations': Registration.objects.count(),
            'confirmed_registrations': Registration.objects.filter(status='confirmed').count(),
            'total_revenue':       Payment.objects.filter(
                                       status='success'
                                   ).aggregate(total=Sum('amount'))['total'] or 0,
        })