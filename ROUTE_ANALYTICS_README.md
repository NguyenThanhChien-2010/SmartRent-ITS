# Route Analytics Dashboard - TIER 1

## 📊 Overview

Analytics dashboard cho admin để theo dõi và phân tích routes đã được plan bởi users trong hệ thống SmartRent ITS.

## ✅ Features Implemented

### 1. Database Model
- **RouteHistory** model với 16 fields:
  - User info (user_id)
  - Route coordinates (start_lat/lng, end_lat/lng)
  - Route addresses (start_address, end_address)
  - Metrics (distance_km, duration_minutes, estimated_cost)
  - Hazard info (hazards_detected, hazard_zones_passed)
  - Algorithm tracking (routing_algorithm: OSRM/A*)
  - Timestamps (created_at with index)

### 2. Non-Intrusive Logging
- **Safe logging** wrapped in try/except - không ảnh hưởng main functionality
- Auto-logs mỗi route planning event từ `/trips/api/optimize-route`
- Stores địa chỉ và coordinates để analytics chi tiết

### 3. Admin Analytics Page
**URL:** `/admin/route-analytics`

**Stats Cards:**
- Total Routes (với % change vs tuần trước)
- Average Distance (km/route)
- Average Duration (minutes/route)
- Routes with Hazards (với % of total)

**Charts (Chart.js):**
- Line Chart: Routes theo thời gian (daily)
- Doughnut Chart: Algorithm usage (OSRM vs A*)
- Bar Charts: Top 10 start/end locations

**Tables:**
- Top 20 Popular Routes (start → end với count, avg metrics)
- Hazard Zone Impact (zones affected, % routes, avg/day)

### 4. API Endpoint
**Endpoint:** `GET /admin/api/route-analytics?days=<7|30|90|all>`

**Returns:**
```json
{
  "stats": { total_routes, routes_change, avg_distance, ... },
  "routes_over_time": { labels: [], values: [] },
  "algorithm_usage": { labels: [], values: [] },
  "top_start_locations": { labels: [], values: [] },
  "top_end_locations": { labels: [], values: [] },
  "top_routes": [ {start, end, count, avg_distance, ...} ],
  "hazard_impact": [ {zone_name, severity, routes_affected, ...} ]
}
```

### 5. UI Integration
- Menu item: **ITS Analytics → Route Analytics** (icon: chart-line)
- Dashboard card: **Route Analytics TIER 1** (links to analytics page)
- Filter: Date range selector (7/30/90 days, all)
- Responsive design with Bootstrap 5

## 🔧 Files Modified/Created

### Created:
1. `create_route_history_table.py` - Migration script
2. `test_route_analytics.py` - Test data generator
3. `app/views/admin/route_analytics.html` - Analytics UI
4. `ROUTE_ANALYTICS_README.md` - This file

### Modified:
1. `app/models/__init__.py` - Added RouteHistory model
2. `app/controllers/admin_controller.py` - Added 2 routes:
   - `/admin/route-analytics` (page)
   - `/admin/api/route-analytics` (API)
3. `app/controllers/trip_controller.py` - Added safe logging to `/api/optimize-route`
4. `app/views/trips/plan.html` - Send address data to API
5. `app/views/base.html` - Added menu item
6. `app/views/admin/dashboard.html` - Added analytics card

## 🚀 Setup Instructions

### 1. Create Database Table
```bash
python create_route_history_table.py
```

### 2. Generate Test Data (Optional)
```bash
python test_route_analytics.py
```

### 3. Access Dashboard
1. Start server: `python run.py`
2. Login as admin
3. Navigate to: **ITS Analytics → Route Analytics**
4. Or direct: http://localhost:5000/admin/route-analytics

## 📈 Usage

### Automatic Data Collection
- Routes are automatically logged when users plan trips at `/trips/plan`
- Each geocode + optimize-route call creates a RouteHistory record
- No user action needed - 100% automatic

### Manual Data Analysis
1. Select date range filter (7/30/90 days or all)
2. Click "Cập nhật" to refresh data
3. View charts and tables
4. Identify popular routes, hazard impact

### Monitoring Hazard Zones
- See which hazard zones affect most routes
- % of total routes impacted
- Average routes/day through each zone
- Helps prioritize zone management

## 🔒 Safety Features

### Non-Breaking Logging
```python
try:
    # Log route to database
    route_history = RouteHistory(...)
    db.session.add(route_history)
    db.session.commit()
except Exception as log_error:
    # SAFE: Don't break main functionality
    print(f"[Warning] Analytics logging failed: {log_error}")
    db.session.rollback()
```

### Conflict Prevention
- ✅ New model (RouteHistory) - không touch existing models
- ✅ New routes - không modify existing routes
- ✅ Optional logging - wrapped in try/except
- ✅ Isolated analytics - không affect trip planning
- ✅ Admin-only access - không expose to users

## 📊 Sample Queries

### Total Routes Last 30 Days
```python
from datetime import datetime, timedelta
cutoff = datetime.utcnow() - timedelta(days=30)
total = RouteHistory.query.filter(RouteHistory.created_at >= cutoff).count()
```

### Top Routes
```python
from sqlalchemy import func
top_routes = db.session.query(
    RouteHistory.start_address,
    RouteHistory.end_address,
    func.count(RouteHistory.id).label('count')
).group_by(RouteHistory.start_address, RouteHistory.end_address)\
 .order_by(func.count(RouteHistory.id).desc())\
 .limit(10).all()
```

### Hazard Impact
```python
hazard_routes = RouteHistory.query.filter(
    RouteHistory.hazards_detected > 0
).count()
```

## 🎯 Future Enhancements (TIER 2+)

- Real-time dashboard updates (WebSocket)
- Export to CSV/Excel
- Custom date range picker
- Route heatmap overlay
- Predictive analytics (ML)
- User behavior patterns
- Cost optimization insights
- A/B testing alternative routes

## ⚠️ Notes

- Requires Chart.js 3.9.1 (CDN loaded in template)
- PostgreSQL JSON field support needed
- Index on `created_at` for fast queries
- Test data includes 4 sample routes

## ✅ Testing Checklist

- [x] Database table created
- [x] RouteHistory model working
- [x] Safe logging doesn't break route planning
- [x] Analytics API returns correct data
- [x] Charts render properly
- [x] Tables display data
- [x] Date filter works
- [x] Menu navigation works
- [x] Admin-only access enforced
- [x] No conflicts with existing features

---

**Status:** ✅ COMPLETE - TIER 1 Implementation
**Conflicts:** ❌ NONE - Safe, isolated implementation
**Production Ready:** ✅ YES
