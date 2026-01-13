"""
Create demo hazard zones for SmartRent ITS
3 hazard zones in Ho Chi Minh City for testing
"""
from app import create_app
from app.models import db, HazardZone, User
from datetime import datetime, timedelta
from app.utils.hazard_checker import calculate_polygon_bounds, get_severity_color

def create_demo_hazards():
    """Create 3 demo hazard zones in Ho Chi Minh City"""
    app = create_app()
    
    with app.app_context():
        # Get admin user (or create if not exists)
        admin = User.query.filter_by(role='admin').first()
        if not admin:
            print("⚠️  No admin user found. Creating demo admin...")
            admin = User(
                username='admin',
                email='admin@smartrent.com',
                full_name='System Admin',
                role='admin'
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
        
        print(f"✅ Using admin: {admin.username} (ID: {admin.id})")
        
        # Demo Hazard Zones for Ho Chi Minh City
        demo_zones = [
            {
                'zone_name': 'Ngập lụt Đường Nguyễn Huệ',
                'hazard_type': 'flood',
                'severity': 'high',
                'description': 'Khu vực thường xuyên ngập nước vào mùa mưa, độ sâu có thể lên đến 30cm',
                'warning_message': '⚠️ Cảnh báo ngập lụt! Đường Nguyễn Huệ đang có nước sâu 20-30cm',
                'polygon_coordinates': [
                    [10.7746, 106.7016],  # Điểm 1
                    [10.7746, 106.7026],  # Điểm 2
                    [10.7736, 106.7026],  # Điểm 3
                    [10.7736, 106.7016],  # Điểm 4
                ]
            },
            {
                'zone_name': 'Thi công Metro Bến Thành',
                'hazard_type': 'construction',
                'severity': 'medium',
                'description': 'Đang thi công ga metro Bến Thành, giao thông khó khăn, có thể tắc đường',
                'warning_message': '🚧 Cảnh báo thi công! Khu vực Bến Thành đang thi công metro, tránh khu vực này',
                'polygon_coordinates': [
                    [10.7720, 106.6980],
                    [10.7720, 106.6995],
                    [10.7705, 106.6995],
                    [10.7705, 106.6980],
                ]
            },
            {
                'zone_name': 'Tai nạn Ngã tư Hàng Xanh',
                'hazard_type': 'accident',
                'severity': 'critical',
                'description': 'Tai nạn giao thông nghiêm trọng, đường bị phong tỏa tạm thời',
                'warning_message': '🚨 NGUY HIỂM! Tai nạn nghiêm trọng tại Ngã tư Hàng Xanh, vui lòng tránh khu vực',
                'polygon_coordinates': [
                    [10.8015, 106.7145],
                    [10.8015, 106.7165],
                    [10.7995, 106.7165],
                    [10.7995, 106.7145],
                ]
            }
        ]
        
        created_count = 0
        
        for i, zone_data in enumerate(demo_zones, 1):
            # Check if zone already exists
            existing = HazardZone.query.filter_by(zone_name=zone_data['zone_name']).first()
            if existing:
                print(f"⚠️  Zone '{zone_data['zone_name']}' already exists, skipping...")
                continue
            
            # Generate zone code
            zone_code = f"HZ{datetime.now().strftime('%Y%m%d')}{i:03d}"
            
            # Calculate bounding box
            polygon = [(p[0], p[1]) for p in zone_data['polygon_coordinates']]
            bounds = calculate_polygon_bounds(polygon)
            
            # Get color based on severity
            color = get_severity_color(zone_data['severity'])
            
            # Create hazard zone
            zone = HazardZone(
                zone_code=zone_code,
                zone_name=zone_data['zone_name'],
                hazard_type=zone_data['hazard_type'],
                severity=zone_data['severity'],
                description=zone_data['description'],
                warning_message=zone_data['warning_message'],
                polygon_coordinates=zone_data['polygon_coordinates'],
                min_latitude=bounds['min_latitude'],
                max_latitude=bounds['max_latitude'],
                min_longitude=bounds['min_longitude'],
                max_longitude=bounds['max_longitude'],
                color=color,
                is_active=True,
                start_time=datetime.now(),
                end_time=datetime.now() + timedelta(days=30),
                created_by=admin.id
            )
            
            db.session.add(zone)
            created_count += 1
            
            print(f"✅ Created: {zone.zone_name} ({zone.severity.upper()}) - {zone.hazard_type}")
        
        # Commit all changes
        db.session.commit()
        
        print("\n" + "=" * 60)
        print(f"✅ Demo hazard zones created: {created_count}")
        print("=" * 60)
        
        # Display all zones
        all_zones = HazardZone.query.all()
        print(f"\n📊 Total hazard zones in database: {len(all_zones)}")
        
        for zone in all_zones:
            status = "🟢 ACTIVE" if zone.is_active else "🔴 INACTIVE"
            print(f"  • [{zone.zone_code}] {zone.zone_name} - {zone.severity.upper()} - {status}")
        
        print("\n💡 Tip: Visit /admin/hazard-zones to manage these zones!")

if __name__ == '__main__':
    print("🚀 Creating demo hazard zones for TP.HCM...")
    print("=" * 60)
    create_demo_hazards()
    print("=" * 60)
    print("✅ Demo data creation completed!")
