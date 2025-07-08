"""
配置文件 - 电力资产缺陷识别系统
"""

import os

class Config:
    """基础配置"""
    
    # Flask配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    
    # 文件上传配置
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    UPLOAD_FOLDER = 'uploads'
    
    # 模型配置  
    YOLO_MODEL_PATH = os.environ.get('YOLO_MODEL_PATH') or '../best.pt'  # 使用根目录的模型
    BACKUP_MODEL_PATH = '../best.pt'  # 备用模型路径
    
    # Roboflow配置
    ROBOFLOW_API_KEY = os.environ.get('ROBOFLOW_API_KEY') or 'AyBVVXCDNjwSGfiqIG56'
    ROBOFLOW_MODEL_ID = 'inspection-of-power-line/1'
    
    # API配置
    API_HOST = '0.0.0.0'
    API_PORT = 8090
    DEBUG = True
    
    # 缺陷类别配置（基于InsPLAD数据集的资产类别）
    ASSET_CATEGORIES = {
        0: '螺旋阻尼器',           # Damper ‑ Spiral
        1: '斯托克布里奇阻尼器',    # Damper ‑ Stockbridge
        2: '玻璃绝缘子',          # Glass Insulator
        3: '玻璃绝缘子大卸扣',     # Glass Insulator Big Shackle
        4: '玻璃绝缘子小卸扣',     # Glass Insulator Small Shackle
        5: '玻璃绝缘子塔用卸扣',   # Glass Insulator Tower Shackle
        6: '避雷针卸扣',          # Lightning Rod Shackle
        7: '避雷针悬挂',          # Lightning Rod Suspension
        8: '塔身标识牌',          # Tower ID Plate
        9: '聚合物绝缘子',        # Polymer Insulator
        10: '聚合物绝缘子下卸扣',  # Polymer Insulator Lower Shackle
        11: '聚合物绝缘子上卸扣',  # Polymer Insulator Upper Shackle
        12: '聚合物绝缘子塔用卸扣', # Polymer Insulator Tower Shackle
        13: '间隔棒',            # Spacer
        14: '防振锤',            # Vari‑grip
        15: '横担',              # Yoke
        16: '横担悬挂'           # Yoke Suspension
    }
    
    # 英文到中文的映射字典（用于Roboflow返回结果的翻译）
    ASSET_NAME_MAPPING = {
        'Damper ‑ Spiral': '螺旋阻尼器',
        'Damper ‑ Stockbridge': '斯托克布里奇阻尼器',
        'Glass Insulator': '玻璃绝缘子',
        'Glass Insulator Big Shackle': '玻璃绝缘子大卸扣',
        'Glass Insulator Small Shackle': '玻璃绝缘子小卸扣',
        'Glass Insulator Tower Shackle': '玻璃绝缘子塔用卸扣',
        'Lightning Rod Shackle': '避雷针卸扣',
        'Lightning Rod Suspension': '避雷针悬挂',
        'Tower ID Plate': '塔身标识牌',
        'Polymer Insulator': '聚合物绝缘子',
        'Polymer Insulator Lower Shackle': '聚合物绝缘子下卸扣',
        'Polymer Insulator Upper Shackle': '聚合物绝缘子上卸扣',
        'Polymer Insulator Tower Shackle': '聚合物绝缘子塔用卸扣',
        'Spacer': '间隔棒',
        'Vari‑grip': '防振锤',
        'Yoke': '横担',
        'Yoke Suspension': '横担悬挂'
    }
    
    # 缺陷状态配置
    DEFECT_STATUS = {
        0: '正常',
        1: '缺陷'
    }
    
    # 日志配置
    LOG_LEVEL = 'INFO'
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    
class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    LOG_LEVEL = 'WARNING'

# 配置字典
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
