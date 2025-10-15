"""
Authentication API - Registration and Login endpoints
"""

import logging
from flask import Blueprint, request, jsonify
from models.user import User
from auth.password import hash_password, verify_password
from auth.jwt_handler import jwt_handler

logger = logging.getLogger(__name__)

# Create blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Register a new parking owner account
    
    POST /auth/register
    Body:
        - username (required)
        - password (required)
        - organization_name (required)
        - location (required)
        - size (required)
        - verification (optional)
        - details (optional)
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['username', 'password', 'organization_name', 'location', 'size']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            return jsonify({
                'error': f'Missing required fields: {", ".join(missing_fields)}'
            }), 400
        
        username = data['username'].strip()
        password = data['password']
        
        # Validate username and password
        if len(username) < 3:
            return jsonify({'error': 'Username must be at least 3 characters'}), 400
        
        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400
        
        # Check if user already exists
        if User.username_exists(username):
            return jsonify({'error': 'Username already exists'}), 409
        
        # Hash password
        hashed_password = hash_password(password)
        
        # Create user
        user = User.create(
            username=username,
            hashed_password=hashed_password,
            organization_name=data['organization_name'],
            location=data['location'],
            size=int(data['size']),
            verification=data.get('verification', 'pending'),
            details=data.get('details', {})
        )
        
        logger.info(f"✅ New user registered: {username} (ID: {user['user_id']})")
        
        return jsonify({
            'success': True,
            'message': 'Registration successful',
            'user_id': user['user_id'],
            'username': user['username'],
            'organization_name': user['organization_name']
        }), 201
        
    except Exception as e:
        logger.error(f"Registration error: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Registration failed',
            'details': str(e)
        }), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Login to parking owner account
    
    POST /auth/login
    Body:
        - username (required)
        - password (required)
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        if 'username' not in data or 'password' not in data:
            return jsonify({'error': 'Username and password required'}), 400
        
        username = data['username'].strip()
        password = data['password']
        
        # Find user
        user = User.find_by_username(username)
        if not user:
            return jsonify({'error': 'Invalid username or password'}), 401
        
        # Verify password
        if not verify_password(password, user['password']):
            return jsonify({'error': 'Invalid username or password'}), 401
        
        # Check account status
        if user.get('status') != 'active':
            return jsonify({'error': 'Account is not active'}), 403
        
        # Generate JWT token
        access_token = jwt_handler.create_token(
            user_id=user['user_id'],
            additional_claims={
                'username': username,
                'organization': user.get('organization_name')
            }
        )
        
        # Update last login
        User.update_last_login(user['user_id'])
        
        logger.info(f"✅ User logged in: {username}")
        
        return jsonify({
            'success': True,
            'access_token': access_token,
            'user_id': user['user_id'],
            'username': username,
            'organization_name': user.get('organization_name'),
            'expires_in': 3600  # Should come from config
        }), 200
        
    except Exception as e:
        logger.error(f"Login error: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Login failed',
            'details': str(e)
        }), 500
