"""
Parking API - Detection and data management endpoints
"""

import json
import logging
from datetime import datetime
from flask import Blueprint, request, jsonify
from middlewares.auth_middleware import token_required, api_key_or_token_required
from auth.jwt_handler import jwt_handler
from models.parking_data import ParkingData
from config.database import db
from utils.image_utils import decode_image, validate_coordinates, get_image_dimensions
from utils.svg_generator import generate_svg, generate_slot_details
from utils.gcs_storage import gcs_storage
from parking_detection import ParkingDetectionSystem

logger = logging.getLogger(__name__)

# Create blueprint
parking_bp = Blueprint('parking', __name__, url_prefix='/parking')


@parking_bp.route('/updateRaw', methods=['POST'])
@api_key_or_token_required
def update_raw():
    """
    Process raw image frame with coordinates and save to MongoDB + GCS

    POST /parking/updateRaw
    Headers:
        - Authorization: Bearer <token_or_api_key>
    Body (multipart or JSON):
        - image: file or base64
        - coordinates: JSON array [[x1,y1,x2,y2], ...]
        - camera_id: string (used as node_id)
        - node_id: string (optional, defaults to camera_id)
    """
    try:
        # Get user ID from JWT or API key
        user_id = jwt_handler.get_current_user_id()

        # Variables to store image data
        image = None
        image_bytes = None

        # Parse request
        if request.is_json:
            data = request.get_json()

            if 'image' not in data:
                return jsonify({'error': 'Missing image parameter'}), 400

            image = decode_image(data['image'])
            coordinates = data.get('coordinates')
            camera_id = data.get('camera_id')
            # Use node_id or fall back to camera_id
            node_id = data.get('node_id', camera_id)

        else:
            # Multipart form data
            if 'image' not in request.files:
                return jsonify({'error': 'Missing image file'}), 400

            image_file = request.files['image']
            image_bytes = image_file.read()
            image = decode_image(image_bytes)

            coordinates = json.loads(request.form.get('coordinates', '[]'))
            camera_id = request.form.get('camera_id')
            # Use node_id or fall back to camera_id
            node_id = request.form.get('node_id', camera_id)

        # Validate inputs
        if not camera_id:
            return jsonify({'error': 'camera_id is required'}), 400

        if not node_id:
            node_id = camera_id  # Ensure node_id is set

        validate_coordinates(coordinates)

        parking_rectangles = [tuple(coord) for coord in coordinates]
        logger.info(
            f"Processing raw image for user {user_id}, camera {camera_id}, node {node_id}")

        # Current timestamp for all operations
        current_timestamp = datetime.utcnow()

        # Get image dimensions
        image_dims = get_image_dimensions(image)

        # Upload raw image to Google Cloud Storage
        gcs_raw_path = None
        gcs_raw_url = None
        if gcs_storage.enabled:
            try:
                if image_bytes:
                    # Upload bytes directly
                    result = gcs_storage.upload_image_bytes(
                        image_bytes=image_bytes,
                        user_id=user_id,
                        node_id=node_id,
                        timestamp=current_timestamp,
                        image_type="raw"
                    )
                else:
                    # Upload OpenCV image
                    result = gcs_storage.upload_image(
                        image=image,
                        user_id=user_id,
                        node_id=node_id,
                        timestamp=current_timestamp,
                        image_type="raw"
                    )

                if result:
                    gcs_raw_path, gcs_raw_url = result
                    logger.info(f"✅ Raw image uploaded to GCS: {gcs_raw_path}")
            except Exception as e:
                logger.error(f"⚠️ Failed to upload raw image to GCS: {e}")

        # Initialize detection system
        system = ParkingDetectionSystem(parking_positions=parking_rectangles)

        # Process frame
        annotated_frame, statistics, processing_time = system.process_frame(
            image)

        # Upload annotated image to GCS
        gcs_annotated_path = None
        gcs_annotated_url = None
        if gcs_storage.enabled and annotated_frame is not None:
            try:
                result = gcs_storage.upload_image(
                    image=annotated_frame,
                    user_id=user_id,
                    node_id=node_id,
                    timestamp=current_timestamp,
                    image_type="annotated"
                )
                if result:
                    gcs_annotated_path, gcs_annotated_url = result
                    logger.info(
                        f"✅ Annotated image uploaded to GCS: {gcs_annotated_path}")
            except Exception as e:
                logger.error(
                    f"⚠️ Failed to upload annotated image to GCS: {e}")

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

        # Save to MongoDB with GCS paths
        document_id = ParkingData.create_from_raw_processing(
            user_id=user_id,
            camera_id=camera_id,
            node_id=node_id,
            total_slots=statistics.get('total_slots', 0),
            total_cars_detected=len(vehicle_detections),
            occupied_slots=statistics.get('occupied_slots', 0),
            empty_slots=statistics.get('empty_slots', 0),
            occupancy_rate=statistics.get('occupancy_rate', 0.0),
            slots_details=slots_details,
            coordinates=coordinates,
            image_dimensions=image_dims,
            processing_time_ms=round(processing_time * 1000, 2),
            gcs_raw_image_path=gcs_raw_path,
            gcs_raw_image_url=gcs_raw_url,
            gcs_annotated_image_path=gcs_annotated_path,
            gcs_annotated_image_url=gcs_annotated_url,
            timestamp=current_timestamp
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
            'timestamp': current_timestamp.isoformat(),
            'processing_time_ms': round(processing_time * 1000, 2),
            'gcs_storage': {
                'enabled': gcs_storage.enabled,
                'raw_image': {
                    'path': gcs_raw_path,
                    'url': gcs_raw_url
                } if gcs_raw_path else None,
                'annotated_image': {
                    'path': gcs_annotated_path,
                    'url': gcs_annotated_url
                } if gcs_annotated_path else None
            }
        }

        return jsonify(response), 201

    except Exception as e:
        logger.error(f"Error in updateRaw: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@parking_bp.route('/update', methods=['POST'])
@api_key_or_token_required
def update_processed():
    """
    Update MongoDB with pre-processed parking data (from edge device)

    POST /parking/update
    Headers:
        - Authorization: Bearer <token_or_api_key>
    Body (JSON):
        - camera_id: string
        - total_slots: number
        - occupied_slots: number
        - empty_slots: number
        - occupancy_rate: number
        - (optional) total_cars_detected, slots_details, coordinates, additional_data
    """
    try:
        # Get user ID from JWT or API key
        user_id = jwt_handler.get_current_user_id()

        data = request.get_json()

        # Validate required fields
        required_fields = ['camera_id', 'total_slots',
                           'occupied_slots', 'empty_slots', 'occupancy_rate']
        missing_fields = [
            field for field in required_fields if field not in data]

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

        logger.info(
            f"✅ Edge-processed data saved: {document_id} for user {user_id}")

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
            start_date = datetime.fromisoformat(
                start_date.replace('Z', '+00:00'))
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

        logger.info(
            f"📊 Retrieved {result['returned_count']} parking records for user {user_id}")

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


@parking_bp.route('/images', methods=['GET'])
@token_required
def get_uploaded_images():
    """
    Get uploaded images with pagination

    GET /parking/images?page=1&limit=10&camera_id=cam1
    Headers:
        - Authorization: Bearer <token>
    Query Parameters:
        - page: Page number (default: 1)
        - limit: Items per page (default: 10, max: 50)
        - camera_id: Filter by camera ID (optional)
        - node_id: Filter by node ID (optional)
        - source: Filter by source (raw_processing or edge_processing) (optional)
    """
    try:
        user_id = jwt_handler.get_current_user_id()

        # Parse query parameters
        page = max(1, int(request.args.get('page', 1)))
        limit = min(50, max(1, int(request.args.get('limit', 10))))
        camera_id = request.args.get('camera_id')
        node_id = request.args.get('node_id')
        source = request.args.get('source')

        # Build query
        query = {'user_id': user_id}

        # Only get records with GCS images
        query['$or'] = [
            {'gcs_storage.raw_image.url': {'$exists': True, '$ne': None}},
            {'gcs_storage.annotated_image.url': {'$exists': True, '$ne': None}}
        ]

        if camera_id:
            query['camera_id'] = camera_id
        if node_id:
            query['node_id'] = node_id
        if source:
            query['source'] = source

        # Get total count
        total_count = db.parking_data.count_documents(query)

        # Calculate pagination
        skip = (page - 1) * limit
        total_pages = (total_count + limit - 1) // limit

        # Fetch data
        cursor = db.parking_data.find(query).sort(
            'timestamp', -1).skip(skip).limit(limit)

        images = []
        for doc in cursor:
            gcs_storage_data = doc.get('gcs_storage', {})
            raw_image = gcs_storage_data.get(
                'raw_image', {}) if gcs_storage_data else {}
            annotated_image = gcs_storage_data.get(
                'annotated_image', {}) if gcs_storage_data else {}

            images.append({
                'id': str(doc['_id']),
                'timestamp': doc['timestamp'].isoformat(),
                'camera_id': doc.get('camera_id'),
                'node_id': doc.get('node_id'),
                'source': doc.get('source', 'unknown'),
                'total_slots': doc.get('total_slots'),
                'occupied_slots': doc.get('occupied_slots'),
                'empty_slots': doc.get('empty_slots'),
                'occupancy_rate': doc.get('occupancy_rate'),
                'total_cars_detected': doc.get('total_cars_detected'),
                'processing_time_ms': doc.get('processing_time_ms'),
                'raw_image_url': raw_image.get('url') if raw_image else None,
                'annotated_image_url': annotated_image.get('url') if annotated_image else None,
                'image_dimensions': doc.get('image_dimensions')
            })

        return jsonify({
            'success': True,
            'images': images,
            'pagination': {
                'page': page,
                'limit': limit,
                'total_count': total_count,
                'total_pages': total_pages,
                'has_next': page < total_pages,
                'has_prev': page > 1
            }
        })

    except Exception as e:
        logger.error(f"Error fetching images: {e}", exc_info=True)
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
        annotated_frame, statistics, processing_time = system.process_frame(
            image)

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
