"""Test script để kiểm tra sync Firebase khi đăng ký user"""
from app import create_app
from app.models import db, User
from app.utils.firebase_client import get_db
from datetime import datetime
import random

app = create_app()

with app.app_context():
    # Tạo user test
    random_num = random.randint(1000, 9999)
    test_user = User(
        username=f'testuser{random_num}',
        email=f'testuser{random_num}@test.com',
        full_name=f'Test User {random_num}',
        phone=f'0900{random_num}',
        role='customer'
    )
    test_user.set_password('password123')
    
    try:
        print(f'\n{"="*60}')
        print('TESTING USER REGISTRATION & FIREBASE SYNC')
        print(f'{"="*60}\n')
        
        # Add to DB
        print(f'1️⃣ Adding user to database...')
        db.session.add(test_user)
        db.session.commit()
        print(f'   ✅ User saved to DB with ID: {test_user.id}')
        
        # Check Firebase config
        print(f'\n2️⃣ Checking Firebase configuration...')
        firebase_enabled = app.config.get('FIREBASE_ENABLED')
        print(f'   FIREBASE_ENABLED: {firebase_enabled}')
        
        if not firebase_enabled:
            print('   ❌ Firebase is DISABLED in config!')
            print('   💡 Set FIREBASE_ENABLED=true in .env or config.py')
        else:
            print(f'   ✅ Firebase is enabled')
            
            # Get Firestore client
            print(f'\n3️⃣ Getting Firestore client...')
            fs_db = get_db()
            
            if fs_db is None:
                print('   ❌ Firestore client is None!')
                print('   💡 Check firebase_client.py initialization')
            else:
                print(f'   ✅ Firestore client obtained: {type(fs_db)}')
                
                # Sync to Firestore
                print(f'\n4️⃣ Syncing to Firestore...')
                try:
                    user_data = {
                        'id': test_user.id,
                        'username': test_user.username,
                        'email': test_user.email,
                        'full_name': test_user.full_name,
                        'phone': test_user.phone,
                        'role': test_user.role,
                        'wallet_balance': float(test_user.wallet_balance),
                        'is_active': test_user.is_active,
                        'created_at': datetime.utcnow().isoformat(),
                        'synced_from': 'test_script'
                    }
                    
                    print(f'   Data to sync: {user_data}')
                    doc_ref = fs_db.collection('users').document(str(test_user.id))
                    doc_ref.set(user_data)
                    print(f'   ✅ Successfully synced to Firestore!')
                    print(f'   📍 Document path: users/{test_user.id}')
                    
                    # Verify by reading back
                    print(f'\n5️⃣ Verifying sync by reading from Firestore...')
                    doc = doc_ref.get()
                    if doc.exists:
                        print(f'   ✅ Document exists in Firestore!')
                        print(f'   Data: {doc.to_dict()}')
                    else:
                        print(f'   ❌ Document not found in Firestore!')
                        
                except Exception as firebase_error:
                    print(f'   ❌ Failed to sync: {firebase_error}')
                    import traceback
                    traceback.print_exc()
        
        print(f'\n{"="*60}')
        print('TEST COMPLETED')
        print(f'{"="*60}\n')
        
        # Cleanup
        print('🧹 Cleaning up test user from database...')
        db.session.delete(test_user)
        db.session.commit()
        print('   ✅ Test user deleted from database')
        
        if firebase_enabled and fs_db:
            print('🧹 Cleaning up test user from Firestore...')
            try:
                fs_db.collection('users').document(str(test_user.id)).delete()
                print('   ✅ Test user deleted from Firestore')
            except Exception as e:
                print(f'   ⚠️  Failed to delete from Firestore: {e}')
                
    except Exception as e:
        db.session.rollback()
        print(f'\n❌ Error: {e}')
        import traceback
        traceback.print_exc()
