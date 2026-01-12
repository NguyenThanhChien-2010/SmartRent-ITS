from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required, current_user
from app.models import db, Vehicle, Booking, Trip, IoTLog
from datetime import datetime
import math
from sqlalchemy import func, and_
from app.utils.repositories import VehicleRepository

vehicle_bp = Blueprint('vehicle', __name__, url_prefix='/vehicles')

@vehicle_bp.route('/')
@login_required
def list_vehicles():
    """Danh sách phương tiện"""
    vehicle_type = request.args.get('type', 'all')
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    query = Vehicle.query.filter_by(status='available')
    
    if vehicle_type != 'all':
        query = query.filter_by(vehicle_type=vehicle_type)
    
    vehicles = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('vehicles/list.html', vehicles=vehicles, vehicle_type=vehicle_type)


@vehicle_bp.route('/map')
@login_required
def vehicle_map():
    """Hiển thị bản đồ phương tiện (GIS)"""
    return render_template('vehicles/map.html', mapbox_token=current_app.config.get('MAPBOX_ACCESS_TOKEN', ''))


@vehicle_bp.route('/api/nearby')
@login_required
def nearby_vehicles():
    """API tìm xe gần vị trí người dùng"""
    lat = request.args.get('lat', type=float)
    lng = request.args.get('lng', type=float)
    radius = request.args.get('radius', 5, type=float)  # km
    vehicle_type = request.args.get('type', 'all')
    
    if not lat or not lng:
        return jsonify({'error': 'Missing location parameters'}), 400
    
    vehicles = []
    # If Firebase enabled, use Firestore
    if current_app.config.get('FIREBASE_ENABLED', False):
        vehicles = VehicleRepository.list_available(vehicle_type)
    else:
        # Query from SQL database
        query = Vehicle.query.filter_by(status='available')
        if vehicle_type != 'all':
            query = query.filter_by(vehicle_type=vehicle_type)
        vehicles = query.all()
    
    # Filter by distance
    nearby = []
    for vehicle in vehicles:
        # Support both dict (Firestore) and SQLAlchemy object
        v_lat = vehicle['latitude'] if isinstance(vehicle, dict) else vehicle.latitude
        v_lng = vehicle['longitude'] if isinstance(vehicle, dict) else vehicle.longitude
        distance = calculate_distance(lat, lng, v_lat, v_lng)
        if distance <= radius:
            nearby.append({
                'id': vehicle.get('id') if isinstance(vehicle, dict) else vehicle.id,
                'code': vehicle.get('vehicle_code') if isinstance(vehicle, dict) else vehicle.vehicle_code,
                'type': vehicle.get('vehicle_type') if isinstance(vehicle, dict) else vehicle.vehicle_type,
                'brand': vehicle.get('brand') if isinstance(vehicle, dict) else vehicle.brand,
                'model': vehicle.get('model') if isinstance(vehicle, dict) else vehicle.model,
                'latitude': v_lat,
                'longitude': v_lng,
                'distance': round(distance, 2),
                'battery': vehicle.get('battery_level') if isinstance(vehicle, dict) else vehicle.battery_level,
                'price_per_minute': vehicle.get('price_per_minute') if isinstance(vehicle, dict) else vehicle.price_per_minute,
                'qr_code': vehicle.get('qr_code') if isinstance(vehicle, dict) else vehicle.qr_code
            })
    
    # Sort by distance
    nearby.sort(key=lambda x: x['distance'])
    
    return jsonify({'vehicles': nearby, 'count': len(nearby)})


@vehicle_bp.route('/<int:vehicle_id>')
@login_required
def vehicle_detail(vehicle_id):
    """Chi tiết phương tiện"""
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    
    # Get recent IoT logs
    recent_logs = IoTLog.query.filter_by(vehicle_id=vehicle_id)\
        .order_by(IoTLog.timestamp.desc())\
        .limit(10).all()
    
    # Get vehicle usage stats
    total_trips = Trip.query.filter_by(vehicle_id=vehicle_id, status='completed').count()
    total_distance = db.session.query(func.sum(Trip.distance_km))\
        .filter_by(vehicle_id=vehicle_id, status='completed').scalar() or 0
    
    return render_template('vehicles/detail.html', 
                         vehicle=vehicle, 
                         recent_logs=recent_logs,
                         total_trips=total_trips,
                         total_distance=round(total_distance, 2))


@vehicle_bp.route('/<int:vehicle_id>/book', methods=['POST'])
@login_required
def book_vehicle(vehicle_id):
    """Đặt xe"""
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    
    if vehicle.status != 'available':
        return jsonify({'error': 'Xe không khả dụng'}), 400
    
    # Check if user already has active trip
    active_trip = Trip.query.filter_by(
        user_id=current_user.id,
        status='in_progress'
    ).first()
    
    if active_trip:
        return jsonify({'error': 'Bạn đang có chuyến đi đang diễn ra'}), 400
    
    # Check if user has enough balance (deposit ~1 hour)
    estimated_cost = vehicle.price_per_minute * 60
    if current_user.wallet_balance < estimated_cost:
        return jsonify({'error': f'Số dư không đủ. Cần tối thiểu {estimated_cost:,.0f} VND để đặt xe.'}), 400
    
    # Create trip with pending status
    trip_code = f"TRIP{datetime.now().strftime('%Y%m%d%H%M%S')}"
    now = datetime.now()
    trip = Trip(
        trip_code=trip_code,
        user_id=current_user.id,
        vehicle_id=vehicle_id,
        status='pending',  # waiting for QR scan
        start_latitude=vehicle.latitude,
        start_longitude=vehicle.longitude,
        start_address=vehicle.address,
        start_time=now,  # Set start time when booking
        created_at=now,
        updated_at=now
    )
    
    # Reserve vehicle
    vehicle.status = 'reserved'
    
    try:
        db.session.add(trip)
        db.session.commit()
        
        # Mirror to Firestore if enabled
        if current_app.config.get('FIREBASE_ENABLED', False):
            VehicleRepository.update_fields(vehicle_id, {'status': 'reserved'})
        
        return jsonify({
            'success': True,
            'trip_code': trip_code,
            'trip_id': trip.id,
            'message': 'Đặt xe thành công! Vui lòng quét QR code trong vòng 5 phút.'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@vehicle_bp.route('/<int:vehicle_id>/unlock', methods=['POST'])
@login_required
def unlock_vehicle(vehicle_id):
    """Mở khóa xe (Smart Lock)"""
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    
    # Check if user has active booking
    booking = Booking.query.filter_by(
        user_id=current_user.id,
        vehicle_id=vehicle_id,
        status='confirmed'
    ).first()
    
    if not booking:
        return jsonify({'error': 'Không có booking hợp lệ'}), 400
    
    # Unlock vehicle
    vehicle.is_locked = False
    vehicle.lock_status = 'unlocked'
    
    try:
        db.session.commit()
        if current_app.config.get('FIREBASE_ENABLED', False):
            VehicleRepository.update_fields(vehicle_id, {
                'is_locked': False,
                'lock_status': 'unlocked'
            })
        # TODO: Send MQTT command to IoT device
        return jsonify({'success': True, 'message': 'Đã mở khóa xe'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@vehicle_bp.route('/<int:vehicle_id>/lock', methods=['POST'])
@login_required
def lock_vehicle(vehicle_id):
    """Khóa xe"""
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    
    vehicle.is_locked = True
    vehicle.lock_status = 'locked'
    
    try:
        db.session.commit()
        if current_app.config.get('FIREBASE_ENABLED', False):
            VehicleRepository.update_fields(vehicle_id, {
                'is_locked': True,
                'lock_status': 'locked'
            })
        # TODO: Send MQTT command to IoT device
        return jsonify({'success': True, 'message': 'Đã khóa xe'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


def calculate_distance(lat1, lon1, lat2, lon2):
    """Tính khoảng cách giữa 2 điểm (Haversine formula)"""
    R = 6371  # Earth radius in km
    
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    
    a = math.sin(dlat/2) * math.sin(dlat/2) + \
        math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * \
        math.sin(dlon/2) * math.sin(dlon/2)
    
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    distance = R * c
    
    return distance
