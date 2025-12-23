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
from concurrent.futures import ThreadPoolExecutor
from queue import Queue

# Class Mappings
CLASS_MAPPING = {
    0: 'yoke', 1: 'yoke suspension', 2: 'spacer', 3: 'stockbridge damper', 
    4: 'lightning rod shackle', 5: 'lightning rod suspension', 6: 'polymer insulator', 
    7: 'glass insulator', 8: 'tower id plate', 9: 'vari-grip', 
    10: 'polymer insulator lower shackle', 11: 'polymer insulator upper shackle', 
    12: 'polymer insulator tower shackle', 13: 'glass insulator big shackle', 
    14: 'glass insulator small shackle', 15: 'glass insulator tower shackle', 
    16: 'spiral damper', 17: 'sphere'
}

CLASS_MAPPING_ZH = {
    0: '横担', 1: '横担悬挂', 2: '间隔棒', 3: '斯托克布里奇阻尼器', 
    4: '避雷针卸扣', 5: '避雷针悬挂', 6: '聚合物绝缘子', 
    7: '玻璃绝缘子', 8: '塔身标识牌', 9: '防振锤', 
    10: '聚合物绝缘子下卸扣', 11: '聚合物绝缘子上卸扣', 
    12: '聚合物绝缘子塔用卸扣', 13: '玻璃绝缘子大卸扣', 
    14: '玻璃绝缘子小卸扣', 15: '玻璃绝缘子塔用卸扣', 
    16: '螺旋阻尼器', 17: '球'
}

class ImageRecognitionWorker:
    def __init__(self):
        print("正在加载 AI 模型...")
        start_time = time.time()
        self._setup_optimization()
        
        model_start = time.time()
        self.model1 = YOLO("best.pt")
        print(f"主模型加载完成: {time.time() - model_start:.2f}s")
        
        model2_start = time.time()
        self.model2 = YOLO("last.pt")
        print(f"子模型加载完成: {time.time() - model2_start:.2f}s")
        
        print(f"模型初始化完成! 总耗时: {time.time() - start_time:.2f}s")
    
    def _setup_optimization(self):
        self.device = torch.device('cpu')
        print("正在使用 CPU")
        torch.set_num_threads(min(4, torch.get_num_threads()))
    
    def draw_annotations(self, image, predictions):
        draw = ImageDraw.Draw(image)
        try:
            font_paths = [
                "C:/Windows/Fonts/msyh.ttc",
                "C:/Windows/Fonts/simhei.ttf",
                "C:/Windows/Fonts/simsun.ttc",
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
        
        colors = {
            '正常': (0, 255, 0),
            '缺陷': (255, 0, 0),
            'default': (0, 255, 255)
        }
        
        for pred in predictions:
            try:
                x1, y1, x2, y2 = pred['bbox']
                defect_status = pred.get('defect_status', '正常')
                color = colors.get(defect_status, colors['default'])
                
                draw.rectangle([x1, y1, x2, y2], outline=color, width=3)
                
                class_name_zh = pred['class_name_zh']
                confidence = pred['confidence']
                label_text = f"{class_name_zh} ({confidence:.2f})"
                
                if defect_status:
                    label_text += f" - {defect_status}"
                
                try:
                    bbox = draw.textbbox((0, 0), label_text, font=font)
                    text_width = bbox[2] - bbox[0]
                    text_height = bbox[3] - bbox[1]
                except:
                    try:
                        text_width, text_height = draw.textsize(label_text, font=font)
                    except:
                        text_width, text_height = 100, 20
                
                label_bg_x1 = x1
                label_bg_y1 = y1 - text_height - 5
                label_bg_x2 = x1 + text_width + 10
                label_bg_y2 = y1
                
                if label_bg_y1 < 0:
                    label_bg_y1 = y2
                    label_bg_y2 = y2 + text_height + 5
                
                draw.rectangle([label_bg_x1, label_bg_y1, label_bg_x2, label_bg_y2], 
                             fill=color, outline=color)
                
                text_color = (255, 255, 255) if defect_status == '缺陷' else (0, 0, 0)
                draw.text((x1 + 5, label_bg_y1 + 2), label_text, 
                         fill=text_color, font=font)
                         
            except Exception as e:
                print(f"Error drawing annotation: {e}")
                continue
        
        return image

    def predict(self, img, return_annotated=False, realtime_mode=False):
        start_time = time.time()
        
        original_img = img
        if realtime_mode and hasattr(img, 'width') and hasattr(img, 'height'):
            max_size = max(img.width, img.height)
            if max_size < 640:
                pass
            elif max_size > 1024:
                ratio = 960 / max_size
                new_width = int(img.width * ratio)
                new_height = int(img.height * ratio)
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
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
        
        crop_start = time.time()
        crops = []
        crop_indices = []
        
        for i, box in enumerate(result[0].boxes):
            class_id = int(box.cls.item())
            class_name_en = CLASS_MAPPING.get(class_id, f"unknown_class_{class_id}")
            class_name_zh = CLASS_MAPPING_ZH.get(class_id, f"未知类别_{class_id}")
            
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
            
            try:
                x1 = max(0, min(x1, img.width))
                y1 = max(0, min(y1, img.height))
                x2 = max(x1 + 1, min(x2, img.width))
                y2 = max(y1 + 1, min(y2, img.height))
                
                cimg = img.crop((x1, y1, x2, y2))
                crops.append(cimg)
                crop_indices.append(i)
                
            except Exception as e:
                print(f"Error cropping box {i}: {e}")
                prediction.update({
                    "subclass_id": None,
                    "subconfidence": 0.0,
                    "defect_status": "正常",
                    "error": str(e)
                })
            
            predictions.append(prediction)
        
        crop_time = (time.time() - crop_start) * 1000
        
        sub_start = time.time()
        sub_model_time = 0
        
        if crops:
            try:
                for j, cimg in enumerate(crops):
                    try:
                        pre = self.model2(cimg, save=False, verbose=False)
                        idx = crop_indices[j]
                        
                        if hasattr(pre[0], 'probs') and pre[0].probs is not None:
                            subclass_id = pre[0].probs.top1
                            subconfidence = pre[0].probs.top1conf.item()
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
                        print(f"Error in sub model for crop {j}: {e}")
                        idx = crop_indices[j]
                        predictions[idx].update({
                            "subclass_id": None,
                            "subconfidence": 0.0,
                            "defect_status": "正常",
                            "error": str(e)
                        })
                        
            except Exception as e:
                print(f"Batch sub model inference failed: {e}")
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
        
        if return_annotated:
            annotated_img = self.draw_annotations(img.copy(), predictions)
            with io.BytesIO() as output:
                annotated_img.save(output, format="PNG")
                img_data = output.getvalue()
            
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
        start_time = time.time()
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_input_file:
            video_file.seek(0)
            temp_input_file.write(video_file.read())
            temp_input_path = temp_input_file.name
        
        temp_output_path = temp_input_path.replace('.mp4', '_annotated.mp4')
        
        try:
            cap = cv2.VideoCapture(temp_input_path)
            
            if not cap.isOpened():
                raise ValueError("Cannot open video file")
            
            fps = int(cap.get(cv2.CAP_PROP_FPS))
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            duration = total_frames / fps if fps > 0 else 0
            
            fourcc_options = [
                cv2.VideoWriter_fourcc(*'H264'),
                cv2.VideoWriter_fourcc(*'avc1'),
                cv2.VideoWriter_fourcc(*'mp4v'),
                cv2.VideoWriter_fourcc(*'XVID')
            ]
            
            out = None
            for fourcc in fourcc_options:
                try:
                    out = cv2.VideoWriter(temp_output_path, fourcc, fps, (width, height))
                    if out.isOpened():
                        break
                    else:
                        out.release()
                        out = None
                except Exception:
                    if out is not None:
                        out.release()
                        out = None
            
            if out is None:
                raise Exception("Cannot create video writer")
            
            frame_results = []
            frame_count = 0
            processed_frames = 0
            last_detection_result = None
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                if task_checker and task_checker():
                    break
                
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame_pil = Image.fromarray(frame_rgb)
                
                if frame_count % frame_interval == 0:
                    frame_result = self.predict(frame_pil, return_annotated=False)
                    last_detection_result = frame_result
                    
                    frame_result['frame_number'] = frame_count
                    frame_result['timestamp'] = frame_count / fps if fps > 0 else 0
                    frame_result['is_keyframe'] = True
                    
                    frame_results.append(frame_result)
                    processed_frames += 1
                    
                    annotated_frame_pil = self.draw_annotations(frame_pil.copy(), frame_result['predictions'])
                    
                else:
                    if last_detection_result:
                        annotated_frame_pil = self.draw_annotations(frame_pil.copy(), last_detection_result['predictions'])
                    else:
                        annotated_frame_pil = frame_pil
                
                annotated_frame_bgr = cv2.cvtColor(np.array(annotated_frame_pil), cv2.COLOR_RGB2BGR)
                out.write(annotated_frame_bgr)
                
                frame_count += 1
                
                if progress_callback:
                    progress_callback(frame_count, total_frames)
                
                if frame_count % 50 == 0 and task_checker and task_checker():
                    break
            
            cap.release()
            out.release()
            
            with open(temp_output_path, 'rb') as f:
                annotated_video_data = f.read()
            
            final_size_mb = len(annotated_video_data) / (1024 * 1024)
            return_video = True
            
            if return_video:
                annotated_video_base64 = base64.b64encode(annotated_video_data).decode('utf-8')
            else:
                annotated_video_base64 = None
            
            total_detections = sum(frame['detected_objects'] for frame in frame_results)
            avg_detections_per_frame = total_detections / len(frame_results) if frame_results else 0
            
            all_classes = {}
            for frame in frame_results:
                for pred in frame['predictions']:
                    class_name = pred['class_name']
                    if class_name not in all_classes:
                        all_classes[class_name] = 0
                    all_classes[class_name] += 1
            
            defect_objects = sum(1 for frame in frame_results 
                               for pred in frame['predictions'] 
                               if pred.get('defect_status') == '缺陷')
            normal_objects = total_detections - defect_objects
            
            processing_time = (time.time() - start_time) * 1000
            
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
            
            if return_video and annotated_video_base64:
                result['annotated_video'] = f"data:video/mp4;base64,{annotated_video_base64}"
            else:
                result['video_too_large'] = True
                result['video_size_mb'] = round(final_size_mb, 3)
                
            return result
            
        except Exception as e:
            raise Exception(f"Video processing failed: {str(e)}")
        finally:
            try:
                if 'cap' in locals() and cap is not None: cap.release()
            except: pass
            try:
                if 'out' in locals() and out is not None: out.release()
            except: pass
            try:
                if 'temp_input_path' in locals(): os.unlink(temp_input_path)
                if 'temp_output_path' in locals() and os.path.exists(temp_output_path): os.unlink(temp_output_path)
            except: pass

    def batch_predict_images(self, images, return_annotated=False, batch_size=8):
        if not images:
            return []
        
        start_time = time.time()
        all_results = []
        
        for batch_idx in range(0, len(images), batch_size):
            batch_start = time.time()
            batch_images = images[batch_idx:batch_idx + batch_size]
            batch_results = []
            
            main_start = time.time()
            try:
                main_results = []
                for img in batch_images:
                    result = self.model1(img, save=False, verbose=False)
                    main_results.append(result)
                
                main_time = (time.time() - main_start) * 1000
                
                all_crops = []
                crop_mappings = []
                
                crop_start = time.time()
                for img_idx, (img, result) in enumerate(zip(batch_images, main_results)):
                    img_predictions = []
                    
                    if len(result[0].boxes) == 0:
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
                        
                        try:
                            x1_crop = max(0, min(int(x1), img.width))
                            y1_crop = max(0, min(int(y1), img.height))
                            x2_crop = max(x1_crop + 1, min(int(x2), img.width))
                            y2_crop = max(y1_crop + 1, min(int(y2), img.height))
                            
                            cimg = img.crop((x1_crop, y1_crop, x2_crop, y2_crop))
                            all_crops.append(cimg)
                            crop_mappings.append((batch_idx + img_idx, len(img_predictions)))
                            
                        except Exception as e:
                            print(f"Error cropping: {e}")
                            prediction.update({
                                "subclass_id": None,
                                "subconfidence": 0.0,
                                "defect_status": "正常",
                                "error": str(e)
                            })
                        
                        img_predictions.append(prediction)
                    
                    batch_results.append({
                        "predictions": img_predictions,
                        "inference_time_ms": 0,
                        "detected_objects": len(img_predictions)
                    })
                
                crop_time = (time.time() - crop_start) * 1000
                
                sub_start = time.time()
                if all_crops:
                    try:
                        sub_batch_size = min(16, len(all_crops))
                        for i in range(0, len(all_crops), sub_batch_size):
                            sub_crops = all_crops[i:i + sub_batch_size]
                            sub_mappings = crop_mappings[i:i + sub_batch_size]
                            
                            for j, (cimg, (result_idx, pred_idx)) in enumerate(zip(sub_crops, sub_mappings)):
                                local_img_idx = result_idx - batch_idx
                                if local_img_idx >= len(batch_results):
                                    continue
                                
                                try:
                                    pre = self.model2(cimg, save=False, verbose=False)
                                    
                                    if hasattr(pre[0], 'probs') and pre[0].probs is not None:
                                        subclass_id = pre[0].probs.top1
                                        subconfidence = pre[0].probs.top1conf.item()
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
                                    print(f"Sub model error: {e}")
                                    if local_img_idx < len(batch_results) and pred_idx < len(batch_results[local_img_idx]["predictions"]):
                                        batch_results[local_img_idx]["predictions"][pred_idx].update({
                                            "subclass_id": None,
                                            "subconfidence": 0.0,
                                            "defect_status": "正常",
                                            "error": str(e)
                                        })
                        
                    except Exception as e:
                        print(f"Batch sub model inference failed: {e}")
                
                sub_time = (time.time() - sub_start) * 1000
                
                batch_inference_time = main_time + crop_time + sub_time
                for result in batch_results:
                    if "predictions" in result:
                        result["inference_time_ms"] = batch_inference_time / len(batch_results)
                        result["main_model_time_ms"] = main_time / len(batch_results)
                        result["sub_model_time_ms"] = sub_time / len(batch_results)
                
                if return_annotated:
                    for img_idx, (img, result) in enumerate(zip(batch_images, batch_results)):
                        if "predictions" in result and result["predictions"]:
                            annotated_img = self.draw_annotations(img.copy(), result["predictions"])
                            with io.BytesIO() as output:
                                annotated_img.save(output, format="PNG")
                                img_data = output.getvalue()
                            img_base64 = base64.b64encode(img_data).decode('utf-8')
                            batch_results[img_idx]["annotated_image"] = f"data:image/png;base64,{img_base64}"
                        elif "annotated_image" not in result:
                            with io.BytesIO() as output:
                                img.save(output, format="PNG")
                                img_data = output.getvalue()
                            img_base64 = base64.b64encode(img_data).decode('utf-8')
                            batch_results[img_idx]["annotated_image"] = f"data:image/png;base64,{img_base64}"
                
            except Exception as e:
                print(f"Batch processing failed: {e}")
                for img in batch_images:
                    result_data = {
                        "predictions": [],
                        "inference_time_ms": 0,
                        "detected_objects": 0,
                        "error": str(e)
                    }
                    if return_annotated:
                        with io.BytesIO() as output:
                            img.save(output, format="PNG")
                            img_data = output.getvalue()
                        img_base64 = base64.b64encode(img_data).decode('utf-8')
                        result_data["annotated_image"] = f"data:image/png;base64,{img_base64}"
                    batch_results.append(result_data)
            all_results.extend(batch_results)
            
        return all_results

    def predict_realtime(self, img, min_confidence=0.3):
        start_time = time.time()
        
        original_size = (img.width, img.height)
        target_img = img
        
        max_dim = max(img.width, img.height)
        
        if max_dim < 480:
            scale = 640 / max_dim
            new_width = int(img.width * scale)
            new_height = int(img.height * scale)
            target_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        elif max_dim > 1280:
            scale = 1024 / max_dim
            new_width = int(img.width * scale)
            new_height = int(img.height * scale)
            target_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        result = self.model1(target_img, save=False, verbose=False, 
                           conf=min_confidence,
                           iou=0.45,
                           max_det=50)
        
        predictions = []
        
        if len(result[0].boxes) == 0:
            return {
                "predictions": predictions,
                "inference_time_ms": (time.time() - start_time) * 1000,
                "detected_objects": 0,
                "realtime_optimized": True
            }
        
        scale_x = original_size[0] / target_img.width
        scale_y = original_size[1] / target_img.height
        
        for i, box in enumerate(result[0].boxes):
            confidence = box.conf[0].item()
            
            if confidence < min_confidence:
                continue
                
            class_id = int(box.cls.item())
            class_name_zh = CLASS_MAPPING_ZH.get(class_id, f"未知类别_{class_id}")
            
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            
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
            
                pre = self.model2(cimg, save=False, verbose=False)
                if hasattr(pre[0], 'probs') and pre[0].probs is not None:
                    subclass_id = pre[0].probs.top1
                    defect_status = "缺陷" if subclass_id == 0 else "正常"
                else:
                    defect_status = "正常"
            except:
                defect_status = "正常"

            prediction = {
                "center": {
                    "x": (x1_orig + x2_orig) / 2 / original_size[0],
                    "y": (y1_orig + y2_orig) / 2 / original_size[1]
                },
                "width": (x2_orig - x1_orig) / original_size[0],
                "height": (y2_orig - y1_orig) / original_size[1],
                "asset_category": class_name_zh,
                "confidence": confidence,
                "defect_status": defect_status
            }
            
            predictions.append(prediction)
        
        inference_time = (time.time() - start_time) * 1000
        
        return {
            "predictions": predictions,
            "inference_time_ms": inference_time,
            "detected_objects": len(predictions),
            "realtime_optimized": True,
            "processed_size": f"{target_img.width}x{target_img.height}",
            "original_size": f"{original_size[0]}x{original_size[1]}"
        }

class RealtimeDetectionWorker:
    def __init__(self, model_worker):
        self.model_worker = model_worker
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.frame_queue = Queue(maxsize=3)
        
    def async_predict(self, image):
        if self.frame_queue.full():
            try:
                self.frame_queue.get_nowait()
            except:
                pass
        future = self.executor.submit(self._predict_worker, image)
        return future
    
    def _predict_worker(self, image):
        try:
            result = self.model_worker.predict_realtime(image)
            return result
        except Exception as e:
            print(f"Realtime detection error: {e}")
            return {"predictions": [], "inference_time_ms": 0, "detected_objects": 0}

# Initialize workers
worker = ImageRecognitionWorker()
realtime_worker = RealtimeDetectionWorker(worker)

def process_image(image, return_annotated=False, realtime_mode=False):
    return worker.predict(image, return_annotated, realtime_mode)

def process_video_with_annotation(video_file, frame_interval=1, task_checker=None, progress_callback=None):
    return worker.process_video_with_annotation(video_file, frame_interval, task_checker, progress_callback)

def process_images_batch(images, return_annotated=True, batch_size=8):
    return worker.batch_predict_images(images, return_annotated, batch_size)

def process_image_realtime(image):
    future = realtime_worker.async_predict(image)
    return future.result()
