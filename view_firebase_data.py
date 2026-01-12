"""View Firebase collections data"""
from app import create_app
from app.utils.firebase_client import get_db as get_firestore
import json

app = create_app()

with app.app_context():
    fs = get_firestore()
    
    if not fs:
        print("❌ Firebase not connected")
        exit(1)
    
    print("=" * 80)
    print("FIREBASE COLLECTIONS DATA")
    print("=" * 80)
    
    collection_name = input("\nEnter collection name (vehicles/trips/bookings/users/payments): ").strip()
    
    if not collection_name:
        collection_name = 'vehicles'
    
    print(f"\n📁 Collection: {collection_name}")
    print("=" * 80)
    
    try:
        collection = fs.collection(collection_name)
        docs = list(collection.stream())
        
        print(f"\nTotal documents: {len(docs)}")
        
        if len(docs) == 0:
            print("⚠️  Collection is empty")
        else:
            limit = int(input(f"\nHow many documents to display? (max {len(docs)}): ").strip() or "5")
            
            for i, doc in enumerate(docs[:limit]):
                print(f"\n{'─' * 80}")
                print(f"Document {i+1}: {doc.id}")
                print('─' * 80)
                
                data = doc.to_dict()
                
                # Pretty print
                for key, value in data.items():
                    if isinstance(value, dict):
                        print(f"  {key}:")
                        for k, v in value.items():
                            print(f"    {k}: {v}")
                    else:
                        print(f"  {key}: {value}")
            
            if len(docs) > limit:
                print(f"\n... and {len(docs) - limit} more documents")
        
        # Collection stats
        print(f"\n{'=' * 80}")
        print("COLLECTION STATISTICS")
        print('=' * 80)
        
        if collection_name == 'vehicles':
            # Vehicle status breakdown
            statuses = {}
            for doc in docs:
                data = doc.to_dict()
                status = data.get('status', 'unknown')
                statuses[status] = statuses.get(status, 0) + 1
            
            print("\nVehicle Status:")
            for status, count in statuses.items():
                print(f"  {status}: {count}")
        
        elif collection_name == 'trips':
            # Trip status breakdown
            statuses = {}
            for doc in docs:
                data = doc.to_dict()
                status = data.get('status', 'unknown')
                statuses[status] = statuses.get(status, 0) + 1
            
            print("\nTrip Status:")
            for status, count in statuses.items():
                print(f"  {status}: {count}")
        
        elif collection_name == 'users':
            # User roles
            roles = {}
            for doc in docs:
                data = doc.to_dict()
                role = data.get('role', 'unknown')
                roles[role] = roles.get(role, 0) + 1
            
            print("\nUser Roles:")
            for role, count in roles.items():
                print(f"  {role}: {count}")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print(f"Available collections: vehicles, trips, bookings, users, payments")
