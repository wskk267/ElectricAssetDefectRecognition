<template>
  <el-card class="table-card">
    <template #header>
      <div class="table-header">
        <div class="table-title">
          <h3>{{ title }}</h3>
          <el-tag 
            v-if="filterTag" 
            size="small" 
            type="success" 
            effect="dark"
            class="filter-tag"
          >
            {{ filterTag }}
          </el-tag>
        </div>
        <div class="table-actions">
          <slot name="actions"></slot>
        </div>
      </div>
    </template>
    
    <el-table 
      :data="data" 
      style="width: 100%" 
      v-loading="loading"
      :header-cell-style="{ 
        background: 'rgba(0, 245, 255, 0.1)', 
        color: '#00f5ff',
        fontWeight: 'bold',
        textAlign: 'center'
      }"
      :max-height="maxHeight"
      :empty-text="emptyText"
      v-bind="$attrs"
    >
      <slot></slot>
    </el-table>
    
    <!-- 分页 -->
    <div v-if="showPagination" class="pagination-wrapper">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="pageSizes"
        layout="total, sizes, prev, pager, next, jumper"
        :total="total"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>
  </el-card>
</template>

<script lang="ts">
import { defineComponent, ref, watch } from 'vue'

export default defineComponent({
  name: 'EnhancedTable',
  props: {
    title: {
      type: String,
      required: true
    },
    data: {
      type: Array,
      default: () => []
    },
    loading: {
      type: Boolean,
      default: false
    },
    filterTag: {
      type: String,
      default: ''
    },
    maxHeight: {
      type: [String, Number],
      default: 600
    },
    emptyText: {
      type: String,
      default: '暂无数据'
    },
    showPagination: {
      type: Boolean,
      default: true
    },
    total: {
      type: Number,
      default: 0
    },
    currentPage: {
      type: Number,
      default: 1
    },
    pageSize: {
      type: Number,
      default: 20
    },
    pageSizes: {
      type: Array,
      default: () => [20, 50, 100, 200]
    }
  },
  emits: ['update:currentPage', 'update:pageSize', 'size-change', 'current-change'],
  setup(props, { emit }) {
    const handleSizeChange = (newSize: number) => {
      emit('update:pageSize', newSize)
      emit('size-change', newSize)
    }

    const handleCurrentChange = (newPage: number) => {
      emit('update:currentPage', newPage)
      emit('current-change', newPage)
    }

    return {
      handleSizeChange,
      handleCurrentChange
    }
  }
})
</script>

<style scoped>
.table-card {
  background: rgba(26, 26, 46, 0.8);
  border: 1px solid rgba(0, 245, 255, 0.3);
  transition: all 0.3s ease;
}

.table-card:hover {
  border-color: rgba(0, 245, 255, 0.5);
  box-shadow: 0 8px 25px rgba(0, 245, 255, 0.15);
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: rgba(0, 245, 255, 0.02);
  padding: 15px;
  border-radius: 8px;
  margin-bottom: 15px;
}

.table-title {
  display: flex;
  align-items: center;
  gap: 15px;
}

.table-title h3 {
  color: #00f5ff;
  font-size: 18px;
  font-weight: bold;
  margin: 0;
  text-shadow: 0 0 10px rgba(0, 245, 255, 0.3);
}

.filter-tag {
  background: linear-gradient(45deg, rgba(103, 194, 58, 0.2), rgba(133, 206, 97, 0.1));
  border-color: rgba(103, 194, 58, 0.5);
  color: #67c23a;
  font-weight: 500;
  padding: 4px 12px;
  border-radius: 20px;
}

.table-actions {
  display: flex;
  gap: 10px;
}

.pagination-wrapper {
  padding: 25px 0;
  text-align: center;
  background: rgba(0, 245, 255, 0.02);
  border-radius: 12px;
  margin-top: 20px;
}

/* 表格美化 */
:deep(.el-table) {
  background: transparent;
  color: #ffffff;
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid rgba(0, 245, 255, 0.2);
}

:deep(.el-table .el-table__header-wrapper) {
  background: linear-gradient(135deg, rgba(0, 245, 255, 0.15), rgba(0, 128, 255, 0.1));
  border-bottom: 2px solid rgba(0, 245, 255, 0.3);
}

:deep(.el-table th) {
  background: transparent !important;
  color: #00f5ff !important;
  font-weight: bold;
  text-align: center;
  padding: 15px 10px;
  border-bottom: 1px solid rgba(0, 245, 255, 0.3);
}

:deep(.el-table td) {
  border-bottom: 1px solid rgba(0, 245, 255, 0.1);
  padding: 12px 10px;
  background: transparent;
  transition: all 0.3s ease;
  text-align: center;
}

:deep(.el-table tr) {
  transition: all 0.3s ease;
}

:deep(.el-table tr:hover > td) {
  background-color: rgba(0, 245, 255, 0.08) !important;
  transform: translateX(2px);
  box-shadow: inset 3px 0 0 rgba(0, 245, 255, 0.5);
}

:deep(.el-table tr:nth-child(even)) {
  background-color: rgba(0, 245, 255, 0.02);
}

:deep(.el-table tr:nth-child(odd)) {
  background-color: rgba(0, 245, 255, 0.05);
}

/* 空状态美化 */
:deep(.el-table__empty-block) {
  background: rgba(0, 245, 255, 0.05);
  border-radius: 12px;
  margin: 20px;
  padding: 40px 20px;
}

:deep(.el-table__empty-text) {
  color: rgba(255, 255, 255, 0.6);
  font-size: 16px;
}

/* 加载状态优化 */
:deep(.el-loading-mask) {
  background-color: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(5px);
}

:deep(.el-loading-spinner) {
  font-size: 36px;
}

:deep(.el-loading-spinner .circular) {
  width: 50px;
  height: 50px;
  color: #00f5ff;
}

/* 分页样式 */
:deep(.el-pagination) {
  --el-pagination-bg-color: rgba(0, 245, 255, 0.1);
  --el-pagination-text-color: #ffffff;
  --el-pagination-border-radius: 8px;
}

:deep(.el-pagination .el-select .el-input) {
  --el-input-bg-color: rgba(0, 245, 255, 0.1);
  --el-input-border-color: rgba(0, 245, 255, 0.3);
  --el-input-text-color: #ffffff;
}

:deep(.el-pagination .btn-prev),
:deep(.el-pagination .btn-next),
:deep(.el-pagination .el-pager li) {
  background: rgba(0, 245, 255, 0.1);
  border: 1px solid rgba(0, 245, 255, 0.3);
  color: #ffffff;
  margin: 0 2px;
  border-radius: 6px;
  transition: all 0.3s ease;
}

:deep(.el-pagination .btn-prev:hover),
:deep(.el-pagination .btn-next:hover),
:deep(.el-pagination .el-pager li:hover) {
  background: rgba(0, 245, 255, 0.2);
  border-color: rgba(0, 245, 255, 0.5);
  color: #00f5ff;
}

:deep(.el-pagination .el-pager li.is-active) {
  background: linear-gradient(45deg, #00f5ff, #0080ff);
  border-color: #00f5ff;
  color: #000;
  font-weight: bold;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .table-header {
    flex-direction: column;
    gap: 15px;
    align-items: stretch;
  }
  
  .table-title {
    flex-direction: column;
    align-items: center;
    gap: 10px;
  }
  
  .table-actions {
    justify-content: center;
  }
}
</style>
