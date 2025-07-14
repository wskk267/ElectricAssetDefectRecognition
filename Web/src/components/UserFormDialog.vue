<template>
  <el-dialog 
    :model-value="visible" 
    :title="isEdit ? '编辑用户' : '创建新用户'" 
    width="500px"
    @update:model-value="handleClose"
    :before-close="handleClose"
  >
    <el-form :model="formData" :rules="rules" ref="formRef">
      <el-form-item label="用户名" prop="username">
        <el-input 
          v-model="formData.username" 
          placeholder="请输入用户名" 
          :disabled="isEdit"
        />
      </el-form-item>
      <el-form-item :label="isEdit ? '新密码' : '密码'" prop="password">
        <el-input 
          v-model="formData.password" 
          type="password" 
          :placeholder="isEdit ? '留空则不修改密码' : '请输入密码'"
          show-password
        />
      </el-form-item>
      <el-form-item label="图片识别限额" prop="imagelimit">
        <el-input-number 
          v-model="formData.imagelimit" 
          :min="-1" 
          :max="10000"
          controls-position="right"
          style="width: 100%"
        />
        <small style="color: #888; font-size: 12px;">-1表示无限制</small>
      </el-form-item>
      <el-form-item label="批量处理限额" prop="batchlimit">
        <el-input-number 
          v-model="formData.batchlimit" 
          :min="-1" 
          :max="1000"
          controls-position="right"
          style="width: 100%"
        />
        <small style="color: #888; font-size: 12px;">-1表示无限制</small>
      </el-form-item>
      <el-form-item label="实时检测权限">
        <el-switch v-model="formData.realtimePermission" />
      </el-form-item>
    </el-form>
    
    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button type="primary" @click="handleSubmit" :loading="loading">
        {{ isEdit ? '保存' : '创建' }}
      </el-button>
    </template>
  </el-dialog>
</template>

<script lang="ts">
import { defineComponent, ref, reactive, watch, PropType } from 'vue'
import type { FormInstance, FormRules } from 'element-plus'

interface UserFormData {
  id?: number
  username: string
  password: string
  imagelimit: number
  batchlimit: number
  realtimePermission: boolean
}

export default defineComponent({
  name: 'UserFormDialog',
  props: {
    visible: {
      type: Boolean,
      default: false
    },
    isEdit: {
      type: Boolean,
      default: false
    },
    userData: {
      type: Object as PropType<UserFormData>,
      default: () => ({})
    },
    loading: {
      type: Boolean,
      default: false
    }
  },
  emits: ['update:visible', 'submit', 'close'],
  setup(props, { emit }) {
    const formRef = ref<FormInstance>()
    
    const defaultFormData: UserFormData = {
      username: '',
      password: '',
      imagelimit: 100,
      batchlimit: 10,
      realtimePermission: false
    }
    
    const formData = reactive<UserFormData>({ ...defaultFormData })
    
    const rules: FormRules = {
      username: [
        { required: true, message: '请输入用户名', trigger: 'blur' },
        { min: 3, max: 20, message: '用户名长度在 3 到 20 个字符', trigger: 'blur' }
      ],
      password: props.isEdit 
        ? [] 
        : [
            { required: true, message: '请输入密码', trigger: 'blur' },
            { min: 6, message: '密码长度至少 6 个字符', trigger: 'blur' }
          ],
      imagelimit: [
        { required: true, message: '请设置图片识别限额', trigger: 'blur' }
      ],
      batchlimit: [
        { required: true, message: '请设置批量处理限额', trigger: 'blur' }
      ]
    }
    
    // 监听用户数据变化
    watch(() => props.userData, (newData) => {
      if (newData && Object.keys(newData).length > 0) {
        Object.assign(formData, newData)
      }
    }, { immediate: true, deep: true })
    
    // 监听显示状态变化
    watch(() => props.visible, (visible) => {
      if (!visible) {
        resetForm()
      }
    })
    
    const resetForm = () => {
      Object.assign(formData, defaultFormData)
      formRef.value?.clearValidate()
    }
    
    const handleClose = () => {
      emit('update:visible', false)
      emit('close')
    }
    
    const handleSubmit = async () => {
      if (!formRef.value) return
      
      try {
        await formRef.value.validate()
        emit('submit', { ...formData })
      } catch (error) {
        console.error('表单验证失败:', error)
      }
    }
    
    return {
      formRef,
      formData,
      rules,
      handleClose,
      handleSubmit
    }
  }
})
</script>

<style scoped>
/* 对话框样式继承父组件的样式 */
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
  padding: 30px;
  background: rgba(26, 26, 46, 0.8);
}

:deep(.el-dialog__footer) {
  background: rgba(26, 26, 46, 0.8);
  border-top: 1px solid rgba(0, 245, 255, 0.2);
  padding: 25px 30px;
  border-radius: 0 0 15px 15px;
  text-align: right;
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

:deep(.el-form-item) {
  margin-bottom: 28px;
}

:deep(.el-form-item small) {
  color: rgba(255, 255, 255, 0.6) !important;
  font-size: 12px;
  margin-left: 8px;
}

:deep(.el-button--primary) {
  background: linear-gradient(45deg, #00f5ff, #0080ff);
  border: none;
  color: #000;
}

:deep(.el-button--primary:hover) {
  background: linear-gradient(45deg, #0080ff, #00f5ff);
  box-shadow: 0 0 15px rgba(0, 245, 255, 0.4);
}
</style>
