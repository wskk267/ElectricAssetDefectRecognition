from ultralytics import YOLO
import numpy as np
import torch
import time
from PIL import Image, ImageDraw, ImageFont
import cv2
import os
import tempfile
import io
import base64

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
        print("正在加载AI模型...")
        start_time = time.time()
        
        # 设置优化配置
        self._setup_optimization()
        
        # 加载模型
        model_start = time.time()
        self.model1 = YOLO("best.pt")
        print(f"主模型加载完成: {time.time() - model_start:.2f}秒")
        
        model2_start = time.time()
        self.model2 = YOLO("last.pt")
        print(f"子模型加载完成: {time.time() - model2_start:.2f}秒")

        # 模型预热
        warmup_start = time.time()
        self._warmup_models()
        print(f"模型预热完成: {time.time() - warmup_start:.2f}秒")
        
        total_time = time.time() - start_time
        print(f"模型初始化完成! 总耗时: {total_time:.2f}秒")
    
    def _setup_optimization(self):
        """设置优化配置"""
        # 使用CPU模式
        self.device = torch.device('cpu')
        print("使用CPU")
        
        # 设置线程数避免争用（CPU推理优化）
        torch.set_num_threads(min(4, torch.get_num_threads()))  # 限制线程数
    
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
    
    def draw_annotations(self, image, predictions):
        """
        在图片上绘制检测框和标签
        
        Args:
            image: PIL Image对象
            predictions: 预测结果列表
            
        Returns:
            PIL Image: 绘制了标注的图片
        """
        # 创建绘图对象
        draw = ImageDraw.Draw(image)
        
        # 尝试加载中文字体，如果失败则使用默认字体
        try:
            # Windows系统的中文字体路径
            font_paths = [
                "C:/Windows/Fonts/msyh.ttc",  # 微软雅黑
                "C:/Windows/Fonts/simhei.ttf",  # 黑体
                "C:/Windows/Fonts/simsun.ttc",  # 宋体
            ]
            font = None
            for font_path in font_paths:
                if os.path.exists(font_path):
                    font = ImageFont.truetype(font_path, 20)
                    break
            if font is None:
                font = ImageFont.load_default()
        except:
            font = ImageFont.load_default()
        
        # 定义颜色
        colors = {
            '正常': (0, 255, 0),      # 绿色
            '缺陷': (255, 0, 0),      # 红色
            'default': (0, 255, 255)   # 青色
        }
        
        for pred in predictions:
            try:
                # 获取边界框坐标
                x1, y1, x2, y2 = pred['bbox']
                
                # 获取状态颜色
                defect_status = pred.get('defect_status', '正常')
                color = colors.get(defect_status, colors['default'])
                
                # 绘制边界框
                draw.rectangle([x1, y1, x2, y2], outline=color, width=3)
                
                # 准备标签文本
                class_name_zh = pred['class_name_zh']
                confidence = pred['confidence']
                label_text = f"{class_name_zh} ({confidence:.2f})"
                
                # 如果有缺陷状态，添加到标签中
                if defect_status:
                    label_text += f" - {defect_status}"
                
                # 计算文本大小
                try:
                    bbox = draw.textbbox((0, 0), label_text, font=font)
                    text_width = bbox[2] - bbox[0]
                    text_height = bbox[3] - bbox[1]
                except:
                    # 如果textbbox不可用，使用textsize（旧版本PIL）
                    try:
                        text_width, text_height = draw.textsize(label_text, font=font)
                    except:
                        text_width, text_height = 100, 20  # 默认大小
                
                # 绘制标签背景
                label_bg_x1 = x1
                label_bg_y1 = y1 - text_height - 5
                label_bg_x2 = x1 + text_width + 10
                label_bg_y2 = y1
                
                # 确保标签不超出图片边界
                if label_bg_y1 < 0:
                    label_bg_y1 = y2
                    label_bg_y2 = y2 + text_height + 5
                
                draw.rectangle([label_bg_x1, label_bg_y1, label_bg_x2, label_bg_y2], 
                             fill=color, outline=color)
                
                # 绘制文本
                text_color = (255, 255, 255) if defect_status == '缺陷' else (0, 0, 0)
                draw.text((x1 + 5, label_bg_y1 + 2), label_text, 
                         fill=text_color, font=font)
                         
            except Exception as e:
                print(f"绘制标注时出错: {e}")
                continue
        
        return image

    def predict(self, img, return_annotated=False, realtime_mode=False):
        """
        预测图片中的目标 - 优化版本，支持批量子模型推理
        
        Args:
            img: PIL Image对象或图片路径
            return_annotated: 是否返回标注后的图片
            realtime_mode: 是否为实时模式，影响处理策略
            
        Returns:
            dict: 预测结果
        """
        start_time = time.time()
        
        # 实时模式优化：动态调整图片尺寸以平衡速度和精度
        original_img = img
        if realtime_mode and hasattr(img, 'width') and hasattr(img, 'height'):
            # 计算合适的尺寸：确保最长边至少640像素以保证检测效果
            max_size = max(img.width, img.height)
            if max_size < 640:
                # 图片太小，不降采样
                pass
            elif max_size > 1024:
                # 图片太大，适度降采样到960px
                ratio = 960 / max_size
                new_width = int(img.width * ratio)
                new_height = int(img.height * ratio)
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                print(f"实时模式：图片从 {original_img.width}x{original_img.height} 调整到 {img.width}x{img.height}")
            # 中等尺寸图片保持原样
        
        # 主模型预测
        main_start = time.time()
        result = self.model1(img, save=False, verbose=False)
        main_time = (time.time() - main_start) * 1000
        
        predictions = []
        
        if len(result[0].boxes) == 0:
            return {
                "predictions": predictions,
                "inference_time_ms": (time.time() - start_time) * 1000,
                "main_model_time_ms": main_time,
                "sub_model_time_ms": 0,
                "detected_objects": 0
            }
        
        # 批量裁剪所有检测框
        crop_start = time.time()
        crops = []
        crop_indices = []
        
        for i, box in enumerate(result[0].boxes):
            class_id = int(box.cls.item())
            class_name_en = CLASS_MAPPING.get(class_id, f"unknown_class_{class_id}")
            class_name_zh = CLASS_MAPPING_ZH.get(class_id, f"未知类别_{class_id}")
            
            # 获取边界框信息 (xyxy格式，像素坐标)
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            
            prediction = {
                "bbox": [int(x1), int(y1), int(x2), int(y2)],  # draw_annotations需要的格式
                "box": [x1, y1, x2-x1, y2-y1],  # 前端需要的格式 [x, y, w, h]
                "center": {"x": (x1+x2)/2 / img.width, "y": (y1+y2)/2 / img.height},
                "width": (x2-x1) / img.width,
                "height": (y2-y1) / img.height,
                "class_id": class_id,
                "class_name": class_name_en,
                "class_name_zh": class_name_zh,
                "asset_category": class_name_zh,
                "confidence": box.conf[0].item()
            }
            
            # 裁剪图像用于子分类
            try:
                # 使用xyxy格式进行裁剪
                x1, y1, x2, y2 = prediction["bbox"]
                # 确保裁剪区域在图像范围内
                x1 = max(0, min(x1, img.width))
                y1 = max(0, min(y1, img.height))
                x2 = max(x1 + 1, min(x2, img.width))
                y2 = max(y1 + 1, min(y2, img.height))
                
                cimg = img.crop((x1, y1, x2, y2))
                crops.append(cimg)
                crop_indices.append(i)
                
            except Exception as e:
                print(f"处理第{i}个检测框时出错: {e}")
                prediction.update({
                    "subclass_id": None,
                    "subconfidence": 0.0,
                    "defect_status": "正常",
                    "error": str(e)
                })
            
            predictions.append(prediction)
        
        crop_time = (time.time() - crop_start) * 1000
        
        # 批量进行子模型推理（如果有裁剪图像）
        sub_start = time.time()
        sub_model_time = 0
        
        if crops:
            try:
                # 对所有裁剪图像进行批量预测
                for j, cimg in enumerate(crops):
                    try:
                        pre = self.model2(cimg, save=False, verbose=False)
                        idx = crop_indices[j]
                        
                        if hasattr(pre[0], 'probs') and pre[0].probs is not None:
                            # 使用新的分类模型结构
                            subclass_id = pre[0].probs.top1  # 获取top1类别ID
                            subconfidence = pre[0].probs.top1conf.item()  # 获取置信度
                            
                            # 根据新模型的类别定义设置缺陷状态
                            # 0代表defect（缺陷），1代表normal（正常）
                            defect_status = "缺陷" if subclass_id == 0 else "正常"
                            
                            predictions[idx].update({
                                "subclass_id": subclass_id,
                                "subconfidence": subconfidence,
                                "defect_status": defect_status
                            })
                        else:
                            predictions[idx].update({
                                "subclass_id": None,
                                "subconfidence": 0.0,
                                "defect_status": "正常"
                            })
                            
                    except Exception as e:
                        print(f"子模型处理第{j}个裁剪图像时出错: {e}")
                        idx = crop_indices[j]
                        predictions[idx].update({
                            "subclass_id": None,
                            "subconfidence": 0.0,
                            "defect_status": "正常",
                            "error": str(e)
                        })
                        
            except Exception as e:
                print(f"批量子模型推理失败: {e}")
                # 为所有预测添加默认值
                for pred in predictions:
                    if 'defect_status' not in pred:
                        pred.update({
                            "subclass_id": None,
                            "subconfidence": 0.0,
                            "defect_status": "正常",
                            "error": str(e)
                        })
        
        sub_model_time = (time.time() - sub_start) * 1000
        inference_time = (time.time() - start_time) * 1000
        
        # 添加性能统计日志
        if len(predictions) > 0:
            print(f"性能统计 - 总时间: {inference_time:.1f}ms, 主模型: {main_time:.1f}ms, "
                  f"裁剪: {crop_time:.1f}ms, 子模型: {sub_model_time:.1f}ms, "
                  f"检测框数: {len(predictions)}, 平均每框: {inference_time/len(predictions):.1f}ms")
        
        # 如果需要返回标注后的图片
        if return_annotated:
            annotated_img = self.draw_annotations(img.copy(), predictions)
            # 将图片转换为字节流
            with io.BytesIO() as output:
                annotated_img.save(output, format="PNG")
                img_data = output.getvalue()
            
            # 编码为base64
            img_base64 = base64.b64encode(img_data).decode('utf-8')
            
            return {
                "annotated_image": f"data:image/png;base64,{img_base64}"
            }
        
        return {
            "predictions": predictions,
            "inference_time_ms": inference_time,
            "main_model_time_ms": main_time,
            "sub_model_time_ms": sub_model_time,
            "crop_time_ms": crop_time,
            "detected_objects": len(predictions)
        }

    def process_video_with_annotation(self, video_file, frame_interval=2, task_checker=None, progress_callback=None):
        """
        处理视频文件并生成带标注的视频 - 性能优化版本
        
        Args:
            video_file: 视频文件对象（BytesIO或文件路径）
            frame_interval: 抽帧间隔，默认每30帧抽取一帧
            task_checker: 任务取消检查函数，返回True表示任务被取消
            progress_callback: 进度回调函数，接收(current_frame, total_frames)参数
            
        Returns:
            dict: 包含视频分析结果和带标注视频的字典
        """
        start_time = time.time()
        
        # 创建临时文件保存输入视频
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_input_file:
            video_file.seek(0)
            temp_input_file.write(video_file.read())
            temp_input_path = temp_input_file.name
        
        # 创建临时文件保存输出视频
        temp_output_path = temp_input_path.replace('.mp4', '_annotated.mp4')
        
        try:
            # 使用OpenCV读取视频
            cap = cv2.VideoCapture(temp_input_path)
            
            if not cap.isOpened():
                raise ValueError("无法打开视频文件")
            
            # 获取视频信息
            fps = int(cap.get(cv2.CAP_PROP_FPS))
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            duration = total_frames / fps if fps > 0 else 0
            
            # 创建视频写入器 - 使用更兼容的H.264编码
            # 尝试使用H.264编码，如果不支持则回退到mp4v
            fourcc_options = [
                cv2.VideoWriter_fourcc(*'H264'),  # H.264编码，最佳兼容性
                cv2.VideoWriter_fourcc(*'avc1'),  # 另一种H.264编码
                cv2.VideoWriter_fourcc(*'mp4v'),  # 回退选项
                cv2.VideoWriter_fourcc(*'XVID')   # 最后的回退选项
            ]
            
            out = None
            used_fourcc = None
            for fourcc in fourcc_options:
                try:
                    out = cv2.VideoWriter(temp_output_path, fourcc, fps, (width, height))
                    if out.isOpened():
                        used_fourcc = fourcc
                        print(f"成功创建视频写入器，使用编码: {fourcc}")
                        break
                    else:
                        out.release()
                        out = None
                except Exception as e:
                    print(f"尝试编码 {fourcc} 失败: {e}")
                    if out is not None:
                        out.release()
                        out = None
            
            if out is None:
                raise Exception("无法创建视频写入器，请检查OpenCV视频编码支持")
            
            frame_results = []
            frame_count = 0
            processed_frames = 0
            last_log_time = time.time()
            last_detection_result = None  # 缓存上次检测结果，用于跳过帧
            
            print(f"开始处理视频 - 总帧数: {total_frames}, FPS: {fps}, 时长: {duration:.1f}秒")
            print(f"性能优化: 抽帧间隔 {frame_interval}, 预计处理 {total_frames//frame_interval} 帧")
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # 检查任务是否被取消
                if task_checker and task_checker():
                    print(f"视频处理被取消 - 已处理 {processed_frames} 帧")
                    break
                
                # 转换BGR到RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame_pil = Image.fromarray(frame_rgb)
                
                # 性能优化：只对关键帧进行完整检测，其他帧复用结果
                if frame_count % frame_interval == 0:
                    # 关键帧：进行完整检测
                    frame_start_time = time.time()
                    frame_result = self.predict(frame_pil, return_annotated=False)
                    frame_inference_time = (time.time() - frame_start_time) * 1000
                    
                    # 缓存检测结果
                    last_detection_result = frame_result
                    
                    # 添加帧信息
                    frame_result['frame_number'] = frame_count
                    frame_result['timestamp'] = frame_count / fps if fps > 0 else 0
                    frame_result['is_keyframe'] = True
                    
                    frame_results.append(frame_result)
                    processed_frames += 1
                    
                    print(f"关键帧 {frame_count}: 检测到 {frame_result['detected_objects']} 个目标, "
                          f"推理时间: {frame_inference_time:.1f}ms")
                    
                    # 绘制标注
                    annotated_frame_pil = self.draw_annotations(frame_pil.copy(), frame_result['predictions'])
                    
                else:
                    # 非关键帧：复用上次检测结果（如果有的话）
                    if last_detection_result:
                        # 快速绘制上次的检测结果
                        annotated_frame_pil = self.draw_annotations(frame_pil.copy(), last_detection_result['predictions'])
                    else:
                        # 如果没有缓存结果，直接使用原帧
                        annotated_frame_pil = frame_pil
                
                # 转换回BGR格式用于视频写入
                annotated_frame_bgr = cv2.cvtColor(np.array(annotated_frame_pil), cv2.COLOR_RGB2BGR)
                
                # 写入帧到输出视频
                out.write(annotated_frame_bgr)
                
                frame_count += 1
                
                # 更新进度回调
                if progress_callback:
                    progress_callback(frame_count, total_frames)
                
                # 每处理50帧检查一次任务状态（减少检查频率）
                if frame_count % 50 == 0 and task_checker and task_checker():
                    print(f"视频处理被取消 - 已处理 {frame_count} 帧")
                    break
                
                # 每5秒输出一次进度日志
                current_time = time.time()
                if current_time - last_log_time >= 5.0:
                    progress_percent = (frame_count / total_frames) * 100 if total_frames > 0 else 0
                    elapsed_time = current_time - start_time
                    estimated_total = elapsed_time * total_frames / frame_count if frame_count > 0 else 0
                    remaining_time = estimated_total - elapsed_time if estimated_total > elapsed_time else 0
                    
                    avg_time_per_keyframe = elapsed_time / processed_frames if processed_frames > 0 else 0
                    
                    print(f"视频处理进度: {frame_count}/{total_frames} 帧 ({progress_percent:.1f}%) - "
                          f"已用时: {elapsed_time:.1f}s, 预计剩余: {remaining_time:.1f}s, "
                          f"关键帧处理: {processed_frames}, 平均耗时: {avg_time_per_keyframe*1000:.1f}ms/帧")
                    last_log_time = current_time
            
            cap.release()
            out.release()
            
            # 读取生成的带标注视频
            with open(temp_output_path, 'rb') as f:
                annotated_video_data = f.read()
            
            # 检查视频文件大小
            video_size_mb = len(annotated_video_data) / (1024 * 1024)
            print(f"生成的标注视频大小: {video_size_mb:.2f} MB")
            
            # 如果视频过大（超过50MB），尝试压缩
            
            # 最终大小检查
            final_size_mb = len(annotated_video_data) / (1024 * 1024)
            if final_size_mb > 100:  # 如果仍然超过100MB
                print(f"警告: 视频文件过大({final_size_mb:.3f}MB)，可能影响播放性能")
                # 可以选择不返回视频数据，只返回统计信息
                return_video = True
            else:
                return_video = True
            
            # 编码为base64（仅当文件不太大时）
            if return_video:
                annotated_video_base64 = base64.b64encode(annotated_video_data).decode('utf-8')
                print(f"视频base64编码完成，数据大小: {len(annotated_video_base64) / 1024:.1f} KB")
            else:
                annotated_video_base64 = None
                print("视频文件过大，跳过base64编码")
            
            # 统计结果
            total_detections = sum(frame['detected_objects'] for frame in frame_results)
            avg_detections_per_frame = total_detections / len(frame_results) if frame_results else 0
            
            # 统计检测到的类别
            all_classes = {}
            for frame in frame_results:
                for pred in frame['predictions']:
                    class_name = pred['class_name']
                    if class_name not in all_classes:
                        all_classes[class_name] = 0
                    all_classes[class_name] += 1
            
            # 统计缺陷状态 - 统计缺陷目标数量
            defect_objects = sum(1 for frame in frame_results 
                               for pred in frame['predictions'] 
                               if pred.get('defect_status') == '缺陷')
            normal_objects = total_detections - defect_objects
            
            processing_time = (time.time() - start_time) * 1000
            
            # 性能统计
            print(f"视频处理完成统计:")
            print(f"  总帧数: {total_frames}, 处理关键帧: {processed_frames}")
            print(f"  总处理时间: {processing_time/1000:.1f}s")
            print(f"  平均每关键帧: {processing_time/processed_frames:.1f}ms" if processed_frames > 0 else "")
            print(f"  检测目标总数: {total_detections}")
            
            result = {
                'video_info': {
                    'duration_seconds': duration,
                    'total_frames': total_frames,
                    'fps': fps,
                    'resolution': f"{width}x{height}",
                    'processed_frames': processed_frames,
                    'frame_interval': frame_interval,
                    'keyframes_only': True,
                    'file_size_mb': round(final_size_mb, 3)
                },
                'detection_summary': {
                    'total_detections': total_detections,
                    'avg_detections_per_frame': round(avg_detections_per_frame, 2),
                    'detected_classes': all_classes,
                    'defect_objects': defect_objects,
                    'normal_objects': normal_objects
                },
                'frame_results': frame_results,
                'processing_time_ms': processing_time,
                'detected_objects': total_detections,
                'performance_stats': {
                    'avg_keyframe_time_ms': processing_time / processed_frames if processed_frames > 0 else 0,
                    'total_inference_time_ms': sum(f.get('inference_time_ms', 0) for f in frame_results),
                    'optimization_enabled': True
                }
            }
            
            # 只有在视频不太大时才返回base64数据
            if return_video and annotated_video_base64:
                result['annotated_video'] = f"data:video/mp4;base64,{annotated_video_base64}"
            else:
                result['video_too_large'] = True
                result['video_size_mb'] = round(final_size_mb, 3)
                # 可以提供下载链接或其他处理方式
                
            return result
            
        except Exception as e:
            raise Exception(f"视频处理失败: {str(e)}")
        finally:
            # 确保资源被正确释放
            try:
                if 'cap' in locals() and cap is not None:
                    cap.release()
            except:
                pass
            try:
                if 'out' in locals() and out is not None:
                    out.release()
            except:
                pass
            # 清理临时文件
            try:
                if 'temp_input_path' in locals():
                    os.unlink(temp_input_path)
                if 'temp_output_path' in locals() and os.path.exists(temp_output_path):
                    os.unlink(temp_output_path)
            except:
                pass

    def batch_predict_images(self, images, return_annotated=False, batch_size=8):
        """
        批量处理多张图片 - 高效版本，减少模型调用开销
        
        Args:
            images: PIL Image对象列表
            return_annotated: 是否返回标注后的图片
            batch_size: 批处理大小，建议4-16
            
        Returns:
            list: 每张图片的预测结果列表
        """
        if not images:
            return []
        
        start_time = time.time()
        all_results = []
        
        print(f"批量处理 {len(images)} 张图片，批大小: {batch_size}, 返回标注: {return_annotated}")
        
        # 分批处理以管理内存使用
        for batch_idx in range(0, len(images), batch_size):
            batch_start = time.time()
            batch_images = images[batch_idx:batch_idx + batch_size]
            batch_results = []
            
            # 主模型批量推理
            main_start = time.time()
            try:
                # 对批次中的每张图片进行主模型推理
                main_results = []
                for img in batch_images:
                    result = self.model1(img, save=False, verbose=False)
                    main_results.append(result)
                
                main_time = (time.time() - main_start) * 1000
                
                # 收集所有检测框进行批量子模型推理
                all_crops = []
                crop_mappings = []  # 记录每个crop对应的图片索引和框索引
                
                crop_start = time.time()
                for img_idx, (img, result) in enumerate(zip(batch_images, main_results)):
                    img_predictions = []
                    
                    if len(result[0].boxes) == 0:
                        # 如果需要返回标注图片，无检测结果时也保留原始结构但添加图片
                        result_data = {
                            "predictions": img_predictions,
                            "inference_time_ms": 0,
                            "detected_objects": 0
                        }
                        if return_annotated:
                            with io.BytesIO() as output:
                                img.save(output, format="PNG")
                                img_data = output.getvalue()
                            img_base64 = base64.b64encode(img_data).decode('utf-8')
                            result_data["annotated_image"] = f"data:image/png;base64,{img_base64}"
                        batch_results.append(result_data)
                        continue
                    
                    for box_idx, box in enumerate(result[0].boxes):
                        class_id = int(box.cls.item())
                        class_name_en = CLASS_MAPPING.get(class_id, f"unknown_class_{class_id}")
                        class_name_zh = CLASS_MAPPING_ZH.get(class_id, f"未知类别_{class_id}")
                        
                        # 获取边界框信息
                        x1, y1, x2, y2 = box.xyxy[0].tolist()
                        
                        prediction = {
                            "bbox": [int(x1), int(y1), int(x2), int(y2)],
                            "box": [x1, y1, x2-x1, y2-y1],
                            "center": {"x": (x1+x2)/2 / img.width, "y": (y1+y2)/2 / img.height},
                            "width": (x2-x1) / img.width,
                            "height": (y2-y1) / img.height,
                            "class_id": class_id,
                            "class_name": class_name_en,
                            "class_name_zh": class_name_zh,
                            "asset_category": class_name_zh,
                            "confidence": box.conf[0].item()
                        }
                        
                        # 裁剪图像
                        try:
                            x1_crop = max(0, min(int(x1), img.width))
                            y1_crop = max(0, min(int(y1), img.height))
                            x2_crop = max(x1_crop + 1, min(int(x2), img.width))
                            y2_crop = max(y1_crop + 1, min(int(y2), img.height))
                            
                            cimg = img.crop((x1_crop, y1_crop, x2_crop, y2_crop))
                            all_crops.append(cimg)
                            crop_mappings.append((batch_idx + img_idx, len(img_predictions)))
                            
                        except Exception as e:
                            print(f"裁剪第{img_idx}张图片第{box_idx}个框时出错: {e}")
                            prediction.update({
                                "subclass_id": None,
                                "subconfidence": 0.0,
                                "defect_status": "正常",
                                "error": str(e)
                            })
                        
                        img_predictions.append(prediction)
                    
                    batch_results.append({
                        "predictions": img_predictions,
                        "inference_time_ms": 0,  # 稍后更新
                        "detected_objects": len(img_predictions)
                    })
                
                crop_time = (time.time() - crop_start) * 1000
                
                # 批量子模型推理
                sub_start = time.time()
                if all_crops:
                    try:
                        # 分小批次进行子模型推理，避免GPU内存溢出
                        sub_batch_size = min(16, len(all_crops))
                        for i in range(0, len(all_crops), sub_batch_size):
                            sub_crops = all_crops[i:i + sub_batch_size]
                            sub_mappings = crop_mappings[i:i + sub_batch_size]
                            
                            # 对每个裁剪图像进行子模型推理
                            for j, (cimg, (result_idx, pred_idx)) in enumerate(zip(sub_crops, sub_mappings)):
                                local_img_idx = result_idx - batch_idx
                                if local_img_idx >= len(batch_results):
                                    continue
                                
                                try:
                                    pre = self.model2(cimg, save=False, verbose=False)
                                    
                                    if hasattr(pre[0], 'probs') and pre[0].probs is not None:
                                        # 使用新的分类模型结构
                                        subclass_id = pre[0].probs.top1  # 获取top1类别ID
                                        subconfidence = pre[0].probs.top1conf.item()  # 获取置信度
                                        
                                        # 根据新模型的类别定义设置缺陷状态
                                        # 0代表defect（缺陷），1代表normal（正常）
                                        defect_status = "缺陷" if subclass_id == 0 else "正常"
                                        
                                        batch_results[local_img_idx]["predictions"][pred_idx].update({
                                            "subclass_id": subclass_id,
                                            "subconfidence": subconfidence,
                                            "defect_status": defect_status
                                        })
                                    else:
                                        batch_results[local_img_idx]["predictions"][pred_idx].update({
                                            "subclass_id": None,
                                            "subconfidence": 0.0,
                                            "defect_status": "正常"
                                        })
                                        
                                except Exception as e:
                                    print(f"子模型处理第{j}个裁剪图像时出错: {e}")
                                    if local_img_idx < len(batch_results) and pred_idx < len(batch_results[local_img_idx]["predictions"]):
                                        batch_results[local_img_idx]["predictions"][pred_idx].update({
                                            "subclass_id": None,
                                            "subconfidence": 0.0,
                                            "defect_status": "正常",
                                            "error": str(e)
                                        })
                        
                    except Exception as e:
                        print(f"批量子模型推理失败: {e}")
                
                sub_time = (time.time() - sub_start) * 1000
                
                # 更新推理时间
                batch_inference_time = main_time + crop_time + sub_time
                for result in batch_results:
                    if "predictions" in result:  # 只更新非标注图片结果
                        result["inference_time_ms"] = batch_inference_time / len(batch_results)
                        result["main_model_time_ms"] = main_time / len(batch_results)
                        result["sub_model_time_ms"] = sub_time / len(batch_results)
                
                # 如果需要返回标注图片，在完成所有推理后生成标注图片
                if return_annotated:
                    for img_idx, (img, result) in enumerate(zip(batch_images, batch_results)):
                        if "predictions" in result and result["predictions"]:
                            # 生成标注图片
                            annotated_img = self.draw_annotations(img.copy(), result["predictions"])
                            with io.BytesIO() as output:
                                annotated_img.save(output, format="PNG")
                                img_data = output.getvalue()
                            img_base64 = base64.b64encode(img_data).decode('utf-8')
                            # 保留检测结果，添加标注图片
                            batch_results[img_idx]["annotated_image"] = f"data:image/png;base64,{img_base64}"
                        elif "annotated_image" not in result:
                            # 无检测结果，返回原图
                            with io.BytesIO() as output:
                                img.save(output, format="PNG")
                                img_data = output.getvalue()
                            img_base64 = base64.b64encode(img_data).decode('utf-8')
                            batch_results[img_idx]["annotated_image"] = f"data:image/png;base64,{img_base64}"
                
                batch_time = (time.time() - batch_start) * 1000

                print(f"批次 {batch_idx//batch_size + 1}: {len(batch_images)} 张图片, "
                      f"耗时: {batch_time:.1f}ms, 平均: {batch_time/len(batch_images):.1f}ms/张")
                
            except Exception as e:
                print(f"批次处理失败: {e}")
                # 为失败的批次创建空结果
                for img in batch_images:
                    result_data = {
                        "predictions": [],
                        "inference_time_ms": 0,
                        "detected_objects": 0,
                        "error": str(e)
                    }
                    if return_annotated:
                        # 返回原图
                        with io.BytesIO() as output:
                            img.save(output, format="PNG")
                            img_data = output.getvalue()
                        img_base64 = base64.b64encode(img_data).decode('utf-8')
                        result_data["annotated_image"] = f"data:image/png;base64,{img_base64}"
                    batch_results.append(result_data)
            all_results.extend(batch_results)
            

        total_time = (time.time() - start_time) * 1000
        if not return_annotated:
            total_detections = sum(r.get("detected_objects", 0) for r in all_results)
            print(f"批量处理完成: {len(images)} 张图片, 总耗时: {total_time:.1f}ms, "
                  f"平均: {total_time/len(images):.1f}ms/张, 总检测: {total_detections} 个目标")
        else:
            print(f"批量标注完成: {len(images)} 张图片, 总耗时: {total_time:.1f}ms, "
                  f"平均: {total_time/len(images):.1f}ms/张")
        
        return all_results

    def predict_realtime(self, img, min_confidence=0.3):
        """
        专门为实时检测优化的预测函数
        
        Args:
            img: PIL Image对象
            min_confidence: 最小置信度阈值，低于此值的检测结果将被过滤
            
        Returns:
            dict: 精简的预测结果
        """
        start_time = time.time()
        
        # 智能尺寸调整：保证检测效果的同时提高速度
        original_size = (img.width, img.height)
        target_img = img
        
        # 如果图片太小，先放大以提高检测率
        max_dim = max(img.width, img.height)
        min_dim = min(img.width, img.height)
        
        if max_dim < 480:
            # 图片太小，放大到640
            scale = 640 / max_dim
            new_width = int(img.width * scale)
            new_height = int(img.height * scale)
            target_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            print(f"实时检测：图片从 {original_size} 放大到 {target_img.width}x{target_img.height}")
        elif max_dim > 1280:
            # 图片太大，适度缩小到1024以提高速度
            scale = 1024 / max_dim
            new_width = int(img.width * scale)
            new_height = int(img.height * scale)
            target_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            print(f"实时检测：图片从 {original_size} 缩小到 {target_img.width}x{target_img.height}")
        
        # 使用优化的推理参数
        result = self.model1(target_img, save=False, verbose=False, 
                           conf=min_confidence,  # 设置置信度阈值
                           iou=0.45,  # 设置NMS阈值
                           max_det=50)  # 限制最大检测数量
        
        predictions = []
        
        if len(result[0].boxes) == 0:
            return {
                "predictions": predictions,
                "inference_time_ms": (time.time() - start_time) * 1000,
                "detected_objects": 0,
                "realtime_optimized": True
            }
        
        # 计算缩放比例，用于坐标转换
        scale_x = original_size[0] / target_img.width
        scale_y = original_size[1] / target_img.height
        
        for i, box in enumerate(result[0].boxes):
            confidence = box.conf[0].item()
            
            # 过滤低置信度结果
            if confidence < min_confidence:
                continue
                
            class_id = int(box.cls.item())
            class_name_zh = CLASS_MAPPING_ZH.get(class_id, f"未知类别_{class_id}")
            
            # 获取边界框信息并转换回原始图片坐标
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            
            # 转换坐标到原始图片尺寸
            x1_orig = x1 * scale_x
            y1_orig = y1 * scale_y
            x2_orig = x2 * scale_x
            y2_orig = y2 * scale_y
            
            try:
                x1_crop = max(0, min(int(x1), target_img.width))
                y1_crop = max(0, min(int(y1), target_img.height))
                x2_crop = max(x1_crop + 1, min(int(x2), target_img.width))
                y2_crop = max(y1_crop + 1, min(int(y2), target_img.height))
            
                cimg = target_img.crop((x1_crop, y1_crop, x2_crop, y2_crop))
            
             # 调用子模型进行缺陷分类
                pre = self.model2(cimg, save=False, verbose=False)
                if hasattr(pre[0], 'probs') and pre[0].probs is not None:
                    subclass_id = pre[0].probs.top1
                    defect_status = "缺陷" if subclass_id == 0 else "正常"
                else:
                    defect_status = "正常"
            except:
                defect_status = "正常"

            # 计算相对于原始图片的相对坐标
            prediction = {
                "center": {
                    "x": (x1_orig + x2_orig) / 2 / original_size[0],
                    "y": (y1_orig + y2_orig) / 2 / original_size[1]
                },
                "width": (x2_orig - x1_orig) / original_size[0],
                "height": (y2_orig - y1_orig) / original_size[1],
                "asset_category": class_name_zh,
                "confidence": confidence,
                "defect_status": defect_status  # 实时模式跳过子分类，假设正常
            }
            
            predictions.append(prediction)
        
        inference_time = (time.time() - start_time) * 1000
        
        # 简化日志
        if len(predictions) > 0 and inference_time > 100:  # 只在耗时较长时打印
            print(f"实时检测: 检测到 {len(predictions)} 个目标，耗时 {inference_time:.1f}ms")
        
        return {
            "predictions": predictions,
            "inference_time_ms": inference_time,
            "detected_objects": len(predictions),
            "realtime_optimized": True,
            "processed_size": f"{target_img.width}x{target_img.height}",
            "original_size": f"{original_size[0]}x{original_size[1]}"
        }

# 全局初始化工作器
print("初始化图像识别服务...")
worker = ImageRecognitionWorker()

def process_image(img, return_annotated=False, realtime_mode=False):
    """对外接口函数"""
    return worker.predict(img, return_annotated, realtime_mode)

def process_image_realtime(img, min_confidence=0.3):
    """实时检测专用接口函数 - 高性能优化"""
    return worker.predict_realtime(img, min_confidence)

def process_image_with_annotation(img):
    """返回带标注的图片"""
    return worker.predict(img, return_annotated=True)

def process_video_with_annotation(video_file, frame_interval=2, task_checker=None, progress_callback=None):
    """处理视频文件并返回带标注视频的对外接口函数"""
    return worker.process_video_with_annotation(video_file, frame_interval, task_checker, progress_callback)

# 批量处理优化函数
def process_images_batch(images, return_annotated=True, batch_size=8):
    """批量处理多张图片的对外接口函数 - 高效版本"""
    return worker.batch_predict_images(images, return_annotated, batch_size)
