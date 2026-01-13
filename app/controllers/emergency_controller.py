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
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    alert_code = f"ALERT{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # Convert latitude/longitude to float if provided
    latitude = None
    longitude = None
    if data.get('latitude'):
        try:
            latitude = float(data.get('latitude'))
        except (ValueError, TypeError):
            pass
    if data.get('longitude'):
        try:
            longitude = float(data.get('longitude'))
        except (ValueError, TypeError):
            pass
    
    alert = EmergencyAlert(
        alert_code=alert_code,
        user_id=current_user.id,
        vehicle_id=data.get('vehicle_id'),
        trip_id=data.get('trip_id'),
        alert_type=data.get('alert_type', 'emergency'),
        severity=data.get('severity', 'medium'),
        description=data.get('description', ''),
        latitude=latitude,
        longitude=longitude,
        address=data.get('address', ''),
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
        print(f"Error creating emergency alert: {str(e)}")
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
    # Admin xem tất cả alerts, user chỉ xem của mình
    if current_user.role == 'admin':
        alerts = EmergencyAlert.query.order_by(EmergencyAlert.created_at.desc()).all()
        is_admin = True
    else:
        alerts = EmergencyAlert.query.filter_by(user_id=current_user.id)\
            .order_by(EmergencyAlert.created_at.desc()).all()
        is_admin = False
    
    # Get all available vehicles for the emergency form
    user_vehicles = Vehicle.query.all()
    
    return render_template('emergency/my_alerts.html', alerts=alerts, is_admin=is_admin, user_vehicles=user_vehicles)


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


@emergency_bp.route('/<int:alert_id>/update', methods=['POST'])
@login_required
def update_alert(alert_id):
    """Cập nhật trạng thái cảnh báo (Admin only)"""
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    alert = EmergencyAlert.query.get_or_404(alert_id)
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    try:
        # Update fields
        if 'status' in data:
            alert.status = data['status']
        if 'response_team' in data:
            alert.response_team = data['response_team']
        if 'resolution_notes' in data:
            alert.resolution_notes = data['resolution_notes']
        
        # Set response time if status changes to 'responding'
        if data.get('status') == 'responding' and not alert.response_time:
            alert.response_time = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Đã cập nhật trạng thái cảnh báo'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@emergency_bp.route('/<int:alert_id>/edit', methods=['POST'])
@login_required
def edit_alert(alert_id):
    """Chỉnh sửa cảnh báo (User only, status must be 'open')"""
    alert = EmergencyAlert.query.get_or_404(alert_id)
    
    # Only the alert creator can edit, and only if status is 'open'
    if alert.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    if alert.status != 'open':
        return jsonify({'error': 'Chỉ có thể chỉnh sửa cảnh báo ở trạng thái "Đang mở"'}), 400
    
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    try:
        # Update fields
        if 'alert_type' in data:
            alert.alert_type = data['alert_type']
        if 'severity' in data:
            alert.severity = data['severity']
        if 'description' in data:
            alert.description = data['description']
        
        alert.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Đã cập nhật cảnh báo'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@emergency_bp.route('/<int:alert_id>/delete', methods=['POST'])
@login_required
def delete_alert(alert_id):
    """Xóa cảnh báo (User only, status must be 'open')"""
    alert = EmergencyAlert.query.get_or_404(alert_id)
    
    # Only the alert creator can delete, and only if status is 'open'
    if alert.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    if alert.status != 'open':
        return jsonify({'error': 'Chỉ có thể xóa cảnh báo ở trạng thái "Đang mở"'}), 400
    
    try:
        alert_code = alert.alert_code
        db.session.delete(alert)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Đã xóa cảnh báo {alert_code}'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
