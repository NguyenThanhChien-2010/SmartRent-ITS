"""Test notification creation manually"""
from app import create_app
from app.utils.notification_helper import notify_trip_completed
from app.models import Trip

app = create_app()

with app.app_context():
    print("Testing notification creation...")
    
    # Get a recent completed trip
    trip = Trip.query.filter_by(status='completed').order_by(Trip.created_at.desc()).first()
    
    if not trip:
        print("❌ No completed trips found")
        exit(1)
    
    print(f"\nTrip: {trip.trip_code}")
    print(f"User: {trip.user_id}")
    print(f"Duration: {trip.duration_minutes} minutes")
    print(f"Cost: {trip.total_cost} VND")
    
    # Create notification
    try:
        from app.models import Vehicle
        vehicle = Vehicle.query.get(trip.vehicle_id)
        
        notif = notify_trip_completed(
            user_id=trip.user_id,
            vehicle_code=vehicle.vehicle_code,
            duration=int(trip.duration_minutes),
            amount=trip.total_cost,
            trip_id=trip.id
        )
        
        if notif:
            print(f"\n✅ Notification created successfully!")
            print(f"   ID: {notif.id}")
            print(f"   Title: {notif.title}")
            print(f"   Message: {notif.message}")
        else:
            print("\n❌ Notification creation failed")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
