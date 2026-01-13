"""
Hazard Zone Checker - Point-in-Polygon Algorithm
ITS Feature: Incident Management & Traveler Information System
"""
import math
from typing import List, Dict, Tuple, Optional


def point_in_polygon(point: Tuple[float, float], polygon: List[Tuple[float, float]]) -> bool:
    """
    Ray-casting algorithm to check if a point is inside a polygon.
    
    Args:
        point: (latitude, longitude) tuple
        polygon: List of (latitude, longitude) tuples forming the polygon
    
    Returns:
        True if point is inside polygon, False otherwise
    
    Algorithm:
        Cast a ray from the point to infinity and count intersections.
        Odd number = inside, Even number = outside
    """
    lat, lng = point
    n = len(polygon)
    inside = False
    
    p1_lat, p1_lng = polygon[0]
    
    for i in range(1, n + 1):
        p2_lat, p2_lng = polygon[i % n]
        
        # Check if point is on the same latitude range as the edge
        if lng > min(p1_lng, p2_lng):
            if lng <= max(p1_lng, p2_lng):
                if lat <= max(p1_lat, p2_lat):
                    # Calculate intersection point
                    if p1_lng != p2_lng:
                        x_intersection = (lng - p1_lng) * (p2_lat - p1_lat) / (p2_lng - p1_lng) + p1_lat
                    
                    if p1_lng == p2_lng or lat <= x_intersection:
                        inside = not inside
        
        p1_lat, p1_lng = p2_lat, p2_lng
    
    return inside


def point_in_bounding_box(
    point: Tuple[float, float], 
    min_lat: float, 
    max_lat: float, 
    min_lng: float, 
    max_lng: float
) -> bool:
    """
    Quick check if point is within bounding box (optimization).
    
    Args:
        point: (latitude, longitude) tuple
        min_lat, max_lat, min_lng, max_lng: Bounding box coordinates
    
    Returns:
        True if point is in bounding box
    """
    lat, lng = point
    return min_lat <= lat <= max_lat and min_lng <= lng <= max_lng


def calculate_polygon_bounds(polygon: List[Tuple[float, float]]) -> Dict[str, float]:
    """
    Calculate bounding box for a polygon.
    
    Args:
        polygon: List of (latitude, longitude) tuples
    
    Returns:
        Dictionary with min_latitude, max_latitude, min_longitude, max_longitude
    """
    lats = [p[0] for p in polygon]
    lngs = [p[1] for p in polygon]
    
    return {
        'min_latitude': min(lats),
        'max_latitude': max(lats),
        'min_longitude': min(lngs),
        'max_longitude': max(lngs)
    }


def check_route_hazards(route_points: List[Tuple[float, float]], hazard_zones: List[Dict]) -> List[Dict]:
    """
    Check if a route passes through any hazard zones.
    
    Args:
        route_points: List of (latitude, longitude) tuples representing the route
        hazard_zones: List of hazard zone dictionaries with polygon_coordinates and bounding box
    
    Returns:
        List of hazard zones that the route passes through
    """
    detected_hazards = []
    
    for zone in hazard_zones:
        # Skip inactive zones
        if not zone.get('is_active', True):
            continue
        
        # Convert polygon coordinates from [lat, lng] to tuples
        polygon = [(p[0], p[1]) for p in zone['polygon_coordinates']]
        
        # Check each point in the route
        for point in route_points:
            # First: Quick bounding box check (optimization)
            if not point_in_bounding_box(
                point,
                zone['min_latitude'],
                zone['max_latitude'],
                zone['min_longitude'],
                zone['max_longitude']
            ):
                continue
            
            # Second: Precise point-in-polygon check
            if point_in_polygon(point, polygon):
                # Add hazard to detected list (avoid duplicates)
                if zone not in detected_hazards:
                    detected_hazards.append(zone)
                break  # No need to check remaining points for this zone
    
    return detected_hazards


def get_severity_color(severity: str) -> str:
    """
    Get color code for severity level.
    
    Args:
        severity: Severity level (low, medium, high, critical)
    
    Returns:
        Hex color code
    """
    colors = {
        'low': '#ffc107',      # Yellow
        'medium': '#ff9800',   # Orange
        'high': '#ff5722',     # Deep Orange
        'critical': '#f44336'  # Red
    }
    return colors.get(severity.lower(), '#ff0000')


def get_severity_icon(severity: str) -> str:
    """
    Get Font Awesome icon for severity level.
    
    Args:
        severity: Severity level (low, medium, high, critical)
    
    Returns:
        Font Awesome icon class
    """
    icons = {
        'low': 'fa-exclamation-circle',
        'medium': 'fa-exclamation-triangle',
        'high': 'fa-radiation-alt',
        'critical': 'fa-skull-crossbones'
    }
    return icons.get(severity.lower(), 'fa-exclamation-triangle')


def get_hazard_type_icon(hazard_type: str) -> str:
    """
    Get Font Awesome icon for hazard type.
    
    Args:
        hazard_type: Type of hazard (flood, landslide, accident, construction, event)
    
    Returns:
        Font Awesome icon class
    """
    icons = {
        'flood': 'fa-water',
        'landslide': 'fa-mountain',
        'accident': 'fa-car-crash',
        'construction': 'fa-hard-hat',
        'event': 'fa-calendar-times',
        'other': 'fa-exclamation-triangle'
    }
    return icons.get(hazard_type.lower(), 'fa-exclamation-triangle')


def distance_between_points(point1: Tuple[float, float], point2: Tuple[float, float]) -> float:
    """
    Calculate distance between two GPS coordinates using Haversine formula.
    
    Args:
        point1: (latitude, longitude)
        point2: (latitude, longitude)
    
    Returns:
        Distance in kilometers
    """
    lat1, lon1 = point1
    lat2, lon2 = point2
    
    R = 6371  # Earth's radius in kilometers
    
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    
    a = (math.sin(dlat / 2) ** 2 + 
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
         math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c


def interpolate_route_points(route_points: List[Tuple[float, float]], max_distance_km: float = 0.1) -> List[Tuple[float, float]]:
    """
    Add intermediate points to a route for better hazard detection.
    
    Args:
        route_points: Original route points
        max_distance_km: Maximum distance between points (default 100m)
    
    Returns:
        Route with interpolated points
    """
    if len(route_points) < 2:
        return route_points
    
    interpolated = [route_points[0]]
    
    for i in range(len(route_points) - 1):
        p1 = route_points[i]
        p2 = route_points[i + 1]
        
        distance = distance_between_points(p1, p2)
        
        # If distance is large, add intermediate points
        if distance > max_distance_km:
            num_points = int(distance / max_distance_km) + 1
            
            for j in range(1, num_points):
                ratio = j / num_points
                interpolated_lat = p1[0] + (p2[0] - p1[0]) * ratio
                interpolated_lng = p1[1] + (p2[1] - p1[1]) * ratio
                interpolated.append((interpolated_lat, interpolated_lng))
        
        interpolated.append(p2)
    
    return interpolated
