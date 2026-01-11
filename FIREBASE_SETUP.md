# Hướng dẫn cấu hình Firebase cho SmartRent-ITS

## Bước 1: Tạo Firebase Project

1. Truy cập [Firebase Console](https://console.firebase.google.com/)
2. Click **"Add project"** hoặc **"Thêm dự án"**
3. Đặt tên project: `smartrent-its` (hoặc tên khác)
4. Tắt Google Analytics (không cần cho project này)
5. Click **"Create project"**

## Bước 2: Tạo Firestore Database

1. Trong Firebase Console, vào **"Firestore Database"**
2. Click **"Create database"**
3. Chọn **"Start in test mode"** (cho development)
4. Chọn location gần bạn nhất (ví dụ: `asia-southeast1` cho Singapore)
5. Click **"Enable"**

## Bước 3: Tạo Service Account Key

1. Vào **"Project Settings"** (icon bánh răng ⚙️ ở góc trên bên trái)
2. Chọn tab **"Service accounts"**
3. Click **"Generate new private key"**
4. Click **"Generate key"** để tải file JSON xuống
5. **Quan trọng**: Đổi tên file vừa tải xuống thành `smartrent-firebase-credentials.json`
6. Copy file này vào thư mục gốc của project: `C:\Users\Lenovo\Downloads\SmartRent-ITS\`

## Bước 4: Cấu hình file .env

File `.env` đã được tạo sẵn. Bạn chỉ cần cập nhật:

```env
# Bật Firebase
FIREBASE_ENABLED=true

# Project ID (tìm trong Firebase Console > Project Settings)
FIREBASE_PROJECT_ID=smartrent-its

# Đường dẫn đến file credentials
FIREBASE_CREDENTIALS_PATH=smartrent-firebase-credentials.json
```

## Bước 5: Kiểm tra cài đặt

```bash
# Đảm bảo đã cài firebase-admin
pip install firebase-admin

# Chạy ứng dụng
python run.py
```

Khi ứng dụng khởi động, bạn sẽ thấy:
```
[Firebase] Firestore initialized successfully.
```

## Bước 6: Kiểm tra dữ liệu trên Firebase

1. Truy cập Firebase Console
2. Vào **Firestore Database**
3. Khi tạo trip, booking, payment → dữ liệu sẽ xuất hiện realtime trong các collections:
   - `trips` - Danh sách chuyến đi
   - `bookings` - Đặt xe
   - `payments` - Thanh toán
   - `vehicles` - Phương tiện

## Cấu trúc dữ liệu Firestore

### Collection: trips
```json
{
  "trip_code": "TR20260111143525",
  "user_id": 1,
  "vehicle_id": 2,
  "booking_id": 3,
  "start_latitude": 10.762622,
  "start_longitude": 106.660172,
  "start_address": "Địa chỉ hiện tại",
  "start_time": "2026-01-11T14:35:25",
  "end_time": null,
  "end_latitude": null,
  "end_longitude": null,
  "distance_km": 0,
  "duration_minutes": 0,
  "total_cost": 0,
  "status": "in_progress",
  "rating": null,
  "feedback": null,
  "created_at": "2026-01-11T14:35:25",
  "updated_at": "2026-01-11T14:35:25"
}
```

### Collection: payments
```json
{
  "payment_code": "PAY20260111143800",
  "user_id": 1,
  "trip_id": 5,
  "amount": 15000,
  "payment_method": "wallet",
  "payment_status": "completed",
  "transaction_date": "2026-01-11T14:38:00",
  "created_at": "2026-01-11T14:38:00"
}
```

### Collection: vehicles
```json
{
  "id": 1,
  "vehicle_code": "VH001",
  "vehicle_type": "motorbike",
  "brand": "Honda",
  "model": "Wave Alpha",
  "license_plate": "51F-12345",
  "latitude": 10.762622,
  "longitude": 106.660172,
  "status": "available",
  "battery_level": 95,
  "price_per_minute": 2000,
  "is_locked": true
}
```

## Tính năng đồng bộ

Hệ thống sẽ tự động:
1. ✅ **Lưu trip** lên Firestore khi bắt đầu chuyến đi
2. ✅ **Cập nhật trip** khi kết thúc (end_time, distance, cost)
3. ✅ **Lưu payment** khi thanh toán
4. ✅ **Cập nhật vehicle status** (available/in_use)
5. ✅ **Lưu feedback** khi user đánh giá

## Lưu ý bảo mật

⚠️ **QUAN TRỌNG**: 
- File `smartrent-firebase-credentials.json` chứa private key
- **KHÔNG commit** file này lên GitHub
- File đã được thêm vào `.gitignore`

## Troubleshooting

### Lỗi: "firebase_admin not installed"
```bash
pip install firebase-admin
```

### Lỗi: "Permission denied"
- Kiểm tra file credentials có đúng đường dẫn không
- Đảm bảo Firestore đã được enable trong Firebase Console

### Lỗi: "Missing or insufficient permissions"
- Vào Firestore Rules và đổi thành test mode:
```
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /{document=**} {
      allow read, write: if true;
    }
  }
}
```

## Demo & Testing

Sau khi cấu hình xong:
1. Đăng nhập vào app
2. Đặt xe và bắt đầu chuyến đi
3. Mở Firebase Console > Firestore Database
4. Refresh để thấy dữ liệu realtime!

---

**Chúc bạn thành công với project ITS!** 🚀
