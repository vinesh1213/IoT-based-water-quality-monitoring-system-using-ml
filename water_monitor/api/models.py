"""
models.py — Database models
===========================
WaterData model for storing sensor readings and ML predictions.
"""

from django.db import models


class WaterData(models.Model):
    ph          = models.FloatField()
    turbidity   = models.FloatField()
    temperature = models.FloatField()
    prediction  = models.CharField(max_length=20)
    confidence  = models.CharField(max_length=10, blank=True, null=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"WaterData {self.id}: pH={self.ph}, pred={self.prediction}"
