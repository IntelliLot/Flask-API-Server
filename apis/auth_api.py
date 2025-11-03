"""
Authentication API - Registration and Login endpoints
"""

import logging
import secrets
from flask import Blueprint, request, jsonify
from models.user import User
from auth.password import hash_password, verify_password
from auth.jwt_handler import jwt_handler
from middlewares.auth_middleware import token_required

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
        required_fields = ['username', 'password',
                           'organization_name', 'location', 'size']
        missing_fields = [
            field for field in required_fields if field not in data]

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

        logger.info(
            f"✅ New user registered: {username} (ID: {user['user_id']})")

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


@auth_bp.route('/profile', methods=['GET'])
@token_required
def get_profile():
    """
    Get current user profile

    GET /auth/profile
    Headers:
        Authorization: Bearer <token>
    """
    try:
        user_id = jwt_handler.get_current_user_id()
        user = User.find_by_user_id(user_id)

        if not user:
            return jsonify({'error': 'User not found'}), 404

        # Convert ObjectId to string if present
        if '_id' in user:
            user['_id'] = str(user['_id'])

        return jsonify(user), 200

    except Exception as e:
        logger.error(f"Profile error: {e}", exc_info=True)
        return jsonify({'error': 'Failed to load profile'}), 500


@auth_bp.route('/credentials', methods=['GET'])
@token_required
def get_credentials():
    """
    Get all API credentials for current user

    GET /auth/credentials
    Headers:
        Authorization: Bearer <token>
    """
    try:
        user_id = jwt_handler.get_current_user_id()
        credentials = User.get_user_credentials(user_id)

        # Convert ObjectId to string for each credential
        for cred in credentials:
            if '_id' in cred:
                cred['_id'] = str(cred['_id'])

        return jsonify(credentials), 200

    except Exception as e:
        logger.error(f"Get credentials error: {e}", exc_info=True)
        return jsonify({'error': 'Failed to load credentials'}), 500


@auth_bp.route('/credentials/generate', methods=['POST'])
@token_required
def generate_credential():
    """
    Generate a new API credential

    POST /auth/credentials/generate
    Headers:
        Authorization: Bearer <token>
    Body:
        - name (required): Name/description for the credential
    """
    try:
        user_id = jwt_handler.get_current_user_id()
        data = request.get_json()

        if not data or 'name' not in data:
            return jsonify({'error': 'Name is required'}), 400

        name = data['name'].strip()
        if not name:
            return jsonify({'error': 'Name cannot be empty'}), 400

        # Generate secure API key
        api_key = secrets.token_urlsafe(48)

        # Create credential
        credential = User.create_api_credential(
            user_id=user_id,
            name=name,
            api_key=api_key
        )

        # Convert ObjectId to string if present
        if '_id' in credential:
            credential['_id'] = str(credential['_id'])

        logger.info(f"✅ API credential generated for user {user_id}: {name}")

        return jsonify({
            'success': True,
            'credential': credential
        }), 201

    except Exception as e:
        logger.error(f"Generate credential error: {e}", exc_info=True)
        return jsonify({'error': 'Failed to generate credential'}), 500


@auth_bp.route('/credentials/<credential_id>/revoke', methods=['POST'])
@token_required
def revoke_credential(credential_id):
    """
    Revoke an API credential

    POST /auth/credentials/<credential_id>/revoke
    Headers:
        Authorization: Bearer <token>
    """
    try:
        user_id = jwt_handler.get_current_user_id()

        success = User.revoke_credential(user_id, credential_id)

        if success:
            logger.info(f"API credential revoked: {credential_id}")
            return jsonify({'success': True, 'message': 'Credential revoked'}), 200
        else:
            return jsonify({'error': 'Credential not found'}), 404

    except Exception as e:
        logger.error(f"Revoke credential error: {e}", exc_info=True)
        return jsonify({'error': 'Failed to revoke credential'}), 500


@auth_bp.route('/credentials/<credential_id>/activate', methods=['POST'])
@token_required
def activate_credential(credential_id):
    """
    Activate an API credential

    POST /auth/credentials/<credential_id>/activate
    Headers:
        Authorization: Bearer <token>
    """
    try:
        user_id = jwt_handler.get_current_user_id()

        success = User.activate_credential(user_id, credential_id)

        if success:
            logger.info(f"API credential activated: {credential_id}")
            return jsonify({'success': True, 'message': 'Credential activated'}), 200
        else:
            return jsonify({'error': 'Credential not found'}), 404

    except Exception as e:
        logger.error(f"Activate credential error: {e}", exc_info=True)
        return jsonify({'error': 'Failed to activate credential'}), 500


@auth_bp.route('/credentials/<credential_id>', methods=['DELETE'])
@token_required
def delete_credential(credential_id):
    """
    Delete an API credential

    DELETE /auth/credentials/<credential_id>
    Headers:
        Authorization: Bearer <token>
    """
    try:
        user_id = jwt_handler.get_current_user_id()

        success = User.delete_credential(user_id, credential_id)

        if success:
            logger.info(f"API credential deleted: {credential_id}")
            return jsonify({'success': True, 'message': 'Credential deleted'}), 200
        else:
            return jsonify({'error': 'Credential not found'}), 404

    except Exception as e:
        logger.error(f"Delete credential error: {e}", exc_info=True)
        return jsonify({'error': 'Failed to delete credential'}), 500
