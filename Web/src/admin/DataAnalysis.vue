<template>
  <div class="data-analysis">
    <!-- 概览统计 -->
    <StatsGrid :stats="overviewStats" />

    <!-- 图表区域 -->
    <div class="charts-section">
      <!-- 使用趋势图 -->
      <el-card class="chart-card">
        <template #header>
          <div class="card-header">
            <el-icon><TrendCharts /></el-icon>
            使用趋势分析
          </div>
        </template>
        
        <div class="chart-container">
          <div class="trend-chart">
            <canvas ref="trendChartRef"></canvas>
          </div>
        </div>
      </el-card>

      <!-- 缺陷类型分布 -->
      <el-card class="chart-card">
        <template #header>
          <div class="card-header">
            <el-icon><PieChart /></el-icon>
            缺陷类型分布
          </div>
        </template>
        
        <div class="chart-container">
          <div class="pie-chart">
            <canvas ref="pieChartRef"></canvas>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 用户活跃度 -->
    <div class="activity-section">
      <el-card class="activity-card">
        <template #header>
          <div class="card-header">
            <el-icon><User /></el-icon>
            用户活跃度排行
          </div>
        </template>
        
        <div class="activity-list">
          <div 
            v-for="(user, index) in usersWithPercentage" 
            :key="user.id"
            class="activity-item"
          >
            <div class="rank">
              <span class="rank-number" :class="user.rankClass">{{ index + 1 }}</span>
            </div>
            <div class="user-info">
              <span class="username">{{ user.username }}</span>
              <span class="activity-count">{{ user.activity }} 次操作</span>
            </div>
            <div class="progress-section">
              <el-progress 
                :percentage="user.percentage" 
                :color="user.progressColor"
                :show-text="false"
              />
            </div>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 系统性能指标 -->
    <div class="performance-section">
      <el-card class="performance-card">
        <template #header>
          <div class="card-header">
            <el-icon><Monitor /></el-icon>
            系统性能指标
          </div>
        </template>
        
        <div class="performance-metrics">
          <div class="metric-item">
            <div class="metric-icon cpu">
              <el-icon><Cpu /></el-icon>
            </div>
            <div class="metric-info">
              <div class="metric-label">平均处理时间</div>
              <div class="metric-value">{{ performanceStats.avgProcessTime }}s</div>
            </div>
          </div>
          
          <div class="metric-item">
            <div class="metric-icon success">
              <el-icon><Check /></el-icon>
            </div>
            <div class="metric-info">
              <div class="metric-label">成功率</div>
              <div class="metric-value">{{ performanceStats.successRate }}%</div>
            </div>
          </div>
          
          <div class="metric-item">
            <div class="metric-icon storage">
              <el-icon><FolderOpened /></el-icon>
            </div>
            <div class="metric-info">
              <div class="metric-label">存储使用量</div>
              <div class="metric-value">{{ performanceStats.storageUsed }}GB</div>
            </div>
          </div>
          
          <div class="metric-item">
            <div class="metric-icon speed">
              <el-icon><Lightning /></el-icon>
            </div>
            <div class="metric-info">
              <div class="metric-label">系统负载</div>
              <div class="metric-value">{{ performanceStats.systemLoad }}%</div>
            </div>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 快速操作 -->
    <div class="actions-section">
      <el-card class="actions-card">
        <template #header>
          <div class="card-header">
            <el-icon><Setting /></el-icon>
            快速操作
          </div>
        </template>
        
        <div class="quick-actions">
          <el-button type="primary" @click="refreshAllData" :loading="loading">
            <el-icon><RefreshRight /></el-icon>
            刷新数据
          </el-button>
          
          <el-button @click="exportReport">
            <el-icon><Download /></el-icon>
            导出报告
          </el-button>
          
          <el-button @click="systemCleanup">
            <el-icon><Delete /></el-icon>
            系统清理
          </el-button>
          
          <el-button type="warning" @click="systemSettings">
            <el-icon><Tools /></el-icon>
            系统设置
          </el-button>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, reactive, onMounted, onUnmounted, nextTick, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  DataAnalysis as DataAnalysisIcon, TrendCharts, PieChart, User, Monitor, 
  Cpu, Check, FolderOpened, Lightning, Setting, 
  RefreshRight, Download, Delete, Tools 
} from '@element-plus/icons-vue'
import axiosInstance from '../axios'
import { useApi } from '../composables/useApi'
import StatsGrid from '../components/StatsGrid.vue'

interface UserActivity {
  id: number
  username: string
  activity: number
}

export default defineComponent({
  name: 'AdminDataAnalysis',
  components: {
    DataAnalysis: DataAnalysisIcon,
    TrendCharts,
    PieChart,
    User,
    Monitor,
    Cpu,
    Check,
    FolderOpened,
    Lightning,
    Setting,
    RefreshRight,
    Download,
    Delete,
    Tools,
    StatsGrid
  },
  setup() {
    const { request, loading } = useApi()
    const trendChartRef = ref<HTMLCanvasElement>()
    const pieChartRef = ref<HTMLCanvasElement>()
    
    const systemStats = reactive({
      totalUsers: 0,
      totalImages: 0,
      totalDefects: 0,
      activeToday: 0
    })
    
    const performanceStats = reactive({
      avgProcessTime: 0,
      successRate: 0,
      storageUsed: 0,
      systemLoad: 0
    })
    
    const topUsers = ref<UserActivity[]>([])

    // 概览统计数据
    const overviewStats = computed(() => [
      {
        label: '总用户数',
        value: systemStats.totalUsers,
        icon: User,
        iconType: 'primary',
        type: 'primary'
      },
      {
        label: '处理图片',
        value: systemStats.totalImages,
        icon: DataAnalysisIcon,
        iconType: 'success',
        type: 'success'
      },
      {
        label: '发现缺陷',
        value: systemStats.totalDefects,
        icon: Monitor,
        iconType: 'warning',
        type: 'warning'
      },
      {
        label: '今日活跃',
        value: systemStats.activeToday,
        icon: Lightning,
        iconType: 'info',
        type: 'info'
      }
    ])

    // 计算最大活动值的计算属性
    const maxActivity = computed(() => {
      if (!topUsers.value || topUsers.value.length === 0) return 1
      return Math.max(...topUsers.value.map(u => u.activity || 0))
    })

    // 预计算用户活动百分比的计算属性
    const usersWithPercentage = computed(() => {
      if (!topUsers.value || topUsers.value.length === 0) return []
      const max = maxActivity.value
      return topUsers.value.map((user, index) => {
        if (!user) return { id: 0, username: '', activity: 0, percentage: 0, rankClass: '', progressColor: '' }
        return {
          ...user,
          percentage: max > 0 ? Math.round((user.activity / max) * 100) : 0,
          rankClass: getRankClass(index),
          progressColor: getProgressColor(index)
        }
      }).filter(u => u.id !== 0)
    })

    const loadSystemStats = async () => {
      try {
        // 获取系统统计数据
        const statsResponse = await request('get', '/api/admin/statistics')
        
        // 获取用户活跃度数据
        const usersResponse = await request('get', '/api/admin/user_logs/all?page=1&limit=1000')
        
        if (statsResponse.success) {
          const data = statsResponse.data
          Object.assign(systemStats, {
            totalUsers: data.totalUsers || 0,
            totalImages: data.totalImages || 0,
            totalDefects: data.totalDefects || 0,
            activeToday: data.activeToday || 0
          })
          
          Object.assign(performanceStats, {
            avgProcessTime: data.avgProcessTime || 2.3,
            successRate: data.successRate || 95.2,
            storageUsed: data.storageUsed || 12.5,
            systemLoad: data.systemLoad || 35
          })
        }
        
        // 处理用户活跃度数据
        if (usersResponse.success && usersResponse.data) {
          topUsers.value = processUserActivity(usersResponse.data)
        } else {
          topUsers.value = generateMockUsers()
        }
        
      } catch (error: any) {
        console.error('获取统计数据失败:', error)
        // 使用模拟数据
        loadMockData()
      }
    }

    const processUserActivity = (userLogs: any[]) => {
      // 统计每个用户的活动次数
      const activityMap = new Map()
      
      userLogs.forEach(log => {
        const userId = log.user_id
        const username = log.username || `用户${userId}`
        
        if (activityMap.has(userId)) {
          activityMap.get(userId).activity += 1
        } else {
          activityMap.set(userId, {
            id: userId,
            username: username,
            activity: 1
          })
        }
      })
      
      // 转换为数组并排序
      return Array.from(activityMap.values())
        .sort((a, b) => b.activity - a.activity)
        .slice(0, 5) // 只取前5名
    }

    const generateMockUsers = (): UserActivity[] => {
      return [
        { id: 1, username: 'admin', activity: 156 },
        { id: 2, username: 'testuser', activity: 89 },
        { id: 3, username: 'guest', activity: 45 },
        { id: 4, username: 'user001', activity: 32 },
        { id: 5, username: 'user002', activity: 28 }
      ]
    }

    const loadMockData = () => {
      Object.assign(systemStats, {
        totalUsers: 25,
        totalImages: 1234,
        totalDefects: 89,
        activeToday: 8
      })
      
      Object.assign(performanceStats, {
        avgProcessTime: 2.3,
        successRate: 95.2,
        storageUsed: 12.5,
        systemLoad: 35
      })
      
      topUsers.value = generateMockUsers()
    }

    const drawTrendChart = () => {
      if (!trendChartRef.value) return
      
      const canvas = trendChartRef.value
      if (!canvas || !canvas.parentNode) return
      
      // 设置canvas尺寸适应容器
      const container = canvas.parentNode as HTMLElement
      const containerWidth = Math.max(400, container.clientWidth - 40) // 减去padding
      const containerHeight = Math.min(400, containerWidth * 0.5)
      
      canvas.width = containerWidth
      canvas.height = containerHeight
      canvas.style.width = containerWidth + 'px'
      canvas.style.height = containerHeight + 'px'
      
      const ctx = canvas.getContext('2d')
      if (!ctx) return
      
      // 清空画布
      ctx.clearRect(0, 0, canvas.width, canvas.height)
      
      // 模拟数据
      const data = [12, 19, 15, 25, 22, 30, 35, 28, 32, 40, 38, 45]
      const labels = ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月']
      
      const padding = 60
      const chartWidth = canvas.width - 2 * padding
      const chartHeight = canvas.height - 2 * padding
      
      // 绘制背景网格
      ctx.strokeStyle = 'rgba(0, 245, 255, 0.1)'
      ctx.lineWidth = 1
      
      for (let i = 0; i <= 10; i++) {
        const y = padding + (chartHeight / 10) * i
        ctx.beginPath()
        ctx.moveTo(padding, y)
        ctx.lineTo(canvas.width - padding, y)
        ctx.stroke()
      }
      
      for (let i = 0; i <= 11; i++) {
        const x = padding + (chartWidth / 11) * i
        ctx.beginPath()
        ctx.moveTo(x, padding)
        ctx.lineTo(x, canvas.height - padding)
        ctx.stroke()
      }
      
      // 绘制数据线
      ctx.strokeStyle = '#00f5ff'
      ctx.lineWidth = 3
      ctx.beginPath()
      
      data.forEach((value, index) => {
        const x = padding + (chartWidth / 11) * index
        const y = canvas.height - padding - (value / 50) * chartHeight
        
        if (index === 0) {
          ctx.moveTo(x, y)
        } else {
          ctx.lineTo(x, y)
        }
      })
      
      ctx.stroke()
      
      // 绘制数据点
      ctx.fillStyle = '#00f5ff'
      data.forEach((value, index) => {
        const x = padding + (chartWidth / 11) * index
        const y = canvas.height - padding - (value / 50) * chartHeight
        
        ctx.beginPath()
        ctx.arc(x, y, 4, 0, 2 * Math.PI)
        ctx.fill()
      })
      
      // 绘制标签
      ctx.fillStyle = '#ffffff'
      ctx.font = '12px Arial'
      ctx.textAlign = 'center'
      
      labels.forEach((label, index) => {
        const x = padding + (chartWidth / 11) * index
        ctx.fillText(label, x, canvas.height - 20)
      })
    }

    const drawPieChart = () => {
      if (!pieChartRef.value) return
      
      const canvas = pieChartRef.value
      if (!canvas || !canvas.parentNode) return
      
      // 设置canvas尺寸适应容器
      const container = canvas.parentNode as HTMLElement
      const containerWidth = Math.max(300, container.clientWidth - 40)
      const size = Math.min(400, containerWidth)
      
      canvas.width = size
      canvas.height = size
      canvas.style.width = size + 'px'
      canvas.style.height = size + 'px'
      
      const ctx = canvas.getContext('2d')
      if (!ctx) return
      
      ctx.clearRect(0, 0, canvas.width, canvas.height)
      
      const data = [
        { label: '绝缘子缺陷', value: 35, color: '#00f5ff' },
        { label: '导线磨损', value: 25, color: '#0080ff' },
        { label: '设备老化', value: 20, color: '#67c23a' },
        { label: '连接松动', value: 15, color: '#e6a23c' },
        { label: '其他', value: 5, color: '#f56c6c' }
      ]
      
      const centerX = canvas.width / 2
      const centerY = canvas.height / 2
      const radius = Math.min(canvas.width, canvas.height) * 0.25
      
      let currentAngle = -Math.PI / 2
      
      data.forEach(item => {
        const sliceAngle = (item.value / 100) * 2 * Math.PI
        
        // 绘制扇形
        ctx.fillStyle = item.color
        ctx.beginPath()
        ctx.moveTo(centerX, centerY)
        ctx.arc(centerX, centerY, radius, currentAngle, currentAngle + sliceAngle)
        ctx.closePath()
        ctx.fill()
        
        // 绘制边框
        ctx.strokeStyle = '#1a1a1a'
        ctx.lineWidth = 1
        ctx.stroke()
        
        // 绘制标签
        const labelAngle = currentAngle + sliceAngle / 2
        const labelX = centerX + Math.cos(labelAngle) * (radius + 40)
        const labelY = centerY + Math.sin(labelAngle) * (radius + 40)
        
        ctx.fillStyle = '#ffffff'
        ctx.font = '12px Arial'
        ctx.textAlign = 'center'
        ctx.fillText(`${item.label}`, labelX, labelY)
        ctx.fillText(`${item.value}%`, labelX, labelY + 15)
        
        currentAngle += sliceAngle
      })
    }

    const getRankClass = (index: number) => {
      switch (index) {
        case 0: return 'rank-first'
        case 1: return 'rank-second'
        case 2: return 'rank-third'
        default: return 'rank-other'
      }
    }

    const getActivityPercentage = (activity: number) => {
      const max = maxActivity.value
      return max > 0 ? Math.round((activity / max) * 100) : 0
    }

    const getProgressColor = (index: number) => {
      const colors = ['#00f5ff', '#67c23a', '#e6a23c', '#f56c6c', '#909399']
      return colors[index] || '#909399'
    }

    const refreshAllData = async () => {
      await loadSystemStats()
      await nextTick()
      drawTrendChart()
      drawPieChart()
      ElMessage.success('数据已刷新')
    }
    
    // 窗口resize事件处理
    const handleResize = () => {
      setTimeout(() => {
        drawTrendChart()
        drawPieChart()
      }, 100)
    }

    const exportReport = () => {
      // 模拟导出功能
      ElMessage.success('报告导出功能开发中...')
    }

    const systemCleanup = async () => {
      try {
        await ElMessageBox.confirm('确定要进行系统清理吗？这将清理临时文件和过期日志。', '系统清理', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        })
        
        ElMessage.success('系统清理功能开发中...')
      } catch {
        // 用户取消
      }
    }

    const systemSettings = () => {
      ElMessage.info('系统设置功能开发中...')
    }

    onMounted(async () => {
      await loadSystemStats()
      await nextTick()
      drawTrendChart()
      drawPieChart()
      
      // 添加resize监听
      window.addEventListener('resize', handleResize)
    })

    onUnmounted(() => {
      // 清理canvas引用
      if (trendChartRef.value) {
        trendChartRef.value = undefined
      }
      if (pieChartRef.value) {
        pieChartRef.value = undefined
      }
      
      // 移除resize监听
      window.removeEventListener('resize', handleResize)
    })

    return {
      loading,
      trendChartRef,
      pieChartRef,
      systemStats,
      performanceStats,
      topUsers,
      maxActivity,
      usersWithPercentage,
      overviewStats,
      getRankClass,
      getActivityPercentage,
      getProgressColor,
      refreshAllData,
      exportReport,
      systemCleanup,
      systemSettings
    }
  }
})
</script>

<style scoped>
/* 数据分析容器修复 */
.data-analysis {
  width: 100%;
  max-width: 100%;
  overflow-x: hidden;
  box-sizing: border-box;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 卡片通用样式 */
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
  padding: 25px;
}

.card-header {
  color: #00f5ff;
  font-weight: bold;
  font-size: 16px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.card-header .el-icon {
  font-size: 18px;
}

/* 概览统计 - 使用StatsGrid组件 */

/* 图表区域 */
.charts-section {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 25px;
}

.chart-container {
  position: relative;
  background: rgba(0, 245, 255, 0.02);
  border-radius: 12px;
  padding: 20px;
  border: 1px solid rgba(0, 245, 255, 0.1);
  width: 100%;
  max-width: 100%;
  overflow: hidden;
}

.trend-chart canvas,
.pie-chart canvas {
  border-radius: 8px;
  background: rgba(0, 0, 0, 0.2);
  box-shadow: inset 0 2px 8px rgba(0, 0, 0, 0.3);
  max-width: 100%;
  height: auto;
  object-fit: contain;
}

/* 用户活跃度 */
.activity-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
  max-height: 400px;
  overflow-y: auto;
  padding-right: 10px;
}

.activity-list::-webkit-scrollbar {
  width: 6px;
}

.activity-list::-webkit-scrollbar-track {
  background: rgba(0, 245, 255, 0.1);
  border-radius: 3px;
}

.activity-list::-webkit-scrollbar-thumb {
  background: rgba(0, 245, 255, 0.3);
  border-radius: 3px;
}

.activity-list::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 245, 255, 0.5);
}

.activity-item {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 15px;
  background: linear-gradient(135deg, rgba(0, 245, 255, 0.05), rgba(0, 128, 255, 0.03));
  backdrop-filter: blur(5px);
  transition: all 0.4s ease;
  position: relative;
  overflow: hidden;
}

.activity-item::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(0, 245, 255, 0.1), transparent);
  transition: left 0.8s ease;
}

.activity-item:hover::before {
  left: 100%;
}

.activity-item:hover {
  background: linear-gradient(135deg, rgba(0, 245, 255, 0.1), rgba(0, 128, 255, 0.05));
  transform: translateX(5px);
  box-shadow: 0 8px 25px rgba(0, 245, 255, 0.2);
}

/* 性能指标 */
.performance-metrics {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
}

.metric-item {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 20px;
  background: rgba(0, 245, 255, 0.05);
  border: 1px solid rgba(0, 245, 255, 0.2);
  border-radius: 12px;
  transition: all 0.3s ease;
}

.metric-item:hover {
  background: rgba(0, 245, 255, 0.1);
  border-color: rgba(0, 245, 255, 0.4);
  transform: translateY(-3px);
}

.metric-icon {
  width: 50px;
  height: 50px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
}

.metric-icon.cpu {
  background: linear-gradient(45deg, #e6a23c, #f4bd47);
}

.metric-icon.success {
  background: linear-gradient(45deg, #67c23a, #85ce61);
}

.metric-icon.storage {
  background: linear-gradient(45deg, #409eff, #66b3ff);
}

.metric-icon.speed {
  background: linear-gradient(45deg, #f56c6c, #f78989);
}

.metric-icon .el-icon {
  font-size: 20px;
  color: #000;
}

.metric-info {
  flex: 1;
}

.metric-label {
  color: #888;
  font-size: 14px;
  margin-bottom: 5px;
}

.metric-value {
  color: #00f5ff;
  font-size: 24px;
  font-weight: bold;
}

/* 快速操作 */
.quick-actions {
  display: flex;
  gap: 15px;
  justify-content: center;
  flex-wrap: wrap;
}

:deep(.el-button) {
  padding: 12px 24px;
  border-radius: 25px;
  font-weight: bold;
  transition: all 0.3s ease;
}

:deep(.el-button--primary) {
  background: linear-gradient(45deg, #00f5ff, #0080ff);
  border: none;
  color: #000;
}

:deep(.el-button--primary:hover) {
  background: linear-gradient(45deg, #0080ff, #00f5ff);
  box-shadow: 0 0 20px rgba(0, 245, 255, 0.4);
  transform: translateY(-2px);
}

:deep(.el-button--warning) {
  background: rgba(230, 162, 60, 0.1);
  border-color: rgba(230, 162, 60, 0.3);
  color: #e6a23c;
}

:deep(.el-button--warning:hover) {
  background: rgba(230, 162, 60, 0.2);
  border-color: #e6a23c;
  box-shadow: 0 0 15px rgba(230, 162, 60, 0.3);
  transform: translateY(-2px);
}

/* 进度条美化 */
:deep(.el-progress-bar__outer) {
  background-color: rgba(0, 0, 0, 0.3);
  border-radius: 10px;
  overflow: hidden;
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.2);
}

:deep(.el-progress-bar__inner) {
  border-radius: 10px;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  background-size: 200% 100%;
  animation: progressShine 2s ease-in-out infinite;
}

@keyframes progressShine {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .charts-section {
    grid-template-columns: 1fr;
  }
  
  .performance-metrics {
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  }
}

@media (max-width: 768px) {
  .overview-stats {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .performance-metrics {
    grid-template-columns: 1fr;
  }
  
  .quick-actions {
    flex-direction: column;
    align-items: stretch;
  }
  
  .activity-item {
    flex-direction: column;
    text-align: center;
    gap: 10px;
  }
  
  .progress-section {
    width: 100%;
  }
}
</style>
