<template>
    <div class="image-recognition">
        <div class="left-panel">
            <!-- 合并上传和预览区域 -->
            <div class="image-display-section">
                <el-card class="image-card">
                    <template #header>
                        <div class="card-header">
                            <span><el-icon>
                                    <Picture />
                                </el-icon> 图片识别</span>
                        </div>
                    </template>

                    <div class="image-container">
                        <!-- 当没有图片时显示上传区域 -->
                        <div v-if="!uploadedImage" class="upload-area-wrapper">
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
                        </div>

                        <!-- 当有图片时显示预览 -->
                        <div v-else class="image-wrapper">
                            <img :src="imagePreview" alt="预览图片" class="preview-image" ref="previewImage"
                                @load="onImageLoad" />

                            <!-- 边界框叠加层 -->
                            <div v-if="showBoundingBoxes && recognitionResults.length > 0 && !detailViewActive" class="bounding-boxes-overlay">
                                <div v-for="(result, index) in filteredResults" :key="`bbox-${result.uniqueId || result.id}-${index}`" class="bounding-box"
                                    :style="getBboxStyle(result)" @click="showDetailedView(result)">
                                    <!-- 标签 -->
                                    <div class="box-label" :class="{
                                        'label-normal': !showDefects || result.defect_status === '正常',
                                        'label-defect': showDefects && result.defect_status === '缺陷',
                                        'label-inside': shouldShowLabelInside(result)
                                    }">
                                        设备{{ result.id }}: {{ result.asset_category }}
                                        <span v-if="showConfidence" class="confidence">
                                            ({{ (result.confidence * 100).toFixed(1) }}%)
                                        </span>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- 放大视图模式 -->
                        <div v-if="detailViewActive" class="detail-view-overlay" @click="closeDetailedView">
                            <div class="detail-view-container" @click.stop>
                                <div class="detail-view-header">
                                    <span>设备详情 #{{ selectedDetail.id }}</span> <el-button class="custom-btn return-btn"
                                        type="info" plain size="large" @click="closeDetailedView">
                                        <el-icon class="btn-icon">
                                            <Back />
                                        </el-icon>返回
                                    </el-button>
                                </div>
                                <div class="detail-view-content">
                                    <div class="detail-image-container">
                                        <div class="detail-image-wrapper">
                                            <img :src="detailImage" alt="裁剪视图"
                                                style="object-fit: contain;width: 100%; height: 100%;background-color:#1A1A2D;" />
                                        </div>
                                    </div>
                                    <div class="detail-info">
                                        <h3>设备信息</h3>
                                        <p><strong>设备类别:</strong> {{ selectedDetail.asset_category }}</p>
                                        <p><strong>缺陷状态:</strong>
                                            <el-tag :type="selectedDetail.defect_status === '缺陷' ? 'danger' : 'success'"
                                                size="small">
                                                {{ selectedDetail.defect_status }}
                                            </el-tag>
                                        </p>
                                        <p><strong>置信度:</strong> {{ (selectedDetail.confidence * 100).toFixed(1) }}%</p>
                                        <p><strong>中心位置:</strong> ({{ (selectedDetail.center.x * 100).toFixed(1) }}%, {{
                                            (selectedDetail.center.y * 100).toFixed(1) }}%)</p>
                                        <p><strong>检测框尺寸:</strong> {{ (selectedDetail.width * 100).toFixed(1) }}% × {{
                                            (selectedDetail.height * 100).toFixed(1) }}%</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    <!-- 将按钮移到卡片底部 -->
                    <div v-if="uploadedImage" class="image-controls">
                        <el-button class="custom-btn reset-btn" type="primary" plain size="large" @click="resetImage">
                            <el-icon class="btn-icon">
                                <RefreshRight />
                            </el-icon>重新上传
                        </el-button>
                        <el-button class="custom-btn recognize-btn" type="success" :loading="recognizing"
                            @click="startRecognition" size="large">
                            <el-icon class="btn-icon">
                                <Monitor />
                            </el-icon>
                            {{ recognizing ? '识别中...' : '开始识别' }}
                        </el-button>
                    </div>
                </el-card>
            </div>
        </div>

        <!-- 中间识别结果面板 -->
        <div v-if="recognitionResults.length > 0" class="middle-panel">
            <el-card class="results-card">
                <template #header>
                    <div class="card-header">
                        <span><el-icon>
                                <DataAnalysis />
                            </el-icon> 识别结果</span>
                    </div>
                </template>

                <div class="results-list">
                    <div v-for="(result, index) in filteredResults"
                        :key="`result-${result.uniqueId || result.id}-${index}`" class="result-item"
                        :class="{ 'result-selected': isResultSelected(result) }" @click="showDetailedView(result)">
                        <div class="result-header">
                            <span class="result-index">设备{{ result.id }}</span>
                            <el-tag :type="result.defect_status === '缺陷' ? 'danger' : 'success'" size="small">
                                {{ result.defect_status }}
                            </el-tag>
                        </div>
                        <div class="result-details">
                            <p><strong>设备类别:</strong> {{ result.asset_category }}</p>
                            <p><strong>置信度:</strong> {{ (result.confidence * 100).toFixed(1) }}%</p>
                        </div>
                    </div>
                </div>
            </el-card>
        </div>

        <!-- 右侧控制面板 -->
        <div class="right-panel">
            <!-- 显示选项 -->
            <el-card class="control-card">
                <template #header>
                    <div class="card-header">
                        <span><el-icon>
                                <Setting />
                            </el-icon> 显示选项</span>
                    </div>
                </template>

                <div class="control-options">
                    <div class="option-item">
                        <el-switch v-model="showBoundingBoxes" active-text="显示框选标记" inactive-text="隐藏框选标记">
                        </el-switch>
                    </div>
                    <div class="option-item">
                        <el-switch v-model="showConfidence" active-text="显示置信度" inactive-text="隐藏置信度">
                        </el-switch>
                    </div>
                    <div class="option-item">
                        <el-switch v-model="showDefects" active-text="显示缺陷标记" inactive-text="统一蓝色显示">
                        </el-switch>
                    </div>
                    <div class="option-item">
                        <label class="slider-label">设备识别阈值: {{ deviceConfidenceThreshold }}%</label>
                        <el-slider v-model="deviceConfidenceThreshold" :min="0" :max="100" :step="1" show-tooltip
                            :format-tooltip="(val) => `${val}%`" style="margin: 10px 0;">
                        </el-slider>
                    </div>
                    <div class="option-item">
                        <label class="slider-label">缺陷识别阈值: {{ defectConfidenceThreshold }}%</label>
                        <el-slider v-model="defectConfidenceThreshold" :min="0" :max="100" :step="1" show-tooltip
                            :format-tooltip="(val) => `${val}%`" class="defect-threshold-slider"
                            style="margin: 10px 0;">
                        </el-slider>
                    </div>
                </div>
            </el-card>

            <!-- 类别筛选 -->
            <el-card class="control-card">
                <template #header>
                    <div class="card-header">
                        <span><el-icon>
                                <Menu />
                            </el-icon> 设备类别筛选</span>
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
        </div>
    </div>
</template>

<script lang="ts">
import { ref, computed, watch, onMounted, defineComponent, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { Setting, Upload, Monitor, RefreshRight, Back, Picture, Menu, DataAnalysis } from '@element-plus/icons-vue'
import axiosInstance from '../axios'
import axios from 'axios'

export default defineComponent({
    name: 'ImageRecognition',
    components: {
        Upload,
        Picture,
        Setting,
        Menu,
        DataAnalysis,
        Back,
        Monitor,
        RefreshRight
    },
    setup() {
        const uploadedImage = ref<File | null>(null)
        const imagePreview = ref('')
        const recognizing = ref(false)
        const showBoundingBoxes = ref(true)
        const showConfidence = ref(true)
        const showDefects = ref(true)

        // 替换单一置信度阈值为设备识别阈值和缺陷识别阈值
        const deviceConfidenceThreshold = ref(50) // 设备识别置信度阈值
        const defectConfidenceThreshold = ref(50) // 缺陷识别置信度阈值

        const selectedCategories = ref<string[]>([])
        const recognitionResults = ref<any[]>([])
        const previewImage = ref<HTMLImageElement | null>(null)

        // 添加详细视图相关状态
        const detailViewActive = ref(false)
        const selectedDetail = ref<any>({})
        const selectedResultId = ref<number | null>(null) // 当前选中的结果ID
        const detailImage = ref<string>('') // 原先string base64，并非HTMLImageElement
        const naturalImageSize = ref({ width: 0, height: 0 })

        // 设备类别配置（对应后端workerImage.py的CLASS_MAPPING_ZH）
        const assetCategories = [
            '横担',
            '横担悬挂',
            '间隔棒',
            '斯托克布里奇阻尼器',
            '避雷针卸扣',
            '避雷针悬挂',
            '聚合物绝缘子',
            '玻璃绝缘子',
            '塔身标识牌',
            '防振锤',
            '聚合物绝缘子下卸扣',
            '聚合物绝缘子上卸扣',
            '聚合物绝缘子塔用卸扣',
            '玻璃绝缘子大卸扣',
            '玻璃绝缘子小卸扣',
            '玻璃绝缘子塔用卸扣',
            '螺旋阻尼器',
            '球'
        ]

        // 默认全选所有类别
        onMounted(() => {
            selectedCategories.value = [...assetCategories]
        })

        // 根据类别和置信度过滤结果
        const filteredResults = computed(() => {
            return recognitionResults.value
                // 根据设备识别置信度过滤
                .filter(result => (result.confidence * 100) >= deviceConfidenceThreshold.value)
                // 根据类别过滤
                .filter(result => {
                    if (selectedCategories.value.length === 0) {
                        return true // 如果没有选择任何类别，则显示所有类别
                    }
                    return selectedCategories.value.includes(result.asset_category)
                })
        })

        // 获取边界框样式
        const getBboxStyle = (result) => {
            if (!previewImage.value) return {}

            const img = previewImage.value
            const container = img.parentElement

            if (!container) return {}

            // 获取容器和图片的实际尺寸
            const containerRect = container.getBoundingClientRect()
            const imgRect = img.getBoundingClientRect()

            // 计算图片在容器中的实际显示尺寸和位置
            const imgDisplayWidth = imgRect.width
            const imgDisplayHeight = imgRect.height
            const imgOffsetX = (containerRect.width - imgDisplayWidth) / 2
            const imgOffsetY = (containerRect.height - imgDisplayHeight) / 2

            // 基于百分比计算边界框在图片上的位置
            const centerXPercent = result.center.x
            const centerYPercent = result.center.y
            const widthPercent = result.width
            const heightPercent = result.height

            // 转换为在容器中的像素位置
            const boxWidth = widthPercent * imgDisplayWidth
            const boxHeight = heightPercent * imgDisplayHeight
            const boxLeft = imgOffsetX + (centerXPercent - widthPercent / 2) * imgDisplayWidth
            const boxTop = imgOffsetY + (centerYPercent - heightPercent / 2) * imgDisplayHeight

            // 根据缺陷状态和显示选项确定颜色
            let borderColor = '#00f5ff'  // 默认蓝色
            let backgroundColor = 'rgba(0, 245, 255, 0.1)'

            if (showDefects.value) {
                // 显示缺陷模式：根据缺陷状态分色
                if (result.defect_status === '缺陷') {
                    // 缺陷识别的置信度阈值逻辑
                    const confidence = result.confidence * 100;
                    if (confidence >= defectConfidenceThreshold.value) {
                        borderColor = '#ff4757'  // 红色（缺陷且置信度高）
                        backgroundColor = 'rgba(255, 71, 87, 0.1)'
                    } else {
                        borderColor = '#ffba00'  // 黄色（缺陷但置信度低）
                        backgroundColor = 'rgba(255, 186, 0, 0.1)'
                    }
                } else { // 正常状态
                    borderColor = '#2ed573'  // 绿色（正常）
                    backgroundColor = 'rgba(46, 213, 115, 0.1)'
                }
            }

            return {
                position: 'absolute' as const,
                left: `${boxLeft}px`,
                top: `${boxTop}px`,
                width: `${boxWidth}px`,
                height: `${boxHeight}px`,
                border: `2px solid ${borderColor}`,
                borderRadius: '4px',
                backgroundColor: backgroundColor,
                cursor: 'pointer',
                pointerEvents: 'auto' as const
            }
        }

        // 判断标签是否应该显示在边界框内部
        const shouldShowLabelInside = (result) => {
            if (!previewImage.value) return false

            const img = previewImage.value
            const container = img.parentElement
            if (!container) return false

            const containerRect = container.getBoundingClientRect()
            const imgRect = img.getBoundingClientRect()

            // 计算图片在容器中的实际显示位置
            const imgOffsetY = (containerRect.height - imgRect.height) / 2
            const boxTop = imgOffsetY + (result.center.y - result.height / 2) * imgRect.height

            // 如果边界框太靠近顶部（距离顶部小于30px），则标签显示在内部
            return boxTop < 30
        }

        // 重置图片
        const resetImage = () => {
            uploadedImage.value = null
            imagePreview.value = ''
            recognitionResults.value = []
            selectedResultId.value = null
            closeDetailedView()
        }

        // 显示详细视图
        const showDetailedView = async (result) => {
            // 确保传递的是完整的result对象
            selectedDetail.value = { ...result }
            selectedResultId.value = result.id

            // 等待下一帧，确保图片已经加载完成
            await nextTick()

            // 手动获取图片的自然尺寸，确保 naturalImageSize 正确
            if (previewImage.value) {
                const img = previewImage.value
                naturalImageSize.value = {
                    width: img.naturalWidth || img.width,
                    height: img.naturalHeight || img.height
                }
            }
            // 裁剪视图的图片尺寸必须在显示前获取
            ensureImageSize()
            // 裁剪图片
            cropImage(selectedDetail.value)

            detailViewActive.value = true

            // 调试输出，确保数据正确
            console.log('显示详情视图:', {
                id: result.id,
                category: result.asset_category,
                center: result.center,
                uniqueId: result.uniqueId,
                naturalSize: naturalImageSize.value
            })
        }

        // 关闭详细视图
        const closeDetailedView = () => {
            detailViewActive.value = false
            selectedResultId.value = null
        }

        // 检查结果是否被选中
        const isResultSelected = (result) => {
            if (!detailViewActive.value || !selectedDetail.value) return false
            // 优先使用uniqueId进行匹配，如果没有则使用多字段匹配
            if (result.uniqueId && selectedDetail.value.uniqueId) {
                return result.uniqueId === selectedDetail.value.uniqueId
            }
            // 降级到多字段精确匹配
            return selectedDetail.value.id === result.id &&
                selectedDetail.value.asset_category === result.asset_category &&
                Math.abs(selectedDetail.value.center.x - result.center.x) < 0.01 &&
                Math.abs(selectedDetail.value.center.y - result.center.y) < 0.01
        }

        // 图片加载完成事件
        const onImageLoad = (event) => {
            const img = event.target
            naturalImageSize.value = {
                width: img.naturalWidth,
                height: img.naturalHeight
            }
            console.log('图片加载完成，自然尺寸:', naturalImageSize.value)

            // 监听窗口大小变化，重新计算边界框位置
            window.addEventListener('resize', () => {
                // 触发响应式更新
                if (recognitionResults.value.length > 0) {
                    // 强制重新渲染
                    const results = recognitionResults.value
                    recognitionResults.value = []
                    setTimeout(() => {
                        recognitionResults.value = results
                    }, 10)
                }
            })
        }

        // 确保图片尺寸数据可用的辅助函数
        const ensureImageSize = () => {
            if (previewImage.value && (!naturalImageSize.value.width || !naturalImageSize.value.height)) {
                const img = previewImage.value
                naturalImageSize.value = {
                    width: img.naturalWidth || img.width,
                    height: img.naturalHeight || img.height
                }
                console.log('手动获取图片尺寸:', naturalImageSize.value)
            }
        }

        const handleImageChange = (file) => {
            uploadedImage.value = file.raw
            // 清空上次识别结果和选中状态
            recognitionResults.value = []
            selectedResultId.value = null

            const reader = new FileReader()
            reader.onload = (e) => {
                imagePreview.value = typeof e.target?.result === 'string' ? e.target.result : ''
            }
            reader.readAsDataURL(file.raw)
        }

        const startRecognition = async () => {
            if (!uploadedImage.value) return

            recognizing.value = true
            closeDetailedView() // 关闭详情视图（如果打开）

            try {
                // 创建FormData来上传文件
                const formData = new FormData()
                formData.append('file', uploadedImage.value)

                // 调用后端API
                const response = await axiosInstance.post('/api/predict', formData, {
                    headers: {
                        'Content-Type': 'multipart/form-data'
                    }
                })

                const result = await response.data

                if (result.success) {
                    const apiData = result.data

                    // 转换API返回的数据格式以匹配前端显示
                    // predictions是对象，需要转换为数组
                    const predictionsArray = Object.values(apiData.predictions) as any[]
                    recognitionResults.value = predictionsArray.map((pred, index) => ({
                        id: index + 1, // 确保ID从1开始且连续
                        asset_category: pred.asset_category,
                        defect_status: pred.defect_status || '正常',
                        confidence: pred.confidence,
                        center: {
                            x: Number(pred.center.x),
                            y: Number(pred.center.y)
                        },
                        width: Number(pred.width),
                        height: Number(pred.height),
                        isDefective: pred.defect_status === '缺陷',
                        // 添加唯一标识符确保数据一致性
                        uniqueId: `${pred.asset_category}-${Math.round(pred.center.x * 1000)}-${Math.round(pred.center.y * 1000)}-${index}`
                    }))

                    ElMessage.success(`识别完成！检测到 ${apiData.detected_objects} 个目标，耗时 ${apiData.inference_time_ms.toFixed(1)}ms`)
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

        // 裁剪图片函数
        const cropImage = (result) => {
            if (!previewImage.value || !naturalImageSize.value.width || !naturalImageSize.value.height) return
            const imgEl = previewImage.value
            const imgWidth = naturalImageSize.value.width
            const imgHeight = naturalImageSize.value.height
            const w = result.width * imgWidth
            const h = result.height * imgHeight
            const cx = result.center.x * imgWidth
            const cy = result.center.y * imgHeight
            const left = cx - w / 2
            const top = cy - h / 2

            const canvas = document.createElement('canvas')
            canvas.width = w
            canvas.height = h
            const ctx = canvas.getContext('2d')

            if (!ctx) return
            ctx.drawImage(imgEl, left, top, w, h, 0, 0, w, h)

            detailImage.value = canvas.toDataURL('image/png')
        }

        return {
            uploadedImage,
            imagePreview,
            recognizing,
            showBoundingBoxes,
            showConfidence,
            showDefects,
            deviceConfidenceThreshold,
            defectConfidenceThreshold,
            selectedCategories,
            recognitionResults,
            assetCategories,
            filteredResults,
            getBboxStyle,
            onImageLoad,
            ensureImageSize,
            previewImage,
            detailImage,
            handleImageChange,
            startRecognition,
            detailViewActive,
            selectedDetail,
            selectedResultId,
            showDetailedView,
            closeDetailedView,
            resetImage,
            shouldShowLabelInside,
            isResultSelected,
            cropImage
        }
    }
})
</script>

<style scoped>
/* 图片识别面板 */
.image-recognition {
    display: flex;
    gap: 15px;
    /* 减小左右面板的间距 */
    height:calc(100vh - 120px);
    /* 占满整个视口高度 */
    box-sizing: border-box;
}

.logo {
    color: #00f5ff;
    font-size: 18px;
    font-weight: bold;
}

.left-panel {
    flex: 2;
    /* 调整左侧面板比例 */
    display: flex;
    flex-direction: column;
    gap: 20px;
    height: 100%;
}

.middle-panel {
    flex: 1;
    /* 中间面板 */
    display: flex;
    flex-direction: column;
    gap: 15px;
    max-width: 350px;
    /* 限制最大宽度 */
    height: 100%;
    max-height: 80vh;
    /* 限制最大高度，防止超出 */
}

.right-panel {
    flex: 0.8;
    /* 进一步收窄右侧面板 */
    display: flex;
    flex-direction: column;
    gap: 15px;
    max-width: 280px;
    /* 限制最大宽度 */
    height: 100%;
}

/* 卡片样式 */
:deep(.el-card) {
    background: rgba(26, 26, 46, 0.8);
    border: 1px solid rgba(0, 245, 255, 0.3);
    border-radius: 15px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    backdrop-filter: blur(10px);
    display: flex;
    flex-direction: column;
    height: 100%;
}

:deep(.el-card__header) {
    background: rgba(0, 245, 255, 0.1);
    border-bottom: 1px solid rgba(0, 245, 255, 0.3);
    padding: 12px 15px;
    /* 缩小头部高度 */
}

:deep(.el-card__body) {
    padding: 15px;
    flex: 1;
    overflow: hidden;
    display: flex;
    flex-direction: column;
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
.upload-area-wrapper {
    width: 100%;
    height: 100%;
    display: flex;
    justify-content: center;
    align-items: center;
    background: rgba(0, 245, 255, 0.05);
    border-radius: 10px;
    border: 1px dashed rgba(0, 245, 255, 0.2);
    /* 减小边框 */
}

:deep(.el-upload-dragger) {
    background: transparent;
    border: none;
    border-radius: 10px;
    width: 100%;
    height: 100%;
    transition: all 0.3s ease;
}

:deep(.el-upload-dragger:hover) {
    background: rgba(0, 245, 255, 0.05);
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

.upload-demo {
    width: 100%;
    height: 100%;
}

/* 图片控制条样式 */
.image-controls {
    padding: 15px;
    text-align: center;
    border-top: 1px solid rgba(0, 245, 255, 0.1);
    background: linear-gradient(to bottom, rgba(0, 0, 0, 0), rgba(0, 0, 0, 0.2));
    border-radius: 0 0 10px 10px;
}

/* 图片展示区域 */
.image-card {
    flex: 1;
    height: 100%;
    min-height: 0;
    /* 确保可以收缩 */
    max-height: calc(100vh - 120px);
    /* 进一步限制高度 */
}

.image-container {
    position: relative;
    width: 100%;
    height: 100%;
    display: flex;
    justify-content: center;
    align-items: center;
    border-radius: 10px;
    overflow: hidden;
    background: transparent;
    flex: 1;
    min-height: 0;
    /* 允许收缩 */
    max-height: calc(100vh - 200px);
    /* 限制容器高度，防止超出页面 */
}

.image-wrapper {
    position: relative;
    display: flex;
    justify-content: center;
    align-items: center;
    width: 100%;
    height: 100%;
    max-width: 100%;
    max-height: 100%;
}

.preview-image {
    max-width: 100%;
    max-height: calc(100vh - 250px);
    /* 进一步限制高度 */
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
    margin-bottom: 15px;
    height: auto;
    /* 控制面板高度自适应 */
}

.control-options {
    padding: 8px 0;
}

.option-item {
    margin: 12px 0;
    color: #ffffff;
}

.slider-label {
    color: #ffffff;
    font-size: 14px;
    display: block;
    margin-bottom: 8px;
}

/* 设置缺陷识别阈值滑块颜色 */
:deep(.defect-threshold-slider .el-slider__bar) {
    background: linear-gradient(to right, #ffba00, #ff4757);
}

:deep(.defect-threshold-slider .el-slider__button) {
    border-color: #ff4757;
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
    max-height: 200px;
    /* 减小高度 */
    overflow-y: auto;
}

.category-checkbox {
    display: block;
    margin: 6px 0;
    /* 减小间距 */
    color: #ffffff;
}

:deep(.el-checkbox__label) {
    color: #ffffff;
    font-size: 13px;
    /* 缩小字体 */
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
    min-height: 0;
    /* 允许结果卡片收缩 */
}

.results-list {
    height: 100%;
    overflow-y: auto;
    max-height: calc(100vh - 200px);
    /* 防止结果列表超出屏幕 */
    padding-right: 5px;
    /* 为滚动条留出空间 */
}

.result-item {
    background: rgba(0, 245, 255, 0.05);
    border: 1px solid rgba(0, 245, 255, 0.2);
    border-radius: 8px;
    padding: 12px;
    margin-bottom: 12px;
    transition: all 0.3s ease;
    cursor: pointer;
    position: relative;
    overflow: hidden;
}

.result-item:hover {
    background: rgba(0, 245, 255, 0.1);
    box-shadow: 0 4px 15px rgba(0, 245, 255, 0.3);
    transform: translateY(-2px);
}

.result-item::after {
    content: '';
    position: absolute;
    top: 0;
    right: 0;
    width: 5px;
    height: 100%;
    background: transparent;
    transition: all 0.3s ease;
}

.result-item:hover::after {
    background: rgba(0, 245, 255, 0.5);
}

.result-selected {
    background: rgba(0, 245, 255, 0.2);
    border-color: #00f5ff;
    box-shadow: 0 4px 20px rgba(0, 245, 255, 0.5);
}

.result-selected::after {
    background: #00f5ff;
}

.result-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
    padding-bottom: 6px;
    border-bottom: 1px solid rgba(0, 245, 255, 0.1);
}

.result-index {
    font-weight: bold;
    color: #00f5ff;
    font-size: 16px;
    text-shadow: 0 0 5px rgba(0, 245, 255, 0.5);
}

.result-details p {
    margin: 6px 0;
    font-size: 14px;
    color: #ccc;
    display: flex;
    align-items: center;
}

.result-details strong {
    color: #ffffff;
    margin-right: 5px;
    min-width: 80px;
    display: inline-block;
}

/* 边界框样式 */
.bounding-boxes-overlay {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
}

.bounding-box {
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    cursor: pointer;
    pointer-events: auto;
    /* 让边界框可以被点击 */
    box-shadow: 0 0 5px rgba(0, 0, 0, 0.5);
    position: relative;
}

.bounding-box:hover {
    transform: scale(1.03);
    filter: brightness(1.3);
    z-index: 10;
    box-shadow:
        0 0 8px rgba(0, 0, 0, 0.6),
        0 0 20px rgba(0, 245, 255, 0.4),
        inset 0 0 10px rgba(255, 255, 255, 0.1);
}

.bounding-box:active {
    transform: scale(0.98);
    transition: all 0.1s ease;
}

.box-normal {
    border-color: #00f5ff !important;
    background-color: rgba(0, 245, 255, 0.1) !important;
    box-shadow: 0 0 15px rgba(0, 245, 255, 0.3);
}

.box-defect {
    border-color: #ff4757 !important;
    background-color: rgba(255, 71, 87, 0.1) !important;
    box-shadow: 0 0 15px rgba(255, 71, 87, 0.3);
}

.box-label {
    position: absolute;
    top: 0;
    left: 0;
    transform: translateY(-100%);
    background-color: rgba(0, 0, 0, 0.7);
    color: white;
    padding: 2px 5px;
    font-size: min(14px, 1.8vh);
    /* 响应式字体大小 */
    white-space: nowrap;
    border-radius: 3px;
    pointer-events: none;
    max-width: 200px;
    overflow: hidden;
    text-overflow: ellipsis;
}

/* 标签在盒子内部样式 */
.label-inside {
    top: 5px;
    transform: none;
    border-radius: 4px;
    font-size: min(12px, 1.5vh);
    /* 内部标签稍小 */
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

/* 详细视图样式 */
.detail-view-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.85);
    z-index: 2000;
    /* 提高层级 */
    display: flex;
    justify-content: center;
    align-items: center;
    backdrop-filter: blur(5px);
}

.detail-view-container {
    width: 95%;
    /* 增加宽度 */
    max-width: 1400px;
    /* 增加最大宽度 */
    height: 85%;
    /* 增加高度 */
    background: rgba(26, 26, 46, 0.95);
    border: 1px solid rgba(0, 245, 255, 0.5);
    border-radius: 15px;
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
    display: flex;
    flex-direction: column;
    overflow: hidden;
}

.detail-view-header {
    padding: 15px 20px;
    border-bottom: 1px solid rgba(0, 245, 255, 0.3);
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: rgba(0, 0, 0, 0.3);
}

.detail-view-header span {
    color: #00f5ff;
    font-size: 18px;
    font-weight: bold;
}

.detail-view-content {
    flex: 1;
    display: flex;
    overflow: hidden;
}

.detail-image-container {
    flex: 2.5;
    /* 减少图片区域比例，给信息区域更多空间 */
    position: relative;
    overflow: hidden;
    display: flex;
    justify-content: center;
    align-items: center;
    padding: 15px;
    /* 减小内边距 */
    background: linear-gradient(145deg, #0E1212, #111);
    border-radius: 8px;
    margin: 10px;
    box-shadow: inset 0 0 20px rgba(0, 0, 0, 0.5);
    min-height: 300px;
    /* 确保最小高度 */
    max-height: 60vh;
    /* 限制最大高度 */
}

.detail-image-wrapper {
    position: relative;
    /* 弹性大小，根据内容自适应 */
    width: 100%;
    height: 100%;
    overflow: hidden;
    border-radius: 8px;
    box-shadow: 0 0 20px rgba(0, 245, 255, 0.2);
    border: 2px solid rgba(0, 245, 255, 0.3);
    transition: all 0.3s ease;
    background-color: #0E1212;
    /* 让容器根据裁剪内容的宽高比自适应 */
    aspect-ratio: var(--crop-aspect-ratio, 1);
    /* 确保背景图片完全覆盖容器，避免黑边 */
    background-clip: padding-box;
    /* 添加 contain 以确保图片完整显示在容器内 */
    object-fit: contain;
}

.detail-image-wrapper:hover {
    box-shadow: 0 0 30px rgba(0, 245, 255, 0.4);
    border-color: rgba(0, 245, 255, 0.5);
}

/* 使用背景图片方式，不需要detail-image样式 */

.detail-info {
    flex: 1;
    padding: 15px;
    /* 减小内边距 */
    background: rgba(0, 0, 0, 0.2);
    border-left: 1px solid rgba(0, 245, 255, 0.3);
    overflow-y: auto;
    color: #ccc;
    min-width: 250px;
    /* 设置最小宽度，防止过度挤压 */
}

.detail-info h3 {
    color: #00f5ff;
    margin-top: 0;
    border-bottom: 1px solid rgba(0, 245, 255, 0.2);
    padding-bottom: 8px;
    /* 减小底部内边距 */
    margin-bottom: 15px;
    /* 减小底部外边距 */
    font-size: 16px;
    /* 减小字体大小 */
    font-weight: 600;
}

.detail-info p {
    margin: 8px 0;
    /* 减小上下边距 */
    display: flex;
    align-items: center;
    padding: 6px;
    /* 减小内边距 */
    border-radius: 4px;
    /* 减小圆角 */
    background: rgba(0, 245, 255, 0.05);
    transition: all 0.3s ease;
    font-size: 13px;
    /* 减小字体大小 */
    line-height: 1.4;
    /* 调整行高 */
}

.detail-info p:hover {
    background: rgba(0, 245, 255, 0.1);
    transform: translateX(3px);
    /* 减小悬停偏移 */
}

.detail-info strong {
    color: #fff;
    display: inline-block;
    width: 80px;
    /* 减小标签宽度 */
    font-weight: 500;
    font-size: 12px;
    /* 减小标签字体 */
    flex-shrink: 0;
    /* 防止标签被挤压 */
}

/* 滚动条样式 */
::-webkit-scrollbar {
    width: 6px;
}

::-webkit-scrollbar-track {
    background: rgba(0, 0, 0, 0.2);
    border-radius: 3px;
}

::-webkit-scrollbar-thumb {
    background: rgba(0, 245, 255, 0.6);
    border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
    background: rgba(0, 245, 255, 0.8);
}

/* 自定义按钮样式 */
.custom-btn {
    transition: all 0.3s ease;
    position: relative;
    overflow: hidden;
    border-radius: 8px;
    margin: 0 10px;
    font-size: 16px;
    padding: 12px 24px;
    letter-spacing: 0.8px;
    font-weight: 600;
    min-width: 140px;
}

.custom-btn::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg,
            rgba(255, 255, 255, 0) 0%,
            rgba(255, 255, 255, 0.1) 50%,
            rgba(255, 255, 255, 0) 100%);
    transition: all 0.6s ease;
}

.custom-btn:hover::before {
    left: 100%;
}

.btn-icon {
    margin-right: 8px;
    font-size: 18px;
}

.recognize-btn {
    background: linear-gradient(135deg, #28a745, #20c997) !important;
    border-color: #20c997 !important;
    box-shadow: 0 2px 10px rgba(32, 201, 151, 0.3);
}

.recognize-btn:hover {
    box-shadow: 0 4px 15px rgba(32, 201, 151, 0.5);
    transform: translateY(-2px);
}

.reset-btn {
    background: linear-gradient(135deg, #2c3e50, #3498db) !important;
    border-color: #3498db !important;
    box-shadow: 0 2px 10px rgba(52, 152, 219, 0.3);
}

.reset-btn:hover {
    box-shadow: 0 4px 15px rgba(52, 152, 219, 0.5);
    transform: translateY(-2px);
}

.return-btn {
    background: linear-gradient(135deg, #34495e, #7f8c8d) !important;
    border-color: #7f8c8d !important;
    box-shadow: 0 2px 10px rgba(127, 140, 141, 0.3);
}

.return-btn:hover {
    box-shadow: 0 4px 15px rgba(127, 140, 141, 0.5);
    transform: translateY(-2px);
}

/* 添加脉冲边框动画 */
@keyframes pulse-border {
    0% {
        box-shadow:
            0 0 0 1px rgba(0, 245, 255, 0.3),
            0 0 0 4px rgba(0, 245, 255, 0.1),
            0 0 30px rgba(0, 0, 0, 0.5);
    }

    50% {
        box-shadow:
            0 0 0 1px rgba(0, 245, 255, 0.5),
            0 0 0 8px rgba(0, 245, 255, 0.2),
            0 0 30px rgba(0, 0, 0, 0.5);
    }

    100% {
        box-shadow:
            0 0 0 1px rgba(0, 245, 255, 0.3),
            0 0 0 4px rgba(0, 245, 255, 0.1),
            0 0 30px rgba(0, 0, 0, 0.5);
    }
}

/* 设备脉冲动画 */
@keyframes device-pulse {
    0% {
        box-shadow: 0 0 15px currentColor;
        opacity: 1;
    }

    50% {
        box-shadow: 0 0 25px currentColor;
        opacity: 0.8;
    }

    100% {
        box-shadow: 0 0 15px currentColor;
        opacity: 1;
    }
}

/* 响应式设计 */
@media (max-width: 1400px) {
    .image-recognition {
        gap: 10px;
    }

    .middle-panel {
        max-width: 300px;
    }

    .right-panel {
        max-width: 250px;
    }

    .detail-view-container {
        width: 90%;
        height: 80%;
    }

    .detail-info {
        min-width: 200px;
    }

    .detail-info p {
        font-size: 12px;
    }

    .detail-info strong {
        width: 70px;
        font-size: 11px;
    }
}

@media (max-width: 1200px) {
    .image-recognition {
        flex-direction: column;
        padding-top: 70px;
        height: auto;
    }

    .left-panel,
    .middle-panel,
    .right-panel {
        flex: none;
        max-width: 100%;
        height: auto;
        max-height: none;
    }

    .middle-panel {
        order: 2;
        max-height: 400px;
        /* 移动端限制高度 */
    }

    .right-panel {
        order: 3;
    }

    .detail-view-content {
        flex-direction: column;
    }

    .detail-info {
        border-left: none;
        border-top: 1px solid rgba(0, 245, 255, 0.3);
        min-width: auto;
    }

    .detail-image-container {
        flex: 1;
        min-height: 250px;
        /* 移动端保证足够的图片显示空间 */
        max-height: 40vh;
        /* 限制最大高度，留出空间给信息区域 */
    }

    .detail-image-wrapper {
        min-height: 200px;
        /* 移动端最小高度调整 */
    }

    .results-list {
        max-height: 350px;
    }

    .detail-view-container {
        width: 95%;
        /* 移动端增加可视区域 */
        height: 85%;
        /* 调整高度比例 */
        margin: auto;
    }
}

/* 添加更小屏幕的适配 */
@media (max-width: 768px) {
    .detail-view-container {
        width: 98%;
        height: 90%;
        padding: 10px;
    }

    .detail-image-container {
        padding: 10px;
        margin: 5px;
        min-height: 200px;
        max-height: 35vh;
    }

    .detail-info {
        padding: 10px;
        font-size: 12px;
    }

    .detail-info h3 {
        font-size: 14px;
        margin-bottom: 10px;
    }

    .detail-info p {
        margin: 6px 0;
        padding: 4px;
        font-size: 11px;
    }

    .detail-info strong {
        width: 60px;
        font-size: 10px;
    }
}
</style>
