import axios from "axios"
import { getToken, removeToken } from "./auth"

const api = axios.create({
  baseURL:
    process.env.NEXT_PUBLIC_API_BASE_URL ||
    process.env.API_BASE_URL ||
    "http://localhost:8000",
  withCredentials: false,
  timeout: 10000, // 10秒超时
})

// Attach token on each request if available
api.interceptors.request.use((config) => {
  const token = getToken()
  if (token) {
    config.headers = config.headers ?? {}
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Handle response errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      // 服务器返回了错误响应
      if (error.response.status === 401) {
        // 未授权，清除 token 并跳转到登录页
        removeToken()
        if (typeof window !== 'undefined') {
          window.location.href = '/login'
        }
      }
    } else if (error.request) {
      // 请求已发出但没有收到响应
      console.error('Network error: No response from server')
    } else {
      // 请求配置出错
      console.error('Request error:', error.message)
    }
    return Promise.reject(error)
  }
)

export default api

