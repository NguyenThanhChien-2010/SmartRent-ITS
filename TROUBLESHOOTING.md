# SmartRent ITS - Hướng dẫn xử lý dữ liệu

## 🔧 Vấn đề đã giải quyết

### 1. **Xe "in_use" nhưng không có trip active**
**Nguyên nhân:** 
- Scheduler auto-release đã cancel trip nhưng chưa sync Firebase
- Hoặc trip bị lỗi trong quá trình end_trip

**Đã sửa:**
```bash
# Chạy script fix thủ công
python fix_orphaned_vehicles.py

# Hoặc dùng API endpoint
POST /admin/vehicles/fix-orphaned
GET /admin/system/check-consistency
```

**Kết quả:** Fixed 6 xe (BIKE003, BIKE004, MOTOR002, MOTOR004, CAR002, CAR003) → available

---

### 2. **Firebase Collections và Data Sync**

**Firebase đang hoạt động với các collections:**

| Collection | Documents | Mô tả |
|-----------|-----------|-------|
| `vehicles` | 21 | Thông tin xe (status, location, battery) |
| `trips` | 9 | Chuyến đi (đã hoàn thành/đang diễn ra) |
| `bookings` | 4 | Đặt chỗ |
| `users` | 5 | Thông tin người dùng |
| `payments` | 32 | Giao dịch thanh toán |

**Sync points (khi nào data được đồng bộ Firebase):**
1. ✅ **Book xe:** Vehicle → `reserved`, Trip → `pending`
2. ✅ **Verify OTP:** Vehicle → `in_use`, Trip → `in_progress`
3. ✅ **End trip:** Vehicle → `available`, Trip → `completed`
4. ✅ **Auto-release (5 phút):** Vehicle → `available`, Trip → `cancelled`

---

## 📊 Admin Tools

### Kiểm tra consistency
```bash
# Script command line
python check_consistency.py

# Hoặc API
curl http://localhost:5000/admin/system/check-consistency
```

**Response:**
```json
{
  "vehicle_status": {
    "available": 20,
    "in_use": 0
  },
  "trip_status": {
    "cancelled": 13,
    "completed": 2
  },
  "orphaned_vehicles": [],
  "orphaned_trips": [],
  "is_consistent": true
}
```

### Fix orphaned vehicles
```bash
# Script
python fix_orphaned_vehicles.py

# API
curl -X POST http://localhost:5000/admin/vehicles/fix-orphaned
```

### Xem Firebase data
```bash
python view_firebase_data.py
# Chọn collection: vehicles/trips/bookings/users/payments
```

---

## 🔍 Debugging Tips

### 1. Kiểm tra xe đang "in_use"
```python
from app.models import Vehicle, Trip

# Tìm xe in_use
vehicles = Vehicle.query.filter_by(status='in_use').all()

# Kiểm tra có trip active không
for v in vehicles:
    trip = Trip.query.filter_by(vehicle_id=v.id, status='in_progress').first()
    print(f"{v.vehicle_code}: {'OK' if trip else 'ORPHANED'}")
```

### 2. Kiểm tra Firebase sync
```python
from app.utils.firebase_client import get_db
from app.utils.repositories import VehicleRepository

# Test connection
db = get_db()
print("Firebase connected:", db is not None)

# List vehicles in Firebase
vehicles = VehicleRepository.list_available()
print(f"Firebase vehicles: {len(vehicles)}")
```

### 3. Log trong terminal
Khi chạy server, xem logs:
```
[Booking] ✓ Firebase synced: vehicle BIKE001 → reserved
[DEBUG] ✓ Firebase sync SUCCESS for vehicle MOTOR001
[Scheduler] Released 12 expired bookings
```

---

## ⚙️ Auto-release Scheduler

**Cấu hình trong `.env`:**
```env
ENABLE_AUTO_RELEASE=true
AUTO_RELEASE_TIMEOUT_MINUTES=5  # Default: 5 phút
```

**Hoạt động:**
- Chạy mỗi 60 giây
- Tìm trip `pending` > 5 phút
- Auto-cancel trip
- Release vehicle về `available`
- Sync Firebase

**Logs:**
```
[Scheduler] Auto-released vehicle MOTOR001 from trip TRIP20260112185409
[Scheduler] ✓ Firebase synced: vehicle MOTOR001 → available
[Scheduler] Released 1 expired bookings
```

---

## 📍 Admin Dashboard Updates

### Trips Today Page
**Cập nhật:** Thêm status filter và statistics

**URL:** `http://localhost:5000/admin/trips/today?status=all`

**Filters:**
- `?status=all` - Tất cả
- `?status=completed` - Hoàn thành
- `?status=in_progress` - Đang diễn ra
- `?status=pending` - Đang chờ
- `?status=cancelled` - Đã hủy

**Statistics:**
```
Total: 15
Completed: 2
In Progress: 0
Pending: 0
Cancelled: 13
```

---

## 🐛 Common Issues

### Issue: "Xe đang 'in_use' trên map nhưng không có trip"
**Fix:**
```bash
python fix_orphaned_vehicles.py
# Hoặc reload trang admin và click "Fix Orphaned Vehicles"
```

### Issue: "Firebase không có data"
**Check:**
1. `FIREBASE_ENABLED=true` trong `.env`
2. File `smartrent-firebase-credentials.json` tồn tại
3. Run `python test_firebase.py`

### Issue: "Xe không auto-release sau 5 phút"
**Check:**
1. Server có đang chạy không?
2. Xem log có message `[Scheduler] Background auto-release scheduler started`
3. Kiểm tra `ENABLE_AUTO_RELEASE=true`

---

## 📝 Summary

**Đã fix:**
- ✅ 6 xe orphaned → available
- ✅ Firebase sync hoạt động (vehicles, trips, bookings, users, payments)
- ✅ Auto-release scheduler (5 phút timeout)
- ✅ Admin tools để check consistency
- ✅ API endpoints để fix lỗi

**Firebase Collections:**
- ✅ vehicles (21 docs)
- ✅ trips (9 docs)
- ✅ bookings (4 docs)
- ✅ users (5 docs)
- ✅ payments (32 docs)

**Scripts:**
- `check_consistency.py` - Kiểm tra xe/trip consistency
- `fix_orphaned_vehicles.py` - Fix xe orphaned
- `view_firebase_data.py` - Xem data Firebase
- `test_firebase.py` - Test Firebase connection
