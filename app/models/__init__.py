from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model, UserMixin):
    """Model người dùng"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    role = db.Column(db.String(20), default='customer')  # customer, admin, operator
    
    # Wallet & Payment
    wallet_balance = db.Column(db.Float, default=0.0)
    
    # Location
    current_latitude = db.Column(db.Float)
    current_longitude = db.Column(db.Float)
    
    # Verification
    is_verified = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    bookings = db.relationship('Booking', back_populates='user', lazy='dynamic')
    trips = db.relationship('Trip', back_populates='user', lazy='dynamic')
    payments = db.relationship('Payment', back_populates='user', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'


class Vehicle(db.Model):
    """Model phương tiện"""
    __tablename__ = 'vehicles'
    
    id = db.Column(db.Integer, primary_key=True)
    vehicle_code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    vehicle_type = db.Column(db.String(20), nullable=False)  # bike, motorbike, car
    
    # Basic Info
    brand = db.Column(db.String(50))
    model = db.Column(db.String(50))
    license_plate = db.Column(db.String(20), unique=True)
    color = db.Column(db.String(30))
    year = db.Column(db.Integer)
    
    # Location (GIS)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    address = db.Column(db.String(255))
    
    # Status
    status = db.Column(db.String(20), default='available')  # available, in_use, maintenance, offline
    is_locked = db.Column(db.Boolean, default=True)
    
    # IoT Data (Telematics)
    battery_level = db.Column(db.Float)  # 0-100%
    fuel_level = db.Column(db.Float)  # 0-100%
    tire_pressure = db.Column(db.Float)  # PSI
    odometer = db.Column(db.Float, default=0.0)  # km
    
    # Smart Lock
    qr_code = db.Column(db.String(255), unique=True)
    lock_status = db.Column(db.String(20), default='locked')  # locked, unlocked
    
    # Pricing
    price_per_minute = db.Column(db.Float, nullable=False)
    
    # Geofencing
    geofence_enabled = db.Column(db.Boolean, default=True)
    geofence_center_lat = db.Column(db.Float)
    geofence_center_lng = db.Column(db.Float)
    geofence_radius = db.Column(db.Float)  # km
    
    # Maintenance
    last_maintenance_date = db.Column(db.DateTime)
    next_maintenance_date = db.Column(db.DateTime)
    maintenance_interval_km = db.Column(db.Float, default=1000)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    bookings = db.relationship('Booking', back_populates='vehicle', lazy='dynamic')
    trips = db.relationship('Trip', back_populates='vehicle', lazy='dynamic')
    maintenances = db.relationship('Maintenance', back_populates='vehicle', lazy='dynamic')
    iot_logs = db.relationship('IoTLog', back_populates='vehicle', lazy='dynamic')
    
    def __repr__(self):
        return f'<Vehicle {self.vehicle_code}>'


class Booking(db.Model):
    """Model đặt xe"""
    __tablename__ = 'bookings'
    
    id = db.Column(db.Integer, primary_key=True)
    booking_code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    
    # Foreign Keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicles.id'), nullable=False)
    
    # Status
    status = db.Column(db.String(20), default='pending')  # pending, confirmed, completed, cancelled
    
    # Time
    booking_time = db.Column(db.DateTime, default=datetime.utcnow)
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', back_populates='bookings')
    vehicle = db.relationship('Vehicle', back_populates='bookings')
    trip = db.relationship('Trip', back_populates='booking', uselist=False)
    
    def __repr__(self):
        return f'<Booking {self.booking_code}>'


class Trip(db.Model):
    """Model chuyến đi"""
    __tablename__ = 'trips'
    
    id = db.Column(db.Integer, primary_key=True)
    trip_code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    
    # Foreign Keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicles.id'), nullable=False)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'))
    
    # Location
    start_latitude = db.Column(db.Float)
    start_longitude = db.Column(db.Float)
    start_address = db.Column(db.String(255))
    
    end_latitude = db.Column(db.Float)
    end_longitude = db.Column(db.Float)
    end_address = db.Column(db.String(255))
    
    # Time
    start_time = db.Column(db.DateTime)  # Nullable, sẽ set khi quét QR
    end_time = db.Column(db.DateTime)
    duration_minutes = db.Column(db.Float)
    
    # Trip Details
    distance_km = db.Column(db.Float)
    route_json = db.Column(db.Text)  # JSON data of route coordinates
    
    # Cost
    total_cost = db.Column(db.Float)
    
    # Feedback
    rating = db.Column(db.Integer)  # 1-5 stars
    feedback = db.Column(db.Text)
    
    # Status
    status = db.Column(db.String(20), default='in_progress')  # in_progress, completed, cancelled
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', back_populates='trips')
    vehicle = db.relationship('Vehicle', back_populates='trips')
    booking = db.relationship('Booking', back_populates='trip')
    payment = db.relationship('Payment', back_populates='trip', uselist=False)
    
    def __repr__(self):
        return f'<Trip {self.trip_code}>'


class Payment(db.Model):
    """Model thanh toán"""
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    payment_code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    
    # Foreign Keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    trip_id = db.Column(db.Integer, db.ForeignKey('trips.id'))
    
    # Payment Info
    amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(50))  # wallet, credit_card, stripe, momo
    payment_status = db.Column(db.String(20), default='pending')  # pending, completed, failed, refunded
    
    # Transaction
    transaction_id = db.Column(db.String(100))
    transaction_date = db.Column(db.DateTime)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', back_populates='payments')
    trip = db.relationship('Trip', back_populates='payment')
    
    def __repr__(self):
        return f'<Payment {self.payment_code}>'


class Maintenance(db.Model):
    """Model bảo trì"""
    __tablename__ = 'maintenances'
    
    id = db.Column(db.Integer, primary_key=True)
    maintenance_code = db.Column(db.String(50), unique=True, nullable=False)
    
    # Foreign Keys
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicles.id'), nullable=False)
    
    # Maintenance Info
    maintenance_type = db.Column(db.String(50))  # routine, repair, emergency
    description = db.Column(db.Text)
    cost = db.Column(db.Float)
    
    # Status
    status = db.Column(db.String(20), default='scheduled')  # scheduled, in_progress, completed
    
    # Time
    scheduled_date = db.Column(db.DateTime)
    completed_date = db.Column(db.DateTime)
    
    # Technician
    technician_name = db.Column(db.String(100))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    vehicle = db.relationship('Vehicle', back_populates='maintenances')
    
    def __repr__(self):
        return f'<Maintenance {self.maintenance_code}>'


class EmergencyAlert(db.Model):
    """Model cảnh báo khẩn cấp (eCall)"""
    __tablename__ = 'emergency_alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    alert_code = db.Column(db.String(50), unique=True, nullable=False)
    
    # Foreign Keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicles.id'))
    trip_id = db.Column(db.Integer, db.ForeignKey('trips.id'))
    
    # Alert Info
    alert_type = db.Column(db.String(50))  # accident, breakdown, theft, medical
    severity = db.Column(db.String(20))  # low, medium, high, critical
    description = db.Column(db.Text)
    
    # Location
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    address = db.Column(db.String(255))
    
    # Status
    status = db.Column(db.String(20), default='open')  # open, acknowledged, resolved, closed
    
    # Response
    response_team = db.Column(db.String(100))
    response_time = db.Column(db.DateTime)
    resolution_time = db.Column(db.DateTime)
    resolution_notes = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='emergency_alerts')
    vehicle = db.relationship('Vehicle', backref='emergency_alerts')
    trip = db.relationship('Trip', backref='emergency_alerts')
    
    def __repr__(self):
        return f'<EmergencyAlert {self.alert_code}>'


class IoTLog(db.Model):
    """Model log dữ liệu IoT từ xe"""
    __tablename__ = 'iot_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign Keys
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicles.id'), nullable=False)
    
    # Sensor Data
    battery_level = db.Column(db.Float)
    fuel_level = db.Column(db.Float)
    tire_pressure = db.Column(db.Float)
    speed = db.Column(db.Float)  # km/h
    
    # Location
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    
    # Engine Status
    engine_status = db.Column(db.String(20))  # on, off
    temperature = db.Column(db.Float)  # Celsius
    
    # Geofence Violation
    geofence_violation = db.Column(db.Boolean, default=False)
    
    # Timestamp
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    vehicle = db.relationship('Vehicle', back_populates='iot_logs')
    
    def __repr__(self):
        return f'<IoTLog Vehicle:{self.vehicle_id} at {self.timestamp}>'


class Notification(db.Model):
    """Model thông báo chung cho người dùng"""
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign Keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Notification Info
    type = db.Column(db.String(50), nullable=False)  # payment, trip, emergency, system, promotion
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    icon = db.Column(db.String(50))  # fa icon class
    color = db.Column(db.String(20))  # success, danger, warning, info, primary
    
    # Related IDs (optional)
    related_id = db.Column(db.Integer)  # ID của payment, trip, emergency alert, etc.
    related_type = db.Column(db.String(50))  # payment, trip, emergency_alert, etc.
    
    # Link/Action
    action_url = db.Column(db.String(255))  # URL to redirect when clicked
    
    # Status
    is_read = db.Column(db.Boolean, default=False)
    is_deleted = db.Column(db.Boolean, default=False)
    
    # Timestamp
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    read_at = db.Column(db.DateTime)
    
    # Relationships
    user = db.relationship('User', backref='notifications')
    
    def __repr__(self):
        return f'<Notification {self.type}: {self.title}>'


class HazardZone(db.Model):
    """Model vùng nguy hiểm (ITS Incident Management)"""
    __tablename__ = 'hazard_zones'
    
    id = db.Column(db.Integer, primary_key=True)
    zone_code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    
    # Zone Info
    zone_name = db.Column(db.String(200), nullable=False)
    hazard_type = db.Column(db.String(50), nullable=False)  # flood, landslide, accident, construction, event
    severity = db.Column(db.String(20), default='medium')  # low, medium, high, critical
    description = db.Column(db.Text)
    warning_message = db.Column(db.String(500))
    
    # Polygon Coordinates (GeoJSON format)
    polygon_coordinates = db.Column(db.JSON, nullable=False)  # Array of [lat, lng] points
    
    # Bounding Box (for faster filtering)
    min_latitude = db.Column(db.Float, nullable=False, index=True)
    max_latitude = db.Column(db.Float, nullable=False, index=True)
    min_longitude = db.Column(db.Float, nullable=False, index=True)
    max_longitude = db.Column(db.Float, nullable=False, index=True)
    
    # Visual
    color = db.Column(db.String(20), default='#ff0000')  # Hex color for map display
    
    # Status & Duration
    is_active = db.Column(db.Boolean, default=True, index=True)
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    
    # Statistics
    warning_count = db.Column(db.Integer, default=0)  # Number of times users were warned
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))  # Admin who created
    
    # Relationships
    creator = db.relationship('User', backref='hazard_zones_created')
    
    def __repr__(self):
        return f'<HazardZone {self.zone_code}: {self.zone_name}>'


class RouteHistory(db.Model):
    """
    Model lưu lịch sử routes đã plan (for Analytics)
    Không conflict với Trip model (Trip = actual rental, RouteHistory = planning only)
    """
    __tablename__ = 'route_history'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # User info
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Route info
    start_address = db.Column(db.String(500))
    end_address = db.Column(db.String(500))
    start_lat = db.Column(db.Float, nullable=False)
    start_lng = db.Column(db.Float, nullable=False)
    end_lat = db.Column(db.Float, nullable=False)
    end_lng = db.Column(db.Float, nullable=False)
    
    # Route metrics
    distance_km = db.Column(db.Float)
    duration_minutes = db.Column(db.Float)
    estimated_cost = db.Column(db.Integer)
    
    # Hazard info
    hazards_detected = db.Column(db.Integer, default=0)
    hazard_zones_passed = db.Column(db.JSON)  # List of zone IDs
    alternative_route_chosen = db.Column(db.Boolean, default=False)
    
    # Algorithm used
    routing_algorithm = db.Column(db.String(50))  # 'OSRM', 'A*', etc.
    
    # Timestamp
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Relationship
    user = db.relationship('User', backref='route_plans')
    
    def __repr__(self):
        return f'<RouteHistory {self.id}: {self.start_address} -> {self.end_address}>'
