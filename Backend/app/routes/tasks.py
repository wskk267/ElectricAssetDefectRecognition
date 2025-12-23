from flask import Blueprint, jsonify
from app.services.task_service import active_tasks, recently_completed_tasks, get_task_progress, cancel_task
import logging

tasks_bp = Blueprint('tasks', __name__)

@tasks_bp.route('/progress/<task_id>', methods=['GET'])
def get_progress(task_id):
    try:
        if task_id not in active_tasks:
            if task_id in recently_completed_tasks:
                return jsonify({
                    'success': True,
                    'progress': recently_completed_tasks[task_id],
                    'message': '任务已完成'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': '任务不存在或已过期',
                    'error_type': 'task_not_found'
                }), 404

        progress = get_task_progress(task_id)
        return jsonify({
            'success': True,
            'progress': progress
        })
        
    except Exception as e:
        logging.error(f"Get task progress failed: {e}")
        return jsonify({
            'success': False,
            'message': '获取进度失败',
            'error_type': 'server_error'
        }), 500

@tasks_bp.route('/cancel/<task_id>', methods=['POST'])
def cancel_batch_task(task_id):
    """Cancel batch task"""
    try:
        if cancel_task(task_id):
            logging.info(f"Task cancelled: {task_id}")
            return jsonify({
                'success': True,
                'message': f'任务 {task_id} 已取消'
            })
        else:
            return jsonify({
                'success': False,
                'message': f'任务 {task_id} 不存在或已完成'
            }), 404
    except Exception as e:
        logging.error(f"Cancel task failed: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'取消任务失败: {str(e)}'
        }), 500
