"""
Web UI API - Serves HTML interface and health check
"""

import logging
from flask import Blueprint, jsonify, render_template, send_from_directory
import os

logger = logging.getLogger(__name__)

# Create blueprint
web_bp = Blueprint('web', __name__)


@web_bp.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'parking-detection'
    })


@web_bp.route('/testing')
def testing():
    """Serve the API testing interface"""
    try:
        # Get the templates directory path
        templates_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates')
        return send_from_directory(templates_dir, 'testing.html')
    except Exception as e:
        logger.error(f"Error serving testing page: {e}")
        return jsonify({'error': 'Testing page not found'}), 404


@web_bp.route('/')
def index():
    """Serve the interactive web interface"""
    try:
        # Get the templates directory path
        templates_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates')
        return send_from_directory(templates_dir, 'index.html')
    except Exception as e:
        logger.error(f"Error serving index page: {e}")
        return jsonify({'error': 'Index page not found'}), 404
