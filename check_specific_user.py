"""Kiểm tra chi tiết user cụ thể"""
from app import create_app
from app.models import db, User
from app.utils.firebase_client import get_db

app = create_app()

with app.app_context():
    # Tìm user trong SQLite
    print('='*70)
    print('CHECKING USER: nguyenchitrung2702@gmail.com')
    print('='*70)
    
    user = User.query.filter_by(email='nguyenchitrung2702@gmail.com').first()
    
    if user:
        print(f'\n✅ Found in SQLite:')
        print(f'   ID: {user.id}')
        print(f'   Username: {user.username}')
        print(f'   Email: {user.email}')
        print(f'   Full Name: {user.full_name}')
        print(f'   Phone: {user.phone}')
        print(f'   Role: {user.role}')
        print(f'   Created: {user.created_at}')
        
        # Check Firebase
        fs_db = get_db()
        if fs_db:
            print(f'\n🔍 Checking Firebase for user ID {user.id}...')
            doc = fs_db.collection('users').document(str(user.id)).get()
            
            if doc.exists:
                data = doc.to_dict()
                print(f'✅ Found in Firebase:')
                print(f'   ID: {data.get("id")}')
                print(f'   Username: {data.get("username")}')
                print(f'   Email: {data.get("email")}')
                print(f'   Full Name: {data.get("full_name")}')
                print(f'   Phone: {data.get("phone")}')
                print(f'   Role: {data.get("role")}')
                print(f'   Created: {data.get("created_at")}')
                
                # Compare
                if data.get('email') != user.email:
                    print(f'\n⚠️  WARNING: Email mismatch!')
                    print(f'   SQLite: {user.email}')
                    print(f'   Firebase: {data.get("email")}')
                    print(f'\n💡 Need to re-sync this user!')
                else:
                    print(f'\n✅ Data matches!')
            else:
                print(f'❌ NOT found in Firebase with ID {user.id}')
                print(f'\n💡 Need to sync this user to Firebase!')
                
                # Sync it
                print(f'\n🔄 Syncing user to Firebase...')
                from datetime import datetime
                user_data = {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'full_name': user.full_name,
                    'phone': user.phone,
                    'role': user.role,
                    'wallet_balance': float(user.wallet_balance),
                    'is_active': user.is_active,
                    'created_at': user.created_at.isoformat() if user.created_at else datetime.utcnow().isoformat(),
                    'synced_from': 'manual_fix',
                    'synced_at': datetime.utcnow().isoformat()
                }
                fs_db.collection('users').document(str(user.id)).set(user_data)
                print(f'✅ User synced successfully!')
    else:
        print(f'\n❌ User not found in SQLite!')
    
    print(f'\n{'='*70}')
