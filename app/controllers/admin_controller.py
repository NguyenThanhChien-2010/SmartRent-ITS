from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import db, User, Vehicle, Booking, Trip, Payment, Maintenance, EmergencyAlert, IoTLog
from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_
from functools import wraps
from app.utils.repositories import VehicleRepository

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            return "Unauthorized", 403
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Dashboard quản trị (Big Data Analytics)"""
    
    # Today's stats
    today = datetime.utcnow().date()
    today_start = datetime.combine(today, datetime.min.time())
    
    stats = {
        'total_users': User.query.filter_by(role='customer').count(),
        'total_vehicles': Vehicle.query.count(),
        'available_vehicles': Vehicle.query.filter_by(status='available').count(),
        'in_use_vehicles': Vehicle.query.filter_by(status='in_use').count(),
        'maintenance_vehicles': Vehicle.query.filter_by(status='maintenance').count(),
        'today_trips': Trip.query.filter(Trip.created_at >= today_start).count(),
        'today_revenue': db.session.query(func.sum(Payment.amount))\
            .filter(Payment.created_at >= today_start, Payment.payment_status == 'completed')\
            .scalar() or 0,
        'active_trips': Trip.query.filter_by(status='in_progress').count(),
        'pending_maintenances': Maintenance.query.filter_by(status='scheduled').count(),
        'open_alerts': EmergencyAlert.query.filter_by(status='open').count()
    }
    
    # Revenue chart data (last 7 days)
    revenue_data = []
    for i in range(6, -1, -1):
        date = today - timedelta(days=i)
        date_start = datetime.combine(date, datetime.min.time())
        date_end = datetime.combine(date, datetime.max.time())
        
        revenue = db.session.query(func.sum(Payment.amount))\
            .filter(and_(Payment.created_at >= date_start, 
                        Payment.created_at <= date_end,
                        Payment.payment_status == 'completed'))\
            .scalar() or 0
        
        revenue_data.append({
            'date': date.strftime('%d/%m'),
            'revenue': round(revenue, 2)
        })
    
    # Vehicle usage by type
    vehicle_usage = db.session.query(
        Vehicle.vehicle_type,
        func.count(Trip.id).label('trip_count')
    ).join(Trip).filter(Trip.status == 'completed')\
     .group_by(Vehicle.vehicle_type).all()
    
    vehicle_usage_data = [{'type': vt, 'count': count} for vt, count in vehicle_usage]
    
    # Peak hours analysis
    peak_hours = db.session.query(
        func.extract('hour', Trip.start_time).label('hour'),
        func.count(Trip.id).label('trip_count')
    ).filter(Trip.status == 'completed')\
     .group_by('hour')\
     .order_by('hour').all()
    
    peak_hours_data = [{'hour': int(hour), 'count': count} for hour, count in peak_hours]
    
    return render_template('admin/dashboard.html', 
                         stats=stats,
                         revenue_data=revenue_data,
                         vehicle_usage_data=vehicle_usage_data,
                         peak_hours_data=peak_hours_data)


@admin_bp.route('/users')
@login_required
@admin_required
def manage_users():
    """Quản lý người dùng"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    users = User.query.order_by(User.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('admin/users.html', users=users)


@admin_bp.route('/users/<int:user_id>')
@login_required
@admin_required
def user_detail(user_id):
    """Chi tiết người dùng"""
    user = User.query.get_or_404(user_id)
    
    # Get user statistics
    total_trips = Trip.query.filter_by(user_id=user_id, status='completed').count()
    total_distance = db.session.query(func.sum(Trip.distance_km))\
        .filter_by(user_id=user_id, status='completed').scalar() or 0
    total_spent = db.session.query(func.sum(Trip.total_cost))\
        .filter_by(user_id=user_id, status='completed').scalar() or 0
    
    # Recent trips
    recent_trips = Trip.query.filter_by(user_id=user_id)\
        .order_by(Trip.created_at.desc())\
        .limit(10).all()
    
    # Recent payments
    recent_payments = Payment.query.filter_by(user_id=user_id)\
        .order_by(Payment.created_at.desc())\
        .limit(10).all()
    
    stats = {
        'total_trips': total_trips,
        'total_distance': round(total_distance, 2),
        'total_spent': round(total_spent, 2)
    }
    
    return render_template('admin/user_detail.html', 
                         user=user, 
                         stats=stats,
                         recent_trips=recent_trips,
                         recent_payments=recent_payments)


@admin_bp.route('/trips/today')
@login_required
@admin_required
def today_trips():
    """Danh sách chuyến đi hôm nay"""
    today = datetime.now().date()  # Use local time instead of UTC
    today_start = datetime.combine(today, datetime.min.time())
    
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', 'all')
    per_page = 50
    
    # Base query
    query = Trip.query.filter(Trip.created_at >= today_start)
    
    # Apply status filter
    if status_filter != 'all':
        query = query.filter(Trip.status == status_filter)
    
    trips = query.order_by(Trip.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    # Statistics
    total_today = Trip.query.filter(Trip.created_at >= today_start).count()
    completed_today = Trip.query.filter(
        Trip.created_at >= today_start, 
        Trip.status == 'completed'
    ).count()
    in_progress = Trip.query.filter(
        Trip.created_at >= today_start, 
        Trip.status == 'in_progress'
    ).count()
    pending = Trip.query.filter(
        Trip.created_at >= today_start,
        Trip.status == 'pending'
    ).count()
    cancelled = Trip.query.filter(
        Trip.created_at >= today_start,
        Trip.status == 'cancelled'
    ).count()
    
    stats = {
        'total': total_today,
        'completed': completed_today,
        'in_progress': in_progress,
        'pending': pending,
        'cancelled': cancelled
    }
    
    return render_template('admin/today_trips.html', 
                         trips=trips, 
                         stats=stats, 
                         status_filter=status_filter)


@admin_bp.route('/revenue/today')
@login_required
@admin_required
def today_revenue():
    """Chi tiết doanh thu hôm nay"""
    today = datetime.utcnow().date()
    today_start = datetime.combine(today, datetime.min.time())
    
    page = request.args.get('page', 1, type=int)
    per_page = 50
    
    payments = Payment.query.filter(
        Payment.created_at >= today_start,
        Payment.payment_status == 'completed'
    ).order_by(Payment.created_at.desc())\
     .paginate(page=page, per_page=per_page, error_out=False)
    
    # Statistics
    total_revenue = db.session.query(func.sum(Payment.amount))\
        .filter(Payment.created_at >= today_start, Payment.payment_status == 'completed')\
        .scalar() or 0
    
    total_payments = Payment.query.filter(
        Payment.created_at >= today_start,
        Payment.payment_status == 'completed'
    ).count()
    
    stats = {
        'total_revenue': total_revenue,
        'total_payments': total_payments,
        'average_payment': total_revenue / total_payments if total_payments > 0 else 0
    }
    
    return render_template('admin/today_revenue.html', payments=payments, stats=stats)


@admin_bp.route('/vehicles')
@login_required
@admin_required
def manage_vehicles():
    """Quản lý phương tiện"""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', 'all')
    per_page = 20
    
    query = Vehicle.query
    if status != 'all':
        query = query.filter_by(status=status)
    
    vehicles = query.order_by(Vehicle.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('admin/vehicles.html', vehicles=vehicles, status=status)


@admin_bp.route('/vehicles/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_vehicle():
    """Thêm phương tiện mới"""
    if request.method == 'POST':
        data = request.form
        
        # Kiểm tra biển số đã tồn tại chưa
        license_plate = data.get('license_plate')
        existing_vehicle = Vehicle.query.filter_by(license_plate=license_plate).first()
        if existing_vehicle:
            flash(f'Biển số "{license_plate}" đã tồn tại! Vui lòng nhập biển số khác.', 'danger')
            return redirect(url_for('admin.add_vehicle'))
        
        vehicle_code = f"VH{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        vehicle = Vehicle(
            vehicle_code=vehicle_code,
            vehicle_type=data.get('vehicle_type'),
            brand=data.get('brand'),
            model=data.get('model'),
            license_plate=license_plate,
            color=data.get('color'),
            year=data.get('year', type=int),
            latitude=data.get('latitude', type=float),
            longitude=data.get('longitude', type=float),
            price_per_minute=data.get('price_per_minute', type=float),
            battery_level=100.0,
            status='available',
            qr_code=f"QR{vehicle_code}"
        )
        
        try:
            db.session.add(vehicle)
            db.session.commit()
            
            # Sync to Firebase
            vehicle_data = {
                'id': vehicle.id,
                'vehicle_code': vehicle.vehicle_code,
                'vehicle_type': vehicle.vehicle_type,
                'brand': vehicle.brand,
                'model': vehicle.model,
                'license_plate': vehicle.license_plate,
                'color': vehicle.color,
                'year': vehicle.year,
                'latitude': vehicle.latitude,
                'longitude': vehicle.longitude,
                'price_per_minute': vehicle.price_per_minute,
                'battery_level': vehicle.battery_level,
                'status': vehicle.status,
                'qr_code': vehicle.qr_code,
                'created_at': vehicle.created_at.isoformat() if vehicle.created_at else None
            }
            firebase_id = VehicleRepository.add(vehicle_data, doc_id=vehicle.id)
            print(f"[Firebase] Vehicle {vehicle.vehicle_code} synced to Firestore: {firebase_id}")
            
            flash('Thêm phương tiện thành công!', 'success')
            return redirect(url_for('admin.manage_vehicles'))
        except Exception as e:
            db.session.rollback()
            print(f"[Firebase] Error syncing vehicle: {str(e)}")
            flash(f'Lỗi: {str(e)}', 'danger')
            return redirect(url_for('admin.add_vehicle'))
    
    return render_template('admin/add_vehicle.html')


@admin_bp.route('/vehicles/<int:vehicle_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_vehicle(vehicle_id):
    """Chỉnh sửa phương tiện"""
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    
    if request.method == 'POST':
        data = request.form
        
        vehicle.brand = data.get('brand')
        vehicle.model = data.get('model')
        vehicle.color = data.get('color')
        vehicle.status = data.get('status')
        vehicle.price_per_minute = data.get('price_per_minute', type=float)
        
        try:
            db.session.commit()
            return redirect(url_for('admin.manage_vehicles'))
        except Exception as e:
            db.session.rollback()
            return f"Error: {str(e)}", 500
    
    return render_template('admin/edit_vehicle.html', vehicle=vehicle)


@admin_bp.route('/maintenance')
@login_required
@admin_required
def manage_maintenance():
    """Quản lý bảo trì"""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', 'all')
    per_page = 20
    
    query = Maintenance.query
    if status != 'all':
        query = query.filter_by(status=status)
    
    maintenances = query.order_by(Maintenance.scheduled_date.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('admin/maintenance.html', maintenances=maintenances, status=status)


@admin_bp.route('/maintenance/schedule', methods=['POST'])
@login_required
@admin_required
def schedule_maintenance():
    """Lên lịch bảo trì"""
    data = request.get_json()
    
    maintenance_code = f"MT{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    maintenance = Maintenance(
        maintenance_code=maintenance_code,
        vehicle_id=data.get('vehicle_id'),
        maintenance_type=data.get('maintenance_type'),
        description=data.get('description'),
        scheduled_date=datetime.fromisoformat(data.get('scheduled_date')),
        status='scheduled'
    )
    
    # Update vehicle status
    vehicle = Vehicle.query.get(data.get('vehicle_id'))
    vehicle.status = 'maintenance'
    
    try:
        db.session.add(maintenance)
        db.session.commit()
        return jsonify({'success': True, 'maintenance_code': maintenance_code})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/alerts')
@login_required
@admin_required
def emergency_alerts():
    """Quản lý cảnh báo khẩn cấp (eCall)"""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', 'open')
    per_page = 20
    
    query = EmergencyAlert.query
    if status != 'all':
        query = query.filter_by(status=status)
    
    alerts = query.order_by(EmergencyAlert.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('admin/alerts.html', alerts=alerts, status=status)


@admin_bp.route('/alerts/<int:alert_id>/respond', methods=['POST'])
@login_required
@admin_required
def respond_alert(alert_id):
    """Phản hồi cảnh báo khẩn cấp"""
    alert = EmergencyAlert.query.get_or_404(alert_id)
    data = request.get_json()
    
    alert.status = 'acknowledged'
    alert.response_team = data.get('response_team')
    alert.response_time = datetime.utcnow()
    
    try:
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/rebalancing')
@login_required
@admin_required
def vehicle_rebalancing():
    """Điều phối phương tiện (Rebalancing)"""
    # Analyze vehicle distribution
    # Group vehicles by area (simplified - using rounded coordinates)
    distribution = db.session.query(
        func.round(Vehicle.latitude, 2).label('lat_area'),
        func.round(Vehicle.longitude, 2).label('lng_area'),
        func.count(Vehicle.id).label('vehicle_count')
    ).filter_by(status='available')\
     .group_by('lat_area', 'lng_area').all()
    
    distribution_data = [{
        'lat': float(lat),
        'lng': float(lng),
        'count': count
    } for lat, lng, count in distribution]
    
    # High demand areas (areas with recent trips but few vehicles)
    high_demand = []
    # TODO: Implement demand prediction algorithm
    
    return render_template('admin/rebalancing.html', 
                         distribution=distribution_data,
                         high_demand=high_demand)


@admin_bp.route('/analytics')
@login_required
@admin_required
def analytics():
    """Phân tích dữ liệu chi tiết"""
    # 1. KPI Tổng quan
    total_revenue = db.session.query(func.sum(Payment.amount))\
        .filter(Payment.payment_status == 'completed').scalar() or 0
        
    total_trips = Trip.query.filter_by(status='completed').count()
    
    avg_rating = db.session.query(func.avg(Trip.rating))\
        .filter(Trip.status == 'completed', Trip.rating != None).scalar() or 0
        
    total_distance = db.session.query(func.sum(Trip.distance_km))\
        .filter(Trip.status == 'completed').scalar() or 0
        
    avg_trip_cost = total_revenue / total_trips if total_trips > 0 else 0

    # 2. Doanh thu theo tháng (6 tháng gần nhất)
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=180)
    
    # Query payments & xử lý group by ở Python để tương thích tốt nhất
    payments = db.session.query(Payment.created_at, Payment.amount)\
        .filter(Payment.payment_status == 'completed', 
                Payment.created_at >= start_date).all()
    
    revenue_by_month = {}
    for p_date, amount in payments:
        month_key = p_date.strftime('%Y-%m')
        revenue_by_month[month_key] = revenue_by_month.get(month_key, 0) + amount
        
    sorted_months = sorted(revenue_by_month.keys())
    revenue_chart = {
        'labels': sorted_months,
        'data': [round(revenue_by_month[m], 2) for m in sorted_months]
    }

    # 3. Số chuyến đi theo loại xe
    trips_by_vehicle = db.session.query(
        Vehicle.vehicle_type,
        func.count(Trip.id)
    ).join(Trip).filter(Trip.status == 'completed')\
     .group_by(Vehicle.vehicle_type).all()
     
    vehicle_chart = {
        'labels': [t[0] for t in trips_by_vehicle],
        'data': [t[1] for t in trips_by_vehicle]
    }
    
    # 4. Top 5 xe doanh thu cao nhất
    top_vehicles = db.session.query(
        Vehicle.vehicle_code,
        Vehicle.vehicle_type,
        func.count(Trip.id).label('trip_count'),
        func.sum(Trip.total_cost).label('revenue')
    ).join(Trip).filter(Trip.status == 'completed')\
     .group_by(Vehicle.id, Vehicle.vehicle_code, Vehicle.vehicle_type)\
     .order_by(func.sum(Trip.total_cost).desc())\
     .limit(5).all()

    # 5. Firebase Data Integration
    firebase_stats = {'status': 'Checking...'}
    try:
        from app.utils.firebase_client import get_db
        firestore_db = get_db()
        
        if firestore_db:
            firebase_stats['status'] = 'Connected'
            collections = ['vehicles', 'trips', 'bookings', 'users', 'payments']
            
            for col in collections:
                # Get collection reference
                col_ref = firestore_db.collection(col)
                # Get count (using stream for now as it's simple for small datasets)
                docs = col_ref.stream()
                firebase_stats[col] = sum(1 for _ in docs)
        else:
            firebase_stats['status'] = 'Not Configured'
            
    except Exception as e:
        print(f"Error fetching Firebase stats: {e}")
        firebase_stats['status'] = 'Error'
        firebase_stats['error'] = str(e)

    return render_template('admin/analytics.html',
                         kpi={
                             'revenue': total_revenue,
                             'trips': total_trips,
                             'avg_rating': round(avg_rating, 1),
                             'total_distance': round(total_distance, 1),
                             'avg_trip_cost': round(avg_trip_cost, 2)
                         },
                         revenue_chart=revenue_chart,
                         vehicle_chart=vehicle_chart,
                         top_vehicles=top_vehicles,
                         firebase_stats=firebase_stats)


@admin_bp.route('/iot-monitor')
@login_required
@admin_required
def iot_monitor():
    """Real-time IoT monitoring dashboard"""
    from flask import current_app
    vehicles = Vehicle.query.all()
    
    # Prepare vehicle data for real-time display
    vehicle_data = [{
        'id': v.id,
        'brand': v.brand,
        'model': v.model,
        'license_plate': v.license_plate,
        'vehicle_type': v.vehicle_type,
        'status': v.status,
        'latitude': float(v.latitude) if v.latitude else 10.8231,
        'longitude': float(v.longitude) if v.longitude else 106.6297,
        'battery_level': v.battery_level or 100,
        'fuel_level': v.fuel_level or 100
    } for v in vehicles]
    
    
    return render_template('admin/iot_monitor.html', 
                         vehicles=vehicle_data)


@admin_bp.route('/heatmap')
@login_required
@admin_required
def trip_heatmap():
    """Trip heatmap analysis"""
    from flask import current_app
    from collections import Counter
    from datetime import datetime
    import requests
    import time
    
    # Get all completed trips with coordinates
    trips = Trip.query.filter(
        Trip.status.in_(['completed', 'in_progress']),
        Trip.start_latitude.isnot(None),
        Trip.start_longitude.isnot(None)
    ).all()
    
    # Prepare heatmap data
    heatmap_data = []
    location_counter = Counter()
    hour_counter = Counter()
    
    for trip in trips:
        if trip.start_latitude and trip.start_longitude:
            lat = float(trip.start_latitude)
            lng = float(trip.start_longitude)
            heatmap_data.append({
                'lat': lat,
                'lng': lng,
                'intensity': 1
            })
            # Count locations (rounded to 3 decimals for grouping)
            location_key = f"{lat:.3f},{lng:.3f}"
            location_counter[location_key] += 1
            
        if trip.end_latitude and trip.end_longitude:
            lat = float(trip.end_latitude)
            lng = float(trip.end_longitude)
            heatmap_data.append({
                'lat': lat,
                'lng': lng,
                'intensity': 1
            })
            location_key = f"{lat:.3f},{lng:.3f}"
            location_counter[location_key] += 1
        
        # Count hours
        if trip.start_time:
            hour = trip.start_time.hour
            hour_counter[hour] += 1
    
    # Find hottest area with reverse geocoding
    hottest_area = "Chưa có dữ liệu"
    if location_counter:
        hottest_location, hottest_count = location_counter.most_common(1)[0]
        lat, lng = hottest_location.split(',')
        
        # Reverse geocoding using Nominatim (OpenStreetMap - FREE!)
        try:
            url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lng}&format=json&addressdetails=1"
            headers = {'User-Agent': 'SmartRent-ITS/1.0'}
            response = requests.get(url, headers=headers, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                address = data.get('address', {})
                
                # Build readable address
                parts = []
                if address.get('road'):
                    parts.append(address['road'])
                if address.get('suburb') or address.get('neighbourhood'):
                    parts.append(address.get('suburb') or address.get('neighbourhood'))
                if address.get('city_district'):
                    parts.append(address.get('city_district'))
                if address.get('city'):
                    parts.append(address.get('city'))
                
                address_str = ", ".join(parts) if parts else data.get('display_name', f"Tọa độ {lat}, {lng}")
                hottest_area = f"{address_str} ({hottest_count} chuyến)"
            else:
                hottest_area = f"Tọa độ {lat}, {lng} ({hottest_count} chuyến)"
        except Exception as e:
            print(f"Reverse geocoding error: {e}")
            hottest_area = f"Tọa độ {lat}, {lng} ({hottest_count} chuyến)"
    
    # Find peak hours
    peak_hours = "Chưa có dữ liệu"
    if hour_counter:
        top_hours = hour_counter.most_common(3)
        peak_hours_list = [f"{h}h ({c} chuyến)" for h, c in top_hours]
        peak_hours = ", ".join(peak_hours_list)
    
    return render_template('admin/heatmap.html',
                         heatmap_data=heatmap_data,
                         hottest_area=hottest_area,
                         peak_hours=peak_hours,
                         total_trips=len(trips))


@admin_bp.route('/vehicles/fix-orphaned', methods=['POST'])
@login_required
@admin_required
def fix_orphaned_vehicles():
    """Fix vehicles that are 'in_use' but have no active trip"""
    try:
        # Find orphaned vehicles
        orphaned = []
        in_use_vehicles = Vehicle.query.filter_by(status='in_use').all()
        
        for v in in_use_vehicles:
            active_trip = Trip.query.filter_by(
                vehicle_id=v.id,
                status='in_progress'
            ).first()
            
            if not active_trip:
                orphaned.append(v)
                # Fix: Set back to available
                v.status = 'available'
                v.lock_status = 'locked'
                v.is_locked = True
        
        if not orphaned:
            return jsonify({
                'success': True,
                'message': 'No orphaned vehicles found',
                'fixed_count': 0
            })
        
        # Commit changes
        db.session.commit()
        
        # Sync to Firebase
        from flask import current_app
        if current_app.config.get('FIREBASE_ENABLED', False):
            for v in orphaned:
                VehicleRepository.update_fields(v.id, {
                    'status': 'available',
                    'lock_status': 'locked',
                    'is_locked': True
                })
        
        return jsonify({
            'success': True,
            'message': f'Fixed {len(orphaned)} orphaned vehicles',
            'fixed_count': len(orphaned),
            'vehicles': [v.vehicle_code for v in orphaned]
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin_bp.route('/system/check-consistency', methods=['GET'])
@login_required
@admin_required
def check_system_consistency():
    """Check data consistency between vehicles and trips"""
    # Check orphaned vehicles
    orphaned_vehicles = []
    in_use_vehicles = Vehicle.query.filter_by(status='in_use').all()
    
    for v in in_use_vehicles:
        active_trip = Trip.query.filter_by(
            vehicle_id=v.id,
            status='in_progress'
        ).first()
        
        if not active_trip:
            orphaned_vehicles.append({
                'id': v.id,
                'code': v.vehicle_code,
                'status': v.status
            })
    
    # Check orphaned trips
    orphaned_trips = []
    active_trips = Trip.query.filter_by(status='in_progress').all()
    
    for t in active_trips:
        v = Vehicle.query.get(t.vehicle_id)
        if v and v.status != 'in_use':
            orphaned_trips.append({
                'id': t.id,
                'code': t.trip_code,
                'vehicle_code': v.vehicle_code,
                'vehicle_status': v.status
            })
    
    # Vehicle status summary
    vehicle_status = {}
    for v in Vehicle.query.all():
        vehicle_status[v.status] = vehicle_status.get(v.status, 0) + 1
    
    # Trip status summary
    today = datetime.now().date()
    today_start = datetime.combine(today, datetime.min.time())
    trip_status = {}
    for t in Trip.query.filter(Trip.created_at >= today_start).all():
        trip_status[t.status] = trip_status.get(t.status, 0) + 1
    
    return jsonify({
        'vehicle_status': vehicle_status,
        'trip_status': trip_status,
        'orphaned_vehicles': orphaned_vehicles,
        'orphaned_trips': orphaned_trips,
        'is_consistent': len(orphaned_vehicles) == 0 and len(orphaned_trips) == 0
    })
