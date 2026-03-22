"""
events/urls.py
"""

from django.urls import path
from .views import (
    CategoryListView,
    EventListView,
    EventDetailView,
    AdminEventListCreateView,
    AdminEventDetailView,
    AdminEventStatusView,
    AdminDashboardStatsView,
)

urlpatterns = [
    # Public
    path('',                       EventListView.as_view(),            name='event_list'),
    path('categories/',            CategoryListView.as_view(),         name='category_list'),

    # Admin — exact paths first, then dynamic
    path('admin/',                 AdminEventListCreateView.as_view(), name='admin_event_list'),
    path('admin/stats/',           AdminDashboardStatsView.as_view(),  name='admin_stats'),
    path('admin/<int:pk>/',        AdminEventDetailView.as_view(),     name='admin_event_detail'),
    path('admin/<int:pk>/status/', AdminEventStatusView.as_view(),     name='admin_event_status'),

    # Public detail — keep this LAST since it catches any slug
    path('<slug:slug>/',           EventDetailView.as_view(),          name='event_detail'),
]