import threading
import time

active_tasks = {}
task_progress = {}
task_lock = threading.Lock()
recently_completed_tasks = {}

def is_task_cancelled(task_id):
    """Check if task is cancelled"""
    with task_lock:
        return active_tasks.get(task_id, {}).get('cancelled', False)

def cancel_task(task_id):
    """Cancel a task"""
    with task_lock:
        if task_id in active_tasks:
            active_tasks[task_id]['cancelled'] = True
            return True
    return False

def register_task(task_id):
    """Register a new task"""
    with task_lock:
        active_tasks[task_id] = {'cancelled': False, 'created_at': time.time()}
        task_progress[task_id] = {
            'current_file_index': 0,
            'total_files': 0,
            'current_file_name': '',
            'current_file_progress': 0,
            'overall_progress': 0,
            'stage': 'starting',
            'start_time': time.time(),
            'processed_files': []
        }

def unregister_task(task_id):
    """Unregister a task"""
    with task_lock:
        active_tasks.pop(task_id, None)
        task_progress.pop(task_id, None)
        recently_completed_tasks.discard(task_id)

def update_task_progress(task_id, **kwargs):
    """Update task progress"""
    with task_lock:
        if task_id in task_progress:
            task_progress[task_id].update(kwargs)
            if task_progress[task_id]['total_files'] > 0:
                file_progress = task_progress[task_id]['current_file_index'] / task_progress[task_id]['total_files']
                current_file_progress = task_progress[task_id]['current_file_progress'] / 100.0
                if task_progress[task_id]['total_files'] > 0:
                    current_file_weight = 1.0 / task_progress[task_id]['total_files']
                    task_progress[task_id]['overall_progress'] = min(100, 
                        (file_progress + current_file_progress * current_file_weight) * 100)

def get_task_progress(task_id):
    """Get task progress"""
    with task_lock:
        return task_progress.get(task_id, {}).copy()
