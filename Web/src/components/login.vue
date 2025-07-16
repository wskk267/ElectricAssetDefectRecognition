<template>
  <div class="app-container">
    <Particles id="tsparticles" :particlesInit="particlesInit" :particlesLoaded="particlesLoaded" :options="options" />
    
    <!-- 登录表单覆盖层 -->
    <div class="login-overlay">
      <div class="login-container">
        <div class="login-header">
          <el-icon class="logo-icon"><Setting /></el-icon>
          <h2>电力资产缺陷识别系统</h2>
          <p>Electric Asset Defect Recognition System</p>
        </div>
        
        <el-form :model="loginForm" :rules="rules" ref="loginFormRef" class="login-form">
          <el-form-item prop="username">
            <el-input 
              v-model="loginForm.username" 
              placeholder="请输入用户名"
              size="large"
              :prefix-icon="User"
            />
          </el-form-item>
          
          <el-form-item prop="password">
            <el-input 
              v-model="loginForm.password" 
              type="password" 
              placeholder="请输入密码"
              size="large"
              :prefix-icon="Lock"
              show-password
              @keyup.enter="handleLogin"
            />
          </el-form-item>
          
          <el-form-item prop="userType">
            <el-radio-group v-model="loginForm.userType" size="large">
              <el-radio label="user">普通用户</el-radio>
              <el-radio label="admin">管理员</el-radio>
            </el-radio-group>
          </el-form-item>
          
          <el-form-item>
            <el-button 
              type="primary" 
              size="large" 
              :loading="loading" 
              @click="handleLogin"
              class="login-btn"
            >
              登录
            </el-button>
          </el-form-item>
          
          <el-form-item>
            <el-button 
              type="info" 
              size="large" 
              @click="guestLogin"
              class="guest-btn"
            >
              游客登录
            </el-button>
          </el-form-item>
        </el-form>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock, Setting } from '@element-plus/icons-vue'
import { useParticles } from './re'
import { SHA256 } from '../sha256.js'
import axiosInstance from '../axios'
import '../style.css'

const hashPassword = (password: string) => {
  return SHA256.hash(password);
}

export default defineComponent({
  name: 'Login',
  components: {
    User,
    Lock,
    Setting
  },
  setup() {
    const router = useRouter()
    const { particlesInit, particlesLoaded, options } = useParticles()
    
    const loginFormRef = ref()
    const loading = ref(false)
    
    const loginForm = reactive({
      username: '',
      password: '',
      userType: 'user'
    })
    
    const rules = {
      username: [
        { required: true, message: '请输入用户名', trigger: 'blur' }
      ],
      password: [
        { required: true, message: '请输入密码', trigger: 'blur' }
      ]
    }
    
    const handleLogin = async () => {
      if (!loginFormRef.value) return
      
      try {
        await loginFormRef.value.validate()
        loading.value = true
        
        // SHA256加密密码
        const hashedPassword = hashPassword(loginForm.password)
        
        const response = await axiosInstance.post('/api/login', {
          username: loginForm.username,
          password: hashedPassword,
          user_type: loginForm.userType
        })
        
        if (response.data.success) {
          // 保存登录信息到localStorage
          localStorage.setItem('token', response.data.token)
          localStorage.setItem('userType', response.data.user_type)
          localStorage.setItem('userId', response.data.user_id.toString())
          localStorage.setItem('username', response.data.username)
          
          // 如果是普通用户，保存权限信息
          if (response.data.user_type === 'user') {
            localStorage.setItem('userPermissions', JSON.stringify({
              imagelimit: response.data.imagelimit,
              batchlimit: response.data.batchlimit,
              realtimePermission: response.data.realtimePermission,
              isbannd: response.data.isbannd || 0
            }))
          }
          
          ElMessage.success('登录成功！')
          
          // 根据用户类型跳转
          if (response.data.user_type === 'admin') {
            router.push('/admin')
          } else {
            router.push('/user')
          }
        } else {
          ElMessage.error(response.data.message || '登录失败')
        }
      } catch (error: any) {
        console.error('登录错误:', error)
        ElMessage.error(error.response?.data?.message || '登录失败，请检查网络连接')
      } finally {
        loading.value = false
      }
    }
    
    const guestLogin = async () => {
      loading.value = true
      
      try {
        // 使用游客账号登录
        const hashedPassword = hashPassword('guest123')
        
        const response = await axiosInstance.post('/api/login', {
          username: 'guest',
          password: hashedPassword,
          user_type: 'user'
        })
        
        if (response.data.success) {
          // 保存登录信息到localStorage
          localStorage.setItem('token', response.data.token)
          localStorage.setItem('userType', 'user')
          localStorage.setItem('userId', response.data.user_id.toString())
          localStorage.setItem('username', 'guest')
          localStorage.setItem('userPermissions', JSON.stringify({
            imagelimit: response.data.imagelimit,
            batchlimit: response.data.batchlimit,
            realtimePermission: response.data.realtimePermission
          }))
          
          ElMessage.success('游客登录成功！')
          router.push('/user')
        } else {
          ElMessage.error(response.data.message || '游客登录失败')
        }
      } catch (error: any) {
        console.error('游客登录错误:', error)
        ElMessage.error('游客登录失败，请检查网络连接')
      } finally {
        loading.value = false
      }
    }
    
    return {
      particlesInit,
      particlesLoaded,
      options,
      loginForm,
      rules,
      loginFormRef,
      loading,
      handleLogin,
      guestLogin,
      User,
      Lock
    }
  }
})
</script>

<style scoped>
.app-container {
  position: relative;
  min-height: 100vh;
  overflow: hidden;
}

.login-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 10;
}

.login-container {
  background: rgba(26, 26, 46, 0.9);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(0, 245, 255, 0.3);
  border-radius: 20px;
  padding: 40px;
  width: 100%;
  max-width: 400px;
  box-shadow: 0 20px 60px rgba(0, 245, 255, 0.2);
}

.login-header {
  text-align: center;
  margin-bottom: 30px;
}

.logo-icon {
  font-size: 48px;
  color: #00f5ff;
  margin-bottom: 15px;
  animation: float 3s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-10px); }
}

.login-header h2 {
  color: #00f5ff;
  margin: 0 0 10px 0;
  font-size: 24px;
  font-weight: bold;
  text-shadow: 0 0 10px rgba(0, 245, 255, 0.5);
}

.login-header p {
  color: #888;
  margin: 0;
  font-size: 14px;
}

.login-form {
  margin-top: 20px;
}

:deep(.el-input__wrapper) {
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(0, 245, 255, 0.3);
  border-radius: 10px;
  box-shadow: none;
}

:deep(.el-input__wrapper:hover) {
  border-color: rgba(0, 245, 255, 0.5);
}

:deep(.el-input__wrapper.is-focus) {
  border-color: #00f5ff;
  box-shadow: 0 0 10px rgba(0, 245, 255, 0.3);
}

:deep(.el-input__inner) {
  color: #ffffff;
  background: transparent;
}

:deep(.el-input__inner::placeholder) {
  color: #666;
}

:deep(.el-radio-group) {
  display: flex;
  justify-content: center;
  gap: 20px;
}

:deep(.el-radio) {
  color: #ffffff;
  margin-right: 0;
}

:deep(.el-radio__input.is-checked .el-radio__inner) {
  background-color: #00f5ff;
  border-color: #00f5ff;
}

:deep(.el-radio__input.is-checked + .el-radio__label) {
  color: #00f5ff;
}

.login-btn {
  width: 100%;
  background: linear-gradient(45deg, #00f5ff, #0080ff);
  border: none;
  border-radius: 10px;
  height: 45px;
  font-size: 16px;
  font-weight: bold;
  color: #000;
  transition: all 0.3s ease;
}

.login-btn:hover {
  background: linear-gradient(45deg, #0080ff, #00f5ff);
  box-shadow: 0 0 20px rgba(0, 245, 255, 0.4);
  transform: translateY(-2px);
}

.guest-btn {
  width: 100%;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(0, 245, 255, 0.3);
  border-radius: 10px;
  height: 45px;
  font-size: 16px;
  color: #00f5ff;
  transition: all 0.3s ease;
}

.guest-btn:hover {
  background: rgba(0, 245, 255, 0.1);
  border-color: #00f5ff;
  box-shadow: 0 0 15px rgba(0, 245, 255, 0.3);
  transform: translateY(-2px);
}

@media (max-width: 768px) {
  .login-container {
    margin: 20px;
    padding: 30px 20px;
  }
  
  .login-header h2 {
    font-size: 20px;
  }
  
  .logo-icon {
    font-size: 36px;
  }
}
</style>
