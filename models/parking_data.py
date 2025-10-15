"""
Parking Data Model - Handles parking detection records
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from config.database import db


class ParkingData:
    """Parking data model for detection records"""
    
    @staticmethod
    def create_from_raw_processing(user_id: str, camera_id: str,
                                   total_slots: int, total_cars_detected: int,
                                   occupied_slots: int, empty_slots: int,
                                   occupancy_rate: float, slots_details: List[Dict],
                                   coordinates: List[List[int]],
                                   image_dimensions: Dict[str, int],
                                   processing_time_ms: float) -> str:
        """
        Create parking data record from raw image processing
        
        Returns:
            Inserted document ID
        """
        if not db.is_connected():
            raise Exception("Database not connected")
        
        document = {
            'user_id': user_id,
            'camera_id': camera_id,
            'timestamp': datetime.utcnow(),
            'total_slots': total_slots,
            'total_cars_detected': total_cars_detected,
            'occupied_slots': occupied_slots,
            'empty_slots': empty_slots,
            'occupancy_rate': occupancy_rate,
            'slots_details': slots_details,
            'coordinates': coordinates,
            'image_dimensions': image_dimensions,
            'processing_time_ms': processing_time_ms,
            'source': 'raw_processing'
        }
        
        result = db.parking_data.insert_one(document)
        return str(result.inserted_id)
    
    @staticmethod
    def create_from_edge_processing(user_id: str, camera_id: str,
                                    total_slots: int, occupied_slots: int,
                                    empty_slots: int, occupancy_rate: float,
                                    total_cars_detected: Optional[int] = None,
                                    slots_details: Optional[List[Dict]] = None,
                                    coordinates: Optional[List[List[int]]] = None,
                                    additional_data: Optional[Dict] = None) -> str:
        """
        Create parking data record from edge device processing
        
        Returns:
            Inserted document ID
        """
        if not db.is_connected():
            raise Exception("Database not connected")
        
        document = {
            'user_id': user_id,
            'camera_id': camera_id,
            'timestamp': datetime.utcnow(),
            'total_slots': total_slots,
            'occupied_slots': occupied_slots,
            'empty_slots': empty_slots,
            'occupancy_rate': occupancy_rate,
            'total_cars_detected': total_cars_detected,
            'slots_details': slots_details or [],
            'coordinates': coordinates or [],
            'source': 'edge_processing',
            'additional_data': additional_data or {}
        }
        
        result = db.parking_data.insert_one(document)
        return str(result.inserted_id)
    
    @staticmethod
    def find_by_user(user_id: str, camera_id: Optional[str] = None,
                    start_date: Optional[datetime] = None,
                    end_date: Optional[datetime] = None,
                    limit: int = 50, skip: int = 0) -> Dict[str, Any]:
        """
        Find parking data for a user with optional filters
        
        Returns:
            Dictionary with data array, count, and latest summary
        """
        if not db.is_connected():
            raise Exception("Database not connected")
        
        # Build query
        query = {'user_id': user_id}
        
        if camera_id:
            query['camera_id'] = camera_id
        
        if start_date or end_date:
            query['timestamp'] = {}
            if start_date:
                query['timestamp']['$gte'] = start_date
            if end_date:
                query['timestamp']['$lte'] = end_date
        
        # Get total count
        total_count = db.parking_data.count_documents(query)
        
        # Get paginated data
        cursor = db.parking_data.find(query).sort('timestamp', -1).skip(skip).limit(limit)
        
        documents = []
        for doc in cursor:
            doc['_id'] = str(doc['_id'])
            doc['timestamp'] = doc['timestamp'].isoformat()
            documents.append(doc)
        
        # Get latest record
        latest_doc = db.parking_data.find_one(query, sort=[('timestamp', -1)])
        latest_summary = None
        if latest_doc:
            latest_summary = {
                'timestamp': latest_doc['timestamp'].isoformat(),
                'camera_id': latest_doc.get('camera_id'),
                'total_slots': latest_doc.get('total_slots'),
                'occupied_slots': latest_doc.get('occupied_slots'),
                'occupancy_rate': latest_doc.get('occupancy_rate')
            }
        
        return {
            'data': documents,
            'total_count': total_count,
            'returned_count': len(documents),
            'latest': latest_summary
        }
    
    @staticmethod
    def get_latest_by_camera(user_id: str, camera_id: str) -> Optional[Dict[str, Any]]:
        """Get latest parking data for a specific camera"""
        if not db.is_connected():
            return None
        
        doc = db.parking_data.find_one(
            {'user_id': user_id, 'camera_id': camera_id},
            sort=[('timestamp', -1)]
        )
        
        if doc:
            doc['_id'] = str(doc['_id'])
            doc['timestamp'] = doc['timestamp'].isoformat()
        
        return doc
    
    @staticmethod
    def delete_old_records(user_id: str, days: int = 90) -> int:
        """Delete records older than specified days"""
        if not db.is_connected():
            return 0
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        result = db.parking_data.delete_many({
            'user_id': user_id,
            'timestamp': {'$lt': cutoff_date}
        })
        
        return result.deleted_count
