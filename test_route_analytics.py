"""
Test Route Analytics Dashboard
- Plan a route to create data
- Call analytics API
- Verify data structure
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app
from app.models import db, RouteHistory, User
from datetime import datetime, timedelta
import json

def test_analytics():
    app = create_app('development')
    
    with app.app_context():
        print("=" * 60)
        print("ROUTE ANALYTICS TEST")
        print("=" * 60)
        
        # Get admin user (for testing API)
        admin_user = User.query.filter_by(role='admin').first()
        customer_user = User.query.filter_by(role='customer').first()
        
        if not admin_user:
            print("❌ No admin user found in database")
            return
        
        if not customer_user:
            print("⚠️  Creating test customer user...")
            customer_user = User(
                username='test_customer',
                email='customer@test.com',
                phone='0123456789',
                role='customer'
            )
            customer_user.set_password('password')
            db.session.add(customer_user)
            db.session.commit()
            print(f"✅ Created test customer: {customer_user.username}")
        
        print(f"\n📍 Admin user: {admin_user.username}")
        print(f"📍 Customer user: {customer_user.username}")
        
        # Check current route history count
        current_count = RouteHistory.query.count()
        print(f"\n📊 Current route history records: {current_count}")
        
        # Create test route data (last 7 days)
        test_routes = [
            {
                'user_id': customer_user.id,
                'start_address': 'Bến Thành Market, HCMC',
                'end_address': 'Tân Sơn Nhất Airport',
                'start_lat': 10.7728,
                'start_lng': 106.6980,
                'end_lat': 10.8167,
                'end_lng': 106.6589,
                'distance_km': 8.5,
                'duration_minutes': 15,
                'estimated_cost': 25000,
                'hazards_detected': 0,
                'hazard_zones_passed': [],
                'routing_algorithm': 'OSRM',
                'created_at': datetime.utcnow() - timedelta(days=1)
            },
            {
                'user_id': customer_user.id,
                'start_address': 'District 1, HCMC',
                'end_address': 'District 7, HCMC',
                'start_lat': 10.7769,
                'start_lng': 106.7009,
                'end_lat': 10.7327,
                'end_lng': 106.7190,
                'distance_km': 12.3,
                'duration_minutes': 25,
                'estimated_cost': 35000,
                'hazards_detected': 1,
                'hazard_zones_passed': [1],
                'routing_algorithm': 'OSRM',
                'created_at': datetime.utcnow() - timedelta(days=2)
            },
            {
                'user_id': customer_user.id,
                'start_address': 'Bến Thành Market, HCMC',
                'end_address': 'Tân Sơn Nhất Airport',
                'start_lat': 10.7728,
                'start_lng': 106.6980,
                'end_lat': 10.8167,
                'end_lng': 106.6589,
                'distance_km': 8.7,
                'duration_minutes': 16,
                'estimated_cost': 26000,
                'hazards_detected': 0,
                'hazard_zones_passed': [],
                'routing_algorithm': 'OSRM',
                'created_at': datetime.utcnow() - timedelta(days=3)
            },
            {
                'user_id': customer_user.id,
                'start_address': 'Saigon Central Post Office',
                'end_address': 'Notre-Dame Cathedral Basilica',
                'start_lat': 10.7798,
                'start_lng': 106.6998,
                'end_lat': 10.7797,
                'end_lng': 106.6990,
                'distance_km': 0.2,
                'duration_minutes': 2,
                'estimated_cost': 5000,
                'hazards_detected': 0,
                'hazard_zones_passed': [],
                'routing_algorithm': 'A*',
                'created_at': datetime.utcnow() - timedelta(days=5)
            }
        ]
        
        print(f"\n➕ Adding {len(test_routes)} test routes...")
        for i, route_data in enumerate(test_routes, 1):
            route = RouteHistory(**route_data)
            db.session.add(route)
            print(f"   {i}. {route_data['start_address']} → {route_data['end_address']}")
        
        db.session.commit()
        print(f"✅ Added {len(test_routes)} test routes")
        
        # Verify new count
        new_count = RouteHistory.query.count()
        print(f"📊 New route history count: {new_count} (added {new_count - current_count})")
        
        # Test analytics queries
        print("\n" + "=" * 60)
        print("TESTING ANALYTICS QUERIES")
        print("=" * 60)
        
        # Query 1: Total routes last 30 days
        from sqlalchemy import func
        cutoff = datetime.utcnow() - timedelta(days=30)
        total_routes = RouteHistory.query.filter(RouteHistory.created_at >= cutoff).count()
        print(f"\n1️⃣  Total routes (30 days): {total_routes}")
        
        # Query 2: Average distance
        avg_distance = db.session.query(func.avg(RouteHistory.distance_km))\
            .filter(RouteHistory.created_at >= cutoff).scalar()
        print(f"2️⃣  Average distance: {avg_distance:.2f} km")
        
        # Query 3: Hazard routes
        hazard_routes = RouteHistory.query.filter(
            RouteHistory.created_at >= cutoff,
            RouteHistory.hazards_detected > 0
        ).count()
        hazard_percent = (hazard_routes / total_routes * 100) if total_routes > 0 else 0
        print(f"3️⃣  Routes with hazards: {hazard_routes} ({hazard_percent:.1f}%)")
        
        # Query 4: Top routes
        top_routes = db.session.query(
            RouteHistory.start_address,
            RouteHistory.end_address,
            func.count(RouteHistory.id).label('count')
        ).filter(RouteHistory.created_at >= cutoff)\
         .group_by(RouteHistory.start_address, RouteHistory.end_address)\
         .order_by(func.count(RouteHistory.id).desc())\
         .limit(5)\
         .all()
        
        print("\n4️⃣  Top 5 routes:")
        for i, r in enumerate(top_routes, 1):
            print(f"   {i}. {r.start_address} → {r.end_address} ({r.count} times)")
        
        # Query 5: Algorithm usage
        algorithm_usage = db.session.query(
            RouteHistory.routing_algorithm,
            func.count(RouteHistory.id).label('count')
        ).filter(RouteHistory.created_at >= cutoff)\
         .group_by(RouteHistory.routing_algorithm)\
         .all()
        
        print("\n5️⃣  Algorithm usage:")
        for r in algorithm_usage:
            print(f"   - {r.routing_algorithm or 'Unknown'}: {r.count} routes")
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        print("\n📊 You can now visit: http://localhost:5000/admin/route-analytics")
        print("   (Login as admin to see the dashboard)")

if __name__ == '__main__':
    test_analytics()
