"""
Authentication Middleware - JWT verification decorators
"""

from functools import wraps
from flask import jsonify

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
