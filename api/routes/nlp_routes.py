"""
API routes for the Natural Language Processing (NLP) model management.
These routes allow the frontend to interact with the NLP agent for model configuration.
"""

from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
import sys
import logging
import traceback

# Set up logging
logger = logging.getLogger(__name__)

# Create a blueprint for NLP routes
nlp_routes = Blueprint('nlp_routes', __name__)

# Try to import the agents module
try:
    from agents import get_agent
except ImportError:
    logger.error("Failed to import get_agent from agents")
    get_agent = None

@nlp_routes.route('/api/natural_language/model_info', methods=['GET'])
@cross_origin()
def get_model_info():
    """Get information about the current NLP model configuration."""
    try:
        # Get the natural language agent
        nlp_agent = get_agent('natural_language')
        if not nlp_agent:
            return jsonify({
                'status': 'error',
                'message': 'Natural language agent not found'
            }), 404
            
        # Get model info from the agent
        model_info = nlp_agent.get_model_info()
        
        # Return the model info
        return jsonify({
            'status': 'success',
            'data': model_info
        })
    except Exception as e:
        logger.error(f"Error getting model info: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'status': 'error',
            'message': f'Error getting model info: {str(e)}'
        }), 500

@nlp_routes.route('/api/natural_language/set_provider', methods=['POST'])
@cross_origin()
def set_model_provider():
    """Change the model provider."""
    try:
        # Get the request data
        data = request.json
        if not data or 'provider' not in data:
            return jsonify({
                'status': 'error',
                'message': 'No provider specified'
            }), 400
            
        provider = data['provider']
        
        # Get the natural language agent
        nlp_agent = get_agent('natural_language')
        if not nlp_agent:
            return jsonify({
                'status': 'error',
                'message': 'Natural language agent not found'
            }), 404
            
        # Set the model provider
        success = nlp_agent.set_model_provider(provider)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': f'Model provider changed to {provider}',
                'provider': provider
            })
        else:
            return jsonify({
                'status': 'error',
                'message': f'Failed to change model provider to {provider}'
            }), 400
    except Exception as e:
        logger.error(f"Error setting model provider: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'status': 'error',
            'message': f'Error setting model provider: {str(e)}'
        }), 500

@nlp_routes.route('/api/natural_language/set_model', methods=['POST'])
@cross_origin()
def set_model():
    """Change the specific model for the current provider."""
    try:
        # Get the request data
        data = request.json
        if not data or 'model_name' not in data:
            return jsonify({
                'status': 'error',
                'message': 'No model name specified'
            }), 400
            
        model_name = data['model_name']
        
        # Get the natural language agent
        nlp_agent = get_agent('natural_language')
        if not nlp_agent:
            return jsonify({
                'status': 'error',
                'message': 'Natural language agent not found'
            }), 404
            
        # Set the model
        success = nlp_agent.set_model(model_name)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': f'Model changed to {model_name}',
                'model': model_name
            })
        else:
            return jsonify({
                'status': 'error',
                'message': f'Failed to change model to {model_name}'
            }), 400
    except Exception as e:
        logger.error(f"Error setting model: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'status': 'error',
            'message': f'Error setting model: {str(e)}'
        }), 500

@nlp_routes.route('/api/natural_language/health_check', methods=['GET'])
@cross_origin()
def health_check():
    """Perform a health check on the NLP agent."""
    try:
        # Get the natural language agent
        nlp_agent = get_agent('natural_language')
        if not nlp_agent:
            return jsonify({
                'status': 'error',
                'message': 'Natural language agent not found'
            }), 404
            
        # Get health status
        health_status = nlp_agent.health_check()
        
        return jsonify({
            'status': 'success',
            'data': health_status
        })
    except Exception as e:
        logger.error(f"Error checking NLP health: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'status': 'error',
            'message': f'Error checking NLP health: {str(e)}'
        }), 500 