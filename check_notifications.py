"""Check notification system"""
from app import create_app
from app.models import Notification, Trip, User
from datetime import datetime

app = create_app()

with app.app_context():
    print("=" * 60)
    print("NOTIFICATION SYSTEM CHECK")
    print("=" * 60)
    
    # Check if notifications table exists
    try:
        notifs = Notification.query.all()
        print(f"\n✅ Notifications table exists")
        print(f"Total notifications: {len(notifs)}")
    except Exception as e:
        print(f"\n❌ Error accessing notifications table: {e}")
        print("\nRun: python create_notifications_table.py")
        exit(1)
    
    # Show recent notifications
    if notifs:
        print("\n" + "-" * 60)
        print("Recent Notifications (last 10):")
        print("-" * 60)
        
        for n in notifs[:10]:
            read_status = "✓" if n.is_read else "✗"
            print(f"\n{n.id}. [{read_status}] {n.title}")
            print(f"   Type: {n.type} | Color: {n.color} | Icon: {n.icon}")
            print(f"   Message: {n.message[:60]}...")
            print(f"   User: {n.user_id} | Created: {n.created_at}")
            if n.related_type:
                print(f"   Related: {n.related_type} #{n.related_id}")
    else:
        print("\n⚠️  No notifications found")
    
    # Check unread count per user
    print("\n" + "-" * 60)
    print("Unread Notifications by User:")
    print("-" * 60)
    
    users = User.query.filter_by(role='customer').all()
    for user in users:
        unread = Notification.query.filter_by(
            user_id=user.id,
            is_read=False,
            is_deleted=False
        ).count()
        
        if unread > 0:
            print(f"  {user.full_name} ({user.email}): {unread} unread")
    
    # Check completed trips without notifications
    print("\n" + "-" * 60)
    print("Completed Trips (Today):")
    print("-" * 60)
    
    today = datetime.now().date()
    today_start = datetime.combine(today, datetime.min.time())
    
    completed_trips = Trip.query.filter(
        Trip.status == 'completed',
        Trip.created_at >= today_start
    ).all()
    
    print(f"\nTotal completed trips today: {len(completed_trips)}")
    
    for trip in completed_trips:
        # Check if notification exists
        trip_notif = Notification.query.filter_by(
            user_id=trip.user_id,
            related_type='trip',
            related_id=trip.id,
            type='trip'
        ).first()
        
        status = "✅ Has notification" if trip_notif else "❌ Missing notification"
        print(f"  Trip {trip.trip_code}: {status}")
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total notifications: {len(notifs)}")
    print(f"Completed trips today: {len(completed_trips)}")
    print(f"Trips with notifications: {sum(1 for t in completed_trips if Notification.query.filter_by(user_id=t.user_id, related_type='trip', related_id=t.id).first())}")
