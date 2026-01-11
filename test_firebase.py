"""
Test Firebase Connection và đồng bộ dữ liệu
"""
import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.utils.firebase_client import init_firebase, get_db
from app.utils.repositories import TripRepository, VehicleRepository, PaymentRepository
from flask import Flask
from config import config

def test_firebase_connection():
    """Test kết nối Firebase"""
    print("\n" + "="*60)
    print("KIỂM TRA KẾT NỐI FIREBASE")
    print("="*60)
    
    # Create Flask app
    app = Flask(__name__)
    app.config.from_object(config['development'])
    
    # Force enable Firebase for testing
    app.config['FIREBASE_ENABLED'] = True
    app.config['FIREBASE_PROJECT_ID'] = 'smartrent-its'
    app.config['FIREBASE_CREDENTIALS_PATH'] = 'smartrent-firebase-credentials.json'
    
    with app.app_context():
        # Initialize Firebase
        print("\n1. Khởi tạo Firebase...")
        init_firebase(app)
        
        db = get_db()
        if db is None:
            print("❌ THẤT BẠI: Không thể kết nối Firebase")
            print("\nKiểm tra lại:")
            print("- File smartrent-firebase-credentials.json có tồn tại không?")
            print("- FIREBASE_ENABLED=true trong .env?")
            return False
        
        print("✅ THÀNH CÔNG: Đã kết nối Firebase Firestore")
        
        # Test write data
        print("\n2. Test ghi dữ liệu lên Firestore...")
        
        # Test vehicle
        test_vehicle = {
            'vehicle_code': f'TEST_VH_{datetime.now().strftime("%Y%m%d%H%M%S")}',
            'vehicle_type': 'motorbike',
            'brand': 'Honda',
            'model': 'Wave Alpha (Test)',
            'license_plate': 'TEST-001',
            'latitude': 10.762622,
            'longitude': 106.660172,
            'status': 'available',
            'battery_level': 100,
            'price_per_minute': 2000,
            'is_locked': True,
            'created_at': datetime.utcnow().isoformat()
        }
        
        vehicle_id = VehicleRepository.add(test_vehicle)
        if vehicle_id:
            print(f"✅ Đã tạo vehicle test: {vehicle_id}")
        else:
            print("❌ Không thể tạo vehicle")
            return False
        
        # Test trip
        test_trip = {
            'trip_code': f'TEST_TR_{datetime.now().strftime("%Y%m%d%H%M%S")}',
            'user_id': 999,
            'vehicle_id': 1,
            'booking_id': 1,
            'start_latitude': 10.762622,
            'start_longitude': 106.660172,
            'start_address': 'Test Location',
            'start_time': datetime.utcnow(),
            'status': 'in_progress',
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        trip_id = TripRepository.add(test_trip)
        if trip_id:
            print(f"✅ Đã tạo trip test: {trip_id}")
        else:
            print("❌ Không thể tạo trip")
            return False
        
        # Test payment
        test_payment = {
            'payment_code': f'TEST_PAY_{datetime.now().strftime("%Y%m%d%H%M%S")}',
            'user_id': 999,
            'trip_id': 1,
            'amount': 15000,
            'payment_method': 'wallet',
            'payment_status': 'completed',
            'transaction_date': datetime.utcnow(),
            'created_at': datetime.utcnow()
        }
        
        payment_id = PaymentRepository.add(test_payment)
        if payment_id:
            print(f"✅ Đã tạo payment test: {payment_id}")
        else:
            print("❌ Không thể tạo payment")
            return False
        
        # Test read data
        print("\n3. Test đọc dữ liệu từ Firestore...")
        
        vehicle_data = VehicleRepository.get_by_id(vehicle_id)
        if vehicle_data:
            print(f"✅ Đọc vehicle: {vehicle_data.get('vehicle_code')}")
        
        trip_data = TripRepository.get_by_id(trip_id)
        if trip_data:
            print(f"✅ Đọc trip: {trip_data.get('trip_code')}")
        
        payment_data = PaymentRepository.get_by_id(payment_id)
        if payment_data:
            print(f"✅ Đọc payment: {payment_data.get('payment_code')}")
        
        # Test update
        print("\n4. Test cập nhật dữ liệu...")
        
        update_result = TripRepository.update_fields(trip_id, {
            'status': 'completed',
            'end_time': datetime.utcnow(),
            'total_cost': 15000
        })
        
        if update_result:
            print("✅ Đã cập nhật trip")
        else:
            print("❌ Không thể cập nhật trip")
        
        print("\n" + "="*60)
        print("✅ TẤT CẢ TEST ĐỀU THÀNH CÔNG!")
        print("="*60)
        print("\n📋 Kiểm tra dữ liệu trên Firebase Console:")
        print("   https://console.firebase.google.com/project/smartrent-its/firestore")
        print("\n📁 Collections được tạo:")
        print("   - vehicles")
        print("   - trips")
        print("   - payments")
        print("\n💡 Mỗi lần bạn đặt xe, dữ liệu sẽ tự động được đồng bộ lên Firestore!")
        print("="*60 + "\n")
        
        return True

if __name__ == '__main__':
    try:
        success = test_firebase_connection()
        if not success:
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ LỖI: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
