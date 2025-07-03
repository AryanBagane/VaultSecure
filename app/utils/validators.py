# app/utils/validators.py
import re
from flask import request, jsonify

def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Password must be at least 8 characters with uppercase, lowercase, digit, and special char"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r'\d', password):
        return False, "Password must contain at least one digit"
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character"
    
    return True, "Password is valid"

def validate_json(*required_fields):
    """Decorator to validate JSON request data"""
    def decorator(f):
        def wrapper(*args, **kwargs):
            if not request.is_json:
                return jsonify({'message': 'Request must be JSON'}), 400
            
            data = request.get_json()
            if not data:
                return jsonify({'message': 'No JSON data provided'}), 400
            
            for field in required_fields:
                if field not in data or not data[field]:
                    return jsonify({'message': f'Missing required field: {field}'}), 400
            
            return f(*args, **kwargs)
        wrapper.__name__ = f.__name__
        return wrapper
    return decorator