"""Script để đồng bộ các users bị thiếu từ SQLite lên Firebase"""
from app import create_app
from app.models import db, User
from app.utils.firebase_client import get_db
from datetime import datetime

app = create_app()

with app.app_context():
    # Lấy tất cả users từ SQLite
    db_users = User.query.all()
    print(f'\n📊 USERS IN SQLITE DATABASE: {len(db_users)}')
    print('='*70)
    for user in db_users:
        print(f'{user.id}. {user.username} ({user.email}) - Created: {user.created_at}')
    
    # Lấy tất cả users từ Firebase
    fs_db = get_db()
    if fs_db is None:
        print('\n❌ Firebase not initialized!')
        exit(1)
    
    print(f'\n📊 USERS IN FIREBASE:')
    print('='*70)
    
    firebase_users = {}
    users_ref = fs_db.collection('users')
    docs = list(users_ref.stream())  # Convert to list immediately
    
    for doc in docs:
        user_id = int(doc.id)
        firebase_users[user_id] = doc.to_dict()
        print(f'{user_id}. {firebase_users[user_id].get("username")} ({firebase_users[user_id].get("email")})')
    
    print(f'\nTotal in Firebase: {len(firebase_users)}')
    
    # Tìm users bị thiếu
    print(f'\n🔍 FINDING MISSING USERS...')
    print('='*70)
    
    missing_users = []
    for user in db_users:
        if user.id not in firebase_users:
            missing_users.append(user)
            print(f'❌ Missing: {user.id}. {user.username} ({user.email})')
    
    if not missing_users:
        print('✅ No missing users! All users are synced.')
    else:
        print(f'\n⚠️  Found {len(missing_users)} missing user(s) in Firebase')
        
        # Hỏi user có muốn sync không
        print(f'\n🔄 Do you want to sync these users to Firebase? (y/n): ', end='')
        response = input().strip().lower()
        
        if response == 'y':
            print(f'\n🔄 SYNCING MISSING USERS TO FIREBASE...')
            print('='*70)
            
            synced_count = 0
            failed_count = 0
            
            for user in missing_users:
                try:
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
                        'synced_from': 'sync_script',
                        'synced_at': datetime.utcnow().isoformat()
                    }
                    
                    fs_db.collection('users').document(str(user.id)).set(user_data)
                    synced_count += 1
                    print(f'✅ Synced: {user.username} ({user.email})')
                    
                except Exception as e:
                    failed_count += 1
                    print(f'❌ Failed to sync {user.username}: {e}')
            
            print(f'\n{"="*70}')
            print(f'✅ Successfully synced: {synced_count} users')
            if failed_count > 0:
                print(f'❌ Failed: {failed_count} users')
            print(f'{"="*70}')
            
            # Verify
            print(f'\n🔍 VERIFYING SYNC...')
            docs = list(fs_db.collection('users').stream())  # Convert to list
            firebase_user_count = len(docs)
            print(f'Total users in Firebase now: {firebase_user_count}')
            print(f'Total users in SQLite: {len(db_users)}')
            
            if firebase_user_count == len(db_users):
                print(f'✅ All users are now synced! 🎉')
            else:
                print(f'⚠️  Mismatch: Firebase ({firebase_user_count}) vs SQLite ({len(db_users)})')
        else:
            print('\n❌ Sync cancelled.')
