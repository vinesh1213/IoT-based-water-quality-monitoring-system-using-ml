"""
api/dashboard_urls.py — URL routing for the HTML dashboard
"""

from django.urls import path
from .views import dashboard_view

urlpatterns = [
    path('', dashboard_view, name='dashboard'),
]
