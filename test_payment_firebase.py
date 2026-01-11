"""
Test Payment Firebase sync
"""
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.utils.firebase_client import init_firebase, get_db
from app.utils.repositories import PaymentRepository
from flask import Flask
from config import config

def test_payment_sync():
    """Test payment sync to Firebase"""
    print("\n" + "="*60)
    print("KIỂM TRA ĐỒNG BỘ PAYMENT LÊN FIREBASE")
    print("="*60)
    
    # Create Flask app
    app = Flask(__name__)
    app.config.from_object(config['development'])
    app.config['FIREBASE_ENABLED'] = True
    
    with app.app_context():
        print("\n1. Khởi tạo Firebase...")
        init_firebase(app)
        
        db = get_db()
        if db is None:
            print("❌ Không thể kết nối Firebase")
            return False
        
        print("✅ Đã kết nối Firebase")
        
        # Test payment topup
        print("\n2. Test payment topup...")
        test_payment = {
            'payment_code': f'TEST_TOPUP_{datetime.now().strftime("%Y%m%d%H%M%S")}',
            'user_id': 1,
            'trip_id': None,  # topup không có trip_id
            'amount': 100000,
            'payment_method': 'wallet',
            'payment_status': 'completed',
            'transaction_date': datetime.utcnow(),
            'transaction_id': 'DEMO_TEST_123',
            'created_at': datetime.utcnow()
        }
        
        payment_id = PaymentRepository.add(test_payment)
        if payment_id:
            print(f"✅ Đã tạo payment test: {payment_id}")
            print(f"   Mã: {test_payment['payment_code']}")
            print(f"   Số tiền: {test_payment['amount']:,} VND")
        else:
            print("❌ Không thể tạo payment")
            return False
        
        # Test read
        print("\n3. Test đọc payment...")
        payment_data = PaymentRepository.get_by_id(payment_id)
        if payment_data:
            print(f"✅ Đọc payment: {payment_data.get('payment_code')}")
            print(f"   User ID: {payment_data.get('user_id')}")
            print(f"   Amount: {payment_data.get('amount'):,} VND")
            print(f"   Status: {payment_data.get('payment_status')}")
        
        # Test update
        print("\n4. Test cập nhật payment...")
        update_result = PaymentRepository.update_fields(payment_id, {
            'payment_status': 'completed',
            'updated_at': datetime.utcnow()
        })
        
        if update_result:
            print("✅ Đã cập nhật payment")
        else:
            print("❌ Không thể cập nhật payment")
        
        print("\n" + "="*60)
        print("✅ TEST PAYMENT FIREBASE HOÀN TẤT!")
        print("="*60)
        print("\n📋 Kiểm tra trên Firebase Console:")
        print("   https://console.firebase.google.com/project/smartrent-its/firestore")
        print("\n📁 Collection: payments")
        print("\n💡 Khi user nạp tiền, payment sẽ tự động lưu lên Firestore!")
        print("="*60 + "\n")
        
        return True

if __name__ == '__main__':
    try:
        test_payment_sync()
    except Exception as e:
        print(f"\n❌ LỖI: {e}")
        import traceback
        traceback.print_exc()
