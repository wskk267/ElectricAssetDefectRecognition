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
        
        <button class="btn-danger btn-sm logout-btn" @click="logout">
          <el-icon><SwitchButton /></el-icon>
          退出
        </button>
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
import { debounce } from '../utils/common.js'
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

    const switchTab = debounce((tab: string) => {
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
    }, 300)

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
/* 简化的样式，使用共享的CSS变量和类 */
.app-container {
  min-height: 100vh;
  display: flex;
  background: var(--bg-primary);
  color: var(--text-primary);
  font-family: var(--font-family);
  animation: fadeIn 0.8s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.sidebar {
  width: 250px;
  background: var(--bg-secondary);
  backdrop-filter: blur(15px);
  border-right: 1px solid var(--border-color);
  position: fixed;
  left: 0;
  top: 0;
  height: 100vh;
  z-index: 1000;
  overflow-y: auto;
  scrollbar-width: thin;
  scrollbar-color: var(--border-color) transparent;
  transition: all 0.3s ease;
}

.sidebar::-webkit-scrollbar {
  width: 6px;
}

.sidebar::-webkit-scrollbar-track {
  background: transparent;
}

.sidebar::-webkit-scrollbar-thumb {
  background: var(--border-color);
  border-radius: 3px;
}

.sidebar-header {
  padding: 30px 25px;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  gap: 15px;
}

.logo-icon {
  font-size: 36px;
  color: var(--primary-color);
  animation: glow 2s ease-in-out infinite alternate;
}

@keyframes glow {
  from { text-shadow: 0 0 10px var(--primary-color); }
  to { text-shadow: 0 0 20px var(--primary-color); }
}

.logo-text h3 {
  margin: 0;
  color: var(--primary-color);
  font-size: 18px;
  font-weight: bold;
}

.logo-text p {
  margin: 5px 0 0 0;
  color: var(--text-secondary);
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
  padding: 15px 20px;
  margin: 5px 10px 20px;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid transparent;
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
  background: rgba(0, 245, 255, 0.2);
  border-radius: 50%;
  transform: translate(-50%, -50%);
  transition: all 0.6s ease;
  z-index: 0;
}

.menu-item:active::before {
  width: 300%;
  height: 300%;
}

.menu-item:hover {
  background: rgba(0, 245, 255, 0.1);
  border-color: var(--primary-color);
  transform: translateX(5px);
  box-shadow: 0 5px 15px rgba(0, 245, 255, 0.2);
}

.menu-item.active {
  background: linear-gradient(45deg, var(--primary-color), var(--primary-dark));
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
}

.sidebar-footer {
  padding: 20px 25px;
  border-top: 1px solid var(--border-color);
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
  border: 1px solid var(--border-color);
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
  background: linear-gradient(45deg, var(--primary-color), var(--primary-dark));
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(0, 245, 255, 0.3);
  transition: all 0.3s ease;
}

.admin-avatar:hover {
  transform: scale(1.1) rotate(5deg);
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
  color: var(--primary-color);
  font-weight: bold;
  font-size: 14px;
}

.admin-role {
  color: var(--text-secondary);
  font-size: 12px;
}

.logout-btn {
  width: 100%;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.logout-btn:hover {
  transform: translateY(-2px);
}

.main-content {
  flex: 1;
  margin-left: 250px;
  height: 100vh;
  overflow-y: auto;
  background: transparent;
  transition: margin-left 0.3s ease;
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

.content-header {
  padding: 30px 40px 20px;
  background: var(--bg-secondary);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid var(--border-color);
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
  position: relative;
  overflow: hidden;
}

.content-header::before {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 2px;
  background: linear-gradient(90deg, var(--primary-color), var(--primary-dark), var(--primary-color));
  background-size: 200% 100%;
  animation: borderFlow 3s ease-in-out infinite;
}

@keyframes borderFlow {
  0%, 100% { background-position: 0% 0%; }
  50% { background-position: 100% 0%; }
}

.content-header h2 {
  margin: 0 0 10px 0;
  color: var(--primary-color);
  font-size: 28px;
  font-weight: bold;
  text-shadow: 0 0 10px rgba(0, 245, 255, 0.5);
}

.breadcrumb {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--text-secondary);
  font-size: 14px;
}

.breadcrumb .el-icon {
  font-size: 12px;
}

.breadcrumb span:last-child {
  color: var(--primary-color);
}

.content-body {
  flex: 1;
  padding: 24px;
  overflow: visible;
  min-height: 0;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .app-container {
    flex-direction: column;
  }
  
  .sidebar {
    width: 100%;
    height: auto;
    position: relative;
  }
  
  .main-content {
    margin-left: 0;
    height: auto;
  }
  
  .sidebar-header {
    padding: 20px;
  }
  
  .menu-item {
    margin: 3px 10px;
    padding: 12px 20px;
  }
  
  .content-header {
    padding: 20px;
  }
  
  .content-header h2 {
    font-size: 24px;
  }
}
</style>
