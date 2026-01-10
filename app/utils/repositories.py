from typing import List, Dict, Optional
from .firebase_client import get_db

class VehicleRepository:
    COLLECTION = 'vehicles'

    @staticmethod
    def list_available(vehicle_type: str = 'all') -> List[Dict]:
        db = get_db()
        if db is None:
            return []
        query = db.collection(VehicleRepository.COLLECTION).where('status', '==', 'available')
        if vehicle_type != 'all':
            query = query.where('vehicle_type', '==', vehicle_type)
        docs = query.stream()
        items = []
        for d in docs:
            data = d.to_dict()
            data['id'] = data.get('id') or d.id
            items.append(data)
        return items

    @staticmethod
    def get_by_id(doc_id: str) -> Optional[Dict]:
        db = get_db()
        if db is None:
            return None
        doc = db.collection(VehicleRepository.COLLECTION).document(str(doc_id)).get()
        if not doc.exists:
            return None
        data = doc.to_dict()
        data['id'] = data.get('id') or doc.id
        return data

    @staticmethod
    def update_fields(doc_id: str, fields: Dict) -> bool:
        db = get_db()
        if db is None:
            return False
        try:
            db.collection(VehicleRepository.COLLECTION).document(str(doc_id)).set(fields, merge=True)
            return True
        except Exception:
            return False

    @staticmethod
    def add(doc: Dict, doc_id: Optional[str] = None) -> str:
        db = get_db()
        if db is None:
            return ''
        ref = db.collection(VehicleRepository.COLLECTION)
        if doc_id:
            ref.document(str(doc_id)).set(doc)
            return str(doc_id)
        else:
            new_ref = ref.add(doc)[1]
            return new_ref.id
