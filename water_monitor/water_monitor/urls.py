"""
Root URL Configuration — Smart Water Quality Monitoring System
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # API endpoints — consumed by ESP32 and dashboard frontend
    path('api/', include('api.urls')),

    # Dashboard — served at root URL
    path('', include('api.dashboard_urls')),
] + static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0] if settings.STATICFILES_DIRS else None)
