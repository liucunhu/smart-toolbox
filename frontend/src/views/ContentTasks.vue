<template>
  <div class="content-tasks">
    <!-- 任务详情对话框 -->
    <el-dialog
      v-model="detailDialogVisible"
      title="任务详情"
      width="700px"
      @close="handleDetailClose"
    >
      <el-descriptions :column="2" border v-if="currentTask">
        <el-descriptions-item label="任务ID">
          {{ currentTask.id }}
        </el-descriptions-item>
        <el-descriptions-item label="任务类型">
          <el-tag :type="getTaskTypeColor(currentTask.task_type)">
            {{ getTaskTypeName(currentTask.task_type) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="状态" span="2">
          <el-tag :type="getStatusColor(currentTask.status)">
            {{ getStatusName(currentTask.status) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="平台" span="2">
          <el-tag>{{ getPlatformName(currentTask.platform) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="创建时间" span="2">
          {{ formatTime(currentTask.created_at) }}
        </el-descriptions-item>
        <el-descriptions-item label="开始时间" span="2">
          {{ currentTask.started_at ? formatTime(currentTask.started_at) : '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="完成时间" span="2">
          {{ currentTask.completed_at ? formatTime(currentTask.completed_at) : '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="进度" span="2">
          <el-progress 
            :percentage="currentTask.progress || 0"
            :status="getProgressStatus(currentTask.status)"
          />
        </el-descriptions-item>
        <el-descriptions-item label="输入内容" span="2" v-if="currentTask.input_data">
          <div class="content-box">
            {{ JSON.stringify(currentTask.input_data, null, 2) }}
          </div>
        </el-descriptions-item>
        <el-descriptions-item label="输出结果" span="2" v-if="currentTask.output_data">
          <div class="content-box">
            {{ JSON.stringify(currentTask.output_data, null, 2) }}
          </div>
        </el-descriptions-item>
        <el-descriptions-item label="错误信息" span="2" v-if="currentTask.error_message">
          <el-alert type="error" :closable="false" show-icon>
            {{ currentTask.error_message }}
          </el-alert>
        </el-descriptions-item>
      </el-descriptions>
      
      <template #footer v-if="currentTask">
        <el-button @click="handleDetailClose">关闭</el-button>
        <el-button 
          type="primary" 
          v-if="currentTask.status === 'failed'"
          @click="handleRetry"
        >
          重试任务
        </el-button>
        <el-button 
          type="danger" 
          v-if="['pending', 'processing'].includes(currentTask.status)"
          @click="handleCancelTask"
        >
          取消任务
        </el-button>
      </template>
    </el-dialog>

    <el-card>
      <template #header>
        <div class="card-header">
          <span>📝 内容任务管理</span>
          <div>
            <el-select 
              v-model="filters.status" 
              placeholder="任务状态" 
              clearable
              style="width: 150px; margin-right: 10px;"
              @change="handleFilterChange"
            >
              <el-option label="全部" value="" />
              <el-option label="待处理" value="pending" />
              <el-option label="处理中" value="processing" />
              <el-option label="已完成" value="completed" />
              <el-option label="失败" value="failed" />
              <el-option label="已取消" value="cancelled" />
            </el-select>
            
            <el-select 
              v-model="filters.task_type" 
              placeholder="任务类型" 
              clearable
              style="width: 150px; margin-right: 10px;"
              @change="handleFilterChange"
            >
              <el-option label="全部" value="" />
              <el-option label="AI文案生成" value="generate_script" />
              <el-option label="视频处理" value="process_video" />
              <el-option label="封面生成" value="generate_cover" />
              <el-option label="违禁词检测" value="compliance_check" />
              <el-option label="内容发布" value="publish" />
            </el-select>
            
            <el-button type="primary" @click="handleRefresh" :loading="loading">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
          </div>
        </div>
      </template>

      <!-- 任务统计 -->
      <el-row :gutter="20" style="margin-bottom: 20px;">
        <el-col :span="6">
          <el-card shadow="hover" class="stat-card">
            <div class="stat-item">
              <div class="stat-label">总任务数</div>
              <div class="stat-value">{{ statistics.total }}</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="hover" class="stat-card">
            <div class="stat-item">
              <div class="stat-label">处理中</div>
              <div class="stat-value primary">{{ statistics.processing }}</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="hover" class="stat-card">
            <div class="stat-item">
              <div class="stat-label">已完成</div>
              <div class="stat-value success">{{ statistics.completed }}</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="hover" class="stat-card">
            <div class="stat-item">
              <div class="stat-label">失败</div>
              <div class="stat-value danger">{{ statistics.failed }}</div>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 任务列表 -->
      <el-table
        :data="tasks"
        style="width: 100%"
        v-loading="loading"
        stripe
      >
        <el-table-column prop="id" label="任务ID" width="80" />
        
        <el-table-column prop="task_type" label="任务类型" width="150">
          <template #default="{ row }">
            <el-tag :type="getTaskTypeColor(row.task_type)" size="small">
              {{ getTaskTypeName(row.task_type) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="platform" label="平台" width="120">
          <template #default="{ row }">
            <el-tag v-if="row.platform" size="small">
              {{ getPlatformName(row.platform) }}
            </el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
        
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusColor(row.status)" size="small">
              {{ getStatusName(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="progress" label="进度" width="150">
          <template #default="{ row }">
            <el-progress 
              :percentage="row.progress || 0"
              :status="getProgressStatus(row.status)"
              :stroke-width="6"
            />
          </template>
        </el-table-column>
        
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        
        <el-table-column prop="duration" label="耗时" width="100">
          <template #default="{ row }">
            {{ getDuration(row) }}
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button 
              size="small" 
              type="primary" 
              link
              @click="handleViewDetail(row)"
            >
              详情
            </el-button>
            <el-button 
              v-if="row.status === 'failed'"
              size="small" 
              type="warning" 
              link
              @click="handleRetry(row)"
            >
              重试
            </el-button>
            <el-button 
              v-if="['pending', 'processing'].includes(row.status)"
              size="small" 
              type="danger" 
              link
              @click="handleCancel(row)"
            >
              取消
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <el-pagination
        v-if="total > 0"
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="total"
        layout="total, sizes, prev, pager, next, jumper"
        :page-sizes="[10, 20, 50, 100]"
        style="margin-top: 20px; justify-content: flex-end"
        @size-change="handleSizeChange"
        @current-change="handlePageChange"
      />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import apiClient from '../utils/api'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'

const loading = ref(false)
const tasks = ref<any[]>([])
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)
const detailDialogVisible = ref(false)
const currentTask = ref<any>(null)

const filters = ref({
  status: '',
  task_type: '',
  platform: ''
})

const statistics = ref({
  total: 0,
  processing: 0,
  completed: 0,
  failed: 0
})

let refreshTimer: NodeJS.Timeout | null = null

/**
 * 获取任务类型名称
 */
const getTaskTypeName = (type: string) => {
  const names: Record<string, string> = {
    generate_script: 'AI文案生成',
    process_video: '视频处理',
    generate_cover: '封面生成',
    compliance_check: '违禁词检测',
    publish: '内容发布',
    ai_cover: 'AI封面生成',
    template_cover: '模板封面生成'
  }
  return names[type] || type
}

/**
 * 获取任务类型颜色
 */
const getTaskTypeColor = (type: string) => {
  const colors: Record<string, string> = {
    generate_script: 'primary',
    process_video: 'success',
    generate_cover: 'warning',
    compliance_check: 'danger',
    publish: 'info',
    ai_cover: 'primary',
    template_cover: 'warning'
  }
  return colors[type] || ''
}

/**
 * 获取状态名称
 */
const getStatusName = (status: string) => {
  const names: Record<string, string> = {
    pending: '待处理',
    processing: '处理中',
    completed: '已完成',
    failed: '失败',
    cancelled: '已取消'
  }
  return names[status] || status
}

/**
 * 获取状态颜色
 */
const getStatusColor = (status: string) => {
  const colors: Record<string, string> = {
    pending: 'info',
    processing: 'warning',
    completed: 'success',
    failed: 'danger',
    cancelled: ''
  }
  return colors[status] || ''
}

/**
 * 获取进度条状态
 */
const getProgressStatus = (status: string) => {
  const statusMap: Record<string, any> = {
    completed: 'success',
    failed: 'exception'
  }
  return statusMap[status] || undefined
}

/**
 * 获取平台名称
 */
const getPlatformName = (platform: string) => {
  const names: Record<string, string> = {
    toutiao: '今日头条',
    douyin: '抖音',
    kuaishou: '快手',
    wechat: '视频号',
    bilibili: 'B站',
    xiaohongshu: '小红书'
  }
  return names[platform] || platform
}

/**
 * 格式化时间
 */
const formatTime = (time: string) => {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

/**
 * 获取任务耗时
 */
const getDuration = (row: any) => {
  if (!row.created_at) return '-'
  
  const startTime = new Date(row.created_at).getTime()
  const endTime = row.completed_at 
    ? new Date(row.completed_at).getTime()
    : new Date().getTime()
  
  const duration = Math.floor((endTime - startTime) / 1000)
  
  if (duration < 60) {
    return `${duration}秒`
  } else if (duration < 3600) {
    return `${Math.floor(duration / 60)}分钟`
  } else {
    return `${Math.floor(duration / 3600)}小时`
  }
}

/**
 * 加载任务列表
 */
const loadTasks = async () => {
  loading.value = true
  try {
    const response = await apiClient.get(`${API_BASE_URL}/content/tasks`, {
      params: {
        page: currentPage.value,
        page_size: pageSize.value,
        ...filters.value
      }
    })

    if (response.data.status === 'success') {
      tasks.value = response.data.data.items || []
      total.value = response.data.data.total || 0
      statistics.value = response.data.data.statistics || {
        total: 0,
        processing: 0,
        completed: 0,
        failed: 0
      }
    } else {
      ElMessage.error('加载失败：' + (response.data.message || '未知错误'))
    }
  } catch (error: any) {
    console.error('加载任务列表失败:', error)
    ElMessage.error('加载失败，请检查后端服务')
  } finally {
    loading.value = false
  }
}

/**
 * 查看任务详情
 */
const handleViewDetail = async (task: any) => {
  try {
    const response = await apiClient.get(`${API_BASE_URL}/content/tasks/${task.id}`)
    
    if (response.data.status === 'success') {
      currentTask.value = response.data.data
      detailDialogVisible.value = true
    } else {
      ElMessage.error('获取任务详情失败')
    }
  } catch (error) {
    console.error('获取任务详情失败:', error)
    ElMessage.error('获取任务详情失败')
  }
}

/**
 * 关闭详情对话框
 */
const handleDetailClose = () => {
  detailDialogVisible.value = false
  currentTask.value = null
}

/**
 * 重试任务
 */
const handleRetry = async (task: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要重试任务 ${task.id} 吗？`,
      '确认重试',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    const response = await apiClient.post(`${API_BASE_URL}/content/tasks/${task.id}/retry`)
    
    if (response.data.status === 'success') {
      ElMessage.success('任务重试成功')
      loadTasks()
    } else {
      ElMessage.error('重试失败：' + (response.data.message || '未知错误'))
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('重试任务失败:', error)
      ElMessage.error('重试任务失败')
    }
  }
}

/**
 * 取消任务
 */
const handleCancel = async (task: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要取消任务 ${task.id} 吗？`,
      '确认取消',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    const response = await apiClient.post(`${API_BASE_URL}/content/tasks/${task.id}/cancel`)
    
    if (response.data.status === 'success') {
      ElMessage.success('任务已取消')
      loadTasks()
    } else {
      ElMessage.error('取消失败：' + (response.data.message || '未知错误'))
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('取消任务失败:', error)
      ElMessage.error('取消任务失败')
    }
  }
}

/**
 * 刷新任务列表
 */
const handleRefresh = () => {
  loadTasks()
}

/**
 * 筛选条件变化
 */
const handleFilterChange = () => {
  currentPage.value = 1
  loadTasks()
}

/**
 * 分页大小变化
 */
const handleSizeChange = () => {
  currentPage.value = 1
  loadTasks()
}

/**
 * 页码变化
 */
const handlePageChange = () => {
  loadTasks()
}

/**
 * 取消当前任务
 */
const handleCancelTask = async () => {
  if (currentTask.value) {
    await handleCancel(currentTask.value)
  }
}

/**
 * 重试当前任务
 */
const handleRetryTask = async () => {
  if (currentTask.value) {
    await handleRetry(currentTask.value)
  }
}

/**
 * 自动刷新任务列表
 */
const startAutoRefresh = () => {
  refreshTimer = setInterval(() => {
    if (!detailDialogVisible.value) {
      loadTasks()
    }
  }, 10000) // 每10秒刷新一次
}

/**
 * 停止自动刷新
 */
const stopAutoRefresh = () => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
}

onMounted(() => {
  loadTasks()
  startAutoRefresh()
})

onUnmounted(() => {
  stopAutoRefresh()
})
</script>

<style scoped>
.content-tasks {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
}

.stat-card {
  text-align: center;
  cursor: pointer;
  transition: transform 0.3s;
}

.stat-card:hover {
  transform: translateY(-5px);
}

.stat-item {
  padding: 15px 0;
}

.stat-label {
  color: #666;
  font-size: 14px;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #333;
}

.stat-value.primary {
  color: #409eff;
}

.stat-value.success {
  color: #67c23a;
}

.stat-value.danger {
  color: #f56c6c;
}

.content-box {
  max-height: 300px;
  overflow-y: auto;
  background: #f5f5f5;
  padding: 10px;
  border-radius: 4px;
  font-family: monospace;
  font-size: 12px;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-all;
}
</style>
