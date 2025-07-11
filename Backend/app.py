from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image
import io
import os
import logging
from datetime import datetime
import traceback
import threading
import time
import uuid

# 导入我们的识别服务
from workerImage import process_image, process_image_with_annotation, process_video_with_annotation, process_images_batch

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)
CORS(app)  # 允许跨域请求，便于前端调用

# 全局变量用于管理正在进行的任务
active_tasks = {}
task_progress = {}
task_lock = threading.Lock()

# 配置上传文件夹
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 限制文件大小为500MB，支持批量处理和视频文件

logger = logging.getLogger(__name__)

# 任务管理函数
def is_task_cancelled(task_id):
    """检查任务是否被取消"""
    with task_lock:
        return active_tasks.get(task_id, {}).get('cancelled', False)

def cancel_task(task_id):
    """取消指定任务"""
    with task_lock:
        if task_id in active_tasks:
            active_tasks[task_id]['cancelled'] = True
            return True
    return False

def register_task(task_id):
    """注册新任务"""
    with task_lock:
        active_tasks[task_id] = {'cancelled': False, 'created_at': time.time()}
        task_progress[task_id] = {
            'current_file_index': 0,
            'total_files': 0,
            'current_file_name': '',
            'current_file_progress': 0,
            'overall_progress': 0,
            'stage': 'starting',  # starting, processing, completed, cancelled
            'start_time': time.time(),
            'processed_files': []
        }

def unregister_task(task_id):
    """注销任务"""
    with task_lock:
        active_tasks.pop(task_id, None)
        task_progress.pop(task_id, None)

def update_task_progress(task_id, **kwargs):
    """更新任务进度"""
    with task_lock:
        if task_id in task_progress:
            task_progress[task_id].update(kwargs)
            # 计算总体进度
            if task_progress[task_id]['total_files'] > 0:
                file_progress = task_progress[task_id]['current_file_index'] / task_progress[task_id]['total_files']
                current_file_progress = task_progress[task_id]['current_file_progress'] / 100.0
                # 当前文件进度占当前文件在总进度中的比重
                if task_progress[task_id]['total_files'] > 0:
                    current_file_weight = 1.0 / task_progress[task_id]['total_files']
                    task_progress[task_id]['overall_progress'] = min(100, 
                        (file_progress + current_file_progress * current_file_weight) * 100)

def get_task_progress(task_id):
    """获取任务进度"""
    with task_lock:
        return task_progress.get(task_id, {}).copy()

# 文件类型检查函数
def allowed_file(filename):
    """检查文件格式是否支持"""
    allowed_extensions = {'png', 'jpg', 'jpeg', 'bmp', 'mp4', 'avi', 'mov', 'mkv', 'wmv'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def is_video_file(filename):
    """检查是否为视频文件"""
    video_extensions = {'mp4', 'avi', 'mov', 'mkv', 'wmv'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in video_extensions

@app.route('/', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({
        'status': 'healthy',
        'service': '电力资产缺陷识别API',
        'version': '1.0.0',
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

@app.route('/api/predict', methods=['POST'])
def predict():
    """
    图片识别预测接口 - 文件上传方式
    """
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': '请选择要上传的文件'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'message': '未选择文件'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'message': '不支持的文件格式，请上传JPG、PNG、BMP格式的图片'}), 400
        
        try:
            # 读取图片
            image = Image.open(io.BytesIO(file.read()))
        except Exception as e:
            return jsonify({'success': False, 'message': f'无法读取图片文件: {str(e)}'}), 400
        
        # 确保图片是RGB格式
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        logger.info(f"接收到图片文件: {file.filename}, 尺寸: {image.size}")
        
        # 调用识别服务
        logger.info("开始进行图片识别...")
        result = process_image(image)
        
        # 返回结果
        logger.info(f"识别成功，检测到 {result['detected_objects']} 个目标，耗时 {result.get('inference_time_ms', 0):.2f}ms")
        return jsonify({
            'success': True,
            'message': '识别完成',
            'filename': file.filename,
            'data': result
        })
            
    except Exception as e:
        error_msg = f"API调用失败: {str(e)}"
        logger.error(f"{error_msg}\n{traceback.format_exc()}")
        return jsonify({
            'success': False,
            'message': error_msg,
            'error': str(e)
        }), 500

@app.route('/api/progress/<task_id>', methods=['GET'])
def get_progress(task_id):
    """获取任务进度"""
    try:
        progress = get_task_progress(task_id)
        if not progress:
            return jsonify({
                'success': False,
                'message': '任务不存在'
            }), 404
        
        return jsonify({
            'success': True,
            'progress': progress
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取进度失败: {str(e)}'
        }), 500

@app.route('/api/cancel/<task_id>', methods=['POST'])
def cancel_batch_task(task_id):
    """取消批量处理任务"""
    try:
        if cancel_task(task_id):
            logger.info(f"任务已取消: {task_id}")
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
        logger.error(f"取消任务失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'取消任务失败: {str(e)}'
        }), 500

@app.route('/api/batch', methods=['POST'])
def batch_predict():
    """
    批量处理接口 - 处理多个文件，支持实时进度反馈
    """
    try:
        # 生成任务ID
        task_id = f"batch_{uuid.uuid4().hex[:8]}"
        register_task(task_id)
        
        if 'files' not in request.files:
            unregister_task(task_id)
            return jsonify({'success': False, 'message': '请选择要上传的文件'}), 400
        
        files = request.files.getlist('files')
        if len(files) == 0:
            unregister_task(task_id)
            return jsonify({'success': False, 'message': '未选择文件'}), 400
        
        # 检查文件数量限制
        if len(files) > 100:
            unregister_task(task_id)
            return jsonify({'success': False, 'message': '最多只能处理100个文件'}), 400
        
        # 检查总文件大小
        file_data_cache = {}  # 缓存文件数据，避免重复读取
        total_size = 0
        
        logger.info(f"开始缓存 {len(files)} 个文件的数据...")
        for i, file in enumerate(files):
            try:
                file.seek(0)
                data = file.read()
                file_data_cache[file.filename] = data
                total_size += len(data)
                logger.info(f"缓存文件 {i+1}/{len(files)}: {file.filename} ({len(data)} bytes)")
            except Exception as e:
                logger.error(f"缓存文件 {file.filename} 失败: {str(e)}")
                unregister_task(task_id)
                return jsonify({'success': False, 'message': f'读取文件失败: {str(e)}'}), 400
        
        logger.info(f"文件缓存完成，总大小: {total_size} bytes")
        
        if total_size > 100 * 1024 * 1024:  # 100MB
            unregister_task(task_id)
            return jsonify({'success': False, 'message': '文件总大小不能超过100MB'}), 400
        
        # 初始化进度
        update_task_progress(task_id, 
                           total_files=len(files), 
                           stage='processing')
        
        # 使用后台线程处理文件，立即返回任务ID
        def process_files_background():
            results = []
            
            try:
                # 分离图片和视频文件
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
                
                logger.info(f"批量处理分类: {len(image_files)} 张图片, {len(video_files)} 个视频")
                
                # 优化：批量处理图片
                if image_files:
                    logger.info(f"开始批量处理 {len(image_files)} 张图片...")
                    
                    try:
                        # 准备图片数据
                        images = []
                        valid_image_filenames = []
                        
                        for i, file in enumerate(image_files):
                            # 检查任务是否被取消
                            if is_task_cancelled(task_id):
                                logger.info(f"任务 {task_id} 被用户取消，停止处理")
                                update_task_progress(task_id, stage='cancelled')
                                return
                            
                            # 更新当前处理文件信息
                            update_task_progress(task_id, 
                                               current_file_index=len(results) + i,
                                               current_file_name=file.filename,
                                               current_file_progress=25)
                            
                            try:
                                # 使用缓存的文件数据
                                image_data = file_data_cache.get(file.filename)
                                if not image_data:
                                    results.append({
                                        'filename': file.filename,
                                        'success': False,
                                        'error': '文件数据缺失'
                                    })
                                    continue
                                
                                # 检查文件是否为空
                                if len(image_data) == 0:
                                    results.append({
                                        'filename': file.filename,
                                        'success': False,
                                        'error': '上传的文件为空'
                                    })
                                    continue
                                
                                # 尝试打开图片
                                image = Image.open(io.BytesIO(image_data))
                                
                                # 验证图片格式
                                if image.format not in ['JPEG', 'PNG', 'BMP', 'WEBP']:
                                    results.append({
                                        'filename': file.filename,
                                        'success': False,
                                        'error': f'不支持的图片格式: {image.format}'
                                    })
                                    continue
                                
                                # 确保图片是RGB格式
                                if image.mode != 'RGB':
                                    image = image.convert('RGB')
                                
                                images.append(image)
                                valid_image_filenames.append(file.filename)
                                
                                logger.info(f"准备图片 {i+1}/{len(image_files)}: {file.filename}, 尺寸: {image.size}")
                                
                            except Exception as e:
                                logger.error(f"准备图片 {file.filename} 失败: {str(e)}")
                                results.append({
                                    'filename': file.filename,
                                    'success': False,
                                    'error': f'无法读取图片文件: {str(e)}'
                                })
                        
                        # 批量处理所有图片
                        if images:
                            update_task_progress(task_id, current_file_progress=50)
                            logger.info(f"开始批量推理 {len(images)} 张图片...")
                            
                            batch_start_time = time.time()
                            # 使用优化的批量处理函数
                            batch_results = process_images_batch(images, return_annotated=True, batch_size=8)
                            batch_time = (time.time() - batch_start_time) * 1000
                            
                            logger.info(f"批量推理完成: {len(images)} 张图片, 耗时: {batch_time:.1f}ms, "
                                      f"平均: {batch_time/len(images):.1f}ms/张")
                            
                            # 处理批量结果
                            for i, (result, filename) in enumerate(zip(batch_results, valid_image_filenames)):
                                update_task_progress(task_id, 
                                                   current_file_index=len(results),
                                                   current_file_name=filename,
                                                   current_file_progress=100)
                                
                                if 'error' in result:
                                    results.append({
                                        'filename': filename,
                                        'success': False,
                                        'error': result['error']
                                    })
                                else:
                                    results.append({
                                        'filename': filename,
                                        'success': True,
                                        'file_type': 'image',
                                        'data': result,
                                        'detected_objects': result['detected_objects'],
                                        'inference_time_ms': result.get('inference_time_ms', 0)
                                    })
                                    
                                    logger.info(f"批量图片处理完成: {filename}, 检测到 {result['detected_objects']} 个目标")
                    
                    except Exception as e:
                        logger.error(f"批量图片处理失败: {str(e)}")
                        # 为剩余图片添加错误结果
                        for filename in image_filenames:
                            if not any(r['filename'] == filename for r in results):
                                results.append({
                                    'filename': filename,
                                    'success': False,
                                    'error': f'批量处理失败: {str(e)}'
                                })
                
                # 逐个处理视频文件（视频较大，不适合批量处理）
                for i, file in enumerate(video_files):
                    # 检查任务是否被取消
                    if is_task_cancelled(task_id):
                        logger.info(f"任务 {task_id} 被用户取消，停止处理")
                        update_task_progress(task_id, stage='cancelled')
                        break
                    
                    # 更新当前处理文件信息
                    update_task_progress(task_id, 
                                       current_file_index=len(results),
                                       current_file_name=file.filename,
                                       current_file_progress=0)
                    
                    try:
                        logger.info(f"批量处理视频: {file.filename}")
                        
                        # 使用缓存的文件数据
                        video_data = file_data_cache.get(file.filename)
                        if not video_data:
                            results.append({
                                'filename': file.filename,
                                'success': False,
                                'error': '文件数据缺失'
                            })
                            continue
                            
                        video_file = io.BytesIO(video_data)
                        
                        # 创建进度回调函数
                        def progress_callback(current_frame, total_frames):
                            if total_frames > 0:
                                progress_percent = (current_frame / total_frames) * 100
                                update_task_progress(task_id, current_file_progress=progress_percent)
                        
                        # 调用视频识别服务，返回带标注的视频，传递任务检查函数和进度回调
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
                        
                        logger.info(f"批量视频处理完成: {file.filename}, 检测到 {result['detected_objects']} 个目标")
                        
                        # 完成当前文件处理
                        update_task_progress(task_id, current_file_progress=100)
                        
                    except Exception as e:
                        logger.error(f"处理视频文件 {file.filename} 失败: {str(e)}")
                        results.append({
                            'filename': file.filename,
                            'success': False,
                            'error': str(e)
                        })
                
                # 处理完成，更新最终进度
                was_cancelled = is_task_cancelled(task_id)
                update_task_progress(task_id, 
                                   current_file_index=len(files),
                                   overall_progress=100,
                                   stage='completed' if not was_cancelled else 'cancelled',
                                   processed_files=results)
                
                # 统计结果
                successful_count = sum(1 for r in results if r['success'])
                failed_count = len(results) - successful_count
                total_detections = sum(r.get('detected_objects', 0) for r in results if r['success'])
                
                # 计算性能统计
                image_count = len(image_files)
                video_count = len(video_files)
                
                logger.info(f"批量处理完成: 成功 {successful_count}/{len(files)} 个文件，失败 {failed_count} 个文件")
                logger.info(f"性能统计: 图片 {image_count} 张, 视频 {video_count} 个, 共检测到 {total_detections} 个目标")
                
            except Exception as e:
                logger.error(f"批量处理失败: {str(e)}")
                update_task_progress(task_id, stage='error', error=str(e))
        
        # 启动后台处理线程
        threading.Thread(target=process_files_background, daemon=True).start()
        
        # 立即返回任务ID，供前端轮询进度
        return jsonify({
            'success': True,
            'message': '批量处理已开始',
            'task_id': task_id
        })
        
    except Exception as e:
        logger.error(f"批量处理启动失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'批量处理失败: {str(e)}'
        }), 500

@app.route('/api/status', methods=['GET'])
def get_status():
    """获取服务状态"""
    try:
        from workerImage import worker, CLASS_MAPPING_ZH
        return jsonify({
            'success': True,
            'service_status': 'running',
            'model_loaded': True,
            'supported_formats': ['jpg', 'jpeg', 'png', 'bmp', 'mp4', 'avi', 'mov', 'mkv', 'wmv'],
            'max_file_size': '500MB',
            'defect_categories': list(CLASS_MAPPING_ZH.values()),
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'service_status': 'error',
            'model_loaded': False,
            'error': str(e)
        }), 500

@app.errorhandler(413)
def file_too_large(error):
    """处理文件过大错误"""
    return jsonify({
        'success': False,
        'message': '文件过大',
        'error': '文件大小不能超过500MB'
    }), 413

@app.errorhandler(404)
def not_found(error):
    """处理404错误"""
    return jsonify({
        'success': False,
        'message': 'API接口不存在',
        'error': '请检查请求URL是否正确'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """处理500错误"""
    return jsonify({
        'success': False,
        'message': '服务器内部错误',
        'error': '请联系系统管理员'
    }), 500

if __name__ == '__main__':
    logger.info("正在启动电力资产缺陷识别API服务...")
    
    # 预先初始化服务（加载模型）
    try:
        from workerImage import worker
        logger.info("模型加载完成，服务启动成功")
    except Exception as e:
        logger.error(f"模型加载失败: {str(e)}")
        exit(1)
    
    # 启动Flask服务
    app.run(
        host='0.0.0.0',  # 允许外部访问
        port=8090,       # 端口号（与前端配置的baseURL对应）
        debug=True,      # 开发模式
        threaded=True    # 支持多线程
    )
