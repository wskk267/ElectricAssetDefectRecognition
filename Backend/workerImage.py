from inference_sdk import InferenceHTTPClient
from PIL import Image
from ultralytics import YOLO
import os
import logging
from config import Config

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class PowerLineInspectionService:
    """电力线路缺陷识别服务类 - 预加载模型，提供在线识别服务"""
    
    def __init__(self, model_path=None, roboflow_api_key=None):
        """
        初始化识别服务
        
        Args:
            model_path (str): YOLO模型文件路径
            roboflow_api_key (str): Roboflow API密钥
        """
        self.logger = logging.getLogger(__name__)
        self.logger.info("正在初始化电力线路缺陷识别服务...")
        
        # 使用配置文件中的设置
        self.model_path = model_path or Config.YOLO_MODEL_PATH
        self.roboflow_api_key = roboflow_api_key or Config.ROBOFLOW_API_KEY
        self.asset_categories = Config.ASSET_CATEGORIES
        self.defect_status = Config.DEFECT_STATUS
        
        try:
            # 初始化Roboflow客户端（用于目标检测）
            self.roboflow_client = InferenceHTTPClient(
                api_url="https://serverless.roboflow.com",
                api_key=self.roboflow_api_key
            )
            self.logger.info("Roboflow客户端初始化成功")
            
            # 查找可用的模型文件
            available_models = []
            for model_file in [self.model_path, Config.BACKUP_MODEL_PATH, "yolov8n.pt"]:
                if os.path.exists(model_file):
                    available_models.append(model_file)
            
            if not available_models:
                self.logger.warning("未找到任何YOLO模型文件，将使用模拟模式")
                self.yolo_model = None
            else:
                # 使用第一个找到的模型文件
                selected_model = available_models[0]
                self.logger.info(f"找到模型文件: {available_models}")
                self.logger.info(f"使用模型: {selected_model}")
                
                # 加载YOLO模型（用于缺陷分类）
                try:
                    self.yolo_model = YOLO(selected_model)
                    self.logger.info(f"YOLO模型加载成功: {selected_model}")
                except Exception as model_error:
                    self.logger.warning(f"无法加载模型 {selected_model}: {str(model_error)}")
                    self.yolo_model = None
            
            self.logger.info("电力线路缺陷识别服务初始化完成")
            
        except Exception as e:
            self.logger.error(f"服务初始化失败: {str(e)}")
            raise
    
    def predict_image(self, image):
        """
        对图片进行缺陷识别
        
        Args:
            image: PIL.Image对象或图片路径
            
        Returns:
            dict: 识别结果
        """
        try:
            # 如果输入是路径，则加载图片
            if isinstance(image, str):
                image = Image.open(image)
            elif not isinstance(image, Image.Image):
                raise ValueError("输入必须是PIL.Image对象或图片路径")
            
            self.logger.info(f"开始处理图片，尺寸: {image.size}")
            
            # 第一步：使用Roboflow进行目标检测
            detection_result = self.roboflow_client.infer(image, model_id="inspection-of-power-line/1")
            self.logger.info(f"检测到 {len(detection_result['predictions'])} 个目标")
            
            # 第二步：对每个检测到的目标进行缺陷分类
            final_results = []
            
            for i, item in enumerate(detection_result['predictions']):
                try:
                    # 获取边界框坐标
                    cx = item['x']
                    cy = item['y'] 
                    w = item['width']
                    h = item['height']
                    
                    # 计算裁剪区域
                    lx = max(0, int(cx - w/2))
                    ly = max(0, int(cy - h/2))
                    rx = min(image.width, int(cx + w/2))
                    ry = min(image.height, int(cy + h/2))
                    
                    # 裁剪图片
                    cut_img = image.crop((lx, ly, rx, ry))
                    
                    # 使用YOLO进行缺陷分类
                    if self.yolo_model is not None:
                        fault_result = self.yolo_model(cut_img, save=False, verbose=False)
                        
                        # 处理分类结果
                        if len(fault_result[0].boxes) > 0:
                            # 获取置信度
                            confidence = float(fault_result[0].boxes.conf[0].item())
                            
                            # 从Roboflow结果获取资产类别
                            roboflow_class = item.get('class', 'other')
                            
                            # 将Roboflow的类别名映射到我们的资产类别
                            asset_name = self._map_roboflow_class_to_asset(roboflow_class)
                            asset_id = self._get_asset_id_by_name(asset_name)
                            
                            # 模拟缺陷检测（在实际应用中这里应该是真实的缺陷分类逻辑）
                            # 目前使用YOLO的类别ID来模拟缺陷状态
                            cls_id = int(fault_result[0].boxes.cls[0].item())
                            defect_status_id = cls_id % 2  # 简单映射：偶数为正常，奇数为缺陷
                        else:
                            asset_name = '横担悬挂'  # 默认为最后一个类别
                            asset_id = 16
                            defect_status_id = 0  # 默认正常
                            confidence = item.get('confidence', 0.0)
                    else:
                        # 模拟模式：生成测试结果
                        import random
                        
                        # 从Roboflow结果获取资产类别
                        roboflow_class = item.get('class', 'other')
                        asset_name = self._map_roboflow_class_to_asset(roboflow_class)
                        asset_id = self._get_asset_id_by_name(asset_name)
                        
                        defect_status_id = random.randint(0, 1)  # 随机缺陷状态
                        confidence = random.uniform(0.7, 0.95)  # 模拟置信度
                        self.logger.info(f"模拟模式：资产类别 {asset_name}，缺陷状态 {defect_status_id}，置信度 {confidence:.3f}")
                    
                    # 获取缺陷状态
                    defect_status = self.defect_status.get(defect_status_id, '未知')
                    is_defective = defect_status_id == 1
                    
                    # 构建结果（使用YOLO格式的相对坐标）
                    result_item = {
                        'id': i + 1,
                        'center': {
                            'x': round(cx / image.width, 6),  # 相对于图片宽度的比例
                            'y': round(cy / image.height, 6)  # 相对于图片高度的比例
                        },
                        'width': round(w / image.width, 6),   # 相对宽度
                        'height': round(h / image.height, 6), # 相对高度
                        'bbox': {
                            'left': lx,
                            'top': ly, 
                            'right': rx,
                            'bottom': ry
                        },
                        'asset_category': asset_name,
                        'asset_id': asset_id,
                        'defect_status': defect_status,
                        'defect_status_id': defect_status_id,
                        'confidence': round(confidence, 3),
                        'detection_confidence': round(item.get('confidence', 0.0), 3),
                        'isDefective': is_defective
                    }
                    
                    final_results.append(result_item)
                    self.logger.info(f"目标 {i+1}: {asset_name} - {defect_status}, 置信度: {confidence:.3f}")
                    
                except Exception as e:
                    self.logger.error(f"处理第 {i+1} 个目标时出错: {str(e)}")
                    continue
            
            # 返回最终结果
            result = {
                'success': True,
                'image_size': {'width': image.width, 'height': image.height},
                'total_detections': len(final_results),
                'defect_count': sum(1 for r in final_results if r['isDefective']),
                'predictions': final_results,
                'timestamp': str(self.get_timestamp())
            }
            
            self.logger.info(f"识别完成，共检测到 {len(final_results)} 个目标，其中 {result['defect_count']} 个缺陷")
            return result
            
        except Exception as e:
            self.logger.error(f"图片识别失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'predictions': [],
                'timestamp': str(self.get_timestamp())
            }
    
    def _map_roboflow_class_to_asset(self, roboflow_class):
        """
        将Roboflow的英文类别名映射到中文资产类别
        
        Args:
            roboflow_class (str): Roboflow返回的英文类别名
            
        Returns:
            str: 映射后的中文资产类别名
        """
        # 使用配置文件中的映射字典
        return Config.ASSET_NAME_MAPPING.get(roboflow_class, '横担悬挂')  # 默认为最后一个类别
    
    def _get_asset_id_by_name(self, asset_name):
        """
        通过资产名称获取资产ID
        
        Args:
            asset_name (str): 资产名称
            
        Returns:
            int: 资产ID
        """
        for asset_id, name in self.asset_categories.items():
            if name == asset_name:
                return asset_id
        return 16  # 默认为"横担悬挂"
    
    def get_timestamp(self):
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# 创建全局服务实例（在模块加载时初始化，避免重复加载模型）
_service_instance = None

def get_service():
    """获取服务实例（单例模式）"""
    global _service_instance
    if _service_instance is None:
        _service_instance = PowerLineInspectionService()
    return _service_instance

def predict_image(image):
    """
    便捷函数：对图片进行识别
    
    Args:
        image: PIL.Image对象或图片路径
        
    Returns:
        dict: 识别结果
    """
    service = get_service()
    return service.predict_image(image)

# 测试代码
if __name__ == "__main__":
    # 测试服务
    test_image_path = "C://Users//wsk//Desktop//项目//reg//InsPLAD-det//val//309-1_DJI_0065.jpg"
    
    if os.path.exists(test_image_path):
        print("开始测试图片识别服务...")
        result = predict_image(test_image_path)
        
        if result['success']:
            print(f"\n识别成功！")
            print(f"图片尺寸: {result['image_size']}")
            print(f"检测到目标数: {result['total_detections']}")
            print(f"缺陷数量: {result['defect_count']}")
            print("\n详细结果:")
            for pred in result['predictions']:
                print(f"  - {pred['category']}: 置信度 {pred['confidence']}, 位置 ({pred['center']['x']}, {pred['center']['y']})")
        else:
            print(f"识别失败: {result['error']}")
    else:
        print(f"测试图片不存在: {test_image_path}")
        print("请修改test_image_path变量为有效的图片路径")