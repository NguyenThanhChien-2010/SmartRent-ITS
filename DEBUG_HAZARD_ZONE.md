# 🔧 HƯỚNG DẪN DEBUG HAZARD ZONE

## ✅ Backend hoạt động OK
- Database table: ✅ Đã tạo
- Model import: ✅ OK
- API endpoints: ✅ OK  
- Test create zone: ✅ Thành công (4 zones trong DB)
- Server: ✅ Đang chạy

## 🧪 CÁCH TEST FRONTEND

### Bước 1: Đăng nhập Admin
1. Mở browser: http://localhost:5000
2. Đăng nhập với tài khoản admin:
   - Email: `admin@smartrent.com`
   - Password: `admin123`

### Bước 2: Truy cập Hazard Zones
1. URL: http://localhost:5000/admin/hazard-zones
2. **Mở Developer Console** (F12)
3. Chọn tab **Console**

### Bước 3: Vẽ Polygon và Lưu
1. Click nút **Polygon** (góc trái bản đồ)
2. Click 4-5 điểm để vẽ polygon
3. Double-click để hoàn thành
4. Điền form bên phải:
   - Tên vùng: "Test Vùng Nguy Hiểm"
   - Loại: Chọn bất kỳ
   - Mức độ: Chọn bất kỳ
5. Click **"Lưu vùng nguy hiểm"**

### Bước 4: Kiểm tra Console
Trong console bạn sẽ thấy:

**Nếu THÀNH CÔNG:**
```
📤 Sending hazard zone data: {zone_name: "...", ...}
📥 Response status: 200
📥 Response data: {success: true, message: "..."}
```

**Nếu LỖI:**
```
❌ Error: ...
```

## 🐛 CÁC LỖI THƯỜNG GẶP

### Lỗi 1: "Login required"
→ Chưa đăng nhập hoặc session hết hạn
→ **Fix:** Đăng nhập lại

### Lỗi 2: "Unauthorized" / 403
→ Tài khoản không phải admin
→ **Fix:** Đăng nhập với tài khoản admin

### Lỗi 3: "L is not defined"
→ Leaflet chưa load
→ **Fix:** Refresh trang, đợi load xong

### Lỗi 4: "Cannot read properties of undefined"
→ Leaflet Draw chưa load xong
→ **Fix:** Đã fix bằng dynamic loading

### Lỗi 5: Polygon không vẽ được
→ Draw control chưa hiển thị
→ **Fix:** Check console log, có thể cần refresh

### Lỗi 6: Nút "Lưu" bị disable
→ Chưa vẽ polygon
→ **Fix:** Vẽ polygon trước khi submit

## 📊 KIỂM TRA DATABASE

Chạy lệnh sau để xem zones trong DB:
```bash
python -c "from app import create_app; from app.models import HazardZone; app = create_app(); ctx = app.app_context(); ctx.push(); zones = HazardZone.query.all(); print(f'Total: {len(zones)}'); [print(f'{i+1}. {z.zone_name} ({z.severity})') for i, z in enumerate(zones)]"
```

## 🔥 TEST TRỰC TIẾP TỪ CONSOLE

Mở Console trong browser và chạy:
```javascript
// Test API connection
fetch('/admin/api/hazard-zones')
  .then(r => r.json())
  .then(d => console.log('Zones:', d))
```

## 📝 GHI CHÚ QUAN TRỌNG

1. **Luôn mở Console (F12)** khi test để thấy lỗi
2. **Check tab Network** để xem request/response
3. Server log cũng hiển thị debug info
4. Nếu vẫn lỗi, copy **toàn bộ error message** từ console

## ✅ CHECKLIST

- [ ] Server đang chạy (http://localhost:5000)
- [ ] Đã đăng nhập admin
- [ ] Console mở (F12)
- [ ] Thấy bản đồ hiển thị
- [ ] Thấy nút vẽ polygon
- [ ] Vẽ được polygon (ít nhất 3 điểm)
- [ ] Form đã điền đầy đủ
- [ ] Nút "Lưu" không disable
- [ ] Check console log khi click "Lưu"

Nếu tất cả OK mà vẫn không lưu được, gửi cho tôi:
1. Screenshot console log
2. Server terminal output khi click "Lưu"
