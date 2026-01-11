from flask import Blueprint, render_template, request, jsonify, redirect, url_for, current_app
from flask_login import login_required, current_user
from app.models import db, Trip, Booking, Vehicle, Payment, User
from app.utils.repositories import TripRepository, BookingRepository, PaymentRepository, VehicleRepository
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
    
    # Update trip
    trip.end_time = datetime.utcnow()
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


@trip_bp.route('/api/route')
@login_required
def get_route():
    """API tính toán lộ trình tối ưu"""
    start_lat = request.args.get('start_lat', type=float)
    start_lng = request.args.get('start_lng', type=float)
    end_lat = request.args.get('end_lat', type=float)
    end_lng = request.args.get('end_lng', type=float)
    
    if not all([start_lat, start_lng, end_lat, end_lng]):
        return jsonify({'error': 'Missing parameters'}), 400
    
    # TODO: Integrate with Google Maps Directions API or similar service
    # For now, return mock data
    
    route = {
        'distance_km': 5.2,
        'duration_minutes': 15,
        'polyline': [],  # List of [lat, lng] coordinates
        'warnings': [
            {'type': 'traffic', 'message': 'Tắc đường nhẹ trên đường ABC'},
            {'type': 'restricted', 'message': 'Đường XYZ đang cấm xe'}
        ]
    }
    
    return jsonify(route)


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

