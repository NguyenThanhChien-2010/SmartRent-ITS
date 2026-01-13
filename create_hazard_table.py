"""
Migration script to create hazard_zones table
Run this after adding HazardZone model to create the database table
"""
from app import create_app
from app.models import db, HazardZone
from datetime import datetime

def create_hazard_zones_table():
    """Create hazard_zones table in database"""
    app = create_app()
    
    with app.app_context():
        # Create all tables (including hazard_zones)
        db.create_all()
        
        print("✅ Database tables created successfully!")
        print("📊 HazardZone table is ready to use.")
        
        # Verify table exists
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()
        
        if 'hazard_zones' in tables:
            print("✅ Verified: 'hazard_zones' table exists")
            
            # Get column info
            columns = inspector.get_columns('hazard_zones')
            print(f"\n📋 Table structure ({len(columns)} columns):")
            for col in columns:
                print(f"   - {col['name']}: {col['type']}")
        else:
            print("❌ Warning: 'hazard_zones' table not found")

if __name__ == '__main__':
    print("🚀 Creating HazardZone database table...")
    print("=" * 50)
    create_hazard_zones_table()
    print("=" * 50)
    print("✅ Migration completed!")
