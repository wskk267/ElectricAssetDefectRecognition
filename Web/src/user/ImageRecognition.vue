<template>
    <div class="image-recognition">
        <div class="left-panel">
            <!-- 合并上传和预览区域 -->
            <div class="image-display-section">
                <div class="app-card">
                    <div class="app-card-header">
                        <span><el-icon>
                                <Picture />
                            </el-icon> 图片识别</span>
                    </div>

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
                            <div class="image-content">
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
                        </div>

                        <!-- 放大视图模式 -->
                        <div v-if="detailViewActive" class="detail-view-overlay" @click="closeDetailedView">
                            <div class="detail-view-container" @click.stop>
                                <div class="detail-view-header">
                                    <span>设备详情 #{{ selectedDetail.id }}</span> 
                                    <button class="btn-secondary" @click="closeDetailedView">
                                        <el-icon class="btn-icon">
                                            <Back />
                                        </el-icon>返回
                                    </button>
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
                        <button class="btn-primary" @click="resetImage">
                            <el-icon class="btn-icon">
                                <RefreshRight />
                            </el-icon>重新上传
                        </button>
                        <button class="btn-success" :disabled="recognizing"
                            @click="startRecognition">
                            <el-icon class="btn-icon">
                                <Monitor />
                            </el-icon>
                            {{ recognizing ? '识别中...' : '开始识别' }}
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <!-- 中间识别结果面板 -->
        <div v-if="recognitionResults.length > 0" class="middle-panel">
            <div class="app-card">
                <div class="app-card-header">
                    <span><el-icon>
                            <DataAnalysis />
                        </el-icon> 识别结果</span>
                    <div class="app-card-actions">
                        <button class="btn-secondary btn-sm" @click="exportResults">
                            <el-icon><Download /></el-icon>
                            导出结果
                        </button>
                    </div>
                </div>

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
            </div>
        </div>

        <!-- 右侧控制面板 -->
        <div class="right-panel">
            <!-- 显示选项 -->
            <div class="app-card">
                <div class="app-card-header">
                    <span><el-icon>
                            <Setting />
                        </el-icon> 显示选项</span>
                </div>

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
            </div>

            <!-- 类别筛选 -->
            <div class="app-card">
                <div class="app-card-header">
                    <span><el-icon>
                            <Menu />
                        </el-icon> 设备类别筛选</span>
                </div>

                <div class="category-filter">
                    <el-checkbox-group v-model="selectedCategories">
                        <el-checkbox v-for="category in assetCategories" :key="category" :label="category"
                            class="category-checkbox">
                            {{ category }}
                        </el-checkbox>
                    </el-checkbox-group>
                </div>
            </div>
        </div>
    </div>
</template>

<script lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, defineComponent, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { Setting, Upload, Monitor, RefreshRight, Back, Picture, Menu, DataAnalysis, Download } from '@element-plus/icons-vue'
import axiosInstance from '../axios'
import { formatTime, downloadFile, generateCSV } from '../utils/common'

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
        RefreshRight,
        Download
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

        // 窗口大小变化监听器的引用
        let resizeListener: (() => void) | null = null

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
            
            // 添加窗口大小变化监听器
            resizeListener = () => {
                if (recognitionResults.value.length > 0) {
                    // 防抖处理，避免频繁重新计算
                    setTimeout(() => {
                        updateBoundingBoxes()
                    }, 150)
                }
            }
            window.addEventListener('resize', resizeListener)
        })

        // 组件卸载时清理
        onUnmounted(() => {
            cleanup()
        })
        
        // 清理函数
        const cleanup = () => {
            if (resizeListener) {
                window.removeEventListener('resize', resizeListener)
                resizeListener = null
            }
        }

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
            if (!previewImage.value) return { display: 'none' }

            const img = previewImage.value
            
            // 等待图片完全加载
            if (!img.complete || img.naturalWidth === 0) {
                return { display: 'none' }
            }

            // 确保结果数据有效
            if (!result || !result.center || typeof result.width !== 'number' || typeof result.height !== 'number') {
                return { display: 'none' }
            }

            // 新的简化方法：直接基于图片的实际显示尺寸计算
            // 获取图片的显示尺寸
            const imgDisplayWidth = img.offsetWidth
            const imgDisplayHeight = img.offsetHeight
            
            // 确保图片已正确渲染并有有效尺寸
            if (imgDisplayWidth === 0 || imgDisplayHeight === 0) {
                return { display: 'none' }
            }

            // 基于百分比直接计算边界框位置（相对于图片）
            const centerXPercent = result.center.x
            const centerYPercent = result.center.y
            const widthPercent = result.width
            const heightPercent = result.height

            // 计算边界框的尺寸和位置（相对于图片）
            const boxWidth = widthPercent * imgDisplayWidth
            const boxHeight = heightPercent * imgDisplayHeight
            const boxLeft = (centerXPercent - widthPercent / 2) * imgDisplayWidth
            const boxTop = (centerYPercent - heightPercent / 2) * imgDisplayHeight

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
                pointerEvents: 'auto' as const,
                zIndex: 10
            }
        }

        // 判断标签是否应该显示在边界框内部
        const shouldShowLabelInside = (result) => {
            if (!previewImage.value) return false

            const img = previewImage.value
            const imgDisplayHeight = img.offsetHeight
            
            if (imgDisplayHeight === 0) return false
            
            // 计算边界框顶部位置
            const boxTop = (result.center.y - result.height / 2) * imgDisplayHeight

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

            // 图片加载完成后，如果有识别结果，重新计算边界框位置
            if (recognitionResults.value.length > 0) {
                setTimeout(() => {
                    updateBoundingBoxes()
                }, 100) // 给图片一点时间完全渲染
            }
        }

        // 更新边界框位置的方法
        const updateBoundingBoxes = () => {
            // 确保图片完全加载
            if (!previewImage.value || !previewImage.value.complete) {
                setTimeout(updateBoundingBoxes, 100)
                return
            }
            
            // 等待DOM更新完成并强制重新计算
            nextTick(() => {
                // 触发响应式更新，强制重新计算边界框位置
                if (recognitionResults.value.length > 0) {
                    const results = [...recognitionResults.value]
                    recognitionResults.value = []
                    
                    // 使用requestAnimationFrame确保在下一个渲染帧执行
                    requestAnimationFrame(() => {
                        setTimeout(() => {
                            recognitionResults.value = results
                            // 再次确保图片尺寸数据正确
                            ensureImageSize()
                        }, 100) // 增加延迟确保布局完全稳定
                    })
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

                // 获取token进行认证
                const token = localStorage.getItem('token')

                // 调用后端API
                const response = await axiosInstance.post('/api/predict', formData, {
                    headers: {
                        'Content-Type': 'multipart/form-data',
                        'Authorization': `Bearer ${token}`
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
                    
                    // 等待DOM更新完成后重新计算边界框位置
                    // 使用多重等待确保布局完全稳定
                    await nextTick()
                    // 再等待一个动画帧，确保CSS布局完全完成
                    await new Promise(resolve => requestAnimationFrame(resolve))
                } else {
                    console.error('识别失败:', result.error || result.message)
                    // 根据错误类型显示不同的消息
                    if (result.error_type === 'quota_exceeded') {
                        ElMessage.error(`识别次数已用完！${result.message}`)
                    } else {
                        ElMessage.error(result.error || result.message || '识别失败，请重试')
                    }
                    recognitionResults.value = []
                }
            } catch (error) {
                console.error('API调用失败:', error)
                // 检查是否是 HTTP 错误
                if (error.response && error.response.data) {
                    const errorData = error.response.data
                    if (errorData.error_type === 'quota_exceeded') {
                        ElMessage.error(`识别次数已用完！${errorData.message}`)
                    } else {
                        ElMessage.error(errorData.message || '网络请求失败')
                    }
                } else {
                    ElMessage.error('网络连接失败，请检查后端服务是否启动')
                }
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

        // 导出识别结果
        const exportResults = () => {
            if (recognitionResults.value.length === 0) {
                ElMessage.warning('暂无识别结果可导出')
                return
            }

            const exportData = filteredResults.value.map(result => ({
                '设备ID': result.id,
                '设备类别': result.asset_category,
                '缺陷状态': result.defect_status,
                '置信度': `${(result.confidence * 100).toFixed(1)}%`,
                '中心位置X': `${(result.center.x * 100).toFixed(1)}%`,
                '中心位置Y': `${(result.center.y * 100).toFixed(1)}%`,
                '宽度': `${(result.width * 100).toFixed(1)}%`,
                '高度': `${(result.height * 100).toFixed(1)}%`,
                '导出时间': formatTime(new Date())
            }))

            const headers = ['设备ID', '设备类别', '缺陷状态', '置信度', '中心位置X', '中心位置Y', '宽度', '高度', '导出时间']
            const csvContent = generateCSV(exportData, headers, (item) => Object.values(item))
            const filename = `图片识别结果_${new Date().toISOString().slice(0, 10)}.csv`
            downloadFile(csvContent, filename, 'text/csv')
            
            ElMessage.success(`导出成功！共导出 ${exportData.length} 条记录`)
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
            updateBoundingBoxes,
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
            cropImage,
            exportResults
        }
    }
})
</script>

<style scoped>
/* 图片识别面板 */
.image-recognition {
    display: flex;
    gap: 15px;
    height: calc(100vh - 120px);
    box-sizing: border-box;
}

.left-panel {
    flex: 2;
    display: flex;
    flex-direction: column;
    gap: 20px;
    height: 100%;
}

.middle-panel {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 15px;
    max-width: 350px;
    height: 100%;
    max-height: 80vh;
}

.right-panel {
    flex: 0.8;
    display: flex;
    flex-direction: column;
    gap: 15px;
    max-width: 280px;
    height: 100%;
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
    color: var(--primary-color);
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
    max-height: calc(100vh - 200px);
    /* 确保布局稳定 */
    transition: all 0.2s ease;
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
    /* 防止布局闪烁 */
    contain: layout style;
}

.image-content {
    position: relative;
    display: inline-block;
    max-width: 100%;
    max-height: 100%;
}

.preview-image {
    max-width: 100%;
    max-height: calc(100vh - 250px);
    width: auto;
    height: auto;
    object-fit: contain;
    display: block;
    border-radius: 8px;
    /* 防止图片重排导致的布局跳动 */
    transition: none;
}

.bounding-boxes-overlay {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
    z-index: 10;
}

/* 控制面板样式 */
.control-options {
    padding: 20px 24px;
}

.option-item {
    margin: 18px 0;
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
    --el-slider-main-bg-color: var(--primary-color);
    --el-slider-runway-bg-color: rgba(255, 255, 255, 0.2);
}

:deep(.el-slider__button) {
    border: 2px solid var(--primary-color);
    background: var(--primary-color);
}

:deep(.el-switch) {
    --el-switch-on-color: var(--primary-color);
    --el-switch-off-color: #666;
}

:deep(.el-switch__label) {
    color: #ffffff;
}

/* 类别筛选 */
.category-filter {
    max-height: 200px;
    overflow-y: auto;
    padding: 20px 24px;
}

.category-checkbox {
    display: block;
    margin: 10px 0;
    color: #ffffff;
}

:deep(.el-checkbox__label) {
    color: #ffffff;
    font-size: 13px;
}

:deep(.el-checkbox__input.is-checked .el-checkbox__inner) {
    background-color: var(--primary-color);
    border-color: var(--primary-color);
}

:deep(.el-checkbox__inner:hover) {
    border-color: var(--primary-color);
}

/* 识别结果 */
.results-list {
    height: 100%;
    overflow-y: auto;
    max-height: calc(100vh - 200px);
    padding-right: 5px;
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

.result-selected {
    background: rgba(0, 245, 255, 0.2);
    border-color: var(--primary-color);
    box-shadow: 0 4px 20px rgba(0, 245, 255, 0.5);
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
    color: var(--primary-color);
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
.bounding-box {
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    cursor: pointer;
    pointer-events: auto;
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

.box-label {
    position: absolute;
    top: 0;
    left: 0;
    transform: translateY(-100%);
    background-color: rgba(0, 0, 0, 0.7);
    color: white;
    padding: 2px 5px;
    font-size: min(14px, 1.8vh);
    white-space: nowrap;
    border-radius: 3px;
    pointer-events: none;
    max-width: 200px;
    overflow: hidden;
    text-overflow: ellipsis;
}

.label-inside {
    top: 5px;
    transform: none;
    border-radius: 4px;
    font-size: min(12px, 1.5vh);
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
    display: flex;
    justify-content: center;
    align-items: center;
    backdrop-filter: blur(5px);
}

.detail-view-container {
    width: 95%;
    max-width: 1400px;
    height: 85%;
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
    color: var(--primary-color);
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
    position: relative;
    overflow: hidden;
    display: flex;
    justify-content: center;
    align-items: center;
    padding: 15px;
    background: linear-gradient(145deg, #0E1212, #111);
    border-radius: 8px;
    margin: 10px;
    box-shadow: inset 0 0 20px rgba(0, 0, 0, 0.5);
    min-height: 300px;
    max-height: 60vh;
}

.detail-image-wrapper {
    position: relative;
    width: 100%;
    height: 100%;
    overflow: hidden;
    border-radius: 8px;
    box-shadow: 0 0 20px rgba(0, 245, 255, 0.2);
    border: 2px solid rgba(0, 245, 255, 0.3);
    transition: all 0.3s ease;
    background-color: #0E1212;
}

.detail-image-wrapper:hover {
    box-shadow: 0 0 30px rgba(0, 245, 255, 0.4);
    border-color: rgba(0, 245, 255, 0.5);
}

.detail-info {
    flex: 1;
    padding: 15px;
    background: rgba(0, 0, 0, 0.2);
    border-left: 1px solid rgba(0, 245, 255, 0.3);
    overflow-y: auto;
    color: #ccc;
    min-width: 250px;
}

.detail-info h3 {
    color: var(--primary-color);
    margin-top: 0;
    border-bottom: 1px solid rgba(0, 245, 255, 0.2);
    padding-bottom: 8px;
    margin-bottom: 15px;
    font-size: 16px;
    font-weight: 600;
}

.detail-info p {
    margin: 8px 0;
    display: flex;
    align-items: center;
    padding: 6px;
    border-radius: 4px;
    background: rgba(0, 245, 255, 0.05);
    transition: all 0.3s ease;
    font-size: 13px;
    line-height: 1.4;
}

.detail-info p:hover {
    background: rgba(0, 245, 255, 0.1);
    transform: translateX(3px);
}

.detail-info strong {
    color: #fff;
    display: inline-block;
    width: 80px;
    font-weight: 500;
    font-size: 12px;
    flex-shrink: 0;
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
}

@media (max-width: 1200px) {
    .image-recognition {
        flex-direction: column;
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
        max-height: 40vh;
    }
}

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
}
</style>
