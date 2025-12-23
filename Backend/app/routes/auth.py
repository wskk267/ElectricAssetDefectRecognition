from flask import Blueprint, request, jsonify
from datetime import datetime
import hashlib
from app.database import fetch_one, execute_sql
from app.utils.common import generate_token
from app.utils.auth import require_auth
from app.services.auth_service import log_admin_action
import logging

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    """User login"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': '请求数据格式错误'}), 400
        
        username = data.get('username')
        password_hash = data.get('password')
        user_type = data.get('user_type', 'user') 
        
        if not username or not password_hash:
            return jsonify({'success': False, 'message': '用户名和密码不能为空'}), 400
        
        table = 'admin' if user_type == 'admin' else 'user'
        sql = f"SELECT * FROM {table} WHERE username = %s AND pw = %s"
        user = fetch_one(sql, (username, password_hash))
        
        if not user:
            return jsonify({'success': False, 'message': '用户名或密码错误'}), 401
        
        new_token = generate_token()
        update_sql = f"UPDATE {table} SET token = %s, update_time = %s WHERE id = %s"
        execute_sql(update_sql, (new_token, datetime.now(), user['id']))
        
        response_data = {
            'success': True,
            'message': '登录成功',
            'token': new_token,
            'user_id': user['id'],
            'username': user['username'],
            'user_type': user_type
        }
        
        if user_type == 'user':
            response_data.update({
                'imagelimit': user['imagelimit'],
                'batchlimit': user['batchlimit'],
                'realtimePermission': user['realtimePermission'],
                'isbannd': user['isbannd']
            })
        
        logging.info(f"User login success: {username} ({user_type})")
        return jsonify(response_data)
        
    except Exception as e:
        logging.error(f"Login failed: {str(e)}")
        return jsonify({'success': False, 'message': f'登录失败: {str(e)}'}), 500

@auth_bp.route('/register', methods=['POST'])
def register():
    """User register"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': '请求数据格式错误'}), 400
        
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'success': False, 'message': '用户名和密码不能为空'}), 400
        
        if len(username) < 3 or len(username) > 50:
            return jsonify({'success': False, 'message': '用户名长度必须在3-50个字符之间'}), 400
        
        if len(password) < 6:
            return jsonify({'success': False, 'message': '密码长度不能少于6个字符'}), 400
        
        existing_user = fetch_one("SELECT id FROM user WHERE username = %s", (username,))
        if existing_user:
            return jsonify({'success': False, 'message': '用户名已存在'}), 400
        
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        sql = """
        INSERT INTO user (username, pw, imagelimit, batchlimit, realtimePermission, isbannd)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        result = execute_sql(sql, (username, password_hash, 10, 5, 0, 0))
        
        if result > 0:
            logging.info(f"New user registered: {username}")
            return jsonify({'success': True, 'message': '注册成功'})
        else:
            return jsonify({'success': False, 'message': '注册失败'}), 500
            
    except Exception as e:
        logging.error(f"Register failed: {str(e)}")
        return jsonify({'success': False, 'message': f'注册失败: {str(e)}'}), 500

@auth_bp.route('/change_password', methods=['POST'])
@require_auth()
def change_password(user_info):
    """Change password"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': '请求数据格式错误'}), 400
        
        old_password = data.get('old_password')
        new_password = data.get('new_password')
        user_type = data.get('user_type', 'user')
        
        if not old_password or not new_password:
            return jsonify({'success': False, 'message': '旧密码和新密码不能为空'}), 400
        
        if len(new_password) < 6:
            return jsonify({'success': False, 'message': '新密码长度不能少于6个字符'}), 400
        
        old_password_hash = hashlib.sha256(old_password.encode()).hexdigest()
        if user_info['pw'] != old_password_hash:
            return jsonify({'success': False, 'message': '旧密码不正确'}), 400
        
        new_password_hash = hashlib.sha256(new_password.encode()).hexdigest()
        table = 'user' if user_type == 'user' else 'admin'
        sql = f"UPDATE {table} SET pw = %s WHERE id = %s"
        result = execute_sql(sql, (new_password_hash, user_info['id']))
        
        if result > 0:
            if user_type == 'admin':
                log_admin_action(user_info['id'], f"管理员{user_info['id']}修改了密码")
            
            return jsonify({'success': True, 'message': '密码修改成功'})
        else:
            return jsonify({'success': False, 'message': '密码修改失败'}), 500
            
    except Exception as e:
        logging.error(f"Change password failed: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500
