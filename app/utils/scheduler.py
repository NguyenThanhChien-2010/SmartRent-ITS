"""Background scheduler for auto-release vehicles and cleanup tasks"""
from datetime import datetime, timedelta
from app.models import db, Trip, Vehicle
from app.utils.repositories import VehicleRepository
from flask import current_app
import threading
import time


def auto_release_expired_bookings():
    """Release vehicles that are pending for more than configured timeout (default 5 minutes)"""
    try:
        # Get timeout from config (default 5 minutes)
        timeout_minutes = current_app.config.get('AUTO_RELEASE_TIMEOUT_MINUTES', 5)
        expiry_time = datetime.now() - timedelta(minutes=timeout_minutes)
        
        # Find trips that are pending for > timeout minutes
        expired_trips = Trip.query.filter(
            Trip.status == 'pending',
            Trip.created_at < expiry_time
        ).all()
        
        released_count = 0
        for trip in expired_trips:
            vehicle = Vehicle.query.get(trip.vehicle_id)
            if vehicle and vehicle.status == 'reserved':
                # Release vehicle back to available
                vehicle.status = 'available'
                trip.status = 'cancelled'
                trip.updated_at = datetime.now()
                
                db.session.commit()
                
                # Sync to Firebase
                if current_app.config.get('FIREBASE_ENABLED', False):
                    try:
                        success = VehicleRepository.update_fields(vehicle.id, {'status': 'available'})
                        if success:
                            print(f'[Scheduler] ✓ Firebase synced: vehicle {vehicle.vehicle_code} → available')
                        else:
                            print(f'[Scheduler] ⚠ Firebase sync returned False for vehicle {vehicle.vehicle_code}')
                    except Exception as e:
                        print(f'[Scheduler] ❌ Firebase sync failed: {e}')
                
                released_count += 1
                print(f'[Scheduler] Auto-released vehicle {vehicle.vehicle_code} from trip {trip.trip_code}')
        
        if released_count > 0:
            print(f'[Scheduler] Released {released_count} expired bookings')
            
    except Exception as e:
        print(f'[Scheduler] Error in auto_release_expired_bookings: {e}')
        db.session.rollback()


def run_scheduler():
    """Run background scheduler every 60 seconds"""
    while True:
        try:
            with current_app.app_context():
                auto_release_expired_bookings()
        except Exception as e:
            print(f'[Scheduler] Error: {e}')
        
        # Run every 60 seconds
        time.sleep(60)


def start_scheduler(app):
    """Start the background scheduler thread"""
    if not app.config.get('ENABLE_AUTO_RELEASE', True):
        print('[Scheduler] Auto-release disabled in config')
        return
    
    def run_with_context():
        with app.app_context():
            run_scheduler()
    
    thread = threading.Thread(target=run_with_context, daemon=True)
    thread.start()
    print('[Scheduler] Background auto-release scheduler started (checking every 60s)')
