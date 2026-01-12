from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required, current_user
from app.models import db, Payment, User
from app.utils.repositories import PaymentRepository
from app.utils.notification_helper import notify_payment_topup
from datetime import datetime
import os

payment_bp = Blueprint('payment', __name__, url_prefix='/payments')

# Chỉ sử dụng ví nội bộ - MIỄN PHÍ, không cần Stripe

@payment_bp.route('/wallet')
@login_required
def wallet():
    """Ví điện tử"""
    transactions = Payment.query.filter_by(user_id=current_user.id)\
        .order_by(Payment.created_at.desc())\
        .limit(20).all()
    
    return render_template('payments/wallet.html', 
                         balance=current_user.wallet_balance,
                         transactions=transactions)


@payment_bp.route('/topup', methods=['GET', 'POST'])
@login_required
def topup():
    """Nạp tiền vào ví"""
    if request.method == 'POST':
        data = request.get_json()
        amount = float(data.get('amount', 0))
        
        if amount <= 0:
            return jsonify({'error': 'Số tiền không hợp lệ'}), 400
        
        payment_method = data.get('payment_method', 'stripe')
        
        # Create payment record
        payment_code = f"TOP{datetime.now().strftime('%Y%m%d%H%M%S')}"
        payment = Payment(
            payment_code=payment_code,
            user_id=current_user.id,
            amount=amount,
            payment_method=payment_method,
            payment_status='pending'
        )
        
        try:
            # Nạp tiền trực tiếp vào ví (DEMO/FREE version)
            # Trong thực tế, có thể tích hợp: MoMo, ZaloPay, VNPay (miễn phí sandbox)
            payment.payment_status = 'completed'
            payment.transaction_date = datetime.utcnow()
            payment.transaction_id = f"DEMO{payment_code}"
            current_user.wallet_balance += amount
            
            db.session.add(payment)
            db.session.commit()
            
            # Tạo thông báo nạp tiền thành công
            notify_payment_topup(current_user.id, amount, payment.id)
            
            # Đồng bộ lên Firebase nếu được bật
            if current_app.config.get('FIREBASE_ENABLED', False):
                payment_data = {
                    'payment_code': payment.payment_code,
                    'user_id': payment.user_id,
                    'trip_id': payment.trip_id,
                    'amount': payment.amount,
                    'payment_method': payment.payment_method,
                    'payment_status': payment.payment_status,
                    'transaction_date': payment.transaction_date,
                    'transaction_id': payment.transaction_id,
                    'created_at': datetime.utcnow()
                }
                firebase_payment_id = PaymentRepository.add(payment_data, doc_id=str(payment.id))
                if firebase_payment_id:
                    print(f'[Firebase] Payment topup {payment_code} synced to Firestore: {firebase_payment_id}')
            
            return jsonify({
                'success': True,
                'message': f'Đã nạp {amount:,.0f} VND vào ví',
                'new_balance': current_user.wallet_balance
            })
                
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500
    
    return render_template('payments/topup.html')


@payment_bp.route('/confirm', methods=['POST'])
@login_required
def confirm_payment():
    """Xác nhận thanh toán"""
    data = request.get_json()
    payment_code = data.get('payment_code')
    
    payment = Payment.query.filter_by(payment_code=payment_code).first()
    
    if not payment or payment.user_id != current_user.id:
        return jsonify({'error': 'Không tìm thấy thanh toán'}), 404
    
    if payment.payment_status == 'completed':
        return jsonify({'error': 'Thanh toán đã được xử lý'}), 400
    
    # Update payment status
    payment.payment_status = 'completed'
    payment.transaction_date = datetime.utcnow()
    
    # Add to wallet if it's a top-up
    if not payment.trip_id:
        current_user.wallet_balance += payment.amount
    
    try:
        db.session.commit()
        
        # Đồng bộ lên Firebase nếu được bật
        if current_app.config.get('FIREBASE_ENABLED', False):
            PaymentRepository.update_fields(str(payment.id), {
                'payment_status': 'completed',
                'transaction_date': payment.transaction_date,
                'updated_at': datetime.utcnow()
            })
            print(f'[Firebase] Payment {payment_code} confirmed in Firestore')
        
        return jsonify({
            'success': True,
            'message': 'Thanh toán thành công',
            'new_balance': current_user.wallet_balance
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@payment_bp.route('/history')
@login_required
def payment_history():
    """Lịch sử thanh toán"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    payments = Payment.query.filter_by(user_id=current_user.id)\
        .order_by(Payment.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('payments/history.html', payments=payments)


@payment_bp.route('/invoice/<int:payment_id>')
@login_required
def invoice(payment_id):
    """Hóa đơn"""
    payment = Payment.query.get_or_404(payment_id)
    
    if payment.user_id != current_user.id and current_user.role != 'admin':
        return "Unauthorized", 403
    
    return render_template('payments/invoice.html', payment=payment)
