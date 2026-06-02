# AquaWatch — Smart Water Quality Monitoring System
## Setup & Run Instructions (Antigravity / VS Code)

---

## 📁 Project Structure

```
smart water quality monitoring system using iot and ml/
├── water_monitor/               ← Django project (run from here)
│   ├── manage.py
│   ├── requirements_django.txt
│   ├── db.sqlite3               ← auto-created after migrate
│   ├── water_monitor/           ← Django settings
│   │   ├── settings.py
│   │   └── urls.py
│   ├── api/                     ← Main Django app
│   │   ├── models.py            ← WaterData model
│   │   ├── serializers.py
│   │   ├── views.py             ← REST API + dashboard view
│   │   ├── urls.py              ← /api/* routes
│   │   ├── dashboard_urls.py    ← / route
│   │   ├── admin.py
│   │   └── ml/
│   │       └── predictor.py     ← Loads model_outputs/ RF model
│   ├── templates/
│   │   └── dashboard.html       ← Premium dashboard UI
│   ├── static/
│   │   ├── css/style.css
│   │   └── js/dashboard.js
│   └── esp32_sketch/
│       └── esp32_sketch.ino     ← Arduino code for ESP32
├── model_outputs/               ← Pre-trained ML model files
│   ├── water_quality_rf_model.joblib
│   ├── label_encoder.joblib
│   └── feature_names.joblib
└── water_quality_model.py       ← Original ML training script
```

---

## ⚡ Quick Start (3 Commands)

> Run all commands from the **`water_monitor/`** folder

### Step 1 — Activate the virtual environment
```powershell
# From the project root (smart water quality monitoring system using iot and ml)
.venv\Scripts\activate
```

### Step 2 — Apply migrations (first time only)
```powershell
# From water_monitor/
python manage.py migrate
```

### Step 3 — Start the server
```powershell
# From water_monitor/
python manage.py runserver
```

Then open → **http://127.0.0.1:8000/**

---

## 🌐 API Endpoints

| Method | URL | Description |
|--------|-----|-------------|
| `POST` | `/api/data/` | Receive ESP32 sensor reading + run ML prediction |
| `GET`  | `/api/history/?limit=50` | Last N readings |
| `GET`  | `/api/latest/` | Most recent single reading |
| `GET`  | `/api/stats/`  | Safe/Warning/Hazard counts + averages |
| `GET`  | `/` | Live dashboard (HTML) |
| `GET`  | `/admin/` | Django admin panel |

---

## 🧪 Test the API (PowerShell curl)

```powershell
# Safe reading
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/data/" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"ph": 7.2, "turbidity": 2.5, "temperature": 24.0}'

# Warning reading
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/data/" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"ph": 6.0, "turbidity": 6.0, "temperature": 28.0}'

# Hazard reading
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/data/" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"ph": 4.5, "turbidity": 50.0, "temperature": 35.0}'
```

Or use the **⚡ Simulate ESP32 Reading** button on the dashboard.

---

## 🔌 ESP32 Hardware Setup

### Required Libraries (Arduino IDE)
Install via **Sketch → Include Library → Manage Libraries**:
- `ArduinoJson` by Benoit Blanchon (v6.x)
- `OneWire` by Paul Stoffregen
- `DallasTemperature` by Miles Burton

### Configuration (esp32_sketch.ino)
```cpp
const char* WIFI_SSID     = "YOUR_WIFI_SSID";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";
const char* SERVER_URL    = "http://YOUR_PC_IP:8000/api/data/";
```

> ⚠️ Replace `YOUR_PC_IP` with the IP of the machine running Django.
> Use `ipconfig` in PowerShell to find it. Example: `192.168.1.105`

### Wiring
| Sensor | ESP32 Pin |
|--------|-----------|
| pH Sensor OUT | GPIO 34 (ADC) |
| Turbidity OUT | GPIO 35 (ADC) |
| DS18B20 DATA  | GPIO 4 (with 4.7kΩ pull-up to 3.3V) |
| DS18B20 VCC   | 3.3V |
| DS18B20 GND   | GND |

---

## 🤖 Retrain the ML Model (optional)

If you want to retrain using updated data:
```powershell
# From project root
.venv\Scripts\activate
python water_quality_model.py
```
The new model files will be saved to `model_outputs/` and picked up automatically by Django.

---

## 🗄️ Admin Panel

Create a superuser to access `/admin/`:
```powershell
python manage.py createsuperuser
```

---

## 🔄 System Flow

```
pH Sensor    ┐
Turbidity    ├─→ ESP32 → POST /api/data/ → Django REST API
Temperature  ┘                                   │
                                                 ▼
                                        ML Predictor (RF Model)
                                                 │
                                       ┌─────────┴──────────┐
                                       │  SQLite Database   │
                                       │   (WaterData)      │
                                       └─────────┬──────────┘
                                                 │
                                    Web Dashboard (http://localhost:8000)
                                   ┌─────────────────────────────────────┐
                                   │  Status Ring  |  Gauge Cards        │
                                   │  Chart.js     |  History Table      │
                                   │  Auto-refresh every 10 seconds      │
                                   └─────────────────────────────────────┘
```
