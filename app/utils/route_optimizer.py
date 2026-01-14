"""
Route Optimization using A* Algorithm for Intelligent Transportation System
Tối ưu hóa tuyến đường sử dụng thuật toán A*
"""

import heapq
import math
import requests
from typing import List, Tuple, Dict, Optional


class Node:
    """Node trong graph cho A* algorithm"""
    def __init__(self, lat: float, lng: float, name: str = ""):
        self.lat = lat
        self.lng = lng
        self.name = name
        self.g = float('inf')  # Cost from start
        self.h = 0  # Heuristic cost to goal
        self.f = float('inf')  # Total cost
        self.parent = None
    
    def __lt__(self, other):
        return self.f < other.f
    
    def __eq__(self, other):
        return abs(self.lat - other.lat) < 0.0001 and abs(self.lng - other.lng) < 0.0001
    
    def __hash__(self):
        return hash((round(self.lat, 4), round(self.lng, 4)))


def haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """
    Tính khoảng cách Haversine giữa 2 điểm trên trái đất (km)
    """
    R = 6371  # Bán kính trái đất (km)
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlng/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c


def get_route_from_osrm(start_lat: float, start_lng: float, 
                        end_lat: float, end_lng: float,
                        waypoints: List[Dict[str, float]] = None) -> Optional[Dict]:
    """
    Lấy route thực tế từ OSRM API (theo đường phố thật)
    
    Args:
        start_lat, start_lng: Tọa độ điểm bắt đầu
        end_lat, end_lng: Tọa độ điểm kết thúc
        waypoints: Các điểm trung gian (optional)
    
    Returns:
        Dict với route coordinates và thông tin, hoặc None nếu fail
    """
    try:
        # Build coordinates string: lng,lat;lng,lat format
        coords = f"{start_lng},{start_lat}"
        
        if waypoints:
            for wp in waypoints:
                coords += f";{wp['lng']},{wp['lat']}"
        
        coords += f";{end_lng},{end_lat}"
        
        # OSRM API endpoint (public demo server)
        url = f"http://router.project-osrm.org/route/v1/driving/{coords}"
        params = {
            'overview': 'full',
            'geometries': 'geojson',
            'steps': 'false'
        }
        
        response = requests.get(url, params=params, timeout=5)
        
        if response.status_code != 200:
            print(f"[OSRM] API returned {response.status_code}")
            return None
        
        data = response.json()
        
        if data['code'] != 'Ok' or not data.get('routes'):
            print(f"[OSRM] No routes found")
            return None
        
        route = data['routes'][0]
        
        # Convert GeoJSON coordinates [lng, lat] to [lat, lng]
        coordinates = route['geometry']['coordinates']
        path = [{'lat': coord[1], 'lng': coord[0]} for coord in coordinates]
        
        # Distance in meters → km
        distance_km = route['distance'] / 1000
        
        # Duration in seconds → minutes
        duration_minutes = route['duration'] / 60
        
        print(f"[OSRM] ✅ Route found: {distance_km:.2f} km, {duration_minutes:.1f} minutes")
        
        return {
            'path': path,
            'distance_km': round(distance_km, 2),
            'duration_minutes': round(duration_minutes, 1),
            'source': 'osrm'
        }
        
    except requests.Timeout:
        print("[OSRM] ⚠️ Timeout - using fallback")
        return None
    except Exception as e:
        print(f"[OSRM] ❌ Error: {e}")
        return None


def heuristic(node: Node, goal: Node) -> float:
    """
    Heuristic function: Euclidean distance
    Ước lượng khoảng cách từ node hiện tại đến đích
    """
    return haversine_distance(node.lat, node.lng, goal.lat, goal.lng)


def get_neighbors(node: Node, all_nodes: List[Node], max_distance: float = 2.0) -> List[Node]:
    """
    Lấy các node láng giềng trong bán kính max_distance km
    """
    neighbors = []
    for other in all_nodes:
        if node != other:
            dist = haversine_distance(node.lat, node.lng, other.lat, other.lng)
            if dist <= max_distance:
                neighbors.append(other)
    return neighbors


def a_star_search(start: Node, goal: Node, all_nodes: List[Node]) -> Optional[List[Node]]:
    """
    Thuật toán A* tìm đường đi ngắn nhất
    
    Args:
        start: Điểm bắt đầu
        goal: Điểm kết thúc
        all_nodes: Danh sách tất cả các node (intersection points)
    
    Returns:
        List[Node]: Đường đi tối ưu, hoặc None nếu không tìm thấy
    """
    open_set = []
    closed_set = set()
    
    start.g = 0
    start.h = heuristic(start, goal)
    start.f = start.g + start.h
    
    heapq.heappush(open_set, start)
    
    iterations = 0
    max_iterations = 1000
    
    while open_set and iterations < max_iterations:
        iterations += 1
        current = heapq.heappop(open_set)
        
        # Đã đến đích
        if current == goal:
            path = []
            while current:
                path.append(current)
                current = current.parent
            return list(reversed(path))
        
        closed_set.add(current)
        
        # Duyệt các node láng giềng
        neighbors = get_neighbors(current, all_nodes)
        
        for neighbor in neighbors:
            if neighbor in closed_set:
                continue
            
            # Tính cost từ start đến neighbor qua current
            tentative_g = current.g + haversine_distance(
                current.lat, current.lng,
                neighbor.lat, neighbor.lng
            )
            
            if tentative_g < neighbor.g:
                neighbor.parent = current
                neighbor.g = tentative_g
                neighbor.h = heuristic(neighbor, goal)
                neighbor.f = neighbor.g + neighbor.h
                
                if neighbor not in open_set:
                    heapq.heappush(open_set, neighbor)
    
    # Không tìm thấy đường đi
    return None


def optimize_route(start_lat: float, start_lng: float, 
                   end_lat: float, end_lng: float,
                   waypoints: List[Dict[str, float]] = None) -> Dict:
    """
    Tối ưu hóa tuyến đường từ điểm A đến B
    
    Args:
        start_lat, start_lng: Tọa độ điểm bắt đầu
        end_lat, end_lng: Tọa độ điểm kết thúc
        waypoints: Danh sách các điểm trung gian (optional)
    
    Returns:
        Dict chứa thông tin route optimized
    """
    
    # TRY 1: Use OSRM for realistic routing (theo đường phố thật)
    osrm_route = get_route_from_osrm(start_lat, start_lng, end_lat, end_lng, waypoints)
    
    if osrm_route:
        # Success! Use OSRM route
        path = osrm_route['path']
        total_distance = osrm_route['distance_km']
        duration_minutes = osrm_route['duration_minutes']
        
        # Ước lượng chi phí (500 VND/phút cho bike)
        estimated_cost = duration_minutes * 500
        
        return {
            'success': True,
            'path': path,
            'distance_km': total_distance,
            'estimated_time_minutes': duration_minutes,
            'estimated_cost_vnd': int(estimated_cost),
            'waypoints_count': len(waypoints) if waypoints else 0,
            'algorithm': 'OSRM (Real Roads)',
            'avg_speed_kmh': round((total_distance / duration_minutes) * 60, 1) if duration_minutes > 0 else 30
        }
    
    # FALLBACK: Use grid-based A* (demo mode)
    print("[Route] Using fallback grid-based routing")
    
    # Tạo grid nodes cho TP.HCM (demo)
    nodes = []
    
    # Thêm start và end nodes
    start_node = Node(start_lat, start_lng, "Start")
    end_node = Node(end_lat, end_lng, "End")
    nodes.extend([start_node, end_node])
    
    # Tạo lưới các điểm trung gian (simulated intersections)
    lat_min, lat_max = min(start_lat, end_lat) - 0.02, max(start_lat, end_lat) + 0.02
    lng_min, lng_max = min(start_lng, end_lng) - 0.02, max(start_lng, end_lng) + 0.02
    
    step = 0.01  # ~1km grid
    lat = lat_min
    while lat <= lat_max:
        lng = lng_min
        while lng <= lng_max:
            nodes.append(Node(lat, lng))
            lng += step
        lat += step
    
    # Thêm waypoints nếu có
    if waypoints:
        for wp in waypoints:
            nodes.append(Node(wp['lat'], wp['lng'], wp.get('name', '')))
    
    # Chạy A* algorithm
    path = a_star_search(start_node, end_node, nodes)
    
    if not path:
        # Fallback: đường thẳng
        path = [start_node, end_node]
    
    # Tính toán thông tin route
    total_distance = 0
    for i in range(len(path) - 1):
        total_distance += haversine_distance(
            path[i].lat, path[i].lng,
            path[i+1].lat, path[i+1].lng
        )
    
    # Ước lượng thời gian (giả sử tốc độ trung bình 30 km/h)
    avg_speed = 30  # km/h
    estimated_time = (total_distance / avg_speed) * 60  # minutes
    
    # Ước lượng chi phí (500 VND/phút cho bike)
    estimated_cost = estimated_time * 500
    
    return {
        'success': True,
        'path': [{'lat': node.lat, 'lng': node.lng, 'name': node.name} for node in path],
        'distance_km': round(total_distance, 2),
        'estimated_time_minutes': round(estimated_time, 1),
        'estimated_cost_vnd': int(estimated_cost),
        'waypoints_count': len(path) - 2,
        'algorithm': 'A* (A-Star) Pathfinding',
        'avg_speed_kmh': avg_speed
    }


def calculate_optimal_speed(distance_km: float, traffic_level: str = 'normal') -> float:
    """
    Tính tốc độ tối ưu dựa trên khoảng cách và mức độ tắc nghẽn
    """
    base_speed = {
        'clear': 40,      # km/h
        'normal': 30,
        'heavy': 15,
        'congested': 10
    }
    
    speed = base_speed.get(traffic_level, 30)
    
    # Điều chỉnh tốc độ theo khoảng cách
    if distance_km < 1:
        speed *= 0.7  # Trong phố đi chậm hơn
    elif distance_km > 10:
        speed *= 1.2  # Đường xa có thể đi nhanh hơn
    
    return speed


def predict_traffic(hour: int, day_of_week: int) -> str:
    """
    Dự đoán mức độ tắc nghẽn theo giờ và ngày
    
    Args:
        hour: Giờ trong ngày (0-23)
        day_of_week: Thứ (0=Monday, 6=Sunday)
    
    Returns:
        str: 'clear', 'normal', 'heavy', 'congested'
    """
    # Giờ cao điểm buổi sáng (7-9h)
    if 7 <= hour <= 9 and day_of_week < 5:
        return 'heavy'
    
    # Giờ cao điểm buổi chiều (17-19h)
    if 17 <= hour <= 19 and day_of_week < 5:
        return 'congested'
    
    # Giờ trưa
    if 11 <= hour <= 13:
        return 'normal'
    
    # Đêm khuya
    if hour >= 22 or hour <= 5:
        return 'clear'
    
    # Cuối tuần
    if day_of_week >= 5:
        return 'normal'
    
    return 'normal'


def calculate_alternative_routes(start_lat: float, start_lng: float,
                                 end_lat: float, end_lng: float,
                                 hazard_zones: List = None,
                                 num_alternatives: int = 3) -> List[Dict]:
    """
    Tính toán nhiều routes thay thế, tránh hazard zones
    
    Args:
        start_lat, start_lng: Tọa độ điểm bắt đầu
        end_lat, end_lng: Tọa độ điểm kết thúc
        hazard_zones: List các HazardZone objects cần tránh
        num_alternatives: Số lượng routes thay thế cần tính
    
    Returns:
        List[Dict]: Danh sách routes với risk level và metrics
    """
    from app.utils.hazard_checker import check_route_hazards, point_in_polygon
    
    routes = []
    
    # Convert HazardZone objects to dicts for hazard_checker
    zones_data = []
    if hazard_zones:
        for zone in hazard_zones:
            zones_data.append({
                'id': zone.id,
                'zone_code': zone.zone_code,
                'zone_name': zone.zone_name,
                'hazard_type': zone.hazard_type,
                'severity': zone.severity,
                'description': zone.description,
                'warning_message': zone.warning_message,
                'polygon_coordinates': zone.polygon_coordinates,
                'min_latitude': zone.min_latitude,
                'max_latitude': zone.max_latitude,
                'min_longitude': zone.min_longitude,
                'max_longitude': zone.max_longitude,
                'color': zone.color,
                'is_active': zone.is_active
            })
    
    # Route 1: Đường thẳng (baseline - có thể đi qua hazard)
    direct_route = optimize_route(start_lat, start_lng, end_lat, end_lng)
    direct_route['route_type'] = 'direct'
    direct_route['route_name'] = 'Đường ngắn nhất'
    
    # Check hazards cho direct route
    if zones_data:
        route_points = [(p['lat'], p['lng']) for p in direct_route['path']]
        hazards_detected = check_route_hazards(route_points, zones_data)
        direct_route['hazards'] = hazards_detected
        direct_route['hazard_count'] = len(hazards_detected)
        direct_route['risk_level'] = _calculate_risk_level(hazards_detected)
    else:
        direct_route['hazards'] = []
        direct_route['hazard_count'] = 0
        direct_route['risk_level'] = 'safe'
    
    routes.append(direct_route)
    
    # Route 2 & 3: Alternative routes tránh hazard zones
    if zones_data and direct_route['hazard_count'] > 0:
        # Tạo waypoints để đi vòng tránh hazard zones
        for i in range(num_alternatives - 1):
            offset = 0.01 * (i + 1)  # Tăng độ lệch cho mỗi alternative
            
            # Tính waypoint ở bên phải hoặc trái của direct line
            mid_lat = (start_lat + end_lat) / 2
            mid_lng = (start_lng + end_lng) / 2
            
            # Perpendicular offset (đi vuông góc với đường thẳng)
            if i % 2 == 0:
                # Route đi bên phải
                waypoint_lat = mid_lat + offset
                waypoint_lng = mid_lng - offset
                route_name = f'Đường tránh {i+1} (bên phải)'
            else:
                # Route đi bên trái
                waypoint_lat = mid_lat - offset
                waypoint_lng = mid_lng + offset
                route_name = f'Đường tránh {i+1} (bên trái)'
            
            # Kiểm tra waypoint không nằm trong hazard zone
            waypoint_safe = True
            for zone in zones_data:
                if zone.get('is_active', True) and point_in_polygon((waypoint_lat, waypoint_lng), zone['polygon_coordinates']):
                    waypoint_safe = False
                    break
            
            if not waypoint_safe:
                # Tăng offset nếu waypoint vẫn trong hazard
                waypoint_lat += offset * 1.5
                waypoint_lng += offset * 1.5
            
            # Tính route qua waypoint
            alt_route = optimize_route(
                start_lat, start_lng, end_lat, end_lng,
                waypoints=[{'lat': waypoint_lat, 'lng': waypoint_lng}]
            )
            alt_route['route_type'] = 'alternative'
            alt_route['route_name'] = route_name
            
            # Check hazards cho alternative route
            route_points = [(p['lat'], p['lng']) for p in alt_route['path']]
            hazards_detected = check_route_hazards(route_points, zones_data)
            alt_route['hazards'] = hazards_detected
            alt_route['hazard_count'] = len(hazards_detected)
            alt_route['risk_level'] = _calculate_risk_level(hazards_detected)
            
            routes.append(alt_route)
    
    # Sort routes by risk level then distance
    routes.sort(key=lambda r: (
        _risk_score(r['risk_level']),
        r['distance_km']
    ))
    
    # Add route rankings
    for idx, route in enumerate(routes):
        route['rank'] = idx + 1
        route['recommended'] = (idx == 0)  # Route đầu tiên là recommended
    
    return routes


def _calculate_risk_level(hazards: List[Dict]) -> str:
    """
    Tính risk level dựa trên hazards detected
    """
    if not hazards:
        return 'safe'
    
    severity_scores = {'low': 1, 'medium': 2, 'high': 3, 'critical': 4}
    max_severity = max([severity_scores.get(h.get('severity', 'medium'), 2) for h in hazards])
    
    if max_severity >= 4:
        return 'critical'
    elif max_severity >= 3:
        return 'high'
    elif max_severity >= 2:
        return 'medium'
    else:
        return 'low'


def _risk_score(risk_level: str) -> int:
    """
    Convert risk level to numeric score for sorting
    """
    risk_scores = {
        'safe': 0,
        'low': 1,
        'medium': 2,
        'high': 3,
        'critical': 4
    }
    return risk_scores.get(risk_level, 2)
