"""
Script để tạo bảng notifications trong database
Chạy: python create_notifications_table.py
"""

from app import create_app
from app.models import db
from sqlalchemy import text

app = create_app()

with app.app_context():
    # Tạo bảng notifications
    with db.engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                type VARCHAR(50) NOT NULL,
                title VARCHAR(200) NOT NULL,
                message TEXT NOT NULL,
                icon VARCHAR(50),
                color VARCHAR(20),
                related_id INTEGER,
                related_type VARCHAR(50),
                action_url VARCHAR(255),
                is_read BOOLEAN DEFAULT 0,
                is_deleted BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                read_at DATETIME,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """))
        conn.commit()
    
    print("✅ Đã tạo bảng notifications thành công!")
    print("Bạn có thể thử nạp tiền để xem thông báo hoạt động!")
