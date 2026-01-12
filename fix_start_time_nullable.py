"""Fix start_time to be nullable"""
import sqlite3

# Connect to database
conn = sqlite3.connect('instance/smartrent.db')
cursor = conn.cursor()

try:
    # SQLite doesn't support ALTER COLUMN directly
    # We need to recreate the table
    
    # 1. Create new table with correct schema
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trips_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trip_code VARCHAR(50) UNIQUE NOT NULL,
            user_id INTEGER NOT NULL,
            vehicle_id INTEGER NOT NULL,
            booking_id INTEGER,
            start_latitude FLOAT,
            start_longitude FLOAT,
            start_address VARCHAR(255),
            end_latitude FLOAT,
            end_longitude FLOAT,
            end_address VARCHAR(255),
            start_time DATETIME,
            end_time DATETIME,
            duration_minutes FLOAT,
            distance_km FLOAT,
            route_json TEXT,
            total_cost FLOAT,
            rating INTEGER,
            feedback TEXT,
            status VARCHAR(20) DEFAULT 'pending',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (vehicle_id) REFERENCES vehicles(id),
            FOREIGN KEY (booking_id) REFERENCES bookings(id)
        )
    ''')
    
    # 2. Copy data from old table to new table
    cursor.execute('''
        INSERT INTO trips_new 
        SELECT * FROM trips
    ''')
    
    # 3. Drop old table
    cursor.execute('DROP TABLE trips')
    
    # 4. Rename new table to trips
    cursor.execute('ALTER TABLE trips_new RENAME TO trips')
    
    # 5. Recreate indexes
    cursor.execute('CREATE INDEX IF NOT EXISTS ix_trips_trip_code ON trips(trip_code)')
    
    conn.commit()
    print("✅ Successfully updated trips table - start_time is now nullable")
    
except Exception as e:
    conn.rollback()
    print(f"❌ Error: {e}")
finally:
    conn.close()
