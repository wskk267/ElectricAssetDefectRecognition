<template>
  <div class="realtime-detection">
    <!-- 左侧控制面板 -->
    <div class="left-panel">
      <!-- 摄像头设备选择 -->
      <div class="app-card">
        <div class="app-card-header">
          <span><el-icon><VideoCamera /></el-icon> 摄像头设备</span>
        </div>
        <div class="device-controls">
          <div class="control-item">
            <label class="control-label">选择摄像头：</label>
            <el-select 
              v-model="selectedDeviceId" 
              placeholder="请选择摄像头设备"
              :disabled="cameraActive"
              style="width: 100%"
            >
              <el-option
                v-for="device in availableDevices"
                :key="device.deviceId"
                :label="device.label || `摄像头 ${device.deviceId.slice(0, 8)}...`"
                :value="device.deviceId"
              />
            </el-select>
          </div>
          
          <div class="control-item">
            <label class="control-label">分辨率设置：</label>
            <el-select 
              v-model="selectedResolution" 
              :disabled="cameraActive"
              style="width: 100%"
            >
              <el-option label="1920x1080 (Full HD)" value="1920x1080" />
              <el-option label="1280x720 (HD)" value="1280x720" />
              <el-option label="640x480 (VGA)" value="640x480" />
            </el-select>
          </div>

          <div class="control-buttons">
            <button 
              class="btn-primary" 
              @click="toggleCamera"
              :disabled="!selectedDeviceId"
            >
              <el-icon class="btn-icon">
                <VideoCamera v-if="!cameraActive" />
                <VideoPause v-else />
              </el-icon>
              {{ cameraActive ? '关闭摄像头' : '开启摄像头' }}
            </button>

            <button 
              class="btn-success" 
              @click="toggleDetection"
              :disabled="!cameraActive"
            >
              <el-icon class="btn-icon">
                <Monitor v-if="!detectionActive" />
                <Loading v-else class="loading-icon" />
              </el-icon>
              {{ detectionActive ? '停止识别' : '开始识别' }}
            </button>

            <button 
              class="btn-secondary" 
              @click="refreshDevices"
              :disabled="cameraActive"
            >
              <el-icon class="btn-icon"><RefreshRight /></el-icon>
              刷新设备
            </button>
          </div>
        </div>
      </div>

      <!-- 检测设置 -->
      <div class="app-card">
        <div class="app-card-header">
          <span><el-icon><Setting /></el-icon> 检测设置</span>
        </div>
        <div class="detection-settings">
          <div class="setting-item">
            <label class="slider-label">检测频率: {{ detectionFrequency }} 帧/秒</label>
            <el-slider 
              v-model="detectionFrequency" 
              :min="0.1" 
              :max="10" 
              :step="0.1"
              :format-tooltip="(val) => `${val} 帧/秒`"
              style="margin: 10px 0;"
            />
          </div>
          <div class="setting-item">
            <el-switch
              v-model="performanceMode"
              active-text="性能优化"
              inactive-text="标准模式"
              style="margin-top: 15px;"
            />
            <div class="setting-hint" v-if="performanceMode">
              启用智能跳帧、降采样等优化策略
            </div>
          </div>
        </div>
      </div>

      <!-- 环境检查信息 -->
      <div class="app-card" v-if="showEnvironmentInfo">
        <div class="app-card-header">
          <span><el-icon><InfoFilled /></el-icon> 环境信息</span>
          <el-button size="small" @click="showEnvironmentInfo = false" type="text">
            <el-icon><Close /></el-icon>
          </el-button>
        </div>
        <div class="environment-info">
          <div class="env-item">
            <span class="env-label">协议:</span>
            <span class="env-value" :class="{ 'env-error': !environmentStatus.isSecure }">
              {{ environmentStatus.protocol }}
            </span>
          </div>
          <div class="env-item">
            <span class="env-label">主机:</span>
            <span class="env-value">{{ environmentStatus.hostname }}</span>
          </div>
          <div class="env-item">
            <span class="env-label">MediaDevices:</span>
            <span class="env-value" :class="{ 'env-error': !environmentStatus.hasMediaDevices }">
              {{ environmentStatus.hasMediaDevices ? '支持' : '不支持' }}
            </span>
          </div>
          <div class="env-item">
            <span class="env-label">GetUserMedia:</span>
            <span class="env-value" :class="{ 'env-error': !environmentStatus.hasGetUserMedia }">
              {{ environmentStatus.hasGetUserMedia ? '支持' : '不支持' }}
            </span>
          </div>
          <div class="env-item">
            <span class="env-label">EnumerateDevices:</span>
            <span class="env-value" :class="{ 'env-error': !environmentStatus.hasEnumerateDevices }">
              {{ environmentStatus.hasEnumerateDevices ? '支持' : '不支持' }}
            </span>
          </div>
          <div class="env-item">
            <span class="env-label">浏览器:</span>
            <span class="env-value">{{ environmentStatus.browser }}</span>
          </div>
        </div>
      </div>

      <!-- 检测统计 - 移除统计显示 -->
    </div>

    <!-- 右侧视频预览区域 -->
    <div class="right-panel">
      <div class="app-card video-card">
        <div class="app-card-header">
          <span><el-icon><Monitor /></el-icon> 实时画面</span>
          <div class="app-card-actions" v-if="cameraActive">
            <el-button size="small" @click="captureFrame">
              <el-icon><Camera /></el-icon>
              截图
            </el-button>
            <el-button size="small" @click="toggleRecording" :type="recording ? 'danger' : 'primary'">
              <el-icon>
                <VideoCamera v-if="!recording" />
                <VideoPause v-else />
              </el-icon>
              {{ recording ? '停止录制' : '开始录制' }}
            </el-button>
          </div>
        </div>
        
        <div class="video-container">
          <!-- 摄像头预览 -->
          <div v-if="!cameraActive" class="video-placeholder">
            <el-icon class="placeholder-icon"><VideoCamera /></el-icon>
            <p>请先选择并开启摄像头</p>
          </div>
          
          <!-- 视频包装器 - 始终渲染，但根据摄像头状态显示/隐藏 -->
          <div class="video-wrapper" :class="{ 'video-hidden': !cameraActive }">
            <video 
              ref="videoElement" 
              autoplay 
              muted 
              playsinline
              class="video-preview"
              @loadedmetadata="onVideoLoaded"
              @loadstart="() => console.log('视频开始加载')"
              @loadeddata="() => console.log('视频数据加载完成')"
              @canplay="() => console.log('视频可以播放')"
              @canplaythrough="() => console.log('视频可以流畅播放')"
              @playing="() => console.log('视频正在播放')"
              @error="(e) => console.error('视频加载错误:', e)"
              @stalled="() => console.log('视频加载停滞')"
              @waiting="() => console.log('视频缓冲中')"
            ></video>
            
            <!-- 检测结果叠加层 -->
            <canvas 
              ref="overlayCanvas" 
              class="detection-overlay"
            ></canvas>
          </div>
        </div>

        <!-- 状态信息 -->
        <div class="status-bar" v-if="cameraActive">
          <div class="status-item">
            <el-icon><VideoCamera /></el-icon>
            <span>{{ videoResolution }}</span>
          </div>
          <div class="status-item">
            <el-icon><Timer /></el-icon>
            <span>{{ detectionActive ? '检测时长' : '运行时长' }}: {{ formatRunningTime(runningTime) }}</span>
          </div>
          <div class="status-item" v-if="detectionActive">
            <el-icon class="status-detecting"><Monitor /></el-icon>
            <span>检测中</span>
          </div>
          <div class="status-item" v-if="recording">
            <el-icon class="status-recording"><VideoCamera /></el-icon>
            <span>录制中</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Monitor, VideoCamera, VideoPause, Loading, 
  RefreshRight, Setting, Camera, Timer, InfoFilled, Close
} from '@element-plus/icons-vue'
import axiosInstance from '../axios'

interface CameraDevice {
  deviceId: string
  label: string
  kind: string
}

interface DetectionResult {
  id: number
  asset_category: string
  defect_status: string
  confidence: number
  center: { x: number; y: number }
  width: number
  height: number
}

export default defineComponent({
  name: 'RealtimeDetection',
  components: {
    Monitor,
    VideoCamera,
    VideoPause,
    Loading,
    RefreshRight,
    Setting,
    Camera,
    Timer,
    InfoFilled,
    Close
  },
  setup() {
    // 检查用户权限 - 从后端实时验证
    const checkUserPermissions = async () => {
      try {
        const response = await axiosInstance.get('/api/check-permissions')
        if (response.data.success) {
          const permissions = response.data.data
          
          if (permissions.realtimePermission !== 1) {
            ElMessage.error('您没有实时检测权限，请联系管理员开通')
            return false
          }
          
          if (permissions.isbannd === 1) {
            ElMessage.error('您的账户已被封禁，请联系管理员')
            return false
          }
          
          return true
        } else {
          ElMessage.error('权限验证失败，请重新登录')
          return false
        }
      } catch (error) {
        console.error('权限检查失败:', error)
        if (error.response?.status === 401) {
          ElMessage.error('登录已过期，请重新登录')
        } else if (error.response?.status === 403) {
          ElMessage.error('账户权限不足或已被封禁')
        } else {
          ElMessage.error('权限验证失败，请检查网络连接')
        }
        return false
      }
    }
    
    // 基础状态
    const videoElement = ref<HTMLVideoElement>()
    const overlayCanvas = ref<HTMLCanvasElement>()
    const availableDevices = ref<CameraDevice[]>([])
    const selectedDeviceId = ref<string>('')
    const selectedResolution = ref<string>('1280x720')
    
    // 摄像头状态
    const cameraActive = ref(false)
    const currentStream = ref<MediaStream | null>(null)
    const videoResolution = ref<string>('')
    
    // 检测状态
    const detectionActive = ref(false)
    const detectionResults = ref<DetectionResult[]>([])
    const detectionFrequency = ref<number>(1) // 检测频率（帧/秒）
    const detectionTimer = ref<number | null>(null)
    
    // 录制功能
    const recording = ref(false)
    const mediaRecorder = ref<MediaRecorder | null>(null)
    const recordedChunks = ref<Blob[]>([])
    
    // 统计信息 - 修改为分别记录摄像头和检测时间
    const runningTime = ref<number>(0)
    const cameraStartTime = ref<number>(0) // 摄像头开始时间
    const detectionStartTime = ref<number>(0) // 检测开始时间，初始化为0
    const timeTimer = ref<number | null>(null)

    // 性能优化相关状态
    const performanceMode = ref(false) // 性能模式开关，默认关闭
    const frameSkipCount = ref(0) // 跳帧计数
    const lastProcessTime = ref(0) // 上次处理时间
    const canvasPool = ref<HTMLCanvasElement[]>([]) // Canvas池，复用canvas减少创建开销
    const requestId = ref(0) // 用于取消不必要的请求
    
    // 并发控制状态
    const isProcessing = ref(false) // 是否正在处理请求
    const currentAbortController = ref<AbortController | null>(null) // 当前请求的取消控制器
    const maxConcurrentRequests = 1 // 最大并发请求数量
    const activeRequests = ref(0) // 当前活跃请求数量
    
    // 自适应频率控制
    const recentResponseTimes = ref<number[]>([]) // 最近的响应时间记录
    const maxResponseTimeHistory = 5 // 保留最近5次响应时间
    const baseDetectionInterval = ref(1000) // 基础检测间隔（毫秒）
    
    // 环境检查状态
    const showEnvironmentInfo = ref(false) // 是否显示环境信息
    const environmentStatus = ref({
      protocol: location.protocol,
      hostname: location.hostname,
      isSecure: location.protocol === 'https:' || location.hostname === 'localhost' || location.hostname === '127.0.0.1',
      hasMediaDevices: !!navigator.mediaDevices,
      hasGetUserMedia: !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia),
      hasEnumerateDevices: !!(navigator.mediaDevices && navigator.mediaDevices.enumerateDevices),
      browser: (() => {
        const ua = navigator.userAgent
        if (ua.includes('Chrome')) return 'Chrome'
        if (ua.includes('Firefox')) return 'Firefox'
        if (ua.includes('Safari')) return 'Safari'
        if (ua.includes('Edge')) return 'Edge'
        return 'Unknown'
      })()
    })
    
    // Canvas池管理
    const getCanvas = (): HTMLCanvasElement => {
      if (canvasPool.value.length > 0) {
        return canvasPool.value.pop()!
      }
      const canvas = document.createElement('canvas')
      return canvas
    }
    
    const returnCanvas = (canvas: HTMLCanvasElement) => {
      if (canvasPool.value.length < 3) { // 最多保留3个canvas
        const ctx = canvas.getContext('2d')
        if (ctx) {
          ctx.clearRect(0, 0, canvas.width, canvas.height)
        }
        canvasPool.value.push(canvas)
      }
    }
    
    // 检查浏览器兼容性
    const checkBrowserSupport = () => {
      // 检查基本的 navigator 支持
      if (!navigator) {
        return {
          supported: false,
          reason: 'navigator API 不可用'
        }
      }

      // 检查 mediaDevices API 支持
      if (!navigator.mediaDevices) {
        return {
          supported: false,
          reason: 'mediaDevices API 不可用（需要 HTTPS 或 localhost）'
        }
      }

      // 检查 getUserMedia 支持
      if (!navigator.mediaDevices.getUserMedia) {
        return {
          supported: false,
          reason: 'getUserMedia API 不可用'
        }
      }

      // 检查 enumerateDevices 支持
      if (!navigator.mediaDevices.enumerateDevices) {
        return {
          supported: false,
          reason: 'enumerateDevices API 不可用'
        }
      }

      // 检查是否在安全上下文中
      if (location.protocol !== 'https:' && location.hostname !== 'localhost' && location.hostname !== '127.0.0.1') {
        return {
          supported: false,
          reason: '摄像头访问需要 HTTPS 协议或 localhost 环境'
        }
      }

      return {
        supported: true,
        reason: '浏览器支持摄像头功能'
      }
    }

    // 获取可用摄像头设备
    const getAvailableDevices = async () => {
      try {
        // 首先检查浏览器兼容性
        const browserCheck = checkBrowserSupport()
        if (!browserCheck.supported) {
          console.error('浏览器不支持摄像头功能:', browserCheck.reason)
          ElMessage.error(`浏览器不支持: ${browserCheck.reason}`)
          
          // 提供解决方案提示
          if (browserCheck.reason.includes('HTTPS')) {
            ElMessage({
              message: '解决方案：请使用 HTTPS 协议访问，或在 localhost 环境下使用',
              type: 'warning',
              duration: 8000,
              showClose: true
            })
          } else if (browserCheck.reason.includes('mediaDevices')) {
            ElMessage({
              message: '解决方案：请更新浏览器到最新版本，或尝试使用 Chrome/Firefox 浏览器',
              type: 'warning',
              duration: 8000,
              showClose: true
            })
          }
          
          return
        }

        console.log('浏览器兼容性检查通过:', browserCheck.reason)

        // 首先尝试获取设备列表（不需要权限）
        let devices = await navigator.mediaDevices.enumerateDevices()
        const videoDevices = devices.filter(device => device.kind === 'videoinput')
        
        console.log('初始设备列表:', videoDevices.map(d => ({ 
          deviceId: d.deviceId.slice(0, 8) + '...', 
          label: d.label || '(无标签)', 
          kind: d.kind 
        })))

        // 如果设备没有标签，说明没有权限，需要请求权限
        if (videoDevices.length > 0 && !videoDevices[0].label) {
          console.log('设备列表无标签，需要请求摄像头权限...')
          try {
            // 请求摄像头权限
            const stream = await navigator.mediaDevices.getUserMedia({ 
              video: { 
                width: { ideal: 640 },
                height: { ideal: 480 }
              } 
            })
            console.log('获取权限成功，立即释放流')
            
            // 立即停止流，我们只是为了获取权限
            stream.getTracks().forEach(track => {
              track.stop()
              console.log('停止轨道:', track.kind, track.label)
            })
            
            // 等待一小段时间后重新获取设备列表
            await new Promise(resolve => setTimeout(resolve, 100))
            devices = await navigator.mediaDevices.enumerateDevices()
            console.log('权限获取后的设备列表:', devices.filter(d => d.kind === 'videoinput').map(d => ({ 
              deviceId: d.deviceId.slice(0, 8) + '...', 
              label: d.label || '(仍无标签)', 
              kind: d.kind 
            })))
          } catch (permissionError) {
            console.error('摄像头权限被拒绝:', permissionError)
            let errorMsg = '摄像头权限被拒绝'
            
            if (permissionError.name === 'NotAllowedError') {
              errorMsg = '用户拒绝了摄像头权限，请在浏览器地址栏左侧点击摄像头图标允许访问'
            } else if (permissionError.name === 'NotFoundError') {
              errorMsg = '未找到摄像头设备，请检查设备是否正确连接'
            } else if (permissionError.name === 'NotReadableError') {
              errorMsg = '摄像头被其他应用占用，请关闭其他使用摄像头的程序'
            } else if (permissionError.name === 'SecurityError') {
              errorMsg = '安全限制：请使用 HTTPS 协议访问本页面'
            }
            
            ElMessage.error(errorMsg)
            return
          }
        }
        
        // 处理设备列表
        const processedDevices = devices
          .filter(device => device.kind === 'videoinput')
          .map((device, index) => ({
            deviceId: device.deviceId,
            label: device.label || `摄像头设备 ${index + 1}`,
            kind: device.kind
          }))

        console.log('最终处理的设备列表:', processedDevices)
        availableDevices.value = processedDevices
        
        // 如果有设备但没有选中任何设备，默认选择第一个
        if (availableDevices.value.length > 0 && !selectedDeviceId.value) {
          selectedDeviceId.value = availableDevices.value[0].deviceId
          console.log('自动选择第一个设备:', selectedDeviceId.value)
        }
        
        if (availableDevices.value.length === 0) {
          ElMessage.warning('未找到可用的摄像头设备，请检查设备连接')
        } else {
          ElMessage.success(`找到 ${availableDevices.value.length} 个摄像头设备`)
        }
        
      } catch (error) {
        console.error('获取摄像头设备失败:', error)
        
        let errorMessage = '获取摄像头设备失败'
        
        // 根据错误类型提供具体的解决方案
        if (error.name === 'TypeError' && error.message.includes('enumerateDevices')) {
          errorMessage = '浏览器不支持摄像头枚举功能，请更新浏览器或使用 Chrome/Firefox'
        } else if (error.name === 'SecurityError') {
          errorMessage = '安全限制：请使用 HTTPS 协议或在 localhost 环境下访问'
        } else if (error.name === 'NotSupportedError') {
          errorMessage = '当前环境不支持摄像头功能'
        } else {
          errorMessage = `摄像头功能不可用: ${error.message || '未知错误'}`
        }
        
        ElMessage.error(errorMessage)
        
        // 显示详细的解决方案
        ElMessage({
          message: '建议解决方案：1. 确保使用 HTTPS 协议 2. 更新浏览器到最新版本 3. 检查摄像头设备连接 4. 允许浏览器访问摄像头',
          type: 'info',
          duration: 10000,
          showClose: true
        })
      }
    }

    // 刷新设备列表
    const refreshDevices = async () => {
      // 检查浏览器兼容性
      const browserCheck = checkBrowserSupport()
      if (!browserCheck.supported) {
        ElMessage.error(`无法刷新设备: ${browserCheck.reason}`)
        return
      }
      
      try {
        await getAvailableDevices()
        ElMessage.success('设备列表已刷新')
      } catch (error) {
        console.error('刷新设备列表失败:', error)
        ElMessage.error('刷新设备列表失败，请检查浏览器兼容性')
      }
    }

    // 解析分辨率字符串
    const parseResolution = (resolution: string) => {
      const [width, height] = resolution.split('x').map(Number)
      return { width, height }
    }

    // 开启/关闭摄像头
    const toggleCamera = async () => {
      if (cameraActive.value) {
        await stopCamera()
      } else {
        await startCamera()
      }
    }

    // 启动摄像头
    const startCamera = async () => {
      if (!selectedDeviceId.value) {
        ElMessage.warning('请先选择摄像头设备')
        return
      }

      try {
        const { width, height } = parseResolution(selectedResolution.value)
        
        const constraints: MediaStreamConstraints = {
          video: {
            deviceId: { exact: selectedDeviceId.value },
            width: { ideal: width },
            height: { ideal: height },
            frameRate: { ideal: 30 }
          },
          audio: false
        }

        console.log('请求摄像头访问，约束条件:', constraints)
        const stream = await navigator.mediaDevices.getUserMedia(constraints)
        currentStream.value = stream
        
        console.log('检查video元素:', {
          videoElement: !!videoElement.value,
          cameraActive: cameraActive.value,
          stream: !!stream
        })

        if (videoElement.value) {
          console.log('设置视频流到视频元素')
          videoElement.value.srcObject = stream
          
          // 等待一小段时间让视频流设置完成
          await new Promise(resolve => setTimeout(resolve, 100))
          
          // 等待视频开始播放
          try {
            await videoElement.value.play()
            console.log('视频开始播放')
          } catch (playError) {
            console.warn('自动播放失败，可能需要用户交互:', playError)
            // 通常在现代浏览器中，摄像头流可以自动播放，所以这个错误可以忽略
          }
          
          // 只有成功设置视频流后才激活摄像头状态
          cameraActive.value = true
          
          // 开始摄像头计时 - 记录摄像头开始时间（但不是检测计时）
          cameraStartTime.value = Date.now()
          startTimer()
          
          console.log('摄像头启动成功, 开始时间:', new Date(cameraStartTime.value))
          ElMessage.success('摄像头已启动')
        } else {
          console.error('视频元素未找到 - ref绑定失败')
          
          // 清理流
          if (stream) {
            stream.getTracks().forEach(track => track.stop())
          }
          currentStream.value = null
          
          ElMessage.error('视频元素初始化失败，请刷新页面重试')
        }
      } catch (error: any) {
        console.error('启动摄像头失败:', error)
        
        let errorMessage = '启动摄像头失败'
        
        if (error.name === 'NotAllowedError') {
          errorMessage = '摄像头权限被拒绝，请允许浏览器访问摄像头'
        } else if (error.name === 'NotFoundError') {
          errorMessage = '未找到指定的摄像头设备'
        } else if (error.name === 'NotReadableError') {
          errorMessage = '摄像头设备被其他应用占用'
        } else if (error.name === 'OverconstrainedError') {
          errorMessage = '摄像头不支持所选分辨率，请尝试其他分辨率'
        } else if (error.name === 'SecurityError') {
          errorMessage = '安全限制：请使用HTTPS协议或localhost访问'
        } else {
          errorMessage = `摄像头启动失败: ${error.message || '未知错误'}`
        }
        
        ElMessage.error(errorMessage)
        
        // 清理失败的流
        if (currentStream.value) {
          currentStream.value.getTracks().forEach(track => track.stop())
          currentStream.value = null
        }
        
        // 确保状态重置
        cameraActive.value = false
        cameraStartTime.value = 0
      }
    }

    // 停止摄像头
    const stopCamera = async () => {
      // 先停止检测（如果正在检测）
      if (detectionActive.value) {
        stopDetection()
      }
      
      // 注意：检测时长的记录由 stopDetection 函数负责，这里不重复记录
      
      // 停止录制
      if (recording.value) {
        await stopRecording()
      }

      // 停止摄像头流
      if (currentStream.value) {
        currentStream.value.getTracks().forEach(track => track.stop())
        currentStream.value = null
      }

      if (videoElement.value) {
        videoElement.value.srcObject = null
      }

      cameraActive.value = false
      videoResolution.value = ''
      
      // 停止计时
      stopTimer()
      
      // 清空检测结果
      detectionResults.value = []
      
      // 重置时间状态
      cameraStartTime.value = 0
      detectionStartTime.value = 0
      
      // 重置时间
      runningTime.value = 0
      startTime.value = 0
      
      ElMessage.info('摄像头已关闭')
    }

    // 视频加载完成
    const onVideoLoaded = () => {
      if (videoElement.value) {
        const video = videoElement.value
        console.log('视频元数据加载完成:', {
          videoWidth: video.videoWidth,
          videoHeight: video.videoHeight,
          readyState: video.readyState
        })
        
        videoResolution.value = `${video.videoWidth}x${video.videoHeight}`
        
        // 设置 canvas 尺寸匹配视频，确保在下一个渲染周期执行
        nextTick(() => {
          if (overlayCanvas.value && video.videoWidth > 0 && video.videoHeight > 0) {
            // 设置canvas的实际尺寸为视频的原始尺寸
            overlayCanvas.value.width = video.videoWidth
            overlayCanvas.value.height = video.videoHeight
            
            console.log('Canvas尺寸已设置:', {
              canvasWidth: overlayCanvas.value.width,
              canvasHeight: overlayCanvas.value.height,
              videoWidth: video.videoWidth,
              videoHeight: video.videoHeight
            })
          }
        })
        
        console.log('视频加载完成:', videoResolution.value)
      }
    }

    // 开始/停止检测
    const toggleDetection = () => {
      if (detectionActive.value) {
        stopDetection()
      } else {
        startDetection()
      }
    }

    // 启动检测
    const startDetection = async () => {
      // 检查权限
      const hasPermission = await checkUserPermissions()
      if (!hasPermission) {
        return
      }
      
      if (!cameraActive.value) {
        ElMessage.warning('请先启动摄像头')
        return
      }

      detectionActive.value = true
      
      // 开始检测计时 - 只有在开始检测时才计时
      detectionStartTime.value = Date.now()
      console.log('开始检测计时:', new Date(detectionStartTime.value))

      // 使用动态检测频率，不使用固定定时器
      // 通过requestAnimationFrame实现更平滑的检测循环
      let lastDetectionTime = 0
      const dynamicDetectionLoop = (currentTime: number) => {
        if (!detectionActive.value) return
        
        // 计算自适应检测间隔
        let adaptiveInterval = 1000 / detectionFrequency.value
        
        // 根据最近的响应时间调整检测频率
        if (recentResponseTimes.value.length > 0) {
          const avgResponseTime = recentResponseTimes.value.reduce((a, b) => a + b, 0) / recentResponseTimes.value.length
          
          // 如果平均响应时间过长，增加检测间隔
          if (avgResponseTime > 2000) { // 响应时间超过2秒
            adaptiveInterval = Math.max(adaptiveInterval, avgResponseTime * 0.8) // 至少等待80%的响应时间
          } else if (avgResponseTime > 1000) { // 响应时间超过1秒
            adaptiveInterval = Math.max(adaptiveInterval, avgResponseTime * 0.6)
          }
        }
        
        // 如果有请求正在处理，延长间隔
        if (isProcessing.value) {
          adaptiveInterval = Math.max(adaptiveInterval, 500) // 至少等待500ms
        }
        
        // 检查是否应该执行检测
        if (currentTime - lastDetectionTime >= adaptiveInterval) {
          performDetection()
          lastDetectionTime = currentTime
        }
        
        // 继续循环
        requestAnimationFrame(dynamicDetectionLoop)
      }
      
      // 启动检测循环
      requestAnimationFrame(dynamicDetectionLoop)

      ElMessage.success(`实时检测已启动 (${detectionFrequency.value} 帧/秒)`)
    }

    // 停止检测
    const stopDetection = () => {
      detectionActive.value = false
      
      // 计算检测时长并记录（只在这里记录一次）
      if (detectionStartTime.value > 0) {
        const detectionDuration = Math.floor((Date.now() - detectionStartTime.value) / 1000)
        console.log('停止检测，检测时长:', detectionDuration, '秒')
        
        // 如果检测时长合理（至少5秒，避免记录极短的测试），记录到后端
        if (detectionDuration >= 5 && detectionDuration < 86400) {
          axiosInstance.post('/api/realtime/log', {
            duration: detectionDuration
          }).then(() => {
            console.log(`检测时长已记录: ${detectionDuration}秒`)
          }).catch(error => {
            console.error('记录检测时长失败:', error)
          })
        } else if (detectionDuration < 5) {
          console.log('检测时长过短，跳过记录:', detectionDuration)
        } else {
          console.warn('检测时长异常，跳过记录:', detectionDuration)
        }
        
        // 重置检测开始时间
        detectionStartTime.value = 0
      }
      
      // 注意：不再需要清除定时器，因为使用了requestAnimationFrame
      if (detectionTimer.value) {
        clearInterval(detectionTimer.value)
        detectionTimer.value = null
      }
      
      // 取消所有未完成的请求
      if (currentAbortController.value) {
        currentAbortController.value.abort()
        currentAbortController.value = null
      }
      
      // 重置处理状态
      isProcessing.value = false
      activeRequests.value = 0
      
      // 清除检测结果
      detectionResults.value = []
      clearCanvas()
      
      ElMessage.info('实时检测已停止')
    }

    // 执行检测 - 性能优化版本（添加并发控制）
    const performDetection = async () => {
      if (!videoElement.value || !detectionActive.value) {
        return
      }

      // 并发控制：如果已有请求在处理，跳过本次检测
      if (isProcessing.value || activeRequests.value >= maxConcurrentRequests) {
        console.log('跳过检测：已有请求在处理中')
        return
      }

      const now = Date.now()
      
      // 性能模式：智能跳帧
      if (performanceMode.value) {
        if (frameSkipCount.value > 0) {
          frameSkipCount.value--
          return
        }
        
        // 如果上次处理时间太短，跳过这一帧
        if (now - lastProcessTime.value < 100) { // 最少间隔100ms
          return
        }
      }

      lastProcessTime.value = now
      const currentRequestId = ++requestId.value

      // 设置处理状态
      isProcessing.value = true
      activeRequests.value++

      try {
        // 使用canvas池减少创建开销
        const canvas = getCanvas()
        const ctx = canvas.getContext('2d')
        
        if (!ctx) {
          returnCanvas(canvas)
          return
        }

        // 降采样处理 - 减少传输数据量
        const sourceWidth = videoElement.value.videoWidth
        const sourceHeight = videoElement.value.videoHeight
        const maxSize = 480 // 降低分辨率以提高速度
        
        let targetWidth = sourceWidth
        let targetHeight = sourceHeight
        
        if (Math.max(sourceWidth, sourceHeight) > maxSize) {
          const ratio = maxSize / Math.max(sourceWidth, sourceHeight)
          targetWidth = Math.round(sourceWidth * ratio)
          targetHeight = Math.round(sourceHeight * ratio)
        }

        canvas.width = targetWidth
        canvas.height = targetHeight
        ctx.drawImage(videoElement.value, 0, 0, targetWidth, targetHeight)

        // 转换为blob进行API调用 - 使用更高压缩率
        canvas.toBlob(async (blob) => {
          if (!blob || requestId.value !== currentRequestId || !detectionActive.value) {
            returnCanvas(canvas)
            // 重置处理状态
            isProcessing.value = false
            activeRequests.value = Math.max(0, activeRequests.value - 1)
            return
          }

          try {
            // 创建AbortController用于取消请求
            const abortController = new AbortController()
            currentAbortController.value = abortController
            
            const formData = new FormData()
            formData.append('file', blob, 'frame.jpg')

            // 记录请求开始时间
            const startTime = performance.now()
            
            const response = await axiosInstance.post('/api/realtime/detect', formData, {
              headers: {
                'Content-Type': 'multipart/form-data'
              },
              timeout: 8000, // 增加超时时间到8秒
              signal: abortController.signal // 添加取消信号
            })

            // 记录响应时间
            const responseTime = performance.now() - startTime
            recentResponseTimes.value.push(responseTime)
            // 只保留最近10次的响应时间
            if (recentResponseTimes.value.length > 10) {
              recentResponseTimes.value.shift()
            }

            // 检查请求是否还有效（避免过期响应）
            if (requestId.value !== currentRequestId || !detectionActive.value) {
              returnCanvas(canvas)
              return
            }

            const result = response.data
            
            if (result.success) {
              const predictions = Object.values(result.data.predictions) as any[]
              
              // 调试：打印后端返回的原始数据
              console.log('后端返回的检测结果:', {
                sourceWidth,
                sourceHeight,
                targetWidth,
                targetHeight,
                predictions: predictions.slice(0, 1) // 只打印第一个结果
              })
              
              // 后端返回的坐标是基于发送图片的相对坐标(0-1)
              // 直接使用这些相对坐标，在canvas上绘制时会自动缩放到canvas尺寸
              const filteredResults: DetectionResult[] = predictions
                .map((pred, index) => {
                  // 检查坐标是否异常小，如果是则可能需要修正
                  let center = pred.center
                  let width = pred.width
                  let height = pred.height
                  
                  // 如果坐标值异常小（小于0.01），可能是坐标计算错误，尝试修正
                  if (pred.center.x < 0.01 || pred.center.y < 0.01 || pred.width < 0.01 || pred.height < 0.01) {
                    console.warn('检测到异常小的坐标值，尝试修正:', pred)
                    
                    // 假设这些值可能是像素坐标被错误地当作相对坐标
                    // 尝试将其转换为合理的相对坐标
                    const potentialPixelX = pred.center.x * targetWidth
                    const potentialPixelY = pred.center.y * targetHeight
                    const potentialPixelW = pred.width * targetWidth
                    const potentialPixelH = pred.height * targetHeight
                    
                    console.log('尝试像素坐标解释:', {
                      pixelCenter: { x: potentialPixelX, y: potentialPixelY },
                      pixelSize: { w: potentialPixelW, h: potentialPixelH }
                    })
                    
                    // 如果像素坐标看起来合理（在图片范围内），则使用
                    if (potentialPixelX > 0 && potentialPixelX < targetWidth && 
                        potentialPixelY > 0 && potentialPixelY < targetHeight) {
                      // 保持原值，因为可能是正确的相对坐标
                    } else {
                      // 设置一个可见的测试框在图片中心
                      console.warn('使用测试坐标')
                      center = { x: 0.5, y: 0.5 }
                      width = 0.2
                      height = 0.2
                    }
                  }
                  
                  // 直接使用后端返回的相对坐标
                  const result = {
                    id: index + 1,
                    asset_category: pred.asset_category,
                    defect_status: pred.defect_status || '正常',
                    confidence: pred.confidence,
                    center: center,
                    width: width,
                    height: height
                  }
                  
                  // 详细调试信息
                  console.log(`检测框 ${index + 1} 详细信息:`, {
                    后端原始: {
                      center: pred.center,
                      size: { w: pred.width, h: pred.height }
                    },
                    最终使用: {
                      center: result.center,
                      size: { w: result.width, h: result.height }
                    },
                    转换为像素坐标: {
                      centerX: result.center.x * sourceWidth,
                      centerY: result.center.y * sourceHeight,
                      width: result.width * sourceWidth,
                      height: result.height * sourceHeight
                    }
                  })
                  
                  return result
                })

              // 调试：打印转换后的结果
              console.log('转换后的检测结果:', filteredResults.slice(0, 2))

              detectionResults.value = filteredResults
              
              // 绘制检测结果
              drawDetectionResults(filteredResults)
              
              // 自适应跳帧策略
              if (performanceMode.value) {
                if (filteredResults.length > 0) {
                  frameSkipCount.value = Math.max(0, frameSkipCount.value - 1) // 有目标时提高频率
                } else {
                  frameSkipCount.value = Math.min(2, frameSkipCount.value + 1) // 无目标时降低频率
                }
              }
              
              // 不再记录每次检测的数量，避免产生大量日志
              // 只在停止检测时记录总的检测时长
            }
            
          } catch (error) {
            // 检查是否是取消的请求
            if (error.name === 'AbortError' || error.code === 'ERR_CANCELED') {
              console.log('检测请求被取消')
              returnCanvas(canvas)
              return
            }
            
            // 检查是否是超时错误
            if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
              console.warn('检测请求超时，可能服务器负载过高')
              // 超时时适当降低检测频率
              if (performanceMode.value) {
                frameSkipCount.value = Math.min(5, frameSkipCount.value + 3)
              }
            } else {
              // 其他网络错误时降低频率
              if (performanceMode.value) {
                frameSkipCount.value = Math.min(3, frameSkipCount.value + 2)
              }
              console.error('检测失败:', error)
            }
          } finally {
            returnCanvas(canvas)
            // 重置处理状态
            isProcessing.value = false
            activeRequests.value = Math.max(0, activeRequests.value - 1)
            currentAbortController.value = null
          }
        }, 'image/jpeg', 0.7) // 提高图片质量，减少因压缩导致的检测精度损失
        
      } catch (error) {
        console.error('检测过程出错:', error)
        // 确保状态重置
        isProcessing.value = false
        activeRequests.value = Math.max(0, activeRequests.value - 1)
      }
    }

    // 绘制检测结果
    const drawDetectionResults = (results: DetectionResult[]) => {
      if (!overlayCanvas.value || !videoElement.value) return

      const canvas = overlayCanvas.value
      const video = videoElement.value
      const ctx = canvas.getContext('2d')
      if (!ctx) return

      // 清除之前的绘制
      ctx.clearRect(0, 0, canvas.width, canvas.height)

      // 确保canvas尺寸与视频匹配
      if (canvas.width !== video.videoWidth || canvas.height !== video.videoHeight) {
        canvas.width = video.videoWidth
        canvas.height = video.videoHeight
        console.log('Canvas尺寸已更新:', { width: canvas.width, height: canvas.height })
      }

      // 如果没有检测结果，直接返回
      if (results.length === 0) return

      // 调试：打印绘制信息
      console.log('绘制检测框:', {
        canvasWidth: canvas.width,
        canvasHeight: canvas.height,
        videoWidth: video.videoWidth,
        videoHeight: video.videoHeight,
        resultsCount: results.length
      })

      results.forEach((result, index) => {
        // 计算边界框位置 - 使用canvas的实际尺寸
        const centerX = result.center.x * canvas.width
        const centerY = result.center.y * canvas.height
        const boxWidth = result.width * canvas.width
        const boxHeight = result.height * canvas.height
        const x = centerX - boxWidth / 2
        const y = centerY - boxHeight / 2

        // 调试：打印每个框的坐标
        if (index === 0) { // 只打印第一个框的信息以减少日志
          console.log('绘制框坐标:', {
            center: result.center,
            size: { width: result.width, height: result.height },
            canvasCoords: { centerX, centerY, boxWidth, boxHeight, x, y }
          })
        }

        // 设置颜色
        let color = '#00f5ff' // 默认蓝色
        if (result.defect_status === '缺陷') {
          color = '#ff4757' // 红色（缺陷）
        } else {
          color = '#2ed573' // 绿色（正常）
        }

        // 绘制边界框
        ctx.strokeStyle = color
        ctx.lineWidth = 3
        ctx.strokeRect(x, y, boxWidth, boxHeight)

        // 绘制填充背景（半透明）
        ctx.fillStyle = color + '20' // 添加透明度
        ctx.fillRect(x, y, boxWidth, boxHeight)

        // 绘制标签
        const label = result.asset_category
        
        ctx.font = '16px Arial'
        const textMetrics = ctx.measureText(label)
        const textWidth = textMetrics.width
        const textHeight = 20

        // 标签背景
        ctx.fillStyle = 'rgba(0, 0, 0, 0.8)'
        ctx.fillRect(x, y - textHeight - 5, textWidth + 10, textHeight + 5)

        // 标签文字
        ctx.fillStyle = '#ffffff'
        ctx.fillText(label, x + 5, y - 8)
      })
    }

    // 清除canvas
    const clearCanvas = () => {
      if (!overlayCanvas.value) return
      const ctx = overlayCanvas.value.getContext('2d')
      if (ctx) {
        ctx.clearRect(0, 0, overlayCanvas.value.width, overlayCanvas.value.height)
      }
    }

    // 截图功能
    const captureFrame = () => {
      if (!videoElement.value) return

      const canvas = document.createElement('canvas')
      const ctx = canvas.getContext('2d')
      if (!ctx) return

      canvas.width = videoElement.value.videoWidth
      canvas.height = videoElement.value.videoHeight
      ctx.drawImage(videoElement.value, 0, 0)

      // 如果有检测结果，也绘制到截图上
      if (detectionResults.value.length > 0 && overlayCanvas.value) {
        ctx.drawImage(overlayCanvas.value, 0, 0)
      }

      // 下载截图
      canvas.toBlob(blob => {
        if (!blob) return
        const url = URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        link.download = `实时检测截图_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.png`
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        URL.revokeObjectURL(url)
        
        ElMessage.success('截图已保存')
      }, 'image/png')
    }

    // 开始/停止录制
    const toggleRecording = async () => {
      if (recording.value) {
        await stopRecording()
      } else {
        await startRecording()
      }
    }

    // 开始录制
    const startRecording = async () => {
      if (!currentStream.value) return

      try {
        recordedChunks.value = []
        mediaRecorder.value = new MediaRecorder(currentStream.value, {
          mimeType: 'video/webm'
        })

        mediaRecorder.value.ondataavailable = (event) => {
          if (event.data.size > 0) {
            recordedChunks.value.push(event.data)
          }
        }

        mediaRecorder.value.onstop = () => {
          const blob = new Blob(recordedChunks.value, { type: 'video/webm' })
          const url = URL.createObjectURL(blob)
          const link = document.createElement('a')
          link.href = url
          link.download = `实时检测录像_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.webm`
          document.body.appendChild(link)
          link.click()
          document.body.removeChild(link)
          URL.revokeObjectURL(url)
          
          ElMessage.success('录像已保存')
        }

        mediaRecorder.value.start()
        recording.value = true
        ElMessage.success('开始录制')
      } catch (error) {
        console.error('开始录制失败:', error)
        ElMessage.error('录制功能不可用')
      }
    }

    // 停止录制
    const stopRecording = async () => {
      if (mediaRecorder.value && recording.value) {
        mediaRecorder.value.stop()
        recording.value = false
        ElMessage.info('录制已停止')
      }
    }

    // 计时器功能 - 修改为显示检测时间
    const startTimer = () => {
      timeTimer.value = window.setInterval(() => {
        // 如果正在检测，显示检测时间；否则显示摄像头运行时间
        if (detectionActive.value && detectionStartTime.value > 0) {
          runningTime.value = Math.floor((Date.now() - detectionStartTime.value) / 1000)
        } else if (cameraActive.value && cameraStartTime.value > 0) {
          runningTime.value = Math.floor((Date.now() - cameraStartTime.value) / 1000)
        } else {
          runningTime.value = 0
        }
      }, 1000)
    }

    const stopTimer = () => {
      if (timeTimer.value) {
        clearInterval(timeTimer.value)
        timeTimer.value = null
      }
    }

    // 格式化运行时间
    const formatRunningTime = (seconds: number): string => {
      const hrs = Math.floor(seconds / 3600)
      const mins = Math.floor((seconds % 3600) / 60)
      const secs = seconds % 60
      
      if (hrs > 0) {
        return `${hrs.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
      } else {
        return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
      }
    }

    // 页面离开时的清理
    const handleBeforeUnload = (event: BeforeUnloadEvent) => {
      // 如果正在检测，提示用户确认离开，但不记录日志
      // 因为 stopDetection 会在组件卸载时自动调用并记录日志
      if (detectionActive.value) {
        const message = '实时检测正在进行中，确定要离开吗？'
        event.returnValue = message
        return message
      }
    }

    // 调试函数 - 检查视频状态
    const debugVideoStatus = () => {
      if (videoElement.value) {
        const video = videoElement.value
        console.log('视频元素状态检查:', {
          srcObject: !!video.srcObject,
          currentSrc: video.currentSrc,
          videoWidth: video.videoWidth,
          videoHeight: video.videoHeight,
          readyState: video.readyState,
          networkState: video.networkState,
          paused: video.paused,
          ended: video.ended,
          muted: video.muted,
          autoplay: video.autoplay,
          playsinline: video.getAttribute('playsinline'),
          style: {
            display: video.style.display,
            visibility: video.style.visibility,
            width: video.style.width,
            height: video.style.height
          },
          computedStyle: {
            display: getComputedStyle(video).display,
            visibility: getComputedStyle(video).visibility,
            width: getComputedStyle(video).width,
            height: getComputedStyle(video).height
          }
        })
        
        // 检查流的状态
        if (currentStream.value) {
          const tracks = currentStream.value.getVideoTracks()
          console.log('视频流状态:', {
            active: currentStream.value.active,
            id: currentStream.value.id,
            tracks: tracks.map(track => ({
              enabled: track.enabled,
              muted: track.muted,
              readyState: track.readyState,
              kind: track.kind,
              label: track.label
            }))
          })
        }
      } else {
        console.log('视频元素不存在!')
      }
    }

    // 组件挂载
    onMounted(async () => {
      // 首先检查浏览器兼容性
      const browserCheck = checkBrowserSupport()
      if (!browserCheck.supported) {
        console.error('浏览器环境检查失败:', browserCheck.reason)
        ElMessage.error(`当前环境不支持摄像头功能: ${browserCheck.reason}`)
        
        // 显示环境信息卡片，帮助用户诊断问题
        showEnvironmentInfo.value = true
        
        // 提供环境信息
        console.log('当前环境信息:', {
          protocol: location.protocol,
          hostname: location.hostname,
          userAgent: navigator.userAgent,
          hasMediaDevices: !!navigator.mediaDevices,
          hasGetUserMedia: !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia),
          hasEnumerateDevices: !!(navigator.mediaDevices && navigator.mediaDevices.enumerateDevices)
        })
        
        return // 环境不支持，停止初始化
      }
      
      // 检查用户权限
      const hasPermission = await checkUserPermissions()
      if (!hasPermission) {
        return // 权限检查失败，停止初始化
      }
      
      // 尝试获取摄像头设备
      try {
        await getAvailableDevices()
      } catch (error) {
        console.error('初始化摄像头设备失败:', error)
        ElMessage.error('摄像头功能初始化失败，请检查浏览器设置和设备权限')
        // 显示环境信息，帮助用户诊断问题
        showEnvironmentInfo.value = true
      }
      
      // 注册页面卸载事件
      window.addEventListener('beforeunload', handleBeforeUnload)
    })

    // 组件卸载
    onUnmounted(() => {
      stopCamera()
      stopTimer()
      window.removeEventListener('beforeunload', handleBeforeUnload)
    })

    return {
      // DOM引用
      videoElement,
      overlayCanvas,
      
      // 设备相关
      availableDevices,
      selectedDeviceId,
      selectedResolution,
      refreshDevices,
      
      // 摄像头状态
      cameraActive,
      videoResolution,
      toggleCamera,
      onVideoLoaded,
      
      // 检测相关
      detectionActive,
      detectionResults,
      detectionFrequency,
      toggleDetection,
      
      // 性能优化
      performanceMode,
      
      // 录制功能
      recording,
      toggleRecording,
      captureFrame,
      
      // 统计信息
      runningTime,
      formatRunningTime,
      
      // 环境检查
      showEnvironmentInfo,
      environmentStatus,
      
      // 调试功能
      debugVideoStatus
    }
  }
})
</script>

<style scoped>
.realtime-detection {
  display: flex;
  gap: 20px;
  height: calc(100vh - 120px);
  padding: 20px;
  box-sizing: border-box;
}

/* 左侧控制面板 */
.left-panel {
  flex: 0 0 350px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  height: 100%;
  overflow-y: auto;
}

/* 右侧视频区域 */
.right-panel {
  flex: 1;
  height: 100%;
}

.video-card {
  height: 100%;
  display: flex;
  flex-direction: column;
}

/* 设备控制 */
.device-controls {
  padding: 20px;
}

.control-item {
  margin-bottom: 20px;
}

.control-label {
  display: block;
  color: #ffffff;
  font-size: 14px;
  margin-bottom: 8px;
  font-weight: 500;
}

.control-buttons {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 25px;
}

.control-buttons .btn-primary,
.control-buttons .btn-success,
.control-buttons .btn-secondary {
  width: 100%;
  padding: 12px 20px;
  font-size: 14px;
  border-radius: 8px;
  border: none;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.btn-primary {
  background: linear-gradient(135deg, var(--primary-color), #0099cc);
  color: #ffffff;
}

.btn-primary:hover:not(:disabled) {
  background: linear-gradient(135deg, #0099cc, var(--primary-color));
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(0, 245, 255, 0.3);
}

.btn-success {
  background: linear-gradient(135deg, #2ed573, #20bf6b);
  color: #ffffff;
}

.btn-success:hover:not(:disabled) {
  background: linear-gradient(135deg, #20bf6b, #2ed573);
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(46, 213, 115, 0.3);
}

.btn-secondary {
  background: linear-gradient(135deg, #666, #888);
  color: #ffffff;
}

.btn-secondary:hover:not(:disabled) {
  background: linear-gradient(135deg, #888, #666);
  transform: translateY(-2px);
}

.btn-primary:disabled,
.btn-success:disabled,
.btn-secondary:disabled {
  background: #444;
  color: #888;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.btn-icon {
  font-size: 16px;
}

.loading-icon {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* 检测设置 */
.detection-settings {
  padding: 20px;
}

.setting-item {
  margin: 20px 0;
  color: #ffffff;
}

.slider-label {
  color: #ffffff;
  font-size: 14px;
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
}

/* Element Plus 组件样式覆盖 */
:deep(.el-select) {
  width: 100%;
}

:deep(.el-select .el-input__wrapper) {
  background-color: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(0, 245, 255, 0.3);
  color: #ffffff;
}

:deep(.el-select .el-input__inner) {
  color: #ffffff;
}

:deep(.el-select .el-input__wrapper:hover) {
  border-color: var(--primary-color);
}

:deep(.el-switch) {
  --el-switch-on-color: var(--primary-color);
  --el-switch-off-color: #666;
}

:deep(.el-switch__label) {
  color: #ffffff;
}

:deep(.el-slider) {
  --el-slider-main-bg-color: var(--primary-color);
  --el-slider-runway-bg-color: rgba(255, 255, 255, 0.2);
}

:deep(.el-slider__button) {
  border: 2px solid var(--primary-color);
  background: var(--primary-color);
}

/* 统计信息 */
.stats-content {
  padding: 20px;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 12px 0;
  padding: 8px 0;
  border-bottom: 1px solid rgba(0, 245, 255, 0.1);
}

.stat-label {
  color: #ccc;
  font-size: 14px;
}

.stat-value {
  color: var(--primary-color);
  font-weight: bold;
  font-size: 16px;
}

.defect-count {
  color: #ff4757;
}

/* 视频容器 */
.video-container {
  flex: 1;
  position: relative;
  display: flex;
  justify-content: center;
  align-items: center;
  background: #000;
  border-radius: 8px;
  overflow: hidden;
  margin: 0 20px 20px 20px;
  min-height: 400px;
}

.video-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #666;
  height: 100%;
  width: 100%;
}

.placeholder-icon {
  font-size: 64px;
  margin-bottom: 16px;
  color: #444;
}

.video-wrapper {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  background: #000;
}

.video-wrapper.video-hidden {
  display: none;
}

.video-preview {
  max-width: 100%;
  max-height: 100%;
  width: auto;
  height: auto;
  object-fit: contain;
  border-radius: 8px;
  display: block;
  background: #000;
}

.detection-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 10;
  object-fit: contain;
}

/* 状态栏 */
.status-bar {
  display: flex;
  justify-content: space-around;
  align-items: center;
  padding: 15px 20px;
  background: rgba(0, 0, 0, 0.3);
  border-top: 1px solid rgba(0, 245, 255, 0.2);
  color: #ffffff;
  font-size: 14px;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.status-detecting {
  color: #2ed573;
  animation: pulse 2s infinite;
}

.status-recording {
  color: #ff4757;
  animation: pulse 1s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

/* 操作按钮 */
.app-card-actions {
  display: flex;
  gap: 10px;
}

:deep(.el-button) {
  background: rgba(0, 245, 255, 0.1);
  border: 1px solid rgba(0, 245, 255, 0.3);
  color: #ffffff;
}

:deep(.el-button:hover) {
  background: rgba(0, 245, 255, 0.2);
  border-color: var(--primary-color);
}

:deep(.el-button--primary) {
  background: var(--primary-color);
  border-color: var(--primary-color);
}

:deep(.el-button--danger) {
  background: #ff4757;
  border-color: #ff4757;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .realtime-detection {
    flex-direction: column;
    height: auto;
  }
  
  .left-panel {
    flex: none;
    width: 100%;
    height: auto;
    max-height: none;
  }
  
  .right-panel {
    flex: none;
    height: 500px;
  }
}

@media (max-width: 768px) {
  .realtime-detection {
    padding: 10px;
    gap: 15px;
  }
  
  .left-panel {
    gap: 15px;
  }
  
  .control-buttons {
    gap: 10px;
  }
  
  .status-bar {
    flex-wrap: wrap;
    gap: 10px;
    justify-content: center;
  }
  
  .video-container {
    min-height: 300px;
    margin: 0 10px 10px 10px;
  }
  
  .device-controls,
  .detection-settings,
  .stats-content {
    padding: 15px;
  }
}

/* 环境信息 */
.environment-info {
  padding: 20px;
}

.env-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 10px 0;
  padding: 8px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.env-label {
  color: #ccc;
  font-size: 14px;
  font-weight: 500;
}

.env-value {
  color: #2ed573;
  font-weight: bold;
  font-size: 14px;
}

.env-error {
  color: #ff4757 !important;
}

/* 设置提示 */
.setting-hint {
  color: #999;
  font-size: 12px;
  margin-top: 8px;
  line-height: 1.4;
}

/* 滚动条样式 */
.left-panel::-webkit-scrollbar {
  width: 6px;
}

.left-panel::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 3px;
}

.left-panel::-webkit-scrollbar-thumb {
  background: rgba(0, 245, 255, 0.5);
  border-radius: 3px;
}

.left-panel::-webkit-scrollbar-thumb:hover {
  background: var(--primary-color);
}
</style>
