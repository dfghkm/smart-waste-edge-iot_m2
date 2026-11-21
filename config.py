# Конфігурація периферійних вузлів, меж сенсорів та хмарного середовища

CONTAINERS = [
    {"id": 1, "location": "Вул. Політехнічна, 14", "capacity_l": 1100, "rate": 1.45},
    {"id": 2, "location": "Пр. Перемоги, 37",       "capacity_l": 1100, "rate": 1.85},
    {"id": 3, "location": "Вул. Борщагівська, 115", "capacity_l": 2400, "rate": 1.15},
]

SENSOR_LIMITS = {
    "fill_level":  (0.0, 100.0),
    "temperature": (-20.0, 65.0),
    "humidity":    (0.0, 100.0),
    "methane_ppm": (0.0, 2000.0),
}

COLLECTION_THRESHOLD_PCT = 85.0
METHANE_ALERT_PPM = 800.0
DB_PATH = "data/smart_waste_edge.db"
REPORT_IMAGE_PATH = "output/waste_analytics_report.png"

# URL бази даних Firebase Realtime Database
FIREBASE_DB_URL = "https://smart-waste-iiot-default-rtdb.europe-west1.firebasedatabase.app"