<template>
  <div class="user-management">
    <!-- 用户统计卡片 -->
    <StatsGrid :stats="userStatsArray" />

    <!-- 操作工具栏 -->
    <el-card class="toolbar-card">
      <div class="toolbar">
        <div class="search-section">
          <el-input 
            v-model="searchQuery" 
            placeholder="搜索用户名..."
            @input="handleSearch"
            class="search-input"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </div>
        
        <div class="action-section">
          <el-button type="primary" @click="showCreateUserDialog">
            <el-icon><Plus /></el-icon>
            创建用户
          </el-button>
          <el-button @click="refreshUsers" :loading="loading">
            <el-icon><RefreshRight /></el-icon>
            刷新
          </el-button>
        </div>
      </div>
    </el-card>

    <!-- 用户列表 -->
    <el-card class="table-card">
      <el-table 
        :data="filteredUsers" 
        style="width: 100%" 
        v-loading="loading"
        :header-cell-style="{ background: 'rgba(0, 245, 255, 0.1)', color: '#00f5ff' }"
      >
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="username" label="用户名" min-width="80" />
        <el-table-column label="权限状态" width="120">
          <template #default="scope">
            <el-tag :type="scope.row.banned ? 'danger' : 'success'">
              {{ scope.row.banned ? '已封禁' : '正常' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="图片识别" width="130">
          <template #default="scope">
            <span class="limit-text">{{ formatLimit(scope.row.imagelimit) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="批量处理" width="130">
          <template #default="scope">
            <span class="limit-text">{{ formatLimit(scope.row.batchlimit) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="实时检测" width="130">
          <template #default="scope">
            <el-tag :type="scope.row.realtimePermission ? 'success' : 'info'" size="small">
              {{ scope.row.realtimePermission ? '开启' : '关闭' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="最后登录" min-width="100">
          <template #default="scope">
            <span class="time-text">{{ formatTime(scope.row.update_time) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="300" fixed="right">
          <template #default="scope">
            <el-button 
              type="primary" 
              size="small" 
              @click="editUser(scope.row)"
            >
              编辑
            </el-button>
            <el-button 
              :type="scope.row.banned ? 'success' : 'warning'" 
              size="small" 
              @click="toggleUserStatus(scope.row)"
            >
              {{ scope.row.banned ? '解封' : '封禁' }}
            </el-button>
            <el-button 
              type="danger" 
              size="small" 
              @click="deleteUser(scope.row)"
              :disabled="scope.row.username === 'admin'"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 创建/编辑用户对话框 -->
    <UserFormDialog
      v-model:visible="showFormDialog"
      :is-edit="isEditMode"
      :user-data="currentUserData"
      :loading="formLoading"
      @submit="handleFormSubmit"
    />
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, reactive, onMounted, computed, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  UserFilled, Check, Close, Search, Plus, RefreshRight 
} from '@element-plus/icons-vue'
import { SHA256 } from '../sha256.js'
import axiosInstance from '../axios'
import { useApi } from '../composables/useApi'
import UserFormDialog from '../components/UserFormDialog.vue'
import StatsGrid from '../components/StatsGrid.vue'

interface User {
  id: number
  username: string
  imagelimit: number
  batchlimit: number
  realtimePermission: boolean
  update_time: string
  banned?: boolean
}

export default defineComponent({
  name: 'AdminUserManagement',
  components: {
    UserFilled,
    Check,
    Close,
    Search,
    Plus,
    RefreshRight,
    UserFormDialog,
    StatsGrid
  },
  setup() {
    const apiHook = useApi()
    console.log('UserManagement useApi hook:', apiHook)
    const { request, loading } = apiHook
    console.log('UserManagement request function:', typeof request)
    console.log('UserManagement loading ref:', loading)
    
    const searchQuery = ref('')
    const users = ref<User[]>([])
    
    const showFormDialog = ref(false)
    const isEditMode = ref(false)
    const formLoading = ref(false)
    const currentUserData = ref<any>({})
    
    const userStats = reactive({
      total: 0,
      active: 0,
      banned: 0
    })

    // 用户统计数据
    const userStatsArray = computed(() => [
      {
        label: '总用户数',
        value: userStats.total,
        icon: UserFilled,
        iconType: 'primary',
        type: 'primary'
      },
      {
        label: '活跃用户',
        value: userStats.active,
        icon: Check,
        iconType: 'active',
        type: 'success'
      },
      {
        label: '封禁用户',
        value: userStats.banned,
        icon: Close,
        iconType: 'danger',
        type: 'danger'
      }
    ])

    const filteredUsers = computed(() => {
      if (!searchQuery.value) return users.value
      return users.value.filter(user => 
        user.username.toLowerCase().includes(searchQuery.value.toLowerCase())
      )
    })

    const getUsers = async () => {
      try {
        if (typeof request !== 'function') {
          console.error('request不是一个函数:', request)
          ElMessage.error('API请求函数未正确初始化')
          return
        }
        
        const response = await request('get', '/api/admin/users')
        
        if (response.success) {
          // 修正数据结构：后端返回的是data.users，使用数据库中的isbannd字段
          const usersData = response.data.users || []
          users.value = usersData.map(user => ({
            ...user,
            banned: user.isbannd === 1  // 使用数据库中的isbannd字段
          }))
          updateStats()
        }
      } catch (error: any) {
        console.error('获取用户列表失败:', error)
        ElMessage.error('获取用户列表失败')
      }
    }

    const updateStats = () => {
      userStats.total = users.value.length
      userStats.active = users.value.filter(u => !u.banned).length
      userStats.banned = users.value.filter(u => u.banned).length
    }

    const showCreateUserDialog = () => {
      isEditMode.value = false
      currentUserData.value = {
        username: '',
        password: '',
        imagelimit: 100,
        batchlimit: 10,
        realtimePermission: false
      }
      showFormDialog.value = true
    }

    const editUser = (user: User) => {
      isEditMode.value = true
      currentUserData.value = {
        id: user.id,
        username: user.username,
        password: '',
        imagelimit: user.imagelimit,
        batchlimit: user.batchlimit,
        realtimePermission: user.realtimePermission
      }
      showFormDialog.value = true
    }

    const handleFormSubmit = async (formData: any) => {
      try {
        formLoading.value = true
        
        if (isEditMode.value) {
          // 编辑用户
          const updateData: any = {
            imagelimit: formData.imagelimit,
            batchlimit: formData.batchlimit,
            realtimePermission: formData.realtimePermission ? 1 : 0
          }
          
          if (formData.password) {
            updateData.password = SHA256.hash(formData.password)
          }
          
          const response = await request('put', `/api/admin/user/${formData.id}`, updateData)
          
          if (response.success) {
            ElMessage.success('用户更新成功')
            showFormDialog.value = false
            getUsers()
          } else {
            ElMessage.error(response.message || '更新失败')
          }
        } else {
          // 创建用户
          const hashedPassword = SHA256.hash(formData.password)
          
          const response = await request('post', '/api/admin/user', {
            username: formData.username,
            password: hashedPassword,
            imagelimit: formData.imagelimit,
            batchlimit: formData.batchlimit,
            realtimePermission: formData.realtimePermission ? 1 : 0
          } as any)
          
          if (response.success) {
            ElMessage.success('用户创建成功')
            showFormDialog.value = false
            getUsers()
          } else {
            ElMessage.error(response.message || '创建失败')
          }
        }
      } catch (error: any) {
        console.error('操作用户失败:', error)
        ElMessage.error(isEditMode.value ? '更新用户失败' : '创建用户失败')
      } finally {
        formLoading.value = false
      }
    }

    const toggleUserStatus = async (user: User) => {
      try {
        const action = user.banned ? '解封' : '封禁'
        await ElMessageBox.confirm(`确定要${action}用户 ${user.username} 吗？`, `${action}确认`, {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        })
        
        const response = await request('put', `/api/admin/user/${user.id}/status`, {
          banned: !user.banned
        } as any)
        
        if (response.success) {
          ElMessage.success(`${action}成功`)
          getUsers()
        }
      } catch (error: any) {
        if (error !== 'cancel') {
          console.error('操作失败:', error)
          ElMessage.error('操作失败')
        }
      }
    }

    const deleteUser = async (user: User) => {
      try {
        await ElMessageBox.confirm(`确定要删除用户 ${user.username} 吗？此操作不可恢复！`, '删除确认', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'error'
        })
        
        const response = await request('delete', `/api/admin/user/${user.id}`)
        
        if (response.success) {
          ElMessage.success('删除成功')
          getUsers()
        }
      } catch (error: any) {
        if (error !== 'cancel') {
          console.error('删除失败:', error)
          ElMessage.error('删除失败')
        }
      }
    }

    const refreshUsers = () => {
      getUsers()
    }

    const handleSearch = () => {
      // 搜索在计算属性中处理
    }

    const formatTime = (time: string) => {
      if (!time) return '未知'
      return new Date(time).toLocaleString('zh-CN')
    }

    const formatLimit = (limit: number) => {
      return limit === -1 ? '无限制' : limit.toString()
    }

    onMounted(async () => {
      await nextTick()
      console.log('UserManagement mounted, 准备加载数据...')
      console.log('request function available:', typeof request)
      getUsers()
    })

    return {
      loading,
      searchQuery,
      users,
      filteredUsers,
      userStats,
      userStatsArray,
      showFormDialog,
      isEditMode,
      formLoading,
      currentUserData,
      getUsers,
      showCreateUserDialog,
      editUser,
      handleFormSubmit,
      toggleUserStatus,
      deleteUser,
      refreshUsers,
      handleSearch,
      formatTime,
      formatLimit
    }
  }
})
</script>

<style scoped>
/* 页面加载动画 */
.user-management {
  animation: fadeInUp 0.6s ease-out;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 用户统计 - 使用StatsGrid组件 */

/* 工具栏增强 */
.toolbar {
  background: rgba(0, 245, 255, 0.02);
  padding: 20px;
  border-radius: 12px;
}

.search-section {
  position: relative;
}

.search-input {
  position: relative;
}

.search-input :deep(.el-input__wrapper) {
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(0, 245, 255, 0.3);
  border-radius: 25px;
  transition: all 0.3s ease;
  overflow: hidden;
}

.search-input :deep(.el-input__wrapper::before) {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(0, 245, 255, 0.1), transparent);
  transition: left 0.6s ease;
}

.search-input :deep(.el-input__wrapper:hover::before) {
  left: 100%;
}

.search-input :deep(.el-input__wrapper:hover) {
  border-color: rgba(0, 245, 255, 0.5);
  box-shadow: 0 0 15px rgba(0, 245, 255, 0.2);
}

.search-input :deep(.el-input__wrapper.is-focus) {
  border-color: #00f5ff;
  box-shadow: 0 0 20px rgba(0, 245, 255, 0.3);
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

/* 表格卡片 */
.table-card {
  background: rgba(26, 26, 46, 0.8);
  border: 1px solid rgba(0, 245, 255, 0.3);
}

/* 表格美化 - 增强版本 */
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

/* 用户表格特殊样式 */
.limit-text {
  color: #00f5ff;
  font-weight: bold;
  font-size: 14px;
  padding: 6px 12px;
  background: rgba(0, 245, 255, 0.1);
  border-radius: 20px;
  border: 1px solid rgba(0, 245, 255, 0.3);
  display: inline-block;
  transition: all 0.3s ease;
}

.limit-text:hover {
  background: rgba(0, 245, 255, 0.2);
  transform: scale(1.05);
}

.time-text {
  color: rgba(255, 255, 255, 0.8);
  font-size: 12px;
  font-weight: 400;
  padding: 4px 8px;
  background: rgba(0, 245, 255, 0.05);
  border-radius: 6px;
  border: 1px solid rgba(0, 245, 255, 0.1);
}

/* 对话框样式 */
:deep(.el-dialog) {
  background: rgba(26, 26, 46, 0.95);
  border: 1px solid rgba(0, 245, 255, 0.3);
  border-radius: 15px;
  box-shadow: 0 20px 60px rgba(0, 245, 255, 0.2);
}

:deep(.el-dialog__header) {
  background: rgba(0, 245, 255, 0.1);
  border-bottom: 1px solid rgba(0, 245, 255, 0.3);
  padding: 20px;
  border-radius: 15px 15px 0 0;
}

:deep(.el-dialog__title) {
  color: #00f5ff;
  font-weight: bold;
  font-size: 18px;
}

:deep(.el-dialog__body) {
  padding: 25px;
  background: rgba(26, 26, 46, 0.8);
}

:deep(.el-dialog__footer) {
  background: rgba(26, 26, 46, 0.8);
  border-top: 1px solid rgba(0, 245, 255, 0.2);
  padding: 20px;
  border-radius: 0 0 15px 15px;
}

:deep(.el-form-item__label) {
  color: #ffffff !important;
  font-weight: 500;
}

:deep(.el-input__wrapper) {
  background: rgba(0, 0, 0, 0.4) !important;
  border: 1px solid rgba(0, 245, 255, 0.3) !important;
  border-radius: 8px;
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.2);
}

:deep(.el-input__wrapper:hover) {
  border-color: rgba(0, 245, 255, 0.5) !important;
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.2), 0 0 8px rgba(0, 245, 255, 0.2);
}

:deep(.el-input__wrapper.is-focus) {
  border-color: #00f5ff !important;
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.2), 0 0 12px rgba(0, 245, 255, 0.3);
}

:deep(.el-input__inner) {
  color: #ffffff !important;
  background: transparent !important;
}

:deep(.el-input__inner::placeholder) {
  color: rgba(255, 255, 255, 0.5) !important;
}

:deep(.el-input-number) {
  width: 100%;
}

:deep(.el-input-number .el-input__wrapper) {
  background: rgba(0, 0, 0, 0.4) !important;
  border: 1px solid rgba(0, 245, 255, 0.3) !important;
}

:deep(.el-input-number__decrease),
:deep(.el-input-number__increase) {
  background: rgba(0, 245, 255, 0.1);
  border-color: rgba(0, 245, 255, 0.3);
  color: #00f5ff;
}

:deep(.el-input-number__decrease:hover),
:deep(.el-input-number__increase:hover) {
  background: rgba(0, 245, 255, 0.2);
  color: #ffffff;
}

:deep(.el-switch.is-checked .el-switch__core) {
  background-color: #00f5ff;
}

:deep(.el-switch .el-switch__core) {
  background-color: rgba(255, 255, 255, 0.2);
  border-color: rgba(0, 245, 255, 0.3);
}

/* 表单项间距优化 */
:deep(.el-form-item) {
  margin-bottom: 20px;
}

:deep(.el-form-item small) {
  color: rgba(255, 255, 255, 0.6) !important;
  font-size: 12px;
  margin-left: 8px;
}

/* 按钮样式 */
:deep(.el-button--primary) {
  background: linear-gradient(45deg, #00f5ff, #0080ff);
  border: none;
  color: #000;
}

:deep(.el-button--primary:hover) {
  background: linear-gradient(45deg, #0080ff, #00f5ff);
  box-shadow: 0 0 15px rgba(0, 245, 255, 0.4);
}

/* 标签美化 */
:deep(.el-tag) {
  border-radius: 20px;
  padding: 6px 14px;
  font-weight: 500;
  border-width: 1px;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

:deep(.el-tag:hover) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

:deep(.el-tag--success) {
  background: linear-gradient(45deg, rgba(103, 194, 58, 0.2), rgba(133, 206, 97, 0.1));
  border-color: rgba(103, 194, 58, 0.5);
  color: #67c23a;
}

:deep(.el-tag--danger) {
  background: linear-gradient(45deg, rgba(245, 108, 108, 0.2), rgba(247, 137, 137, 0.1));
  border-color: rgba(245, 108, 108, 0.5);
  color: #f56c6c;
}

:deep(.el-tag--info) {
  background: linear-gradient(45deg, rgba(144, 147, 153, 0.2), rgba(176, 179, 184, 0.1));
  border-color: rgba(144, 147, 153, 0.5);
  color: #909399;
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

/* 响应式设计 */
@media (max-width: 768px) {
  .toolbar {
    flex-direction: column;
    align-items: stretch;
  }
  
  .action-section {
    justify-content: center;
  }
  
  .search-section {
    max-width: none;
  }
}
</style>
