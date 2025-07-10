from ultralytics import YOLO
import numpy as np
import torch
import time
from PIL import Image

# 类别映射字典 - 英文类别名
CLASS_MAPPING = {
    0: 'yoke', 
    1: 'yoke suspension', 
    2: 'spacer', 
    3: 'stockbridge damper', 
    4: 'lightning rod shackle', 
    5: 'lightning rod suspension', 
    6: 'polymer insulator', 
    7: 'glass insulator', 
    8: 'tower id plate', 
    9: 'vari-grip', 
    10: 'polymer insulator lower shackle', 
    11: 'polymer insulator upper shackle', 
    12: 'polymer insulator tower shackle', 
    13: 'glass insulator big shackle', 
    14: 'glass insulator small shackle', 
    15: 'glass insulator tower shackle', 
    16: 'spiral damper', 
    17: 'sphere'
}

# 中文类别映射字典 - 对应前端显示
CLASS_MAPPING_ZH = {
    0: '横担', 
    1: '横担悬挂', 
    2: '间隔棒', 
    3: '斯托克布里奇阻尼器', 
    4: '避雷针卸扣', 
    5: '避雷针悬挂', 
    6: '聚合物绝缘子', 
    7: '玻璃绝缘子', 
    8: '塔身标识牌', 
    9: '防振锤', 
    10: '聚合物绝缘子下卸扣', 
    11: '聚合物绝缘子上卸扣', 
    12: '聚合物绝缘子塔用卸扣', 
    13: '玻璃绝缘子大卸扣', 
    14: '玻璃绝缘子小卸扣', 
    15: '玻璃绝缘子塔用卸扣', 
    16: '螺旋阻尼器', 
    17: '球'
}

class ImageRecognitionWorker:
    def __init__(self):
        print("正在加载模型...")
        # 设置优化配置
        self._setup_optimization()
        
        # 加载模型
        self.model1 = YOLO("best.pt")
        self.model2 = YOLO("last.pt")
        
        # 模型预热
        self._warmup_models()
        print("模型加载完成并已预热!")
    
    def _setup_optimization(self):
        """设置优化配置"""
        
        print("使用CPU")
        
        # 设置线程数避免争用
        torch.set_num_threads(1)
    
    def _warmup_models(self):
        """模型预热，消除首次推理的延迟"""
        print("正在预热模型...")
        
        # 创建假图像进行预热
        dummy_img = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)
        dummy_pil = Image.fromarray(dummy_img)
        
        # 预热主模型
        for i in range(3):
            _ = self.model1(dummy_pil, save=False, verbose=False)
        
        # 预热子模型
        dummy_crop = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
        dummy_crop_pil = Image.fromarray(dummy_crop)
        for i in range(3):
            _ = self.model2(dummy_crop_pil, save=False, verbose=False)
        
        print("模型预热完成!")
    
    def predict(self, img):
        """执行图像识别预测"""
        start_time = time.time()
        
        # 主模型预测
        result = self.model1(img, save=False, verbose=False)
        predictions = {}
        
        if len(result[0].boxes) == 0:
            return {
                "predictions": predictions,
                "inference_time_ms": (time.time() - start_time) * 1000,
                "detected_objects": 0
            }
        
        for i, box in enumerate(result[0].boxes):
            class_id = int(box.cls.item())
            class_name_en = CLASS_MAPPING.get(class_id, f"unknown_class_{class_id}")
            class_name_zh = CLASS_MAPPING_ZH.get(class_id, f"未知类别_{class_id}")
            
            # 获取边界框信息 (xywh格式，已归一化)
            x, y, w, h = box.xywh[0].tolist()
            
            predictions[i] = {
                "box": [x, y, w, h],
                "center": {"x": x / img.width, "y": y / img.height},  # 转换为相对坐标
                "width": w / img.width,
                "height": h / img.height,
                "class_id": class_id,
                "class_name": class_name_en,
                "class_name_zh": class_name_zh,
                "asset_category": class_name_zh,  # 前端需要的字段
                "confidence": box.conf[0].item()
            }
            
            # 裁剪图像用于子分类
            try:
                # 转换xywh到xyxy格式进行裁剪
                x, y, w, h = box.xywh[0].tolist()
                x1 = max(0, int(x - w/2))
                y1 = max(0, int(y - h/2))
                x2 = min(img.width, int(x + w/2))
                y2 = min(img.height, int(y + h/2))
                
                cimg = img.crop((x1, y1, x2, y2))
                
                # 子模型预测
                pre = self.model2(cimg, save=False, verbose=False)
                
                if len(pre[0].boxes) > 0:
                    subclass_id = int(pre[0].boxes.cls.item())
                    subconfidence = pre[0].boxes.conf[0].item()
                    
                    # 根据子模型预测结果设置缺陷状态
                    # 假设类别0是正常，类别1是缺陷（需要根据实际模型调整）
                    defect_status = "缺陷" if subclass_id == 1 else "正常"
                    
                    predictions[i].update({
                        "subclass_id": subclass_id,
                        "subconfidence": subconfidence,
                        "defect_status": defect_status
                    })
                else:
                    predictions[i].update({
                        "subclass_id": None,
                        "subconfidence": 0.0,
                        "defect_status": "正常"  # 没有检测到结果，默认正常
                    })
                    
            except Exception as e:
                print(f"处理第{i}个检测框时出错: {e}")
                predictions[i].update({
                    "subclass_id": None,
                    "subconfidence": 0.0,
                    "defect_status": "正常",  # 异常情况默认正常
                    "error": str(e)
                })
        
        inference_time = (time.time() - start_time) * 1000
        
        return {
            "predictions": predictions,
            "inference_time_ms": inference_time,
            "detected_objects": len(predictions)
        }

# 全局初始化工作器
print("初始化图像识别服务...")
worker = ImageRecognitionWorker()

def process_image(img):
    """对外接口函数"""
    return worker.predict(img)
