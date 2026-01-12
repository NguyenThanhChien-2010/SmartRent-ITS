"""Check data consistency between vehicles and trips"""
from app import create_app
from app.models import Vehicle, Trip
from datetime import datetime

app = create_app()

with app.app_context():
    print("=" * 60)
    print("VEHICLE STATUS CHECK")
    print("=" * 60)
    
    vehicles = Vehicle.query.all()
    status_count = {}
    for v in vehicles:
        status_count[v.status] = status_count.get(v.status, 0) + 1
    
    print("\nVehicle Status Summary:")
    for status, count in status_count.items():
        print(f"  {status}: {count}")
    
    print("\n" + "=" * 60)
    print("TRIPS TODAY")
    print("=" * 60)
    
    today = datetime.now().date()
    today_start = datetime.combine(today, datetime.min.time())
    trips = Trip.query.filter(Trip.created_at >= today_start).all()
    
    print(f"\nTotal trips today: {len(trips)}")
    
    trip_status = {}
    for t in trips:
        trip_status[t.status] = trip_status.get(t.status, 0) + 1
    
    print("\nTrip Status Summary:")
    for status, count in trip_status.items():
        print(f"  {status}: {count}")
    
    print("\n" + "=" * 60)
    print("INCONSISTENCY CHECK")
    print("=" * 60)
    
    # Find vehicles with status='in_use' but no active trip
    print("\nVehicles 'in_use' but NO active trip:")
    in_use_vehicles = Vehicle.query.filter_by(status='in_use').all()
    
    orphaned = []
    for v in in_use_vehicles:
        active_trip = Trip.query.filter_by(
            vehicle_id=v.id, 
            status='in_progress'
        ).first()
        
        if not active_trip:
            orphaned.append(v)
            print(f"  ❌ {v.vehicle_code} (ID: {v.id}) - Status: {v.status}")
            # Find last trip
            last_trip = Trip.query.filter_by(vehicle_id=v.id)\
                .order_by(Trip.created_at.desc()).first()
            if last_trip:
                print(f"     Last trip: {last_trip.trip_code} - {last_trip.status}")
    
    if not orphaned:
        print("  ✅ All 'in_use' vehicles have active trips")
    
    # Find active trips but vehicle not 'in_use'
    print("\nActive trips but vehicle NOT 'in_use':")
    active_trips = Trip.query.filter_by(status='in_progress').all()
    
    for t in active_trips:
        v = Vehicle.query.get(t.vehicle_id)
        if v.status != 'in_use':
            print(f"  ❌ Trip {t.trip_code} - Vehicle {v.vehicle_code}: {v.status}")
    
    if not active_trips or all(Vehicle.query.get(t.vehicle_id).status == 'in_use' for t in active_trips):
        print("  ✅ All active trips have correct vehicle status")
    
    print("\n" + "=" * 60)
    print("FIX RECOMMENDATIONS")
    print("=" * 60)
    
    if orphaned:
        print(f"\n⚠️  Found {len(orphaned)} orphaned vehicles!")
        print("These vehicles are marked 'in_use' but have no active trip.")
        print("\nTo fix, run:")
        print("  python fix_orphaned_vehicles.py")
