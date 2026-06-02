"""
api/urls.py — REST API endpoint URLs
"""

from django.urls import path
from . import views

urlpatterns = [
    # POST: ESP32 sends sensor data — /api/data/
    path('data/', views.SensorDataView.as_view(), name='sensor-data'),

    # GET: Historical readings — /api/history/?limit=50
    path('history/', views.HistoryView.as_view(), name='history'),

    # GET: Latest single reading — /api/latest/
    path('latest/', views.LatestView.as_view(), name='latest'),

    # GET: Aggregated statistics — /api/stats/
    path('stats/', views.StatsView.as_view(), name='stats'),
]
