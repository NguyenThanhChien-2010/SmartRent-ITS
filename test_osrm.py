"""
Test OSRM Integration
"""
import sys
import os

# Fix Windows console encoding
os.system('chcp 65001 > nul')
sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, 'D:\\Nam_3\\ITS\\SmartRent-ITS')

from app.utils.route_optimizer import optimize_route

print("=" * 60)
print("TESTING OSRM REALISTIC ROUTING")
print("=" * 60)

# Test route: Quan 1 -> Quan 12 (TP.HCM)
print("\nRoute: Quan 1 -> Quan 12")
print("Start: Ben Thanh (10.7729, 106.6981)")
print("End: Go Vap (10.8376, 106.6758)")

result = optimize_route(
    start_lat=10.7729,
    start_lng=106.6981,
    end_lat=10.8376,
    end_lng=106.6758
)

print("\n" + "=" * 60)
print("RESULT:")
print("=" * 60)
print(f"Success: {result['success']}")
print(f"Distance: {result['distance_km']} km")
print(f"Time: {result['estimated_time_minutes']} minutes")
print(f"Cost: {result['estimated_cost_vnd']:,} VND")
print(f"Algorithm: {result['algorithm']}")
print(f"Avg Speed: {result['avg_speed_kmh']} km/h")
print(f"Path points: {len(result['path'])} coordinates")

print("\n" + "=" * 60)
if 'OSRM' in result['algorithm']:
    print("SUCCESS! Route theo duong pho thuc te!")
    print("Route se hien thi realistic tren map nhu Google Maps")
else:
    print("WARNING: OSRM khong available, dung fallback grid")
    print("Check internet connection hoac OSRM server status")
print("=" * 60)
