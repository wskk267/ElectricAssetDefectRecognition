<template>
  <div class="stats-grid">
    <el-card 
      v-for="(stat, index) in stats" 
      :key="index" 
      class="stat-card"
      :class="stat.type"
    >
      <div class="stat-content">
        <div class="stat-icon" :class="stat.iconType">
          <el-icon v-if="stat.icon">
            <component :is="stat.icon" />
          </el-icon>
        </div>
        <div class="stat-info">
          <h3 class="stat-value" :class="stat.valueClass">{{ stat.value }}</h3>
          <p class="stat-label">{{ stat.label }}</p>
          <div v-if="stat.description" class="stat-description">
            {{ stat.description }}
          </div>
        </div>
      </div>
      <div v-if="stat.trend" class="stat-trend" :class="stat.trend.type">
        <el-icon>
          <component :is="stat.trend.icon" />
        </el-icon>
        <span>{{ stat.trend.value }}%</span>
      </div>
    </el-card>
  </div>
</template>

<script lang="ts">
import { defineComponent, PropType } from 'vue'
import { ArrowUp, ArrowDown, Minus } from '@element-plus/icons-vue'

interface StatTrend {
  type: 'increase' | 'decrease' | 'stable'
  value: number
  icon: any
}

interface StatItem {
  label: string
  value: string | number
  icon?: any
  iconType?: string
  type?: string
  valueClass?: string
  description?: string
  trend?: StatTrend
}

export default defineComponent({
  name: 'StatsGrid',
  components: {
    ArrowUp,
    ArrowDown,
    Minus
  },
  props: {
    stats: {
      type: Array as PropType<StatItem[]>,
      required: true,
      default: () => []
    },
    columns: {
      type: Number,
      default: 3
    }
  },
  setup(props) {
    return {}
  }
})
</script>

<style scoped>
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin-bottom: 25px;
}

.stat-card {
  background: rgba(26, 26, 46, 0.8);
  border: 1px solid rgba(0, 245, 255, 0.3);
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.stat-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(0, 245, 255, 0.1), transparent);
  transition: left 0.8s ease;
}

.stat-card:hover::before {
  left: 100%;
}

.stat-card:hover {
  border-color: rgba(0, 245, 255, 0.5);
  box-shadow: 0 8px 25px rgba(0, 245, 255, 0.2);
  transform: translateY(-2px);
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 20px;
  position: relative;
  z-index: 1;
}

.stat-icon {
  width: 60px;
  height: 60px;
  background: linear-gradient(45deg, #00f5ff, #0080ff);
  border-radius: 15px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 5px 15px rgba(0, 245, 255, 0.3);
  transition: all 0.3s ease;
}

.stat-icon.active {
  background: linear-gradient(45deg, #67c23a, #85ce61);
  box-shadow: 0 5px 15px rgba(103, 194, 58, 0.3);
}

.stat-icon.warning {
  background: linear-gradient(45deg, #e6a23c, #f4bd47);
  box-shadow: 0 5px 15px rgba(230, 162, 60, 0.3);
}

.stat-icon.danger {
  background: linear-gradient(45deg, #f56c6c, #f78989);
  box-shadow: 0 5px 15px rgba(245, 108, 108, 0.3);
}

.stat-icon.info {
  background: linear-gradient(45deg, #909399, #b0b3b8);
  box-shadow: 0 5px 15px rgba(144, 147, 153, 0.3);
}

.stat-icon .el-icon {
  font-size: 24px;
  color: #000;
  transition: all 0.3s ease;
}

.stat-card:hover .stat-icon {
  transform: scale(1.1) rotate(5deg);
}

.stat-info {
  flex: 1;
}

.stat-value {
  margin: 0 0 5px 0;
  color: #00f5ff;
  font-size: 28px;
  font-weight: bold;
  text-shadow: 0 0 10px rgba(0, 245, 255, 0.3);
  transition: all 0.3s ease;
}

.stat-value.success {
  color: #67c23a;
  text-shadow: 0 0 10px rgba(103, 194, 58, 0.3);
}

.stat-value.warning {
  color: #e6a23c;
  text-shadow: 0 0 10px rgba(230, 162, 60, 0.3);
}

.stat-value.danger {
  color: #f56c6c;
  text-shadow: 0 0 10px rgba(245, 108, 108, 0.3);
}

.stat-label {
  margin: 0;
  color: #888;
  font-size: 14px;
  font-weight: 500;
}

.stat-description {
  margin-top: 5px;
  color: rgba(255, 255, 255, 0.6);
  font-size: 12px;
}

.stat-trend {
  position: absolute;
  top: 10px;
  right: 10px;
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
  backdrop-filter: blur(5px);
}

.stat-trend.increase {
  background: rgba(103, 194, 58, 0.2);
  color: #67c23a;
  border: 1px solid rgba(103, 194, 58, 0.3);
}

.stat-trend.decrease {
  background: rgba(245, 108, 108, 0.2);
  color: #f56c6c;
  border: 1px solid rgba(245, 108, 108, 0.3);
}

.stat-trend.stable {
  background: rgba(144, 147, 153, 0.2);
  color: #909399;
  border: 1px solid rgba(144, 147, 153, 0.3);
}

.stat-trend .el-icon {
  font-size: 14px;
}

/* 特定类型的卡片样式 */
.stat-card.primary {
  border-image: linear-gradient(45deg, #00f5ff, #0080ff) 1;
}

.stat-card.success {
  border-image: linear-gradient(45deg, #67c23a, #85ce61) 1;
}

.stat-card.warning {
  border-image: linear-gradient(45deg, #e6a23c, #f4bd47) 1;
}

.stat-card.danger {
  border-image: linear-gradient(45deg, #f56c6c, #f78989) 1;
}

/* 动画效果 */
@keyframes statPulse {
  0% { transform: scale(1); }
  50% { transform: scale(1.05); }
  100% { transform: scale(1); }
}

.stat-card:hover .stat-value {
  animation: statPulse 0.5s ease-in-out;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .stat-content {
    gap: 15px;
  }
  
  .stat-icon {
    width: 50px;
    height: 50px;
  }
  
  .stat-icon .el-icon {
    font-size: 20px;
  }
  
  .stat-value {
    font-size: 24px;
  }
}
</style>
