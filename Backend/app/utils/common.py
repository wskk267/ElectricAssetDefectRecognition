import secrets
import os

def generate_token():
    """Generate random token"""
    return secrets.token_hex(64)

def allowed_file(filename):
    """Check if file extension is allowed"""
    allowed_extensions = {'png', 'jpg', 'jpeg', 'bmp', 'mp4', 'avi', 'mov', 'mkv', 'wmv'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def is_video_file(filename):
    """Check if file is a video"""
    video_extensions = {'mp4', 'avi', 'mov', 'mkv', 'wmv'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in video_extensions
