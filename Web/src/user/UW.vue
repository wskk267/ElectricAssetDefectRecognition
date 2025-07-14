<template>
  <div class="app-container">
    <div class="navbar">
      <div class="nav-title">
        <el-icon><Setting /></el-icon>
        电力资产缺陷识别系统
      </div>
      <div class="nav-menu">
        <div 
          class="nav-item" 
          :class="{ active: activeTab === 'image' }" 
          @click="switchTab('image')"
        >
          <el-icon><Picture /></el-icon>
          图片识别
        </div>
        <div 
          class="nav-item" 
          :class="{ active: activeTab === 'batch' }" 
          @click="switchTab('batch')"
        >
          <el-icon><FolderOpened /></el-icon>
          批量处理
        </div>
        <div 
          class="nav-item" 
          :class="{ active: activeTab === 'realtime' }" 
          @click="switchTab('realtime')"
        >
          <el-icon><Monitor /></el-icon>
          实时检测
        </div>
        <div 
          class="nav-item" 
          :class="{ active: activeTab === 'profile' }" 
          @click="switchTab('profile')"
        >
          <el-icon><User /></el-icon>
          个人中心
        </div>
      </div>
      <div class="user-info">
        <span class="username">{{ username }}</span>
        <button class="btn-danger btn-sm" @click="logout">
          <el-icon><SwitchButton /></el-icon>
          退出
        </button>
      </div>
    </div>

    <!-- 主要内容区域 -->
    <div class="main-content">
      <router-view />
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, watch, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessageBox, ElMessage } from 'element-plus'
import { Picture, FolderOpened, User, Setting, Monitor, SwitchButton } from '@element-plus/icons-vue'
import { debounce } from '../utils/common.js'
import '../style.css'

export default defineComponent({
  name: 'UW',
  components: {
    Picture,
    FolderOpened,
    User,
    Setting,
    Monitor,
    SwitchButton
  },
  setup() {
    const router = useRouter()
    const route = useRoute()
    const activeTab = ref('image')
    const username = ref('')

    const updateActiveTab = () => {
      const path = route.path
      if (path.includes('image-recognition')) {
        activeTab.value = 'image'
      } else if (path.includes('batch-processing')) {
        activeTab.value = 'batch'
      } else if (path.includes('realtime-detection')) {
        activeTab.value = 'realtime'
      } else if (path.includes('profile')) {
        activeTab.value = 'profile'
      }
    }

    const switchTab = debounce((tab: string) => {
      activeTab.value = tab
      switch (tab) {
        case 'image':
          router.push('/user/image-recognition')
          break
        case 'batch':
          router.push('/user/batch-processing')
          break
        case 'realtime':
          router.push('/user/realtime-detection')
          break
        case 'profile':
          router.push('/user/profile')
          break
      }
    }, 300)

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
        localStorage.removeItem('userPermissions')
        
        ElMessage.success('退出成功')
        router.push('/login')
      } catch {
        // 用户取消退出
      }
    }

    onMounted(() => {
      username.value = localStorage.getItem('username') || '用户'
      updateActiveTab()
    })

    watch(() => route.path, updateActiveTab)

    return {
      activeTab,
      username,
      switchTab,
      logout
    }
  }
})
</script>

<style scoped>
/* 简化的样式，使用共享的CSS变量 */
.app-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--bg-primary);
  color: var(--text-primary);
  font-family: var(--font-family);
}

.navbar {
  position: fixed;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 30px;
  height: 70px;
  right: 0;
  left: 0;
  z-index: 1000;
  background: var(--bg-secondary);
  backdrop-filter: blur(10px);
  border-bottom: 2px solid var(--primary-color);
  box-shadow: var(--shadow-primary);
}

.nav-title {
  font-size: 24px;
  font-weight: bold;
  color: var(--primary-color);
  display: flex;
  align-items: center;
  gap: 10px;
}

.nav-title .el-icon {
  font-size: 28px;
}

.nav-menu {
  display: flex;
  gap: 20px;
  justify-content: center;
  flex: 1;
}

.nav-item {
  padding: 10px 20px;
  border-radius: 25px;
  cursor: pointer;
  transition: all 0.3s ease;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
}

.nav-item:hover {
  background: rgba(0, 245, 255, 0.1);
  border-color: var(--primary-color);
  transform: translateY(-2px);
}

.nav-item.active {
  background: var(--primary-color);
  color: #000;
  border-color: transparent;
}

.nav-item .el-icon {
  font-size: 16px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 15px;
}

.username {
  color: var(--primary-color);
  font-weight: bold;
  padding: 8px 12px;
  background: rgba(0, 245, 255, 0.1);
  border-radius: 20px;
  border: 1px solid var(--border-color);
}

.main-content {
  flex: 1;
  margin-top: 70px;
  padding: 30px;
  padding-bottom: 0;
  overflow: auto;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .nav-menu {
    gap: 15px;
  }
  
  .nav-item {
    padding: 8px 16px;
    font-size: 13px;
  }
  
  .nav-title {
    font-size: 20px;
  }
}

@media (max-width: 968px) {
  .navbar {
    flex-direction: column;
    height: auto;
    padding: 15px;
  }
  
  .nav-menu {
    margin-top: 15px;
    flex-wrap: wrap;
    justify-content: center;
  }
  
  .user-info {
    margin-top: 15px;
  }
  
  .main-content {
    margin-top: 120px;
    padding: 15px;
  }
  
  .nav-item {
    padding: 8px 16px;
    font-size: 14px;
  }
}
</style>
