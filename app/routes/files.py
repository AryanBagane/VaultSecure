# app/routes/files.py
from flask import Blueprint, request, jsonify, send_file, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
import os
from app import db
from app.models.file import File
from app.models.user import User
from app.utils.file_utils import allowed_file, generate_unique_filename, calculate_file_hash

files_bp = Blueprint('files', __name__)

@files_bp.route('/upload', methods=['POST'])
@jwt_required()
def upload_file():
    current_user_id = get_jwt_identity()
    
    if 'file' not in request.files:
        return jsonify({'message': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'message': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'message': 'File type not allowed'}), 400
    
    try:
        # Generate unique filename
        unique_filename = generate_unique_filename(file.filename)
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
        
        # Save file
        file.save(file_path)
        
        # Calculate file hash
        file_hash = calculate_file_hash(file_path)
        
        # Check for duplicate files
        existing_file = File.query.filter_by(
            file_hash=file_hash,
            user_id=current_user_id
        ).first()
        
        if existing_file:
            os.remove(file_path)  # Remove duplicate
            return jsonify({
                'message': 'File already exists',
                'file': existing_file.to_dict()
            }), 409
        
        # Create file record
        file_record = File(
            filename=unique_filename,
            original_filename=file.filename,
            file_path=file_path,
            file_size=os.path.getsize(file_path),
            content_type=file.content_type,
            file_hash=file_hash,
            user_id=current_user_id
        )
        
        db.session.add(file_record)
        db.session.commit()
        
        return jsonify({
            'message': 'File uploaded successfully',
            'file': file_record.to_dict()
        }), 201
        
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        return jsonify({'message': f'Upload failed: {str(e)}'}), 500

@files_bp.route('/list', methods=['GET'])
@jwt_required()
def list_files():
    current_user_id = get_jwt_identity()
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    files = File.query.filter_by(user_id=current_user_id).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'files': [file.to_dict() for file in files.items],
        'pagination': {
            'page': page,
            'pages': files.pages,
            'per_page': per_page,
            'total': files.total
        }
    }), 200

@files_bp.route('/<int:file_id>', methods=['GET'])
@jwt_required()
def get_file(file_id):
    current_user_id = get_jwt_identity()
    
    file_record = File.query.filter_by(
        id=file_id,
        user_id=current_user_id
    ).first()
    
    if not file_record:
        return jsonify({'message': 'File not found'}), 404
    
    return jsonify({
        'file': file_record.to_dict()
    }), 200

@files_bp.route('/<int:file_id>/download', methods=['GET'])
@jwt_required()
def download_file(file_id):
    current_user_id = get_jwt_identity()
    
    file_record = File.query.filter_by(
        id=file_id,
        user_id=current_user_id
    ).first()
    
    if not file_record:
        return jsonify({'message': 'File not found'}), 404
    
    if not os.path.exists(file_record.file_path):
        return jsonify({'message': 'File not found on disk'}), 404
    
    return send_file(
        file_record.file_path,
        as_attachment=True,
        download_name=file_record.original_filename
    )

@files_bp.route('/<int:file_id>', methods=['DELETE'])
@jwt_required()
def delete_file(file_id):
    current_user_id = get_jwt_identity()
    
    file_record = File.query.filter_by(
        id=file_id,
        user_id=current_user_id
    ).first()
    
    if not file_record:
        return jsonify({'message': 'File not found'}), 404
    
    try:
        # Delete file from disk
        file_record.delete_file()
        
        # Delete record from database
        db.session.delete(file_record)
        db.session.commit()
        
        return jsonify({'message': 'File deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Delete failed: {str(e)}'}), 500

@files_bp.route('/<int:file_id>/rename', methods=['PUT'])
@jwt_required()
def rename_file(file_id):
    current_user_id = get_jwt_identity()
    
    data = request.get_json()
    if not data or 'new_name' not in data:
        return jsonify({'message': 'New name is required'}), 400
    
    file_record = File.query.filter_by(
        id=file_id,
        user_id=current_user_id
    ).first()
    
    if not file_record:
        return jsonify({'message': 'File not found'}), 404
    
    # Update the original filename (display name)
    file_record.original_filename = secure_filename(data['new_name'])
    
    db.session.commit()
    
    return jsonify({
        'message': 'File renamed successfully',
        'file': file_record.to_dict()
    }), 200