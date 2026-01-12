"""Notification Controller - Xử lý thông báo"""
from flask import Blueprint, jsonify, request, render_template
from flask_login import login_required, current_user
from app.models import db, Notification

notification_bp = Blueprint('notification', __name__, url_prefix='/notifications')


@notification_bp.route('/')
@login_required
def list_notifications():
    """Trang xem tất cả thông báo"""
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', 'all')
    per_page = 20
    
    # Base query
    query = Notification.query.filter_by(
        user_id=current_user.id,
        is_deleted=False
    )
    
    # Apply status filter
    if status_filter == 'unread':
        query = query.filter_by(is_read=False)
    elif status_filter == 'read':
        query = query.filter_by(is_read=True)
    
    notifications = query.order_by(Notification.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    # Stats
    total = Notification.query.filter_by(
        user_id=current_user.id,
        is_deleted=False
    ).count()
    
    unread = Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False,
        is_deleted=False
    ).count()
    
    return render_template('notifications/list.html',
                         notifications=notifications,
                         status_filter=status_filter,
                         total=total,
                         unread=unread)


@notification_bp.route('/<int:notif_id>/mark-read', methods=['POST'])
@login_required
def mark_as_read(notif_id):
    """Đánh dấu thông báo đã đọc"""
    notif = Notification.query.get_or_404(notif_id)
    
    # Check ownership
    if notif.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    notif.is_read = True
    notif.read_at = db.func.now()
    
    try:
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@notification_bp.route('/mark-all-read', methods=['POST'])
@login_required
def mark_all_read():
    """Đánh dấu tất cả thông báo đã đọc"""
    try:
        Notification.query.filter_by(
            user_id=current_user.id,
            is_read=False
        ).update({'is_read': True, 'read_at': db.func.now()})
        
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@notification_bp.route('/<int:notif_id>/delete', methods=['POST'])
@login_required
def delete_notification(notif_id):
    """Xóa thông báo (soft delete)"""
    notif = Notification.query.get_or_404(notif_id)
    
    # Check ownership
    if notif.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    notif.is_deleted = True
    
    try:
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@notification_bp.route('/count-unread', methods=['GET'])
@login_required
def count_unread():
    """Đếm số thông báo chưa đọc"""
    count = Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False,
        is_deleted=False
    ).count()
    
    return jsonify({'count': count})
