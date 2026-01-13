"""
Simple test script to verify hazard zone creation
Run this with Flask app context
"""
from app import create_app
from app.models import db, HazardZone, User
from app.utils.hazard_checker import calculate_polygon_bounds, get_severity_color
from datetime import datetime

def test_create_zone():
    """Test creating a hazard zone programmatically"""
    app = create_app()
    
    with app.app_context():
        # Get admin user
        admin = User.query.filter_by(role='admin').first()
        if not admin:
            print("❌ No admin user found!")
            return
        
        print(f"✅ Admin user: {admin.username}")
        
        # Test data
        test_polygon = [
            [10.7800, 106.7000],
            [10.7800, 106.7020],
            [10.7780, 106.7020],
            [10.7780, 106.7000]
        ]
        
        # Calculate bounds
        polygon = [(p[0], p[1]) for p in test_polygon]
        bounds = calculate_polygon_bounds(polygon)
        color = get_severity_color('high')
        
        # Create zone
        zone_code = f"HZ{datetime.now().strftime('%Y%m%d%H%M%S')}"
        test_zone = HazardZone(
            zone_code=zone_code,
            zone_name="Test Zone from Script",
            hazard_type="construction",
            severity="high",
            description="Testing zone creation",
            warning_message="This is a test warning",
            polygon_coordinates=test_polygon,
            min_latitude=bounds['min_latitude'],
            max_latitude=bounds['max_latitude'],
            min_longitude=bounds['min_longitude'],
            max_longitude=bounds['max_longitude'],
            color=color,
            is_active=True,
            created_by=admin.id
        )
        
        try:
            db.session.add(test_zone)
            db.session.commit()
            
            print(f"\n✅ Successfully created test zone:")
            print(f"   Code: {test_zone.zone_code}")
            print(f"   Name: {test_zone.zone_name}")
            print(f"   Type: {test_zone.hazard_type}")
            print(f"   Severity: {test_zone.severity}")
            print(f"   Color: {test_zone.color}")
            print(f"   Bounds: {bounds}")
            
            # Verify
            all_zones = HazardZone.query.all()
            print(f"\n📊 Total zones in database: {len(all_zones)}")
            
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Error creating zone: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    print("🧪 Testing Hazard Zone Creation...")
    print("=" * 60)
    success = test_create_zone()
    print("=" * 60)
    if success:
        print("✅ Test PASSED")
    else:
        print("❌ Test FAILED")
