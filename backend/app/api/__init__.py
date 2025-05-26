"""
API package initialization.

This module initializes the API package and exposes routes and endpoints.
"""
from flask import Blueprint

# Create a Blueprint for the API
api_bp = Blueprint('api', __name__, url_prefix='/api')

# Import routes to register them with the blueprint
# These imports are placed here to avoid circular imports
# from .routes import *

# Additional API configuration can be added here
