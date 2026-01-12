"""
Email Helper for SmartRent ITS
Handles sending OTP and notification emails
"""
from flask import current_app, render_template_string
from flask_mail import Mail, Message
from datetime import datetime, timedelta
import secrets

mail = Mail()

# In-memory OTP storage (for demo - use Redis in production)
otp_storage = {}

def generate_otp(trip_id, email, pin):
    """Generate 6-digit OTP and store with expiry"""
    otp = pin  # Use Smart PIN as OTP
    
    # Store OTP with 5 minute expiry
    otp_storage[trip_id] = {
        'otp': otp,
        'email': email,
        'created_at': datetime.utcnow(),
        'expires_at': datetime.utcnow() + timedelta(minutes=5)
    }
    
    return otp

def verify_otp(trip_id, otp):
    """Verify OTP is valid and not expired"""
    stored_data = otp_storage.get(trip_id)
    
    if not stored_data:
        return False, "Mã OTP không tồn tại"
    
    if datetime.utcnow() > stored_data['expires_at']:
        del otp_storage[trip_id]
        return False, "Mã OTP đã hết hạn"
    
    if stored_data['otp'] != otp:
        return False, "Mã OTP không chính xác"
    
    # OTP valid - remove it after use
    del otp_storage[trip_id]
    return True, "Xác thực thành công"

def send_otp_email(to_email, trip_code, vehicle_code, otp):
    """Send OTP email to user"""
    try:
        email_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px; }}
                .container {{ max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ text-align: center; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px 10px 0 0; margin: -30px -30px 30px -30px; }}
                .otp-box {{ background-color: #f8f9fa; border: 2px dashed #667eea; padding: 20px; text-align: center; margin: 20px 0; border-radius: 10px; }}
                .otp-code {{ font-size: 36px; font-weight: bold; color: #667eea; letter-spacing: 10px; }}
                .info-box {{ background-color: #e7f3ff; padding: 15px; border-left: 4px solid #2196F3; margin: 20px 0; }}
                .footer {{ text-align: center; color: #666; font-size: 12px; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; }}
                .warning {{ color: #ff6b6b; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚗 SmartRent ITS</h1>
                    <p>Intelligent Transportation System</p>
                </div>
                
                <h2>Mã OTP Mở Khóa Xe</h2>
                <p>Xin chào,</p>
                <p>Bạn vừa yêu cầu mở khóa xe thông qua Email OTP Verification. Đây là mã xác thực của bạn:</p>
                
                <div class="otp-box">
                    <div style="color: #666; font-size: 14px; margin-bottom: 10px;">MÃ OTP CỦA BẠN</div>
                    <div class="otp-code">{otp}</div>
                    <div style="color: #999; font-size: 12px; margin-top: 10px;">Nhập mã này trên trang web để mở khóa xe</div>
                </div>
                
                <div class="info-box">
                    <strong>📋 Thông tin chuyến đi:</strong><br>
                    • Mã chuyến đi: <strong>{trip_code}</strong><br>
                    • Mã xe: <strong>{vehicle_code}</strong><br>
                    • Thời gian: {datetime.now().strftime('%H:%M:%S - %d/%m/%Y')}
                </div>
                
                <p class="warning">⚠️ Lưu ý quan trọng:</p>
                <ul>
                    <li>Mã OTP có hiệu lực trong <strong>5 phút</strong></li>
                    <li>Không chia sẻ mã này với bất kỳ ai</li>
                    <li>Nếu không phải bạn yêu cầu, vui lòng bỏ qua email này</li>
                </ul>
                
                <div style="text-align: center; margin-top: 30px;">
                    <p style="color: #666;">Chúc bạn có chuyến đi an toàn! 🛡️</p>
                </div>
                
                <div class="footer">
                    <p><strong>SmartRent - Intelligent Transportation System</strong></p>
                    <p>Email tự động, vui lòng không trả lời</p>
                    <p>© 2026 SmartRent ITS. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        msg = Message(
            subject=f'🔑 Mã OTP Mở Khóa Xe - {trip_code}',
            recipients=[to_email],
            html=email_body,
            sender=current_app.config.get('MAIL_USERNAME') or 'noreply@smartrent.com'
        )
        
        mail.send(msg)
        return True, "Email đã được gửi thành công"
        
    except Exception as e:
        current_app.logger.error(f"Failed to send OTP email: {str(e)}")
        return False, f"Lỗi gửi email: {str(e)}"

def send_unlock_notification(to_email, trip_code, vehicle_code):
    """Send notification when vehicle is unlocked"""
    try:
        email_body = f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: Arial; padding: 20px;">
            <h2 style="color: #28a745;">✅ Xe đã được mở khóa thành công!</h2>
            <p>Chuyến đi <strong>{trip_code}</strong> của bạn đã bắt đầu.</p>
            <p><strong>Xe:</strong> {vehicle_code}</p>
            <p><strong>Thời gian:</strong> {datetime.now().strftime('%H:%M - %d/%m/%Y')}</p>
            <hr>
            <p style="color: #666; font-size: 12px;">SmartRent ITS - Intelligent Transportation System</p>
        </body>
        </html>
        """
        
        msg = Message(
            subject=f'✅ Xe {vehicle_code} đã mở khóa',
            recipients=[to_email],
            html=email_body,
            sender=current_app.config.get('MAIL_USERNAME') or 'noreply@smartrent.com'
        )
        
        mail.send(msg)
        return True, "Notification sent"
        
    except Exception as e:
        current_app.logger.error(f"Failed to send unlock notification: {str(e)}")
        return False, str(e)
