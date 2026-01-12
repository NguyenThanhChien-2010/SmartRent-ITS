"""Fix orphaned vehicles and list Firebase collections"""
from app import create_app
from app.models import db, Vehicle, Trip
from app.utils.firebase_client import get_db as get_firestore
from app.utils.repositories import VehicleRepository, TripRepository

app = create_app()

with app.app_context():
    print("=" * 60)
    print("FIXING ORPHANED VEHICLES")
    print("=" * 60)
    
    # Find orphaned vehicles
    orphaned = []
    in_use_vehicles = Vehicle.query.filter_by(status='in_use').all()
    
    for v in in_use_vehicles:
        active_trip = Trip.query.filter_by(
            vehicle_id=v.id,
            status='in_progress'
        ).first()
        
        if not active_trip:
            orphaned.append(v)
    
    if not orphaned:
        print("\n✅ No orphaned vehicles found!")
    else:
        print(f"\n⚠️  Found {len(orphaned)} orphaned vehicles")
        print("\nFixing...")
        
        for v in orphaned:
            print(f"\n  Vehicle: {v.vehicle_code} (ID: {v.id})")
            
            # Check last trip
            last_trip = Trip.query.filter_by(vehicle_id=v.id)\
                .order_by(Trip.created_at.desc()).first()
            
            if last_trip:
                print(f"    Last trip: {last_trip.trip_code} - {last_trip.status}")
            
            # Fix: Set back to available
            v.status = 'available'
            v.lock_status = 'locked'
            v.is_locked = True
            
            print(f"    ✓ Updated to: available")
        
        # Commit changes
        db.session.commit()
        print(f"\n✅ Fixed {len(orphaned)} vehicles in SQL database")
        
        # Sync to Firebase
        if app.config.get('FIREBASE_ENABLED', False):
            print("\n🔄 Syncing to Firebase...")
            for v in orphaned:
                success = VehicleRepository.update_fields(v.id, {
                    'status': 'available',
                    'lock_status': 'locked',
                    'is_locked': True
                })
                if success:
                    print(f"  ✓ {v.vehicle_code} synced to Firebase")
                else:
                    print(f"  ✗ {v.vehicle_code} failed to sync")
    
    print("\n" + "=" * 60)
    print("FIREBASE COLLECTIONS")
    print("=" * 60)
    
    fs = get_firestore()
    if fs:
        print("\nListing all collections:")
        collections = fs.collections()
        
        for collection in collections:
            print(f"\n📁 Collection: {collection.id}")
            
            # Count documents
            docs = list(collection.stream())
            print(f"   Documents: {len(docs)}")
            
            if len(docs) > 0 and len(docs) <= 5:
                print(f"   Sample doc IDs:")
                for doc in docs[:5]:
                    print(f"     - {doc.id}")
    else:
        print("\n❌ Firebase not connected")
    
    print("\n" + "=" * 60)
    print("VERIFICATION")
    print("=" * 60)
    
    # Re-check
    remaining = Vehicle.query.filter_by(status='in_use').count()
    active_trips = Trip.query.filter_by(status='in_progress').count()
    available = Vehicle.query.filter_by(status='available').count()
    
    print(f"\nSQL Database:")
    print(f"  Available vehicles: {available}")
    print(f"  In-use vehicles: {remaining}")
    print(f"  Active trips: {active_trips}")
    
    if remaining == active_trips:
        print("\n✅ Consistency restored!")
    else:
        print(f"\n⚠️  Still inconsistent: {remaining} in-use vehicles but {active_trips} active trips")
