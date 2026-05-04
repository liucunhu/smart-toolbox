/**
 * 通用 API 响应结构
 */
export interface ApiResponse<T = any> {
  code?: number
  message?: string
  data: T
}

/**
 * 统一错误信息接口
 */
export interface ApiError {
  status: number
  message: string
  details?: string
}

/**
 * 账号相关类型
 */
export interface Account {
  id: number
  platform: 'douyin' | 'xiaohongshu' | 'bilibili' | 'toutiao'
  username?: string
  status: 'registering' | 'nurturing' | 'active' | 'banned'
  health_score: number
  proxy_ip?: string
  cookies?: string  // 登录后的 Cookie（用于自动化发布）
  created_at?: string
  updated_at?: string
}

/**
 * 内容任务类型
 */
export interface ContentTask {
  task_id: string
  topic: string
  script?: string
  status: 'pending' | 'processing' | 'completed'
}
