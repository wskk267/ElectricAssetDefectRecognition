from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image
import io
import os
import logging
from datetime import datetime, timedelta
import traceback
import threading
import time
import uuid
import dbutils.pooled_db as dbutils
import pymysql
import hashlib
import secrets
import functools

POOL= dbutils.PooledDB(
    creator=pymysql,
    maxconnections=8,  # 连接池允许的最大连接数
    mincached=2,      # 初始化时，连接池中至少创建的空闲连接数
    maxcached=5,      # 连接池中最多空闲的连接数
    blocking=True,    # 连接池中没有可用连接时是否阻塞等待
    host='localhost',
    port=3306,
    user='root',
    password='123456wushikai',
    database='ead',
    charset='utf8mb4'
)

def fetch_one(sql, params=None):
    """执行查询并返回单条记录"""
    conn = POOL.connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        cursor.execute(sql, params or ())
        result = cursor.fetchone()
        return result
    except Exception as e:
        logging.error(f"数据库查询失败: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def fetch_all(sql, params=None):
    """执行查询并返回所有记录"""
    conn = POOL.connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        cursor.execute(sql, params or ())
        result = cursor.fetchall()
        return result
    except Exception as e:
        logging.error(f"数据库查询失败: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def execute_sql(sql, params=None):
    """执行SQL语句（INSERT, UPDATE, DELETE）"""
    conn = POOL.connection()
    cursor = conn.cursor()
    try:
        cursor.execute(sql, params or ())
        conn.commit()
        # 如果是INSERT语句，返回插入的ID
        if sql.strip().upper().startswith('INSERT'):
            return cursor.lastrowid
        return cursor.rowcount
    except Exception as e:
        conn.rollback()
        logging.error(f"数据库操作失败: {e}")
        return 0
    finally:
        cursor.close()
        conn.close()


def generate_token():
    """生成随机token"""
    return secrets.token_hex(64)

def verify_token(token, user_type='user'):
    """验证token有效性"""
    if not token:
        return None
    
    # 根据用户类型查询对应的表
    table = 'admin' if user_type == 'admin' else 'user'
    sql = f"SELECT * FROM {table} WHERE token = %s"
    result = fetch_one(sql, (token,))
    
    if not result:
        return None
    
    # 检查token是否过期（3天）
    if result['update_time']:
        time_diff = datetime.now() - result['update_time']
        if time_diff > timedelta(days=3):
            return None
    
    return result

def require_auth(user_type='user'):
    """装饰器：要求用户认证"""
    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            token = request.headers.get('Authorization')
            if token and token.startswith('Bearer '):
                token = token[7:]  # 移除 'Bearer ' 前缀
            
            user_info = verify_token(token, user_type)
            if not user_info:
                return jsonify({
                    'success': False,
                    'message': '认证失败，请重新登录'
                }), 401
            
            # 将用户信息传递给路由函数
            return f(user_info, *args, **kwargs)
        return decorated_function
    return decorator

def log_user_action(user_id, action_class, quantity, remain):
    """记录用户操作日志"""
    try:
        sql = """
        INSERT INTO user_log (user_id, time, class, quantity, remain)
        VALUES (%s, %s, %s, %s, %s)
        """
        execute_sql(sql, (user_id, datetime.now(), action_class, quantity, remain))
    except Exception as e:
        logging.error(f"记录用户日志失败: {e}")

def log_admin_action(admin_id, log_message):
    """记录管理员操作日志"""
    try:
        sql = """
        INSERT INTO admin_log (user_id, time, log)
        VALUES (%s, %s, %s)
        """
        execute_sql(sql, (admin_id, datetime.now(), log_message))
    except Exception as e:
        logging.error(f"记录管理员日志失败: {e}")

def update_user_limit(user_id, limit_type, delta):
    """更新用户限制次数"""
    try:
        # 获取当前用户信息
        user = fetch_one("SELECT * FROM user WHERE id = %s", (user_id,))
        if not user:
            return False, "用户不存在"
        
        # 检查是否为无限制用户
        current_limit = user[limit_type]
        if current_limit == -1:  # 无限制用户
            return True, current_limit
        
        # 检查余量是否足够
        if current_limit + delta < 0:
            return False, "余量不足"
        
        # 更新限制次数
        new_limit = current_limit + delta
        sql = f"UPDATE user SET {limit_type} = %s WHERE id = %s"
        execute_sql(sql, (new_limit, user_id))
        
        return True, new_limit
    except Exception as e:
        logging.error(f"更新用户限制失败: {e}")
        return False, str(e)

# 导入我们的识别服务
from workerImage import process_image, process_video_with_annotation, process_images_batch

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)
# 配置CORS允许前端访问
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:5173", "http://localhost:5174", "http://127.0.0.1:5173", "http://127.0.0.1:5174"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# 全局变量用于管理正在进行的任务
active_tasks = {}
task_progress = {}
task_lock = threading.Lock()

# 配置上传文件夹
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024

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
@require_auth('user')
def predict(user_info):
    """
    图片识别预测接口 - 文件上传方式（需要用户认证）
    """
    try:
        # 检查用户图片识别权限
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
            # 读取图片
            image = Image.open(io.BytesIO(file.read()))
        except Exception as e:
            return jsonify({'success': False, 'message': f'无法读取图片文件: {str(e)}'}), 400
        
        # 确保图片是RGB格式
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        logger.info(f"用户{user_info['username']}接收到图片文件: {file.filename}, 尺寸: {image.size}")
        
        # 调用识别服务
        logger.info("开始进行图片识别...")
        result = process_image(image)
        
        # 扣除用户次数（如果不是无限制用户）
        remaining_limit = -1  # 默认为无限制
        if user_info['imagelimit'] != -1:
            success, new_limit = update_user_limit(user_info['id'], 'imagelimit', -1)
            if success:
                # 记录用户操作日志
                log_user_action(user_info['id'], 1, 1, new_limit)
                logger.info(f"用户{user_info['username']}图片识别次数扣除1，剩余{new_limit}次")
                remaining_limit = new_limit
            else:
                logger.error(f"用户{user_info['username']}次数扣除失败: {new_limit}")
                remaining_limit = 0
        else:
            # 无限制用户也要记录操作日志
            log_user_action(user_info['id'], 1, 1, -1)
            logger.info(f"用户{user_info['username']}(无限制)图片识别完成")
        
        # 返回结果
        logger.info(f"识别成功，检测到 {result['detected_objects']} 个目标，耗时 {result.get('inference_time_ms', 0):.2f}ms")
        
        return jsonify({
            'success': True,
            'message': '识别完成',
            'filename': file.filename,
            'data': result,
            'remaining_limit': remaining_limit
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
@require_auth('user')
def batch_predict(user_info):
    """
    批量处理接口 - 处理多个文件，支持实时进度反馈（需要用户认证）
    流量计费：根据文件大小(MB)扣除相应额度
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
        
        # 检查总文件大小并计算所需流量
        file_data_cache = {}  # 缓存文件数据，避免重复读取
        total_size_bytes = 0
        
        logger.info(f"用户{user_info['username']}开始缓存 {len(files)} 个文件的数据...")
        for i, file in enumerate(files):
            try:
                file.seek(0)
                data = file.read()
                file_data_cache[file.filename] = data
                total_size_bytes += len(data)
                logger.info(f"缓存文件 {i+1}/{len(files)}: {file.filename} ({len(data)} bytes)")
            except Exception as e:
                logger.error(f"缓存文件 {file.filename} 失败: {str(e)}")
                unregister_task(task_id)
                return jsonify({'success': False, 'message': f'读取文件失败: {str(e)}'}), 400
        
        # 计算所需流量 (MB)
        total_size_mb = total_size_bytes / (1024 * 1024)
        required_quota = round(total_size_mb, 3)  # 保留3位小数
        
        logger.info(f"文件缓存完成，总大小: {total_size_bytes} bytes ({total_size_mb:.3f} MB), 需要流量: {required_quota:.3f} MB")
        
        # 检查文件大小限制
        if total_size_bytes > 100 * 1024 * 1024:  # 100MB
            unregister_task(task_id)
            return jsonify({'success': False, 'message': '文件总大小不能超过100MB'}), 400
        
        # 检查用户流量是否足够
        if user_info['batchlimit'] != -1:  # 不是无限制用户
            if user_info['batchlimit'] < required_quota:
                unregister_task(task_id)
                return jsonify({
                    'success': False, 
                    'message': f'流量不足！需要 {required_quota:.3f} MB，剩余 {user_info["batchlimit"]:.3f} MB',
                    'error_type': 'quota_exceeded',
                    'required_quota': round(required_quota, 3),
                    'remaining_quota': round(user_info['batchlimit'], 3)
                }), 403
        
        # 初始化进度
        update_task_progress(task_id, 
                           total_files=len(files), 
                           stage='processing')
        
        # 使用后台线程处理文件，立即返回任务ID
        def process_files_background():
            results = []
            # 实际使用的流量就是提交的文件总大小
            actual_quota_used = round(required_quota, 3)  # 保留3位小数
            
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
                
                # 优化：批量处理图片，分批进行以提供更好的进度反馈
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
                            
                            # 更新当前处理文件信息（仅更新文件名，准备阶段不更新进度）
                            update_task_progress(task_id, 
                                               current_file_name=f"准备图片: {file.filename}")
                            
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
                        
                        # 分批处理图片，每批提供进度反馈
                        if images:
                            batch_size = 8
                            total_batches = (len(images) + batch_size - 1) // batch_size
                            
                            logger.info(f"开始分批推理 {len(images)} 张图片，分为 {total_batches} 批，每批 {batch_size} 张")
                            
                            for batch_idx in range(total_batches):
                                # 检查任务是否被取消
                                if is_task_cancelled(task_id):
                                    logger.info(f"任务 {task_id} 被用户取消，停止处理")
                                    update_task_progress(task_id, stage='cancelled')
                                    return
                                
                                start_idx = batch_idx * batch_size
                                end_idx = min(start_idx + batch_size, len(images))
                                batch_images = images[start_idx:end_idx]
                                batch_filenames = valid_image_filenames[start_idx:end_idx]
                                
                                logger.info(f"处理第 {batch_idx + 1}/{total_batches} 批图片，包含 {len(batch_images)} 张图片")
                                
                                batch_start_time = time.time()
                                # 使用优化的批量处理函数
                                batch_results = process_images_batch(batch_images, return_annotated=True, batch_size=batch_size)
                                batch_time = (time.time() - batch_start_time) * 1000
                                
                                logger.info(f"第 {batch_idx + 1} 批推理完成: {len(batch_images)} 张图片, 耗时: {batch_time:.1f}ms")
                                
                                # 处理当前批次结果并立即更新进度
                                for i, (result, filename) in enumerate(zip(batch_results, batch_filenames)):
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
                                        
                                        logger.info(f"图片处理完成: {filename}, 检测到 {result['detected_objects']} 个目标")
                                    
                                    # 每张图片处理完立即更新进度
                                    current_index = len(results)  # 已处理的文件数
                                    total_files = len(image_files) + len(video_files)  # 总文件数
                                    overall_progress = (current_index / total_files) * 100 if total_files > 0 else 0
                                    
                                    # 更新进度
                                    update_task_progress(task_id, 
                                                       current_file_index=current_index,
                                                       current_file_name=filename,
                                                       current_file_progress=100,
                                                       overall_progress=overall_progress)
                    
                    except Exception as e:
                        logger.error(f"批量图片处理失败: {str(e)}")
                        # 为剩余图片添加错误结果并更新进度
                        for filename in image_filenames:
                            if not any(r['filename'] == filename for r in results):
                                results.append({
                                    'filename': filename,
                                    'success': False,
                                    'error': f'批量处理失败: {str(e)}'
                                })
                                
                                # 每个失败的文件也需要更新进度
                                current_index = len(results)
                                total_files = len(image_files) + len(video_files)
                                overall_progress = (current_index / total_files) * 100 if total_files > 0 else 0
                                
                                update_task_progress(task_id, 
                                                   current_file_index=current_index,
                                                   current_file_name=filename,
                                                   current_file_progress=100,
                                                   overall_progress=overall_progress)
                
                # 逐个处理视频文件（视频较大，不适合批量处理）
                for i, file in enumerate(video_files):
                    # 检查任务是否被取消
                    if is_task_cancelled(task_id):
                        logger.info(f"任务 {task_id} 被用户取消，停止处理")
                        update_task_progress(task_id, stage='cancelled')
                        break
                    
                    # 注意：这里不应该先计算current_file_index，应该等处理完成后再更新
                    total_files = len(image_files) + len(video_files)
                    
                    # 更新当前处理文件信息，但不改变file_index
                    current_completed = len(results)  # 当前已完成的文件数
                    update_task_progress(task_id, 
                                       current_file_name=file.filename,
                                       current_file_progress=0)
                    
                    try:
                        logger.info(f"开始处理视频: {file.filename} ({i+1}/{len(video_files)})")
                        
                        # 使用缓存的文件数据
                        video_data = file_data_cache.get(file.filename)
                        if not video_data:
                            results.append({
                                'filename': file.filename,
                                'success': False,
                                'error': '文件数据缺失'
                            })
                            # 即使失败也要更新进度
                            current_completed = len(results)
                            overall_progress = (current_completed / total_files) * 100 if total_files > 0 else 0
                            update_task_progress(task_id, 
                                               current_file_index=current_completed,
                                               current_file_name=file.filename,
                                               current_file_progress=100,
                                               overall_progress=overall_progress)
                            continue
                            
                        video_file = io.BytesIO(video_data)
                        
                        # 创建进度回调函数
                        def progress_callback(current_frame, total_frames):
                            if total_frames > 0:
                                progress_percent = (current_frame / total_frames) * 100
                                # 计算当前整体进度，基于已完成文件 + 当前文件进度
                                current_completed_files = len(results)
                                base_progress = (current_completed_files / total_files) * 100 if total_files > 0 else 0
                                file_weight = (1 / total_files) * 100 if total_files > 0 else 0
                                overall_progress = base_progress + (progress_percent / 100) * file_weight
                                
                                update_task_progress(task_id, 
                                                   current_file_progress=progress_percent,
                                                   overall_progress=overall_progress)
                        
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
                        
                        logger.info(f"视频处理完成: {file.filename}, 检测到 {result['detected_objects']} 个目标")
                        
                        # 视频处理完成后才更新文件索引和进度
                        current_completed = len(results)
                        overall_progress = (current_completed / total_files) * 100 if total_files > 0 else 0
                        
                        update_task_progress(task_id, 
                                           current_file_index=current_completed,
                                           current_file_name=file.filename,
                                           current_file_progress=100,
                                           overall_progress=overall_progress)
                        
                    except Exception as e:
                        logger.error(f"处理视频文件 {file.filename} 失败: {str(e)}")
                        results.append({
                            'filename': file.filename,
                            'success': False,
                            'error': str(e)
                        })
                        
                        # 即使失败也要更新进度
                        current_completed = len(results)
                        overall_progress = (current_completed / total_files) * 100 if total_files > 0 else 0
                        
                        update_task_progress(task_id, 
                                           current_file_index=current_completed,
                                           current_file_name=file.filename,
                                           current_file_progress=100,
                                           overall_progress=overall_progress)
                
                # 处理完成，更新最终进度
                was_cancelled = is_task_cancelled(task_id)
                total_files = len(image_files) + len(video_files)
                
                # 计算实际使用的流量（基于成功处理的文件）
                successful_results = [r for r in results if r['success']]
                quota_used = 0.0  # 初始化实际使用的流量计数器
                if successful_results:
                    # 计算成功处理文件的总大小
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
                
                # 只有在成功处理至少一个文件时才扣除用户流量
                if not was_cancelled and actual_quota_used > 0:
                    # 扣除用户批量处理流量（如果不是无限制用户）
                    if user_info['batchlimit'] != -1:
                        success, new_limit = update_user_limit(user_info['id'], 'batchlimit', -actual_quota_used)
                        if success:
                            # 记录用户操作日志（记录处理的文件大小，单位MB）
                            log_user_action(user_info['id'], 2, actual_quota_used, new_limit)
                            logger.info(f"用户{user_info['username']}批量处理流量扣除{actual_quota_used:.3f}MB，剩余{new_limit:.3f}MB")
                        else:
                            logger.error(f"用户{user_info['username']}流量扣除失败: {new_limit}")
                    else:
                        # 无限制用户也记录日志
                        log_user_action(user_info['id'], 2, actual_quota_used, -1)
                        logger.info(f"用户{user_info['username']}批量处理使用流量{actual_quota_used:.3f}MB（无限制用户）")
                elif was_cancelled:
                    logger.info(f"批量处理被取消，不扣除流量")
                else:
                    logger.info(f"批量处理无成功文件，不扣除流量")
                
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
        # 注意：这里返回的是预计的剩余流量，实际扣除在后台完成后进行
        if user_info['batchlimit'] == -1:
            remaining_quota = -1  # 无限制
        else:
            remaining_quota = round(max(0, user_info['batchlimit'] - required_quota), 3)  # 预计剩余流量，保留3位小数
        
        return jsonify({
            'success': True,
            'message': f'批量处理已开始，预计消耗流量 {required_quota:.3f} MB',
            'task_id': task_id,
            'required_quota': round(required_quota, 3),
            'remaining_quota': remaining_quota
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

@app.route('/api/login', methods=['POST'])
def login():
    """用户登录接口"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': '请求数据格式错误'}), 400
        
        username = data.get('username')
        password_hash = data.get('password')
        user_type = data.get('user_type', 'user') 
        
        if not username or not password_hash:
            return jsonify({'success': False, 'message': '用户名和密码不能为空'}), 400
        
        
        # 根据用户类型查询对应表
        table = 'admin' if user_type == 'admin' else 'user'
        sql = f"SELECT * FROM {table} WHERE username = %s AND pw = %s"
        user = fetch_one(sql, (username, password_hash))
        
        if not user:
            return jsonify({'success': False, 'message': '用户名或密码错误'}), 401
        
        # 生成新token并更新登录时间
        new_token = generate_token()
        update_sql = f"UPDATE {table} SET token = %s, update_time = %s WHERE id = %s"
        execute_sql(update_sql, (new_token, datetime.now(), user['id']))
        
        # 返回登录成功信息
        response_data = {
            'success': True,
            'message': '登录成功',
            'token': new_token,
            'user_id': user['id'],
            'username': user['username'],
            'user_type': user_type
        }
        
        # 如果是普通用户，返回权限信息
        if user_type == 'user':
            response_data.update({
                'imagelimit': user['imagelimit'],
                'batchlimit': user['batchlimit'],
                'realtimePermission': user['realtimePermission']
            })
        
        logging.info(f"用户登录成功: {username} ({user_type})")
        return jsonify(response_data)
        
    except Exception as e:
        logging.error(f"登录失败: {str(e)}")
        return jsonify({'success': False, 'message': f'登录失败: {str(e)}'}), 500

@app.route('/api/register', methods=['POST'])
def register():
    """用户注册接口"""
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
        
        # 检查用户名是否已存在
        existing_user = fetch_one("SELECT id FROM user WHERE username = %s", (username,))
        if existing_user:
            return jsonify({'success': False, 'message': '用户名已存在'}), 400
        
        # SHA256加密密码
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        # 创建新用户
        sql = """
        INSERT INTO user (username, pw, imagelimit, batchlimit, realtimePermission, isbannd)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        result = execute_sql(sql, (username, password_hash, 10, 5, 0, 0))
        
        if result > 0:
            logging.info(f"新用户注册成功: {username}")
            return jsonify({'success': True, 'message': '注册成功'})
        else:
            return jsonify({'success': False, 'message': '注册失败'}), 500
            
    except Exception as e:
        logging.error(f"注册失败: {str(e)}")
        return jsonify({'success': False, 'message': f'注册失败: {str(e)}'}), 500

@app.route('/api/user/info', methods=['GET'])
@require_auth('user')
def get_user_info(user_info):
    """获取用户信息"""
    try:
        # 查询图片识别使用次数
        image_used_result = fetch_one("""
            SELECT COUNT(*) as count FROM operation_logs 
            WHERE user_id = %s AND operation_type = 'image_recognition'
        """, (user_info['id'],))
        image_used = image_used_result['count'] if image_used_result else 0
        
        # 查询批量处理使用次数
        batch_used_result = fetch_one("""
            SELECT COUNT(*) as count FROM operation_logs 
            WHERE user_id = %s AND operation_type = 'batch_processing'
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
                'imageUsed': image_used,
                'batchUsed': batch_used,
                'update_time': user_info['update_time'].strftime('%Y-%m-%d %H:%M:%S') if user_info['update_time'] else None
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/user/logs', methods=['GET'])
@require_auth('user')
def get_user_logs(user_info):
    """获取用户操作日志"""
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))
        offset = (page - 1) * limit
        
        # 获取日志列表
        logs_sql = """
        SELECT * FROM user_log 
        WHERE user_id = %s 
        ORDER BY time DESC 
        LIMIT %s OFFSET %s
        """
        logs = fetch_all(logs_sql, (user_info['id'], limit, offset))
        
        # 获取总数
        count_sql = "SELECT COUNT(*) as total FROM user_log WHERE user_id = %s"
        total_result = fetch_one(count_sql, (user_info['id'],))
        total = total_result['total'] if total_result else 0
        
        # 格式化日志
        formatted_logs = []
        for log in logs:
            action_type = {1: '图片识别', 2: '批量处理', 3: '实时检测'}.get(log['class'], '未知操作')
            formatted_logs.append({
                'id': log['id'],
                'time': log['time'].strftime('%Y-%m-%d %H:%M:%S'),
                'action_type': action_type,
                'quantity': log['quantity'],
                'remain': log['remain']
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

# 管理员接口
@app.route('/api/admin/users', methods=['GET'])
@require_auth('admin')
def admin_get_users(admin_info):
    """管理员获取用户列表"""
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))
        offset = (page - 1) * limit
        
        # 获取用户列表
        users_sql = """
        SELECT id, username, imagelimit, batchlimit, realtimePermission, isbannd, update_time
        FROM user 
        ORDER BY id DESC 
        LIMIT %s OFFSET %s
        """
        users = fetch_all(users_sql, (limit, offset))
        
        # 获取总数
        count_sql = "SELECT COUNT(*) as total FROM user"
        total_result = fetch_one(count_sql)
        total = total_result['total'] if total_result else 0
        
        # 格式化用户信息
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

@app.route('/api/admin/user/<int:user_id>', methods=['PUT'])
@require_auth('admin')
def admin_update_user(admin_info, user_id):
    """管理员更新用户信息"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': '请求数据格式错误'}), 400
        
        # 获取当前用户信息
        user = fetch_one("SELECT * FROM user WHERE id = %s", (user_id,))
        if not user:
            return jsonify({'success': False, 'message': '用户不存在'}), 404
        
        # 构建更新字段
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
        
        # 执行更新
        params.append(user_id)
        sql = f"UPDATE user SET {', '.join(update_fields)} WHERE id = %s"
        result = execute_sql(sql, params)
        
        if result > 0:
            # 记录管理员操作日志
            for message in log_messages:
                log_admin_action(admin_info['id'], message)
            
            return jsonify({'success': True, 'message': '用户信息更新成功'})
        else:
            return jsonify({'success': False, 'message': '更新失败'}), 500
            
    except Exception as e:
        logging.error(f"管理员更新用户失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/admin/logs', methods=['GET'])
@require_auth('admin')
def admin_get_logs(admin_info):
    """管理员获取操作日志"""
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))
        offset = (page - 1) * limit
        
        # 获取日志列表
        logs_sql = """
        SELECT al.*, a.username as admin_username 
        FROM admin_log al
        LEFT JOIN admin a ON al.user_id = a.id
        ORDER BY al.time DESC 
        LIMIT %s OFFSET %s
        """
        logs = fetch_all(logs_sql, (limit, offset))
        
        # 获取总数
        count_sql = "SELECT COUNT(*) as total FROM admin_log"
        total_result = fetch_one(count_sql)
        total = total_result['total'] if total_result else 0
        
        # 格式化日志
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

@app.route('/api/admin/user_logs/<int:user_id>', methods=['GET'])
@require_auth('admin')
def admin_get_user_logs(admin_info, user_id):
    """管理员获取指定用户的操作日志"""
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))
        offset = (page - 1) * limit
        
        # 检查用户是否存在
        user = fetch_one("SELECT username FROM user WHERE id = %s", (user_id,))
        if not user:
            return jsonify({'success': False, 'message': '用户不存在'}), 404
        
        # 获取日志列表
        logs_sql = """
        SELECT * FROM user_log 
        WHERE user_id = %s 
        ORDER BY time DESC 
        LIMIT %s OFFSET %s
        """
        logs = fetch_all(logs_sql, (user_id, limit, offset))
        
        # 获取总数
        count_sql = "SELECT COUNT(*) as total FROM user_log WHERE user_id = %s"
        total_result = fetch_one(count_sql, (user_id,))
        total = total_result['total'] if total_result else 0
        # 格式化日志
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

@app.route('/api/realtime', methods=['POST'])
@require_auth('user')
def realtime_detect(user_info):
    """实时检测接口"""
    try:
        # 检查用户实时检测权限
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
            # 读取图片
            image = Image.open(io.BytesIO(file.read()))
        except Exception as e:
            return jsonify({'success': False, 'message': f'无法读取图片文件: {str(e)}'}), 400
        
        # 确保图片是RGB格式
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        logger.info(f"用户{user_info['username']}实时检测文件: {file.filename}, 尺寸: {image.size}")
        
        # 调用识别服务，返回带标注的图片
        result = process_image(image, return_annotated=True)
        
        # 记录用户操作日志（实时检测不扣减次数，但记录日志）
        log_user_action(user_info['id'], 3, 0, user_info['realtimePermission'])
        
        # 返回结果
        logger.info(f"实时检测完成，检测到 {result.get('detected_objects', 0)} 个目标")
        return jsonify({
            'success': True,
            'message': '实时检测完成',
            'filename': file.filename,
            'data': result
        })
            
    except Exception as e:
        error_msg = f"实时检测失败: {str(e)}"
        logger.error(f"{error_msg}\n{traceback.format_exc()}")
        return jsonify({
            'success': False,
            'message': error_msg,
            'error': str(e)
        }), 500

@app.route('/api/admin/user/<int:user_id>/limits', methods=['POST'])
@require_auth('admin')
def admin_adjust_user_limits(admin_info, user_id):
    """管理员调整用户次数"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': '请求数据格式错误'}), 400
        
        # 获取当前用户信息
        user = fetch_one("SELECT * FROM user WHERE id = %s", (user_id,))
        if not user:
            return jsonify({'success': False, 'message': '用户不存在'}), 404
        
        # 调整图片识别次数
        if 'imagelimit_delta' in data:
            delta = int(data['imagelimit_delta'])
            if user['imagelimit'] != -1:  # 如果不是无限制用户
                new_limit = max(0, user['imagelimit'] + delta)
                execute_sql("UPDATE user SET imagelimit = %s WHERE id = %s", (new_limit, user_id))
                if delta > 0:
                    log_admin_action(admin_info['id'], f"管理员{admin_info['id']}为用户{user_id}的图片识别次数+{delta}")
                else:
                    log_admin_action(admin_info['id'], f"管理员{admin_info['id']}为用户{user_id}的图片识别次数{delta}")
        
        # 调整批量处理次数
        if 'batchlimit_delta' in data:
            delta = int(data['batchlimit_delta'])
            if user['batchlimit'] != -1:  # 如果不是无限制用户
                new_limit = max(0, user['batchlimit'] + delta)
                execute_sql("UPDATE user SET batchlimit = %s WHERE id = %s", (new_limit, user_id))
                if delta > 0:
                    log_admin_action(admin_info['id'], f"管理员{admin_info['id']}为用户{user_id}的批量处理次数+{delta}")
                else:
                    log_admin_action(admin_info['id'], f"管理员{admin_info['id']}为用户{user_id}的批量处理次数{delta}")
        
        return jsonify({'success': True, 'message': '用户次数调整成功'})
        
    except Exception as e:
        logging.error(f"管理员调整用户次数失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/admin/statistics', methods=['GET'])
@require_auth('admin')
def admin_get_statistics(admin_info):
    """管理员获取系统统计信息"""
    try:
        # 用户总数
        user_count_result = fetch_one("SELECT COUNT(*) as total FROM user")
        user_count = user_count_result['total'] if user_count_result else 0
        
        # 今日活跃用户数（有操作日志的用户）
        today = datetime.now().date()
        active_users_result = fetch_one("""
            SELECT COUNT(DISTINCT user_id) as active 
            FROM user_log 
            WHERE DATE(time) = %s
        """, (today,))
        active_users = active_users_result['active'] if active_users_result else 0
        
        # 今日操作统计
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
            'total_traffic': 0  # 总流量（字节）
        }
        
        for stat in today_stats:
            if stat['class'] == 1:
                today_operations['image_recognition'] = stat['count']
            elif stat['class'] == 2:
                today_operations['batch_processing'] = stat['count']
                today_operations['total_traffic'] = stat['total_quantity'] or 0
            elif stat['class'] == 3:
                today_operations['realtime_detection'] = stat['count']
        
        # 近7天操作趋势
        seven_days_ago = (datetime.now() - timedelta(days=7)).date()
        trend_data = fetch_all("""
            SELECT DATE(time) as date, class, COUNT(*) as count
            FROM user_log 
            WHERE DATE(time) >= %s
            GROUP BY DATE(time), class
            ORDER BY date DESC
        """, (seven_days_ago,))
        
        # 用户权限统计
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

@app.route('/api/change_password', methods=['POST'])
@require_auth()
def change_password(user_info):
    """修改密码接口（用户和管理员通用）"""
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
        
        # 验证旧密码
        old_password_hash = hashlib.sha256(old_password.encode()).hexdigest()
        if user_info['pw'] != old_password_hash:
            return jsonify({'success': False, 'message': '旧密码不正确'}), 400
        
        # 更新密码
        new_password_hash = hashlib.sha256(new_password.encode()).hexdigest()
        table = 'user' if user_type == 'user' else 'admin'
        sql = f"UPDATE {table} SET pw = %s WHERE id = %s"
        result = execute_sql(sql, (new_password_hash, user_info['id']))
        
        if result > 0:
            # 记录日志
            if user_type == 'admin':
                log_admin_action(user_info['id'], f"管理员{user_info['id']}修改了密码")
            
            return jsonify({'success': True, 'message': '密码修改成功'})
        else:
            return jsonify({'success': False, 'message': '密码修改失败'}), 500
            
    except Exception as e:
        logging.error(f"修改密码失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/admin/user', methods=['POST'])
@require_auth('admin')
def create_user(admin_info):
    """管理员创建用户接口"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': '请求数据格式错误'}), 400
        
        username = data.get('username')
        password = data.get('password')  # 已经是SHA256加密后的
        imagelimit = data.get('imagelimit', 100)
        batchlimit = data.get('batchlimit', 10)
        realtimePermission = data.get('realtimePermission', 0)
        
        if not username or not password:
            return jsonify({'success': False, 'message': '用户名和密码不能为空'}), 400
        
        # 检查用户名是否已存在
        existing_user = fetch_one("SELECT id FROM user WHERE username = %s", (username,))
        if existing_user:
            return jsonify({'success': False, 'message': '用户名已存在'}), 409
        
        # 获取下一个ID
        max_id_result = fetch_one("SELECT MAX(id) as max_id FROM user")
        next_id = (max_id_result['max_id'] or 0) + 1
        
        # 创建用户
        sql = """
        INSERT INTO user (id, username, pw, imagelimit, batchlimit, realtimePermission, isbannd, token, update_time) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        result = execute_sql(sql, (
            next_id, username, password, imagelimit, batchlimit, 
            realtimePermission, 0, '', datetime.now()
        ))
        
        if result:
            # 记录管理员日志
            log_admin_action(admin_info['id'], f"创建用户: {username}")
            
            logging.info(f"管理员创建用户成功: {username}")
            return jsonify({
                'success': True, 
                'message': '用户创建成功',
                'data': {'id': next_id, 'username': username}
            })
        else:
            return jsonify({'success': False, 'message': '创建用户失败'}), 500
            
    except Exception as e:
        logging.error(f"创建用户失败: {str(e)}")
        return jsonify({'success': False, 'message': f'创建用户失败: {str(e)}'}), 500

@app.route('/api/admin/user/<int:user_id>', methods=['DELETE'])
@require_auth('admin')
def delete_user(admin_info, user_id):
    """管理员删除用户接口"""
    try:
        # 检查用户是否存在
        user = fetch_one("SELECT username FROM user WHERE id = %s", (user_id,))
        if not user:
            return jsonify({'success': False, 'message': '用户不存在'}), 404
        
        # 防止删除管理员账户
        if user['username'] == 'admin':
            return jsonify({'success': False, 'message': '不能删除管理员账户'}), 403
        
        # 删除用户相关的日志记录
        execute_sql("DELETE FROM user_log WHERE user_id = %s", (user_id,))
        
        # 删除用户
        result = execute_sql("DELETE FROM user WHERE id = %s", (user_id,))
        
        if result:
            # 记录管理员日志
            log_admin_action(admin_info['id'], f"删除用户: {user['username']}")
            
            logging.info(f"管理员删除用户成功: {user['username']}")
            return jsonify({'success': True, 'message': '用户删除成功'})
        else:
            return jsonify({'success': False, 'message': '删除用户失败'}), 500
            
    except Exception as e:
        logging.error(f"删除用户失败: {str(e)}")
        return jsonify({'success': False, 'message': f'删除用户失败: {str(e)}'}), 500

@app.route('/api/admin/user/<int:user_id>/status', methods=['PUT'])
@require_auth('admin')
def toggle_user_status(admin_info, user_id):
    """管理员切换用户状态（封禁/解封）"""
    try:
        data = request.get_json()
        banned = data.get('banned', False)
        
        # 检查用户是否存在
        user = fetch_one("SELECT username FROM user WHERE id = %s", (user_id,))
        if not user:
            return jsonify({'success': False, 'message': '用户不存在'}), 404
        
        # 防止封禁管理员账户
        if user['username'] == 'admin':
            return jsonify({'success': False, 'message': '不能封禁管理员账户'}), 403
        
        # 使用数据库中的isbannd字段来控制用户状态
        ban_status = 1 if banned else 0
        sql = "UPDATE user SET isbannd = %s WHERE id = %s"
        action = "封禁" if banned else "解封"
        
        result = execute_sql(sql, (ban_status, user_id))
        
        if result:
            # 记录管理员日志
            log_admin_action(admin_info['id'], f"{action}用户: {user['username']}")
            
            logging.info(f"管理员{action}用户成功: {user['username']}")
            return jsonify({'success': True, 'message': f'{action}用户成功'})
        else:
            return jsonify({'success': False, 'message': f'{action}用户失败'}), 500
            
    except Exception as e:
        logging.error(f"切换用户状态失败: {str(e)}")
        return jsonify({'success': False, 'message': f'操作失败: {str(e)}'}), 500

@app.route('/api/admin/user_logs/all', methods=['GET'])
@require_auth('admin')
def get_all_user_logs(admin_info):
    """获取所有用户的操作日志"""
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 50))
        offset = (page - 1) * limit
        
        # 获取用户日志（带分页）
        sql = """
        SELECT ul.id, ul.user_id, ul.time, ul.class, ul.quantity, ul.remain, u.username
        FROM user_log ul
        LEFT JOIN user u ON ul.user_id = u.id
        ORDER BY ul.time DESC
        LIMIT %s OFFSET %s
        """
        logs = fetch_all(sql, (limit, offset))
        # 获取总数
        total_sql = "SELECT COUNT(*) as total FROM user_log"
        total_result = fetch_one(total_sql)
        total = total_result['total'] if total_result else 0
        logging.info(f"管理员查询所有用户日志，返回 {len(logs)} 条记录")
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
        logging.error(f"获取用户日志失败: {str(e)}")
        return jsonify({'success': False, 'message': f'获取日志失败: {str(e)}'}), 500

if __name__ == '__main__':
    logger.info("正在启动电力资产缺陷识别API服务...")
    
    # 初始化数据库
    logger.info("初始化数据库...")
    
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
