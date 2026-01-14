"""
TEST COMPLETE FLOW: Geocoding + OSRM Routing
"""
import requests

BASE_URL = "http://localhost:5000"

# Test addresses (using known locations)
START_ADDR = "Ben Thanh Market, Ho Chi Minh"
END_ADDR = "Tan Son Nhat Airport, Ho Chi Minh"

def geocode_address(address):
    """Geocode using Nominatim"""
    url = f"https://nominatim.openstreetmap.org/search?q={address}&format=json&limit=1"
    headers = {'User-Agent': 'SmartRent-ITS/1.0'}
    
    response = requests.get(url, headers=headers)
    data = response.json()
    
    if data:
        return {
            'lat': float(data[0]['lat']),
            'lng': float(data[0]['lon']),
            'display_name': data[0]['display_name']
        }
    return None

print("=" * 80)
print("TEST GEOCODING + OSRM ROUTING")
print("=" * 80)

# Step 1: Geocode start address
print("\n1. Geocoding START address...")
print(f"   Address: {START_ADDR[:80]}...")
start = geocode_address(START_ADDR)

if start:
    print(f"   ✓ Found: {start['lat']}, {start['lng']}")
    print(f"   Display: {start['display_name']}")
else:
    print("   ✗ Not found")
    exit(1)

# Step 2: Geocode end address
print("\n2. Geocoding END address...")
print(f"   Address: {END_ADDR[:80]}...")
end = geocode_address(END_ADDR)

if end:
    print(f"   ✓ Found: {end['lat']}, {end['lng']}")
    print(f"   Display: {end['display_name']}")
else:
    print("   ✗ Not found")
    exit(1)

# Step 3: Calculate route
print("\n3. Calculating OSRM route...")

import sys
sys.path.insert(0, 'D:\\Nam_3\\ITS\\SmartRent-ITS')
from app.utils.route_optimizer import optimize_route

route = optimize_route(
    start['lat'], start['lng'],
    end['lat'], end['lng']
)

print(f"   ✓ Algorithm: {route['algorithm']}")
print(f"   ✓ Distance: {route['distance_km']} km")
print(f"   ✓ Time: {route['estimated_time_minutes']} minutes")
print(f"   ✓ Cost: {route['estimated_cost_vnd']:,} VND")
print(f"   ✓ Path points: {len(route['path'])} coordinates")

print("\n" + "=" * 80)
if 'OSRM' in route['algorithm']:
    print("SUCCESS! Complete flow works:")
    print("1. Address → Geocoding → Coordinates")
    print("2. Coordinates → OSRM → Realistic route")
    print("3. Frontend will display route correctly!")
else:
    print("WARNING: OSRM not used, fallback to grid")
print("=" * 80)
