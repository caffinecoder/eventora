"""
Eventora — Root URL Configuration
All API routes are prefixed with /api/v1/
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Django admin
    path('admin/', admin.site.urls),

    # API v1
    path('api/v1/auth/',          include('apps.accounts.urls')),
    path('api/v1/events/',        include('apps.events.urls')),
    path('api/v1/registrations/', include('apps.registrations.urls')),
    path('api/v1/payments/',      include('apps.payments.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
