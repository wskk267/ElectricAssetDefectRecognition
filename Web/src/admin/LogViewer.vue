<template>
  <div class="log-viewer">
    <!-- 日志类型选择 -->
    <el-card class="app-card control-card">
      <div class="control-section flex-between">
        <div class="log-type-section flex-center">
          <span class="section-label text-primary">
            <el-icon style="margin-right: 8px;"><Document /></el-icon>
            日志类型:
          </span>
          <div class="radio-group-wrapper">
            <el-radio-group v-model="logType" @change="switchLogType" class="custom-radio-group">
              <el-radio-button label="admin">
                <el-icon style="margin-right: 6px;"><UserFilled /></el-icon>
                管理员日志
              </el-radio-button>
              <el-radio-button label="user">
                <el-icon style="margin-right: 6px;"><User /></el-icon>
                用户日志
              </el-radio-button>
            </el-radio-group>
          </div>
        </div>
        
        <div class="filter-section">
          <div class="filter-controls">
            <el-select 
              v-model="selectedUser" 
              placeholder="选择用户筛选" 
              clearable
              @change="handleUserChange"
              v-if="logType === 'user'"
              class="user-select"
              filterable
            >
              <template #prefix>
                <el-icon><User /></el-icon>
              </template>
              <el-option
                v-for="user in users"
                :key="user.id"
                :label="user.username"
                :value="user.id"
              >
                <div class="user-option">
                  <el-icon style="margin-right: 8px; color: #00f5ff;"><User /></el-icon>
                  <span>{{ user.username }}</span>
                </div>
              </el-option>
            </el-select>
            
            <div class="action-buttons">
              <el-button @click="loadLogs" :loading="loading" type="primary" class="refresh-btn">
                <el-icon><RefreshRight /></el-icon>
                刷新数据
              </el-button>
              
              <el-button @click="clearFilters" v-if="selectedUser" type="warning" size="small" class="clear-btn">
                <el-icon><Close /></el-icon>
                清除筛选
              </el-button>
            </div>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 日志统计 -->
    <div class="stats-row">
      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-icon">
            <el-icon><Document /></el-icon>
          </div>
          <div class="stat-info">
            <h3>{{ logStats.total }}</h3>
            <p>总日志数</p>
          </div>
        </div>
      </el-card>
      
      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-icon today-logs">
            <el-icon><Calendar /></el-icon>
          </div>
          <div class="stat-info">
            <h3>{{ logStats.today }}</h3>
            <p>今日日志</p>
          </div>
        </div>
      </el-card>
      
      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-icon active-users">
            <el-icon><User /></el-icon>
          </div>
          <div class="stat-info">
            <h3>{{ logStats.activeUsers }}</h3>
            <p>活跃用户</p>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 日志列表 -->
    <el-card class="app-card table-card">
      <template #header>
        <div class="app-card-header flex-between">
          <div class="table-title flex-center">
            <h3>{{ logType === 'admin' ? '管理员操作日志' : '用户操作日志' }}</h3>
            <el-tag 
              v-if="selectedUser && logType === 'user'" 
              size="small" 
              type="success" 
              effect="dark"
              class="filter-tag"
            >
              筛选用户: {{ getUserName(selectedUser) }}
            </el-tag>
          </div>
          <div class="export-section">
            <el-button size="small" @click="exportLogs" :disabled="logs.length === 0">
              <el-icon><Download /></el-icon>
              导出日志
            </el-button>
          </div>
        </div>
      </template>
      
      <div class="app-table">
        <el-table 
          :data="logs" 
          style="width: 100%" 
          v-loading="loading"
          max-height="600"
          empty-text="暂无日志数据"
          :fit="true"
        >
        <!-- 管理员日志表格 -->
        <template v-if="logType === 'admin'">
          <el-table-column prop="id" label="ID" sortable />
          <el-table-column label="操作时间" sortable>
            <template #default="scope">
              <div class="time-info">
                <el-icon style="margin-right: 5px; color: #00f5ff;"><Calendar /></el-icon>
                <span class="time-text">{{ formatTime(scope.row.time) }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="操作内容" >
            <template #default="scope">
              <div class="log-content">
                <el-tag :type="getLogType(scope.row.log)" size="small">
                  {{ getLogAction(scope.row.log) }}
                </el-tag>
                <span class="log-text">{{ scope.row.log }}</span>
              </div>
            </template>
          </el-table-column>
        </template>
        
        <!-- 用户日志表格 -->
        <template v-else-if="logType === 'user'">
          <!-- 所有用户日志显示完整信息 -->
          <el-table-column prop="id" label="ID" sortable />
          <el-table-column label="用户" v-if="!selectedUser">
            <template #default="scope">
              <div class="user-info">
                <el-tag size="small" type="info" effect="dark">
                  {{ getUserName(scope.row.user_id) }}
                </el-tag>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="操作时间" sortable>
            <template #default="scope">
              <div class="time-info">
                <el-icon style="margin-right: 5px; color: #00f5ff;"><Calendar /></el-icon>
                <span class="time-text">{{ formatTime(scope.row.time) }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="操作类型">
            <template #default="scope">
              <el-tag :type="getOperationType(scope.row.class)" size="small">
                {{ getOperationName(scope.row.class) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="处理数量" width="100">
            <template #default="scope">
              <div class="quantity-info">
                <el-icon style="color: #67c23a; margin-right: 5px;"><Document /></el-icon>
                <span class="quantity-text">{{ scope.row.quantity }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="剩余额度" width="120">
            <template #default="scope">
              <div class="remain-info">
                <el-icon style="color: #e6a23c; margin-right: 5px;"><Wallet /></el-icon>
                <span class="remain-text">
                  {{ scope.row.remain === -1 ? '无限制' : scope.row.remain }}
                </span>
              </div>
            </template>
          </el-table-column>
        </template>
        </el-table>
      </div>
      
      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[20, 50, 100, 200]"
          layout="total, sizes, prev, pager, next, jumper"
          :total="totalLogs"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, reactive, onMounted, computed, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { 
  Document, Calendar, User, RefreshRight, Download, Wallet, UserFilled, Close 
} from '@element-plus/icons-vue'
import { useApi } from '../composables/useApi'
import { usePagination } from '../composables/usePagination'
import { 
  formatTime, 
  getLogType, 
  getLogAction, 
  getOperationType, 
  getOperationName, 
  generateCSV, 
  downloadFile 
} from '../utils/common'

interface AdminLog {
  id: number
  user_id: number
  time: string
  log: string
}

interface UserLog {
  id: number
  user_id: number
  time: string
  class: string
  quantity: number
  remain: number
}

interface UserInfo {
  id: number
  username: string
}

export default defineComponent({
  name: 'AdminLogViewer',
  components: {
    Document,
    Calendar,
    User,
    RefreshRight,
    Download,
    Wallet,
    UserFilled,
    Close
  },
  setup() {
    const apiHook = useApi()
    console.log('LogViewer useApi hook:', apiHook)
    const { request, loading } = apiHook
    console.log('LogViewer request function:', typeof request)
    console.log('LogViewer loading ref:', loading)
    
    const { 
      currentPage, 
      pageSize, 
      total: totalLogs, 
      handleSizeChange, 
      handleCurrentChange 
    } = usePagination()
    
    const logType = ref('admin')
    const selectedUser = ref<number | null>(null)
    
    const logs = ref<(AdminLog | UserLog)[]>([])
    const users = ref<UserInfo[]>([])
    
    const logStats = reactive({
      total: 0,
      today: 0,
      activeUsers: 0
    })

    const loadLogs = async () => {
      try {
        if (typeof request !== 'function') {
          console.error('request不是一个函数:', request)
          ElMessage.error('API请求函数未正确初始化')
          return
        }
        
        let url = ''
        let params: any = {
          page: currentPage.value,
          limit: pageSize.value
        }
        
        if (logType.value === 'admin') {
          url = '/api/admin/logs'
        } else {
          url = selectedUser.value 
            ? `/api/admin/user_logs/${selectedUser.value}`
            : '/api/admin/user_logs/all'
        }
        
        const response = await request('get', url, params)
        
        if (response.success) {
          logs.value = response.data.logs || response.data
          totalLogs.value = response.data.total || logs.value.length
          updateStats() // 确保统计信息更新
        }
      } catch (error: any) {
        console.error('加载日志失败:', error)
        ElMessage.error('加载日志失败')
        logs.value = []
        totalLogs.value = 0
        logStats.total = 0
        logStats.today = 0
        logStats.activeUsers = 0
      }
    }

    const loadUsers = async () => {
      try {
        const response = await request('get', '/api/admin/users')
        
        if (response.success) {
          const usersData = response.data.users || []
          users.value = usersData.map((user: any) => ({
            id: user.id,
            username: user.username
          }))
        }
      } catch (error: any) {
        console.error('加载用户列表失败:', error)
      }
    }

    const updateStats = () => {
      // 直接使用本地计算，避免CORS问题
      logStats.total = totalLogs.value
      
      const today = new Date().toDateString()
      logStats.today = logs.value.filter(log => {
        if (!log.time) return false
        try {
          return new Date(log.time).toDateString() === today
        } catch {
          return false
        }
      }).length
      
      if (logType.value === 'user') {
        const uniqueUsers = new Set(logs.value.map(log => log.user_id))
        logStats.activeUsers = uniqueUsers.size
      } else {
        logStats.activeUsers = 0
      }
    }

    const switchLogType = () => {
      selectedUser.value = null
      currentPage.value = 1
      // 添加视觉反馈
      ElMessage.info(`已切换到${logType.value === 'admin' ? '管理员' : '用户'}日志`)
      loadLogs()
    }

    const handleUserChange = () => {
      currentPage.value = 1 // 重置页码
      if (selectedUser.value) {
        const userName = getUserName(selectedUser.value)
        ElMessage.info(`已筛选用户: ${userName}`)
      } else {
        ElMessage.info('已清除用户筛选，显示所有用户日志')
      }
      loadLogs()
    }

    const clearFilters = () => {
      selectedUser.value = null
      currentPage.value = 1
      ElMessage.success('已清除所有筛选条件')
      loadLogs()
    }

    const getUserName = (userId: number) => {
      const user = users.value.find(u => u.id === userId)
      return user ? user.username : `用户${userId}`
    }

    const handleSizeChangeWrapper = (newSize: number) => {
      handleSizeChange(newSize)
      loadLogs()
    }

    const handleCurrentChangeWrapper = (newPage: number) => {
      handleCurrentChange(newPage)
      loadLogs()
    }

    const exportLogs = () => {
      try {
        let headers, rowMapper
        
        if (logType.value === 'admin') {
          headers = ['ID', '时间', '操作内容']
          rowMapper = (log: any) => [
            log.id,
            formatTime(log.time),
            log.log
          ]
        } else {
          headers = ['ID', '用户', '时间', '操作类型', '处理数量', '剩余额度']
          rowMapper = (log: any) => [
            log.id,
            getUserName(log.user_id),
            formatTime(log.time),
            getOperationName(log.class),
            log.quantity,
            log.remain === -1 ? '无限制' : log.remain
          ]
        }
        
        const csvContent = generateCSV(logs.value, headers, rowMapper)
        const filename = `${logType.value}_logs_${new Date().getTime()}.csv`
        
        if (downloadFile(csvContent, filename, 'text/csv')) {
          ElMessage.success('日志导出成功')
        } else {
          ElMessage.error('导出失败')
        }
      } catch (error: any) {
        console.error('导出失败:', error)
        ElMessage.error('导出失败')
      }
    }

    onMounted(async () => {
      await nextTick()
      console.log('LogViewer mounted, 准备加载数据...')
      console.log('request function available:', typeof request)
      loadUsers()
      loadLogs()
    })

    return {
      loading,
      logType,
      selectedUser,
      currentPage,
      pageSize,
      totalLogs,
      logs,
      users,
      logStats,
      loadLogs,
      switchLogType,
      handleUserChange,
      clearFilters,
      getUserName,
      handleSizeChange: handleSizeChangeWrapper,
      handleCurrentChange: handleCurrentChangeWrapper,
      exportLogs,
      // 使用导入的工具函数
      formatTime,
      getLogType,
      getLogAction,
      getOperationType,
      getOperationName
    }
  }
})
</script>

<style scoped>
/* LogViewer 特定样式 - 只保留独特的样式 */
.log-viewer {
  display: flex;
  flex-direction: column;
  gap: 25px;
  animation: fadeInUp 0.6s ease-out;
}

/* 控制面板特定样式 */
.control-section {
  gap: 20px;
  background: rgba(0, 245, 255, 0.02);
  padding: 20px;
  border-radius: 12px;
}

.log-type-section {
  gap: 15px;
}

.section-label {
  font-weight: bold;
  font-size: 14px;
}

.filter-section {
  display: flex;
  align-items: center;
  gap: 15px;
}

.user-select {
  width: 200px;
}

/* 单选按钮组美化 */
:deep(.el-radio-group) {
  padding: 8px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 25px;
  border: 1px solid rgba(0, 245, 255, 0.2);
}

:deep(.el-radio-button) {
  margin: 0 2px;
}

:deep(.el-radio-button__inner) {
  background-color: transparent;
  border: none;
  color: rgba(255, 255, 255, 0.7);
  border-radius: 20px;
  transition: all 0.3s ease;
  padding: 8px 16px;
}

:deep(.el-radio-button__inner:hover) {
  background-color: rgba(0, 245, 255, 0.1);
  color: #00f5ff;
}

:deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
  background: var(--gradient-primary);
  color: #000;
  box-shadow: 0 4px 15px rgba(0, 245, 255, 0.4);
  transform: translateY(-1px);
}

/* 统计卡片 */
.stats-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
}

.stat-card {
  transition: all 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-3px);
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 20px;
}

.stat-icon {
  width: 60px;
  height: 60px;
  background: var(--gradient-primary);
  border-radius: 15px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 5px 15px rgba(0, 245, 255, 0.3);
}

.stat-icon.today-logs {
  background: var(--gradient-warning);
  box-shadow: 0 5px 15px rgba(230, 162, 60, 0.3);
}

.stat-icon.active-users {
  background: var(--gradient-success);
  box-shadow: 0 5px 15px rgba(103, 194, 58, 0.3);
}

.stat-icon .el-icon {
  font-size: 24px;
  color: #000;
}

.stat-info h3 {
  margin: 0 0 5px 0;
  color: var(--primary-color);
  font-size: 28px;
  font-weight: bold;
}

.stat-info p {
  margin: 0;
  color: var(--text-secondary);
  font-size: 14px;
}

/* 表格特定样式 */
.filter-tag {
  background: linear-gradient(45deg, rgba(103, 194, 58, 0.2), rgba(133, 206, 97, 0.1));
  border-color: rgba(103, 194, 58, 0.5);
  color: #67c23a;
  font-weight: 500;
  padding: 4px 12px;
  border-radius: 20px;
}

.time-info, .user-info, .quantity-info, .remain-info {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 8px;
  background: rgba(0, 245, 255, 0.05);
  border: 1px solid rgba(0, 245, 255, 0.2);
  transition: all 0.3s ease;
}

.time-info:hover, .user-info:hover, .quantity-info:hover, .remain-info:hover {
  background: rgba(0, 245, 255, 0.1);
  border-color: rgba(0, 245, 255, 0.4);
  transform: scale(1.02);
}

.time-text {
  color: var(--text-primary);
  font-size: 13px;
  font-weight: 500;
}

.quantity-text {
  color: #67c23a;
  font-weight: bold;
  font-size: 14px;
}

.remain-text {
  color: #e6a23c;
  font-weight: bold;
  font-size: 14px;
}

.log-content {
  display: flex;
  align-items: center;
  gap: 12px;
}

.log-text {
  color: var(--text-primary);
  font-weight: 500;
}

/* 分页 */
.pagination-wrapper {
  padding: 25px 0;
  text-align: center;
  background: rgba(0, 245, 255, 0.02);
  border-radius: 12px;
  margin-top: 20px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .control-section {
    flex-direction: column;
    align-items: stretch;
    gap: 15px;
  }
  
  .log-type-section {
    justify-content: center;
  }
  
  .filter-section {
    justify-content: center;
    flex-wrap: wrap;
  }
  
  .user-select {
    width: 100%;
    max-width: 300px;
  }
  
  .stats-row {
    grid-template-columns: 1fr;
  }
  
  .filter-tag {
    margin-left: 0;
  }
  
  .time-info,
  .quantity-info,
  .remain-info {
    flex-direction: column;
    align-items: flex-start;
    gap: 5px;
  }
  
  .log-content {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
}
</style>
