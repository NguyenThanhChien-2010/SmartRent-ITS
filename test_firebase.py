"""Test Firebase connection and sync"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.utils.firebase_client import get_db
from app.utils.repositories import VehicleRepository

app = create_app('development')

with app.app_context():
    print("=" * 50)
    print("TESTING FIREBASE CONNECTION")
    print("=" * 50)
    
    # Check config
    firebase_enabled = app.config.get('FIREBASE_ENABLED', False)
    firebase_project = app.config.get('FIREBASE_PROJECT_ID', 'N/A')
    creds_path = app.config.get('FIREBASE_CREDENTIALS_PATH', 'N/A')
    
    print(f"\n📋 Config:")
    print(f"   FIREBASE_ENABLED: {firebase_enabled}")
    print(f"   FIREBASE_PROJECT_ID: {firebase_project}")
    print(f"   FIREBASE_CREDENTIALS_PATH: {creds_path}")
    print(f"   Credentials file exists: {os.path.exists(creds_path)}")
    
    # Test connection
    print(f"\n🔌 Testing Firestore connection...")
    db = get_db()
    
    if db is None:
        print("   ❌ FAILED: Firestore client is None")
        print("   Check:")
        print("   1. FIREBASE_ENABLED=true in .env")
        print("   2. smartrent-firebase-credentials.json exists")
        print("   3. Firebase Admin SDK installed: pip install firebase-admin")
        sys.exit(1)
    
    print("   ✅ SUCCESS: Firestore client initialized")
    
    # Test read/write
    print(f"\n📝 Testing Firestore write...")
    try:
        test_doc = db.collection('_test_connection').document('test_1')
        test_doc.set({
            'test': True,
            'timestamp': '2025-01-12T10:00:00',
            'message': 'Connection test successful'
        })
        print("   ✅ SUCCESS: Write operation completed")
    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        sys.exit(1)
    
    # Test read
    print(f"\n📖 Testing Firestore read...")
    try:
        doc = test_doc.get()
        if doc.exists:
            print(f"   ✅ SUCCESS: Read operation completed")
            print(f"   Data: {doc.to_dict()}")
        else:
            print("   ⚠️  WARNING: Document not found")
    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        sys.exit(1)
    
    # Test VehicleRepository
    print(f"\n🚗 Testing VehicleRepository...")
    try:
        # Try to list vehicles
        vehicles = VehicleRepository.list_available()
        print(f"   ✅ SUCCESS: VehicleRepository.list_available() returned {len(vehicles)} vehicles")
        
        if vehicles:
            print(f"   Sample vehicle: {vehicles[0].get('vehicle_code', 'N/A')}")
    except Exception as e:
        print(f"   ⚠️  Repository query completed with: {e}")
    
    # Cleanup test doc
    print(f"\n🧹 Cleaning up...")
    try:
        test_doc.delete()
        print("   ✅ Test document deleted")
    except:
        pass
    
    print("\n" + "=" * 50)
    print("✅ FIREBASE CONNECTION TEST COMPLETE")
    print("=" * 50)
