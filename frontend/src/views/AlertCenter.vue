<template>
  <div class="alert-center">
    <el-row :gutter="20">
      <!-- 报警配置 -->
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>⚙️ 报警渠道配置</span>
            </div>
          </template>

          <el-tabs v-model="activeTab">
            <!-- 邮件配置 -->
            <el-tab-pane label="📧 邮件报警" name="email">
              <el-form :model="emailConfig" label-width="120px">
                <el-form-item label="启用邮件">
                  <el-switch v-model="emailConfig.enabled" />
                </el-form-item>

                <el-form-item label="SMTP服务器">
                  <el-input v-model="emailConfig.host" placeholder="smtp.example.com" />
                </el-form-item>

                <el-form-item label="端口">
                  <el-input-number v-model="emailConfig.port" :min="1" :max="65535" />
                </el-form-item>

                <el-form-item label="发件人邮箱">
                  <el-input v-model="emailConfig.user" placeholder="noreply@example.com" />
                </el-form-item>

                <el-form-item label="授权码">
                  <el-input v-model="emailConfig.password" type="password" show-password />
                </el-form-item>

                <el-form-item label="收件人列表">
                  <el-select
                    v-model="emailConfig.to"
                    multiple
                    filterable
                    allow-create
                    default-first-option
                    placeholder="输入邮箱地址"
                    style="width: 100%;"
                  >
                    <el-option
                      v-for="item in emailOptions"
                      :key="item"
                      :label="item"
                      :value="item"
                    />
                  </el-select>
                </el-form-item>

                <el-form-item>
                  <el-button type="primary" @click="saveEmailConfig" :loading="saving">
                    💾 保存配置
                  </el-button>
                  <el-button @click="testEmailAlert">📨 发送测试邮件</el-button>
                </el-form-item>
              </el-form>
            </el-tab-pane>

            <!-- 钉钉配置 -->
            <el-tab-pane label="💬 钉钉报警" name="dingtalk">
              <el-form :model="dingtalkConfig" label-width="120px">
                <el-form-item label="Webhook URL">
                  <el-input
                    v-model="dingtalkConfig.webhook_url"
                    type="textarea"
                    :rows="3"
                    placeholder="https://oapi.dingtalk.com/robot/send?access_token=xxx"
                  />
                </el-form-item>

                <el-form-item label="@手机号">
                  <el-select
                    v-model="dingtalkConfig.at_mobiles"
                    multiple
                    filterable
                    allow-create
                    default-first-option
                    placeholder="输入手机号"
                    style="width: 100%;"
                  />
                </el-form-item>

                <el-form-item>
                  <el-button type="primary" @click="saveDingtalkConfig" :loading="saving">
                    💾 保存配置
                  </el-button>
                  <el-button @click="testDingtalkAlert">📨 发送测试消息</el-button>
                </el-form-item>
              </el-form>
            </el-tab-pane>
          </el-tabs>
        </el-card>
      </el-col>

      <!-- 报警历史 -->
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>📜 报警历史记录</span>
              <el-button type="primary" size="small" @click="fetchAlertHistory" :loading="loading">
                🔄 刷新
              </el-button>
            </div>
          </template>

          <!-- 筛选条件 -->
          <el-form :inline="true" :model="filters" class="filter-form">
            <el-form-item label="报警类型">
              <el-select v-model="filters.type" placeholder="全部" clearable @change="fetchAlertHistory">
                <el-option label="账号异常" value="account_anomaly" />
                <el-option label="任务失败" value="task_failed" />
                <el-option label="系统健康" value="system_health" />
              </el-select>
            </el-form-item>
            <el-form-item label="状态">
              <el-select v-model="filters.status" placeholder="全部" clearable @change="fetchAlertHistory">
                <el-option label="成功" value="success" />
                <el-option label="失败" value="failed" />
              </el-select>
            </el-form-item>
          </el-form>

          <!-- 报警列表 -->
          <el-table :data="alertHistory" style="width: 100%" v-loading="loading">
            <el-table-column prop="id" label="ID" width="80" />
            <el-table-column prop="type" label="类型" width="120">
              <template #default="{ row }">
                <el-tag :type="getAlertTypeTag(row.type)">
                  {{ getAlertTypeName(row.type) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="subject" label="主题" min-width="200" />
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="row.status === 'success' ? 'success' : 'danger'">
                  {{ row.status === 'success' ? '成功' : '失败' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="channels" label="渠道" width="120">
              <template #default="{ row }">
                <el-tag v-for="channel in row.channels" :key="channel" size="small" style="margin-right: 3px;">
                  {{ channel }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="时间" width="180">
              <template #default="{ row }">
                {{ formatTime(row.created_at) }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="100">
              <template #default="{ row }">
                <el-button type="primary" size="small" @click="viewAlertDetail(row)">详情</el-button>
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
            @size-change="fetchAlertHistory"
            @current-change="fetchAlertHistory"
            style="margin-top: 20px; justify-content: flex-end;"
          />
        </el-card>
      </el-col>
    </el-row>

    <!-- 报警详情对话框 -->
    <el-dialog v-model="detailVisible" title="报警详情" width="600px">
      <el-descriptions v-if="currentAlert" :column="1" border>
        <el-descriptions-item label="报警ID">{{ currentAlert.id }}</el-descriptions-item>
        <el-descriptions-item label="类型">{{ getAlertTypeName(currentAlert.type) }}</el-descriptions-item>
        <el-descriptions-item label="主题">{{ currentAlert.subject }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="currentAlert.status === 'success' ? 'success' : 'danger'">
            {{ currentAlert.status === 'success' ? '成功' : '失败' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="渠道">{{ currentAlert.channels.join(', ') }}</el-descriptions-item>
        <el-descriptions-item label="内容">
          <pre style="white-space: pre-wrap; background: #f5f5f5; padding: 10px; border-radius: 4px;">{{ currentAlert.message }}</pre>
        </el-descriptions-item>
        <el-descriptions-item label="时间">{{ formatTime(currentAlert.created_at) }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import apiClient from '../utils/api'
import { ElMessage } from 'element-plus'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'

const activeTab = ref('email')
const loading = ref(false)
const saving = ref(false)
const detailVisible = ref(false)
const currentAlert = ref<any>(null)

// 邮件配置
const emailConfig = ref({
  enabled: false,
  host: '',
  port: 587,
  user: '',
  password: '',
  to: [] as string[]
})

const emailOptions = [
  'admin@example.com',
  'ops@example.com',
  'dev@example.com'
]

// 钉钉配置
const dingtalkConfig = ref({
  webhook_url: '',
  at_mobiles: [] as string[]
})

// 报警历史
const alertHistory = ref<any[]>([])
const filters = ref({
  type: '',
  status: ''
})
const pagination = ref({
  page: 1,
  pageSize: 20,
  total: 0
})

// 保存邮件配置
const saveEmailConfig = async () => {
  saving.value = true
  try {
    await apiClient.post(`${API_BASE_URL}/alerts/config/email`, emailConfig.value)
    ElMessage.success('邮件配置保存成功')
  } catch (error) {
    console.error('保存失败:', error)
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

// 保存钉钉配置
const saveDingtalkConfig = async () => {
  saving.value = true
  try {
    await apiClient.post(`${API_BASE_URL}/alerts/config/dingtalk`, dingtalkConfig.value)
    ElMessage.success('钉钉配置保存成功')
  } catch (error) {
    console.error('保存失败:', error)
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

// 测试邮件
const testEmailAlert = async () => {
  try {
    await apiClient.post(`${API_BASE_URL}/alerts/test/email`)
    ElMessage.success('测试邮件已发送')
  } catch (error) {
    console.error('发送失败:', error)
    ElMessage.error('发送失败')
  }
}

// 测试钉钉
const testDingtalkAlert = async () => {
  try {
    await apiClient.post(`${API_BASE_URL}/alerts/test/dingtalk`)
    ElMessage.success('测试消息已发送')
  } catch (error) {
    console.error('发送失败:', error)
    ElMessage.error('发送失败')
  }
}

// 获取报警历史
const fetchAlertHistory = async () => {
  loading.value = true
  try {
    const params: any = {
      skip: (pagination.value.page - 1) * pagination.value.pageSize,
      limit: pagination.value.pageSize
    }

    if (filters.value.type) params.type = filters.value.type
    if (filters.value.status) params.status = filters.value.status

    const response = await apiClient.get(`${API_BASE_URL}/alerts/history`, { params })
    alertHistory.value = response.data.alerts
    pagination.value.total = response.data.total
  } catch (error) {
    console.error('获取报警历史失败:', error)
    ElMessage.error('获取报警历史失败')
  } finally {
    loading.value = false
  }
}

// 查看报警详情
const viewAlertDetail = (alert: any) => {
  currentAlert.value = alert
  detailVisible.value = true
}

// 报警类型标签
const getAlertTypeTag = (type: string) => {
  const typeMap: any = {
    'account_anomaly': 'warning',
    'task_failed': 'danger',
    'system_health': 'info'
  }
  return typeMap[type] || 'info'
}

// 报警类型名称
const getAlertTypeName = (type: string) => {
  const nameMap: any = {
    'account_anomaly': '账号异常',
    'task_failed': '任务失败',
    'system_health': '系统健康'
  }
  return nameMap[type] || type
}

// 格式化时间
const formatTime = (time: string | null) => {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

onMounted(() => {
  fetchAlertHistory()
})
</script>

<style scoped>
.alert-center { padding: 20px; }
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
