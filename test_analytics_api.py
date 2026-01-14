"""
Test Route Analytics API directly
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app
from app.models import db, User
import json

def test_analytics_api():
    app = create_app('development')
    
    with app.app_context():
        # Get admin user
        admin_user = User.query.filter_by(role='admin').first()
        
        if not admin_user:
            print("❌ No admin user found")
            return
        
        print(f"✅ Admin user: {admin_user.username}")
        
        # Import the analytics function
        from app.controllers.admin_controller import get_route_analytics
        
        # Create a test client
        client = app.test_client()
        
        # Login as admin
        with client.session_transaction() as sess:
            sess['_user_id'] = str(admin_user.id)
        
        # Test the API
        print("\n🧪 Testing API endpoint: /admin/api/route-analytics?days=30")
        
        try:
            # Make the request
            with app.test_request_context('/admin/api/route-analytics?days=30'):
                from flask_login import login_user
                login_user(admin_user)
                
                # Call the function directly
                response = get_route_analytics()
                
                if isinstance(response, tuple):
                    data, status_code = response
                    print(f"\n❌ Error {status_code}: {data}")
                else:
                    print(f"\n✅ Success!")
                    data = response.get_json()
                    print(f"\nStats: {json.dumps(data.get('stats', {}), indent=2)}")
                    
        except Exception as e:
            print(f"\n❌ Exception: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    test_analytics_api()
