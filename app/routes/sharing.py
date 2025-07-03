# app/routes/sharing.py
from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
import os
from app import db
from app.models.file import File, FileShare
from app.models.user import User

sharing_bp = Blueprint('sharing', __name__)

@sharing_bp.route('/share', methods=['POST'])
@jwt_required()
def share_file():
    current_user_id = get_jwt_identity()
    
    data = request.get_json()
    if not data or 'file_id' not in data or 'username' not in data:
        return jsonify({'message': 'File ID and username are required'}), 400
    
    # Check if file exists and belongs to current user
    file_record = File.query.filter_by(
        id=data['file_id'],
        user_id=current_user_id
    ).first()
    
    if not file_record:
        return jsonify({'message': 'File not found'}), 404
    
    # Check if target user exists
    target_user = User.query.filter_by(username=data['username']).first()
    if not target_user:
        return jsonify({'message': 'User not found'}), 404
    
    # Check if already shared
    existing_share = FileShare.query.filter_by(
        file_id=data['file_id'],
        shared_with_user_id=target_user.id
    ).first()
    
    if existing_share:
        return jsonify({'message': 'File already shared with this user'}), 409
    
    # Create share record
    permission = data.get('permission', 'read')
    expires_days = data.get('expires_days', 30)
    
    share = FileShare(
        file_id=data['file_id'],
        shared_with_user_id=target_user.id,
        permission=permission,
        expires_at=datetime.utcnow() + timedelta(days=expires_days)
    )
    
    db.session.add(share)
    db.session.commit()
    
    return jsonify({
        'message': 'File shared successfully',
        'share': share.to_dict()
    }), 201

@sharing_bp.route('/shared-with-me', methods=['GET'])
@jwt_required()
def get_shared_files():
    current_user_id = get_jwt_identity()
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    # Get files shared with current user
    shares = db.session.query(FileShare, File, User).join(
        File, FileShare.file_id == File.id
    ).join(
        User, File.user_id == User.id
    ).filter(
        FileShare.shared_with_user_id == current_user_id,
        FileShare.expires_at > datetime.utcnow()
    ).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    shared_files = []
    for share, file, owner in shares.items:
        file_dict = file.to_dict()
        file_dict['owner'] = owner.username
        file_dict['permission'] = share.permission
        file_dict['shared_at'] = share.shared_at.isoformat()
        file_dict['expires_at'] = share.expires_at.isoformat()
        shared_files.append(file_dict)
    
    return jsonify({
        'shared_files': shared_files,
        'pagination': {
            'page': page,
            'pages': shares.pages,
            'per_page': per_page,
            'total': shares.total
        }
    }), 200

@sharing_bp.route('/my-shares', methods=['GET'])
@jwt_required()
def get_my_shares():
    current_user_id = get_jwt_identity()
    
    # Get files shared by current user
    shares = db.session.query(FileShare, File, User).join(
        File, FileShare.file_id == File.id
    ).join(
        User, FileShare.shared_with_user_id == User.id
    ).filter(
        File.user_id == current_user_id
    ).all()
    
    my_shares = []
    for share, file, shared_user in shares:
        share_dict = share.to_dict()
        share_dict['file'] = file.to_dict()
        share_dict['shared_with'] = shared_user.username
        my_shares.append(share_dict)
    
    return jsonify({
        'my_shares': my_shares
    }), 200

@sharing_bp.route('/download/<int:file_id>', methods=['GET'])
@jwt_required()
def download_shared_file(file_id):
    current_user_id = get_jwt_identity()
    
    # Check if file is shared with current user
    share = db.session.query(FileShare, File).join(
        File, FileShare.file_id == File.id
    ).filter(
        FileShare.file_id == file_id,
        FileShare.shared_with_user_id == current_user_id,
        FileShare.expires_at > datetime.utcnow()
    ).first()
    
    if not share:
        return jsonify({'message': 'File not found or access denied'}), 404
    
    file_share, file_record = share
    
    if not os.path.exists(file_record.file_path):
        return jsonify({'message': 'File not found on disk'}), 404
    
    return send_file(
        file_record.file_path,
        as_attachment=True,
        download_name=file_record.original_filename
    )

@sharing_bp.route('/revoke/<int:share_id>', methods=['DELETE'])
@jwt_required()
def revoke_share(share_id):
    current_user_id = get_jwt_identity()
    
    # Check if share exists and belongs to current user's file
    share = db.session.query(FileShare, File).join(
        File, FileShare.file_id == File.id
    ).filter(
        FileShare.id == share_id,
        File.user_id == current_user_id
    ).first()
    
    if not share:
        return jsonify({'message': 'Share not found'}), 404
    
    file_share, file_record = share
    
    db.session.delete(file_share)
    db.session.commit()
    
    return jsonify({'message': 'Share revoked successfully'}), 200