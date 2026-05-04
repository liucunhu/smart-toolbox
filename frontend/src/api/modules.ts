import { request } from '../utils/request'
import type { Account, ContentTask } from '../types/api'

/**
 * 认证 API
 */
export const authApi = {
  // 登录（使用表单格式）
  login: async (username: string, password: string) => {
    // OAuth2 Password Flow 需要使用表单格式
    const formData = new URLSearchParams()
    formData.append('username', username)
    formData.append('password', password)
    
    return request.post<{ access_token: string; token_type: string; user_id: number }>('/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      }
    })
  },

  // 注册
  register: (username: string, password: string, email?: string) => {
    return request.post('/auth/register', {
      username,
      password,
      email
    })
  },

  // 登出
  logout: () => {
    return request.post('/auth/logout')
  }
}

/**
 * 账号管理 API
 */
export const accountApi = {
  // 注册账号
  register: (data: Partial<Account>) => {
    return request.post<{ message: string; task_id: string; account_id: number }>('/accounts/register', data)
  },

  // 获取账号列表
  list: (params?: { platform?: string; status?: string; skip?: number; limit?: number }) => {
    return request.get<{ total: number; accounts: Account[] }>('/accounts/list', { params })
  },

  // 获取账号详情
  detail: (id: number) => {
    return request.get<Account>(`/accounts/${id}`)
  },

  // 获取健康账号列表
  getHealthyAccounts: (platform?: string) => {
    return request.get<{ count: number; accounts: Account[] }>('/accounts/healthy', {
      params: { platform }
    })
  },

  // 头条账号登录
  toutiaoLogin: (accountId: number, username: string, password: string) => {
    return request.post('/accounts/toutiao/login', null, {
      params: { account_id: accountId, username, password }
    })
  }
}

/**
 * 内容创作 API
 */
export const contentApi = {
  // 生成文案
  generateScript: (topic: string, platform: string) => {
    return request.post<ContentTask>('/content/generate', null, {
      params: { topic, platform }
    })
  },

  // 违禁词检测
  checkCompliance: (text: string, platform: string) => {
    return request.post<{ cleaned_text: string; violations: string[]; is_safe: boolean }>('/compliance/check', null, {
      params: { text, platform }
    })
  }
}

/**
 * 调度中心 API
 */
export const scheduleApi = {
  // 获取下一个建议发布时间
  getNextPublishTime: () => {
    return request.get<{ suggested_time: string }>('/schedule/next_time')
  }
}
