from app.models import db, Notification
from datetime import datetime

def create_notification(user_id, type, title, message, icon=None, color=None, related_id=None, related_type=None, action_url=None):
    """
    Tạo thông báo mới cho user
    
    Args:
        user_id: ID của user nhận thông báo
        type: Loại thông báo (payment, trip, emergency, system, promotion)
        title: Tiêu đề thông báo
        message: Nội dung thông báo
        icon: Font Awesome icon class (vd: fa-wallet, fa-car)
        color: Màu sắc (success, danger, warning, info, primary)
        related_id: ID liên quan (payment_id, trip_id, etc.)
        related_type: Loại liên quan (payment, trip, emergency_alert)
        action_url: URL khi click vào thông báo
    """
    notification = Notification(
        user_id=user_id,
        type=type,
        title=title,
        message=message,
        icon=icon,
        color=color,
        related_id=related_id,
        related_type=related_type,
        action_url=action_url
    )
    
    db.session.add(notification)
    try:
        db.session.commit()
        return notification
    except Exception as e:
        db.session.rollback()
        print(f"Error creating notification: {str(e)}")
        return None


def notify_payment_topup(user_id, amount, payment_id):
    """Thông báo nạp tiền thành công"""
    return create_notification(
        user_id=user_id,
        type='payment',
        title='Nạp tiền thành công',
        message=f'Bạn đã nạp {amount:,.0f} ₫ vào ví. Số dư hiện tại đã được cập nhật.',
        icon='fa-wallet',
        color='success',
        related_id=payment_id,
        related_type='payment',
        action_url='/payments/wallet'
    )


def notify_payment_deduct(user_id, amount, trip_id):
    """Thông báo trừ tiền sau chuyến đi"""
    return create_notification(
        user_id=user_id,
        type='payment',
        title='Thanh toán chuyến đi',
        message=f'Đã trừ {amount:,.0f} ₫ từ ví của bạn cho chuyến đi.',
        icon='fa-money-bill-wave',
        color='warning',
        related_id=trip_id,
        related_type='trip',
        action_url=f'/trips/{trip_id}'
    )


def notify_trip_started(user_id, vehicle_code, trip_id):
    """Thông báo bắt đầu chuyến đi"""
    return create_notification(
        user_id=user_id,
        type='trip',
        title='Chuyến đi bắt đầu',
        message=f'Bạn đã bắt đầu chuyến đi với xe {vehicle_code}. Chúc bạn đi đường an toàn!',
        icon='fa-route',
        color='info',
        related_id=trip_id,
        related_type='trip',
        action_url=f'/trips/active'
    )


def notify_trip_completed(user_id, vehicle_code, duration, amount, trip_id):
    """Thông báo hoàn thành chuyến đi"""
    # Format duration better
    if duration < 1:
        seconds = int(duration * 60)
        duration_text = f"{seconds} giây"
    elif duration < 60:
        duration_text = f"{int(duration)} phút"
    else:
        hours = int(duration // 60)
        mins = int(duration % 60)
        duration_text = f"{hours}h {mins}p"
    
    return create_notification(
        user_id=user_id,
        type='trip',
        title='Chuyến đi hoàn thành',
        message=f'Chuyến đi với xe {vehicle_code} đã hoàn thành. Thời gian: {duration_text}. Chi phí: {amount:,.0f} ₫',
        icon='fa-check-circle',
        color='success',
        related_id=trip_id,
        related_type='trip',
        action_url=f'/trips/{trip_id}'
    )


def notify_emergency_alert(user_id, alert_type, alert_id):
    """Thông báo cảnh báo khẩn cấp"""
    return create_notification(
        user_id=user_id,
        type='emergency',
        title='Cảnh báo khẩn cấp',
        message=f'Cảnh báo {alert_type} của bạn đã được gửi. Đội ứng cứu sẽ liên hệ sớm.',
        icon='fa-exclamation-triangle',
        color='danger',
        related_id=alert_id,
        related_type='emergency_alert',
        action_url='/emergency/my-alerts'
    )


def notify_system_message(user_id, title, message):
    """Thông báo hệ thống"""
    return create_notification(
        user_id=user_id,
        type='system',
        title=title,
        message=message,
        icon='fa-info-circle',
        color='info'
    )


def notify_promotion(user_id, title, message, action_url=None):
    """Thông báo khuyến mãi"""
    return create_notification(
        user_id=user_id,
        type='promotion',
        title=title,
        message=message,
        icon='fa-gift',
        color='primary',
        action_url=action_url
    )


def mark_notification_as_read(notification_id):
    """Đánh dấu thông báo đã đọc"""
    notification = Notification.query.get(notification_id)
    if notification:
        notification.is_read = True
        notification.read_at = datetime.utcnow()
        try:
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error marking notification as read: {str(e)}")
    return False


def delete_notification(notification_id):
    """Xóa thông báo (soft delete)"""
    notification = Notification.query.get(notification_id)
    if notification:
        notification.is_deleted = True
        try:
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error deleting notification: {str(e)}")
    return False


def mark_all_as_read(user_id):
    """Đánh dấu tất cả thông báo của user đã đọc"""
    try:
        Notification.query.filter_by(
            user_id=user_id,
            is_read=False,
            is_deleted=False
        ).update({
            'is_read': True,
            'read_at': datetime.utcnow()
        })
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        print(f"Error marking all notifications as read: {str(e)}")
        return False
