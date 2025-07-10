from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image
import io
import os
import logging
from datetime import datetime
import traceback

# 导入我们的识别服务
from workerImage import process_image

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)
CORS(app)  # 允许跨域请求，便于前端调用

# 配置上传文件夹
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 限制文件大小为16MB

logger = logging.getLogger(__name__)

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
        
        # 读取图片
        image = Image.open(io.BytesIO(file.read()))
        
        # 确保图片是RGB格式
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        logger.info(f"接收到图片文件: {file.filename}, 尺寸: {image.size}")
        
        # 调用识别服务
        logger.info("开始进行图片识别...")
        result = process_image(image)
        
        # 返回结果
        logger.info(f"识别成功，检测到 {result['detected_objects']} 个目标，耗时 {result['inference_time_ms']:.2f}ms")
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

@app.route('/api/predict/file', methods=['POST'])
def predict_file():
    """
    文件上传识别接口（专门处理文件上传）
    """
    try:
        if 'file' not in request.files:
            return jsonify({'error': '请选择要上传的文件'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '未选择文件'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': '不支持的文件格式，请上传JPG、PNG、BMP格式的图片'}), 400
        
        # 保存文件（可选，用于调试）
        if request.form.get('save_file') == 'true':
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{timestamp}_{file.filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.seek(0)  # 重置文件指针
            file.save(filepath)
            logger.info(f"文件已保存: {filepath}")
        
        # 重置文件指针并读取图片
        file.seek(0)
        image = Image.open(io.BytesIO(file.read()))
        
        # 确保图片是RGB格式
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        logger.info(f"接收到图片文件: {file.filename}, 尺寸: {image.size}")
        
        # 进行识别
        result = process_image(image)
        
        logger.info(f"识别完成，检测到 {result['detected_objects']} 个目标，耗时 {result['inference_time_ms']:.2f}ms")
        return jsonify({
            'success': True,
            'message': '识别完成',
            'filename': file.filename,
            'data': result
        })
            
    except Exception as e:
        error_msg = f"文件上传识别失败: {str(e)}"
        logger.error(f"{error_msg}\n{traceback.format_exc()}")
        return jsonify({
            'success': False,
            'message': error_msg,
            'error': str(e)
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
            'supported_formats': ['jpg', 'jpeg', 'png', 'bmp'],
            'max_file_size': '16MB',
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

def allowed_file(filename):
    """检查文件格式是否支持"""
    allowed_extensions = {'png', 'jpg', 'jpeg', 'bmp'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

@app.errorhandler(413)
def file_too_large(error):
    """处理文件过大错误"""
    return jsonify({
        'success': False,
        'message': '文件过大',
        'error': '文件大小不能超过16MB'
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
