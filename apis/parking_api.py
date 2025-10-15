"""
Parking API - Detection and data management endpoints
"""

import json
import logging
from datetime import datetime
from flask import Blueprint, request, jsonify
from middlewares.auth_middleware import token_required
from auth.jwt_handler import jwt_handler
from models.parking_data import ParkingData
from utils.image_utils import decode_image, validate_coordinates, get_image_dimensions
from utils.svg_generator import generate_svg, generate_slot_details
from parking_detection import ParkingDetectionSystem

logger = logging.getLogger(__name__)

# Create blueprint
parking_bp = Blueprint('parking', __name__, url_prefix='/parking')


@parking_bp.route('/updateRaw', methods=['POST'])
@token_required
def update_raw():
    """
    Process raw image frame with coordinates and save to MongoDB
    
    POST /parking/updateRaw
    Headers:
        - Authorization: Bearer <token>
    Body (multipart or JSON):
        - image: file or base64
        - coordinates: JSON array [[x1,y1,x2,y2], ...]
        - camera_id: string
    """
    try:
        # Get user ID from JWT
        user_id = jwt_handler.get_current_user_id()
        
        # Parse request
        if request.is_json:
            data = request.get_json()
            
            if 'image' not in data:
                return jsonify({'error': 'Missing image parameter'}), 400
            
            image = decode_image(data['image'])
            coordinates = data.get('coordinates')
            camera_id = data.get('camera_id')
            
        else:
            # Multipart form data
            if 'image' not in request.files:
                return jsonify({'error': 'Missing image file'}), 400
            
            image_file = request.files['image']
            image_bytes = image_file.read()
            image = decode_image(image_bytes)
            
            coordinates = json.loads(request.form.get('coordinates', '[]'))
            camera_id = request.form.get('camera_id')
        
        # Validate inputs
        if not camera_id:
            return jsonify({'error': 'camera_id is required'}), 400
        
        validate_coordinates(coordinates)
        
        parking_rectangles = [tuple(coord) for coord in coordinates]
        logger.info(f"Processing raw image for user {user_id}, camera {camera_id}")
        
        # Get image dimensions
        image_dims = get_image_dimensions(image)
        
        # Initialize detection system
        system = ParkingDetectionSystem(parking_positions=parking_rectangles)
        
        # Process frame
        annotated_frame, statistics, processing_time = system.process_frame(image)
        
        # Get detailed results
        vehicle_detections = system.vehicle_detector.detect_vehicles(image)
        occupancy = system.parking_manager.detect_occupancy(vehicle_detections)
        
        # Generate slot details and SVG
        slots_details = generate_slot_details(parking_rectangles, occupancy)
        svg_code = generate_svg(
            parking_rectangles,
            occupancy,
            image_dims['width'],
            image_dims['height']
        )
        
        # Save to MongoDB
        document_id = ParkingData.create_from_raw_processing(
            user_id=user_id,
            camera_id=camera_id,
            total_slots=statistics.get('total_slots', 0),
            total_cars_detected=len(vehicle_detections),
            occupied_slots=statistics.get('occupied_slots', 0),
            empty_slots=statistics.get('empty_slots', 0),
            occupancy_rate=statistics.get('occupancy_rate', 0.0),
            slots_details=slots_details,
            coordinates=coordinates,
            image_dimensions=image_dims,
            processing_time_ms=round(processing_time * 1000, 2)
        )
        
        logger.info(f"✅ Parking data saved: {document_id} for user {user_id}")
        
        # Prepare response
        response = {
            'success': True,
            'document_id': document_id,
            'total_slots': statistics.get('total_slots', 0),
            'total_cars_detected': len(vehicle_detections),
            'occupied_slots': statistics.get('occupied_slots', 0),
            'empty_slots': statistics.get('empty_slots', 0),
            'occupancy_rate': statistics.get('occupancy_rate', 0.0),
            'svg_code': svg_code,
            'slots_details': slots_details,
            'timestamp': datetime.utcnow().isoformat(),
            'processing_time_ms': round(processing_time * 1000, 2)
        }
        
        return jsonify(response), 201
        
    except Exception as e:
        logger.error(f"Error in updateRaw: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@parking_bp.route('/update', methods=['POST'])
@token_required
def update_processed():
    """
    Update MongoDB with pre-processed parking data (from edge device)
    
    POST /parking/update
    Headers:
        - Authorization: Bearer <token>
    Body (JSON):
        - camera_id: string
        - total_slots: number
        - occupied_slots: number
        - empty_slots: number
        - occupancy_rate: number
        - (optional) total_cars_detected, slots_details, coordinates, additional_data
    """
    try:
        # Get user ID from JWT
        user_id = jwt_handler.get_current_user_id()
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['camera_id', 'total_slots', 'occupied_slots', 'empty_slots', 'occupancy_rate']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            return jsonify({
                'error': f'Missing required fields: {", ".join(missing_fields)}'
            }), 400
        
        # Save to MongoDB
        document_id = ParkingData.create_from_edge_processing(
            user_id=user_id,
            camera_id=data['camera_id'],
            total_slots=int(data['total_slots']),
            occupied_slots=int(data['occupied_slots']),
            empty_slots=int(data['empty_slots']),
            occupancy_rate=float(data['occupancy_rate']),
            total_cars_detected=data.get('total_cars_detected'),
            slots_details=data.get('slots_details', []),
            coordinates=data.get('coordinates', []),
            additional_data=data.get('additional_data', {})
        )
        
        logger.info(f"✅ Edge-processed data saved: {document_id} for user {user_id}")
        
        return jsonify({
            'success': True,
            'document_id': document_id,
            'message': 'Parking data updated successfully',
            'timestamp': datetime.utcnow().isoformat()
        }), 201
        
    except Exception as e:
        logger.error(f"Error in update: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@parking_bp.route('/data/<user_id>', methods=['GET'])
@token_required
def get_parking_data(user_id):
    """
    Get parking data for a registered user
    
    GET /parking/data/<user_id>
    Headers:
        - Authorization: Bearer <token>
    Query Parameters:
        - camera_id (optional)
        - limit (optional, default 50)
        - skip (optional, default 0)
        - start_date (optional)
        - end_date (optional)
    """
    try:
        # Get user ID from JWT
        jwt_user_id = jwt_handler.get_current_user_id()
        
        # Verify user has access
        if user_id != jwt_user_id:
            return jsonify({'error': 'Unauthorized access to user data'}), 403
        
        # Parse query parameters
        camera_id = request.args.get('camera_id')
        limit = min(int(request.args.get('limit', 50)), 500)
        skip = int(request.args.get('skip', 0))
        
        # Date filtering
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if start_date:
            start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        if end_date:
            end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
        # Query database
        result = ParkingData.find_by_user(
            user_id=user_id,
            camera_id=camera_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            skip=skip
        )
        
        logger.info(f"📊 Retrieved {result['returned_count']} parking records for user {user_id}")
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'total_count': result['total_count'],
            'returned_count': result['returned_count'],
            'skip': skip,
            'limit': limit,
            'latest': result['latest'],
            'data': result['data']
        }), 200
        
    except Exception as e:
        logger.error(f"Error retrieving parking data: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@parking_bp.route('/detect', methods=['POST'])
def basic_detect():
    """
    Basic detection endpoint (no auth, no MongoDB storage)
    
    POST /parking/detect
    Body (multipart or JSON):
        - image: file or base64
        - coordinates: JSON array [[x1,y1,x2,y2], ...]
    """
    try:
        # Parse request
        if request.is_json:
            data = request.get_json()
            if 'image' not in data:
                return jsonify({'error': 'Missing image parameter'}), 400
            image = decode_image(data['image'])
            coordinates = data.get('coordinates')
        else:
            if 'image' not in request.files:
                return jsonify({'error': 'Missing image file'}), 400
            image_file = request.files['image']
            image_bytes = image_file.read()
            image = decode_image(image_bytes)
            coordinates = json.loads(request.form.get('coordinates', '[]'))
        
        # Validate coordinates
        validate_coordinates(coordinates)
        
        parking_rectangles = [tuple(coord) for coord in coordinates]
        
        # Get image dimensions
        image_dims = get_image_dimensions(image)
        
        # Initialize detection system
        system = ParkingDetectionSystem(parking_positions=parking_rectangles)
        
        # Process frame
        annotated_frame, statistics, processing_time = system.process_frame(image)
        
        # Get detailed results
        vehicle_detections = system.vehicle_detector.detect_vehicles(image)
        occupancy = system.parking_manager.detect_occupancy(vehicle_detections)
        
        # Generate slot details and SVG
        slots_details = generate_slot_details(parking_rectangles, occupancy)
        svg_code = generate_svg(
            parking_rectangles,
            occupancy,
            image_dims['width'],
            image_dims['height']
        )
        
        response = {
            'success': True,
            'total_slots': statistics.get('total_slots', 0),
            'total_cars_detected': len(vehicle_detections),
            'occupied_slots': statistics.get('occupied_slots', 0),
            'empty_slots': statistics.get('empty_slots', 0),
            'occupancy_rate': statistics.get('occupancy_rate', 0.0),
            'svg_code': svg_code,
            'slots_details': slots_details,
            'image_dimensions': image_dims,
            'processing_time_ms': round(processing_time * 1000, 2)
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error in basic detection: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500
