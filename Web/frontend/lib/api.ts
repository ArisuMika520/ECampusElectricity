import axios from "axios"
import { getToken, removeToken } from "./auth"

// 后端 API 地址
// 使用 Next.js API Routes 作为代理，避免暴露后端地址和 CORS 问题
// 前端请求 /api/proxy/*，Next.js 服务端转发到 localhost:8000
// 统一使用 /api/proxy 作为 baseURL，确保客户端和服务端都通过代理路由
const api = axios.create({
  baseURL: '/api/proxy',
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

