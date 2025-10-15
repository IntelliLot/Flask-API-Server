#!/usr/bin/env python3
"""
YOLOv8 Parking Detection - Modular Flask Application

A well-organized API structure with:
- Blueprints for different API routes (apis/)
- Models for database operations (models/)
- Middlewares for authentication (middlewares/)
- Utilities for reusable functions (utils/)
- Configuration management (config/)

Usage:
    python app.py
    
Then open: http://localhost:5001/
"""

import os
import sys
import logging
from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Enable CORS for React frontend
CORS(app)

# Configure Flask
app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))

# Initialize database
from config.database import db
db.connect()  # Connect to MongoDB on startup

# Initialize JWT
from auth.jwt_handler import jwt_handler
jwt_handler.init_app(app)

# Register blueprints
logger.info("Registering API blueprints...")

# Web UI blueprint (root routes)
from apis.web_api import web_bp
app.register_blueprint(web_bp)

# Authentication blueprint (/auth/*)
from apis.auth_api import auth_bp
app.register_blueprint(auth_bp)

# Parking API blueprint (/parking/*)
from apis.parking_api import parking_bp
app.register_blueprint(parking_bp)

logger.info("✅ All blueprints registered")


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return {
        'error': 'Endpoint not found',
        'message': 'The requested endpoint does not exist'
    }, 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal error: {error}")
    return {
        'error': 'Internal server error',
        'message': 'An unexpected error occurred'
    }, 500


def print_routes():
    """Print all registered routes"""
    logger.info("\n" + "="*70)
    logger.info("📡 Registered API Endpoints:")
    logger.info("="*70)
    
    routes = []
    for rule in app.url_map.iter_rules():
        if rule.endpoint != 'static':
            methods = ', '.join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))
            routes.append((rule.rule, methods, rule.endpoint))
    
    # Sort by URL
    routes.sort()
    
    # Group by category
    web_routes = [r for r in routes if r[2].startswith('web.')]
    auth_routes = [r for r in routes if r[2].startswith('auth.')]
    parking_routes = [r for r in routes if r[2].startswith('parking.')]
    
    if web_routes:
        logger.info("\n🌐 Web UI:")
        for route, methods, endpoint in web_routes:
            logger.info(f"   {methods:15} {route}")
    
    if auth_routes:
        logger.info("\n🔐 Authentication:")
        for route, methods, endpoint in auth_routes:
            logger.info(f"   {methods:15} {route}")
    
    if parking_routes:
        logger.info("\n🅿️  Parking Detection:")
        for route, methods, endpoint in parking_routes:
            logger.info(f"   {methods:15} {route}")
    
    logger.info("\n" + "="*70 + "\n")






if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='YOLOv8 Parking Detection App')
    parser.add_argument('--host', default=os.getenv('FLASK_HOST', '0.0.0.0'),
                       help='Host to bind to')
    parser.add_argument('--port', type=int, default=int(os.getenv('FLASK_PORT', 5001)),
                       help='Port to bind to')
    parser.add_argument('--debug', action='store_true',
                       default=os.getenv('FLASK_DEBUG', 'False').lower() == 'true',
                       help='Enable debug mode')
    
    args = parser.parse_args()
    
    # Print startup banner
    logger.info("\n" + "="*70)
    logger.info("🚀 Starting Parking Detection Application")
    logger.info("="*70)
    logger.info(f"Host: {args.host}")
    logger.info(f"Port: {args.port}")
    logger.info(f"Debug: {args.debug}")
    logger.info(f"MongoDB: {'✅ Connected' if db.is_connected() else '❌ Not Connected'}")
    logger.info(f"JWT Auth: {'✅ Enabled' if jwt_handler.is_available() else '❌ Disabled'}")
    logger.info("")
    logger.info(f"🌐 Open in browser: http://localhost:{args.port}/")
    logger.info("")
    
    # Print all routes
    print_routes()
    
    # Run application
    app.run(host=args.host, port=args.port, debug=args.debug)

