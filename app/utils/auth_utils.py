# app/utils/auth_utils.py
from functools import wraps
from flask import jsonify, request
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from app.models.user import User

def token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            verify_jwt_in_request()
            current_user_id = get_jwt_identity()
            current_user = User.query.get(current_user_id)
            
            if not current_user or not current_user.is_active:
                return jsonify({'message': 'Invalid or inactive user'}), 401
            
            return f(current_user, *args, **kwargs)
        except Exception as e:
            return jsonify({'message': 'Token is invalid'}), 401
    
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            verify_jwt_in_request()
            current_user_id = get_jwt_identity()
            current_user = User.query.get(current_user_id)
            
            if not current_user or not current_user.is_active:
                return jsonify({'message': 'Invalid or inactive user'}), 401
            
            # Add admin check logic here if needed
            return f(current_user, *args, **kwargs)
        except Exception as e:
            return jsonify({'message': 'Token is invalid'}), 401
    
    return decorated_function