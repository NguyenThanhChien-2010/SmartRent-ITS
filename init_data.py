"""
Script tạo dữ liệu mẫu cho SmartRent ITS
Chạy: python init_data.py
"""

from app import create_app
from app.models import db, User, Vehicle
from app.utils.firebase_client import init_firebase
from app.utils.repositories import VehicleRepository
from datetime import datetime
import random

app = create_app()

with app.app_context():
    # Xóa dữ liệu cũ (nếu có)
    print("🗑️  Xóa dữ liệu cũ...")
    db.drop_all()
    db.create_all()
    
    # Tạo admin
    print("👤 Tạo tài khoản admin...")
    admin = User(
        username='admin',
        email='admin@smartrent.com',
        full_name='Administrator',
        phone='0900000000',
        role='admin',
        wallet_balance=10000000,
        is_verified=True,
        current_latitude=10.8231,
        current_longitude=106.6297
    )
    admin.set_password('admin123')
    db.session.add(admin)
    
    # Tạo user demo
    print("👤 Tạo tài khoản demo...")
    users_data = [
        {
            'username': 'demo',
            'email': 'demo@smartrent.com',
            'full_name': 'Nguyễn Văn Demo',
            'phone': '0901111111',
            'password': 'demo123',
            'balance': 500000
        },
        {
            'username': 'user1',
            'email': 'user1@smartrent.com',
            'full_name': 'Trần Thị A',
            'phone': '0902222222',
            'password': 'user123',
            'balance': 300000
        },
        {
            'username': 'user2',
            'email': 'user2@smartrent.com',
            'full_name': 'Lê Văn B',
            'phone': '0903333333',
            'password': 'user123',
            'balance': 200000
        }
    ]
    
    for user_data in users_data:
        user = User(
            username=user_data['username'],
            email=user_data['email'],
            full_name=user_data['full_name'],
            phone=user_data['phone'],
            role='customer',
            wallet_balance=user_data['balance'],
            is_verified=True,
            current_latitude=10.8231 + random.uniform(-0.01, 0.01),
            current_longitude=106.6297 + random.uniform(-0.01, 0.01)
        )
        user.set_password(user_data['password'])
        db.session.add(user)
    
    # Tạo xe đạp điện
    print("🚲 Tạo xe đạp điện...")
    bikes = [
        {
            'code': 'BIKE001',
            'brand': 'Giant',
            'model': 'Electric Pro',
            'color': 'Xanh',
            'lat': 10.8231,
            'lng': 106.6297
        },
        {
            'code': 'BIKE002',
            'brand': 'Trek',
            'model': 'E-Bike 2024',
            'color': 'Đỏ',
            'lat': 10.8241,
            'lng': 106.6287
        },
        {
            'code': 'BIKE003',
            'brand': 'Specialized',
            'model': 'Turbo Vado',
            'color': 'Đen',
            'lat': 10.8221,
            'lng': 106.6307
        },
        {
            'code': 'BIKE004',
            'brand': 'Cannondale',
            'model': 'Quick Neo',
            'color': 'Trắng',
            'lat': 10.8251,
            'lng': 106.6277
        },
        {
            'code': 'BIKE005',
            'brand': 'Scott',
            'model': 'E-Sub Sport',
            'color': 'Vàng',
            'lat': 10.8211,
            'lng': 106.6317
        }
    ]
    
    for bike in bikes:
        vehicle = Vehicle(
            vehicle_code=bike['code'],
            vehicle_type='bike',
            brand=bike['brand'],
            model=bike['model'],
            color=bike['color'],
            license_plate=None,
            year=2024,
            latitude=bike['lat'],
            longitude=bike['lng'],
            address='TP. Hồ Chí Minh',
            status='available',
            battery_level=random.randint(70, 100),
            price_per_minute=500,
            qr_code=f'QR{bike["code"]}',
            geofence_enabled=True,
            geofence_center_lat=10.8231,
            geofence_center_lng=106.6297,
            geofence_radius=10
        )
        db.session.add(vehicle)
    
    # Tạo xe máy
    print("🛵 Tạo xe máy...")
    motorbikes = [
        {
            'code': 'MOTOR001',
            'brand': 'Honda',
            'model': 'Vision 2024',
            'color': 'Đen',
            'plate': '51A-12345',
            'lat': 10.8241,
            'lng': 106.6307
        },
        {
            'code': 'MOTOR002',
            'brand': 'Yamaha',
            'model': 'Grande',
            'color': 'Xanh',
            'plate': '51B-67890',
            'lat': 10.8261,
            'lng': 106.6287
        },
        {
            'code': 'MOTOR003',
            'brand': 'Honda',
            'model': 'Lead 2024',
            'color': 'Trắng',
            'plate': '51C-11111',
            'lat': 10.8221,
            'lng': 106.6327
        },
        {
            'code': 'MOTOR004',
            'brand': 'Yamaha',
            'model': 'Janus',
            'color': 'Đỏ',
            'plate': '51D-22222',
            'lat': 10.8271,
            'lng': 106.6267
        },
        {
            'code': 'MOTOR005',
            'brand': 'Honda',
            'model': 'Air Blade',
            'color': 'Xám',
            'plate': '51E-33333',
            'lat': 10.8201,
            'lng': 106.6337
        }
    ]
    
    for motor in motorbikes:
        vehicle = Vehicle(
            vehicle_code=motor['code'],
            vehicle_type='motorbike',
            brand=motor['brand'],
            model=motor['model'],
            color=motor['color'],
            license_plate=motor['plate'],
            year=2024,
            latitude=motor['lat'],
            longitude=motor['lng'],
            address='TP. Hồ Chí Minh',
            status='available',
            battery_level=random.randint(80, 100),
            fuel_level=random.randint(60, 100),
            tire_pressure=32.0,
            price_per_minute=2000,
            qr_code=f'QR{motor["code"]}',
            geofence_enabled=True,
            geofence_center_lat=10.8231,
            geofence_center_lng=106.6297,
            geofence_radius=20
        )
        db.session.add(vehicle)
    
    # Tạo ô tô
    print("🚗 Tạo ô tô...")
    cars = [
        {
            'code': 'CAR001',
            'brand': 'Toyota',
            'model': 'Vios 2024',
            'color': 'Bạc',
            'plate': '51F-44444',
            'lat': 10.8251,
            'lng': 106.6317
        },
        {
            'code': 'CAR002',
            'brand': 'Honda',
            'model': 'City 2024',
            'color': 'Trắng',
            'plate': '51G-55555',
            'lat': 10.8281,
            'lng': 106.6257
        },
        {
            'code': 'CAR003',
            'brand': 'Mazda',
            'model': 'Mazda3 2024',
            'color': 'Đỏ',
            'plate': '51H-66666',
            'lat': 10.8191,
            'lng': 106.6347
        }
    ]
    
    for car in cars:
        vehicle = Vehicle(
            vehicle_code=car['code'],
            vehicle_type='car',
            brand=car['brand'],
            model=car['model'],
            color=car['color'],
            license_plate=car['plate'],
            year=2024,
            latitude=car['lat'],
            longitude=car['lng'],
            address='TP. Hồ Chí Minh',
            status='available',
            fuel_level=random.randint(50, 100),
            tire_pressure=35.0,
            price_per_minute=5000,
            qr_code=f'QR{car["code"]}',
            geofence_enabled=True,
            geofence_center_lat=10.8231,
            geofence_center_lng=106.6297,
            geofence_radius=50
        )
        db.session.add(vehicle)
    
    # Commit tất cả
    db.session.commit()

    # Seed Firestore if enabled
    init_firebase(app)
    if app.config.get('FIREBASE_ENABLED', False):
        print("\n☁️  Đẩy dữ liệu xe lên Firestore...")
        vehicles = Vehicle.query.all()
        for v in vehicles:
            VehicleRepository.add({
                'id': v.id,
                'vehicle_code': v.vehicle_code,
                'vehicle_type': v.vehicle_type,
                'brand': v.brand,
                'model': v.model,
                'license_plate': v.license_plate,
                'color': v.color,
                'year': v.year,
                'latitude': v.latitude,
                'longitude': v.longitude,
                'address': v.address,
                'status': v.status,
                'is_locked': v.is_locked,
                'battery_level': v.battery_level,
                'fuel_level': v.fuel_level,
                'tire_pressure': v.tire_pressure,
                'odometer': v.odometer,
                'qr_code': v.qr_code,
                'lock_status': v.lock_status,
                'price_per_minute': v.price_per_minute,
                'geofence_enabled': v.geofence_enabled,
                'geofence_center_lat': v.geofence_center_lat,
                'geofence_center_lng': v.geofence_center_lng,
                'geofence_radius': v.geofence_radius
            }, doc_id=str(v.id))
        print("✅ Firestore đã được seed dữ liệu xe.")
    
    print("\n✅ Hoàn thành! Dữ liệu mẫu đã được tạo:")
    print("\n📊 Thống kê:")
    print(f"   - Users: {User.query.count()}")
    print(f"   - Vehicles: {Vehicle.query.count()}")
    print(f"   - Bikes: {Vehicle.query.filter_by(vehicle_type='bike').count()}")
    print(f"   - Motorbikes: {Vehicle.query.filter_by(vehicle_type='motorbike').count()}")
    print(f"   - Cars: {Vehicle.query.filter_by(vehicle_type='car').count()}")
    
    print("\n🔑 Tài khoản đăng nhập:")
    print("   👑 Admin:")
    print("      - Email: admin@smartrent.com")
    print("      - Password: admin123")
    print("\n   👤 User Demo:")
    print("      - Email: demo@smartrent.com")
    print("      - Password: demo123")
    print("      - Số dư: 500,000 VND")
    
    print("\n🚀 Chạy ứng dụng: python run.py")
    print("🌐 Truy cập: http://localhost:5000")
