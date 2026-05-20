<template>
  <div class="account-nurturing">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>🌱 养号中心</span>
        </div>
      </template>

      <el-alert
        title="养号说明"
        type="info"
        :closable="false"
        show-icon
        style="margin-bottom: 20px"
      >
        <p>养号是指模拟真实用户行为，提高账号活跃度和健康度，降低被平台识别为营销号的风险。</p>
        <p><strong>养号策略：</strong></p>
        <ul>
          <li>每日浏览50+相关内容</li>
          <li>随机点赞（5%概率）</li>
          <li>偶尔评论（1%概率）</li>
          <li>极少分享（0.5%概率）</li>
          <li>活跃时间：12:00-13:00, 20:00-22:00</li>
          <li>休息时间：7小时/天</li>
        </ul>
      </el-alert>

      <el-row :gutter="20">
        <el-col :span="8">
          <el-statistic title="养号中账号" :value="nurturingCount">
            <template #suffix>个</template>
          </el-statistic>
        </el-col>
        <el-col :span="8">
          <el-statistic title="已完成养号" :value="completedCount">
            <template #suffix>个</template>
          </el-statistic>
        </el-col>
        <el-col :span="8">
          <el-statistic title="今日操作次数" :value="todayActions">
            <template #suffix>次</template>
          </el-statistic>
        </el-col>
      </el-row>

      <el-divider />

      <el-table :data="accounts" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="platform" label="平台" width="120">
          <template #default="{ row }">
            <el-tag :type="getPlatformType(row.platform)">
              {{ getPlatformName(row.platform) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="username" label="用户名" />
        <el-table-column prop="status" label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="row.status === 'nurturing' ? 'warning' : 'success'">
              {{ row.status === 'nurturing' ? '养号中' : '已完成' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="health_score" label="健康度" width="120">
          <template #default="{ row }">
            <el-progress :percentage="row.health_score" :color="getHealthColor(row.health_score)" />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="startNurturing(row.id)" :loading="operating">
              开始养号
            </el-button>
            <el-button size="small" type="primary" @click="viewSessions(row.id)">
              查看记录
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import apiClient from '../utils/api'
import { ElMessage } from 'element-plus'

const loading = ref(false)
const operating = ref(false)
const accounts = ref<any[]>([])
const nurturingCount = ref(0)
const completedCount = ref(0)
const todayActions = ref(0)

const getPlatformType = (platform: string) => {
  const typeMap: any = {
    'toutiao': 'danger',
    'douyin': '',
    'xiaohongshu': 'danger',
    'bilibili': 'primary',
    'kuaishou': 'warning',
    'wechat': 'success'
  }
  return typeMap[platform] || 'info'
}

const getPlatformName = (platform: string) => {
  const nameMap: any = {
    'toutiao': '今日头条',
    'douyin': '抖音',
    'xiaohongshu': '小红书',
    'bilibili': 'B站',
    'kuaishou': '快手',
    'wechat': '视频号'
  }
  return nameMap[platform] || platform
}

const getHealthColor = (score: number) => {
  if (score >= 80) return '#67c23a'
  if (score >= 60) return '#e6a23c'
  return '#f56c6c'
}

const fetchAccounts = async () => {
  loading.value = true
  try {
    const response = await apiClient.get('/accounts/list', {
      params: { page: 1, page_size: 100 }
    })
    
    accounts.value = response.data.data.items
    nurturingCount.value = accounts.value.filter((a: any) => a.status === 'nurturing').length
    completedCount.value = accounts.value.filter((a: any) => a.status === 'active').length
  } catch (error) {
    console.error('获取账号列表失败:', error)
  } finally {
    loading.value = false
  }
}

const startNurturing = async (accountId: number) => {
  operating.value = true
  try {
    // TODO: 调用后端API启动养号任务
    ElMessage.success('养号任务已启动')
    await fetchAccounts()
  } catch (error) {
    console.error('启动养号失败:', error)
    ElMessage.error('启动养号失败')
  } finally {
    operating.value = false
  }
}

const viewSessions = (accountId: number) => {
  ElMessage.info('查看养号记录功能开发中...')
}

onMounted(() => {
  fetchAccounts()
})
</script>

<style scoped>
.account-nurturing {
  padding: 0;
}

.card-header {
  font-weight: bold;
  font-size: 16px;
}
</style>
