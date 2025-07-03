# app/utils/file_utils.py
import os
import hashlib
import secrets
from werkzeug.utils import secure_filename
from flask import current_app
from cryptography.fernet import Fernet

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def generate_unique_filename(filename):
    """Generate unique filename to prevent conflicts"""
    secure_name = secure_filename(filename)
    name, ext = os.path.splitext(secure_name)
    unique_name = f"{name}_{secrets.token_hex(8)}{ext}"
    return unique_name

def calculate_file_hash(file_path):
    """Calculate SHA-256 hash of file"""
    hash_sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()

def encrypt_file(file_path, key=None):
    """Encrypt file using Fernet encryption"""
    if key is None:
        key = Fernet.generate_key()
    
    fernet = Fernet(key)
    
    with open(file_path, 'rb') as file:
        file_data = file.read()
    
    encrypted_data = fernet.encrypt(file_data)
    
    with open(file_path, 'wb') as file:
        file.write(encrypted_data)
    
    return key

def decrypt_file(file_path, key):
    """Decrypt file using Fernet encryption"""
    fernet = Fernet(key)
    
    with open(file_path, 'rb') as file:
        encrypted_data = file.read()
    
    decrypted_data = fernet.decrypt(encrypted_data)
    
    with open(file_path, 'wb') as file:
        file.write(decrypted_data)
    
    return True