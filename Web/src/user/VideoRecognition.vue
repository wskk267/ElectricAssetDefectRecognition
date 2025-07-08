<template>
  <div class="video-recognition">
    <div class="coming-soon">
      <el-icon><VideoCamera /></el-icon>
      <h3>视频识别功能</h3>
      <p>敬请期待...</p>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue'
import { VideoCamera } from '@element-plus/icons-vue'

export default defineComponent({
  name: 'VideoRecognition',
  components: {
    VideoCamera
  }
})
</script>

<style scoped>
.video-recognition {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
  min-height: 400px;
}

.coming-soon {
  text-align: center;
  color: #666;
}

.coming-soon .el-icon {
  font-size: 80px;
  margin-bottom: 20px;
  color: #00f5ff;
}

.coming-soon h3 {
  font-size: 24px;
  margin-bottom: 10px;
  color: #ffffff;
}

.coming-soon p {
  font-size: 16px;
}
</style>
