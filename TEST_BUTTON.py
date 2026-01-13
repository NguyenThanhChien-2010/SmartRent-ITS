"""
Quick test to verify button state in hazard zones page
"""

# HƯỚNG DẪN TEST NÚT "LƯU VÙNG NGUY HIỂM"

print("=" * 60)
print("🧪 HƯỚNG DẪN TEST NÚT 'LƯU VÙNG NGUY HIỂM'")
print("=" * 60)

print("""
📋 CHECKLIST:

1. ✅ MỞ TRANG ADMIN
   URL: http://localhost:5000/admin/hazard-zones
   
2. ✅ MỞ CONSOLE (F12)
   - Tab Console để xem logs
   - Tab Network để xem requests

3. ✅ KIỂM TRA BAN ĐẦU
   Nút "Lưu vùng nguy hiểm":
   - ❌ Phải BỊ DISABLE (màu xám, không click được)
   - ⚠️  Có alert màu vàng: "Bước tiếp theo: Vẽ polygon..."
   
4. ✅ VẼ POLYGON
   Cách 1 (Nút Draw):
   - Click nút polygon ở góc trái bản đồ
   - Click 4-5 điểm trên bản đồ
   - Double-click để hoàn thành
   
   Cách 2 (Test trong Console):
   Nếu không thấy nút, chạy trong Console:
   ```javascript
   // Tạo polygon demo
   const testPolygon = L.polygon([
       [10.77, 106.70],
       [10.77, 106.71],
       [10.76, 106.71],
       [10.76, 106.70]
   ]);
   drawnItems.addLayer(testPolygon);
   currentPolygon = testPolygon;
   currentPolygon.coordinates = [[10.77, 106.70],[10.77, 106.71],[10.76, 106.71],[10.76, 106.70]];
   document.getElementById('polygonInfo').classList.remove('d-none');
   document.getElementById('polygonPoints').textContent = 4;
   document.getElementById('drawInstructions').classList.add('d-none');
   document.getElementById('saveBtn').disabled = false;
   ```

5. ✅ SAU KHI VẼ XONG
   Nút "Lưu vùng nguy hiểm" phải:
   - ✅ Màu XANH (btn-success)
   - ✅ Không disable (click được)
   - ✅ Alert vàng biến mất
   - ✅ Alert xanh hiện: "Polygon đã vẽ: X điểm"

6. ✅ ĐIỀN FORM
   - Tên vùng: "Test Zone ABC"
   - Loại: Chọn bất kỳ
   - Mức độ: Chọn bất kỳ
   
7. ✅ CLICK NÚT "LƯU"
   Console sẽ log:
   ```
   📤 Sending hazard zone data: {...}
   ```
   
   Nếu thành công:
   ```
   📥 Response status: 200
   📥 Response data: {success: true, ...}
   ```
   
   Alert: "✅ Đã tạo vùng..."
   Trang reload tự động

8. ❌ NẾU NÚT VẪN DISABLE
   Chạy trong Console:
   ```javascript
   // Check state
   console.log('Map loaded:', typeof map !== 'undefined');
   console.log('Leaflet Draw loaded:', typeof L.Draw !== 'undefined');
   console.log('Current polygon:', currentPolygon);
   console.log('Button disabled:', document.getElementById('saveBtn').disabled);
   
   // Force enable (chỉ để test)
   document.getElementById('saveBtn').disabled = false;
   ```

9. ❌ TROUBLESHOOTING
   
   Lỗi: "Cannot read properties of undefined (reading 'Draw')"
   → Leaflet Draw chưa load
   → Đợi 2-3 giây, hoặc refresh trang
   
   Lỗi: "currentPolygon is null"
   → Chưa vẽ polygon
   → Vẽ lại hoặc dùng test code ở bước 4
   
   Lỗi: Nút vẫn disable sau khi vẽ
   → Check console có error không
   → Dùng force enable code ở bước 8

10. ✅ VERIFY DATABASE
    Sau khi lưu, chạy:
    ```bash
    python -c "from app import create_app; from app.models import HazardZone; app = create_app(); ctx = app.app_context(); ctx.push(); zones = HazardZone.query.all(); print(f'Total: {len(zones)}'); [print(f'{z.zone_name}') for z in zones]"
    ```

📊 EXPECTED TIMELINE:
- 0s: Trang load → Nút DISABLE
- 1s: Map render → Alert vàng hiện
- 2s: Leaflet Draw load → Nút polygon góc trái hiện
- 3s+: User vẽ polygon → Nút ENABLE ngay lập tức

🐛 COMMON ISSUES:

Issue: Không thấy nút vẽ polygon
Fix: Refresh trang, đợi 3 giây

Issue: Console error "L.Draw is not a constructor"
Fix: Leaflet Draw đang load, đợi thêm

Issue: Nút enable nhưng không submit
Fix: Check form validation (tên vùng bắt buộc)

Issue: Submit OK nhưng không reload
Fix: Check server log, có thể lỗi backend
""")

print("=" * 60)
print("🎯 QUICK TEST")
print("=" * 60)
print("Chạy đoạn này trong Browser Console sau khi trang load xong:")
print("""
// Test button state
const btn = document.getElementById('saveBtn');
console.log('Button exists:', !!btn);
console.log('Button disabled:', btn.disabled);
console.log('Button classes:', btn.className);

// Test polygon creation
if (typeof L !== 'undefined' && map) {
    console.log('✅ Map OK');
    console.log('✅ Leaflet OK');
} else {
    console.log('❌ Map not ready');
}

// List all zones
fetch('/admin/api/hazard-zones')
    .then(r => r.json())
    .then(d => console.log('📊 Zones:', d.zones));
""")

print("\n✅ Done! Follow the steps above to test.")
