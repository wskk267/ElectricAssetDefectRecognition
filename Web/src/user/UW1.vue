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
          :class="{ active: activeTab === 'video' }" 
          @click="switchTab('video')"
        >
          <el-icon><VideoCamera /></el-icon>
          视频识别
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
    </div>

    <!-- 主要内容区域 -->
    <div class="main-content">
      <router-view />
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { Picture, VideoCamera, User, Setting } from '@element-plus/icons-vue'
import '../style.css'

export default defineComponent({
  name: 'UW1',
  components: {
    Picture,
    VideoCamera,
    User,
    Setting
  },
  setup() {
    const router = useRouter()
    const route = useRoute()
    const activeTab = ref('image')

    const updateActiveTab = () => {
      const path = route.path
      if (path.includes('image-recognition')) {
        activeTab.value = 'image'
      } else if (path.includes('video-recognition')) {
        activeTab.value = 'video'
      } else if (path.includes('user-profile')) {
        activeTab.value = 'profile'
      }
    }

    watch(() => route.path, updateActiveTab, { immediate: true })

    const switchTab = (tab: string) => {
      activeTab.value = tab
      switch (tab) {
        case 'image':
          router.push('/image-recognition')
          break
        case 'video':
          router.push('/video-recognition')
          break
        case 'profile':
          router.push('/user-profile')
          break
      }
    }

    return {
      activeTab,
      switchTab
    }
  }
})
</script>

<style scoped>
.app-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 50%, #16213e 100%);
  color: #ffffff;
  font-family: 'Microsoft YaHei', sans-serif;
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
  background: rgba(26, 26, 46, 0.9);
  backdrop-filter: blur(10px);
  border-bottom: 2px solid #00f5ff;
  box-shadow: 0 4px 20px rgba(0, 245, 255, 0.3);
}

.nav-title {
  font-size: 24px;
  font-weight: bold;
  color: #00f5ff;
  text-shadow: 0 0 10px rgba(0, 245, 255, 0.5);
  display: flex;
  align-items: center;
  gap: 10px;
}

.nav-title .el-icon {
  font-size: 28px;
}

.nav-menu {
  display: flex;
  gap: 30px;
  justify-content: flex-end;
}

.nav-item {
  padding: 12px 24px;
  border-radius: 25px;
  cursor: pointer;
  transition: all 0.3s ease;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(0, 245, 255, 0.3);
  display: flex;
  align-items: center;
  gap: 8px;
}

.nav-item:hover {
  background: rgba(0, 245, 255, 0.1);
  box-shadow: 0 0 20px rgba(0, 245, 255, 0.4);
  transform: translateY(-2px);
}

.nav-item.active {
  background: linear-gradient(45deg, #00f5ff, #0080ff);
  color: #000;
  box-shadow: 0 0 25px rgba(0, 245, 255, 0.6);
}

.nav-item .el-icon {
  font-size: 18px;
}

/* 主内容区域 */
.main-content {
  flex: 1;
  padding:30px;
  overflow: auto; /* 如果内容超出，再显示滚动 */
}



@media (max-width: 768px) {
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
  
  .main-content {
    padding: 15px;
  }
  
  .nav-item {
    padding: 8px 16px;
    font-size: 14px;
  }
}
</style>
