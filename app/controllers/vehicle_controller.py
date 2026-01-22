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
    search_query = request.args.get('search', '').strip()

    query = Vehicle.query.filter_by(status='available')

    if vehicle_type != 'all':
        query = query.filter_by(vehicle_type=vehicle_type)

    # Apply search filter if provided
    if search_query:
        from sqlalchemy import or_
        query = query.filter(
            or_(
                Vehicle.brand.ilike(f'%{search_query}%'),
                Vehicle.model.ilike(f'%{search_query}%'),
                Vehicle.license_plate.ilike(f'%{search_query}%'),
                Vehicle.vehicle_code.ilike(f'%{search_query}%')
            )
        )

    vehicles = query.paginate(page=page, per_page=per_page, error_out=False)

    return render_template('vehicles/list.html', vehicles=vehicles, vehicle_type=vehicle_type, search_query=search_query)


@vehicle_bp.route('/map')
@login_required
def vehicle_map():
    """
    Hiển thị bản đồ phương tiện (GIS) với chức năng tìm kiếm

    Route này xử lý việc hiển thị bản đồ xe với khả năng tìm kiếm.
    Khi người dùng nhập từ khóa tìm kiếm vào thanh search ở navbar,
    từ khóa sẽ được truyền qua query parameter 'search' và được
    sử dụng để lọc và highlight xe trên bản đồ.

    Args:
        search (str): Từ khóa tìm kiếm từ query parameter

    Returns:
        Template: Render template vehicles/map.html với search_query
    """
    # Lấy từ khóa tìm kiếm từ query parameter, loại bỏ khoảng trắng thừa
    search_query = request.args.get('search', '').strip()

    # Truyền search_query vào template để JavaScript có thể sử dụng
    return render_template('vehicles/map.html', search_query=search_query)


@vehicle_bp.route('/api/nearby')
@login_required
def nearby_vehicles():
    """
    API tìm xe gần vị trí người dùng với chức năng tìm kiếm nâng cao

    Endpoint này cung cấp danh sách xe gần vị trí của người dùng,
    hỗ trợ lọc theo loại xe, bán kính, và tìm kiếm theo từ khóa.
    Được sử dụng bởi bản đồ để hiển thị xe và hỗ trợ tìm kiếm nhanh.

    Query Parameters:
        lat (float): Vĩ độ của người dùng (bắt buộc)
        lng (float): Kinh độ của người dùng (bắt buộc)
        radius (float): Bán kính tìm kiếm (km, mặc định 5km)
        type (str): Loại xe ('all', 'motorbike', 'car', mặc định 'all')
        show_all (bool): Hiển thị tất cả xe (bao gồm không khả dụng, cho debug)
        search (str): Từ khóa tìm kiếm (brand, model, license_plate, vehicle_code)

    Returns:
        JSON: {
            'vehicles': [danh sách xe với thông tin chi tiết],
            'count': số lượng xe,
            'status_counts': thống kê theo trạng thái,
            'available_count': số xe khả dụng
        }

    Raises:
        400: Thiếu tham số vị trí (lat, lng)
    """
    # Lấy các tham số từ query string
    lat = request.args.get('lat', type=float)  # Vĩ độ người dùng
    lng = request.args.get('lng', type=float)  # Kinh độ người dùng
    radius = request.args.get('radius', 5, type=float)  # Bán kính tìm kiếm (km)
    vehicle_type = request.args.get('type', 'all')  # Loại xe cần lọc
    show_all = request.args.get('show_all', 'false') == 'true'  # Chế độ debug
    search_query = request.args.get('search', '').strip()  # Từ khóa tìm kiếm

    # Validate tham số bắt buộc
    if not lat or not lng:
        return jsonify({'error': 'Missing location parameters'}), 400

    vehicles = []

    # Kiểm tra xem có sử dụng Firebase hay không
    if current_app.config.get('FIREBASE_ENABLED', False):
        # Sử dụng Firestore database
        if show_all:
            # Lấy tất cả xe cho mục đích debugging
            from app.models import Vehicle as VehicleModel
            query = VehicleModel.query
            if vehicle_type != 'all':
                query = query.filter_by(vehicle_type=vehicle_type)
            vehicles = query.all()
        else:
            # Lấy xe khả dụng từ Firebase repository
            vehicles = VehicleRepository.list_available(vehicle_type)
    else:
        # Sử dụng SQL database (PostgreSQL/SQLite)
        if show_all:
            # Lấy tất cả xe (cho debug)
            query = Vehicle.query
        else:
            # Chỉ lấy xe có trạng thái 'available'
            query = Vehicle.query.filter_by(status='available')

        # Áp dụng bộ lọc loại xe nếu được chỉ định
        if vehicle_type != 'all':
            query = query.filter_by(vehicle_type=vehicle_type)

        # Áp dụng bộ lọc tìm kiếm nếu có từ khóa
        if search_query:
            from sqlalchemy import or_
            # Tìm kiếm không phân biệt hoa thường trong các trường:
            # - brand (thương hiệu): Honda, Yamaha, etc.
            # - model (model): Wave, Civic, etc.
            # - license_plate (biển số): 51A-12345, etc.
            # - vehicle_code (mã xe): V001, V002, etc.
            query = query.filter(
                or_(
                    Vehicle.brand.ilike(f'%{search_query}%'),
                    Vehicle.model.ilike(f'%{search_query}%'),
                    Vehicle.license_plate.ilike(f'%{search_query}%'),
                    Vehicle.vehicle_code.ilike(f'%{search_query}%')
                )
            )

        # Thực thi query để lấy danh sách xe
        vehicles = query.all()
    
    # Filter by distance
    nearby = []
    for vehicle in vehicles:
        # Support both dict (Firestore) and SQLAlchemy object
        v_lat = vehicle['latitude'] if isinstance(vehicle, dict) else vehicle.latitude
        v_lng = vehicle['longitude'] if isinstance(vehicle, dict) else vehicle.longitude
        v_status = vehicle.get('status') if isinstance(vehicle, dict) else vehicle.status
        
        distance = calculate_distance(lat, lng, v_lat, v_lng)
        if distance <= radius:
            nearby.append({
                'id': vehicle.get('id') if isinstance(vehicle, dict) else vehicle.id,
                'code': vehicle.get('vehicle_code') if isinstance(vehicle, dict) else vehicle.vehicle_code,
                'type': vehicle.get('vehicle_type') if isinstance(vehicle, dict) else vehicle.vehicle_type,
                'brand': vehicle.get('brand') if isinstance(vehicle, dict) else vehicle.brand,
                'model': vehicle.get('model') if isinstance(vehicle, dict) else vehicle.model,
                'license_plate': vehicle.get('license_plate') if isinstance(vehicle, dict) else vehicle.license_plate,
                'latitude': v_lat,
                'longitude': v_lng,
                'distance': round(distance, 2),
                'status': v_status,  # Add status to response
                'battery': vehicle.get('battery_level') if isinstance(vehicle, dict) else vehicle.battery_level,
                'price_per_minute': vehicle.get('price_per_minute') if isinstance(vehicle, dict) else vehicle.price_per_minute,
                'qr_code': vehicle.get('qr_code') if isinstance(vehicle, dict) else vehicle.qr_code
            })
    
    # Sort by distance
    nearby.sort(key=lambda x: x['distance'])
    
    # Count by status
    status_counts = {}
    for v in nearby:
        status = v.get('status', 'unknown')
        status_counts[status] = status_counts.get(status, 0) + 1
    
    return jsonify({
        'vehicles': nearby, 
        'count': len(nearby),
        'status_counts': status_counts,  # Debug info
        'available_count': status_counts.get('available', 0)
    })


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
    """
    Đặt xe và tạo chuyến đi mới

    Endpoint này xử lý việc đặt xe của người dùng, bao gồm:
    - Kiểm tra tính khả dụng của xe
    - Xác minh người dùng không có chuyến đi đang hoạt động
    - Kiểm tra số dư ví điện tử đủ cho đặt cọc
    - Tạo bản ghi chuyến đi với trạng thái 'pending'
    - Đồng bộ dữ liệu với Firebase nếu được bật

    Args:
        vehicle_id (int): ID của xe cần đặt

    Returns:
        JSON: Thông tin đặt xe thành công hoặc lỗi

    Raises:
        400: Xe không khả dụng, người dùng có chuyến đi đang diễn ra, hoặc số dư không đủ
        404: Không tìm thấy xe
        500: Lỗi hệ thống khi lưu dữ liệu
    """
    # Lấy thông tin xe từ database, trả về 404 nếu không tìm thấy
    vehicle = Vehicle.query.get_or_404(vehicle_id)

    # Kiểm tra xe có sẵn sàng để đặt không
    if vehicle.status != 'available':
        return jsonify({'error': 'Xe không khả dụng'}), 400

    # Kiểm tra người dùng hiện tại có chuyến đi đang hoạt động không
    # Một người chỉ được đặt một xe tại một thời điểm
    active_trip = Trip.query.filter_by(
        user_id=current_user.id,
        status='in_progress'
    ).first()

    if active_trip:
        return jsonify({'error': 'Bạn đang có chuyến đi đang diễn ra'}), 400

    # Tính toán chi phí đặt cọc (ước tính 1 giờ sử dụng)
    estimated_cost = vehicle.price_per_minute * 60
    if current_user.wallet_balance < estimated_cost:
        return jsonify({'error': f'Số dư không đủ. Cần tối thiểu {estimated_cost:,.0f} VND để đặt xe.'}), 400

    # Tạo mã chuyến đi duy nhất dựa trên timestamp
    trip_code = f"TRIP{datetime.now().strftime('%Y%m%d%H%M%S')}"
    now = datetime.now()

    # Tạo bản ghi chuyến đi mới với trạng thái 'pending'
    # Chuyến đi sẽ chờ người dùng quét QR để kích hoạt
    trip = Trip(
        trip_code=trip_code,
        user_id=current_user.id,
        vehicle_id=vehicle_id,
        status='pending',  # Đang chờ quét QR để bắt đầu
        start_latitude=vehicle.latitude,  # Vị trí bắt đầu từ vị trí xe
        start_longitude=vehicle.longitude,
        start_address=vehicle.address,
        start_time=now,  # Thời gian đặt xe
        created_at=now,
        updated_at=now
    )

    # Đánh dấu xe là đã được đặt trước (reserved)
    vehicle.status = 'reserved'

    try:
        # Lưu thay đổi vào database
        db.session.add(trip)
        db.session.commit()

        # Đồng bộ với Firebase nếu tính năng được bật
        if current_app.config.get('FIREBASE_ENABLED', False):
            print(f"[Booking] Syncing vehicle {vehicle_id} to Firebase...")
            success = VehicleRepository.update_fields(vehicle_id, {'status': 'reserved'})
            if success:
                print(f"[Booking] ✓ Firebase synced: vehicle {vehicle.vehicle_code} → reserved")
            else:
                print(f"[Booking] ⚠ Firebase sync returned False")

            # Đồng bộ thông tin chuyến đi lên Firebase
            from app.utils.repositories import TripRepository
            TripRepository.add({
                'id': trip.id,
                'trip_code': trip.trip_code,
                'user_id': trip.user_id,
                'vehicle_id': trip.vehicle_id,
                'status': 'pending',
                'start_latitude': trip.start_latitude,
                'start_longitude': trip.start_longitude,
                'start_address': trip.start_address,
                'created_at': trip.created_at.isoformat(),
                'updated_at': trip.updated_at.isoformat()
            }, doc_id=str(trip.id))
            print(f"[Booking] ✓ Trip {trip.trip_code} synced to Firebase")

        # Trả về thông tin đặt xe thành công
        return jsonify({
            'success': True,
            'trip_code': trip_code,
            'trip_id': trip.id,
            'message': 'Đặt xe thành công! Mã OTP đã được gửi đến email của bạn. Vui lòng kiểm tra hộp thư để nhận mã mở khóa.'
        })
    except Exception as e:
        # Rollback transaction nếu có lỗi xảy ra
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@vehicle_bp.route('/<int:vehicle_id>/unlock', methods=['POST'])
@login_required
def unlock_vehicle(vehicle_id):
    """
    Mở khóa xe thông qua Smart Lock system

    Endpoint này xử lý việc mở khóa xe từ xa sau khi người dùng
    đã đặt xe thành công và có booking hợp lệ. Hệ thống sẽ:
    - Kiểm tra quyền sở hữu booking của người dùng
    - Cập nhật trạng thái khóa của xe
    - Đồng bộ với Firebase nếu được bật
    - Gửi lệnh MQTT đến thiết bị IoT (chưa implement)

    Args:
        vehicle_id (int): ID của xe cần mở khóa

    Returns:
        JSON: {'success': True, 'message': '...'} hoặc lỗi

    Raises:
        400: Không có booking hợp lệ
        404: Không tìm thấy xe
        500: Lỗi hệ thống

    Note:
        Tính năng MQTT integration chưa được implement (TODO)
    """
    # Lấy thông tin xe từ database
    vehicle = Vehicle.query.get_or_404(vehicle_id)

    # Kiểm tra người dùng có booking hợp lệ cho xe này không
    # Booking phải có trạng thái 'confirmed' (đã xác nhận)
    booking = Booking.query.filter_by(
        user_id=current_user.id,
        vehicle_id=vehicle_id,
        status='confirmed'
    ).first()

    if not booking:
        return jsonify({'error': 'Không có booking hợp lệ'}), 400

    # Cập nhật trạng thái khóa của xe
    vehicle.is_locked = False
    vehicle.lock_status = 'unlocked'

    try:
        # Lưu thay đổi vào database
        db.session.commit()

        # Đồng bộ trạng thái với Firebase nếu được bật
        if current_app.config.get('FIREBASE_ENABLED', False):
            VehicleRepository.update_fields(vehicle_id, {
                'is_locked': False,
                'lock_status': 'unlocked'
            })

        # TODO: Gửi lệnh MQTT đến thiết bị IoT để mở khóa vật lý
        # Đây là tính năng IoT integration chưa được implement

        return jsonify({'success': True, 'message': 'Đã mở khóa xe'})
    except Exception as e:
        # Rollback transaction nếu có lỗi
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
    """
    Tính khoảng cách giữa 2 điểm trên trái đất sử dụng công thức Haversine

    Công thức Haversine được sử dụng để tính khoảng cách giữa 2 điểm
    trên bề mặt trái đất dựa trên vĩ độ và kinh độ. Đây là công thức
    chính xác hơn so với khoảng cách Euclidean cho các ứng dụng GIS.

    Args:
        lat1 (float): Vĩ độ điểm thứ nhất (độ)
        lon1 (float): Kinh độ điểm thứ nhất (độ)
        lat2 (float): Vĩ độ điểm thứ hai (độ)
        lon2 (float): Kinh độ điểm thứ hai (độ)

    Returns:
        float: Khoảng cách giữa 2 điểm (km)

    Formula:
        a = sin²(Δlat/2) + cos(lat1) * cos(lat2) * sin²(Δlon/2)
        c = 2 * atan2(√a, √(1-a))
        distance = R * c

    Where:
        Δlat = lat2 - lat1
        Δlon = lon2 - lon1
        R = 6371 km (bán kính trái đất)
    """
    # Bán kính trái đất (km) - sử dụng giá trị trung bình
    R = 6371

    # Chuyển đổi độ sang radian
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    # Áp dụng công thức Haversine
    a = math.sin(dlat/2) * math.sin(dlat/2) + \
        math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * \
        math.sin(dlon/2) * math.sin(dlon/2)

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    distance = R * c

    return distance
