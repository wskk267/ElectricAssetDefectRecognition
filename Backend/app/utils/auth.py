from datetime import datetime, timedelta
from flask import request, jsonify
import functools
from app.database import fetch_one

def verify_token(token, user_type='user'):
    """Verify token validity"""
    if not token:
        return None
    
    table = 'admin' if user_type == 'admin' else 'user'
    sql = f"SELECT * FROM {table} WHERE token = %s"
    result = fetch_one(sql, (token,))
    
    if not result:
        return None
    
    if result['update_time']:
        time_diff = datetime.now() - result['update_time']
        if time_diff > timedelta(days=3):
            return None
    
    return result

def require_auth(user_type='user'):
    """Decorator: Require user authentication"""
    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            token = request.headers.get('Authorization')
            if token and token.startswith('Bearer '):
                token = token[7:]
            
            user_info = verify_token(token, user_type)
            if not user_info:
                return jsonify({
                    'success': False,
                    'message': '认证失败，请重新登录'
                }), 401
            
            if user_info.get('isbannd', 0) == 1:
                return jsonify({
                    'success': False,
                    'message': '您的账户已被封禁，请联系管理员'
                }), 403
            
            return f(user_info, *args, **kwargs)
        return decorated_function
    return decorator
