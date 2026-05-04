<template>
  <div class="sms-config">
    <el-row :gutter="20">
      <!-- SMS平台配置 -->
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>📱 SMS接码平台配置</span>
            </div>
          </template>

          <el-form :model="smsConfig" label-width="120px">
            <el-form-item label="API Key">
              <el-input v-model="smsConfig.api_key" type="password" show-password placeholder="输入API密钥" />
            </el-form-item>

            <el-form-item label="Base URL">
              <el-input v-model="smsConfig.base_url" placeholder="https://api.sms-platform.com" />
            </el-form-item>

            <el-form-item>
              <el-button type="primary" @click="saveSmsConfig" :loading="saving">
                💾 保存配置
              </el-button>
              <el-button @click="testSmsConnection">🔗 测试连接</el-button>
            </el-form-item>
          </el-form>

          <el-divider />

          <h4>支持的接码平台：</h4>
          <el-tag v-for="platform in supportedPlatforms" :key="platform" style="margin-right: 5px; margin-bottom: 5px;">
            {{ platform }}
          </el-tag>
        </el-card>
      </el-col>

      <!-- 手机号使用记录 -->
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>📋 手机号使用记录</span>
              <el-button type="primary" size="small" @click="fetchPhoneRecords" :loading="loading">
                🔄 刷新
              </el-button>
            </div>
          </template>

          <!-- 筛选条件 -->
          <el-form :inline="true" :model="filters" class="filter-form">
            <el-form-item label="平台">
              <el-select v-model="filters.platform" placeholder="全部" clearable @change="fetchPhoneRecords">
                <el-option label="抖音" value="douyin" />
                <el-option label="小红书" value="xiaohongshu" />
                <el-option label="B站" value="bilibili" />
              </el-select>
            </el-form-item>
            <el-form-item label="状态">
              <el-select v-model="filters.status" placeholder="全部" clearable @change="fetchPhoneRecords">
                <el-option label="使用中" value="in_use" />
                <el-option label="已释放" value="released" />
                <el-option label="失败" value="failed" />
              </el-select>
            </el-form-item>
          </el-form>

          <!-- 记录列表 -->
          <el-table :data="phoneRecords" style="width: 100%" v-loading="loading">
            <el-table-column prop="id" label="ID" width="80" />
            <el-table-column prop="phone_number" label="手机号" width="150" />
            <el-table-column prop="platform" label="平台" width="100">
              <template #default="{ row }">
                <el-tag>{{ row.platform }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="getStatusType(row.status)">
                  {{ getStatusName(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="verification_code" label="验证码" width="100">
              <template #default="{ row }">
                <span v-if="row.verification_code">{{ row.verification_code }}</span>
                <span v-else>-</span>
              </template>
            </el-table-column>
            <el-table-column prop="used_at" label="使用时间" width="180">
              <template #default="{ row }">
                {{ formatTime(row.used_at) }}
              </template>
            </el-table-column>
            <el-table-column prop="released_at" label="释放时间" width="180">
              <template #default="{ row }">
                {{ formatTime(row.released_at) }}
              </template>
            </el-table-column>
          </el-table>

          <!-- 分页 -->
          <el-pagination
            v-model:current-page="pagination.page"
            v-model:page-size="pagination.pageSize"
            :page-sizes="[10, 20, 50]"
            :total="pagination.total"
            layout="total, sizes, prev, pager, next"
            @size-change="fetchPhoneRecords"
            @current-change="fetchPhoneRecords"
            style="margin-top: 20px; justify-content: flex-end;"
          />
        </el-card>
      </el-col>
    </el-row>

    <!-- 验证码获取日志 -->
    <el-card style="margin-top: 20px;">
      <template #header>
        <div class="card-header">
          <span>📜 验证码获取日志</span>
        </div>
      </template>

      <el-table :data="verificationLogs" style="width: 100%">
        <el-table-column prop="timestamp" label="时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.timestamp) }}
          </template>
        </el-table-column>
        <el-table-column prop="phone_number" label="手机号" width="150" />
        <el-table-column prop="platform" label="平台" width="100" />
        <el-table-column prop="action" label="操作" width="120">
          <template #default="{ row }">
            <el-tag :type="getActionType(row.action)">
              {{ getActionName(row.action) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="result" label="结果" min-width="200" />
        <el-table-column prop="duration" label="耗时" width="100">
          <template #default="{ row }">
            {{ row.duration }}s
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'

const loading = ref(false)
const saving = ref(false)

// SMS配置
const smsConfig = ref({
  api_key: '',
  base_url: 'https://api.sms-platform.com'
})

const supportedPlatforms = ['SMS-Activate', '5sim', 'OnlineSIM', '接码号', '云短信']

// 手机号记录
const phoneRecords = ref<any[]>([])
const filters = ref({
  platform: '',
  status: ''
})
const pagination = ref({
  page: 1,
  pageSize: 20,
  total: 0
})

// 验证日志
const verificationLogs = ref<any[]>([
  {
    timestamp: new Date().toISOString(),
    phone_number: '138****1234',
    platform: 'douyin',
    action: 'get_code',
    result: '成功获取验证码: 888888',
    duration: 12.5
  },
  {
    timestamp: new Date(Date.now() - 3600000).toISOString(),
    phone_number: '139****5678',
    platform: 'xiaohongshu',
    action: 'release',
    result: '手机号已释放',
    duration: 0.3
  }
])

// 保存SMS配置
const saveSmsConfig = async () => {
  saving.value = true
  try {
    await axios.post(`${API_BASE_URL}/sms/config`, smsConfig.value)
    ElMessage.success('SMS配置保存成功')
  } catch (error) {
    console.error('保存失败:', error)
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

// 测试连接
const testSmsConnection = async () => {
  try {
    await axios.post(`${API_BASE_URL}/sms/test-connection`)
    ElMessage.success('连接测试成功')
  } catch (error) {
    console.error('连接失败:', error)
    ElMessage.error('连接失败')
  }
}

// 获取手机号记录
const fetchPhoneRecords = async () => {
  loading.value = true
  try {
    const params: any = {
      skip: (pagination.value.page - 1) * pagination.value.pageSize,
      limit: pagination.value.pageSize
    }

    if (filters.value.platform) params.platform = filters.value.platform
    if (filters.value.status) params.status = filters.value.status

    const response = await axios.get(`${API_BASE_URL}/sms/phone-records`, { params })
    phoneRecords.value = response.data.records
    pagination.value.total = response.data.total
  } catch (error) {
    console.error('获取记录失败:', error)
    ElMessage.error('获取记录失败')
  } finally {
    loading.value = false
  }
}

// 状态类型
const getStatusType = (status: string) => {
  const typeMap: any = {
    'in_use': 'warning',
    'released': 'success',
    'failed': 'danger'
  }
  return typeMap[status] || 'info'
}

// 状态名称
const getStatusName = (status: string) => {
  const nameMap: any = {
    'in_use': '使用中',
    'released': '已释放',
    'failed': '失败'
  }
  return nameMap[status] || status
}

// 操作类型
const getActionType = (action: string) => {
  const typeMap: any = {
    'get_code': 'success',
    'release': 'info',
    'error': 'danger'
  }
  return typeMap[action] || 'info'
}

// 操作名称
const getActionName = (action: string) => {
  const nameMap: any = {
    'get_code': '获取验证码',
    'release': '释放号码',
    'error': '错误'
  }
  return nameMap[action] || action
}

// 格式化时间
const formatTime = (time: string | null) => {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

onMounted(() => {
  fetchPhoneRecords()
})
</script>

<style scoped>
.sms-config { padding: 20px; }
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
}
.filter-form {
  margin-bottom: 20px;
}
</style>
