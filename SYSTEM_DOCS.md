# SmartRent ITS - Tài liệu hệ thống

## ✅ Đã hoàn thành

### 1. Auto-Release Xe sau 5 phút
**File:** `app/utils/scheduler.py`

- Tự động release xe về trạng thái `available` nếu trip `pending` > 5 phút
- Chạy background thread kiểm tra mỗi 60 giây
- Cập nhật:
  - `vehicle.status` = 'available'
  - `trip.status` = 'cancelled'
  - Sync Firebase nếu enabled

**Config:**
```env
# .env hoặc config.py
ENABLE_AUTO_RELEASE=true
AUTO_RELEASE_TIMEOUT_MINUTES=5  # Mặc định 5 phút
```

**Log:**
```
[Scheduler] Background auto-release scheduler started (checking every 60s)
[Scheduler] Auto-released vehicle MOTOR001 from trip TRIP20260112185409
[Scheduler] Released 12 expired bookings
```

### 2. Firebase Sync
**File:** `app/utils/repositories.py`

Hệ thống đã sync Firebase ở các điểm:

1. **Book xe** (`vehicle_controller.py`):
   - Sync vehicle status → 'reserved'
   - Sync trip data to Firestore

2. **Verify OTP** (`trip_controller.py`):
   - Sync vehicle status → 'in_use'
   - Sync trip status → 'in_progress'
   - Sync unlock method, time

3. **Auto-release** (`scheduler.py`):
   - Sync vehicle status → 'available'

**Kiểm tra Firebase:**
```bash
python test_firebase.py
```

**Log khi sync:**
```
[Booking] ✓ Firebase synced: vehicle MOTOR001 → reserved
[DEBUG] ✓ Firebase sync SUCCESS for vehicle MOTOR001
[Scheduler] ✓ Firebase synced: vehicle MOTOR001 → available
```

## 📊 Kiến trúc hệ thống

```
User đặt xe
    ↓
Vehicle: available → reserved
Trip: pending (created_at)
Firebase: Sync vehicle + trip
    ↓
[5 phút]
    ↓
Scheduler kiểm tra (mỗi 60s)
    ├─ Trip pending > 5 phút?
    │  ├─ YES → Auto-release
    │  │   ├─ Vehicle → available
    │  │   ├─ Trip → cancelled
    │  │   └─ Firebase sync
    │  └─ NO → Skip
    ↓
User nhập OTP đúng
    ↓
Vehicle: reserved → in_use
Trip: pending → in_progress
Firebase: Sync status
```

## 🔧 Cấu hình

### Config cần thiết (.env)
```env
# Firebase (đã có sẵn)
FIREBASE_ENABLED=true
FIREBASE_PROJECT_ID=smartrent-its
FIREBASE_CREDENTIALS_PATH=smartrent-firebase-credentials.json

# Auto-release (mới thêm)
ENABLE_AUTO_RELEASE=true
AUTO_RELEASE_TIMEOUT_MINUTES=5

# Email OTP (đã có sẵn)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=bata79892@gmail.com
MAIL_PASSWORD=xqdi fhbc ewpf nyhf
```

## 📝 API Endpoints

### Book xe
```http
POST /vehicles/{id}/book
Response: {
  "success": true,
  "trip_id": 18,
  "trip_code": "TRIP20260112185409",
  "message": "Đặt xe thành công! Mã OTP đã được gửi..."
}
```
- Vehicle: available → reserved
- Trip: pending
- Firebase: Synced

### Verify OTP
```http
POST /trips/{id}/verify-otp
Body: {
  "otp": "185409",
  "vehicle_code": "MOTOR001"
}
Response: {
  "success": true,
  "message": "Xe đã được mở khóa..."
}
```
- Vehicle: reserved → in_use
- Trip: pending → in_progress
- Firebase: Synced

## 🎯 Luồng hoạt động

1. **User book xe:**
   - Check balance >= estimated_cost
   - Create trip (status=pending, created_at=now)
   - Reserve vehicle (status=reserved)
   - Send OTP email
   - **Sync Firebase**

2. **Sau 5 phút không OTP:**
   - Scheduler detect trip.created_at < now - 5min
   - Auto-release: vehicle → available, trip → cancelled
   - **Sync Firebase**
   - Log: "Auto-released vehicle X from trip Y"

3. **User nhập OTP đúng (trong 5 phút):**
   - Verify OTP
   - Unlock vehicle: status → in_use
   - Start trip: status → in_progress
   - **Sync Firebase**

## 🐛 Debug & Monitoring

### Xem log scheduler
```bash
# Server terminal sẽ hiện log mỗi 60s
[Scheduler] Background auto-release scheduler started
[Scheduler] Auto-released vehicle MOTOR001...
[Scheduler] Released X expired bookings
```

### Test Firebase connection
```bash
python test_firebase.py
```

### Check xe đang reserved
```python
from app.models import Vehicle
reserved = Vehicle.query.filter_by(status='reserved').all()
print(f"Reserved: {len(reserved)}")
```

### Check trips pending
```python
from app.models import Trip
pending = Trip.query.filter_by(status='pending').all()
print(f"Pending: {len(pending)}")
```

## ⚙️ Files đã thay đổi

1. **app/utils/scheduler.py** (NEW)
   - Background job auto-release xe

2. **app/__init__.py**
   - Import và start scheduler
   - Add cache-busting headers

3. **config.py**
   - ENABLE_AUTO_RELEASE
   - AUTO_RELEASE_TIMEOUT_MINUTES

4. **app/controllers/vehicle_controller.py**
   - Enhanced Firebase sync khi book xe
   - Log sync status

5. **app/controllers/trip_controller.py**
   - Enhanced Firebase sync khi verify OTP
   - Log sync status chi tiết

6. **test_firebase.py** (NEW)
   - Script test Firebase connection

## 📈 Kết quả test

### Auto-release hoạt động ✅
```
[Scheduler] Released 12 expired bookings
[Scheduler] Auto-released vehicle MOTOR001 from trip TRIP20260112185409
```

### Firebase sync hoạt động ✅
```
[Firebase] Firestore initialized successfully
[Booking] ✓ Firebase synced: vehicle MOTOR001 → reserved
[DEBUG] ✓ Firebase sync SUCCESS for vehicle MOTOR001
```

### Email OTP hoạt động ✅
```
[DEBUG] Email send result: success=True
250 2.0.0 OK (Gmail accepted)
```

## 🎉 Tính năng đã có

- ✅ Auto-release xe sau 5 phút không thanh toán
- ✅ Firebase sync tự động (vehicle + trip)
- ✅ Email OTP verification
- ✅ Background scheduler (check mỗi 60s)
- ✅ Config timeout có thể thay đổi
- ✅ Log đầy đủ cho debug
- ✅ Browser cache-busting headers
