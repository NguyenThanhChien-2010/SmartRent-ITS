from flask import Blueprint, render_template, request, jsonify, redirect, url_for, current_app
from flask_login import login_required, current_user
from app.models import db, Trip, Booking, Vehicle, Payment, User, HazardZone
from app.utils.repositories import TripRepository, BookingRepository, PaymentRepository, VehicleRepository
from app.utils.notification_helper import notify_payment_deduct, notify_trip_completed
from app.utils.route_optimizer import optimize_route, predict_traffic
from app.utils.email_helper import generate_otp, verify_otp, send_otp_email, send_unlock_notification
from app.utils.hazard_checker import check_route_hazards, interpolate_route_points, get_hazard_type_icon, get_severity_icon
from datetime import datetime, timedelta
from sqlalchemy import func
import math

trip_bp = Blueprint('trip', __name__, url_prefix='/trips')

@trip_bp.route('/active')
@login_required
def active_trip():
    """Hiển thị chuyến đi đang diễn ra"""
    trip = Trip.query.filter(
        Trip.user_id == current_user.id,
        Trip.status.in_(['pending', 'in_progress'])
    ).order_by(Trip.created_at.desc()).first()
    
    return render_template('trips/active.html', trip=trip)


@trip_bp.route('/<int:trip_id>/scan-qr', methods=['POST'])
@login_required
def scan_qr(trip_id):
    """Quét QR code để mở khóa và bắt đầu chuyến đi"""
    trip = Trip.query.get_or_404(trip_id)
    
    if trip.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    if trip.status != 'pending':
        return jsonify({'error': 'Trip không ở trạng thái chờ'}), 400
    
    data = request.get_json()
    qr_code = data.get('qr_code')
    
    # Verify QR code matches vehicle
    vehicle = Vehicle.query.get(trip.vehicle_id)
    if vehicle.qr_code != qr_code and vehicle.vehicle_code != qr_code:
        return jsonify({'error': 'QR code không hợp lệ cho xe này'}), 400
    
    # Unlock vehicle and start trip
    vehicle.status = 'in_use'
    vehicle.lock_status = 'unlocked'
    vehicle.is_locked = False
    
    trip.status = 'in_progress'
    trip.start_time = datetime.utcnow()
    
    try:
        db.session.commit()
        
        if current_app.config.get('FIREBASE_ENABLED', False):
            VehicleRepository.update_fields(vehicle.id, {
                'status': 'in_use',
                'lock_status': 'unlocked'
            })
        
        return jsonify({
            'success': True,
            'message': 'Xe đã được mở khóa. Chuyến đi bắt đầu!'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@trip_bp.route('/<int:trip_id>/iot-unlock', methods=['POST'])
@login_required
def iot_unlock(trip_id):
    """ITS Feature: IoT Remote Unlock - Mở khóa xe từ xa qua mạng IoT"""
    trip = Trip.query.get_or_404(trip_id)
    
    if trip.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized - Không có quyền mở khóa xe này'}), 403
    
    if trip.status != 'pending':
        return jsonify({'error': 'Trip không ở trạng thái chờ'}), 400
    
    data = request.get_json()
    smart_pin = data.get('pin')
    unlock_method = data.get('method', 'iot_remote')
    vehicle_code = data.get('vehicle_code')
    
    # Verify Smart PIN (last 6 digits of trip code)
    expected_pin = trip.trip_code[-6:]
    if smart_pin != expected_pin:
        return jsonify({'error': 'Smart PIN không hợp lệ'}), 400
    
    vehicle = Vehicle.query.get(trip.vehicle_id)
    
    # Verify vehicle code matches
    if vehicle.vehicle_code != vehicle_code:
        return jsonify({'error': 'Mã xe không khớp'}), 400
    
    # IoT Unlock: Update vehicle status
    vehicle.status = 'in_use'
    vehicle.lock_status = 'unlocked'
    vehicle.is_locked = False
    
    # Start trip
    trip.status = 'in_progress'
    trip.start_time = datetime.utcnow()
    
    try:
        db.session.commit()
        
        # Sync to Firebase/IoT platform
        if current_app.config.get('FIREBASE_ENABLED', False):
            VehicleRepository.update_fields(vehicle.id, {
                'status': 'in_use',
                'lock_status': 'unlocked',
                'is_locked': False,
                'last_unlock_method': unlock_method,
                'last_unlock_time': datetime.utcnow().isoformat()
            })
        
        # TODO: Send MQTT command to physical IoT device
        # mqtt_client.publish(f'smartrent/vehicle/{vehicle_code}/unlock', {'pin': smart_pin})
        
        return jsonify({
            'success': True,
            'message': 'Xe đã được mở khóa qua IoT. Chuyến đi bắt đầu!',
            'method': unlock_method,
            'vehicle_code': vehicle_code,
            'trip_code': trip.trip_code
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Lỗi kết nối IoT: {str(e)}'}), 500


@trip_bp.route('/<int:trip_id>/send-otp-email', methods=['POST'])
@login_required
def send_otp_email_route(trip_id):
    """ITS Feature: Send OTP via Email for vehicle unlock"""
    try:
        trip = Trip.query.get_or_404(trip_id)
        
        if trip.user_id != current_user.id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        if trip.status != 'pending':
            return jsonify({'error': 'Trip không ở trạng thái chờ'}), 400
        
        data = request.get_json()
        trip_code = data.get('trip_code')
        vehicle_code = data.get('vehicle_code')
        email = data.get('email') or current_user.email
        
        # Generate Smart PIN (last 6 digits of trip code)
        smart_pin = trip_code[-6:]
        
        print(f"[DEBUG] Sending OTP to {email}, PIN: {smart_pin}, Trip: {trip_code}")
        
        # Generate and store OTP
        otp = generate_otp(trip_id, email, smart_pin)
        
        # Send OTP email
        success, message = send_otp_email(email, trip_code, vehicle_code, otp)
        
        print(f"[DEBUG] Email send result: success={success}, message={message}")
        
        if success:
            return jsonify({
                'success': True,
                'message': 'OTP đã được gửi đến email',
                'email': email,
                'expires_in': 300  # 5 minutes in seconds
            })
        else:
            return jsonify({'error': message}), 500
    except Exception as e:
        print(f"[ERROR] send_otp_email_route: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Lỗi server: {str(e)}'}), 500


@trip_bp.route('/<int:trip_id>/verify-otp', methods=['POST'])
@login_required
def verify_otp_route(trip_id):
    """ITS Feature: Verify OTP and unlock vehicle"""
    try:
        print(f"[DEBUG] verify-otp called for trip_id={trip_id}")
        
        trip = Trip.query.get_or_404(trip_id)
        
        if trip.user_id != current_user.id:
            print(f"[ERROR] Unauthorized: user {current_user.id} != trip.user {trip.user_id}")
            return jsonify({'error': 'Unauthorized'}), 403
        
        if trip.status != 'pending':
            print(f"[ERROR] Trip status is {trip.status}, not pending")
            return jsonify({'error': 'Trip không ở trạng thái chờ'}), 400
        
        data = request.get_json()
        otp = data.get('otp')
        vehicle_code = data.get('vehicle_code')
        
        print(f"[DEBUG] Verifying OTP: {otp}, vehicle: {vehicle_code}")
        
        # Verify OTP
        is_valid, message = verify_otp(trip_id, otp)
        
        print(f"[DEBUG] OTP verification result: valid={is_valid}, msg={message}")
        
        if not is_valid:
            return jsonify({'error': message}), 400
        
        # OTP valid - unlock vehicle and start trip
        vehicle = Vehicle.query.get(trip.vehicle_id)
        
        if vehicle.vehicle_code != vehicle_code:
            print(f"[ERROR] Vehicle code mismatch: {vehicle.vehicle_code} != {vehicle_code}")
            return jsonify({'error': 'Mã xe không khớp'}), 400
        
        print(f"[DEBUG] Updating vehicle and trip status...")
        
        # Update vehicle status
        vehicle.status = 'in_use'
        vehicle.lock_status = 'unlocked'
        vehicle.is_locked = False
        
        # Start trip
        trip.status = 'in_progress'
        trip.start_time = datetime.now()  # Use local time instead of UTC
        
        # Commit to database first
        db.session.commit()
        print(f"[DEBUG] Database updated successfully")
        
        # Sync to Firebase/IoT (don't block on this)
        try:
            if current_app.config.get('FIREBASE_ENABLED', False):
                print(f"[DEBUG] Firebase ENABLED - syncing vehicle {vehicle.id}...")
                success = VehicleRepository.update_fields(vehicle.id, {
                    'status': 'in_use',
                    'lock_status': 'unlocked',
                    'is_locked': False,
                    'last_unlock_method': 'email_otp',
                    'last_unlock_time': datetime.utcnow().isoformat()
                })
                if success:
                    print(f"[DEBUG] ✓ Firebase sync SUCCESS for vehicle {vehicle.vehicle_code}")
                else:
                    print(f"[DEBUG] ⚠ Firebase sync returned False")
                    
                # Also sync trip to Firebase
                TripRepository.update_fields(trip.id, {
                    'status': 'in_progress',
                    'start_time': trip.start_time.isoformat()
                })
                print(f"[DEBUG] ✓ Trip {trip.id} synced to Firebase")
            else:
                print(f"[DEBUG] Firebase DISABLED in config")
        except Exception as firebase_err:
            print(f"[WARNING] ❌ Firebase sync failed: {firebase_err}")
            import traceback
            traceback.print_exc()
            # Don't fail the request if Firebase sync fails
        
        # Send unlock notification (don't block on this either)
        try:
            print(f"[DEBUG] Sending unlock notification email...")
            send_unlock_notification(current_user.email, trip.trip_code, vehicle.vehicle_code)
        except Exception as email_err:
            print(f"[WARNING] Unlock notification failed: {email_err}")
        
        print(f"[DEBUG] Verify OTP complete - returning success")
        
        return jsonify({
            'success': True,
            'message': 'OTP xác thực thành công! Xe đã mở khóa.',
            'method': 'email_otp',
            'vehicle_code': vehicle_code,
            'trip_code': trip.trip_code
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"[ERROR] verify_otp_route exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Lỗi mở khóa xe: {str(e)}'}), 500


def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points in km"""
    R = 6371  # Earth radius in km
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = math.sin(dLat/2) * math.sin(dLat/2) + math.cos(math.radians(lat1)) * \
        math.cos(math.radians(lat2)) * math.sin(dLon/2) * math.sin(dLon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return round(R * c, 2)


@trip_bp.route('/start/<int:booking_id>', methods=['GET', 'POST'])
@login_required
def start_trip(booking_id):
    """Bắt đầu chuyến đi"""
    booking = Booking.query.get_or_404(booking_id)
    
    if booking.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    if booking.status != 'confirmed':
        return jsonify({'error': 'Booking không hợp lệ'}), 400
    
    if request.method == 'POST':
        data = request.get_json()
        
        trip_code = f"TR{datetime.now().strftime('%Y%m%d%H%M%S')}{booking.vehicle_id}"
        trip = Trip(
            trip_code=trip_code,
            user_id=current_user.id,
            vehicle_id=booking.vehicle_id,
            booking_id=booking.id,
            start_latitude=data.get('latitude'),
            start_longitude=data.get('longitude'),
            start_address=data.get('address'),
            start_time=datetime.utcnow(),
            status='in_progress'
        )
        
        booking.status = 'completed'
        
        try:
            db.session.add(trip)
            db.session.commit()
            
            # Đồng bộ lên Firebase nếu được bật
            if current_app.config.get('FIREBASE_ENABLED', False):
                trip_data = {
                    'trip_code': trip.trip_code,
                    'user_id': trip.user_id,
                    'vehicle_id': trip.vehicle_id,
                    'booking_id': trip.booking_id,
                    'start_latitude': trip.start_latitude,
                    'start_longitude': trip.start_longitude,
                    'start_address': trip.start_address,
                    'start_time': trip.start_time,
                    'status': trip.status,
                    'created_at': trip.created_at,
                    'updated_at': trip.updated_at
                }
                firebase_id = TripRepository.add(trip_data, doc_id=str(trip.id))
                if firebase_id:
                    print(f'[Firebase] Trip {trip_code} synced to Firestore: {firebase_id}')
                
                # Update booking status
                BookingRepository.update_fields(str(booking.id), {'status': 'completed'})
                
                # Update vehicle status
                VehicleRepository.update_fields(str(booking.vehicle_id), {'status': 'in_use', 'is_locked': False})
            
            return jsonify({
                'success': True,
                'trip_code': trip_code,
                'trip_id': trip.id
            })
        except Exception as e:
            db.session.rollback()
            print(f'[Error] Starting trip: {e}')
            return jsonify({'error': str(e)}), 500
    
    return render_template('trips/start.html', booking=booking)


@trip_bp.route('/<int:trip_id>/end', methods=['POST'])
@login_required
def end_trip(trip_id):
    """Kết thúc chuyến đi"""
    trip = Trip.query.get_or_404(trip_id)
    
    if trip.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    if trip.status != 'in_progress':
        return jsonify({'error': 'Chuyến đi không hợp lệ'}), 400
    
    data = request.get_json()
    
    # Update trip with local time
    trip.end_time = datetime.now()  # Use local time instead of UTC
    trip.end_latitude = data.get('latitude')
    trip.end_longitude = data.get('longitude')
    trip.end_address = data.get('address')
    trip.distance_km = data.get('distance', 0)
    trip.status = 'completed'
    
    # Calculate duration
    duration = trip.end_time - trip.start_time
    trip.duration_minutes = duration.total_seconds() / 60
    
    # Calculate cost
    vehicle = Vehicle.query.get(trip.vehicle_id)
    trip.total_cost = trip.duration_minutes * vehicle.price_per_minute
    
    # Update vehicle status
    vehicle.status = 'available'
    vehicle.is_locked = True
    vehicle.odometer += trip.distance_km
    
    # Create payment
    payment_code = f"PAY{datetime.now().strftime('%Y%m%d%H%M%S')}"
    payment = Payment(
        payment_code=payment_code,
        user_id=current_user.id,
        trip_id=trip.id,
        amount=trip.total_cost,
        payment_method='wallet',
        payment_status='completed',
        transaction_date=datetime.utcnow()
    )
    
    # Deduct from wallet
    current_user.wallet_balance -= trip.total_cost
    
    try:
        db.session.add(payment)
        db.session.commit()
        
        # Send notifications
        try:
            notify_payment_deduct(current_user.id, trip.total_cost, trip.id)
            notify_trip_completed(current_user.id, vehicle.vehicle_code, trip.duration_minutes, trip.total_cost, trip.id)
        except Exception as notif_error:
            print(f'[Notification] Error: {notif_error}')
        
        # Đồng bộ lên Firebase nếu được bật
        if current_app.config.get('FIREBASE_ENABLED', False):
            # Update trip
            trip_data = {
                'end_time': trip.end_time,
                'end_latitude': trip.end_latitude,
                'end_longitude': trip.end_longitude,
                'end_address': trip.end_address,
                'distance_km': trip.distance_km,
                'duration_minutes': trip.duration_minutes,
                'total_cost': trip.total_cost,
                'status': 'completed',
                'updated_at': datetime.utcnow()
            }
            TripRepository.update_fields(str(trip.id), trip_data)
            print(f'[Firebase] Trip {trip.trip_code} updated in Firestore')
            
            # Add payment
            payment_data = {
                'payment_code': payment.payment_code,
                'user_id': payment.user_id,
                'trip_id': payment.trip_id,
                'amount': payment.amount,
                'payment_method': payment.payment_method,
                'payment_status': payment.payment_status,
                'transaction_date': payment.transaction_date,
                'created_at': datetime.utcnow()
            }
            firebase_payment_id = PaymentRepository.add(payment_data, doc_id=str(payment.id))
            if firebase_payment_id:
                print(f'[Firebase] Payment {payment_code} synced to Firestore: {firebase_payment_id}')
            
            # Update vehicle status
            VehicleRepository.update_fields(str(vehicle.id), {
                'status': 'available',
                'is_locked': True,
                'odometer': vehicle.odometer,
                'updated_at': datetime.utcnow().isoformat()
            })
        
        return jsonify({
            'success': True,
            'trip_id': trip.id,
            'trip_code': trip.trip_code,
            'duration_minutes': round(trip.duration_minutes, 2),
            'distance_km': trip.distance_km,
            'total_cost': trip.total_cost,
            'payment_code': payment_code
        })
    except Exception as e:
        db.session.rollback()
        print(f'[Error] Ending trip: {e}')
        return jsonify({'error': str(e)}), 500


@trip_bp.route('/history')
@login_required
def trip_history():
    """Lịch sử chuyến đi"""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    trips = Trip.query.filter_by(user_id=current_user.id)\
        .order_by(Trip.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    # Statistics
    total_trips = Trip.query.filter_by(user_id=current_user.id, status='completed').count()
    total_distance = db.session.query(func.sum(Trip.distance_km))\
        .filter_by(user_id=current_user.id, status='completed').scalar() or 0
    total_spent = db.session.query(func.sum(Trip.total_cost))\
        .filter_by(user_id=current_user.id, status='completed').scalar() or 0
    
    stats = {
        'total_trips': total_trips,
        'total_distance': round(total_distance, 2),
        'total_spent': round(total_spent, 2)
    }
    
    return render_template('trips/history.html', trips=trips, stats=stats)


@trip_bp.route('/<int:trip_id>')
@login_required
def trip_detail(trip_id):
    """Chi tiết chuyến đi"""
    trip = Trip.query.get_or_404(trip_id)
    
    if trip.user_id != current_user.id and current_user.role != 'admin':
        return "Unauthorized", 403
    
    return render_template('trips/detail.html', trip=trip)


@trip_bp.route('/<int:trip_id>/feedback', methods=['POST'])
@login_required
def submit_feedback(trip_id):
    """Đánh giá chuyến đi"""
    trip = Trip.query.get_or_404(trip_id)
    
    if trip.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    
    trip.rating = data.get('rating')
    trip.feedback = data.get('feedback')
    
    try:
        db.session.commit()
        
        # Đồng bộ lên Firebase nếu được bật
        if current_app.config.get('FIREBASE_ENABLED', False):
            TripRepository.update_fields(str(trip.id), {
                'rating': trip.rating,
                'feedback': trip.feedback,
                'updated_at': datetime.utcnow()
            })
            print(f'[Firebase] Feedback for trip {trip.trip_code} synced to Firestore')
        
        return jsonify({'success': True, 'message': 'Cảm ơn đánh giá của bạn!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@trip_bp.route('/plan')
@login_required
def plan_trip():
    """Lập kế hoạch hành trình (Trip Planning)"""
    return render_template('trips/plan.html')


@trip_bp.route('/api/optimize-route', methods=['POST'])
@login_required
def optimize_route_api():
    """
    API: Tính toán route tối ưu với OSRM (POST method)
    Frontend gọi API này để lấy route theo đường phố thực tế
    """
    try:
        data = request.get_json()
        start_lat = data.get('start_lat')
        start_lng = data.get('start_lng')
        end_lat = data.get('end_lat')
        end_lng = data.get('end_lng')
        start_address = data.get('start_address', '')
        end_address = data.get('end_address', '')
        
        if not all([start_lat, start_lng, end_lat, end_lng]):
            return jsonify({'error': 'Missing required coordinates'}), 400
        
        print(f"[OptimizeRoute] Request: ({start_lat}, {start_lng}) -> ({end_lat}, {end_lng})")
        
        # Call optimize_route function (uses OSRM)
        route_data = optimize_route(start_lat, start_lng, end_lat, end_lng)
        
        print(f"[OptimizeRoute] Result: {route_data['distance_km']} km, {route_data['estimated_time_minutes']} min")
        
        # SAFE LOGGING for Analytics (non-intrusive - wrapped in try/except)
        try:
            from app.models import RouteHistory
            
            # Create route history record
            route_history = RouteHistory(
                user_id=current_user.id,
                start_address=start_address,
                end_address=end_address,
                start_lat=start_lat,
                start_lng=start_lng,
                end_lat=end_lat,
                end_lng=end_lng,
                distance_km=route_data.get('distance_km'),
                duration_minutes=route_data.get('estimated_time_minutes'),
                estimated_cost=route_data.get('estimated_cost'),
                hazards_detected=0,  # Will be updated if route check happens
                routing_algorithm='OSRM' if route_data.get('algorithm') == 'osrm' else 'A*'
            )
            db.session.add(route_history)
            db.session.commit()
            
            print(f"[Analytics] Route logged: ID={route_history.id}")
            
        except Exception as log_error:
            # SAFE: Don't break main functionality if logging fails
            print(f"[Warning] Analytics logging failed: {log_error}")
            db.session.rollback()
        
        return jsonify(route_data)
        
    except Exception as e:
        print(f"[Error] Optimize route API: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@trip_bp.route('/api/route')
@login_required
def get_route():
    """API tính toán lộ trình tối ưu với A* algorithm"""
    start_lat = request.args.get('start_lat', type=float)
    start_lng = request.args.get('start_lng', type=float)
    end_lat = request.args.get('end_lat', type=float)
    end_lng = request.args.get('end_lng', type=float)
    
    if not all([start_lat, start_lng, end_lat, end_lng]):
        return jsonify({'error': 'Missing parameters'}), 400
    
    try:
        # Use A* algorithm for route optimization
        route_result = optimize_route(start_lat, start_lng, end_lat, end_lng)
        
        # Add traffic prediction
        now = datetime.now()
        traffic_level = predict_traffic(now.hour, now.weekday())
        route_result['traffic_level'] = traffic_level
        route_result['traffic_label'] = {
            'clear': 'Thông thoáng',
            'normal': 'Bình thường',
            'heavy': 'Tắc nhẹ',
            'congested': 'Tắc nặng'
        }.get(traffic_level, 'Bình thường')
        
        return jsonify(route_result)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@trip_bp.route('/api/optimize', methods=['POST'])
@login_required
def optimize_trip_route():
    """API tối ưu hóa chuyến đi với nhiều điểm trung gian"""
    data = request.get_json()
    
    start_lat = data.get('start_lat')
    start_lng = data.get('start_lng')
    end_lat = data.get('end_lat')
    end_lng = data.get('end_lng')
    waypoints = data.get('waypoints', [])  # [{lat, lng, name}, ...]
    
    if not all([start_lat, start_lng, end_lat, end_lng]):
        return jsonify({'error': 'Missing required parameters'}), 400
    
    try:
        result = optimize_route(
            start_lat, start_lng,
            end_lat, end_lng,
            waypoints=waypoints
        )
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@trip_bp.route('/<int:trip_id>/rating', methods=['GET', 'POST'])
@login_required
def rate_trip(trip_id):
    """Đánh giá chuyến đi"""
    trip = Trip.query.get_or_404(trip_id)
    
    if trip.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    if request.method == 'GET':
        return render_template('trips/rating.html', trip=trip)
    
    # POST - Submit rating
    data = request.get_json()
    rating = data.get('rating')
    comment = data.get('comment', '')
    
    if not rating or rating < 1 or rating > 5:
        return jsonify({'error': 'Rating phải từ 1-5'}), 400
    
    trip.rating = rating
    trip.feedback = comment
    
    try:
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'Cảm ơn bạn đã đánh giá!'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ============================================
# HAZARD ZONE CHECK (ITS Feature)
# ============================================

@trip_bp.route('/api/check-route-hazards', methods=['POST'])
@login_required
def check_route_for_hazards():
    """
    API: Kiểm tra route có đi qua vùng nguy hiểm nào không
    ITS Feature: Traveler Information System
    """
    try:
        data = request.get_json()
        route_points = data.get('route_points', [])
        
        if not route_points or len(route_points) < 2:
            return jsonify({
                'success': True,
                'hazards': [],
                'message': 'Route quá ngắn để kiểm tra'
            })
        
        # Convert to tuples
        route_tuples = [(p[0], p[1]) for p in route_points]
        
        # Interpolate route for better detection (add points every 100m)
        interpolated_route = interpolate_route_points(route_tuples, max_distance_km=0.1)
        
        print(f"[HazardCheck] Original route: {len(route_tuples)} points")
        print(f"[HazardCheck] Interpolated route: {len(interpolated_route)} points")
        
        # Get all active hazard zones
        active_zones = HazardZone.query.filter_by(is_active=True).all()
        
        # Convert to dict format for checker
        zones_data = []
        for zone in active_zones:
            zones_data.append({
                'id': zone.id,
                'zone_code': zone.zone_code,
                'zone_name': zone.zone_name,
                'hazard_type': zone.hazard_type,
                'severity': zone.severity,
                'description': zone.description,
                'warning_message': zone.warning_message,
                'polygon_coordinates': zone.polygon_coordinates,
                'min_latitude': zone.min_latitude,
                'max_latitude': zone.max_latitude,
                'min_longitude': zone.min_longitude,
                'max_longitude': zone.max_longitude,
                'color': zone.color,
                'is_active': zone.is_active
            })
        
        # Check route against hazards
        detected_hazards = check_route_hazards(interpolated_route, zones_data)
        
        print(f"[HazardCheck] Detected {len(detected_hazards)} hazards")
        
        # Update warning count for detected zones
        if detected_hazards:
            for hazard in detected_hazards:
                zone = HazardZone.query.get(hazard['id'])
                if zone:
                    zone.warning_count += 1
            db.session.commit()
        
        # Add icons for frontend
        for hazard in detected_hazards:
            hazard['type_icon'] = get_hazard_type_icon(hazard['hazard_type'])
            hazard['severity_icon'] = get_severity_icon(hazard['severity'])
        
        return jsonify({
            'success': True,
            'hazards': detected_hazards,
            'count': len(detected_hazards),
            'has_hazards': len(detected_hazards) > 0
        })
        
    except Exception as e:
        print(f"[Error] Checking route hazards: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@trip_bp.route('/api/alternative-routes', methods=['POST'])
@login_required
def get_alternative_routes():
    """
    API: Tính toán alternative routes tránh hazard zones
    ITS Feature: Advanced Route Planning with Hazard Avoidance
    """
    try:
        from app.utils.route_optimizer import calculate_alternative_routes
        
        data = request.get_json()
        start_lat = data.get('start_lat')
        start_lng = data.get('start_lng')
        end_lat = data.get('end_lat')
        end_lng = data.get('end_lng')
        
        if not all([start_lat, start_lng, end_lat, end_lng]):
            return jsonify({'error': 'Missing required coordinates'}), 400
        
        print(f"[AlternativeRoutes] Calculating routes from ({start_lat}, {start_lng}) to ({end_lat}, {end_lng})")
        
        # Get all active hazard zones
        active_zones = HazardZone.query.filter_by(is_active=True).all()
        print(f"[AlternativeRoutes] Found {len(active_zones)} active hazard zones")
        
        # Calculate alternative routes
        routes = calculate_alternative_routes(
            start_lat, start_lng,
            end_lat, end_lng,
            hazard_zones=active_zones,
            num_alternatives=3
        )
        
        print(f"[AlternativeRoutes] Generated {len(routes)} alternative routes")
        
        # Format response
        routes_data = []
        for route in routes:
            route_info = {
                'rank': route['rank'],
                'route_name': route['route_name'],
                'route_type': route['route_type'],
                'recommended': route['recommended'],
                'path': route['path'],
                'distance_km': route['distance_km'],
                'estimated_time_minutes': route['estimated_time_minutes'],
                'estimated_cost_vnd': route['estimated_cost_vnd'],
                'hazard_count': route['hazard_count'],
                'risk_level': route['risk_level'],
                'hazards': []
            }
            
            # Add hazard details with icons
            for hazard in route['hazards']:
                hazard_info = {
                    'zone_name': hazard['zone_name'],
                    'hazard_type': hazard['hazard_type'],
                    'severity': hazard['severity'],
                    'warning_message': hazard['warning_message'],
                    'type_icon': get_hazard_type_icon(hazard['hazard_type']),
                    'severity_icon': get_severity_icon(hazard['severity'])
                }
                route_info['hazards'].append(hazard_info)
            
            routes_data.append(route_info)
        
        # Find safest route
        safest_route = min(routes, key=lambda r: r['hazard_count'])
        
        return jsonify({
            'success': True,
            'routes': routes_data,
            'total_routes': len(routes_data),
            'safest_route_index': routes.index(safest_route),
            'has_safe_alternative': any(r['hazard_count'] == 0 for r in routes)
        })
        
    except Exception as e:
        print(f"[Error] Calculating alternative routes: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


