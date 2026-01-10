from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app.models import db, User, Vehicle, Booking, Trip, Payment, Maintenance, EmergencyAlert, IoTLog
from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_
from functools import wraps

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
        
        vehicle_code = f"VH{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        vehicle = Vehicle(
            vehicle_code=vehicle_code,
            vehicle_type=data.get('vehicle_type'),
            brand=data.get('brand'),
            model=data.get('model'),
            license_plate=data.get('license_plate'),
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
            return redirect(url_for('admin.manage_vehicles'))
        except Exception as e:
            db.session.rollback()
            return f"Error: {str(e)}", 500
    
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
    return render_template('admin/analytics.html')
