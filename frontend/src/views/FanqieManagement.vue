<template>
  <div class="fanqie-management">
    <el-row :gutter="20">
      <!-- 左侧：账号登录区域 -->
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>📚 番茄作家账号登录</span>
              <el-button size="small" @click="loadAccounts" :loading="loadingAccounts">
                🔄 刷新账号列表
              </el-button>
            </div>
          </template>
          
          <el-form :model="form" label-width="120px">
            <el-form-item label="选择账号">
              <el-select 
                v-model="selectedAccountId" 
                placeholder="请选择已保存的番茄账号"
                style="width: 100%;"
                @change="handleAccountSelect"
              >
                <el-option
                  v-for="account in savedAccounts"
                  :key="account.id"
                  :label="`${account.username} (ID: ${account.id})`"
                  :value="account.id"
                >
                  <span>{{ account.username }}</span>
                  <el-tag size="small" :type="account.has_cookies ? 'success' : 'warning'" style="margin-left: 8px;">
                    {{ account.has_cookies ? '✓ Cookie有效' : '⚠ 需重新登录' }}
                  </el-tag>
                </el-option>
              </el-select>
            </el-form-item>
            
            <el-divider>或添加新账号</el-divider>
            
            <el-form-item label="账号">
              <el-input v-model="form.username" placeholder="请输入番茄作家账号（手机号或邮箱）" />
            </el-form-item>
            
            <el-form-item label="密码">
              <el-input v-model="form.password" type="password" placeholder="请输入密码" show-password />
            </el-form-item>

            <el-form-item>
              <el-button type="primary" @click="handleLogin" :loading="loading">
                🔐 登录并保存Cookie
              </el-button>
            </el-form-item>
            
            <el-alert
              title="💡 提示"
              type="info"
              :closable="false"
              style="margin-top: 10px;"
            >
              <template #default>
                <div style="font-size: 12px;">
                  • 选择已保存的账号可直接登录<br/>
                  • 添加新账号：输入账号密码，首次登录自动创建记录<br/>
                  • 登录成功后 Cookie 会自动保存到数据库
                </div>
              </template>
            </el-alert>
          </el-form>

          <div v-if="loginResult" class="result-area">
            <el-alert
              :title="loginResult.message || loginResult.error"
              :type="loginResult.status === 'success' ? 'success' : 'error'"
              :closable="false"
            />
          </div>
        </el-card>
      </el-col>

      <!-- 右侧：小说管理区域 -->
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>📖 小说管理</span>
              <el-button type="primary" size="small" @click="showCreateNovelDialog = true">
                ➕ 创建新书
              </el-button>
            </div>
          </template>

          <el-table :data="novels" style="width: 100%" v-loading="loadingNovels">
            <el-table-column prop="title" label="书名" width="200" />
            <el-table-column prop="category" label="分类" width="100" />
            <el-table-column prop="total_chapters" label="章节数" width="100" />
            <el-table-column prop="total_words" label="总字数" width="100">
              <template #default="scope">
                {{ formatNumber(scope.row.total_words) }}
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="100">
              <template #default="scope">
                <el-tag :type="getStatusType(scope.row.status)">
                  {{ getStatusText(scope.row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作">
              <template #default="scope">
                <el-button size="small" @click="manageNovel(scope.row)">管理</el-button>
                <el-button size="small" type="primary" @click="publishChapter(scope.row)">发布章节</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <!-- 创建新书对话框 -->
    <el-dialog
      v-model="showCreateNovelDialog"
      title="创建新书"
      width="600px"
    >
      <el-form :model="novelForm" label-width="100px">
        <el-form-item label="小说标题" required>
          <el-input v-model="novelForm.title" placeholder="请输入小说标题" />
        </el-form-item>
        
        <el-form-item label="分类" required>
          <el-select v-model="novelForm.category" placeholder="请选择分类" style="width: 100%;">
            <el-option label="都市" value="都市" />
            <el-option label="玄幻" value="玄幻" />
            <el-option label="仙侠" value="仙侠" />
            <el-option label="历史" value="历史" />
            <el-option label="科幻" value="科幻" />
            <el-option label="游戏" value="游戏" />
            <el-option label="悬疑" value="悬疑" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="标签">
          <el-select
            v-model="novelForm.tags"
            multiple
            filterable
            allow-create
            default-first-option
            placeholder="请输入标签（最多5个）"
            style="width: 100%;"
          >
            <el-option
              v-for="tag in commonTags"
              :key="tag"
              :label="tag"
              :value="tag"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="简介">
          <el-input
            v-model="novelForm.introduction"
            type="textarea"
            :rows="4"
            placeholder="请输入小说简介"
          />
        </el-form-item>
        
        <el-form-item label="封面图">
          <el-upload
            class="cover-uploader"
            action="#"
            :auto-upload="false"
            :on-change="handleCoverChange"
            :show-file-list="false"
            accept="image/*"
          >
            <img v-if="coverPreview" :src="coverPreview" class="cover-preview" />
            <el-icon v-else class="cover-uploader-icon"><Plus /></el-icon>
          </el-upload>
          <div style="font-size: 12px; color: #909399; margin-top: 5px;">
            建议尺寸：600x800像素，支持JPG、PNG格式
          </div>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showCreateNovelDialog = false">取消</el-button>
        <el-button type="primary" @click="handleCreateNovel" :loading="creating">
          创建
        </el-button>
      </template>
    </el-dialog>

    <!-- 发布章节对话框 -->
    <el-dialog
      v-model="showPublishDialog"
      title="发布章节"
      width="800px"
    >
      <el-form :model="chapterForm" label-width="100px">
        <el-form-item label="章节标题" required>
          <el-input v-model="chapterForm.title" placeholder="请输入章节标题" />
        </el-form-item>
        
        <el-form-item label="章节内容" required>
          <el-input
            v-model="chapterForm.content"
            type="textarea"
            :rows="15"
            placeholder="请输入章节内容（建议2000-3000字）"
          />
          <div style="font-size: 12px; color: #909399; margin-top: 5px;">
            当前字数：{{ chapterForm.content.length }}
          </div>
        </el-form-item>
        
        <el-form-item label="定时发布">
          <el-switch v-model="useScheduledTime" />
          <el-date-picker
            v-if="useScheduledTime"
            v-model="chapterForm.scheduled_time"
            type="datetime"
            placeholder="选择发布时间"
            style="margin-left: 10px; width: 250px;"
          />
        </el-form-item>
        
        <el-divider />
        
        <el-form-item label="AI辅助">
          <el-button @click="generateChapterWithAI" :loading="generating">
            ✨ AI生成章节内容
          </el-button>
          <el-button @click="batchGenerateChapters" :loading="batchGenerating">
            📝 批量生成草稿
          </el-button>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showPublishDialog = false">取消</el-button>
        <el-button type="primary" @click="handlePublishChapter" :loading="publishing">
          {{ useScheduledTime ? '定时发布' : '立即发布' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 数据分析对话框 -->
    <el-dialog
      v-model="showAnalyticsDialog"
      title="📊 数据分析"
      width="900px"
    >
      <el-tabs v-model="activeTab">
        <el-tab-pane label="阅读数据" name="reads">
          <el-row :gutter="20">
            <el-col :span="8">
              <el-statistic title="日阅读量" :value="analytics.daily_reads || 0" />
            </el-col>
            <el-col :span="8">
              <el-statistic title="新增关注" :value="analytics.new_followers || 0" />
            </el-col>
            <el-col :span="8">
              <el-statistic title="新增书架" :value="analytics.new_favorites || 0" />
            </el-col>
          </el-row>
        </el-tab-pane>
        
        <el-tab-pane label="收益数据" name="income">
          <el-row :gutter="20">
            <el-col :span="8">
              <el-statistic title="日收益" :value="analytics.daily_ad_revenue || 0" prefix="¥" />
            </el-col>
            <el-col :span="8">
              <el-statistic title="月收益" :value="currentAccount?.monthly_income || 0" prefix="¥" />
            </el-col>
            <el-col :span="8">
              <el-statistic title="总收益" :value="currentAccount?.total_income || 0" prefix="¥" />
            </el-col>
          </el-row>
        </el-tab-pane>
        
        <el-tab-pane label="质量指标" name="quality">
          <el-row :gutter="20">
            <el-col :span="8">
              <el-statistic title="完读率" :value="(analytics.completion_rate || 0) * 100" suffix="%" />
            </el-col>
            <el-col :span="8">
              <el-statistic title="次日留存" :value="(analytics.retention_rate_day1 || 0) * 100" suffix="%" />
            </el-col>
            <el-col :span="8">
              <el-statistic title="7日留存" :value="(analytics.retention_rate_day7 || 0) * 100" suffix="%" />
            </el-col>
          </el-row>
        </el-tab-pane>
      </el-tabs>
      
      <template #footer>
        <el-button @click="showAnalyticsDialog = false">关闭</el-button>
        <el-button type="primary" @click="refreshAnalytics" :loading="fetchingAnalytics">
          🔄 刷新数据
        </el-button>
      </template>
    </el-dialog>

    <!-- 断更预警对话框 -->
    <el-dialog
      v-model="showWarningsDialog"
      title="⚠️ 断更预警"
      width="700px"
    >
      <el-table :data="warnings" style="width: 100%">
        <el-table-column prop="novel_title" label="小说名称" />
        <el-table-column prop="days_since_update" label="断更天数" width="120">
          <template #default="scope">
            <el-tag :type="scope.row.severity === 'critical' ? 'danger' : 'warning'">
              {{ scope.row.days_since_update }}天
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="last_update" label="最后更新" width="180">
          <template #default="scope">
            {{ formatDate(scope.row.last_update) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120">
          <template #default="scope">
            <el-button size="small" @click="quickPublish(scope.row.novel_id)">快速发布</el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <template #footer>
        <el-button @click="showWarningsDialog = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import axios from 'axios'

const API_BASE_URL = 'http://localhost:8000/api/v1'

// 账号相关
const loadingAccounts = ref(false)
const savedAccounts = ref([])
const selectedAccountId = ref(null)
const form = ref({
  username: '',
  password: ''
})
const loading = ref(false)
const loginResult = ref(null)

// 小说相关
const loadingNovels = ref(false)
const novels = ref([])
const showCreateNovelDialog = ref(false)
const creating = ref(false)
const novelForm = ref({
  title: '',
  category: '',
  tags: [],
  introduction: '',
  cover_image_path: null
})
const coverPreview = ref('')
const commonTags = ['爽文', '系统', '重生', '穿越', '无敌', '扮猪吃虎', '打脸', '热血']

// 章节发布相关
const showPublishDialog = ref(false)
const publishing = ref(false)
const generating = ref(false)
const batchGenerating = ref(false)
const useScheduledTime = ref(false)
const currentNovel = ref(null)
const chapterForm = ref({
  chapter_number: 1,
  title: '',
  content: '',
  scheduled_time: null
})

// 数据分析相关
const showAnalyticsDialog = ref(false)
const fetchingAnalytics = ref(false)
const activeTab = ref('reads')
const analytics = ref<any>({})

// 断更预警相关
const showWarningsDialog = ref(false)
const warnings = ref([])

// 加载账号列表
const loadAccounts = async () => {
  loadingAccounts.value = true
  try {
    const response = await axios.get(`${API_BASE_URL}/accounts/list`, {
      params: { platform: 'fanqie' }
    })
    savedAccounts.value = response.data.data.items
  } catch (error) {
    console.error('加载账号失败:', error)
    ElMessage.error('加载账号失败')
  } finally {
    loadingAccounts.value = false
  }
}

// 选择账号
const handleAccountSelect = (accountId: number) => {
  const account = savedAccounts.value.find(a => a.id === accountId)
  if (account) {
    form.value.username = account.username
  }
}

// 登录
const handleLogin = async () => {
  if (!form.value.username || !form.value.password) {
    ElMessage.warning('请输入账号和密码')
    return
  }
  
  loading.value = true
  loginResult.value = null
  
  try {
    const response = await axios.post(`${API_BASE_URL}/accounts/fanqie/login`, null, {
      params: {
        username: form.value.username,
        password: form.value.password
      }
    })
    
    if (response.data.status === 'success') {
      loginResult.value = {
        status: 'success',
        message: response.data.message
      }
      ElMessage.success('登录成功')
      loadAccounts()
      loadNovels()
    } else {
      loginResult.value = {
        status: 'error',
        error: response.data.message
      }
    }
  } catch (error: any) {
    loginResult.value = {
      status: 'error',
      error: error.response?.data?.detail || '登录失败'
    }
  } finally {
    loading.value = false
  }
}

// 加载小说列表
const loadNovels = async () => {
  if (!selectedAccountId.value) return
  
  loadingNovels.value = true
  try {
    const response = await axios.get(`${API_BASE_URL}/content/fanqie/novels/${selectedAccountId.value}`)
    novels.value = response.data.data
  } catch (error) {
    console.error('加载小说失败:', error)
  } finally {
    loadingNovels.value = false
  }
}

// 创建新书
const handleCreateNovel = async () => {
  if (!novelForm.value.title || !novelForm.value.category) {
    ElMessage.warning('请填写必填项')
    return
  }
  
  if (!selectedAccountId.value) {
    ElMessage.warning('请先选择账号')
    return
  }
  
  creating.value = true
  try {
    const response = await axios.post(`${API_BASE_URL}/content/fanqie/create_novel`, null, {
      params: {
        account_id: selectedAccountId.value,
        title: novelForm.value.title,
        category: novelForm.value.category,
        tags: JSON.stringify(novelForm.value.tags),
        introduction: novelForm.value.introduction,
        cover_image_path: novelForm.value.cover_image_path
      }
    })
    
    if (response.data.status === 'success') {
      ElMessage.success('小说创建成功')
      showCreateNovelDialog.value = false
      resetNovelForm()
      loadNovels()
    }
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '创建失败')
  } finally {
    creating.value = false
  }
}

// 处理封面图上传
const handleCoverChange = (file: any) => {
  const reader = new FileReader()
  reader.onload = (e: any) => {
    coverPreview.value = e.target.result
    // 这里需要实现实际的上传逻辑
    novelForm.value.cover_image_path = e.target.result
  }
  reader.readAsDataURL(file.raw)
}

// 重置小说表单
const resetNovelForm = () => {
  novelForm.value = {
    title: '',
    category: '',
    tags: [],
    introduction: '',
    cover_image_path: null
  }
  coverPreview.value = ''
}

// 管理小说
const manageNovel = (novel: any) => {
  ElMessage.info(`管理小说：${novel.title}`)
  // TODO: 跳转到小说详情页
}

// 发布章节
const publishChapter = (novel: any) => {
  currentNovel.value = novel
  chapterForm.value.chapter_number = novel.total_chapters + 1
  showPublishDialog.value = true
}

// 发布章节
const handlePublishChapter = async () => {
  if (!chapterForm.value.title || !chapterForm.value.content) {
    ElMessage.warning('请填写章节标题和内容')
    return
  }
  
  publishing.value = true
  try {
    const response = await axios.post(`${API_BASE_URL}/content/fanqie/publish_chapter`, null, {
      params: {
        novel_id: currentNovel.value.id,
        chapter_number: chapterForm.value.chapter_number,
        title: chapterForm.value.title,
        content: chapterForm.value.content,
        scheduled_time: useScheduledTime.value && chapterForm.value.scheduled_time 
          ? chapterForm.value.scheduled_time.toISOString() 
          : null
      }
    })
    
    if (response.data.status === 'success') {
      ElMessage.success('章节发布成功')
      showPublishDialog.value = false
      resetChapterForm()
      loadNovels()
    }
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '发布失败')
  } finally {
    publishing.value = false
  }
}

// AI生成章节内容
const generateChapterWithAI = async () => {
  if (!currentNovel.value) {
    ElMessage.warning('请先选择小说')
    return
  }
  
  generating.value = true
  try {
    const response = await axios.post(`${API_BASE_URL}/content/fanqie/auto_publish`, null, {
      params: {
        novel_id: currentNovel.value.id,
        topic: '继续故事情节',
        use_ai_content: true
      }
    })
    
    if (response.data.status === 'success') {
      chapterForm.value.title = response.data.title
      chapterForm.value.content = response.data.content || ''
      ElMessage.success('AI生成成功，请检查并修改内容')
    }
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || 'AI生成失败')
  } finally {
    generating.value = false
  }
}

// 批量生成草稿
const batchGenerateChapters = async () => {
  if (!currentNovel.value) {
    ElMessage.warning('请先选择小说')
    return
  }
  
  batchGenerating.value = true
  try {
    const response = await axios.post(`${API_BASE_URL}/content/fanqie/batch_generate`, null, {
      params: {
        novel_id: currentNovel.value.id,
        chapter_count: 5,
        start_chapter: currentNovel.value.total_chapters + 1
      }
    })
    
    if (response.data.status === 'success') {
      ElMessage.success(`批量生成${response.data.chapters.length}章完成，请在草稿箱查看`)
      showPublishDialog.value = false
      loadNovels()
    }
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '批量生成失败')
  } finally {
    batchGenerating.value = false
  }
}

// 重置章节表单
const resetChapterForm = () => {
  chapterForm.value = {
    chapter_number: 1,
    title: '',
    content: '',
    scheduled_time: null
  }
  useScheduledTime.value = false
}

// 刷新数据分析
const refreshAnalytics = async () => {
  if (!currentNovel.value) return
  
  fetchingAnalytics.value = true
  try {
    const response = await axios.get(`${API_BASE_URL}/content/fanqie/analytics/${currentNovel.value.id}`, {
      params: { days: 7 }
    })
    
    if (response.data.status === 'success') {
      analytics.value = response.data.data
      ElMessage.success('数据刷新成功')
    }
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '数据刷新失败')
  } finally {
    fetchingAnalytics.value = false
  }
}

// 加载断更预警
const loadWarnings = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/content/fanqie/warnings`)
    
    if (response.data.status === 'success') {
      warnings.value = response.data.warnings
    }
  } catch (error: any) {
    console.error('加载预警失败:', error)
  }
}

// 快速发布
const quickPublish = (novelId: number) => {
  const novel = novels.value.find(n => n.id === novelId)
  if (novel) {
    publishChapter(novel)
    showWarningsDialog.value = false
  }
}

// 格式化日期
const formatDate = (dateStr: string) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN')
}

// 格式化数字
const formatNumber = (num: number) => {
  if (num >= 10000) {
    return (num / 10000).toFixed(1) + '万'
  }
  return num.toString()
}

// 获取状态类型
const getStatusType = (status: string) => {
  const map: Record<string, string> = {
    draft: 'info',
    published: 'success',
    ongoing: 'primary',
    completed: 'warning'
  }
  return map[status] || 'info'
}

// 获取状态文本
const getStatusText = (status: string) => {
  const map: Record<string, string> = {
    draft: '草稿',
    published: '已发布',
    ongoing: '连载中',
    completed: '已完结'
  }
  return map[status] || status
}

onMounted(() => {
  loadAccounts()
  loadWarnings()
})
</script>

<style scoped>
.fanqie-management {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
}

.result-area {
  margin-top: 20px;
}

.cover-uploader {
  border: 1px dashed #d9d9d9;
  border-radius: 6px;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  width: 150px;
  height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.cover-uploader:hover {
  border-color: #409EFF;
}

.cover-preview {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.cover-uploader-icon {
  font-size: 28px;
  color: #8c939d;
}
</style>
