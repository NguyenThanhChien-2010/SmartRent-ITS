from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app.models import db, EmergencyAlert, Vehicle, Trip
from datetime import datetime

emergency_bp = Blueprint('emergency', __name__, url_prefix='/emergency')

@emergency_bp.route('/report', methods=['POST'])
@login_required
def report_emergency():
    """Báo cáo khẩn cấp (eCall)"""
    data = request.get_json()
    
    alert_code = f"ALERT{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    alert = EmergencyAlert(
        alert_code=alert_code,
        user_id=current_user.id,
        vehicle_id=data.get('vehicle_id'),
        trip_id=data.get('trip_id'),
        alert_type=data.get('alert_type'),  # accident, breakdown, theft, medical
        severity=data.get('severity', 'medium'),
        description=data.get('description'),
        latitude=data.get('latitude'),
        longitude=data.get('longitude'),
        address=data.get('address'),
        status='open'
    )
    
    try:
        db.session.add(alert)
        db.session.commit()
        
        # TODO: Send notification to admin team
        # TODO: Send SMS/Email alert
        
        return jsonify({
            'success': True,
            'alert_code': alert_code,
            'message': 'Đã gửi cảnh báo. Đội ứng cứu sẽ liên hệ sớm.'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@emergency_bp.route('/button/<int:vehicle_id>', methods=['POST'])
@login_required
def emergency_button(vehicle_id):
    """Nút SOS trên xe"""
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    
    # Find active trip
    active_trip = Trip.query.filter_by(
        user_id=current_user.id,
        vehicle_id=vehicle_id,
        status='in_progress'
    ).first()
    
    alert_code = f"SOS{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    alert = EmergencyAlert(
        alert_code=alert_code,
        user_id=current_user.id,
        vehicle_id=vehicle_id,
        trip_id=active_trip.id if active_trip else None,
        alert_type='emergency',
        severity='critical',
        description='Nút SOS được kích hoạt',
        latitude=vehicle.latitude,
        longitude=vehicle.longitude,
        status='open'
    )
    
    try:
        db.session.add(alert)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'alert_code': alert_code,
            'message': 'Đã gửi tín hiệu SOS!'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@emergency_bp.route('/my-alerts')
@login_required
def my_alerts():
    """Danh sách cảnh báo của tôi"""
    alerts = EmergencyAlert.query.filter_by(user_id=current_user.id)\
        .order_by(EmergencyAlert.created_at.desc()).all()
    
    return render_template('emergency/my_alerts.html', alerts=alerts)


@emergency_bp.route('/<int:alert_id>/status')
@login_required
def alert_status(alert_id):
    """Trạng thái cảnh báo"""
    alert = EmergencyAlert.query.get_or_404(alert_id)
    
    if alert.user_id != current_user.id and current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    return jsonify({
        'alert_code': alert.alert_code,
        'status': alert.status,
        'response_team': alert.response_team,
        'response_time': alert.response_time.isoformat() if alert.response_time else None,
        'resolution_notes': alert.resolution_notes
    })
