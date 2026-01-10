# Hướng dẫn cài đặt - Phiên bản MIỄN PHÍ

Hệ thống SmartRent ITS sử dụng **100% công nghệ và dịch vụ miễn phí**, không cần API key hay tài khoản trả phí!

## 🆓 Các dịch vụ MIỄN PHÍ được sử dụng

### 1. **Bản đồ (Maps) - MIỄN PHÍ**
#### OpenStreetMap + Leaflet.js (Đang dùng - Không cần đăng ký)
- ✅ **100% miễn phí, không giới hạn**
- ✅ Không cần API key
- ✅ Bản đồ toàn cầu
- ✅ Tốc độ tốt

```html
<!-- Đã tích hợp sẵn trong views/vehicles/map.html -->
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
```

#### Mapbox (Tùy chọn)
- ✅ Free tier: 50,000 requests/tháng
- 📝 Cần đăng ký: https://www.mapbox.com/
- Thêm vào `.env`: `MAPBOX_ACCESS_TOKEN=your_token`

### 2. **Thanh toán - MIỄN PHÍ**
#### Ví nội bộ (Đang dùng)
- ✅ Không cần payment gateway
- ✅ Quản lý số dư trong database
- ✅ Phù hợp cho demo/học tập

#### Các tùy chọn nâng cấp (Sandbox miễn phí):
- **MoMo**: Sandbox miễn phí - https://developers.momo.vn/
- **ZaloPay**: Sandbox miễn phí - https://docs.zalopay.vn/
- **VNPay**: Test miễn phí - https://sandbox.vnpayment.vn/

### 3. **Database - MIỄN PHÍ**
#### SQLite (Mặc định cho development)
- ✅ Không cần cài đặt
- ✅ File-based database
- ✅ Đủ cho học tập/demo

#### PostgreSQL (Production)
**Free hosting options:**
- **ElephantSQL**: 20MB free - https://www.elephantsql.com/
- **Supabase**: 500MB free - https://supabase.com/
- **Railway**: $5 credit/tháng - https://railway.app/
- **Render**: PostgreSQL free tier - https://render.com/

### 4. **Hosting - MIỄN PHÍ**
- **PythonAnywhere**: Free tier với Flask - https://www.pythonanywhere.com/
- **Render**: Free tier với auto-deploy - https://render.com/
- **Railway**: $5 credit/tháng - https://railway.app/
- **Heroku Alternatives**: Fly.io, Cyclic

### 5. **IoT/MQTT - MIỄN PHÍ**
#### Mosquitto (Local)
- ✅ MQTT broker miễn phí
- Cài đặt local: https://mosquitto.org/download/

#### Cloud MQTT (Free tier)
- **HiveMQ Cloud**: Free tier - https://www.hivemq.com/mqtt-cloud-broker/
- **CloudMQTT**: Free tier - https://www.cloudmqtt.com/

## 🚀 Cài đặt nhanh

### Bước 1: Clone/Download project
```powershell
cd c:\Users\Lenovo\Downloads\SmartRent-ITS
```

### Bước 2: Tạo môi trường ảo
```powershell
python -m venv venv
.\venv\Scripts\activate
```

### Bước 3: Cài đặt dependencies
```powershell
pip install -r requirements.txt
```

### Bước 4: Tạo file .env (Không cần API keys!)
```powershell
copy .env.example .env
```

Nội dung `.env` tối thiểu:
```env
SECRET_KEY=my-super-secret-key-12345
FLASK_APP=run.py
FLASK_ENV=development
DATABASE_URL=sqlite:///smartrent.db
```

### Bước 5: Chạy ứng dụng
```powershell
python run.py
```

Truy cập: **http://localhost:5000**

## 📱 Tính năng hoạt động MIỄN PHÍ

### ✅ Đã có sẵn (Không cần config)
1. ✅ **Bản đồ xe**: OpenStreetMap + Leaflet
2. ✅ **Tìm xe gần**: Tính khoảng cách GPS
3. ✅ **Đặt xe**: Booking system
4. ✅ **Thanh toán**: Ví nội bộ
5. ✅ **Lịch sử chuyến đi**: Tracking
6. ✅ **Dashboard admin**: Thống kê, biểu đồ
7. ✅ **Quản lý xe**: CRUD operations
8. ✅ **User authentication**: Login/Register

### 🔧 Cần config đơn giản (Optional)
1. **Email notifications**: Gmail SMTP (miễn phí)
   ```env
   MAIL_USERNAME=your_gmail@gmail.com
   MAIL_PASSWORD=your_app_password
   ```

2. **MQTT local**: Mosquitto (miễn phí)
   ```powershell
   # Cài Mosquitto trên Windows
   choco install mosquitto
   ```

## 🎯 Demo nhanh với dữ liệu mẫu

Tạo file `init_data.py`:

```python
from app import create_app
from app.models import db, User, Vehicle
from datetime import datetime

app = create_app()

with app.app_context():
    # Tạo admin
    admin = User(
        username='admin',
        email='admin@smartrent.com',
        full_name='Administrator',
        role='admin',
        wallet_balance=1000000
    )
    admin.set_password('admin123')
    
    # Tạo user demo
    user = User(
        username='demo',
        email='demo@smartrent.com',
        full_name='Demo User',
        role='customer',
        wallet_balance=100000
    )
    user.set_password('demo123')
    
    # Tạo xe mẫu
    vehicles = [
        Vehicle(
            vehicle_code='BIKE001',
            vehicle_type='bike',
            brand='Giant',
            model='Electric 2024',
            latitude=10.8231,
            longitude=106.6297,
            battery_level=85,
            status='available',
            price_per_minute=500,
            qr_code='QRBIKE001'
        ),
        Vehicle(
            vehicle_code='MOTOR001',
            vehicle_type='motorbike',
            brand='Honda',
            model='Vision 2024',
            latitude=10.8241,
            longitude=106.6307,
            battery_level=90,
            fuel_level=80,
            status='available',
            price_per_minute=2000,
            qr_code='QRMOTOR001'
        ),
        Vehicle(
            vehicle_code='CAR001',
            vehicle_type='car',
            brand='Toyota',
            model='Vios 2024',
            latitude=10.8251,
            longitude=106.6317,
            fuel_level=75,
            status='available',
            price_per_minute=5000,
            qr_code='QRCAR001'
        )
    ]
    
    db.session.add(admin)
    db.session.add(user)
    for vehicle in vehicles:
        db.session.add(vehicle)
    
    db.session.commit()
    
    print("✅ Đã tạo dữ liệu mẫu!")
    print("👤 Admin: admin@smartrent.com / admin123")
    print("👤 User: demo@smartrent.com / demo123")
    print("🚗 3 xe đã được thêm vào hệ thống")
```

Chạy:
```powershell
python init_data.py
```

## 🌐 Map Alternatives (Tất cả MIỄN PHÍ)

### 1. OpenStreetMap (Đang dùng) ⭐
```javascript
// Đã tích hợp sẵn
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png')
```

### 2. OpenTopoMap (Bản đồ địa hình)
```javascript
L.tileLayer('https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png')
```

### 3. CartoDB (Bản đồ đẹp)
```javascript
L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png')
```

### 4. Thunderforest (Free với đăng ký)
- Free tier: 150,000 requests/tháng
- Đăng ký: https://www.thunderforest.com/

## 💡 Tips

### Giảm dung lượng dependencies
Nếu không cần một số thư viện:
```powershell
# Chỉ cài những gì cần thiết
pip install Flask Flask-SQLAlchemy Flask-Login Flask-WTF python-dotenv
```

### Sử dụng SQLite thay vì PostgreSQL
Trong `.env`:
```env
DATABASE_URL=sqlite:///smartrent.db
```

### Test nhanh không cần database
Sử dụng in-memory database:
```env
DATABASE_URL=sqlite:///:memory:
```

## 🐛 Troubleshooting

### Lỗi: ModuleNotFoundError
```powershell
pip install -r requirements.txt
```

### Lỗi: Database error
```powershell
# Xóa database cũ và tạo lại
rm smartrent.db
python run.py
```

### Lỗi: Port 5000 đã được sử dụng
Trong `run.py`, đổi port:
```python
app.run(port=5001)
```

## 📚 Tài liệu tham khảo

- **Leaflet**: https://leafletjs.com/
- **OpenStreetMap**: https://www.openstreetmap.org/
- **Flask**: https://flask.palletsprojects.com/
- **SQLAlchemy**: https://www.sqlalchemy.org/

---

**🎉 Tất cả đều MIỄN PHÍ! Không cần thẻ tín dụng hay đăng ký dịch vụ trả phí!**
