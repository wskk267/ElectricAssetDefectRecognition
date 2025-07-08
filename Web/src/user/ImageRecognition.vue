<template>
    <div class="image-recognition">
        <div class="left-panel">
            <!-- 上传区域 -->
            <div class="upload-section"> <el-card class="upload-card">
                    <template #header>
                        <div class="card-header">
                            <span><el-icon>
                                    <Upload />
                                </el-icon> 图片上传</span>
                        </div>
                    </template>

                    <el-upload class="upload-demo" drag action="#" :auto-upload="false" :show-file-list="false"
                        accept="image/*" :on-change="handleImageChange">
                        <div class="upload-area">
                            <el-icon class="upload-icon">
                                <Upload />
                            </el-icon>
                            <div class="upload-text">点击或拖拽图片到此区域上传</div>
                            <div class="upload-hint">支持 JPG、PNG 格式</div>
                        </div>
                    </el-upload>

                    <div class="action-buttons">
                        <el-button type="primary" :loading="recognizing" @click="startRecognition"
                            :disabled="!uploadedImage" class="recognition-btn"> <el-icon>
                                <View />
                            </el-icon>
                            {{ recognizing ? '识别中...' : '开始识别' }}
                        </el-button>
                    </div>
                </el-card>
            </div>

            <!-- 图片展示区域 -->
            <div class="image-display-section"> <el-card class="image-card">
                    <template #header>
                        <div class="card-header">
                            <span><el-icon>
                                    <Picture />
                                </el-icon> 图片预览</span>
                        </div>
                    </template>                <div class="image-container" v-if="uploadedImage">
                    <div class="image-wrapper">
                        <img :src="imagePreview" alt="预览图片" class="preview-image" ref="previewImage" @load="onImageLoad" />
                        <!-- 边界框叠加层 -->
                        <div v-if="showBoundingBoxes && recognitionResults.length > 0" class="bounding-boxes-overlay">
                            <div 
                                v-for="result in filteredResults" 
                                :key="result.id"
                                class="bounding-box"
                                :style="getBboxStyle(result)"
                            >
                                <!-- 标签 -->
                                <div class="box-label" :class="{
                                    'label-normal': !showDefects || result.defect_status === '正常',
                                    'label-defect': showDefects && result.defect_status === '缺陷'
                                }">
                                    {{ result.id }}. {{ result.asset_category }}
                                    <span v-if="showConfidence" class="confidence">
                                        ({{ (result.confidence * 100).toFixed(1) }}%)
                                    </span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                    <div v-else class="empty-image">
                        <el-icon>
                            <Picture />
                        </el-icon>
                        <p>暂无图片</p>
                    </div>
                </el-card>
            </div>
        </div>

        <!-- 右侧控制面板 -->
        <div class="right-panel">
            <!-- 显示选项 --> <el-card class="control-card">
                <template #header>
                    <div class="card-header">
                        <span><el-icon>
                                <Setting />
                            </el-icon> 显示选项</span>
                    </div>
                </template>

                <div class="control-options">
                    <div class="option-item">
                        <el-switch
                            v-model="showBoundingBoxes"
                            active-text="显示框选标记"
                            inactive-text="隐藏框选标记">
                        </el-switch>
                    </div>
                    <div class="option-item">
                        <el-switch
                            v-model="showConfidence"
                            active-text="显示置信度"
                            inactive-text="隐藏置信度">
                        </el-switch>
                    </div>
                    <div class="option-item">
                        <el-switch
                            v-model="showDefects"
                            active-text="显示缺陷标记"
                            inactive-text="统一蓝色显示">
                        </el-switch>
                    </div>
                    <div class="option-item">
                        <label class="slider-label">置信度阈值: {{ confidenceThreshold }}%</label>
                        <el-slider
                            v-model="confidenceThreshold"
                            :min="0"
                            :max="100"
                            :step="1"
                            show-tooltip
                            :format-tooltip="(val) => `${val}%`"
                            style="margin: 10px 0;">
                        </el-slider>
                    </div>
                </div>
            </el-card>

            <!-- 类别筛选 --> <el-card class="control-card">
                <template #header>
                    <div class="card-header">
                        <span><el-icon>
                                <Menu />
                            </el-icon> 资产类别筛选</span>
                    </div>
                </template>

                <div class="category-filter">
                    <el-checkbox-group v-model="selectedCategories">
                        <el-checkbox v-for="category in assetCategories" :key="category" :label="category"
                            class="category-checkbox">
                            {{ category }}
                        </el-checkbox>
                    </el-checkbox-group>
                </div>
            </el-card>

            <!-- 识别结果 --> <el-card class="results-card" v-if="recognitionResults.length > 0">
                <template #header>
                    <div class="card-header">
                        <span><el-icon>
                                <DataAnalysis />
                            </el-icon> 识别结果</span>
                    </div>
                </template>

                <div class="results-list">
                    <div v-for="(result, index) in filteredResults" :key="index" class="result-item">
                        <div class="result-header">
                            <span class="result-index">#{{ result.id }}</span>
                            <el-tag :type="result.defect_status === '缺陷' ? 'danger' : 'success'" size="small">
                                {{ result.defect_status }}
                            </el-tag>
                        </div>
                        <div class="result-details">
                            <p><strong>资产类别:</strong> {{ result.asset_category }}</p>
                            <p><strong>缺陷状态:</strong> {{ result.defect_status }}</p>
                            <p><strong>置信度:</strong> {{ (result.confidence * 100).toFixed(1) }}%</p>
                            <p><strong>中心位置:</strong> ({{ (result.center.x * 100).toFixed(1) }}%, {{ (result.center.y * 100).toFixed(1) }}%)</p>
                            <p><strong>检测框尺寸:</strong> {{ (result.width * 100).toFixed(1) }}% × {{ (result.height * 100).toFixed(1) }}%</p>
                        </div>
                    </div>
                </div>
            </el-card>
        </div>
    </div>
</template>

<script lang="ts">
import { defineComponent, ref, computed } from 'vue'
import { Upload, View, Picture, Setting, Menu, DataAnalysis } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

export default defineComponent({
    name: 'ImageRecognition',
    components: {
        Upload,
        View,
        Picture,
        Setting,
        Menu,
        DataAnalysis
    },
    setup() {
        const uploadedImage = ref<File | null>(null)
        const imagePreview = ref('')
        const recognizing = ref(false)
        const showBoundingBoxes = ref(true)
        const showConfidence = ref(true)
        const showDefects = ref(true)
        const confidenceThreshold = ref(50) // 置信度阈值 0-100
        const selectedCategories = ref<string[]>([])
        const recognitionResults = ref<any[]>([])
        const previewImage = ref<HTMLImageElement | null>(null)

        // 资产类别配置（对应后端config.py的ASSET_CATEGORIES）
        const assetCategories = [
            '螺旋阻尼器',
            '斯托克布里奇阻尼器',
            '玻璃绝缘子',
            '玻璃绝缘子大卸扣',
            '玻璃绝缘子小卸扣',
            '玻璃绝缘子塔用卸扣',
            '避雷针卸扣',
            '避雷针悬挂',
            '塔身标识牌',
            '聚合物绝缘子',
            '聚合物绝缘子下卸扣',
            '聚合物绝缘子上卸扣',
            '聚合物绝缘子塔用卸扣',
            '间隔棒',
            '防振锤',
            '横担',
            '横担悬挂'
        ]

        selectedCategories.value = [...assetCategories]

        const filteredResults = computed(() => {
            return recognitionResults.value.filter(result =>
                selectedCategories.value.includes(result.asset_category) &&
                (result.confidence * 100) >= confidenceThreshold.value // 置信度过滤
            )
        })

        // 获取边界框样式
        const getBboxStyle = (result: any) => {
            if (!previewImage.value) return { display: 'none' }
            
            const img = previewImage.value
            const imgWidth = img.clientWidth
            const imgHeight = img.clientHeight
            
            // YOLO格式：center_x, center_y, width, height (都是相对于图片尺寸的比例)
            const centerX = result.center.x * imgWidth
            const centerY = result.center.y * imgHeight
            const boxWidth = result.width * imgWidth
            const boxHeight = result.height * imgHeight
            
            // 计算左上角坐标（相对于图片）
            const left = centerX - boxWidth / 2
            const top = centerY - boxHeight / 2
            
            // 根据缺陷状态和显示选项确定颜色
            let borderColor = '#00f5ff'  // 默认蓝色
            let backgroundColor = 'rgba(0, 245, 255, 0.1)'
            
            if (showDefects.value) {
                // 显示缺陷模式：根据缺陷状态分色
                if (result.defect_status === '缺陷') {
                    borderColor = '#ff4757'  // 红色（缺陷）
                    backgroundColor = 'rgba(255, 71, 87, 0.1)'
                } else {
                    borderColor = '#2ed573'  // 绿色（正常）
                    backgroundColor = 'rgba(46, 213, 115, 0.1)'
                }
            }
            // 不显示缺陷模式：统一蓝色（已在上面设置）
            
            return {
                position: 'absolute' as const,
                left: `${left}px`,
                top: `${top}px`,
                width: `${boxWidth}px`,
                height: `${boxHeight}px`,
                border: `2px solid ${borderColor}`,
                borderRadius: '4px',
                backgroundColor: backgroundColor,
                pointerEvents: 'none' as const
            }
        }

        // 图片加载完成事件
        const onImageLoad = () => {
            console.log('图片加载完成，可以绘制边界框')
        }

        const handleImageChange = (file: any) => {
            uploadedImage.value = file.raw
            // 清空上次识别结果
            recognitionResults.value = []
            
            const reader = new FileReader()
            reader.onload = (e) => {
                imagePreview.value = e.target?.result as string
            }
            reader.readAsDataURL(file.raw)
        }

        const startRecognition = async () => {
            if (!uploadedImage.value) return

            recognizing.value = true

            try {
                // 创建FormData来上传文件
                const formData = new FormData()
                formData.append('file', uploadedImage.value)

                // 调用后端API
                const response = await fetch('http://localhost:8090/api/predict/file', {
                    method: 'POST',
                    body: formData
                })

                const result = await response.json()

                if (result.success && result.data.success) {
                    const apiData = result.data
                    
                    // 转换API返回的数据格式以匹配前端显示
                    recognitionResults.value = apiData.predictions.map((pred: any, index: number) => ({
                        id: index + 1,
                        asset_category: pred.asset_category,
                        defect_status: pred.defect_status,
                        confidence: pred.confidence,
                        center: pred.center,
                        width: pred.width,
                        height: pred.height,
                        isDefective: pred.defect_status === '缺陷'
                    }))

                    ElMessage.success(`识别完成！检测到 ${apiData.total_detections} 个目标，其中 ${apiData.defect_count} 个缺陷`)
                } else {
                    console.error('识别失败:', result.error || result.message)
                    ElMessage.error(result.error || result.message || '识别失败，请重试')
                    recognitionResults.value = []
                }
            } catch (error) {
                console.error('API调用失败:', error)
                ElMessage.error('网络连接失败，请检查后端服务是否启动')
                recognitionResults.value = []
            } finally {
                recognizing.value = false
            }
        }

        return {
            uploadedImage,
            imagePreview,
            recognizing,
            showBoundingBoxes,
            showConfidence,
            showDefects,
            confidenceThreshold,
            selectedCategories,
            recognitionResults,
            assetCategories,
            filteredResults,
            getBboxStyle,
            onImageLoad,
            previewImage,
            handleImageChange,
            startRecognition
        }
    }
})
</script>

<style scoped>
/* 图片识别面板 */
.image-recognition {
    display: flex;
    gap: 30px;
    height: 100%;
}

.left-panel {
    flex: 2;
    display: flex;
    flex-direction: column;
    gap: 30px;
}

.right-panel {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 20px;
}

/* 卡片样式 */
:deep(.el-card) {
    background: rgba(26, 26, 46, 0.8);
    border: 1px solid rgba(0, 245, 255, 0.3);
    border-radius: 15px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    backdrop-filter: blur(10px);
}

:deep(.el-card__header) {
    background: rgba(0, 245, 255, 0.1);
    border-bottom: 1px solid rgba(0, 245, 255, 0.3);
    padding: 15px 20px;
}

:deep(.el-card__body) {
    padding: 20px;
}

.card-header {
    color: #00f5ff;
    font-weight: bold;
    font-size: 16px;
    display: flex;
    align-items: center;
    gap: 8px;
}

.card-header .el-icon {
    font-size: 18px;
}

/* 上传区域样式 */
.upload-card {
    flex: 1;
}

:deep(.el-upload-dragger) {
    background: rgba(0, 245, 255, 0.05);
    border: 2px dashed rgba(0, 245, 255, 0.5);
    border-radius: 10px;
    width: 100%;
    height: 200px;
    transition: all 0.3s ease;
}

:deep(.el-upload-dragger:hover) {
    background: rgba(0, 245, 255, 0.1);
    border-color: #00f5ff;
    box-shadow: 0 0 20px rgba(0, 245, 255, 0.3);
}

.upload-area {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
    color: #ffffff;
}

.upload-icon {
    font-size: 48px;
    color: #00f5ff;
    margin-bottom: 15px;
}

.upload-text {
    font-size: 16px;
    margin-bottom: 8px;
}

.upload-hint {
    font-size: 12px;
    color: #888;
}

.action-buttons {
    margin-top: 20px;
    text-align: center;
}

.recognition-btn {
    background: linear-gradient(45deg, #00f5ff, #0080ff);
    border: none;
    border-radius: 25px;
    padding: 12px 30px;
    font-size: 16px;
    font-weight: bold;
    color: #000;
    box-shadow: 0 4px 15px rgba(0, 245, 255, 0.4);
    transition: all 0.3s ease;
}

.recognition-btn:hover {
    box-shadow: 0 6px 20px rgba(0, 245, 255, 0.6);
    transform: translateY(-2px);
}

.recognition-btn:disabled {
    background: #666;
    color: #999;
    box-shadow: none;
    transform: none;
}

/* 图片展示区域 */
.image-card {
    flex: 2;
}

.image-container {
    position: relative;
    width: 100%;
    display: flex;
    justify-content: center;
    align-items: center;
    border-radius: 10px;
    overflow: hidden;
    background: transparent;
}

.image-wrapper {
    position: relative;
    display: inline-block;
}

.preview-image {
    max-width: 100%;
    max-height: 500px;
    width: auto;
    height: auto;
    object-fit: contain;
    display: block;
    border-radius: 8px;
}

.bounding-boxes-overlay {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
}

.empty-image {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 300px;
    color: #666;
}

.empty-image .el-icon {
    font-size: 64px;
    margin-bottom: 15px;
}

/* 控制面板样式 */
.control-card {
    margin-bottom: 20px;
}

.control-options {
    padding: 10px 0;
}

.option-item {
    margin: 15px 0;
    color: #ffffff;
}

.slider-label {
    color: #ffffff;
    font-size: 14px;
    display: block;
    margin-bottom: 8px;
}

:deep(.el-slider) {
    --el-slider-main-bg-color: #00f5ff;
    --el-slider-runway-bg-color: rgba(255, 255, 255, 0.2);
}

:deep(.el-slider__button) {
    border: 2px solid #00f5ff;
    background: #00f5ff;
}

:deep(.el-slider__stop) {
    background: rgba(255, 255, 255, 0.5);
}

:deep(.el-switch) {
    --el-switch-on-color: #00f5ff;
    --el-switch-off-color: #666;
}

:deep(.el-switch__label) {
    color: #ffffff;
}

/* 类别筛选 */
.category-filter {
    max-height: 300px;
    overflow-y: auto;
}

.category-checkbox {
    display: block;
    margin: 8px 0;
    color: #ffffff;
}

:deep(.el-checkbox__label) {
    color: #ffffff;
}

:deep(.el-checkbox__input.is-checked .el-checkbox__inner) {
    background-color: #00f5ff;
    border-color: #00f5ff;
}

:deep(.el-checkbox__inner:hover) {
    border-color: #00f5ff;
}

/* 识别结果 */
.results-card {
    flex: 1;
}

.results-list {
    max-height: 400px;
    overflow-y: auto;
}

.result-item {
    background: rgba(0, 245, 255, 0.05);
    border: 1px solid rgba(0, 245, 255, 0.2);
    border-radius: 8px;
    padding: 15px;
    margin-bottom: 15px;
    transition: all 0.3s ease;
}

.result-item:hover {
    background: rgba(0, 245, 255, 0.1);
    box-shadow: 0 4px 15px rgba(0, 245, 255, 0.3);
}

.result-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
}

.result-index {
    font-weight: bold;
    color: #00f5ff;
    font-size: 16px;
}

.result-details p {
    margin: 5px 0;
    font-size: 14px;
    color: #ccc;
}

.result-details strong {
    color: #ffffff;
}

/* 边界框样式 */
.bounding-boxes-overlay {
    pointer-events: none;
}

.bounding-box {
    transition: all 0.3s ease;
}

.box-normal {
    border-color: #00f5ff !important;
    background-color: rgba(0, 245, 255, 0.1) !important;
}

.box-defect {
    border-color: #ff4757 !important;
    background-color: rgba(255, 71, 87, 0.1) !important;
}

.box-label {
    position: absolute;
    top: -25px;
    left: 0;
    background: rgba(0, 0, 0, 0.8);
    color: white;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 12px;
    font-weight: bold;
    white-space: nowrap;
    z-index: 10;
}

.label-normal {
    background: rgba(0, 245, 255, 0.8) !important;
    color: #000 !important;
}

.label-defect {
    background: rgba(255, 71, 87, 0.8) !important;
    color: #fff !important;
}

.confidence {
    font-weight: normal;
    opacity: 0.8;
}

/* 滚动条样式 */
::-webkit-scrollbar {
    width: 8px;
}

::-webkit-scrollbar-track {
    background: rgba(0, 0, 0, 0.2);
    border-radius: 4px;
}

::-webkit-scrollbar-thumb {
    background: rgba(0, 245, 255, 0.6);
    border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
    background: rgba(0, 245, 255, 0.8);
}

/* 响应式设计 */
@media (max-width: 1200px) {
    .image-recognition {
        flex-direction: column;
    }

    .left-panel,
    .right-panel {
        flex: none;
    }
}
</style>
