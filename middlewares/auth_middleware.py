"""
Authentication Middleware - JWT verification decorators
"""

from functools import wraps
from flask import jsonify, request

try:
    from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False


def token_required(f):
    """
    Decorator to require valid JWT token for endpoint access

    Usage:
        @app.route('/protected')
        @token_required
        def protected_route():
            user_id = get_jwt_identity()
            return {'user_id': user_id}
    """
    if not JWT_AVAILABLE:
        # If JWT not available, create a passthrough decorator
        @wraps(f)
        def decorated_function(*args, **kwargs):
            return jsonify({'error': 'Authentication service not available'}), 503
        return decorated_function

    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        return f(*args, **kwargs)

    return decorated_function


def api_key_or_token_required(f):
    """
    Decorator that accepts either JWT token or API key
    Checks Authorization header for both Bearer token and API key

    Usage:
        @app.route('/parking/update')
        @api_key_or_token_required
        def update_parking():
            # Access works with either JWT or API key
            return {'status': 'success'}
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from models.user import User
        from auth.jwt_handler import jwt_handler

        auth_header = request.headers.get('Authorization', '')

        # Try JWT token first
        if auth_header.startswith('Bearer '):
            try:
                if JWT_AVAILABLE:
                    verify_jwt_in_request()
                    # JWT is valid, proceed
                    return f(*args, **kwargs)
            except:
                pass  # JWT verification failed, try API key

        # Try API key
        api_key = None
        if auth_header.startswith('Bearer '):
            api_key = auth_header.replace('Bearer ', '').strip()
        elif auth_header.startswith('ApiKey '):
            api_key = auth_header.replace('ApiKey ', '').strip()

        if api_key:
            user = User.find_by_api_key(api_key)
            if user:
                # API key is valid, inject user_id into request context
                # so that jwt_handler.get_current_user_id() works
                request.current_user_id = user['user_id']
                return f(*args, **kwargs)

        # Neither JWT nor API key worked
        return jsonify({
            'error': 'Authentication required',
            'message': 'Provide a valid JWT token or API key in Authorization header'
        }), 401

    return decorated_function


def optional_token(f):
    """
    Decorator for optional JWT token
    Endpoint works with or without token
    """
    if not JWT_AVAILABLE:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            return f(*args, **kwargs)
        return decorated_function

    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            verify_jwt_in_request(optional=True)
        except:
            pass
        return f(*args, **kwargs)

    return decorated_function


def admin_required(f):
    """
    Decorator to require admin privileges
    Checks for 'is_admin' claim in JWT
    """
    if not JWT_AVAILABLE:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            return jsonify({'error': 'Authentication service not available'}), 503
        return decorated_function

    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        from flask_jwt_extended import get_jwt
        claims = get_jwt()

        if not claims.get('is_admin', False):
            return jsonify({'error': 'Admin privileges required'}), 403

        return f(*args, **kwargs)

    return decorated_function
