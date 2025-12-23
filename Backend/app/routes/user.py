from flask import Blueprint, request, jsonify
from app.database import fetch_one, fetch_all
from app.utils.auth import require_auth

user_bp = Blueprint('user', __name__)

@user_bp.route('/info', methods=['GET'])
@require_auth('user')
def get_user_info(user_info):
    """Get user info"""
    try:
        image_used_result = fetch_one("""
            SELECT COUNT(*) as count FROM user_log 
            WHERE user_id = %s AND class = 1
        """, (user_info['id'],))
        image_used = image_used_result['count'] if image_used_result else 0
        
        batch_used_result = fetch_one("""
            SELECT COUNT(*) as count FROM user_log 
            WHERE user_id = %s AND class = 2
        """, (user_info['id'],))
        batch_used = batch_used_result['count'] if batch_used_result else 0
        
        return jsonify({
            'success': True,
            'data': {
                'id': user_info['id'],
                'username': user_info['username'],
                'imagelimit': user_info['imagelimit'],
                'batchlimit': user_info['batchlimit'],
                'realtimePermission': user_info['realtimePermission'],
                'isbannd': user_info['isbannd'],
                'imageUsed': image_used,
                'batchUsed': batch_used,
                'update_time': user_info['update_time'].strftime('%Y-%m-%d %H:%M:%S') if user_info['update_time'] else None
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@user_bp.route('/logs', methods=['GET'])
@require_auth('user')
def get_user_logs(user_info):
    """Get user logs"""
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))
        offset = (page - 1) * limit
        
        logs_sql = """
        SELECT * FROM user_log 
        WHERE user_id = %s 
        ORDER BY time DESC 
        LIMIT %s OFFSET %s
        """
        logs = fetch_all(logs_sql, (user_info['id'], limit, offset))
        
        count_sql = "SELECT COUNT(*) as total FROM user_log WHERE user_id = %s"
        total_result = fetch_one(count_sql, (user_info['id'],))
        total = total_result['total'] if total_result else 0
        
        formatted_logs = []
        for log in logs:
            formatted_logs.append({
                'id': log['id'],
                'time': log['time'].strftime('%Y-%m-%d %H:%M:%S'),
                'class': log['class'],
                'quantity': log['quantity'],
                'remain': log['remain'],
                'user_id': log['user_id']
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

@user_bp.route('/check-permissions', methods=['GET'])
@require_auth('user')
def check_user_permissions(user_info):
    """Check user permissions"""
    try:
        return jsonify({
            'success': True,
            'data': {
                'realtimePermission': user_info['realtimePermission'],
                'isbannd': user_info['isbannd'],
                'username': user_info['username'],
                'user_id': user_info['id']
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
