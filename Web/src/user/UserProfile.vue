<template>
  <div class="user-profile">
    <div class="profile-container">
      <!-- 用户信息卡片 -->
      <el-card class="profile-card">
        <template #header>
          <div class="card-header">
            <el-icon><User /></el-icon>
            个人信息
          </div>
        </template>
        
        <div class="user-info">
          <div class="avatar-section">
            <div class="avatar">
              <el-icon><User /></el-icon>
            </div>
            <h3>{{ userInfo.username }}</h3>
            <p class="user-type">{{ userInfo.username === 'guest' ? '游客用户' : '普通用户' }}</p>
          </div>
          
          <div class="info-details">
            <div class="info-item">
              <span class="label">用户ID:</span>
              <span class="value">{{ userInfo.userId }}</span>
            </div>
            <div class="info-item">
              <span class="label">用户名:</span>
              <span class="value">{{ userInfo.username }}</span>
            </div>
            <div class="info-item">
              <span class="label">上次登录:</span>
              <span class="value">{{ formatDate(userInfo.registerTime) }}</span>
            </div>
          </div>
        </div>
      </el-card>

      <!-- 权限与用量卡片 -->
      <el-card class="permissions-card">
        <template #header>
          <div class="card-header">
            <el-icon><Key /></el-icon>
            权限与用量
          </div>
        </template>
        
        <div class="permissions-content">
          <div class="permission-item">
            <div class="permission-header">
              <el-icon><Picture /></el-icon>
              <span>图片识别</span>
            </div>
            <div class="usage-info">
              <div class="usage-bar">
                <span class="label">剩余次数:</span>
                <el-progress 
                  v-if="permissions.imagelimit !== -1"
                  :percentage=100 
                  :color="getProgressColor(permissions.imagelimit, 0)"
                  :show-text="false"
                />
                <span class="value">{{ getRemainingImageCount }}</span>
              </div>
            </div>
          </div>

          <div class="permission-item">
            <div class="permission-header">
              <el-icon><FolderOpened /></el-icon>
              <span>批量处理</span>
            </div>
            <div class="usage-info">
              <div class="usage-bar">
                <span class="label">剩余流量:</span>
                <el-progress 
                  v-if="permissions.batchlimit !== -1"
                  :percentage=100 
                  :color="getProgressColor(permissions.batchlimit, 0)"
                  :show-text="false"
                />
                <span class="value">{{ getRemainingBatchCount }}</span>
              </div>
            </div>
          </div>

          <div class="permission-item">
            <div class="permission-header">
              <el-icon><Monitor /></el-icon>
              <span>实时检测</span>
            </div>
            <div class="permission-status">
              <el-tag :type="permissions.realtimePermission ? 'success' : 'danger'">
                {{ permissions.realtimePermission ? '已开启' : '未开启' }}
              </el-tag>
            </div>
          </div>
        </div>
      </el-card>

      <!-- 操作按钮卡片 -->
      <el-card class="actions-card">
        <template #header>
          <div class="card-header">
            <el-icon><Setting /></el-icon>
            操作中心
          </div>
        </template>
        
        <div class="actions-content">
          <el-button type="primary" size="large" @click="refreshUserInfo" :loading="loading">
            <el-icon><RefreshRight /></el-icon>
            刷新信息
          </el-button>
          
          <el-button type="danger" size="large" @click="logout">
            <el-icon><SwitchButton /></el-icon>
            退出登录
          </el-button>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { User, Key, Picture, FolderOpened, Monitor, Setting, RefreshRight, SwitchButton } from '@element-plus/icons-vue'
import axiosInstance from '../axios'
import { formatDate, getUsagePercentage, getProgressColor } from '../utils/common'

export default defineComponent({
  name: 'UserProfile',
  components: {
    User,
    Key,
    Picture,
    FolderOpened,
    Monitor,
    Setting,
    RefreshRight,
    SwitchButton
  },
  setup() {
    const router = useRouter()
    const loading = ref(false)
    
    const userInfo = reactive({
      userId: '',
      username: '',
      registerTime: new Date()
    })
    
    const permissions = reactive({
      imagelimit: -1,  // 初始化为 -1，避免显示错误信息
      batchlimit: -1,  // 初始化为 -1，避免显示错误信息
      realtimePermission: false,
      imageUsed: 0,
      batchUsed: 0
    })

    const getUserInfo = async () => {
      try {
        loading.value = true
        const token = localStorage.getItem('token')
        
        const response = await axiosInstance.get('/api/user/info', {
          headers: { Authorization: `Bearer ${token}` }
        })
        
        if (response.data.success) {
          const data = response.data.data
          Object.assign(userInfo, {
            userId: data.id,
            username: data.username,
            registerTime: new Date(data.update_time || Date.now())
          })
          
          Object.assign(permissions, {
            imagelimit: data.imagelimit,
            batchlimit: data.batchlimit,
            realtimePermission: data.realtimePermission,
            imageUsed: data.imageUsed || 0,
            batchUsed: data.batchUsed || 0
          })
          
          // 更新本地存储的权限信息
          localStorage.setItem('userPermissions', JSON.stringify({
            imagelimit: data.imagelimit,
            batchlimit: data.batchlimit,
            realtimePermission: data.realtimePermission
          }))
        }
      } catch (error: any) {
        console.error('获取用户信息失败:', error)
        ElMessage.error('获取用户信息失败')
      } finally {
        loading.value = false
      }
    }

    const refreshUserInfo = async () => {
      await getUserInfo()
      ElMessage.success('信息已刷新')
    }

    const logout = async () => {
      try {
        await ElMessageBox.confirm('确定要退出登录吗？', '退出确认', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        })
        
        // 清除本地存储
        localStorage.removeItem('token')
        localStorage.removeItem('userType')
        localStorage.removeItem('userId')
        localStorage.removeItem('username')
        localStorage.removeItem('userPermissions')
        
        ElMessage.success('退出成功')
        router.push('/login')
      } catch {
        // 用户取消退出
      }
    }

    const formatDateDisplay = (date: Date) => {
      return formatDate(date)
    }


    // 计算剩余次数的计算属性
    const getRemainingImageCount = computed(() => {
      if (permissions.imagelimit === -1) {
        return '无限制'
      }
      const remaining = Math.max(0, permissions.imagelimit)
      return remaining.toString()
    })

    const getRemainingBatchCount = computed(() => {
      if (permissions.batchlimit === -1) {
        return '无限制'
      }
      const remaining = Math.max(0, permissions.batchlimit)
      return `${remaining.toFixed(3)} MB`
    })

    onMounted(() => {
      // 从本地存储获取基本信息
      userInfo.userId = localStorage.getItem('userId') || ''
      userInfo.username = localStorage.getItem('username') || ''
      
      const storedPermissions = localStorage.getItem('userPermissions')
      console.log('Stored Permissions:', storedPermissions)
      if (storedPermissions) {
        try {
          const parsed = JSON.parse(storedPermissions)
          // 确保数值类型正确，避免字符串转换问题
          Object.assign(permissions, {
            imagelimit: typeof parsed.imagelimit === 'number' ? parsed.imagelimit : -1,
            batchlimit: typeof parsed.batchlimit === 'number' ? parsed.batchlimit : -1,
            realtimePermission: !!parsed.realtimePermission,
            imageUsed: permissions.imageUsed, // 保持当前值，等待服务器更新
            batchUsed: permissions.batchUsed  // 保持当前值，等待服务器更新
          })
        } catch (error) {
          console.error('解析本地权限数据失败:', error)
        }
      }
      
      // 获取最新信息
      getUserInfo()
    })

    return {
      userInfo,
      permissions,
      loading,
      refreshUserInfo,
      logout,
      getUsagePercentage,
      getProgressColor,
      formatDate: formatDateDisplay,
      getRemainingImageCount,
      getRemainingBatchCount
    }
  }
})
</script>

<style scoped>
.user-profile {
  padding: 20px;
  min-height: calc(100vh - 120px);
}

.profile-container {
  max-width: 1200px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: 1fr 1fr;
  grid-template-rows: auto auto;
  gap: 25px;
}

.profile-card {
  grid-column: 1 / -1;
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

/* 用户信息样式 */
.user-info {
  display: flex;
  gap: 30px;
  align-items: center;
}

.avatar-section {
  text-align: center;
  flex-shrink: 0;
}

.avatar {
  width: 100px;
  height: 100px;
  background: linear-gradient(45deg, #00f5ff, #0080ff);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 15px;
  box-shadow: 0 10px 30px rgba(0, 245, 255, 0.3);
}

.avatar .el-icon {
  font-size: 48px;
  color: #000;
}

.avatar-section h3 {
  color: #00f5ff;
  margin: 0 0 8px 0;
  font-size: 24px;
  font-weight: bold;
}

.user-type {
  color: #888;
  margin: 0;
  font-size: 14px;
}

.info-details {
  flex: 1;
}

.info-item {
  display: flex;
  justify-content: space-between;
  padding: 12px 0;
  border-bottom: 1px solid rgba(0, 245, 255, 0.1);
  color: #ffffff;
}

.info-item:last-child {
  border-bottom: none;
}

.info-item .label {
  color: #888;
  font-weight: 500;
}

.info-item .value {
  color: #00f5ff;
  font-weight: bold;
}

/* 权限样式 */
.permissions-content {
  display: flex;
  flex-direction: column;
  gap: 25px;
}

.permission-item {
  padding: 20px;
  background: rgba(0, 245, 255, 0.05);
  border: 1px solid rgba(0, 245, 255, 0.2);
  border-radius: 12px;
  transition: all 0.3s ease;
}

.permission-item:hover {
  background: rgba(0, 245, 255, 0.08);
  border-color: rgba(0, 245, 255, 0.3);
}

.permission-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 15px;
  color: #00f5ff;
  font-weight: bold;
  font-size: 16px;
}

.permission-header .el-icon {
  font-size: 18px;
}

.usage-info {
  color: #ffffff;
}

.usage-bar {
  display: flex;
  align-items: center;
  gap: 15px;
}

.usage-bar .label {
  color: #888;
  font-size: 14px;
  min-width: 80px;
}

.usage-bar .value {
  color: #00f5ff;
  font-weight: bold;
  font-size: 14px;
  min-width: 80px;
  text-align: right;
}

:deep(.el-progress) {
  flex: 1;
}

:deep(.el-progress-bar__outer) {
  background-color: rgba(0, 0, 0, 0.3);
  border-radius: 10px;
}

.permission-status {
  display: flex;
  justify-content: center;
}

:deep(.el-tag) {
  padding: 8px 16px;
  font-size: 14px;
  border-radius: 20px;
}

/* 操作按钮样式 */
.actions-content {
  display: flex;
  gap: 20px;
  justify-content: center;
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

:deep(.el-button--danger) {
  background: rgba(255, 71, 87, 0.1);
  border-color: rgba(255, 71, 87, 0.3);
  color: #ff4757;
}

:deep(.el-button--danger:hover) {
  background: rgba(255, 71, 87, 0.2);
  border-color: #ff4757;
  box-shadow: 0 0 20px rgba(255, 71, 87, 0.3);
  transform: translateY(-2px);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .profile-container {
    grid-template-columns: 1fr;
    gap: 20px;
  }
  
  .user-info {
    flex-direction: column;
    gap: 20px;
    text-align: center;
  }
  
  .info-details {
    width: 100%;
  }
  
  .actions-content {
    flex-direction: column;
    gap: 15px;
  }
  
  .usage-bar {
    flex-direction: column;
    align-items: stretch;
    gap: 10px;
  }
  
  .usage-bar .value {
    text-align: center;
  }
}
</style>
