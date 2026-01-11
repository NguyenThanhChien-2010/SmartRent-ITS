from typing import List, Dict, Optional
from datetime import datetime
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


class BookingRepository:
    COLLECTION = 'bookings'

    @staticmethod
    def add(doc: Dict, doc_id: Optional[str] = None) -> str:
        """Thêm booking vào Firestore"""
        db = get_db()
        if db is None:
            return ''
        try:
            ref = db.collection(BookingRepository.COLLECTION)
            if doc_id:
                ref.document(str(doc_id)).set(doc)
                return str(doc_id)
            else:
                new_ref = ref.add(doc)[1]
                return new_ref.id
        except Exception as e:
            print(f'[BookingRepository] Error adding booking: {e}')
            return ''

    @staticmethod
    def update_fields(doc_id: str, fields: Dict) -> bool:
        """Cập nhật booking"""
        db = get_db()
        if db is None:
            return False
        try:
            db.collection(BookingRepository.COLLECTION).document(str(doc_id)).set(fields, merge=True)
            return True
        except Exception as e:
            print(f'[BookingRepository] Error updating booking: {e}')
            return False

    @staticmethod
    def get_by_id(doc_id: str) -> Optional[Dict]:
        """Lấy booking theo ID"""
        db = get_db()
        if db is None:
            return None
        doc = db.collection(BookingRepository.COLLECTION).document(str(doc_id)).get()
        if not doc.exists:
            return None
        data = doc.to_dict()
        data['id'] = data.get('id') or doc.id
        return data


class TripRepository:
    COLLECTION = 'trips'

    @staticmethod
    def add(doc: Dict, doc_id: Optional[str] = None) -> str:
        """Thêm trip vào Firestore"""
        db = get_db()
        if db is None:
            return ''
        try:
            # Convert datetime objects to ISO format strings
            if 'start_time' in doc and isinstance(doc['start_time'], datetime):
                doc['start_time'] = doc['start_time'].isoformat()
            if 'end_time' in doc and isinstance(doc['end_time'], datetime):
                doc['end_time'] = doc['end_time'].isoformat()
            if 'created_at' in doc and isinstance(doc['created_at'], datetime):
                doc['created_at'] = doc['created_at'].isoformat()
            if 'updated_at' in doc and isinstance(doc['updated_at'], datetime):
                doc['updated_at'] = doc['updated_at'].isoformat()
            
            ref = db.collection(TripRepository.COLLECTION)
            if doc_id:
                ref.document(str(doc_id)).set(doc)
                return str(doc_id)
            else:
                new_ref = ref.add(doc)[1]
                return new_ref.id
        except Exception as e:
            print(f'[TripRepository] Error adding trip: {e}')
            return ''

    @staticmethod
    def update_fields(doc_id: str, fields: Dict) -> bool:
        """Cập nhật trip"""
        db = get_db()
        if db is None:
            return False
        try:
            # Convert datetime objects to ISO format strings
            if 'end_time' in fields and isinstance(fields['end_time'], datetime):
                fields['end_time'] = fields['end_time'].isoformat()
            if 'updated_at' in fields and isinstance(fields['updated_at'], datetime):
                fields['updated_at'] = fields['updated_at'].isoformat()
            
            db.collection(TripRepository.COLLECTION).document(str(doc_id)).set(fields, merge=True)
            return True
        except Exception as e:
            print(f'[TripRepository] Error updating trip: {e}')
            return False

    @staticmethod
    def get_by_id(doc_id: str) -> Optional[Dict]:
        """Lấy trip theo ID"""
        db = get_db()
        if db is None:
            return None
        doc = db.collection(TripRepository.COLLECTION).document(str(doc_id)).get()
        if not doc.exists:
            return None
        data = doc.to_dict()
        data['id'] = data.get('id') or doc.id
        return data

    @staticmethod
    def get_user_trips(user_id: int, limit: int = 50) -> List[Dict]:
        """Lấy danh sách trips của user"""
        db = get_db()
        if db is None:
            return []
        try:
            query = db.collection(TripRepository.COLLECTION)\
                .where('user_id', '==', user_id)\
                .order_by('created_at', direction='DESCENDING')\
                .limit(limit)
            docs = query.stream()
            items = []
            for d in docs:
                data = d.to_dict()
                data['id'] = data.get('id') or d.id
                items.append(data)
            return items
        except Exception as e:
            print(f'[TripRepository] Error getting user trips: {e}')
            return []


class PaymentRepository:
    COLLECTION = 'payments'

    @staticmethod
    def add(doc: Dict, doc_id: Optional[str] = None) -> str:
        """Thêm payment vào Firestore"""
        db = get_db()
        if db is None:
            return ''
        try:
            # Convert datetime objects to ISO format strings
            if 'transaction_date' in doc and isinstance(doc['transaction_date'], datetime):
                doc['transaction_date'] = doc['transaction_date'].isoformat()
            if 'created_at' in doc and isinstance(doc['created_at'], datetime):
                doc['created_at'] = doc['created_at'].isoformat()
            
            ref = db.collection(PaymentRepository.COLLECTION)
            if doc_id:
                ref.document(str(doc_id)).set(doc)
                return str(doc_id)
            else:
                new_ref = ref.add(doc)[1]
                return new_ref.id
        except Exception as e:
            print(f'[PaymentRepository] Error adding payment: {e}')
            return ''

    @staticmethod
    def get_by_id(doc_id: str) -> Optional[Dict]:
        """Lấy payment theo ID"""
        db = get_db()
        if db is None:
            return None
        doc = db.collection(PaymentRepository.COLLECTION).document(str(doc_id)).get()
        if not doc.exists:
            return None
        data = doc.to_dict()
        data['id'] = data.get('id') or doc.id
        return data
