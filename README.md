# SmartRent ITS - Hệ thống cho thuê phương tiện thông minh

Ứng dụng cho thuê phương tiện thông minh (Intelligent Transportation System) được xây dựng với Python Flask theo mô hình MVC.

## Tính năng chính

### 1. Chức năng người dùng
- **Tìm kiếm & Định vị (GIS)**: Hiển thị xe trên bản đồ realtime
- **Đặt xe & Thanh toán**: Ví điện tử, quét QR mở khóa Smart Lock
- **Lập kế hoạch hành trình**: Gợi ý lộ trình tối ưu, cảnh báo tắc đường
- **Lịch sử & Phản hồi**: Lưu chuyến đi, đánh giá xe

### 2. Quản lý phương tiện (IoT)
- **Giám sát trạng thái (Telematics)**: Pin, nhiên liệu, áp suất lốp
- **Geofencing**: Cảnh báo khi xe ra khỏi khu vực cho phép
- **Điều phối xe (Rebalancing)**: Di chuyển xe đến nơi có nhu cầu cao

### 3. Quản trị hệ thống
- **Dashboard phân tích (Big Data)**: Thống kê lưu lượng, doanh thu
- **Quản lý bảo trì**: Tự động nhắc lịch bảo dưỡng
- **Hỗ trợ khẩn cấp (eCall)**: Xử lý tín hiệu SOS

## Cấu trúc dự án

```
SmartRent-ITS/
├── app/
│   ├── models/           # Database models
│   │   └── __init__.py   # User, Vehicle, Trip, Payment, etc.
│   ├── controllers/      # Controllers (Routes)
│   │   ├── auth_controller.py
│   │   ├── vehicle_controller.py
│   │   ├── trip_controller.py
│   │   ├── payment_controller.py
│   │   ├── admin_controller.py
│   │   ├── emergency_controller.py
│   │   └── main_controller.py
│   ├── views/           # HTML Templates
│   │   ├── base.html
│   │   ├── index.html
│   │   ├── auth/
│   │   ├── vehicles/
│   │   └── admin/
│   ├── static/          # CSS, JS, Images
│   │   ├── css/
│   │   └── js/
│   ├── utils/           # Utility functions
│   └── __init__.py      # App initialization
├── config.py            # Configuration
├── requirements.txt     # Dependencies
├── .env.example        # Environment variables template
└── run.py              # Application entry point
```

## Cài đặt

### 1. Clone repository
```bash
cd c:\Users\Lenovo\Downloads\SmartRent-ITS
```

### 2. Tạo môi trường ảo
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Cài đặt dependencies
```bash
pip install -r requirements.txt
```

### 4. Cấu hình môi trường
Sao chép file `.env.example` thành `.env` và cập nhật thông tin:
```bash
copy .env.example .env
```

Chỉnh sửa file `.env`:
```
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://user:password@localhost/smartrent_db
GOOGLE_MAPS_API_KEY=your-google-maps-key
STRIPE_SECRET_KEY=your-stripe-key
```

### 5. Tạo database
```bash
# PostgreSQL
createdb smartrent_db

# Hoặc sử dụng SQLite (development)
# Database sẽ tự động được tạo khi chạy app
```

### 6. Chạy ứng dụng
```bash
python run.py
```

Truy cập: http://localhost:5000

## Models (Database)

### User
- Thông tin người dùng, authentication
- Ví điện tử
- Vị trí hiện tại

### Vehicle
- Thông tin xe (loại, biển số, màu sắc)
- Tọa độ GPS
- Dữ liệu IoT (pin, nhiên liệu, áp suất lốp)
- Smart Lock & QR Code
- Geofencing

### Booking
- Đặt xe
- Trạng thái booking

### Trip
- Chuyến đi
- Điểm đầu/điểm cuối
- Khoảng cách, thời gian
- Chi phí
- Đánh giá

### Payment
- Thanh toán
- Phương thức (ví, thẻ, Stripe)
- Lịch sử giao dịch

### Maintenance
- Lịch bảo trì
- Loại bảo trì
- Chi phí sửa chữa

### EmergencyAlert
- Cảnh báo khẩn cấp (eCall)
- Loại sự cố (tai nạn, hỏng xe, trộm cắp)
- Vị trí, mức độ nghiêm trọng

### IoTLog
- Log dữ liệu từ cảm biến xe
- Lịch sử di chuyển
- Cảnh báo vi phạm geofence

## API Endpoints

### Authentication
- `POST /auth/register` - Đăng ký
- `POST /auth/login` - Đăng nhập
- `GET /auth/logout` - Đăng xuất
- `GET /auth/profile` - Thông tin cá nhân

### Vehicles
- `GET /vehicles/` - Danh sách xe
- `GET /vehicles/map` - Bản đồ xe
- `GET /vehicles/api/nearby` - Tìm xe gần
- `GET /vehicles/<id>` - Chi tiết xe
- `POST /vehicles/<id>/book` - Đặt xe
- `POST /vehicles/<id>/unlock` - Mở khóa
- `POST /vehicles/<id>/lock` - Khóa xe

### Trips
- `GET /trips/history` - Lịch sử chuyến đi
- `GET /trips/<id>` - Chi tiết chuyến đi
- `POST /trips/start/<booking_id>` - Bắt đầu chuyến đi
- `POST /trips/<id>/end` - Kết thúc chuyến đi
- `POST /trips/<id>/feedback` - Đánh giá

### Payments
- `GET /payments/wallet` - Ví điện tử
- `POST /payments/topup` - Nạp tiền
- `GET /payments/history` - Lịch sử thanh toán

### Admin
- `GET /admin/dashboard` - Dashboard
- `GET /admin/users` - Quản lý người dùng
- `GET /admin/vehicles` - Quản lý xe
- `POST /admin/vehicles/add` - Thêm xe
- `GET /admin/maintenance` - Quản lý bảo trì
- `GET /admin/alerts` - Cảnh báo khẩn cấp
- `GET /admin/rebalancing` - Điều phối xe

### Emergency
- `POST /emergency/report` - Báo cáo khẩn cấp
- `POST /emergency/button/<vehicle_id>` - Nút SOS
- `GET /emergency/my-alerts` - Cảnh báo của tôi

## Technologies

- **Backend**: Flask, SQLAlchemy
- **Database**: PostgreSQL (hoặc SQLite cho dev)
- **Frontend**: Bootstrap 5, Leaflet.js, Chart.js
- **Maps**: Leaflet/OpenStreetMap, Google Maps API
- **Payment**: Stripe
- **IoT**: MQTT (Paho)
- **Authentication**: Flask-Login, JWT

## Tính năng nâng cao cần implement

1. **IoT Integration**
   - MQTT broker để nhận dữ liệu từ xe
   - Realtime telemetry dashboard
   - Automatic alerts

2. **AI/ML**
   - Dự đoán nhu cầu
   - Tối ưu giá động (Dynamic Pricing)
   - Phát hiện bất thường

3. **Mobile App**
   - React Native hoặc Flutter
   - Push notifications
   - Offline mode

4. **Advanced GIS**
   - Route optimization
   - Traffic integration
   - Restricted zones management

## Hướng dẫn phát triển

### Thêm model mới
```python
# app/models/__init__.py
class NewModel(db.Model):
    # Define fields
    pass
```

### Thêm controller mới
```python
# app/controllers/new_controller.py
from flask import Blueprint
new_bp = Blueprint('new', __name__, url_prefix='/new')

@new_bp.route('/')
def index():
    return render_template('new/index.html')
```

### Đăng ký blueprint
```python
# app/__init__.py
from app.controllers.new_controller import new_bp
app.register_blueprint(new_bp)
```

## License
Educational project for ITS course

## Contact
Email: admin@smartrent.com
