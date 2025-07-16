<template>
    <div class="batch-processing">
        <!-- 文件上传区域 -->
        <div class="app-card">
            <div class="app-card-header">
                <span><el-icon><FolderOpened /></el-icon> 批量文件处理</span>
            </div>

            <div class="upload-section">
                <el-upload
                    ref="uploadRef"
                    class="upload-demo"
                    drag
                    :multiple="true"
                    :auto-upload="false"
                    :show-file-list="true"
                    :file-list="fileList"
                    :on-change="handleFileChange"
                    :on-remove="handleFileRemove"
                    :before-upload="beforeUpload"
                    accept="image/*,video/*"
                    :limit="100"
                    :on-exceed="handleExceed"
                >
                    <div class="upload-area">
                        <el-icon class="upload-icon"><Upload /></el-icon>
                        <div class="upload-text">点击或拖拽文件到此区域上传</div>
                        <div class="upload-hint">
                            支持图片(JPG、PNG、BMP)和视频文件<br/>
                            最多100个文件，总大小不超过100MB
                        </div>
                    </div>
                </el-upload>

                <div class="file-info" v-if="fileList.length > 0">
                    <div class="size-info">
                        <span>已选择 {{ fileList.length }} 个文件</span>
                        <span class="size-text" :class="{ 'size-exceeded': totalSize > maxSize }">
                            总大小: {{ formatFileSize(totalSize) }} / {{ formatFileSize(maxSize) }}
                        </span>
                    </div>
                    
                    <div class="action-buttons">
                        <button class="btn-primary" 
                            :disabled="processing || fileList.length === 0 || totalSize > maxSize"
                            v-if="!processing"
                            @click="startBatchProcessing"
                        >
                            <el-icon><VideoPlay /></el-icon>
                            开始批量处理
                        </button>
                        
                        <button class="btn-danger" 
                            @click="cancelProcessing"
                            v-if="processing && currentTaskId"
                        >
                            <el-icon><CircleClose /></el-icon>
                            取消处理
                        </button>
                        
                        <button class="btn-secondary"
                            :disabled="processing"
                            @click="clearFiles"
                        >
                            <el-icon><Delete /></el-icon>
                            清空文件
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <!-- 处理进度区域 -->
        <div class="app-card" v-if="processing || processedFiles.length > 0">
            <div class="app-card-header">
                <span><el-icon><DataAnalysis /></el-icon> 处理进度</span>
                <div class="app-card-actions" v-if="processing">
                    <span class="status-text">请保持网页连接，处理中断会导致任务失败</span>
                    <span class="timer-text">已用时: {{ formatElapsedTime(elapsedTime) }}</span>
                </div>
            </div>

            <div class="progress-section">
                <!-- 总体进度 -->
                <div class="overall-progress" v-if="processing">
                    <div class="progress-header">
                        <span>总体进度</span>
                        <span>{{ Math.round(overallProgress) }}%</span>
                    </div>
                    <el-progress 
                        :percentage="Math.round(overallProgress)" 
                        :stroke-width="8"
                        :show-text="false"
                        status="success"
                        class="animated-progress"
                    />
                    <div class="progress-info">
                        已完成 {{ completedCount }} / {{ totalCount }} 个文件
                    </div>
                </div>

                <!-- 当前处理文件 -->
                <div class="current-processing" v-if="currentFile">
                    <div class="current-file-info">
                        <el-icon class="processing-icon"><Loading /></el-icon>
                        正在处理: {{ currentFile.name }}
                        
                        <!-- 当前文件进度条 -->
                        <div class="current-file-progress" v-if="currentFileProgress > 0">
                            <div class="file-progress-header">
                                <span>文件进度</span>
                                <span>{{ Math.round(currentFileProgress) }}%</span>
                            </div>
                            <el-progress 
                                :percentage="Math.round(currentFileProgress)" 
                                :stroke-width="6"
                                :show-text="false"
                                status="warning"
                                class="file-progress-bar"
                            />
                        </div>
                    </div>
                </div>

                <!-- 处理结果列表 -->
                <div class="results-list" v-if="processedFiles.length > 0">
                    <h4>处理结果</h4>
                    <div class="result-item" v-for="(result, index) in processedFiles" :key="index">
                        <!-- 结果卡片头部 -->
                        <div class="result-header">
                            <div class="result-info">
                                <el-icon 
                                    class="result-icon" 
                                    :class="{ 'success': result.success, 'error': !result.success }"
                                >
                                    <Check v-if="result.success" />
                                    <Close v-else />
                                </el-icon>
                                <div class="file-details">
                                    <span class="file-name">{{ result.filename }}</span>
                                    <span class="file-size">{{ formatFileSize(result.size) }}</span>
                                </div>
                            </div>
                            
                            <div class="result-actions">
                                <div class="result-details" v-if="result.success">
                                    <!-- 基本检测信息 -->
                                    <span class="detection-count">
                                        检测到 {{ result.detectionCount }} 个目标
                                    </span>
                                    
                                    <!-- 视频额外信息 -->
                                    <div v-if="result.data && result.data.video_info" class="video-info">
                                        <span class="video-detail">
                                            {{ Math.round(result.data.video_info.duration_seconds) }}秒
                                        </span>
                                        <span class="video-detail">
                                            {{ result.data.video_info.processed_frames }}帧
                                        </span>
                                    </div>
                                </div>
                                <span v-else class="error-msg">{{ result.error }}</span>
                                
                                <div class="action-buttons">
                                    <el-button 
                                        v-if="result.success && result.data.annotated_image" 
                                        type="info" 
                                        size="small"
                                        @click="previewImage(result)"
                                    >
                                        <el-icon><View /></el-icon>
                                        预览图片
                                    </el-button>
                                    
                                    <el-button 
                                        v-if="result.success && result.data.annotated_video" 
                                        type="warning" 
                                        size="small"
                                        @click="previewVideo(result)"
                                    >
                                        <el-icon><VideoPlay /></el-icon>
                                        预览视频
                                    </el-button>
                                    
                                    <el-button 
                                        v-if="result.success && result.downloadUrl" 
                                        type="primary" 
                                        size="small"
                                        @click="downloadResult(result)"
                                    >
                                        <el-icon><Download /></el-icon>
                                        下载数据
                                    </el-button>
                                </div>
                            </div>
                        </div>
                        
                        <!-- 可展开的预览区域 -->
                        <div v-if="result.showPreview" class="preview-area">
                            <!-- 图片预览 -->
                            <div v-if="result.data.annotated_image" class="image-preview">
                                <img :src="result.data.annotated_image" alt="标注结果" class="annotated-image" />
                            </div>
                            
                            <!-- 视频预览 -->
                            <div v-if="result.data.annotated_video || result.data.video_too_large" class="video-preview">
                                <!-- 视频过大提示 -->
                                <div v-if="result.data.video_too_large" class="video-too-large-notice">
                                    <el-alert
                                        title="视频文件过大"
                                        :description="`处理后的视频文件大小为 ${result.data.video_size_mb?.toFixed(3)} MB，超出浏览器播放限制。`"
                                        type="warning"
                                        show-icon
                                        :closable="false"
                                    />
                                    <div class="video-info-display">
                                        <h4>视频处理结果:</h4>
                                        <p>分辨率: {{ result.data.video_info?.resolution }}</p>
                                        <p>帧率: {{ result.data.video_info?.fps }} FPS</p>
                                        <p>时长: {{ result.data.video_info?.duration_seconds?.toFixed(1) }} 秒</p>
                                        <p>检测目标总数: {{ result.data.detected_objects }}</p>
                                    </div>
                                </div>
                                
                                <!-- 正常视频播放 -->
                                <div v-else-if="result.data.annotated_video">
                                    <video 
                                        :src="result.data.annotated_video" 
                                        controls 
                                        class="annotated-video"
                                        preload="metadata"
                                        @error="handleVideoError"
                                        @loadstart="handleVideoLoadStart"
                                        @canplay="handleVideoCanPlay"
                                        @loadedmetadata="handleVideoMetadata"
                                    >
                                        您的浏览器不支持视频播放
                                    </video>
                                    <div class="video-debug-info">
                                        <p>视频数据类型: {{ getVideoDataType(result.data.annotated_video) }}</p>
                                        <p>数据大小: {{ getVideoDataLength(result.data.annotated_video) }}</p>
                                        <p>文件大小: {{ result.data.video_info?.file_size_mb?.toFixed(3) }} MB</p>
                                        <p>视频状态: {{ getVideoStatus(result.filename) }}</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- 批量下载 -->
                <div class="batch-download" v-if="completedCount > 0 && !processing">
                    <el-button 
                        type="success" 
                        @click="downloadAllResults"
                        :disabled="!hasSuccessfulResults"
                    >
                        <el-icon><Download /></el-icon>
                        批量下载所有结果 ({{ successfulCount }} 个文件)
                    </el-button>
                </div>
            </div>
        </div>
    </div>
</template>

<script lang="ts">
import { defineComponent, ref, computed, nextTick, onMounted, onUnmounted } from 'vue'
import { 
    FolderOpened, Upload, VideoPlay, Delete, DataAnalysis, 
    Loading, Check, Close, Download, View, CircleClose 
} from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox, ElAlert } from 'element-plus'
import type { UploadFile, UploadFiles, UploadRawFile } from 'element-plus'
import axiosInstance from '../axios'
import { formatTime, downloadFile, formatFileSize } from '../utils/common'

interface ProcessedFile {
    filename: string
    size: number
    success: boolean
    error?: string
    detectionCount?: number
    downloadUrl?: string
    downloadFilename?: string
    data?: any
    showPreview?: boolean
}

export default defineComponent({
    name: 'BatchProcessing',
    components: {
        FolderOpened,
        Upload,
        VideoPlay,
        Delete,
        DataAnalysis,
        Loading,
        Check,
        Close,
        Download,
        View,
        CircleClose
    },
    setup() {
        const uploadRef = ref()
        const fileList = ref<UploadFiles>([])
        const processing = ref(false)
        const currentFile = ref<UploadFile | null>(null)
        const processedFiles = ref<ProcessedFile[]>([])
        const completedCount = ref(0)
        const totalCount = ref(0)
        
        const maxSize = 100 * 1024 * 1024 // 100MB
        const maxFiles = 100
        
        // 新增进度相关状态
        const currentTaskId = ref<string | null>(null)
        const currentFileProgress = ref<number>(0)
        const progressPollInterval = ref<number | null>(null)
        const pollFailureCount = ref<number>(0) // 轮询失败计数器
        
        // 计时器相关
        const processingStartTime = ref<number>(0)
        const elapsedTime = ref<number>(0)
        const timeInterval = ref<number | null>(null)

        // 计算总文件大小
        const totalSize = computed(() => {
            return fileList.value.reduce((total, file) => {
                return total + (file.size || 0)
            }, 0)
        })

        // 总体进度
        const overallProgress = computed(() => {
            if (totalCount.value === 0) return 0
            const fileProgress = completedCount.value / totalCount.value
            const currentProgress = currentFileProgress.value / 100.0
            if (totalCount.value > 0 && completedCount.value < totalCount.value) {
                // 加上当前文件的进度权重
                const currentFileWeight = 1.0 / totalCount.value
                return (fileProgress + currentProgress * currentFileWeight) * 100
            }
            return fileProgress * 100
        })

        // 成功处理的文件数量
        const successfulCount = computed(() => {
            return processedFiles.value.filter(file => file.success).length
        })

        // 是否有成功的结果
        const hasSuccessfulResults = computed(() => {
            return successfulCount.value > 0
        })

        // 格式化经过时间
        const formatElapsedTime = (seconds: number): string => {
            const minutes = Math.floor(seconds / 60)
            const remainingSeconds = seconds % 60
            return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`
        }

        // 开始计时
        const startTimer = () => {
            processingStartTime.value = Date.now()
            elapsedTime.value = 0
            
            timeInterval.value = window.setInterval(() => {
                elapsedTime.value = Math.floor((Date.now() - processingStartTime.value) / 1000)
            }, 1000)
        }

        // 停止计时
        const stopTimer = () => {
            if (timeInterval.value) {
                clearInterval(timeInterval.value)
                timeInterval.value = null
            }
        }

        // 文件类型检查
        const isValidFileType = (file: File): boolean => {
            const imageTypes = ['image/jpeg', 'image/png', 'image/bmp', 'image/jpg']
            const videoTypes = ['video/mp4', 'video/avi', 'video/mov', 'video/mkv', 'video/wmv']
            return [...imageTypes, ...videoTypes].includes(file.type)
        }

        // 文件变化处理
        const handleFileChange = (uploadFile: UploadFile, uploadFiles: UploadFiles) => {
            // 检查文件类型
            if (uploadFile.raw && !isValidFileType(uploadFile.raw)) {
                ElMessage.error(`文件 ${uploadFile.name} 格式不支持`)
                return
            }

            fileList.value = uploadFiles
            
            // 检查总大小
            if (totalSize.value > maxSize) {
                ElMessage.warning('文件总大小超过100MB限制')
            }
        }

        // 文件移除处理
        const handleFileRemove = (uploadFile: UploadFile, uploadFiles: UploadFiles) => {
            fileList.value = uploadFiles
        }

        // 上传前检查
        const beforeUpload = (rawFile: UploadRawFile) => {
            if (!isValidFileType(rawFile)) {
                ElMessage.error('不支持的文件格式')
                return false
            }
            return false // 阻止自动上传
        }

        // 文件数量超限处理
        const handleExceed = () => {
            ElMessage.warning(`最多只能选择 ${maxFiles} 个文件`)
        }

        // 清空文件
        const clearFiles = () => {
            fileList.value = []
            processedFiles.value = []
            completedCount.value = 0
            totalCount.value = 0
            currentFileProgress.value = 0
        }

        // 开始批量处理
        const startBatchProcessing = async () => {
            if (fileList.value.length === 0) {
                ElMessage.warning('请先选择文件')
                return
            }

            if (totalSize.value > maxSize) {
                ElMessage.error('文件总大小超过100MB限制')
                return
            }

            try {
                await ElMessageBox.confirm(
                    '开始批量处理后，请保持网页连接，否则处理会中断。确认开始？',
                    '批量处理确认',
                    {
                        confirmButtonText: '开始处理',
                        cancelButtonText: '取消',
                        type: 'warning',
                    }
                )
            } catch {
                return
            }

            processing.value = true
            processedFiles.value = []
            completedCount.value = 0
            totalCount.value = fileList.value.length
            currentFileProgress.value = 0
            
            // 开始计时
            startTimer()

            try {
                // 使用新的批量处理API
                const formData = new FormData()
                
                // 添加所有文件到FormData
                fileList.value.forEach(uploadFile => {
                    if (uploadFile.raw) {
                        formData.append('files', uploadFile.raw)
                    }
                })

                const response = await axiosInstance.post('/api/batch', formData, {
                    headers: {
                        'Content-Type': 'multipart/form-data'
                    },
                    timeout: 10000 // 10秒超时，因为这个API现在会立即返回
                })

                const batchResult = response.data
                
                if (batchResult.success && batchResult.task_id) {
                    // 保存任务ID，用于取消操作和轮询进度
                    currentTaskId.value = batchResult.task_id
                    
                    ElMessage.success('批量处理已启动，正在后台处理...')
                    
                    // 开始轮询进度
                    startProgressPolling()
                } else {
                    throw new Error(batchResult.message || '批量处理启动失败')
                }

            } catch (error) {
                console.error('批量处理失败:', error)
                
                // 检查是否是 HTTP 错误
                if (error.response && error.response.data) {
                    const errorData = error.response.data
                    if (errorData.error_type === 'quota_exceeded') {
                        ElMessage.error(`批量处理流量不足！${errorData.message}`)
                    } else {
                        ElMessage.error(errorData.message || '批量处理请求失败')
                    }
                } else {
                    ElMessage.error(error instanceof Error ? error.message : '批量处理失败')
                }
                
                processing.value = false
                currentFile.value = null
                currentTaskId.value = null
                currentFileProgress.value = 0
                stopTimer()
            }
        }

        // 开始轮询进度
        const startProgressPolling = () => {
            if (progressPollInterval.value) {
                clearInterval(progressPollInterval.value)
            }

            pollFailureCount.value = 0 // 重置失败计数

            progressPollInterval.value = window.setInterval(async () => {
                try {
                    if (!currentTaskId.value || !processing.value) {
                        stopProgressPolling()
                        return
                    }

                    const response = await axiosInstance.get(`/api/progress/${currentTaskId.value}`)
                    
                    // 重置失败计数
                    pollFailureCount.value = 0
                    
                    if (response.data.success) {
                        const progress = response.data.progress
                        
                        // 更新进度信息
                        completedCount.value = progress.current_file_index || 0
                        currentFileProgress.value = progress.current_file_progress || 0
                        
                        // 更新当前处理文件
                        if (progress.current_file_name) {
                            currentFile.value = { 
                                name: progress.current_file_name,
                                status: 'uploading',
                                uid: Date.now()
                            } as UploadFile
                        }
                        
                        // 检查是否完成
                        if (progress.stage === 'completed' || progress.stage === 'cancelled' || progress.stage === 'error') {
                            stopProgressPolling()
                            
                            // 处理最终结果
                            if (progress.processed_files && progress.processed_files.length > 0) {
                                processBatchResults(progress.processed_files)
                            }
                            
                            // 结束处理
                            processing.value = false
                            currentFile.value = null
                            currentTaskId.value = null
                            currentFileProgress.value = 0
                            stopTimer()
                            
                            // 显示完成消息
                            if (progress.stage === 'completed') {
                                ElMessage.success(`批量处理完成！成功处理 ${successfulCount.value} 个文件`)
                            } else if (progress.stage === 'cancelled') {
                                ElMessage.warning(`批量处理已取消！已处理 ${successfulCount.value} 个文件`)
                            } else if (progress.stage === 'error') {
                                ElMessage.error(`批量处理出错：${progress.error || '未知错误'}`)
                            }
                        }
                    } else {
                        // 任务不存在或获取进度失败，但不要立即终止，可能是临时网络问题
                        console.warn('获取进度失败，继续尝试...', response.data.message)
                        pollFailureCount.value++
                        
                        // 如果连续失败超过5次，停止轮询
                        if (pollFailureCount.value >= 5) {
                            stopProgressPolling()
                            processing.value = false
                            currentFile.value = null
                            currentTaskId.value = null
                            currentFileProgress.value = 0
                            stopTimer()
                            ElMessage.error('无法获取处理进度，任务可能已完成或失败')
                        }
                    }
                } catch (error) {
                    console.error('轮询进度失败:', error)
                    pollFailureCount.value++
                    
                    // 如果连续失败超过5次，停止轮询
                    if (pollFailureCount.value >= 5) {
                        stopProgressPolling()
                        processing.value = false
                        currentFile.value = null
                        currentTaskId.value = null
                        currentFileProgress.value = 0
                        stopTimer()
                        ElMessage.error('网络连接失败，无法获取处理进度')
                    }
                }
            }, 1000) // 每秒轮询一次
        }

        // 停止轮询进度
        const stopProgressPolling = () => {
            if (progressPollInterval.value) {
                clearInterval(progressPollInterval.value)
                progressPollInterval.value = null
            }
        }

        // 处理批量结果
        const processBatchResults = (results: any[]) => {
            processedFiles.value = []
            
            results.forEach((result) => {
                const fileSize = fileList.value.find(f => f.name === result.filename)?.size || 0
                console.log('处理结果:', result)
                if (result.success) {
                    let downloadUrl = ''
                    let downloadFilename = ''
                    
                    // 根据文件类型生成下载URL
                    if (result.file_type === 'image' && result.data.annotated_image) {
                        // 下载标注后的图片
                        const base64Data = result.data.annotated_image.split(',')[1]
                        const binaryData = atob(base64Data)
                        const bytes = new Uint8Array(binaryData.length)
                        for (let i = 0; i < binaryData.length; i++) {
                            bytes[i] = binaryData.charCodeAt(i)
                        }
                        downloadUrl = URL.createObjectURL(new Blob([bytes], { type: 'image/png' }))
                        downloadFilename = result.filename.replace(/\.[^/.]+$/, '_annotated.png')
                    } else if (result.file_type === 'video' && result.data.annotated_video) {
                        // 下载标注后的视频
                        const base64Data = result.data.annotated_video.split(',')[1]
                        const binaryData = atob(base64Data)
                        const bytes = new Uint8Array(binaryData.length)
                        for (let i = 0; i < binaryData.length; i++) {
                            bytes[i] = binaryData.charCodeAt(i)
                        }
                        downloadUrl = URL.createObjectURL(new Blob([bytes], { type: 'video/mp4' }))
                        downloadFilename = result.filename.replace(/\.[^/.]+$/, '_annotated.mp4')
                    } else {
                        // 备用：下载JSON数据
                        downloadUrl = URL.createObjectURL(new Blob([JSON.stringify(result.data, null, 2)], {
                            type: 'application/json'
                        }))
                        downloadFilename = result.filename.replace(/\.[^/.]+$/, '_result.json')
                    }
                    
                    processedFiles.value.push({
                        filename: result.filename,
                        size: fileSize,
                        success: true,
                        detectionCount: result.data.detected_objects,
                        data: result.data,
                        downloadUrl,
                        downloadFilename
                    })
                } else {
                    processedFiles.value.push({
                        filename: result.filename,
                        size: fileSize,
                        success: false,
                        error: result.error || '处理失败'
                    })
                }
            })
            
            completedCount.value = processedFiles.value.length
        }

        // 取消处理
        const cancelProcessing = async () => {
            if (!currentTaskId.value) {
                ElMessage.warning('没有正在进行的任务')
                return
            }

            try {
                // 调用后端取消API
                await axiosInstance.post(`/api/cancel/${currentTaskId.value}`)
                ElMessage.info('正在取消处理，请稍候...')
            } catch (error) {
                console.error('取消任务失败:', error)
                ElMessage.warning('取消处理请求失败，但已停止前端处理')
            }
            
            // 停止轮询
            stopProgressPolling()
            processing.value = false
            currentFile.value = null
            currentTaskId.value = null
            currentFileProgress.value = 0
            stopTimer()
        }

        // 下载单个结果
        const downloadResult = (result: ProcessedFile) => {
            if (result.downloadUrl) {
                const link = document.createElement('a')
                link.href = result.downloadUrl
                link.download = result.downloadFilename || `${result.filename}_result`
                document.body.appendChild(link)
                link.click()
                document.body.removeChild(link)
            }
        }

        // 批量下载所有结果
        const downloadAllResults = async () => {
            const successfulResults = processedFiles.value.filter(file => file.success)
            
            if (successfulResults.length === 0) {
                ElMessage.warning('没有可下载的结果')
                return
            }

            // 如果只有一个文件，直接下载单个文件
            if (successfulResults.length === 1) {
                const file = successfulResults[0]
                if (file.downloadUrl) {
                    const link = document.createElement('a')
                    link.href = file.downloadUrl
                    link.download = file.downloadFilename || file.filename
                    document.body.appendChild(link)
                    link.click()
                    document.body.removeChild(link)
                    return
                }
            }

            // 批量下载：创建压缩包或逐个下载
            try {
                ElMessage.info('开始下载所有文件...')
                
                // 方案1: 逐个下载文件（简单但用户体验较差）
                for (let i = 0; i < successfulResults.length; i++) {
                    const file = successfulResults[i]
                    if (file.downloadUrl) {
                        // 添加延迟避免浏览器限制
                        if (i > 0) {
                            await new Promise(resolve => setTimeout(resolve, 500))
                        }
                        
                        const link = document.createElement('a')
                        link.href = file.downloadUrl
                        link.download = file.downloadFilename || file.filename
                        document.body.appendChild(link)
                        link.click()
                        document.body.removeChild(link)
                    }
                }
                
                ElMessage.success(`已开始下载 ${successfulResults.length} 个文件`)
                
            } catch (error) {
                console.error('批量下载失败:', error)
                ElMessage.error('批量下载失败，请尝试单个下载')
                
                // 降级方案：下载JSON格式的汇总结果
                const allResults = {
                    summary: {
                        total_files: successfulResults.length,
                        total_detections: successfulResults.reduce((sum, file) => sum + (file.detectionCount || 0), 0),
                        processed_time: new Date().toISOString()
                    },
                    results: successfulResults.map(file => ({
                        filename: file.filename,
                        detection_count: file.detectionCount,
                        data: file.data
                    }))
                }

                const blob = new Blob([JSON.stringify(allResults, null, 2)], {
                    type: 'application/json'
                })
                const url = URL.createObjectURL(blob)
                const link = document.createElement('a')
                link.href = url
                link.download = `batch_processing_results_${new Date().getTime()}.json`
                document.body.appendChild(link)
                link.click()
                document.body.removeChild(link)
                URL.revokeObjectURL(url)
            }
        }

        // 预览图片
        const previewImage = (result: ProcessedFile) => {
            result.showPreview = !result.showPreview
        }

        // 预览视频
        const previewVideo = (result: ProcessedFile) => {
            result.showPreview = !result.showPreview
            console.log('预览视频:', result.filename, result.data?.annotated_video ? '有视频数据' : '无视频数据')
        }

        // 视频状态跟踪
        const videoStatus = ref<{[key: string]: string}>({})

        // 视频错误处理
        const handleVideoError = (event: Event) => {
            const target = event.target as HTMLVideoElement
            const videoSrc = target.src
            let errorMsg = '视频播放失败'
            
            if (target.error) {
                switch (target.error.code) {
                    case target.error.MEDIA_ERR_ABORTED:
                        errorMsg = '视频播放被中止'
                        break
                    case target.error.MEDIA_ERR_NETWORK:
                        errorMsg = '网络错误导致视频下载失败'
                        break
                    case target.error.MEDIA_ERR_DECODE:
                        errorMsg = '视频解码失败，可能是格式不支持'
                        break
                    case target.error.MEDIA_ERR_SRC_NOT_SUPPORTED:
                        errorMsg = '视频格式不支持'
                        break
                    default:
                        errorMsg = '未知的视频播放错误'
                }
            }
            
            console.error('视频播放错误:', {
                error: target.error,
                errorCode: target.error?.code,
                errorMessage: errorMsg,
                videoDataSize: videoSrc.length,
                event: event
            })
            
            // 更新视频状态
            const filename = getFilenameFromVideoElement(target)
            if (filename) {
                videoStatus.value[filename] = `错误: ${errorMsg}`
            }
            
            ElMessage.error(`视频播放失败: ${errorMsg}`)
        }

        // 视频开始加载
        const handleVideoLoadStart = (event: Event) => {
            const target = event.target as HTMLVideoElement
            const filename = getFilenameFromVideoElement(target)
            if (filename) {
                videoStatus.value[filename] = '加载中...'
            }
        }

        // 视频可以播放
        const handleVideoCanPlay = (event: Event) => {
            const target = event.target as HTMLVideoElement
            const filename = getFilenameFromVideoElement(target)
            if (filename) {
                videoStatus.value[filename] = '就绪'
            }
        }

        // 视频元数据加载完成
        const handleVideoMetadata = (event: Event) => {
            const target = event.target as HTMLVideoElement
            const filename = getFilenameFromVideoElement(target)
            if (filename) {
                videoStatus.value[filename] = `${target.videoWidth}x${target.videoHeight}, ${target.duration?.toFixed(1)}s`
            }
        }

        // 从视频元素获取文件名（辅助函数）
        const getFilenameFromVideoElement = (videoElement: HTMLVideoElement): string | null => {
            // 通过父元素查找对应的结果项
            let parent = videoElement.parentElement
            while (parent && !parent.classList.contains('result-item')) {
                parent = parent.parentElement
            }
            if (parent) {
                const nameElement = parent.querySelector('.file-name')
                return nameElement?.textContent || null
            }
            return null
        }

        // 获取视频状态
        const getVideoStatus = (filename: string): string => {
            return videoStatus.value[filename] || '未知'
        }

        // 获取视频数据类型（调试用）
        const getVideoDataType = (videoData: string) => {
            if (videoData.startsWith('data:video/mp4;base64,')) {
                return 'MP4 Base64'
            } else if (videoData.startsWith('data:video/')) {
                return '其他视频格式'
            } else {
                return '未知格式'
            }
        }

        // 获取视频数据长度（调试用）
        const getVideoDataLength = (videoData: string) => {
            const base64Part = videoData.split(',')[1] || ''
            return `${Math.round(base64Part.length / 1024)} KB`
        }

        // 页面离开时中断处理
        const handleBeforeUnload = (event: BeforeUnloadEvent) => {
            if (processing.value) {
                // 尝试取消后端任务
                if (currentTaskId.value) {
                    try {
                        const xhr = new XMLHttpRequest()
                        xhr.open('POST', `http://localhost:8090/api/cancel/${currentTaskId.value}`, false)
                        xhr.send()
                    } catch (error) {
                        console.error('无法取消后端任务:', error)
                    }
                }
                
                const message = '批量处理正在进行中，离开页面将中断处理。确定要离开吗？'
                event.returnValue = message
                return message
            }
        }

        // 组件挂载时添加监听器
        onMounted(() => {
            window.addEventListener('beforeunload', handleBeforeUnload)
        })
        
        onUnmounted(() => {
            window.removeEventListener('beforeunload', handleBeforeUnload)
            // 清理轮询和计时器
            stopProgressPolling()
            stopTimer()
        })

        return {
            uploadRef,
            fileList,
            processing,
            currentFile,
            processedFiles,
            completedCount,
            totalCount,
            maxSize,
            totalSize,
            overallProgress,
            successfulCount,
            hasSuccessfulResults,
            currentTaskId,
            currentFileProgress,
            elapsedTime,
            formatElapsedTime,
            // formatFileSize 已从 common.js 导入
            formatFileSize,
            formatTime,
            downloadFile,
            handleFileChange,
            handleFileRemove,
            beforeUpload,
            handleExceed,
            clearFiles,
            startBatchProcessing,
            cancelProcessing,
            downloadResult,
            downloadAllResults,
            previewImage,
            previewVideo,
            handleVideoError,
            handleVideoLoadStart,
            handleVideoCanPlay,
            handleVideoMetadata,
            getVideoStatus,
            getVideoDataType,
            getVideoDataLength
        }
    }
})
</script>

<style scoped>
.batch-processing {
    padding: 20px;
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
    transition: all 0.3s ease;
}

:deep(.el-card:hover) {
    border-color: rgba(0, 245, 255, 0.5);
    box-shadow: 0 12px 40px rgba(0, 245, 255, 0.2);
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
    justify-content: space-between;
    gap: 8px;
}

.card-header .el-icon {
    font-size: 18px;
}

.header-info {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 4px;
}

.status-text {
    font-size: 12px;
    color: #ffa500;
    font-weight: normal;
}

.timer-text {
    font-size: 14px;
    color: #00f5ff;
    font-weight: bold;
    font-family: 'Courier New', monospace;
    background: rgba(0, 245, 255, 0.1);
    padding: 2px 8px;
    border-radius: 4px;
}

/* 上传区域 */
.upload-section {
    display: flex;
    flex-direction: column;
    gap: 20px;
    padding: 24px;
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
    transform: translateY(-2px);
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
    animation: float 3s ease-in-out infinite;
}

@keyframes float {
    0%, 100% { transform: translateY(0px); }
    50% { transform: translateY(-10px); }
}

.upload-text {
    font-size: 16px;
    margin-bottom: 8px;
    font-weight: 500;
}

.upload-hint {
    font-size: 12px;
    color: #888;
    text-align: center;
    line-height: 1.4;
}

/* 文件信息 */
.file-info {
    display: flex;
    flex-direction: column;
    gap: 15px;
}

.size-info {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 16px;
    background: rgba(0, 245, 255, 0.08);
    border-radius: 8px;
    color: #ffffff;
    border: 1px solid rgba(0, 245, 255, 0.2);
}

.size-text {
    color: #00f5ff;
    font-weight: 500;
}

.size-text.size-exceeded {
    color: #ff4757;
    animation: pulse 1s infinite;
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.6; }
}

.action-buttons {
    display: flex;
    gap: 12px;
    align-items: center;
    flex-wrap: wrap;
}

.process-btn {
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

.process-btn:hover {
    box-shadow: 0 6px 20px rgba(0, 245, 255, 0.6);
    transform: translateY(-2px);
    background: linear-gradient(45deg, #0080ff, #00f5ff);
}

.process-btn:disabled {
    background: #666;
    color: #999;
    box-shadow: none;
    transform: none;
}

.abort-btn {
    background: linear-gradient(45deg, #ff4757, #ff3742);
    border: none;
    border-radius: 25px;
    padding: 12px 30px;
    font-size: 16px;
    font-weight: bold;
    color: #fff;
    box-shadow: 0 4px 15px rgba(255, 71, 87, 0.4);
    transition: all 0.3s ease;
}

.abort-btn:hover {
    box-shadow: 0 6px 20px rgba(255, 71, 87, 0.6);
    transform: translateY(-2px);
}

/* 进度区域 */
.progress-section {
    display: flex;
    flex-direction: column;
    gap: 20px;
    padding: 24px;
}

.overall-progress {
    padding: 20px;
    background: rgba(0, 245, 255, 0.05);
    border-radius: 12px;
    border: 1px solid rgba(0, 245, 255, 0.2);
}

.progress-header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 12px;
    color: #ffffff;
    font-weight: bold;
    font-size: 16px;
}

.progress-info {
    margin-top: 10px;
    color: #ccc;
    font-size: 14px;
    text-align: center;
}

.animated-progress {
    margin: 10px 0;
}

.animated-progress :deep(.el-progress-bar__inner) {
    background: linear-gradient(90deg, #00f5ff, #0080ff, #00f5ff);
    background-size: 200% 100%;
    animation: progress-shimmer 2s linear infinite;
}

@keyframes progress-shimmer {
    0% { background-position: -200% 0; }
    100% { background-position: 200% 0; }
}

.current-processing {
    padding: 20px;
    background: rgba(255, 165, 0, 0.1);
    border-radius: 12px;
    border-left: 4px solid #ffa500;
    border: 1px solid rgba(255, 165, 0, 0.3);
}

.current-file-info {
    display: flex;
    flex-direction: column;
    gap: 10px;
    color: #ffa500;
    font-weight: bold;
}

.current-file-info > div:first-child {
    display: flex;
    align-items: center;
    gap: 10px;
}

.processing-icon {
    animation: spin 1s linear infinite;
    font-size: 18px;
}

@keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
}

.current-file-progress {
    margin-top: 10px;
}

.file-progress-header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 6px;
    font-size: 14px;
    color: #ccc;
}

.file-progress-bar {
    margin: 5px 0;
}

.file-progress-bar :deep(.el-progress-bar__inner) {
    background: linear-gradient(90deg, #ffa500, #ff6b35, #ffa500);
    background-size: 200% 100%;
    animation: progress-shimmer 2s linear infinite;
}

/* 结果列表 */
.results-list {
    margin-top: 20px;
}

.results-list h4 {
    color: #00f5ff;
    margin-bottom: 15px;
    font-size: 18px;
    font-weight: bold;
}

.result-item {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 12px;
    margin-bottom: 15px;
    transition: all 0.3s ease;
    border: 1px solid rgba(0, 245, 255, 0.2);
    overflow: hidden;
}

.result-item:hover {
    background: rgba(0, 245, 255, 0.1);
    border-color: rgba(0, 245, 255, 0.4);
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(0, 245, 255, 0.2);
}

.result-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 20px;
}

.result-info {
    display: flex;
    align-items: center;
    gap: 15px;
    flex: 1;
}

.file-details {
    display: flex;
    flex-direction: column;
    gap: 6px;
}

.result-icon {
    font-size: 20px;
    padding: 10px;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.1);
}

.result-icon.success {
    color: #2ed573;
    background: rgba(46, 213, 115, 0.2);
    animation: success-pulse 2s ease-in-out infinite;
}

.result-icon.error {
    color: #ff4757;
    background: rgba(255, 71, 87, 0.2);
}

@keyframes success-pulse {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.1); }
}

.file-name {
    color: #ffffff;
    font-weight: bold;
    font-size: 14px;
}

.file-size {
    color: #888;
    font-size: 12px;
}

.result-actions {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 10px;
}

/* 结果详情 */
.result-details {
    display: flex;
    flex-direction: column;
    gap: 6px;
    margin-bottom: 10px;
}

.detection-count {
    color: #00f5ff;
    font-size: 14px;
    font-weight: bold;
}

.video-info {
    display: flex;
    gap: 10px;
    margin-top: 5px;
}

.video-detail {
    font-size: 12px;
    color: #888;
    background: rgba(0, 245, 255, 0.1);
    padding: 3px 8px;
    border-radius: 6px;
    border: 1px solid rgba(0, 245, 255, 0.2);
}

.error-msg {
    color: #ff4757;
    font-size: 12px;
    font-weight: bold;
}

/* 批量下载 */
.batch-download {
    padding: 20px;
    text-align: center;
    border-top: 1px solid rgba(0, 245, 255, 0.2);
    margin-top: 20px;
}

/* 文件列表样式 */
:deep(.el-upload-list) {
    max-height: 300px;
    overflow-y: auto;
}

:deep(.el-upload-list__item) {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(0, 245, 255, 0.2);
    color: #ffffff;
    margin: 5px 0;
    border-radius: 6px;
}

:deep(.el-upload-list__item-name) {
    color: #ffffff;
}

/* 进度条样式 */
:deep(.el-progress-bar__outer) {
    background-color: rgba(255, 255, 255, 0.1);
    border-radius: 10px;
}

:deep(.el-progress-bar__inner) {
    border-radius: 10px;
}

/* 预览区域 */
.preview-area {
    padding: 20px;
    background: rgba(0, 0, 0, 0.3);
    border-top: 1px solid rgba(0, 245, 255, 0.3);
    animation: slideDown 0.3s ease-out;
}

@keyframes slideDown {
    from {
        opacity: 0;
        max-height: 0;
        padding: 0 20px;
    }
    to {
        opacity: 1;
        max-height: 500px;
        padding: 20px;
    }
}

.image-preview, .video-preview {
    text-align: center;
}

.annotated-image, .annotated-video {
    max-width: 100%;
    max-height: 400px;
    border-radius: 8px;
    border: 2px solid rgba(0, 245, 255, 0.5);
    box-shadow: 0 4px 20px rgba(0, 245, 255, 0.3);
}

.video-debug-info {
    margin-top: 10px;
    padding: 10px;
    background: rgba(0, 0, 0, 0.5);
    border-radius: 6px;
    font-size: 12px;
    color: #ccc;
    text-align: left;
}

/* 视频过大提示样式 */
.video-too-large-notice {
    padding: 20px;
    text-align: center;
}

.video-info-display {
    margin-top: 15px;
    padding: 15px;
    background: rgba(0, 245, 255, 0.1);
    border-radius: 8px;
    border: 1px solid rgba(0, 245, 255, 0.3);
}

.video-info-display h4 {
    color: #00f5ff;
    margin-bottom: 10px;
    font-size: 16px;
}

.video-info-display p {
    color: #ffffff;
    margin: 5px 0;
    font-size: 14px;
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
@media (max-width: 768px) {
    .batch-processing {
        padding: 10px;
    }
    
    .action-buttons {
        flex-direction: column;
        align-items: stretch;
    }
    
    .result-header {
        flex-direction: column;
        align-items: flex-start;
        gap: 15px;
    }
    
    .result-actions {
        width: 100%;
        align-items: flex-start;
    }
    
    .upload-icon {
        font-size: 36px;
    }
    
    .process-btn, .abort-btn {
        padding: 10px 20px;
        font-size: 14px;
    }
}
</style>
