"""
Migration script to create route_history table for Analytics Dashboard
Safe to run - only creates table if not exists
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app
from app.models import db, RouteHistory

def create_route_history_table():
    """Create route_history table for tracking planned routes"""
    app = create_app('development')
    
    with app.app_context():
        # Create table if not exists
        db.create_all()
        print("✅ route_history table created successfully!")
        
        # Verify table exists
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        if 'route_history' in inspector.get_table_names():
            print("✅ Verified: route_history table exists in database")
            
            # Show column info
            columns = inspector.get_columns('route_history')
            print(f"\n📊 Table has {len(columns)} columns:")
            for col in columns:
                print(f"   - {col['name']}: {col['type']}")
        else:
            print("❌ Error: route_history table not found")

if __name__ == '__main__':
    create_route_history_table()
