"""Fix user data conflicts between SQLite and Firebase"""
from app import create_app
from app.models import db, User
from app.utils.firebase_client import get_db
from datetime import datetime

app = create_app()

with app.app_context():
    print('\n' + '='*70)
    print('FIXING USER SYNC CONFLICTS')
    print('='*70)
    
    # Get all users from both sources
    db_users = {u.id: u for u in User.query.all()}
    
    fs_db = get_db()
    if not fs_db:
        print('❌ Firebase not initialized!')
        exit(1)
    
    firebase_users = {}
    for doc in list(fs_db.collection('users').stream()):
        firebase_users[int(doc.id)] = doc.to_dict()
    
    print(f'\nSQLite users: {len(db_users)}')
    print(f'Firebase users: {len(firebase_users)}')
    
    # Find mismatches
    print(f'\n🔍 CHECKING FOR MISMATCHES...\n')
    
    mismatches = []
    for user_id, db_user in db_users.items():
        if user_id in firebase_users:
            fb_user = firebase_users[user_id]
            if fb_user.get('email') != db_user.email:
                mismatches.append({
                    'id': user_id,
                    'db_user': db_user,
                    'fb_email': fb_user.get('email'),
                    'db_email': db_user.email
                })
                print(f'❌ Mismatch at ID {user_id}:')
                print(f'   SQLite: {db_user.username} ({db_user.email})')
                print(f'   Firebase: {fb_user.get("username")} ({fb_user.get("email")})')
                print()
    
    if mismatches:
        print(f'⚠️  Found {len(mismatches)} mismatch(es)!')
        print(f'\n💡 Will overwrite Firebase data with SQLite data (source of truth)')
        print(f'\n🔄 Do you want to fix these mismatches? (y/n): ', end='')
        response = input().strip().lower()
        
        if response == 'y':
            print(f'\n🔄 FIXING MISMATCHES...\n')
            
            for mismatch in mismatches:
                user = mismatch['db_user']
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
                        'synced_from': 'conflict_fix',
                        'synced_at': datetime.utcnow().isoformat()
                    }
                    
                    fs_db.collection('users').document(str(user.id)).set(user_data)
                    print(f'✅ Fixed ID {user.id}: {user.email}')
                    
                except Exception as e:
                    print(f'❌ Failed to fix ID {user.id}: {e}')
            
            print(f'\n✅ Mismatches fixed!')
            
            # Now check if there are Firebase users with wrong IDs that need to be re-added
            print(f'\n🔍 Checking for displaced Firebase users...')
            
            # Find emails in Firebase that don't match their ID in SQLite
            displaced = []
            for fb_id, fb_data in firebase_users.items():
                fb_email = fb_data.get('email')
                # Find this email in SQLite
                db_user = User.query.filter_by(email=fb_email).first()
                if db_user and db_user.id != fb_id:
                    displaced.append({
                        'wrong_id': fb_id,
                        'correct_id': db_user.id,
                        'email': fb_email,
                        'db_user': db_user
                    })
            
            if displaced:
                print(f'\n⚠️  Found {len(displaced)} displaced user(s) in Firebase:')
                for d in displaced:
                    print(f'   - {d["email"]} stored at ID {d["wrong_id"]}, should be at ID {d["correct_id"]}')
                
                print(f'\n🔄 Re-syncing displaced users to correct IDs...\n')
                for d in displaced:
                    user = d['db_user']
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
                            'synced_from': 'displaced_fix',
                            'synced_at': datetime.utcnow().isoformat()
                        }
                        
                        # Delete from wrong location
                        fs_db.collection('users').document(str(d['wrong_id'])).delete()
                        print(f'🗑️  Deleted {user.email} from wrong ID {d["wrong_id"]}')
                        
                        # Add to correct location
                        fs_db.collection('users').document(str(user.id)).set(user_data)
                        print(f'✅ Added {user.email} to correct ID {user.id}')
                        
                    except Exception as e:
                        print(f'❌ Failed to fix {user.email}: {e}')
                        
            print(f'\n{'='*70}')
            print('✅ ALL FIXES COMPLETED!')
            print('='*70)
        else:
            print('\n❌ Fix cancelled.')
    else:
        print('✅ No mismatches found! All data is consistent.')
