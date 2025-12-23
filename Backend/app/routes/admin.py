from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from app.database import fetch_one, fetch_all, execute_sql
from app.utils.auth import require_auth
from app.services.auth_service import log_admin_action
import logging

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/users', methods=['GET'])
@require_auth('admin')
def admin_get_users(admin_info):
    """Admin get users"""
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))
        offset = (page - 1) * limit
        
        users_sql = """
        SELECT id, username, imagelimit, batchlimit, realtimePermission, isbannd, update_time
        FROM user 
        ORDER BY id DESC 
        LIMIT %s OFFSET %s
        """
        users = fetch_all(users_sql, (limit, offset))
        
        count_sql = "SELECT COUNT(*) as total FROM user"
        total_result = fetch_one(count_sql)
        total = total_result['total'] if total_result else 0
        
        formatted_users = []
        for user in users:
            formatted_users.append({
                'id': user['id'],
                'username': user['username'],
                'imagelimit': user['imagelimit'],
                'batchlimit': user['batchlimit'],
                'realtimePermission': user['realtimePermission'],
                'isbannd': user['isbannd'],
                'update_time': user['update_time'].strftime('%Y-%m-%d %H:%M:%S') if user['update_time'] else None
            })
        
        return jsonify({
            'success': True,
            'data': {
                'users': formatted_users,
                'total': total,
                'page': page,
                'limit': limit
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/user/<int:user_id>', methods=['PUT'])
@require_auth('admin')
def admin_update_user(admin_info, user_id):
    """Admin update user"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': '请求数据格式错误'}), 400
        
        user = fetch_one("SELECT * FROM user WHERE id = %s", (user_id,))
        if not user:
            return jsonify({'success': False, 'message': '用户不存在'}), 404
        
        update_fields = []
        params = []
        log_messages = []
        
        if 'imagelimit' in data:
            update_fields.append('imagelimit = %s')
            params.append(data['imagelimit'])
            if data['imagelimit'] == -1:
                log_messages.append(f"管理员{admin_info['id']}设置用户{user_id}图片识别无限制")
            else:
                log_messages.append(f"管理员{admin_info['id']}设置用户{user_id}图片识别次数为{data['imagelimit']}")
        
        if 'batchlimit' in data:
            update_fields.append('batchlimit = %s')
            params.append(data['batchlimit'])
            if data['batchlimit'] == -1:
                log_messages.append(f"管理员{admin_info['id']}设置用户{user_id}批量处理无限制")
            else:
                log_messages.append(f"管理员{admin_info['id']}设置用户{user_id}批量处理次数为{data['batchlimit']}")
        
        if 'realtimePermission' in data:
            update_fields.append('realtimePermission = %s')
            params.append(data['realtimePermission'])
            status = "开启" if data['realtimePermission'] else "关闭"
            log_messages.append(f"管理员{admin_info['id']}{status}用户{user_id}实时检测权限")
        
        if not update_fields:
            return jsonify({'success': False, 'message': '没有需要更新的字段'}), 400
        
        params.append(user_id)
        sql = f"UPDATE user SET {', '.join(update_fields)} WHERE id = %s"
        result = execute_sql(sql, params)
        
        if result > 0:
            for message in log_messages:
                log_admin_action(admin_info['id'], message)
            
            return jsonify({'success': True, 'message': '用户信息更新成功'})
        else:
            return jsonify({'success': False, 'message': '更新失败'}), 500
            
    except Exception as e:
        logging.error(f"Admin update user failed: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/logs', methods=['GET'])
@require_auth('admin')
def admin_get_logs(admin_info):
    """Admin get logs"""
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))
        offset = (page - 1) * limit
        
        logs_sql = """
        SELECT al.*, a.username as admin_username 
        FROM admin_log al
        LEFT JOIN admin a ON al.user_id = a.id
        ORDER BY al.time DESC 
        LIMIT %s OFFSET %s
        """
        logs = fetch_all(logs_sql, (limit, offset))
        
        count_sql = "SELECT COUNT(*) as total FROM admin_log"
        total_result = fetch_one(count_sql)
        total = total_result['total'] if total_result else 0
        
        formatted_logs = []
        for log in logs:
            formatted_logs.append({
                'id': log['id'],
                'admin_username': log['admin_username'],
                'time': log['time'].strftime('%Y-%m-%d %H:%M:%S'),
                'log': log['log']
            })
        
        return jsonify({
            'success': True,
            'data': {
                'logs': formatted_logs,
                'total': total,
                'page': page,
                'limit': limit
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/user_logs/<int:user_id>', methods=['GET'])
@require_auth('admin')
def admin_get_user_logs(admin_info, user_id):
    """Admin get user logs"""
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))
        offset = (page - 1) * limit
        
        user = fetch_one("SELECT username FROM user WHERE id = %s", (user_id,))
        if not user:
            return jsonify({'success': False, 'message': '用户不存在'}), 404
        
        logs_sql = """
        SELECT * FROM user_log 
        WHERE user_id = %s 
        ORDER BY time DESC 
        LIMIT %s OFFSET %s
        """
        logs = fetch_all(logs_sql, (user_id, limit, offset))
        
        count_sql = "SELECT COUNT(*) as total FROM user_log WHERE user_id = %s"
        total_result = fetch_one(count_sql, (user_id,))
        total = total_result['total'] if total_result else 0
        
        formatted_logs = []
        for log in logs:
            formatted_logs.append({
                'user_id': user_id,
                'username': user['username'],
                'id': log['id'],
                'time': log['time'].strftime('%Y-%m-%d %H:%M:%S'),
                'class': log['class'],
                'quantity': log['quantity'],
                'remain': log['remain']
            })
        
        return jsonify({
            'success': True,
            'data': {
                'username': user['username'],
                'logs': formatted_logs,
                'total': total,
                'page': page,
                'limit': limit
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/user/<int:user_id>/limits', methods=['POST'])
@require_auth('admin')
def admin_adjust_user_limits(admin_info, user_id):
    """Admin adjust user limits"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': '请求数据格式错误'}), 400
        
        user = fetch_one("SELECT * FROM user WHERE id = %s", (user_id,))
        if not user:
            return jsonify({'success': False, 'message': '用户不存在'}), 404
        
        if 'imagelimit_delta' in data:
            delta = int(data['imagelimit_delta'])
            if user['imagelimit'] != -1:
                new_limit = max(0, user['imagelimit'] + delta)
                execute_sql("UPDATE user SET imagelimit = %s WHERE id = %s", (new_limit, user_id))
                if delta > 0:
                    log_admin_action(admin_info['id'], f"管理员{admin_info['id']}为用户{user_id}的图片识别次数+{delta}")
                else:
                    log_admin_action(admin_info['id'], f"管理员{admin_info['id']}为用户{user_id}的图片识别次数{delta}")
        
        if 'batchlimit_delta' in data:
            delta = int(data['batchlimit_delta'])
            if user['batchlimit'] != -1:
                new_limit = max(0, user['batchlimit'] + delta)
                execute_sql("UPDATE user SET batchlimit = %s WHERE id = %s", (new_limit, user_id))
                if delta > 0:
                    log_admin_action(admin_info['id'], f"管理员{admin_info['id']}为用户{user_id}的批量处理次数+{delta}")
                else:
                    log_admin_action(admin_info['id'], f"管理员{admin_info['id']}为用户{user_id}的批量处理次数{delta}")
        
        return jsonify({'success': True, 'message': '用户次数调整成功'})
        
    except Exception as e:
        logging.error(f"Admin adjust user limits failed: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/statistics', methods=['GET'])
@require_auth('admin')
def admin_get_statistics(admin_info):
    """Admin get statistics"""
    try:
        user_count_result = fetch_one("SELECT COUNT(*) as total FROM user")
        user_count = user_count_result['total'] if user_count_result else 0
        
        today = datetime.now().date()
        active_users_result = fetch_one("""
            SELECT COUNT(DISTINCT user_id) as active 
            FROM user_log 
            WHERE DATE(time) = %s
        """, (today,))
        active_users = active_users_result['active'] if active_users_result else 0
        
        today_stats = fetch_all("""
            SELECT class, COUNT(*) as count, SUM(quantity) as total_quantity
            FROM user_log 
            WHERE DATE(time) = %s
            GROUP BY class
        """, (today,))
        
        today_operations = {
            'image_recognition': 0,
            'batch_processing': 0,
            'realtime_detection': 0,
            'total_traffic': 0
        }
        
        for stat in today_stats:
            if stat['class'] == 1:
                today_operations['image_recognition'] = stat['count']
            elif stat['class'] == 2:
                today_operations['batch_processing'] = stat['count']
                today_operations['total_traffic'] = stat['total_quantity'] or 0
            elif stat['class'] == 3:
                today_operations['realtime_detection'] = stat['count']
        
        seven_days_ago = (datetime.now() - timedelta(days=7)).date()
        trend_data = fetch_all("""
            SELECT DATE(time) as date, class, COUNT(*) as count
            FROM user_log 
            WHERE DATE(time) >= %s
            GROUP BY DATE(time), class
            ORDER BY date DESC
        """, (seven_days_ago,))
        
        permission_stats = fetch_one("""
            SELECT 
                SUM(CASE WHEN imagelimit = -1 THEN 1 ELSE 0 END) as unlimited_image,
                SUM(CASE WHEN batchlimit = -1 THEN 1 ELSE 0 END) as unlimited_batch,
                SUM(CASE WHEN realtimePermission = 1 THEN 1 ELSE 0 END) as realtime_enabled
            FROM user
        """)
        
        return jsonify({
            'success': True,
            'data': {
                'user_count': user_count,
                'active_users_today': active_users,
                'today_operations': today_operations,
                'trend_data': trend_data,
                'permission_stats': {
                    'unlimited_image_users': permission_stats['unlimited_image'] if permission_stats else 0,
                    'unlimited_batch_users': permission_stats['unlimited_batch'] if permission_stats else 0,
                    'realtime_enabled_users': permission_stats['realtime_enabled'] if permission_stats else 0
                }
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/user', methods=['POST'])
@require_auth('admin')
def create_user(admin_info):
    """Admin create user"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': '请求数据格式错误'}), 400
        
        username = data.get('username')
        password = data.get('password')
        imagelimit = data.get('imagelimit', 100)
        batchlimit = data.get('batchlimit', 10)
        realtimePermission = data.get('realtimePermission', 0)
        
        if not username or not password:
            return jsonify({'success': False, 'message': '用户名和密码不能为空'}), 400
        
        existing_user = fetch_one("SELECT id FROM user WHERE username = %s", (username,))
        if existing_user:
            return jsonify({'success': False, 'message': '用户名已存在'}), 409
        
        max_id_result = fetch_one("SELECT MAX(id) as max_id FROM user")
        next_id = (max_id_result['max_id'] or 0) + 1
        
        sql = """
        INSERT INTO user (id, username, pw, imagelimit, batchlimit, realtimePermission, isbannd, token, update_time) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        result = execute_sql(sql, (
            next_id, username, password, imagelimit, batchlimit, 
            realtimePermission, 0, '', datetime.now()
        ))
        
        if result:
            log_admin_action(admin_info['id'], f"创建用户: {username}")
            
            logging.info(f"Admin created user: {username}")
            return jsonify({
                'success': True, 
                'message': '用户创建成功',
                'data': {'id': next_id, 'username': username}
            })
        else:
            return jsonify({'success': False, 'message': '创建用户失败'}), 500
            
    except Exception as e:
        logging.error(f"Create user failed: {str(e)}")
        return jsonify({'success': False, 'message': f'创建用户失败: {str(e)}'}), 500

@admin_bp.route('/user/<int:user_id>', methods=['DELETE'])
@require_auth('admin')
def delete_user(admin_info, user_id):
    """Admin delete user"""
    try:
        user = fetch_one("SELECT username FROM user WHERE id = %s", (user_id,))
        if not user:
            return jsonify({'success': False, 'message': '用户不存在'}), 404
        
        if user['username'] == 'admin':
            return jsonify({'success': False, 'message': '不能删除管理员账户'}), 403
        
        execute_sql("DELETE FROM user_log WHERE user_id = %s", (user_id,))
        result = execute_sql("DELETE FROM user WHERE id = %s", (user_id,))
        
        if result:
            log_admin_action(admin_info['id'], f"删除用户: {user['username']}")
            logging.info(f"Admin deleted user: {user['username']}")
            return jsonify({'success': True, 'message': '用户删除成功'})
        else:
            return jsonify({'success': False, 'message': '删除用户失败'}), 500
            
    except Exception as e:
        logging.error(f"Delete user failed: {str(e)}")
        return jsonify({'success': False, 'message': f'删除用户失败: {str(e)}'}), 500

@admin_bp.route('/user/<int:user_id>/status', methods=['PUT'])
@require_auth('admin')
def toggle_user_status(admin_info, user_id):
    """Admin toggle user status"""
    try:
        data = request.get_json()
        banned = data.get('banned', False)
        
        user = fetch_one("SELECT username FROM user WHERE id = %s", (user_id,))
        if not user:
            return jsonify({'success': False, 'message': '用户不存在'}), 404
        
        if user['username'] == 'admin':
            return jsonify({'success': False, 'message': '不能封禁管理员账户'}), 403
        
        ban_status = 1 if banned else 0
        sql = "UPDATE user SET isbannd = %s WHERE id = %s"
        action = "封禁" if banned else "解封"
        
        result = execute_sql(sql, (ban_status, user_id))
        
        if result:
            log_admin_action(admin_info['id'], f"{action}用户: {user['username']}")
            logging.info(f"Admin {action} user: {user['username']}")
            return jsonify({'success': True, 'message': f'{action}用户成功'})
        else:
            return jsonify({'success': False, 'message': f'{action}用户失败'}), 500
            
    except Exception as e:
        logging.error(f"Toggle user status failed: {str(e)}")
        return jsonify({'success': False, 'message': f'操作失败: {str(e)}'}), 500

@admin_bp.route('/user_logs/all', methods=['GET'])
@require_auth('admin')
def get_all_user_logs(admin_info):
    """Admin get all user logs"""
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 50))
        offset = (page - 1) * limit
        
        sql = """
        SELECT ul.id, ul.user_id, ul.time, ul.class, ul.quantity, ul.remain, u.username
        FROM user_log ul
        LEFT JOIN user u ON ul.user_id = u.id
        ORDER BY ul.time DESC
        LIMIT %s OFFSET %s
        """
        logs = fetch_all(sql, (limit, offset))
        
        total_sql = "SELECT COUNT(*) as total FROM user_log"
        total_result = fetch_one(total_sql)
        total = total_result['total'] if total_result else 0
        
        return jsonify({
            'success': True,
            'data': {
                'logs': logs,
                'total': total,
                'page': page,
                'limit': limit
            }
        })
        
    except Exception as e:
        logging.error(f"Get all user logs failed: {str(e)}")
        return jsonify({'success': False, 'message': f'获取日志失败: {str(e)}'}), 500
