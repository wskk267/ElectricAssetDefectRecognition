from flask import Blueprint, request, jsonify
from PIL import Image
import io
import uuid
import threading
import time
import logging
from app.utils.common import allowed_file, is_video_file
from app.utils.auth import require_auth
from app.services.auth_service import update_user_limit, log_user_action
from app.services.image_service import process_image, process_images_batch, process_image_realtime, process_video_with_annotation
from app.services.task_service import register_task, unregister_task, update_task_progress, is_task_cancelled

recognition_bp = Blueprint('recognition', __name__)

@recognition_bp.route('/predict', methods=['POST'])
@require_auth('user')
def predict(user_info):
    """图片预测"""
    try:
        if user_info['imagelimit'] == 0:
            return jsonify({
                'success': False, 
                'message': '图片识别次数已用完，请联系管理员增加次数',
                'error_type': 'quota_exceeded',
                'remaining_limit': 0
            }), 403
        
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': '请选择要上传的文件'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'message': '未选择文件'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'message': '不支持的文件格式，请上传JPG、PNG、BMP格式的图片'}), 400
        
        try:
            image = Image.open(io.BytesIO(file.read()))
        except Exception as e:
            return jsonify({'success': False, 'message': f'无法读取图片文件: {str(e)}'}), 400
        
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        logging.info(f"User {user_info['username']} uploaded image: {file.filename}, size: {image.size}")
        
        result = process_image(image)
        
        remaining_limit = -1
        if user_info['imagelimit'] != -1:
            success, new_limit = update_user_limit(user_info['id'], 'imagelimit', -1)
            if success:
                log_user_action(user_info['id'], 1, 1, new_limit)
                logging.info(f"User {user_info['username']} deducted 1 image limit, remaining {new_limit}")
                remaining_limit = new_limit
            else:
                logging.error(f"User {user_info['username']} deduction failed: {new_limit}")
                remaining_limit = 0
        else:
            log_user_action(user_info['id'], 1, 1, -1)
            logging.info(f"User {user_info['username']} (unlimited) image recognition completed")
        
        logging.info(f"Recognition success, detected {result['detected_objects']} objects, time {result.get('inference_time_ms', 0):.2f}ms")
        
        return jsonify({
            'success': True,
            'message': '识别完成',
            'filename': file.filename,
            'data': result,
            'remaining_limit': remaining_limit
        })
            
    except Exception as e:
        error_msg = f"API call failed: {str(e)}"
        logging.error(f"{error_msg}")
        return jsonify({
            'success': False,
            'message': error_msg,
            'error': str(e)
        }), 500

@recognition_bp.route('/batch', methods=['POST'])
@require_auth('user')
def batch_predict(user_info):
    """批量处理"""
    try:
        task_id = f"batch_{uuid.uuid4().hex[:8]}"
        register_task(task_id)
        
        if 'files' not in request.files:
            unregister_task(task_id)
            return jsonify({'success': False, 'message': '请选择要上传的文件'}), 400
        
        files = request.files.getlist('files')
        if len(files) == 0:
            unregister_task(task_id)
            return jsonify({'success': False, 'message': '未选择文件'}), 400
        
        if len(files) > 100:
            unregister_task(task_id)
            return jsonify({'success': False, 'message': '最多只能处理100个文件'}), 400
        
        file_data_cache = {}
        total_size_bytes = 0
        
        logging.info(f"User {user_info['username']} caching {len(files)} files...")
        for i, file in enumerate(files):
            try:
                file.seek(0)
                data = file.read()
                file_data_cache[file.filename] = data
                total_size_bytes += len(data)
            except Exception as e:
                logging.error(f"Cache file {file.filename} failed: {str(e)}")
                unregister_task(task_id)
                return jsonify({'success': False, 'message': f'读取文件失败: {str(e)}'}), 400
        
        total_size_mb = total_size_bytes / (1024 * 1024)
        required_quota = round(total_size_mb, 3)
        
        logging.info(f"Cache complete, total size: {total_size_mb:.3f} MB, required quota: {required_quota:.3f} MB")
        
        if total_size_bytes > 100 * 1024 * 1024:
            unregister_task(task_id)
            return jsonify({'success': False, 'message': '文件总大小不能超过100MB'}), 400
        
        if user_info['batchlimit'] != -1:
            if user_info['batchlimit'] < required_quota:
                unregister_task(task_id)
                return jsonify({
                    'success': False, 
                    'message': f'流量不足！需要 {required_quota:.3f} MB，剩余 {user_info["batchlimit"]:.3f} MB',
                    'error_type': 'quota_exceeded',
                    'required_quota': round(required_quota, 3),
                    'remaining_quota': round(user_info['batchlimit'], 3)
                }), 403
        
        update_task_progress(task_id, total_files=len(files), stage='processing')
        
        def process_files_background():
            results = []
            actual_quota_used = round(required_quota, 3)
            
            try:
                image_files = []
                video_files = []
                image_filenames = []
                video_filenames = []
                
                for file in files:
                    if not allowed_file(file.filename):
                        results.append({
                            'filename': file.filename,
                            'success': False,
                            'error': '不支持的文件格式'
                        })
                        continue
                    
                    if is_video_file(file.filename):
                        video_files.append(file)
                        video_filenames.append(file.filename)
                    else:
                        image_files.append(file)
                        image_filenames.append(file.filename)
                
                logging.info(f"Batch processing: {len(image_files)} images, {len(video_files)} videos")
                
                if image_files:
                    logging.info(f"Start processing {len(image_files)} images...")
                    
                    try:
                        images = []
                        valid_image_filenames = []
                        
                        for i, file in enumerate(image_files):
                            if is_task_cancelled(task_id):
                                logging.info(f"Task {task_id} cancelled")
                                update_task_progress(task_id, stage='cancelled')
                                return
                            
                            update_task_progress(task_id, current_file_name=f"Preparing image: {file.filename}")
                            
                            try:
                                image_data = file_data_cache.get(file.filename)
                                if not image_data:
                                    results.append({'filename': file.filename, 'success': False, 'error': 'Missing file data'})
                                    continue
                                
                                if len(image_data) == 0:
                                    results.append({'filename': file.filename, 'success': False, 'error': 'Empty file'})
                                    continue
                                
                                image = Image.open(io.BytesIO(image_data))
                                
                                if image.format not in ['JPEG', 'PNG', 'BMP', 'WEBP']:
                                    results.append({'filename': file.filename, 'success': False, 'error': f'Unsupported format: {image.format}'})
                                    continue
                                
                                if image.mode != 'RGB':
                                    image = image.convert('RGB')
                                
                                images.append(image)
                                valid_image_filenames.append(file.filename)
                                
                            except Exception as e:
                                logging.error(f"Prepare image {file.filename} failed: {str(e)}")
                                results.append({'filename': file.filename, 'success': False, 'error': f'Read failed: {str(e)}'})
                        
                        if images:
                            batch_size = 8
                            total_batches = (len(images) + batch_size - 1) // batch_size
                            
                            for batch_idx in range(total_batches):
                                if is_task_cancelled(task_id):
                                    logging.info(f"Task {task_id} cancelled")
                                    update_task_progress(task_id, stage='cancelled')
                                    return
                                
                                start_idx = batch_idx * batch_size
                                end_idx = min(start_idx + batch_size, len(images))
                                batch_images = images[start_idx:end_idx]
                                batch_filenames = valid_image_filenames[start_idx:end_idx]
                                
                                batch_results = process_images_batch(batch_images, return_annotated=True, batch_size=batch_size)
                                
                                for i, (result, filename) in enumerate(zip(batch_results, batch_filenames)):
                                    if 'error' in result:
                                        results.append({'filename': filename, 'success': False, 'error': result['error']})
                                    else:
                                        results.append({
                                            'filename': filename,
                                            'success': True,
                                            'file_type': 'image',
                                            'data': result,
                                            'detected_objects': result['detected_objects'],
                                            'inference_time_ms': result.get('inference_time_ms', 0)
                                        })
                                    
                                    current_index = len(results)
                                    total_files = len(image_files) + len(video_files)
                                    overall_progress = (current_index / total_files) * 100 if total_files > 0 else 0
                                    
                                    update_task_progress(task_id, 
                                                       current_file_index=current_index,
                                                       current_file_name=filename,
                                                       current_file_progress=100,
                                                       overall_progress=overall_progress)
                    
                    except Exception as e:
                        logging.error(f"Batch image processing failed: {str(e)}")
                        for filename in image_filenames:
                            if not any(r['filename'] == filename for r in results):
                                results.append({'filename': filename, 'success': False, 'error': f'Batch failed: {str(e)}'})
                                
                                current_index = len(results)
                                total_files = len(image_files) + len(video_files)
                                overall_progress = (current_index / total_files) * 100 if total_files > 0 else 0
                                
                                update_task_progress(task_id, 
                                                   current_file_index=current_index,
                                                   current_file_name=filename,
                                                   current_file_progress=100,
                                                   overall_progress=overall_progress)
                
                for i, file in enumerate(video_files):
                    if is_task_cancelled(task_id):
                        logging.info(f"Task {task_id} cancelled")
                        update_task_progress(task_id, stage='cancelled')
                        break
                    
                    total_files = len(image_files) + len(video_files)
                    current_completed = len(results)
                    update_task_progress(task_id, current_file_name=file.filename, current_file_progress=0)
                    
                    try:
                        logging.info(f"Processing video: {file.filename}")
                        
                        video_data = file_data_cache.get(file.filename)
                        if not video_data:
                            results.append({'filename': file.filename, 'success': False, 'error': 'Missing file data'})
                            current_completed = len(results)
                            overall_progress = (current_completed / total_files) * 100 if total_files > 0 else 0
                            update_task_progress(task_id, current_file_index=current_completed, current_file_name=file.filename, current_file_progress=100, overall_progress=overall_progress)
                            continue
                            
                        video_file = io.BytesIO(video_data)
                        
                        def progress_callback(current_frame, total_frames):
                            if total_frames > 0:
                                progress_percent = (current_frame / total_frames) * 100
                                current_completed_files = len(results)
                                base_progress = (current_completed_files / total_files) * 100 if total_files > 0 else 0
                                file_weight = (1 / total_files) * 100 if total_files > 0 else 0
                                overall_progress = base_progress + (progress_percent / 100) * file_weight
                                
                                update_task_progress(task_id, current_file_progress=progress_percent, overall_progress=overall_progress)
                        
                        result = process_video_with_annotation(
                            video_file, 
                            frame_interval=1,
                            task_checker=lambda: is_task_cancelled(task_id),
                            progress_callback=progress_callback
                        )
                        
                        results.append({
                            'filename': file.filename,
                            'success': True,
                            'file_type': 'video',
                            'data': result,
                            'detected_objects': result['detected_objects'],
                            'processing_time_ms': result['processing_time_ms']
                        })
                        
                        current_completed = len(results)
                        overall_progress = (current_completed / total_files) * 100 if total_files > 0 else 0
                        
                        update_task_progress(task_id, current_file_index=current_completed, current_file_name=file.filename, current_file_progress=100, overall_progress=overall_progress)
                        
                    except Exception as e:
                        logging.error(f"Process video {file.filename} failed: {str(e)}")
                        results.append({'filename': file.filename, 'success': False, 'error': str(e)})
                        
                        current_completed = len(results)
                        overall_progress = (current_completed / total_files) * 100 if total_files > 0 else 0
                        
                        update_task_progress(task_id, current_file_index=current_completed, current_file_name=file.filename, current_file_progress=100, overall_progress=overall_progress)
                
                was_cancelled = is_task_cancelled(task_id)
                total_files = len(image_files) + len(video_files)
                
                successful_results = [r for r in results if r['success']]
                quota_used = 0.0
                if successful_results:
                    for result in successful_results:
                        filename = result['filename']
                        if filename in file_data_cache:
                            file_size_mb = len(file_data_cache[filename]) / (1024 * 1024)
                            quota_used += file_size_mb
                
                update_task_progress(task_id, 
                                   current_file_index=total_files,
                                   overall_progress=100,
                                   stage='completed' if not was_cancelled else 'cancelled',
                                   processed_files=results)
                
                if not was_cancelled and actual_quota_used > 0:
                    if user_info['batchlimit'] != -1:
                        success, new_limit = update_user_limit(user_info['id'], 'batchlimit', -actual_quota_used)
                        if success:
                            log_user_action(user_info['id'], 2, actual_quota_used, new_limit)
                            logging.info(f"User {user_info['username']} batch quota deducted {actual_quota_used:.3f}MB, remaining {new_limit:.3f}MB")
                        else:
                            logging.error(f"User {user_info['username']} quota deduction failed: {new_limit}")
                    else:
                        log_user_action(user_info['id'], 2, actual_quota_used, -1)
                        logging.info(f"User {user_info['username']} batch quota used {actual_quota_used:.3f}MB (unlimited)")
                
            except Exception as e:
                logging.error(f"Batch processing failed: {str(e)}")
                update_task_progress(task_id, stage='error', error=str(e))
        
        threading.Thread(target=process_files_background, daemon=True).start()
        
        if user_info['batchlimit'] == -1:
            remaining_quota = -1
        else:
            remaining_quota = round(max(0, user_info['batchlimit'] - required_quota), 3)
        
        return jsonify({
            'success': True,
            'message': f'批量处理已开始，预计消耗流量 {required_quota:.3f} MB',
            'task_id': task_id,
            'required_quota': round(required_quota, 3),
            'remaining_quota': remaining_quota
        })
        
    except Exception as e:
        logging.error(f"Batch processing start failed: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'批量处理失败: {str(e)}'
        }), 500

@recognition_bp.route('/realtime/detect', methods=['POST'])
@require_auth('user')
def realtime_detect_fast(user_info):
    """快速实时检测"""
    try:
        if user_info['realtimePermission'] != 1:
            return jsonify({'success': False, 'message': '您没有实时检测权限'}), 403
        
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': '请选择要上传的文件'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'message': '未选择文件'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'message': '不支持的文件格式'}), 400
        
        try:
            image_data = file.read()
            image = Image.open(io.BytesIO(image_data))
            
            if image.mode != 'RGB':
                image = image.convert('RGB')
                
        except Exception as e:
            return jsonify({'success': False, 'message': f'无法读取图片: {str(e)}'}), 400
        
        result = process_image_realtime(image)
        
        predictions = result.get('predictions', [])
        formatted_predictions = {}
        
        for i, pred in enumerate(predictions):
            formatted_predictions[i] = {
                'asset_category': pred.get('asset_category', pred.get('class_name_zh', '')),
                'defect_status': pred.get('defect_status', '正常'),
                'confidence': round(pred.get('confidence', 0), 3),
                'center': {
                    'x': round(pred.get('center', {}).get('x', 0), 4),
                    'y': round(pred.get('center', {}).get('y', 0), 4)
                },
                'width': round(pred.get('width', 0), 4),
                'height': round(pred.get('height', 0), 4)
            }
        
        return jsonify({
            'success': True,
            'data': {
                'predictions': formatted_predictions,
                'inference_time_ms': round(result.get('inference_time_ms', 0), 1),
                'detected_objects': len(predictions)
            }
        })
            
    except Exception as e:
        return jsonify({
            'success': True,
            'data': {
                'predictions': {},
                'inference_time_ms': 0,
                'detected_objects': 0
            }
        })

@recognition_bp.route('/realtime', methods=['POST'])
@require_auth('user')
def realtime_detect(user_info):
    """实时检测 (旧版)"""
    try:
        if user_info['realtimePermission'] != 1:
            return jsonify({'success': False, 'message': '您没有实时检测权限'}), 403
        
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': '请选择要上传的文件'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'message': '未选择文件'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'message': '不支持的文件格式，请上传JPG、PNG、BMP格式的图片'}), 400
        
        try:
            image = Image.open(io.BytesIO(file.read()))
        except Exception as e:
            return jsonify({'success': False, 'message': f'无法读取图片文件: {str(e)}'}), 400
        
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        logging.info(f"User {user_info['username']} realtime detect: {file.filename}, size: {image.size}")
        
        result = process_image(image, return_annotated=True)
        
        logging.info(f"Realtime detect complete, detected {result.get('detected_objects', 0)} objects")
        return jsonify({
            'success': True,
            'message': '实时检测完成',
            'filename': file.filename,
            'data': result
        })
            
    except Exception as e:
        error_msg = f"Realtime detect failed: {str(e)}"
        logging.error(f"{error_msg}")
        return jsonify({
            'success': False,
            'message': error_msg,
            'error': str(e)
        }), 500

@recognition_bp.route('/realtime/log', methods=['POST'])
@require_auth('user')
def log_realtime_usage(user_info):
    """记录实时检测使用情况"""
    try:
        data = request.get_json()
        quantity = data.get('quantity', 0)
        duration = data.get('duration', 0)
        
        if user_info['realtimePermission'] != 1:
            return jsonify({
                'success': False,
                'message': '您没有实时检测权限',
                'error_type': 'permission_denied'
            }), 403
        
        if duration > 0:
            log_user_action(user_info['id'], 3, duration, -1)
            logging.info(f"User {user_info['username']} realtime duration: {duration}s")
        elif quantity > 0:
            log_user_action(user_info['id'], 3, quantity, -1)
            logging.info(f"User {user_info['username']} realtime count: {quantity}")
        else:
            log_user_action(user_info['id'], 3, 1, -1)
            logging.info(f"User {user_info['username']} realtime count: 1")
        
        return jsonify({
            'success': True,
            'message': '使用记录已保存',
            'data': {
                'quantity': quantity,
                'duration': duration,
                'user_id': user_info['id']
            }
        })
        
    except Exception as e:
        logging.error(f"Log realtime usage failed: {str(e)}")
        return jsonify({
            'success': False,
            'message': '记录使用失败'
        }), 500
