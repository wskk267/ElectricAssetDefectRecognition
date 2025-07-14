import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import axiosInstance from '../axios'

export function useApi() {
  const loading = ref(false)

  const request = async (method, url, data = null, config = {}) => {
    console.log(`🚀 API请求: ${method.toUpperCase()} ${url}`, { data, config })
    
    loading.value = true
    try {
      const token = localStorage.getItem('token')
      const headers = {
        Authorization: `Bearer ${token}`,
        ...config.headers
      }

      const requestConfig = {
        ...config,
        headers
      }

      let response
      
      switch (method.toLowerCase()) {
        case 'get':
          response = await axiosInstance.get(url, {
            ...requestConfig,
            params: data
          })
          break
        case 'post':
          response = await axiosInstance.post(url, data, requestConfig)
          break
        case 'put':
          response = await axiosInstance.put(url, data, requestConfig)
          break
        case 'delete':
          response = await axiosInstance.delete(url, requestConfig)
          break
        default:
          throw new Error(`Unsupported HTTP method: ${method}`)
      }

      console.log(`✅ API响应: ${method.toUpperCase()} ${url}`, response.data)

      if (response.data.success) {
        return response.data
      } else {
        throw new Error(response.data.message || 'API request failed')
      }
    } catch (error) {
      console.error(`❌ API请求失败: ${method.toUpperCase()} ${url}`, error)
      ElMessage.error(error.message || 'API请求失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  console.log('🔧 useApi初始化完成, request类型:', typeof request)

  return {
    loading,
    request
  }
}
