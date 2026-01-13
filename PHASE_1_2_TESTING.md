# ✅ PHASE 1 & 2 HOÀN THÀNH - HƯỚNG DẪN TEST

## 🎯 ĐÃ TRIỂN KHAI

### Phase 1: Admin Features ✅
- ✅ HazardZone model với database table
- ✅ Point-in-Polygon algorithm (Ray-casting)
- ✅ Admin page: /admin/hazard-zones
- ✅ Vẽ polygon với Leaflet Draw 1.0.4
- ✅ CRUD API endpoints
- ✅ 4 demo zones trong database

### Phase 2: User Integration ✅
- ✅ API check hazards: /trips/api/check-route-hazards
- ✅ Leaflet version fixed (1.9.4 → 1.7.1)
- ✅ Hazard zones hiển thị trên user map
- ✅ Modal cảnh báo khi route đi qua hazard
- ✅ Severity colors và icons

---

## 🧪 HƯỚNG DẪN TEST ĐẦY ĐỦ

### 🔧 Chuẩn bị
```bash
# 1. Ensure server is running
python run.py

# Server should start on: http://localhost:5000
```

---

## 📝 TEST PHASE 1: ADMIN

### Bước 1: Đăng nhập Admin
1. URL: http://localhost:5000/auth/login
2. Credentials:
   - Email: `admin@smartrent.com`
   - Password: `admin123`

### Bước 2: Truy cập Hazard Zones Manager
1. URL: http://localhost:5000/admin/hazard-zones
2. **Kiểm tra:**
   - ✅ Thấy bản đồ (centered Hồ Chí Minh)
   - ✅ Thấy 4 demo zones trên bản đồ
   - ✅ Statistics: Total 4, Active 4
   - ✅ Danh sách zones dưới dạng cards

### Bước 3: Vẽ Polygon Mới
1. **Mở Console** (F12)
2. Click nút **Draw a polygon** (góc trái bản đồ)
3. Click 4-5 điểm để vẽ polygon
4. Double-click để hoàn thành
5. **Check Console:** Nên thấy `"Polygon created with X points"`

### Bước 4: Lưu Hazard Zone
1. Điền form:
   - Tên: "Test Hazard Zone"
   - Loại: Chọn bất kỳ (flood, construction, etc.)
   - Mức độ: Chọn bất kỳ
   - Mô tả: "Testing..."
2. Click **"Lưu vùng nguy hiểm"**
3. **Check Console:**
   ```
   📤 Sending hazard zone data: {...}
   📥 Response status: 200
   📥 Response data: {success: true, ...}
   ```
4. **Kết quả:** Alert "Đã tạo vùng..." → Trang reload → Thấy zone mới

### Debug nếu lỗi:
- **Console log lỗi gì?** → Gửi cho tôi
- **Server log gì?** → Check terminal
- **Nút "Lưu" disable?** → Chưa vẽ polygon

---

## 👤 TEST PHASE 2: USER

### Bước 1: Logout Admin → Login User
1. Logout khỏi admin
2. Login user bất kỳ (hoặc đăng ký mới)

### Bước 2: Lập kế hoạch Route
1. URL: http://localhost:5000/trips/plan
2. **Kiểm tra:**
   - ✅ Thấy form nhập điểm đầu/cuối
   - ✅ Leaflet 1.7.1 (check console, không có lỗi)

### Bước 3: Tìm Lộ Trình
1. Điền form:
   - Điểm xuất phát: "Bến Thành"
   - Điểm đến: "Nhà Thờ Đức Bà"
   - Loại xe: Bất kỳ
2. Click **"Tìm lộ trình"**
3. **Kiểm tra:**
   - ✅ Bản đồ hiển thị
   - ✅ Route vẽ màu xanh
   - ✅ **Hazard zones vẽ màu đỏ/cam/vàng** (polygon bán trong suốt)

### Bước 4: Cảnh Báo Hazards
Route demo đi qua "Ngập lụt Đường Nguyễn Huệ" (zone có sẵn)

**Nếu route đi qua hazard, sẽ thấy:**
1. **Console log:**
   ```
   🔍 Checking route for hazards...
   📥 Hazard check result: {has_hazards: true, count: X}
   ```
2. **Modal popup hiện ra** với:
   - Title: "⚠️ Cảnh báo Vùng Nguy hiểm"
   - Danh sách zones bị ảnh hưởng
   - Severity badges (RED/ORANGE/YELLOW)
   - Icons cho từng loại hazard
3. **Buttons:**
   - "Tôi đã hiểu" → Đóng modal
   - "Tìm đường khác" → Đóng modal

**Nếu không thấy popup:**
- Route không đi qua zone nào
- Check console log: `"No hazards detected"`

---

## 🔍 VERIFY DATABASE

Kiểm tra zones trong database:
```bash
python -c "from app import create_app; from app.models import HazardZone; app = create_app(); ctx = app.app_context(); ctx.push(); zones = HazardZone.query.all(); print(f'Total: {len(zones)}'); [print(f'{i+1}. {z.zone_name} ({z.severity}) - Active: {z.is_active}') for i, z in enumerate(zones)]"
```

Expected output:
```
Total: 4 (hoặc nhiều hơn nếu bạn đã tạo mới)
1. Ngập lụt Đường Nguyễn Huệ (high) - Active: True
2. Thi công Metro Bến Thành (medium) - Active: True
3. Tai nạn Ngã tư Hàng Xanh (critical) - Active: True
4. Test Hazard Zone (...) - Active: True
```

---

## 🐛 TROUBLESHOOTING

### Vấn đề: Map không hiển thị
- **Fix:** Refresh trang, đợi 2-3 giây
- **Nguyên nhân:** Leaflet chưa load xong

### Vấn đề: Không vẽ được polygon
- **Fix:** Click đúng nút polygon (góc trái)
- **Check:** Console có lỗi "L is not defined"?

### Vấn đề: Modal không hiện
- **Nguyên nhân:** Route không đi qua zone nào
- **Test:** Tạo zone rất lớn bao phủ toàn TP.HCM
- **Check:** Console log `has_hazards: false`

### Vấn đề: "Unauthorized" khi call API
- **Nguyên nhân:** Chưa login hoặc session hết
- **Fix:** Login lại

### Vấn đề: Zones không hiển thị trên user map
- **Check:** `/admin/api/hazard-zones` có return data?
- **Browser:** F12 → Network → Check request
- **Fix:** Ensure zones có `is_active: true`

---

## ✅ EXPECTED BEHAVIOR

### Admin Side:
1. ✅ Vẽ polygon → Form enable → Lưu → Reload → Thấy zone mới
2. ✅ Toggle switch → Zone active/inactive
3. ✅ Click "Xem" → Map zoom vào zone
4. ✅ Click "Xóa" → Confirm → Zone inactive

### User Side:
1. ✅ Tìm route → Map vẽ route + hazard zones
2. ✅ Route đi qua hazard → Modal popup cảnh báo
3. ✅ Click polygon trên map → Popup info zone
4. ✅ Console log đầy đủ info

---

## 📊 DEMO DATA LOCATIONS

Zones hiện có ở TP.HCM:
1. **Ngập lụt Đường Nguyễn Huệ** (HIGH) - District 1
2. **Thi công Metro Bến Thành** (MEDIUM) - District 1
3. **Tai nạn Ngã tư Hàng Xanh** (CRITICAL) - District 3

Route demo đi qua: Nguyễn Huệ zone → Should trigger warning!

---

## 🎯 SUCCESS CRITERIA

- [x] Admin vẽ được polygon
- [x] Admin lưu được zone
- [x] Database có zones
- [x] User thấy zones trên map
- [x] User nhận cảnh báo popup
- [x] Severity colors đúng
- [x] Icons hiển thị đúng
- [x] Modal đóng/mở OK

---

## 📝 GHI CHÚ

### Files đã tạo/sửa:
1. ✅ app/models/__init__.py (HazardZone model)
2. ✅ app/utils/hazard_checker.py (Algorithm)
3. ✅ app/controllers/admin_controller.py (Admin APIs)
4. ✅ app/controllers/trip_controller.py (User API)
5. ✅ app/views/admin/hazard_zones.html (Admin UI)
6. ✅ app/views/trips/plan.html (User UI)
7. ✅ app/static/css/hazard_zones.css (Styling)
8. ✅ create_hazard_table.py (Migration)
9. ✅ create_demo_hazards.py (Demo data)

### Ports & URLs:
- Server: http://localhost:5000
- Admin: http://localhost:5000/admin/hazard-zones
- User: http://localhost:5000/trips/plan
- API Test: http://localhost:5000/admin/api/hazard-zones

### Credentials:
- Admin: admin@smartrent.com / admin123
- User: (Tạo mới hoặc dùng có sẵn)

---

Nếu có vấn đề, gửi cho tôi:
1. Screenshot console (F12)
2. Server terminal log
3. Error message cụ thể
