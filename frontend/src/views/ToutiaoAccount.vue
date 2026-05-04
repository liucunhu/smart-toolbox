<template>
  <div class="toutiao-account">
    <!-- 合规审查对话框 -->
    <ComplianceCheckDialog
      ref="complianceDialog"
      @retry="handleRetryCompliance"
      @modify="handleModifyContent"
      @confirm="handleConfirmPublish"
      @close="handleCloseCompliance"
    />
    
    <el-row :gutter="20">
      <!-- 左侧：登录区域 -->
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>📝 头条账号登录</span>
            </div>
          </template>
          
          <!-- 添加头条账号 -->
          <el-form :model="form" label-width="120px">
            <el-form-item label="手机号/邮箱">
              <el-input v-model="form.username" placeholder="请输入头条账号（手机号或邮箱）" />
            </el-form-item>
            
            <el-form-item label="密码">
              <el-input v-model="form.password" type="password" placeholder="请输入密码" show-password />
            </el-form-item>

            <el-form-item>
              <el-button type="primary" @click="handleLogin" :loading="loading">
                🔐 登录并保存Cookie
              </el-button>
              <el-tag type="success" style="margin-left: 10px;">
                ✨ 首次登录自动创建账号
              </el-tag>
            </el-form-item>
            
            <el-alert
              title="💡 提示"
              type="info"
              :closable="false"
              style="margin-top: 10px;"
            >
              <template #default>
                <div style="font-size: 12px;">
                  • 首次登录会自动创建账号记录<br/>
                  • 系统会打开浏览器，自动填充账号密码<br/>
                  • 登录成功后 Cookie 会自动保存
                </div>
              </template>
            </el-alert>
          </el-form>

          <!-- 登录状态 -->
          <div v-if="loginResult" class="result-area">
            <el-alert
              :title="loginResult.message || loginResult.error"
              :type="loginResult.status === 'success' ? 'success' : 'error'"
              :closable="false"
            />
          </div>
        </el-card>
      </el-col>

      <!-- 右侧：发布文章区域 -->
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>✍️ 发布头条文章</span>
              <el-tag v-if="isLoggedIn" type="success" size="small">已登录</el-tag>
              <el-tag v-else type="info" size="small">未登录</el-tag>
            </div>
          </template>

          <el-form :model="publishForm" label-width="100px">
            <el-form-item label="文章主题">
              <el-input 
                v-model="publishForm.topic" 
                placeholder="例如：Python自动化办公技巧"
                type="textarea"
                :rows="2"
              />
            </el-form-item>

            <el-form-item label="文章分类">
              <el-select v-model="publishForm.category" placeholder="请选择分类">
                <el-option label="科技" value="科技" />
                <el-option label="财经" value="财经" />
                <el-option label="娱乐" value="娱乐" />
                <el-option label="体育" value="体育" />
                <el-option label="生活" value="生活" />
                <el-option label="教育" value="教育" />
              </el-select>
            </el-form-item>

            <el-form-item label="封面图片">
              <el-upload
                action="#"
                :auto-upload="false"
                :on-change="handleCoverSelect"
                :limit="1"
                accept="image/*"
              >
                <el-button size="small">选择封面图</el-button>
                <template #tip>
                  <div class="el-upload__tip">支持jpg/png格式，建议尺寸16:9</div>
                </template>
              </el-upload>
              <div v-if="coverPreview" class="cover-preview">
                <img :src="coverPreview" alt="封面预览" style="max-width: 200px; border-radius: 4px;" />
              </div>
            </el-form-item>

            <el-form-item>
              <el-button 
                type="success" 
                @click="handleAutoPublish" 
                :loading="publishing"
                :disabled="!isLoggedIn"
              >
                🚀 一键发布（AI生成+自动发布）
              </el-button>
              <el-text type="info" size="small" style="margin-left: 10px;">
                AI会根据主题自动生成文章内容并发布
              </el-text>
            </el-form-item>
          </el-form>

          <!-- 发布结果 -->
          <div v-if="publishResult" class="result-area">
            <el-alert
              :title="publishResult.message || publishResult.error"
              :type="publishResult.status === 'success' ? 'success' : 'error'"
              :closable="false"
              show-icon
            >
              <template #default v-if="publishResult.status === 'success'">
                <div v-if="publishResult.data">
                  <p><strong>文章标题：</strong>{{ publishResult.data.title }}</p>
                  <p><strong>文章ID：</strong>{{ publishResult.data.article_id }}</p>
                  <p><strong>发布时间：</strong>{{ publishResult.data.publish_time }}</p>
                </div>
              </template>
            </el-alert>
          </div>

          <!-- 功能说明 -->
          <el-divider />
          <el-collapse>
            <el-collapse-item title="💡 功能说明" name="1">
              <el-text size="small">
                <p><strong>登录后可执行的操作：</strong></p>
                <ul>
                  <li>✅ 一键发布文章（AI自动生成内容）</li>
                  <li>✅ 手动发布文章（使用已有内容）</li>
                  <li>✅ 查看已发布的文章列表</li>
                  <li>✅ 查看文章数据分析（阅读量、点赞等）</li>
                  <li>✅ 管理多个头条账号</li>
                </ul>
                <p><strong>自动化流程：</strong></p>
                <ol>
                  <li>系统自动登录头条账号</li>
                  <li>AI根据主题生成文章内容</li>
                  <li>自动填写标题、内容、分类、标签</li>
                  <li>自动点击发布按钮</li>
                  <li>保存发布记录到数据库</li>
                </ol>
              </el-text>
            </el-collapse-item>
          </el-collapse>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from 'axios'
import ComplianceCheckDialog from '../components/ComplianceCheckDialog.vue'
import { checkContentCompliance, type ContentComplianceResponse } from '../api/compliance'

const loading = ref(false)
const publishing = ref(false)
const loginResult = ref<any>(null)
const publishResult = ref<any>(null)
const complianceDialog = ref<InstanceType<typeof ComplianceCheckDialog> | null>(null)

// 临时存储待发布的数据
const pendingPublishData = ref<{
  topic: string
  category: string
  coverImagePath?: string
} | null>(null)

// 当前登录的账号 ID
const currentAccountId = ref<number | null>(null)

const form = ref({
  username: '',
  password: ''
})

const publishForm = ref({
  topic: '',
  category: '科技'
})

const coverFile = ref<File | null>(null)
const coverPreview = ref<string>('')

const isLoggedIn = computed(() => {
  return loginResult.value?.status === 'success'
})

/**
 * 处理封面图选择
 */
const handleCoverSelect = (file: any) => {
  coverFile.value = file.raw
  const reader = new FileReader()
  reader.onload = (e) => {
    coverPreview.value = e.target?.result as string
  }
  reader.readAsDataURL(file.raw)
}

/**
 * 登录并保存Cookie
 */
const handleLogin = async () => {
  if (!form.value.username || !form.value.password) {
    ElMessage.warning('请输入账号和密码')
    return
  }

  loading.value = true
  try {
    const response = await axios.post(
      'http://localhost:8000/api/v1/accounts/toutiao/login',
      null,
      {
        params: {
          // account_id 可选，不提供则自动查找或创建
          username: form.value.username,
          password: form.value.password
        }
      }
    )

    if (response.data.status === 'success') {
      loginResult.value = response.data
      // 保存当前账号 ID
      currentAccountId.value = response.data.account_id || null
      ElMessage.success('✅ 登录成功！Cookie已保存')
      
      // 🆕 触发账号列表刷新（通过自定义事件）
      window.dispatchEvent(new CustomEvent('account-updated', {
        detail: {
          account_id: response.data.account_id,
          platform: 'toutiao'
        }
      }))
    } else {
      loginResult.value = response.data
      ElMessage.error('❌ 登录失败：' + (response.data.message || '未知错误'))
    }
  } catch (error: any) {
    console.error('登录失败:', error)
    loginResult.value = {
      status: 'error',
      error: error.response?.data?.detail || '登录失败，请检查后端服务'
    }
    ElMessage.error('❌ 登录失败：' + (error.response?.data?.detail || '请检查后端服务'))
  } finally {
    loading.value = false
  }
}

/**
 * 一键自动发布
 */
const handleAutoPublish = async () => {
  if (!publishForm.value.topic) {
    ElMessage.warning('请输入文章主题')
    return
  }

  // 步骤1: 显示加载状态
  complianceDialog.value?.showLoading()

  try {
    // 步骤2: 调用合规审查
    const complianceResult = await checkContentCompliance({
      title: publishForm.value.topic,
      content: `关于${publishForm.value.topic}的文章内容`,
      platform: 'toutiao'
    })
    
    // 步骤3: 显示结果
    complianceDialog.value?.hideLoading(complianceResult)
    
    if (complianceResult.passed) {
      // 审查通过，直接发布
      await executePublish()
    } else {
      // 审查失败，保存待发布数据
      pendingPublishData.value = { ...publishForm.value }
    }
  } catch (error: any) {
    console.error('合规审查失败:', error)
    complianceDialog.value?.hideLoading({
      passed: false,
      error: '合规审查服务异常，请稍后重试',
      violations: []
    })
  }
}

/**
 * 执行发布
 */
const executePublish = async () => {
  publishing.value = true
  try {
    const data = pendingPublishData.value || publishForm.value
    
    // 检查是否已登录
    if (!currentAccountId.value) {
      ElMessage.warning('请先登录头条账号')
      publishing.value = false
      return
    }
    
    const response = await axios.post(
      'http://localhost:8000/api/v1/content/toutiao/publish',
      null,
      {
        params: {
          account_id: currentAccountId.value,
          title: data.topic,
          content: `AI自动生成的关于${data.topic}的文章内容`,
          category: data.category,
          cover_image_path: data.coverImagePath,
          // 🆕 传递用户名密码，用于智能登录或自动创建账号
          username: form.value.username,
          password: form.value.password
        }
      }
    )
    
    if (response.data.status === 'success') {
      publishResult.value = response.data
      ElMessage.success('🎉 文章发布成功！')
      pendingPublishData.value = null
      publishForm.value.topic = ''
      coverFile.value = null
      coverPreview.value = ''
    } else {
      publishResult.value = response.data
      ElMessage.error('❌ 发布失败：' + (response.data.message || '未知错误'))
    }
  } catch (error: any) {
    console.error('发布失败:', error)
    publishResult.value = {
      status: 'error',
      error: error.response?.data?.detail || '发布失败，请检查后端服务'
    }
    ElMessage.error('❌ 发布失败：' + (error.response?.data?.detail || '请检查后端服务'))
  } finally {
    publishing.value = false
  }
}

/**
 * 重新检查合规性
 */
const handleRetryCompliance = () => {
  handleAutoPublish()
}

/**
 * 修改内容
 */
const handleModifyContent = () => {
  ElMessage.info('请修改文章内容后重新提交')
  complianceDialog.value?.showResult({
    passed: false,
    error: '请修改内容后重新检查',
    violations: []
  })
}

/**
 * 确认发布
 */
const handleConfirmPublish = () => {
  complianceDialog.value?.showResult({
    passed: true
  })
  setTimeout(() => {
    executePublish()
  }, 500)
}

/**
 * 关闭合规审查对话框
 */
const handleCloseCompliance = () => {
  // 清理逻辑
}
</script>

<style scoped lang="scss">
.toutiao-account {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.result-area {
  margin-top: 20px;
}

.cover-preview {
  margin-top: 10px;
}
</style>
