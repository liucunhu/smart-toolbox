<template>
  <div class="publish-records">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>📤 发布记录</span>
          <el-button type="primary" size="small" @click="fetchRecords" :loading="loading">
             刷新
          </el-button>
        </div>
      </template>

      <!-- 筛选条件 -->
      <el-form :inline="true" :model="filters" class="filter-form">
        <el-form-item label="平台">
          <el-select v-model="filters.platform" placeholder="全部平台" clearable style="width: 150px;">
            <el-option label="今日头条" value="toutiao" />
            <el-option label="抖音" value="douyin" />
            <el-option label="小红书" value="xiaohongshu" />
            <el-option label="B站" value="bilibili" />
            <el-option label="快手" value="kuaishou" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filters.status" placeholder="全部状态" clearable style="width: 120px;">
            <el-option label="已完成" value="completed" />
            <el-option label="处理中" value="processing" />
            <el-option label="待处理" value="pending" />
            <el-option label="失败" value="failed" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="fetchRecords">查询</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- 发布记录列表 -->
      <el-table :data="records" style="width: 100%" v-loading="loading">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="target_platform" label="平台" width="100">
          <template #default="{ row }">
            <el-tag :type="getPlatformType(row.target_platform)">
              {{ getPlatformName(row.target_platform) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="article_title" label="标题" min-width="250">
          <template #default="{ row }">
            <el-tooltip v-if="row.article_title" :content="row.article_title" placement="top">
              <span>{{ truncateText(row.article_title, 30) }}</span>
            </el-tooltip>
            <span v-else class="text-muted">{{ row.original_topic || '无标题' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="article_category" label="分类" width="100">
          <template #default="{ row }">
            {{ row.article_category || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="article_content_length" label="内容长度" width="100">
          <template #default="{ row }">
            {{ row.article_content_length ? `${row.article_content_length}字` : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="viewDetail(row)">
              详情
            </el-button>
            <!-- ✅ 失败的任务显示重新发布按钮 -->
            <el-button 
              v-if="row.status === 'failed'" 
              size="small" 
              type="danger" 
              link 
              @click="republish(row)"
              :loading="republishingId === row.id"
            >
              🔄 重新发布
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        :page-sizes="[10, 20, 50, 100]"
        :total="pagination.total"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="fetchRecords"
        @current-change="fetchRecords"
        style="margin-top: 20px; justify-content: flex-end;"
      />
    </el-card>

    <!-- 详情对话框 -->
    <el-dialog v-model="detailVisible" title="任务详情" width="70%">
      <el-descriptions :column="2" border v-if="currentTask">
        <el-descriptions-item label="任务 ID">{{ currentTask.task_id }}</el-descriptions-item>
        <el-descriptions-item label="平台">
          <el-tag :type="getPlatformType(currentTask.target_platform)">
            {{ getPlatformName(currentTask.target_platform) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="主题" :span="2">{{ currentTask.original_topic || '-' }}</el-descriptions-item>
        <el-descriptions-item label="标题" :span="2">{{ currentTask.article_title || '-' }}</el-descriptions-item>
        <el-descriptions-item label="分类">{{ currentTask.article_category || '-' }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="getStatusType(currentTask.status)">
            {{ getStatusText(currentTask.status) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="内容长度">{{ currentTask.article_content_length }} 字符</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ formatTime(currentTask.created_at) }}</el-descriptions-item>
        <el-descriptions-item label="标签" :span="2">
          <el-tag v-for="tag in (currentTask.tags || [])" :key="tag" style="margin-right: 5px;">
            {{ tag }}
          </el-tag>
          <span v-if="!currentTask.tags || currentTask.tags.length === 0">-</span>
        </el-descriptions-item>
      </el-descriptions>

      <el-divider content-position="left">文章内容预览</el-divider>
      <el-input
        v-if="currentArticleContent"
        v-model="currentArticleContent"
        type="textarea"
        :rows="10"
        readonly
      />
      <el-empty v-else description="无文章内容" />
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import apiClient from '../utils/api'
import { ElMessage } from 'element-plus'

const loading = ref(false)
const records = ref<any[]>([])
const detailVisible = ref(false)
const currentTask = ref<any>(null)
const currentArticleContent = ref('')
const republishingId = ref<number | null>(null)  // ✅ 重新发布中的任务ID

const filters = ref({
  platform: '',
  status: ''
})

const pagination = ref({
  page: 1,
  pageSize: 20,
  total: 0
})

const fetchRecords = async () => {
  loading.value = true
  try {
    const params: any = {
      skip: (pagination.value.page - 1) * pagination.value.pageSize,
      limit: pagination.value.pageSize
    }
    
    if (filters.value.platform) {
      params.platform = filters.value.platform
    }
    if (filters.value.status) {
      params.status = filters.value.status
    }

    const response = await apiClient.get('/content/tasks', { params })
    records.value = response.data.tasks
    pagination.value.total = response.data.total
  } catch (error) {
    console.error('获取发布记录失败:', error)
    ElMessage.error('获取发布记录失败')
  } finally {
    loading.value = false
  }
}

const resetFilters = () => {
  filters.value.platform = ''
  filters.value.status = ''
  pagination.value.page = 1
  fetchRecords()
}

const viewDetail = async (task: any) => {
  currentTask.value = task
  
  // 获取完整文章内容
  try {
    const response = await apiClient.get(`/content/tasks/${task.id}`)
    currentArticleContent.value = response.data.article_content || ''
  } catch (error) {
    console.error('获取文章详情失败:', error)
    currentArticleContent.value = ''
  }
  
  detailVisible.value = true
}

/**
 * ✅ 重新发布失败的任务
 */
const republish = async (task: any) => {
  if (!confirm(`确认要重新发布任务 "${task.article_title || task.original_topic}" 吗？`)) {
    return
  }
  
  republishingId.value = task.id
  
  try {
    // 获取任务详情
    const detailResponse = await apiClient.get(`/content/tasks/${task.id}`)
    const taskDetail = detailResponse.data
    
    // 调用头条自动发布接口
    const publishResponse = await apiClient.post(
      '/content/toutiao/auto_publish',
      null,
      {
        params: {
          account_id: taskDetail.account_id || 1,  // 使用默认账号或从任务中获取
          topic: taskDetail.original_topic,
          category: taskDetail.article_category || '科技',
          auto_generate_cover: true,  // 自动生成封面
          auto_generate_images: true,  // 自动生成配图
          num_images: 3,  // 生成3张配图
          use_template: false
        }
      }
    )
    
    if (publishResponse.data.status === 'success') {
      ElMessage.success('✅ 重新发布成功！')
      // 刷新列表
      fetchRecords()
    } else {
      ElMessage.error('❌ 重新发布失败：' + (publishResponse.data.error || '未知错误'))
    }
  } catch (error: any) {
    console.error('重新发布失败:', error)
    ElMessage.error('❌ 重新发布失败：' + (error.response?.data?.detail || '请检查后端服务'))
  } finally {
    republishingId.value = null
  }
}

const getPlatformType = (platform: string) => {
  const typeMap: any = {
    'toutiao': 'danger',
    'douyin': '',
    'xiaohongshu': 'danger',
    'bilibili': 'primary',
    'kuaishou': 'warning'
  }
  return typeMap[platform] || 'info'
}

const getPlatformName = (platform: string) => {
  const nameMap: any = {
    'toutiao': '今日头条',
    'douyin': '抖音',
    'xiaohongshu': '小红书',
    'bilibili': 'B站',
    'kuaishou': '快手'
  }
  return nameMap[platform] || platform
}

const getStatusType = (status: string) => {
  const typeMap: any = {
    'completed': 'success',
    'failed': 'danger',
    'processing': 'warning',
    'pending': 'info'
  }
  return typeMap[status] || 'info'
}

const getStatusText = (status: string) => {
  const textMap: any = {
    'completed': '已完成',
    'failed': '失败',
    'processing': '处理中',
    'pending': '待处理'
  }
  return textMap[status] || status
}

const truncateText = (text: string, maxLength: number) => {
  if (!text) return '-'
  return text.length > maxLength ? text.substring(0, maxLength) + '...' : text
}

const formatTime = (time: string | null) => {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

onMounted(() => {
  fetchRecords()
})
</script>

<style scoped>
.publish-records {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
}

.filter-form {
  margin-bottom: 20px;
}

.text-muted {
  color: #909399;
  font-style: italic;
}
</style>
