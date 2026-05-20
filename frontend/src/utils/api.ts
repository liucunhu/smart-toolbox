/**
 * API客户端配置
 * 统一管理API请求，包含超时、错误处理等
 */
import axios, { AxiosInstance, AxiosError } from 'axios'
import { ElMessage } from 'element-plus'

// API基础URL - 从环境变量读取
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'

// 请求超时时间（毫秒）
const REQUEST_TIMEOUT = 300000 // 300秒（5分钟），头条发布等浏览器自动化操作需要较长时间

/**
 * 创建axios实例
 */
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: REQUEST_TIMEOUT,
  headers: {
    'Content-Type': 'application/json'
  }
})

/**
 * 请求拦截器
 */
apiClient.interceptors.request.use(
  (config) => {
    // 可以在这里添加认证token
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

/**
 * 响应拦截器
 */
apiClient.interceptors.response.use(
  (response) => {
    return response
  },
  (error: AxiosError) => {
    // 处理常见错误
    if (error.code === 'ECONNABORTED') {
      ElMessage.error('请求超时，请检查网络连接')
    } else if (error.response) {
      const status = error.response.status
      switch (status) {
        case 401:
          ElMessage.error('认证失败，请重新登录')
          // 可以跳转到登录页
          // window.location.href = '/login'
          break
        case 403:
          ElMessage.error('没有权限访问')
          break
        case 404:
          ElMessage.error('请求的资源不存在')
          break
        case 500:
          ElMessage.error('服务器内部错误')
          break
        default:
          ElMessage.error(`请求失败: ${status}`)
      }
    } else if (error.request) {
      ElMessage.error('网络错误，请检查连接')
    } else {
      ElMessage.error('请求配置错误')
    }
    
    return Promise.reject(error)
  }
)

export default apiClient
