<template>
  <div class="api-usage">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>📊 API用量监控</span>
          <el-button type="primary" @click="refreshAll">
            <el-icon><Refresh /></el-icon>
            刷新全部
          </el-button>
        </div>
      </template>

      <!-- 提供商列表 -->
      <el-table :data="providers" v-loading="loading" style="width: 100%">
        <el-table-column prop="provider" label="提供商" width="150">
          <template #default="{ row }">
            <el-tag :type="getProviderType(row.provider)">
              {{ getProviderName(row.provider) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="config_name" label="配置名称" width="200" />

        <el-table-column label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="余额/用量" min-width="350">
          <template #default="{ row }">
            <!-- 有代金券信息的情况（月之暗面） -->
            <div v-if="row.voucher_balance !== undefined">
              <el-descriptions :column="1" border size="small">
                <el-descriptions-item label="总余额">
                  <el-statistic :value="row.balance" suffix="元" />
                </el-descriptions-item>
                <el-descriptions-item label="代金券">
                  <el-tag type="success" size="small">{{ row.voucher_balance }} 元</el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="现金余额">
                  <el-tag type="primary" size="small">{{ row.cash_balance }} 元</el-tag>
                </el-descriptions-item>
              </el-descriptions>
            </div>
            <!-- 硅基流动 - 显示代金券提示 -->
            <div v-else-if="row.provider === 'siliconflow'">
              <el-alert
                type="success"
                :closable="false"
                show-icon
              >
                <template #title>
                  <div style="font-size: 14px; font-weight: bold;">
                    🔖 硅基流动代金券信息
                  </div>
                </template>
                <template #default>
                  <div style="font-size: 13px; line-height: 1.8">
                    <div>• <strong>新用户注册赠送</strong>：16元代金券</div>
                    <div>• <strong>当前状态</strong>：{{ row.api_key_valid ? '✅ API Key有效' : '❌ API Key无效' }}</div>
                    <div>• <strong>代金券范围</strong>：全平台通用</div>
                    <div>• <strong>使用方式</strong>：首次充值后自动抵扣</div>
                    <div>• <strong>无需充值</strong>：代金券可直接使用</div>
                    <el-link 
                      type="primary" 
                      :href="row.dashboard_url || 'https://cloud.siliconflow.cn/account/balance'" 
                      target="_blank"
                      style="margin-top: 10px"
                    >
                      🔍 查看代金券详情（剩余额度、有效期等）
                    </el-link>
                  </div>
                </template>
              </el-alert>
              <!-- 如果有余额信息则显示 -->
              <el-statistic v-if="row.balance !== undefined" title="账户余额" :value="row.balance" style="margin-top: 10px">
                <template #suffix>元</template>
              </el-statistic>
              <el-text v-if="row.message" type="info" size="small" style="display: block; margin-top: 5px">
                {{ row.message }}
              </el-text>
            </div>
            <!-- 普通余额情况 -->
            <div v-else-if="row.balance !== undefined">
              <el-statistic title="账户余额" :value="row.balance">
                <template #suffix>元</template>
              </el-statistic>
              <el-text v-if="row.note" type="info" size="small" style="display: block; margin-top: 5px">
                {{ row.note }}
              </el-text>
            </div>
            <!-- 仅提示信息的情况 -->
            <div v-else-if="row.message">
              <el-text>{{ row.message }}</el-text>
            </div>
            <div v-else>
              <el-text type="info">暂无数据</el-text>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button 
              size="small" 
              type="primary"
              @click="refreshProvider(row.provider)"
              :loading="row.loading"
            >
              刷新
            </el-button>
            <el-button 
              v-if="row.dashboard_url"
              size="small" 
              type="success"
              @click="openDashboard(row.dashboard_url)"
            >
              官网
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 提示信息 -->
      <el-alert
        title="💡 提示"
        type="info"
        :closable="false"
        style="margin-top: 20px"
      >
        <template #default>
          <ul style="margin: 0; padding-left: 20px">
            <li>系统会自动检测已配置的API提供商，只显示有配置的项目</li>
            <li><strong>硅基流动</strong>：实时查询账户余额（包含代金券），新用户注册赠送16元</li>
            <li><strong>月之暗面 (Kimi)</strong>：查询总余额、代金券余额和现金余额</li>
            <li><strong>魔搭社区</strong>：验证API Key有效性，详细用量请查看官网</li>
            <li><strong>阿里百炼</strong>：验证API Key有效性，详细用量请查看控制台</li>
            <li>如需添加新提供商，请前往：<el-link type="primary" href="/llm-config" target="_blank">LLM配置管理</el-link></li>
          </ul>
        </template>
      </el-alert>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import apiClient from '../utils/api'

interface ProviderUsage {
  provider: string
  config_name: string
  status: string
  balance?: number
  voucher_balance?: number  // 代金券余额（月之暗面）
  cash_balance?: number     // 现金余额（月之暗面）
  currency?: string
  message?: string
  note?: string             // 备注信息（硅基流动）
  dashboard_url?: string
  api_key_valid?: boolean
  loading?: boolean
}

const providers = ref<ProviderUsage[]>([])
const loading = ref(false)

// 获取已配置的提供商列表
const fetchConfiguredProviders = async (): Promise<string[]> => {
  try {
    const response = await apiClient.get('/api-usage/providers')
    return response.data.providers.map((p: any) => p.provider)
  } catch (error) {
    console.error('获取配置列表失败:', error)
    // 降级：返回默认列表
    return ['siliconflow', 'modelscope']
  }
}

// 获取提供商显示名称
const getProviderName = (provider: string) => {
  const names: Record<string, string> = {
    siliconflow: '硅基流动',
    modelscope: '魔搭社区',
    dashscope: '阿里百炼'
  }
  return names[provider] || provider
}

// 获取提供商标签类型
const getProviderType = (provider: string) => {
  const types: Record<string, string> = {
    siliconflow: 'success',
    modelscope: 'primary',
    dashscope: 'warning'
  }
  return types[provider] || ''
}

// 获取状态文本
const getStatusText = (status: string) => {
  const texts: Record<string, string> = {
    success: '成功',
    info: '信息',
    warning: '警告',
    failed: '失败'
  }
  return texts[status] || status
}

// 获取状态标签类型
const getStatusType = (status: string) => {
  const types: Record<string, string> = {
    success: 'success',
    info: 'info',
    warning: 'warning',
    failed: 'danger'
  }
  return types[status] || ''
}

// 查询单个提供商用量
const fetchProviderUsage = async (provider: string) => {
  try {
    // 设置加载状态
    const index = providers.value.findIndex(p => p.provider === provider)
    if (index !== -1) {
      providers.value[index].loading = true
    }

    const response = await apiClient.get(`/api-usage/${provider}`)
    
    const usage: ProviderUsage = {
      provider: response.data.provider,
      config_name: response.data.config_name,
      status: response.data.status,
      balance: response.data.balance,
      voucher_balance: response.data.voucher_balance,
      cash_balance: response.data.cash_balance,
      currency: response.data.currency,
      message: response.data.message,
      note: response.data.note,
      dashboard_url: response.data.dashboard_url,
      api_key_valid: response.data.api_key_valid,
      loading: false
    }

    // 更新或添加
    if (index !== -1) {
      providers.value[index] = usage
    } else {
      providers.value.push(usage)
    }
  } catch (error: any) {
    console.error(`查询${provider}用量失败:`, error)
    ElMessage.error(`查询${getProviderName(provider)}用量失败: ${error.response?.data?.detail || error.message}`)
    
    // 移除加载状态
    const index = providers.value.findIndex(p => p.provider === provider)
    if (index !== -1) {
      providers.value[index].loading = false
    }
  }
}

// 刷新单个提供商
const refreshProvider = async (provider: string) => {
  await fetchProviderUsage(provider)
}

// 刷新全部
const refreshAll = async () => {
  loading.value = true
  try {
    // 先获取已配置的提供商列表
    const configuredProviders = await fetchConfiguredProviders()
    
    if (configuredProviders.length === 0) {
      ElMessage.warning('暂无已配置的API提供商，请先在LLM配置页面添加')
      providers.value = []
      return
    }
    
    // 只查询已配置的提供商
    await Promise.all(
      configuredProviders.map(provider => fetchProviderUsage(provider))
    )
    
    ElMessage.success(`刷新成功，共${configuredProviders.length}个提供商`)
  } catch (error) {
    console.error('刷新全部失败:', error)
  } finally {
    loading.value = false
  }
}

// 打开官网
const openDashboard = (url: string) => {
  window.open(url, '_blank')
}

onMounted(() => {
  refreshAll()
})
</script>

<style scoped lang="scss">
.api-usage {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
