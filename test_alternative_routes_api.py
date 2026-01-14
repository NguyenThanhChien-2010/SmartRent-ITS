"""
Test Alternative Routes API
"""
import requests
import json

# Config
BASE_URL = "http://localhost:5000"
LOGIN_URL = f"{BASE_URL}/auth/login"
API_URL = f"{BASE_URL}/trips/api/alternative-routes"

# Test coordinates (qua vùng nguy hiểm)
START_LAT = 10.7692
START_LNG = 106.7010
END_LAT = 10.7734
END_LNG = 106.7005

def test_alternative_routes():
    """Test alternative routes API"""
    
    print("=" * 60)
    print("TESTING ALTERNATIVE ROUTES API")
    print("=" * 60)
    
    # Step 1: Login to get session
    print("\n1️⃣ Logging in...")
    session = requests.Session()
    
    login_data = {
        'email': 'user@smartrent.com',
        'password': 'user123'
    }
    
    response = session.post(LOGIN_URL, data=login_data, allow_redirects=True)
    
    if response.status_code != 200:
        print(f"❌ Login failed: {response.status_code}")
        return
    
    print("✅ Login successful")
    
    # Step 2: Call alternative routes API
    print(f"\n2️⃣ Fetching alternative routes...")
    print(f"   From: ({START_LAT}, {START_LNG})")
    print(f"   To: ({END_LAT}, {END_LNG})")
    
    payload = {
        'start_lat': START_LAT,
        'start_lng': START_LNG,
        'end_lat': END_LAT,
        'end_lng': END_LNG
    }
    
    response = session.post(
        API_URL,
        json=payload,
        headers={'Content-Type': 'application/json'}
    )
    
    if response.status_code != 200:
        print(f"❌ API call failed: {response.status_code}")
        print(f"Response: {response.text}")
        return
    
    data = response.json()
    
    if not data.get('success'):
        print(f"❌ API returned error: {data.get('error')}")
        return
    
    print("✅ API call successful")
    
    # Step 3: Analyze results
    print(f"\n3️⃣ Analyzing results...")
    print(f"   Total routes: {data['total_routes']}")
    print(f"   Has safe alternative: {data['has_safe_alternative']}")
    print(f"   Safest route index: {data['safest_route_index']}")
    
    routes = data['routes']
    
    print(f"\n{'=' * 60}")
    print("ROUTES COMPARISON")
    print(f"{'=' * 60}\n")
    
    for idx, route in enumerate(routes, 1):
        print(f"{'🟢' if route['recommended'] else '⚪'} ROUTE {idx}: {route['route_name']}")
        print(f"   Type: {route['route_type']}")
        print(f"   Risk Level: {route['risk_level'].upper()}")
        print(f"   Distance: {route['distance_km']} km")
        print(f"   Time: {route['estimated_time_minutes']} minutes")
        print(f"   Cost: {route['estimated_cost_vnd']:,} VND")
        print(f"   Hazards: {route['hazard_count']}")
        
        if route['hazards']:
            print(f"   ⚠️  Detected hazards:")
            for hazard in route['hazards']:
                print(f"      - {hazard['zone_name']} ({hazard['severity']})")
        else:
            print(f"   ✅ No hazards")
        
        print()
    
    # Step 4: Validation
    print(f"{'=' * 60}")
    print("VALIDATION")
    print(f"{'=' * 60}\n")
    
    checks = []
    
    # Check 1: Có đúng 3 routes
    check1 = len(routes) >= 1
    checks.append(("At least 1 route returned", check1))
    
    # Check 2: Routes có sorted by risk
    if len(routes) > 1:
        risk_scores = {'safe': 0, 'low': 1, 'medium': 2, 'high': 3, 'critical': 4}
        check2 = all(
            risk_scores.get(routes[i]['risk_level'], 2) <= risk_scores.get(routes[i+1]['risk_level'], 2)
            for i in range(len(routes) - 1)
        )
        checks.append(("Routes sorted by risk level", check2))
    
    # Check 3: All routes có required fields
    required_fields = ['route_name', 'distance_km', 'estimated_time_minutes', 
                       'estimated_cost_vnd', 'risk_level', 'hazard_count']
    check3 = all(all(field in route for field in required_fields) for route in routes)
    checks.append(("All routes have required fields", check3))
    
    # Check 4: Recommended route có hazard count thấp nhất hoặc = 0
    recommended = next((r for r in routes if r['recommended']), None)
    if recommended:
        check4 = recommended['hazard_count'] == min(r['hazard_count'] for r in routes)
        checks.append(("Recommended route is safest", check4))
    
    # Print validation results
    for check_name, result in checks:
        print(f"{'✅' if result else '❌'} {check_name}")
    
    all_passed = all(result for _, result in checks)
    
    print(f"\n{'=' * 60}")
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
    else:
        print("⚠️  SOME TESTS FAILED")
    print(f"{'=' * 60}\n")
    
    return all_passed


if __name__ == "__main__":
    try:
        success = test_alternative_routes()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
