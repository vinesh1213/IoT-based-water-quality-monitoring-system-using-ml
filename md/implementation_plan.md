# Smart Water Quality Monitoring System — Implementation Plan

A complete Django-based backend + dashboard for an ESP32 IoT water quality sensor network. The system receives sensor data via HTTP POST, runs ML prediction using the existing trained Random Forest model, stores results in SQLite, and displays everything on a premium live dashboard.

## Proposed Changes

### Django Project Structure

```
smart water quality monitoring system using iot and ml/
└── water_monitor/               ← Django project root [NEW]
    ├── manage.py
    ├── requirements_django.txt
    ├── water_monitor/           ← Django settings package
    │   ├── __init__.py
    │   ├── settings.py
    │   ├── urls.py
    │   └── wsgi.py
    ├── api/                     ← Django app
    │   ├── __init__.py
    │   ├── models.py
    │   ├── serializers.py
    │   ├── views.py
    │   ├── urls.py
    │   ├── ml/
    │   │   ├── __init__.py
    │   │   └── predictor.py     ← Loads RF model, runs prediction
    │   └── migrations/
    ├── templates/
    │   └── dashboard.html       ← Premium dashboard UI
    └── static/
        ├── css/style.css
        └── js/dashboard.js
```

The existing `model_outputs/` folder will be referenced directly by the predictor.

---

### Component 1: Django Setup

#### [NEW] `water_monitor/manage.py`
Standard Django manage.py entry point.

#### [NEW] `water_monitor/water_monitor/settings.py`
- Install: `rest_framework`, `api`, `corsheaders`
- DB: SQLite (`db.sqlite3`)
- Static/template dirs configured
- CORS allow-all for ESP32 POSTs

#### [NEW] `water_monitor/water_monitor/urls.py`
- Routes `/api/` → api app urls
- Routes `/` → dashboard view

---

### Component 2: Database Model

#### [NEW] `water_monitor/api/models.py`
```python
class WaterData(models.Model):
    ph          = models.FloatField()
    turbidity   = models.FloatField()
    temperature = models.FloatField()
    prediction  = models.CharField(max_length=20)
    created_at  = models.DateTimeField(auto_now_add=True)
```

---

### Component 3: ML Integration

#### [NEW] `water_monitor/api/ml/predictor.py`
- Loads [water_quality_rf_model.joblib](file:///c:/Users/Bubby/Downloads/smart%20water%20quality%20monitoring%20system%20using%20iot%20and%20ml/model_outputs/water_quality_rf_model.joblib), [label_encoder.joblib](file:///c:/Users/Bubby/Downloads/smart%20water%20quality%20monitoring%20system%20using%20iot%20and%20ml/model_outputs/label_encoder.joblib), [feature_names.joblib](file:///c:/Users/Bubby/Downloads/smart%20water%20quality%20monitoring%20system%20using%20iot%20and%20ml/model_outputs/feature_names.joblib) from `model_outputs/`
- Accepts: `ph`, `turbidity`, `temperature` (plus defaults for DO, conductivity, nitrate)
- Returns: predicted class string (`Safe` / `Warning` / `Hazard`)

---

### Component 4: REST API

#### [NEW] `water_monitor/api/serializers.py`
`WaterDataSerializer` for the WaterData model.

#### [NEW] `water_monitor/api/views.py`
- `SensorDataView` (POST `/api/data/`): receives ESP32 JSON → runs ML → saves to DB → returns prediction
- `HistoryView` (GET `/api/history/`): returns last 50 readings as JSON

#### [NEW] `water_monitor/api/urls.py`
Routes for both views.

---

### Component 5: Dashboard (SKILL.md — Premium Design)

**Aesthetic Direction**: Dark industrial/deep-ocean theme. Typeface: `Orbitron` (display) + `Space Mono` (mono data), sharp cyan-on-dark color palette with animated water-ripple status rings. Grid-breaking asymmetric layout with animated canvas background.

#### [NEW] `water_monitor/templates/dashboard.html`
- Live water quality status ring (color-coded)
- 3 sensor gauges: pH, Turbidity, Temperature
- Historical data table (last 20 readings)
- Line charts: pH over time, Turbidity over time (Chart.js)
- Auto-refreshes every 10 seconds via `fetch()` calls

#### [NEW] `water_monitor/static/css/style.css`
- CSS variables with deep-ocean dark palette
- Animated gradient backgrounds
- Glowing border cards with glassmorphism panels
- Animated status pulse rings

#### [NEW] `water_monitor/static/js/dashboard.js`
- Fetches `/api/history/` every 10s
- Updates charts and table dynamically
- Animates status indicator on reading change

---

### Component 6: ESP32 Arduino Sketch

#### [NEW] `water_monitor/esp32_sketch.ino`
Arduino C++ code for ESP32 that:
- Reads pH, turbidity, temperature sensors
- Posts JSON to Django API endpoint via HTTP POST

---

### Component 7: Django requirements + Instructions

#### [NEW] `water_monitor/requirements_django.txt`
```
django>=4.2
djangorestframework>=3.14
django-cors-headers>=4.3
joblib>=1.3
pandas>=2.0
scikit-learn>=1.3
numpy>=1.24
```

#### [NEW] `water_monitor/INSTRUCTIONS.md`
Step-by-step setup and run guide for Antigravity.

---

## Verification Plan

### Automated Tests
```bash
# From water_monitor/ directory
python manage.py test api
```
A basic API test will POST sensor data and check the response contains a prediction field.

### Manual Browser Verification
1. Start server: `python manage.py runserver` from `water_monitor/`
2. Open browser to `http://127.0.0.1:8000/`
3. POST test data using the built-in test button on the dashboard
4. Verify status indicator changes color, charts update, table shows new row

### API Endpoint Test (curl)
```bash
curl -X POST http://127.0.0.1:8000/api/data/ \
  -H "Content-Type: application/json" \
  -d "{\"ph\": 7.2, \"turbidity\": 2.5, \"temperature\": 24.0}"
```
Expected response: `{"prediction": "Safe", "confidence": "...", ...}`
