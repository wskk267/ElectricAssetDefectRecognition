from flask import Flask
from flask_cors import CORS
import os
import logging
from app.utils.logger import setup_logger
from app.routes.auth import auth_bp
from app.routes.user import user_bp
from app.routes.admin import admin_bp
from app.routes.tasks import tasks_bp
from app.routes.recognition import recognition_bp

def create_app():
    # 配置日志
    setup_logger()
    
    app = Flask(__name__)
    
    # 启用 CORS
    CORS(app)
    
    # 确保上传目录存在
    os.makedirs('uploads', exist_ok=True)
    
    # 注册蓝图
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(user_bp, url_prefix='/api/user')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(tasks_bp, url_prefix='/api/tasks')
    app.register_blueprint(recognition_bp, url_prefix='/api')
    
    @app.route('/')
    def index():
        return "Electric Asset Defect Recognition API is running."
        
    return app
