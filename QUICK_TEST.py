"""
🚀 QUICK TEST GUIDE - ALTERNATIVE ROUTES
========================================

✅ SETUP (1 phút):
1. python run.py
2. Browser: http://localhost:5000/auth/login
3. Login: user@smartrent.com / user123
4. Click icon 🗺️ trên navbar

📍 TEST CASE 1: Route qua hazard zone (2 phút)
---------------------------------------------
1. Kéo xuống section "Demo Data" trên trang Plan Trip
2. Click button "Demo: Route qua vùng nguy hiểm"
3. Observe modal xuất hiện với:
   ✅ Cảnh báo hazard zones
   ✅ Loading "Đang tính toán đường thay thế..."
   ✅ 3 routes cards:
      - Đường ngắn nhất (có hazard)
      - Đường tránh 1 (bên phải)  
      - Đường tránh 2 (bên trái) ← Đề xuất
   ✅ Mỗi route có: distance, time, cost, risk level

4. Click "Chọn đường này" ở route có badge [Đề xuất]
5. Verify:
   ✅ Modal đóng
   ✅ Route vẽ màu xanh trên map
   ✅ Alert hiển thị thông tin route

🎯 EXPECTED OUTPUT:
Modal hiển thị như này:

┌────────────────────────────────────┐
│ ⚠️  Ngập lụt Đường Nguyễn Huệ     │
│ [HIGH] Mưa lớn, ngập sâu 30cm     │
├────────────────────────────────────┤
│ 🗺️  Đường thay thế                 │
│                                    │
│ 🟢 Đường tránh 2 [Đề xuất][An toàn]│
│    2.1km | 7min | 3,500đ          │
│    [Chọn đường này]                │
│                                    │
│ ⚪ Đường tránh 1 [Rủi ro thấp]     │
│    2.3km | 8min | 4,000đ          │
│    [Chọn đường này]                │
│                                    │
│ ⚪ Đường ngắn nhất [Rủi ro cao]    │
│    1.8km | 6min | 3,000đ          │
│    ⚠️ 2 vùng nguy hiểm             │
│    [Chọn đường này]                │
└────────────────────────────────────┘

✅ SUCCESS = Bạn thấy modal như trên + chọn route được!

❌ TROUBLESHOOTING:
- Modal không hiện → Check console (F12), xem có lỗi JS không
- Routes giống nhau → Bình thường nếu không có hazards
- Loading không biến → Server lỗi, check terminal logs

📊 DEMO SCRIPT (cho presentation):
"Tôi plan route từ Nguyễn Huệ → Bến Thành.
Hệ thống PHÁT HIỆN đi qua vùng ngập lụt.
NHƯNG không chỉ cảnh báo, nó TỰ ĐỘNG đề xuất 2 đường tránh!
Route an toàn: xa hơn 300m, tốn thêm 500đ, nhưng KHÔNG ngập!
⭐ Đây là điểm vượt trội so với Google Maps!"
"""

print(__doc__)
print("\n" + "="*50)
print("✅ Alternative Routes Feature READY!")
print("📝 Follow guide trên để test")
print("="*50)
