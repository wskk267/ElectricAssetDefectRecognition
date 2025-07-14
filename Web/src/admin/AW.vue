<template>
  <div class="app-container">
    <!-- 左侧导航栏 -->
    <div class="sidebar">
      <div class="sidebar-header">
        <el-icon class="logo-icon"><Key /></el-icon>
        <div class="logo-text">
          <h3>管理员控制台</h3>
          <p>Admin Console</p>
        </div>
      </div>
      
      <div class="sidebar-menu">
        <div 
          class="menu-item" 
          :class="{ active: activeTab === 'users' }" 
          @click="switchTab('users')"
        >
          <el-icon><UserFilled /></el-icon>
          <span>管理用户</span>
        </div>
        
        <div 
          class="menu-item" 
          :class="{ active: activeTab === 'logs' }" 
          @click="switchTab('logs')"
        >
          <el-icon><Document /></el-icon>
          <span>查看日志</span>
        </div>
        
        <div 
          class="menu-item" 
          :class="{ active: activeTab === 'analytics' }" 
          @click="switchTab('analytics')"
        >
          <el-icon><DataAnalysis /></el-icon>
          <span>数据分析</span>
        </div>
      </div>
      
      <div class="sidebar-footer">
        <div class="admin-info">
          <div class="admin-avatar">
            <el-icon><UserFilled /></el-icon>
          </div>
          <div class="admin-details">
            <span class="admin-name">{{ adminName }}</span>
            <span class="admin-role">系统管理员</span>
          </div>
        </div>
        
        <el-button type="danger" size="small" @click="logout" class="logout-btn">
          <el-icon><SwitchButton /></el-icon>
          退出
        </el-button>
      </div>
    </div>

    <!-- 主要内容区域 -->
    <div class="main-content">
      <div class="content-header">
        <h2>{{ getPageTitle() }}</h2>
        <div class="breadcrumb">
          <span>管理员控制台</span>
          <el-icon><ArrowRight /></el-icon>
          <span>{{ getPageTitle() }}</span>
        </div>
      </div>
      
      <div class="content-body">
        <router-view />
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, watch, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessageBox, ElMessage } from 'element-plus'
import { 
  Key, UserFilled, Document, DataAnalysis, 
  SwitchButton, ArrowRight 
} from '@element-plus/icons-vue'
import '../style.css'
import './admin-theme.css'

export default defineComponent({
  name: 'AW',
  components: {
    Key,
    UserFilled,
    Document,
    DataAnalysis,
    SwitchButton,
    ArrowRight
  },
  setup() {
    const router = useRouter()
    const route = useRoute()
    const activeTab = ref('users')
    const adminName = ref('')

    const updateActiveTab = () => {
      const path = route.path
      if (path.includes('user-management')) {
        activeTab.value = 'users'
      } else if (path.includes('logs')) {
        activeTab.value = 'logs'
      } else if (path.includes('analytics')) {
        activeTab.value = 'analytics'
      }
    }

    const switchTab = (tab: string) => {
      activeTab.value = tab
      switch (tab) {
        case 'users':
          router.push('/admin/user-management')
          break
        case 'logs':
          router.push('/admin/logs')
          break
        case 'analytics':
          router.push('/admin/analytics')
          break
      }
    }

    const getPageTitle = () => {
      switch (activeTab.value) {
        case 'users':
          return '管理用户'
        case 'logs':
          return '查看日志'
        case 'analytics':
          return '数据分析'
        default:
          return '管理用户'
      }
    }

    const logout = async () => {
      try {
        await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        })
        
        // 清除本地存储
        localStorage.removeItem('token')
        localStorage.removeItem('userType')
        localStorage.removeItem('userId')
        localStorage.removeItem('username')
        
        ElMessage.success('退出成功')
        router.push('/login')
      } catch {
        // 用户取消退出
      }
    }

    onMounted(() => {
      adminName.value = localStorage.getItem('username') || '管理员'
      updateActiveTab()
    })

    watch(() => route.path, updateActiveTab)

    return {
      activeTab,
      adminName,
      switchTab,
      getPageTitle,
      logout
    }
  }
})
</script>

<style scoped>
/* 页面加载动画 */
.app-container {
  animation: fadeIn 0.8s ease-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.main-content {
  animation: slideInRight 0.6s ease-out;
}

@keyframes slideInRight {
  from {
    opacity: 0;
    transform: translateX(30px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.app-container {
  min-height: 100vh;
  display: flex;
  background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 50%, #16213e 100%);
  color: #ffffff;
  font-family: 'Microsoft YaHei', sans-serif;
}

/* 左侧边栏 */
.sidebar {
  width: 250px;
  background: rgba(26, 26, 46, 0.9);
  backdrop-filter: blur(15px);
  border-right: 1px solid rgba(0, 245, 255, 0.3);
  position: fixed;
  left: 0;
  top: 0;
  height: 100vh;
  z-index: 1000;
  overflow-y: auto;
  scrollbar-width: thin;
  scrollbar-color: rgba(0, 245, 255, 0.3) transparent;
  transition: all 0.3s ease;
}

.sidebar::-webkit-scrollbar {
  width: 6px;
}

.sidebar::-webkit-scrollbar-track {
  background: transparent;
}

.sidebar::-webkit-scrollbar-thumb {
  background: rgba(0, 245, 255, 0.3);
  border-radius: 3px;
}

.sidebar::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 245, 255, 0.5);
}

.sidebar::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, 
    rgba(0, 245, 255, 0.1) 0%, 
    rgba(0, 128, 255, 0.05) 50%, 
    rgba(26, 26, 46, 0.1) 100%);
  z-index: -1;
}

.sidebar-header {
  padding: 30px 25px;
  border-bottom: 1px solid rgba(0, 245, 255, 0.3);
  display: flex;
  align-items: center;
  gap: 15px;
}

.logo-icon {
  font-size: 36px;
  color: #00f5ff;
  animation: glow 2s ease-in-out infinite alternate;
}

@keyframes glow {
  from {
    text-shadow: 0 0 5px #00f5ff, 0 0 10px #00f5ff, 0 0 15px #00f5ff;
  }
  to {
    text-shadow: 0 0 10px #00f5ff, 0 0 20px #00f5ff, 0 0 30px #00f5ff;
  }
}

.logo-text h3 {
  margin: 0;
  color: #00f5ff;
  font-size: 18px;
  font-weight: bold;
}

.logo-text p {
  margin: 5px 0 0 0;
  color: #888;
  font-size: 12px;
}

.sidebar-menu {
  flex: 1;
  padding: 20px 0;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 30px;
  margin: 30px 10px;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(0, 245, 255, 0.2);
  position: relative;
  overflow: hidden;
}

.menu-item::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 0;
  height: 0;
  background: rgba(0, 245, 255, 0.3);
  border-radius: 50%;
  transform: translate(-50%, -50%);
  transition: all 0.6s ease;
  z-index: 0;
}

.menu-item:active::before {
  width: 100%;
  height: 100%;
}

.menu-item:hover {
  background: rgba(0, 245, 255, 0.1);
  border-color: rgba(0, 245, 255, 0.4);
  transform: translateX(5px);
  box-shadow: 0 5px 15px rgba(0, 245, 255, 0.2);
}

.menu-item.active {
  background: linear-gradient(45deg, #00f5ff, #0080ff);
  color: #000;
  border-color: transparent;
  box-shadow: 0 5px 20px rgba(0, 245, 255, 0.4);
}

.menu-item .el-icon {
  font-size: 18px;
}

.menu-item span {
  font-size: 15px;
  font-weight: 500;
  position: relative;
  z-index: 1;
}

.sidebar-footer {
  padding: 20px 25px;
  border-top: 1px solid rgba(0, 245, 255, 0.3);
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.admin-info {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 15px;
  background: rgba(0, 245, 255, 0.05);
  border: 1px solid rgba(0, 245, 255, 0.2);
  border-radius: 12px;
  position: relative;
  overflow: hidden;
}

.admin-info::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(0, 245, 255, 0.1), transparent);
  transition: left 0.8s ease;
}

.admin-info:hover::before {
  left: 100%;
}

.admin-avatar {
  width: 40px;
  height: 40px;
  background: linear-gradient(45deg, #00f5ff, #0080ff);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(0, 245, 255, 0.3);
}

.admin-avatar .el-icon {
  font-size: 20px;
  color: #000;
}

.admin-details {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.admin-name {
  color: #00f5ff;
  font-weight: bold;
  font-size: 14px;
}

.admin-role {
  color: #888;
  font-size: 12px;
}

.logout-btn {
  width: 100%;
  border-radius: 10px;
  background: rgba(255, 71, 87, 0.1);
  border-color: rgba(255, 71, 87, 0.3);
  color: #ff4757;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.logout-btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transition: left 0.5s ease;
}

.logout-btn:hover::before {
  left: 100%;
}

.logout-btn:hover {
  background: rgba(255, 71, 87, 0.2);
  border-color: #ff4757;
  box-shadow: 0 0 15px rgba(255, 71, 87, 0.3);
  transform: translateY(-2px);
}

/* 主内容区域 */
.main-content {
  flex: 1;
  margin-left: 250px;
  height: 100vh;
  overflow-y: auto;
  overflow-x: hidden;
  background: transparent;
  transition: margin-left 0.3s ease;
}

.content-header {
  padding: 30px 40px 20px;
  background: rgba(26, 26, 46, 0.8);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(0, 245, 255, 0.3);
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
  position: relative;
  overflow: hidden;
  flex-shrink: 0;
}

.content-header::before {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 2px;
  background: linear-gradient(90deg, #00f5ff, #0080ff, #00f5ff);
  background-size: 200% 100%;
  animation: borderFlow 3s ease-in-out infinite;
}

@keyframes borderFlow {
  0%, 100% { background-position: 0% 0%; }
  50% { background-position: 100% 0%; }
}

.content-header h2 {
  margin: 0 0 10px 0;
  color: #00f5ff;
  font-size: 28px;
  font-weight: bold;
  text-shadow: 0 0 10px rgba(0, 245, 255, 0.5);
}

.breadcrumb {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #888;
  font-size: 14px;
}

.breadcrumb .el-icon {
  font-size: 12px;
}

.breadcrumb span:last-child {
  color: #00f5ff;
}

.breadcrumb span {
  transition: all 0.3s ease;
}

.breadcrumb span:hover {
  color: #00f5ff;
  text-shadow: 0 0 5px rgba(0, 245, 255, 0.5);
}

.content-body {
  flex: 1;
  padding: 0;
  overflow: visible;
  min-height: 0;
}

/* 滚动条美化 */
.content-body::-webkit-scrollbar {
  width: 8px;
}

.content-body::-webkit-scrollbar-track {
  background: rgba(0, 245, 255, 0.1);
  border-radius: 4px;
}

.content-body::-webkit-scrollbar-thumb {
  background: rgba(0, 245, 255, 0.3);
  border-radius: 4px;
  transition: background 0.3s ease;
}

.content-body::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 245, 255, 0.5);
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .sidebar {
    width: 250px;
  }
  
  .main-content {
    margin-left: 250px;
  }
  
  .content-header {
    padding: 25px 30px 15px;
  }
  
  .content-body {
    padding: 25px 30px;
  }
}

@media (max-width: 768px) {
  .app-container {
    flex-direction: column;
  }
  
  .sidebar {
    width: 100%;
    height: auto;
    border-right: none;
    border-bottom: 2px solid #00f5ff;
    flex-shrink: 0;
    position: relative;
  }
  
  .main-content {
    flex: 1;
    min-height: 0;
    margin-left: 0;
    height: auto;
  }
  
  .sidebar-header {
    padding: 20px;
  }
  
  .sidebar-menu {
    padding: 15px 0;
  }
  
  .menu-item {
    margin: 3px 10px;
    padding: 12px 20px;
  }
  
  .content-header {
    padding: 20px;
  }
  
  .content-body {
    padding: 20px;
  }
  
  .content-header h2 {
    font-size: 24px;
  }
}
</style>
