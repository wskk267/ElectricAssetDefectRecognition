# 电力资产缺陷识别系统

基于YOLO和InsPLAD数据集的电力设备智能识别与缺陷检测系统，支持17种电力资产类别识别和0/1缺陷状态检测。

## 最新更新 (2025-07-09)

### ✨ 新增功能
- **精确置信度滑块**：0-100%连续调节，支持1%精度控制
- **智能边框颜色**：开启缺陷显示时红绿分色，关闭时统一蓝色
- **自适应图片容器**：去除黑框，边框定位无偏移
- **自动状态清理**：上传新图片时自动清空上次识别结果

### 🔧 技术改进
- **多语言支持**：Roboflow英文类别自动翻译为中文显示
- **响应式设计**：图片容器自适应内容，无多余空间
- **实时过滤**：置信度、类别、缺陷状态三重过滤机制
- **性能优化**：边界框坐标计算优化，避免偏移问题

## 系统特色

🔍 **智能识别**：基于InsPLAD数据集的17种电力资产精确识别  
🎯 **缺陷检测**：0/1二元分类，快速判断设备健康状态  
🖼️ **实时标注**：图片上实时显示检测框和资产信息  
📱 **响应式UI**：现代化界面，支持多设备访问  
⚡ **高性能**：模型预加载，快速响应  

## 技术架构

- **前端**：Vue 3 + TypeScript + Element Plus
- **后端**：Flask + YOLO + Roboflow API  
- **模型**：YOLOv8 + InsPLAD数据集
- **通信**：RESTful API + CORS支持

## 支持的资产类别

1. Damper ‑ Spiral (螺旋阻尼器)
2. Damper ‑ Stockbridge (斯托克布里奇阻尼器)
3. Glass Insulator (玻璃绝缘子)
4. Glass Insulator Big Shackle (大卸扣玻璃绝缘子)
5. Glass Insulator Small Shackle (小卸扣玻璃绝缘子)
6. Glass Insulator Tower Shackle (塔用卸扣玻璃绝缘子)
7. Lightning Rod Shackle (避雷针卸扣)
8. Lightning Rod Suspension (避雷针悬挂)
9. Tower ID Plate (塔身标识牌)
10. Polymer Insulator (聚合物绝缘子)
11. Polymer Insulator Lower Shackle (聚合物绝缘子下卸扣)
12. Polymer Insulator Upper Shackle (聚合物绝缘子上卸扣)
13. Polymer Insulator Tower Shackle (聚合物绝缘子塔用卸扣)
14. Spacer (间隔棒)
15. Vari‑grip (防振锤)
16. Yoke (横担)
17. Yoke Suspension (横担悬挂)

## 快速开始

### 环境要求

- Python 3.8+
- Node.js 16+
- npm 或 yarn

### 安装步骤

1. **克隆项目**
```bash
git clone [项目地址]
cd ElectricAssetDefectRecognition
```

2. **启动后端**
```bash
cd Backend
pip install -r requirements.txt
python app.py
```

3. **启动前端**
```bash
cd Web
npm install
npm run dev
```

4. **访问系统**
- 前端界面：http://localhost:5174
- 后端API：http://localhost:8090

### 使用启动脚本（Windows）

```bash
# 启动后端
cd Backend
start_backend.bat

# 启动前端  
cd Web
start_frontend.bat
```

## 主要功能

### 🖼️ 图片上传
- 支持拖拽上传
- 多种图片格式（JPG、PNG、BMP）
- 文件大小限制16MB

### 🔍 智能识别
- 17种电力资产类别识别
- 缺陷状态检测（正常/缺陷）
- 置信度评估

### 📊 可视化展示
- 实时边界框绘制
- 颜色编码：绿色（正常）、红色（缺陷）、蓝色（不显示缺陷）
- 资产信息标签：ID + 名称 + 置信度

### 🎛️ 交互控制
- 资产类别筛选
- 显示选项开关（边框、置信度、缺陷）
- 响应式布局

## API接口

### 健康检查
```http
GET /
```

### 图片预测
```http
POST /api/predict/file
Content-Type: multipart/form-data

file: [图片文件]
```

### 响应格式
```json
{
  "success": true,
  "data": {
    "total_detections": 3,
    "defect_count": 1,
    "predictions": [
      {
        "id": 1,
        "asset_category": "Glass Insulator",
        "defect_status": "正常",
        "confidence": 0.853,
        "center": {"x": 0.456, "y": 0.332},
        "width": 0.124,
        "height": 0.187
      }
    ]
  }
}
```

## 项目结构

```
ElectricAssetDefectRecognition/
├── Backend/                 # 后端服务
│   ├── app.py              # Flask主应用
│   ├── config.py           # 配置文件
│   ├── workerImage.py      # 图像识别服务
│   ├── requirements.txt    # Python依赖
│   ├── start_backend.bat   # Windows启动脚本
│   └── test_system.py      # 系统测试脚本
├── Web/                    # 前端应用
│   ├── src/
│   │   ├── user/
│   │   │   ├── UW1.vue           # 主界面
│   │   │   └── ImageRecognition.vue # 识别组件
│   │   ├── router/         # 路由配置
│   │   └── ...
│   ├── package.json        # 前端依赖
│   └── start_frontend.bat  # Windows启动脚本
├── best.pt                 # 备用模型
├── last.pt                 # 主要模型
└── README.md              # 项目说明
```

## 开发说明

### 后端开发
- 基于Flask框架
- 使用YOLO进行目标检测
- Roboflow API进行资产分类
- 支持模型热加载和错误降级

### 前端开发
- Vue 3 Composition API
- TypeScript类型支持
- Element Plus UI组件
- 响应式设计

### 坐标系统
- 后端使用YOLO格式相对坐标（0-1范围）
- 前端自动转换为像素坐标
- 支持图片缩放和响应式显示

## 测试

运行系统测试：
```bash
cd Backend
python test_system.py
```

## 配置说明

### 后端配置（config.py）
- 模型路径配置
- API密钥设置
- 资产类别定义
- 缺陷状态映射

### 前端配置
- API基地址
- 资产类别列表
- UI主题设置

## 📋 边界框定位修复说明

### 🔍 问题分析
您的分析完全正确！之前的边界框是绘制在"图片预览容器"内，而不是直接绑定到图片本身，导致：
- 容器和图片尺寸不一致时出现偏移
- 复杂的坐标转换计算容易出错
- 图片缩放时边界框位置不准确

### ✅ 修复方案
1. **HTML结构优化**：
   ```vue
   <div class="image-wrapper">
       <img ref="previewImage" class="preview-image" />
       <div class="bounding-boxes-overlay">
           <!-- 边界框直接覆盖在图片上 -->
       </div>
   </div>
   ```

2. **CSS定位修复**：
   - 叠加层使用 `position: absolute` 覆盖整个图片区域
   - 边界框相对于图片而非容器定位

3. **坐标计算简化**：
   ```javascript
   // 直接使用相对坐标，无需复杂转换
   const centerX = result.center.x * imgWidth
   const centerY = result.center.y * imgHeight
   const left = centerX - boxWidth / 2
   const top = centerY - boxHeight / 2
   ```

### 🎯 效果验证
- 边界框精确贴合检测目标
- 支持图片动态缩放
- 消除所有定位偏移问题

## 常见问题

### Q: 边框位置不准确？
A: 已修复边界框定位问题：
- 边界框现在直接绑定到图片元素，而不是容器
- 使用相对坐标直接计算，无需复杂的缩放转换
- 叠加层精确覆盖图片区域，确保边框位置准确

### Q: 支持哪些图片格式？
A: 支持JPG、PNG、BMP格式，建议使用JPG格式以获得最佳性能。

### Q: 如何添加新的资产类别？
A: 更新config.py中的ASSET_CATEGORIES和ASSET_NAME_MAPPING配置，同时更新前端的assetCategories数组。

## 许可证

[项目许可证信息]

## 联系方式

[联系方式信息]
