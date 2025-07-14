<template>
  <div class="app-card enhanced-table">
    <div class="table-header">
      <div class="table-title">
        <h3>{{ title }}</h3>
        <el-tag v-if="filterTag" size="small" type="success" effect="dark">
          {{ filterTag }}
        </el-tag>
      </div>
      <div class="table-actions">
        <slot name="actions"></slot>
      </div>
    </div>
    
    <el-table 
      :data="data" 
      class="app-table" 
      v-loading="loading"
      :max-height="maxHeight"
      :empty-text="emptyText"
      v-bind="$attrs"
    >
      <slot></slot>
    </el-table>
    
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
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue'

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
.enhanced-table {
  /* 继承 app-card 样式，添加特定样式 */
  padding: 20px;
  position: relative;
  z-index: 1;
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 0;
  border-bottom: 1px solid var(--border-color);
  margin-bottom: 15px;
}

.table-title {
  display: flex;
  align-items: center;
  gap: 15px;
}

.table-title h3 {
  color: var(--primary-color);
  font-size: 18px;
  font-weight: bold;
  margin: 0;
}

.table-actions {
  display: flex;
  gap: 10px;
}

.pagination-wrapper {
  padding: 25px 0;
  text-align: center;
  margin-top: 20px;
}

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
