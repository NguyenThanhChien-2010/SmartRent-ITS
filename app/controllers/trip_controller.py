from flask import Blueprint, render_template, request, jsonify, redirect, url_for, current_app
from flask_login import login_required, current_user
from app.models import db, Trip, Booking, Vehicle, Payment
from app.utils.repositories import TripRepository, BookingRepository, PaymentRepository, VehicleRepository
from datetime import datetime, timedelta
from sqlalchemy import func

trip_bp = Blueprint('trip', __name__, url_prefix='/trips')

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
    vehi# Đồng bộ lên Firebase nếu được bật
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
        print(f'[Error] Ending trip: {e}'etime.now().strftime('%Y%m%d%H%M%S')}"
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
        
        # Đồng bộ lên Firebase nếu được bật
        if current_app.config.get('FIREBASE_ENABLED', False):
            TripRepository.update_fields(str(trip.id), {
                'rating': trip.rating,
                'feedback': trip.feedback,
                'updated_at': datetime.utcnow()
            })
            print(f'[Firebase] Feedback for trip {trip.trip_code} synced to Firestore')
        
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
