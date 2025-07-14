<template>
  <div class="realtime-detection">
    <div class="app-card coming-soon">
      <el-icon class="monitor-icon"><Monitor /></el-icon>
      <h3>实时检测</h3>
      <p>功能开发中，敬请期待...</p>
      <div class="feature-preview">
        <div class="feature-item">
          <el-icon><VideoCamera /></el-icon>
          <span>摄像头实时监控</span>
        </div>
        <div class="feature-item">
          <el-icon><DataAnalysis /></el-icon>
          <span>实时缺陷分析</span>
        </div>
        <div class="feature-item">
          <el-icon><Bell /></el-icon>
          <span>预警通知系统</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue'
import { Monitor, VideoCamera, DataAnalysis, Bell } from '@element-plus/icons-vue'

export default defineComponent({
  name: 'RealtimeDetection',
  components: {
    Monitor,
    VideoCamera,
    DataAnalysis,
    Bell
  }
})
</script>

<style scoped>
.realtime-detection {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
  min-height: 500px;
  padding: 20px;
}

.coming-soon {
  text-align: center;
  color: #ffffff;
  padding: 40px;
  max-width: 600px;
}

.monitor-icon {
  font-size: 100px;
  margin-bottom: 20px;
  color: var(--primary-color);
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% { 
    transform: scale(1);
    opacity: 1;
  }
  50% { 
    transform: scale(1.05);
    opacity: 0.8;
  }
  100% { 
    transform: scale(1);
    opacity: 1;
  }
}

.coming-soon h3 {
  font-size: 28px;
  margin-bottom: 15px;
  color: var(--primary-color);
  text-shadow: 0 0 10px rgba(0, 245, 255, 0.5);
}

.coming-soon p {
  font-size: 18px;
  color: #888;
  margin-bottom: 30px;
}

.feature-preview {
  display: flex;
  gap: 30px;
  justify-content: center;
  flex-wrap: wrap;
}

.feature-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 20px;
  background: rgba(0, 245, 255, 0.05);
  border: 1px solid rgba(0, 245, 255, 0.2);
  border-radius: 15px;
  transition: all 0.3s ease;
  min-width: 120px;
}

.feature-item:hover {
  background: rgba(0, 245, 255, 0.1);
  border-color: var(--primary-color);
  transform: translateY(-5px);
  box-shadow: 0 10px 30px rgba(0, 245, 255, 0.2);
}

.feature-item .el-icon {
  font-size: 32px;
  color: var(--primary-color);
}

.feature-item span {
  font-size: 14px;
  color: #ffffff;
  text-align: center;
}

@media (max-width: 768px) {
  .feature-preview {
    gap: 15px;
  }
  
  .feature-item {
    min-width: 100px;
    padding: 15px;
  }
  
  .coming-soon {
    padding: 30px 20px;
  }
  
  .monitor-icon {
    font-size: 80px;
  }
  
  .coming-soon h3 {
    font-size: 24px;
  }
}
</style>
