"""
JWT Token Handler for authentication
"""

import os
from datetime import timedelta
from flask import Flask

try:
    from flask_jwt_extended import JWTManager, create_access_token, get_jwt_identity, get_jwt
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False
    print("⚠️  Warning: Flask-JWT-Extended not installed. JWT features disabled.")


class JWTHandler:
    """JWT Token Management"""

    def __init__(self, app: Flask = None):
        """Initialize JWT with Flask app"""
        self.jwt_manager = None
        if app:
            self.init_app(app)

    def init_app(self, app: Flask):
        """Initialize JWT with Flask app configuration"""
        if not JWT_AVAILABLE:
            return

        # Configure JWT
        app.config['JWT_SECRET_KEY'] = os.getenv(
            'JWT_SECRET_KEY',
            'dev-secret-key-change-in-production'
        )
        app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(
            seconds=int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 3600))
        )

        self.jwt_manager = JWTManager(app)

    @staticmethod
    def create_token(user_id: str, additional_claims: dict = None) -> str:
        """
        Create JWT access token

        Args:
            user_id: User identifier
            additional_claims: Additional data to include in token

        Returns:
            JWT token string
        """
        if not JWT_AVAILABLE:
            raise Exception("JWT not available")

        return create_access_token(
            identity=user_id,
            additional_claims=additional_claims or {}
        )

    @staticmethod
    def get_current_user_id() -> str:
        """
        Get current user ID from JWT token or request context (for API key auth)
        """
        # First try to get from request context (set by API key middleware)
        from flask import request, has_request_context

        if has_request_context() and hasattr(request, 'current_user_id'):
            return request.current_user_id

        # Otherwise get from JWT token
        if not JWT_AVAILABLE:
            return None
        return get_jwt_identity()

    @staticmethod
    def get_jwt_claims() -> dict:
        """Get JWT claims/payload"""
        if not JWT_AVAILABLE:
            return {}
        return get_jwt()

    @staticmethod
    def is_available() -> bool:
        """Check if JWT is available"""
        return JWT_AVAILABLE


# Global JWT handler instance
jwt_handler = JWTHandler()
