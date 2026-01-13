"""Kiểm tra users trong Firestore"""
from app import create_app
from app.utils.firebase_client import get_db

app = create_app()

with app.app_context():
    fs_db = get_db()
    
    if fs_db is None:
        print('❌ Firestore client is None!')
    else:
        print('📋 USERS IN FIRESTORE COLLECTION:')
        print('='*60)
        
        users_ref = fs_db.collection('users')
        docs = users_ref.stream()
        
        count = 0
        for doc in docs:
            count += 1
            data = doc.to_dict()
            print(f'\n{count}. User ID: {doc.id}')
            print(f'   Username: {data.get("username")}')
            print(f'   Email: {data.get("email")}')
            print(f'   Full Name: {data.get("full_name")}')
            print(f'   Role: {data.get("role")}')
            print(f'   Created: {data.get("created_at")}')
            print(f'   Synced from: {data.get("synced_from", "N/A")}')
        
        print(f'\n{"="*60}')
        print(f'Total users in Firestore: {count}')
