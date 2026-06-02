"""
views.py — API Views
====================
SensorDataView  : POST /api/data/    — receives sensor readings, runs ML prediction
HistoryView     : GET  /api/history/ — returns last 50 readings as JSON
LatestView      : GET  /api/latest/  — returns the most recent reading
StatsView       : GET  /api/stats/   — summary statistics
DashboardView   : GET  /            — renders the HTML dashboard
"""

import logging
from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Count, Avg
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import WaterData
from .serializers import WaterDataSerializer
from .ml.predictor import predict

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/data/
# Receives sensor JSON from ESP32, runs ML prediction, saves to DB
# ─────────────────────────────────────────────────────────────────────────────

class SensorDataView(APIView):
    """
    Endpoint for sensor data input.

    Expected JSON payload:
        {
            "ph":        7.2,
            "turbidity": 2.5,    (optional)
            "temperature": 24.0, (optional)
            "timestamp": "2024-01-15T10:30:00"   (optional)
        }

    Response (200 OK):
        {
            "prediction":    "Neutral",
            "confidence":    "92.4%",
            "probabilities": {"Acidic": "1.2%", "Neutral": "92.4%", "Basic": "6.4%"},
            "status":        "processed"
        }
    """

    def post(self, request):
        # Extract data
        ph = request.data.get('ph')
        turbidity = request.data.get('turbidity', 0.0)
        temperature = request.data.get('temperature', 25.0)

        if ph is None:
            return Response(
                {'error': 'pH value is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # ── Run ML prediction ─────────────────────────────────────────────────
        try:
            ml_result = predict(ph=float(ph))
        except FileNotFoundError as e:
            logger.error(f"ML model not found: {e}")
            return Response(
                {'error': 'ML model not available. Run water_quality_model.py first.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except Exception as e:
            logger.exception(f"Prediction failed: {e}")
            return Response(
                {'error': 'Prediction failed', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        logger.info(f"Prediction: {ml_result['prediction']} ({ml_result['confidence']}) | pH={ph}")

        # ── Save to database ──────────────────────────────────────────────────
        try:
            data = WaterData.objects.create(
                ph=ph,
                turbidity=turbidity,
                temperature=temperature,
                prediction=ml_result['prediction'],
                confidence=ml_result['confidence']
            )
            logger.info(f"Saved reading ID {data.id}")
        except Exception as e:
            logger.exception(f"Database save failed: {e}")
            return Response(
                {'error': 'Database save failed', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # ── Return result ────────────────────────────────────────────
        return Response({
            'prediction': ml_result['prediction'],
            'confidence': ml_result['confidence'],
            'probabilities': ml_result['probabilities'],
            'status': 'processed'
        })


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/history/
# Returns last 50 readings as JSON for dashboard charts & table
# ─────────────────────────────────────────────────────────────────────────────

class HistoryView(APIView):
    """Returns last 50 readings."""

    def get(self, request):
        limit = int(request.GET.get('limit', 50))
        readings = WaterData.objects.all()[:limit]
        serializer = WaterDataSerializer(readings, many=True)
        return Response({
            'count': readings.count(),
            'results': serializer.data,
        })


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/latest/
# Returns the single most recent reading
# ─────────────────────────────────────────────────────────────────────────────

class LatestView(APIView):
    """Returns the most recent reading."""

    def get(self, request):
        try:
            latest = WaterData.objects.latest('created_at')
            serializer = WaterDataSerializer(latest)
            return Response(serializer.data)
        except WaterData.DoesNotExist:
            return Response({'message': 'No readings available'}, status=status.HTTP_404_NOT_FOUND)


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/stats/
# Summary statistics for the dashboard header cards
# ─────────────────────────────────────────────────────────────────────────────

class StatsView(APIView):
    """Returns summary statistics."""

    def get(self, request):
        total = WaterData.objects.count()
        hazard = WaterData.objects.filter(prediction='Hazard').count()
        good = WaterData.objects.filter(prediction='Good').count()
        avg_ph = WaterData.objects.aggregate(avg=Avg('ph'))['avg']
        return Response({
            'total': total,
            'hazard': hazard,
            'good': good,
            'avg_ph': round(avg_ph, 2) if avg_ph else None
        })


# ─────────────────────────────────────────────────────────────────────────────
# GET /
# Renders the HTML dashboard page
# ─────────────────────────────────────────────────────────────────────────────

def dashboard_view(request):
    """Render the main monitoring dashboard."""
    try:
        latest = WaterData.objects.latest('created_at')
    except WaterData.DoesNotExist:
        latest = None

    recent = WaterData.objects.all()[:20]
    context = {
        'latest': latest,
        'recent': recent,
    }
    return render(request, 'dashboard.html', context)
