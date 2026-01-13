"""
Test hazard zone API directly
"""
import requests
import json

# Test data
test_zone = {
    'zone_name': 'Test Zone API',
    'hazard_type': 'construction',
    'severity': 'medium',
    'description': 'Testing API endpoint',
    'warning_message': 'This is a test',
    'polygon_coordinates': [
        [10.7700, 106.6900],
        [10.7700, 106.6920],
        [10.7680, 106.6920],
        [10.7680, 106.6900]
    ],
    'is_active': True
}

print("Testing Hazard Zone API...")
print("=" * 60)
print(f"Test data: {json.dumps(test_zone, indent=2)}")
print("=" * 60)
print("\n⚠️  Note: You need to be logged in as admin to test this API")
print("Please test from browser console or use session cookies")
