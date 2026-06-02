# =============================================================================
# predict_sensor.py  –  Live Prediction from ESP32 Sensor Readings
# Run this AFTER training the model with water_quality_model.py
# =============================================================================

from water_quality_model import predict_water_quality

# ── Replace these values with real readings from your ESP32 sensors ──────────
result = predict_water_quality(
    ph               = 7.2,    # pH sensor
    turbidity        = 2.5,    # Turbidity sensor (NTU)
    temperature      = 24.0,   # Temperature sensor (°C)
    dissolved_oxygen = 7.8,    # DO sensor (mg/L)
    conductivity     = 450.0,  # Conductivity / EC sensor (µS/cm)
    nitrate          = 8.0,    # Nitrate sensor (mg/L)
    model_dir        = "model_outputs"
)

# Use result["prediction"] in your ESP32 / MQTT pipeline
print("\nUse this in your IoT pipeline:", result["prediction"])
