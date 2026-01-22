import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Cấu hình chung cho ứng dụng"""
    
    # Flask config
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://postgres:postgres@localhost/smartrent_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    #
    # Session
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # JWT
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    
    # Upload
    UPLOAD_FOLDER = 'app/static/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max
    
    # Maps - Sử dụng OpenStreetMap (MIỄN PHÍ)
    # Leaflet.js + OpenStreetMap - không cần API key
    # Routing: Leaflet Routing Machine + OSRM (miễn phí)
    
    # Payment - Tạm thời chỉ dùng ví nội bộ (MIỄN PHÍ)
    # Không cần Stripe hay payment gateway bên ngoài
    ENABLE_EXTERNAL_PAYMENT = os.environ.get('ENABLE_EXTERNAL_PAYMENT', 'false').lower() == 'true'

    # Firebase / Firestore
    FIREBASE_ENABLED = os.environ.get('FIREBASE_ENABLED', 'true').lower() == 'true'
    FIREBASE_PROJECT_ID = os.environ.get('FIREBASE_PROJECT_ID', 'smartrent-6eadb')
    FIREBASE_CREDENTIALS_PATH = os.environ.get('FIREBASE_CREDENTIALS_PATH', 'smartrent-firebase-credentials.json')
    
    # MQTT Broker (for IoT devices)
    MQTT_BROKER_URL = os.environ.get('MQTT_BROKER_URL', 'localhost')
    MQTT_BROKER_PORT = int(os.environ.get('MQTT_BROKER_PORT', 1883))
    MQTT_USERNAME = os.environ.get('MQTT_USERNAME', '')
    MQTT_PASSWORD = os.environ.get('MQTT_PASSWORD', '')
    
    # Email config (for notifications)
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')
    
    # Geofencing
    DEFAULT_GEOFENCE_RADIUS = 50  # km
    
    # Auto-release expired bookings
    ENABLE_AUTO_RELEASE = os.environ.get('ENABLE_AUTO_RELEASE', 'true').lower() == 'true'
    AUTO_RELEASE_TIMEOUT_MINUTES = int(os.environ.get('AUTO_RELEASE_TIMEOUT_MINUTES', 5))
    
    # Vehicle pricing (VND per minute)
    BIKE_PRICE_PER_MINUTE = 500
    MOTORBIKE_PRICE_PER_MINUTE = 2000
    CAR_PRICE_PER_MINUTE = 5000
    
    # Admin
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@smartrent.com')


class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    DEBUG = False
    TESTING = False


class TestingConfig(Config):
    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
