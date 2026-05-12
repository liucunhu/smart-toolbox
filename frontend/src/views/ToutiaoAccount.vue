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
              <el-button size="small" @click="loadAccounts" :loading="loadingAccounts">
                🔄 刷新账号列表
              </el-button>
            </div>
          </template>
          
          <!-- 账号选择器 -->
          <el-form :model="form" label-width="120px">
            <el-form-item label="选择账号">
              <el-select 
                v-model="selectedAccountId" 
                placeholder="请选择已保存的账号"
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
              <div style="font-size: 12px; color: #909399; margin-top: 5px;">
                💡 选择已保存的账号可直接登录，无需输入密码
              </div>
            </el-form-item>
            
            <el-divider>或添加新账号</el-divider>
            
            <el-form-item label="手机号/邮箱">
              <el-input v-model="form.username" placeholder="请输入新的头条账号（手机号或邮箱）" />
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
                  • 选择已保存的账号：直接登录（使用Cookie或数据库密码）<br/>
                  • 添加新账号：输入账号密码，首次登录自动创建记录<br/>
                  • 登录成功后 Cookie 会自动保存到数据库<br/>
                  • 支持多账号切换，方便管理多个头条号
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
                placeholder="输入主题，留空则自动推荐热门话题"
                type="textarea"
                :rows="2"
                clearable
              >
                <template #suffix>
                  <el-button 
                    link 
                    type="primary" 
                    @click="loadRecommendedTopics" 
                    :loading="loadingTopics"
                    style="padding: 0 5px;"
                  >
                    🔥 获取推荐
                  </el-button>
                </template>
              </el-input>
              <el-text size="small" type="info" style="margin-top: 5px; display: block;">
                💡 留空将自动根据热搜和历史数据推荐最可能火的主题
              </el-text>
            </el-form-item>

            <!-- 🌟 推荐主题列表 -->
            <el-card 
              v-if="recommendedTopics.length > 0" 
              shadow="never" 
              style="margin-bottom: 15px; border: 2px solid #409EFF; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;"
            >
              <template #header>
                <div style="display: flex; justify-content: space-between; align-items: center;">
                  <span style="font-weight: bold; font-size: 16px;">🔥 智能推荐主题</span>
                  <el-tag type="success" size="small">AI驱动</el-tag>
                </div>
              </template>
              <div 
                v-for="(topic, index) in recommendedTopics" 
                :key="index"
                class="recommendation-item"
                @click="selectRecommendedTopic(topic)"
                style="cursor: pointer; padding: 10px; margin-bottom: 8px; background: rgba(255, 255, 255, 0.1); border-radius: 6px; transition: all 0.3s;"
                @mouseenter="$event.currentTarget.style.background = 'rgba(255, 255, 255, 0.2)'"
                @mouseleave="$event.currentTarget.style.background = 'rgba(255, 255, 255, 0.1)'"
              >
                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 5px;">
                  <el-tag :type="getConfidenceType(topic.confidence)" size="small" effect="dark">
                    {{ (topic.confidence * 100).toFixed(0) }}%
                  </el-tag>
                  <span style="font-weight: bold; font-size: 14px; flex: 1;">{{ topic.topic }}</span>
                </div>
                <div style="font-size: 12px; opacity: 0.9; display: flex; align-items: center; gap: 5px;">
                  <el-icon><InfoFilled /></el-icon>
                  {{ topic.reason }}
                </div>
              </div>
              <div style="text-align: center; margin-top: 10px; font-size: 12px; opacity: 0.8;">
                💡 点击任一主题可快速开始创作
              </div>
            </el-card>

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

            <el-form-item label="作品声明">
              <el-checkbox-group v-model="publishForm.declarations">
                <el-checkbox value="引用ai"> 引用ai</el-checkbox>
                <el-checkbox value="取材网络">🌐 取材网络</el-checkbox>
                <el-checkbox value="引用站内">📑 引用站内</el-checkbox>
                <el-checkbox value="个人观点">💭 个人观点，仅供参考</el-checkbox>
                <el-checkbox value="虚构演绎">🎭 虚构演绎，故事经历</el-checkbox>
                <el-checkbox value="投资观点"> 投资观点，仅供参考</el-checkbox>
                <el-checkbox value="健康医疗"> 健康医疗分享，仅供参考</el-checkbox>
              </el-checkbox-group>
              <div style="font-size: 12px; color: #909399; margin-top: 5px;">
                 请根据文章内容勾选相应的声明选项（可多选）
              </div>
            </el-form-item>

            <el-form-item label="封面图片">
              <el-checkbox v-model="publishForm.enableCover" style="margin-bottom: 10px;">
                ️ 启用封面图
              </el-checkbox>
              
              <div v-if="publishForm.enableCover">
                <el-radio-group v-model="publishForm.coverType" style="margin-bottom: 10px;">
                  <el-radio value="auto">🤖 AI自动生成</el-radio>
                  <el-radio value="upload">📁 上传自定义</el-radio>
                </el-radio-group>
                
                <!-- AI自动生成选项 -->
                <div v-if="publishForm.coverType === 'auto'">
                  <el-select v-model="publishForm.coverStyle" placeholder="选择封面风格" style="width: 100%;">
                    <el-option label="现代科技风格" value="modern" />
                    <el-option label="极简风格" value="minimal" />
                    <el-option label="大胆风格" value="bold" />
                  </el-select>
                  <div style="font-size: 12px; color: #909399; margin-top: 5px;">
                     AI会根据标题自动生成16:9比例的封面图
                  </div>
                </div>
                
                <!-- 上传自定义选项 -->
                <div v-if="publishForm.coverType === 'upload'">
                  <el-upload
                    action="#"
                    :auto-upload="false"
                    :on-change="handleCoverSelect"
                    :limit="1"
                    accept="image/*"
                  >
                    <el-button size="small">选择封面图</el-button>
                    <template #tip>
                      <div class="el-upload__tip">支持jpg/png格式，建议尺寸16:9（1280x720）</div>
                    </template>
                  </el-upload>
                  <div v-if="coverPreview" class="cover-preview">
                    <img :src="coverPreview" alt="封面预览" style="max-width: 200px; border-radius: 4px;" />
                  </div>
                </div>
              </div>
              
              <div v-else style="font-size: 12px; color: #909399;">
                ℹ️ 不启用封面图，发布时将使用头条默认封面
              </div>
            </el-form-item>

            <el-form-item label="文章配图">
              <el-checkbox v-model="publishForm.enableImages" style="margin-bottom: 10px;">
                ☑️ 启用文章配图
              </el-checkbox>
              
              <div v-if="publishForm.enableImages">
                <!-- 配图来源选择 -->
                <el-radio-group v-model="publishForm.imageSourceType" style="margin-bottom: 10px;">
                  <el-radio value="ai">🤖 AI自动生成</el-radio>
                  <el-radio value="upload">📁 上传自定义</el-radio>
                </el-radio-group>
                
                <!-- AI自动生成选项 -->
                <div v-if="publishForm.imageSourceType === 'ai'">
                  <el-form-item label="生成数量" label-width="80px">
                    <el-input-number v-model="publishForm.numImages" :min="1" :max="9" style="width: 100%;" />
                  </el-form-item>
                  <div style="font-size: 12px; color: #909399; margin-top: 5px;">
                    💡 AI会根据文章内容自动生成配图，增强视觉效果
                  </div>
                </div>
                
                <!-- 上传自定义选项 -->
                <div v-if="publishForm.imageSourceType === 'upload'">
                  <el-upload
                    action="#"
                    :auto-upload="false"
                    :on-change="handleImageSelect"
                    :limit="9"
                    accept="image/*"
                    multiple
                    list-type="picture-card"
                  >
                    <el-icon><Plus /></el-icon>
                    <template #tip>
                      <div class="el-upload__tip">最多上传9张图片，支持jpg/png格式</div>
                    </template>
                  </el-upload>
                  <div style="font-size: 12px; color: #909399; margin-top: 5px;">
                    💡 配图将插入到文章内容中，增强视觉效果
                  </div>
                </div>
              </div>
              
              <div v-else style="font-size: 12px; color: #909399;">
                ℹ️ 不启用配图，文章将只包含文字内容
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
                AI会根据主题自动生成文章内容、封面图并发布
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
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, InfoFilled } from '@element-plus/icons-vue'
import apiClient from '../utils/api'
import ComplianceCheckDialog from '../components/ComplianceCheckDialog.vue'
import { checkContentCompliance, type ContentComplianceResponse } from '../api/compliance'

const loading = ref(false)
const loadingAccounts = ref(false)  // ✅ 加载账号列表的状态
const publishing = ref(false)
const loginResult = ref<any>(null)
const publishResult = ref<any>(null)
const complianceDialog = ref<InstanceType<typeof ComplianceCheckDialog> | null>(null)
const selectedAccountId = ref<number | null>(null)  // ✅ 选中的账号ID

// ✅ 已保存的头条账号列表
interface SavedAccount {
  id: number
  username: string
  has_password: boolean
  has_cookies: boolean
  status: string
}
const savedAccounts = ref<SavedAccount[]>([])

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
  category: '科技',
  declarations: [] as string[],  // ✅ 作品声明（多选）
  enableCover: true,  // ✅ 是否启用封面图
  coverType: 'auto' as 'auto' | 'upload',  // ✅ 封面类型：AI自动生成或上传自定义
  coverStyle: 'modern',  // ✅ AI封面风格
  enableImages: false,  // ✅ 是否启用文章配图
  imageSourceType: 'ai' as 'ai' | 'upload',  // ✅ 配图来源：AI生成或上传
  numImages: 2  // ✅ AI生成配图数量
})

const coverFile = ref<File | null>(null)
const coverPreview = ref<string>('')

// ✅ 文章配图相关
const imageFiles = ref<File[]>([])
const imagePreviews = ref<string[]>([])

// 🌟 推荐主题相关
const recommendedTopics = ref<any[]>([])
const loadingTopics = ref(false)

const isLoggedIn = computed(() => {
  return loginResult.value?.status === 'success'
})

/**
 * ✅ 加载已保存的头条账号列表
 */
const loadAccounts = async () => {
  loadingAccounts.value = true
  try {
    // ✅ 修复：使用正确的 API 路径和参数名
    const response = await apiClient.get('/accounts/list', {
      params: {
        platform: 'toutiao',
        page: 1,
        page_size: 100
      }
    })
    
    // ✅ 修复：解析正确的响应数据结构
    if (response.data.status === 'success' && response.data.data) {
      const accounts = response.data.data.items || []
      savedAccounts.value = accounts.map((account: any) => ({
        id: account.id,
        username: account.username,
        has_password: account.has_password,
        has_cookies: account.has_cookies,
        status: account.status
      }))
      
      ElMessage.success(`✅ 已加载 ${savedAccounts.value.length} 个头条账号`)
    }
  } catch (error: any) {
    console.error('加载账号列表失败:', error)
    ElMessage.error('❌ 加载账号列表失败')
  } finally {
    loadingAccounts.value = false
  }
}

/**
 * ✅ 选择账号并自动登录
 */
const handleAccountSelect = async (accountId: number) => {
  if (!accountId) return
  
  loading.value = true
  try {
    // 使用账号ID直接登录，后端会自动使用数据库中的密码
    const response = await apiClient.post(
      '/accounts/toutiao/login',
      null,
      {
        params: {
          account_id: accountId
          // 不传入 username 和 password，后端会从数据库获取
        }
      }
    )

    if (response.data.status === 'success') {
      loginResult.value = response.data
      currentAccountId.value = response.data.account_id || null
      ElMessage.success(`✅ 账号 ${response.data.username} 登录成功！`)
      
      // 触发账号列表刷新
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
 * ✅ 处理配图选择
 */
const handleImageSelect = (file: any, fileList: any[]) => {
  if (file.raw) {
    imageFiles.value.push(file.raw)
    const reader = new FileReader()
    reader.onload = (e) => {
      imagePreviews.value.push(e.target?.result as string)
    }
    reader.readAsDataURL(file.raw)
  }
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
    const response = await apiClient.post(
      '/accounts/toutiao/login',
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

  // 检查是否已登录
  if (!currentAccountId.value) {
    ElMessage.warning('请先登录头条账号')
    return
  }

  publishing.value = true
  try {
    // ✅ 先上传文章配图（如果启用）
    let uploadedImagePaths: string[] = []
    if (publishForm.value.enableImages && imageFiles.value.length > 0) {
      ElMessage.info(`正在上传 ${imageFiles.value.length} 张配图...`)
        
      for (const imgFile of imageFiles.value) {
        const formData = new FormData()
        formData.append('file', imgFile)
          
        const uploadResponse = await apiClient.post(
          '/content/upload-image',
          formData,
          { headers: { 'Content-Type': 'multipart/form-data' } }
        )
          
        if (uploadResponse.data.status === 'success') {
          uploadedImagePaths.push(uploadResponse.data.file_path)
        }
      }
        
      ElMessage.success(`✅ 配图上传完成！`)
    }
      
    // ✅ 处理封面图逻辑
    let coverImagePath: string | null = null
    let autoGenerateCover = false
      
    if (publishForm.value.enableCover) {
      if (publishForm.value.coverType === 'upload' && coverFile.value) {
        // 上传自定义封面
        ElMessage.info('正在上传封面图...')
        const formData = new FormData()
        formData.append('file', coverFile.value)
          
        const uploadResponse = await apiClient.post(
          '/content/upload-image',
          formData,
          { headers: { 'Content-Type': 'multipart/form-data' } }
        )
          
        if (uploadResponse.data.status === 'success') {
          coverImagePath = uploadResponse.data.file_path
          ElMessage.success('✅ 封面图上传完成！')
        }
      } else if (publishForm.value.coverType === 'auto') {
        // AI自动生成封面
        autoGenerateCover = true
      }
    }
      
    // ✅ 调用一键全自动发布接口（包含AI生成文章+封面图）
    const response = await apiClient.post(
      '/content/toutiao/auto_publish',
      null,
      {
        params: {
          account_id: currentAccountId.value,
          topic: publishForm.value.topic,
          // ✅ 不再传入 username 和 password，后端会自动从数据库中获取
          category: publishForm.value.category,
          cover_image_path: coverImagePath,
          auto_generate_cover: autoGenerateCover,  // ✅ 根据用户选择决定是否生成
          cover_style: publishForm.value.coverStyle,  // ✅ 使用用户选择的风格
          use_cdp: false,             // ⚠️ CDP模式不可用，使用标准模式
          cdp_port: 9222,             // 保留参数以兼容
          declarations: JSON.stringify(publishForm.value.declarations),  // ✅ 使用用户选择的声明（多选）
          article_images: uploadedImagePaths,  // ✅ 传递配图路径列表（用户上传时）
          auto_generate_images: publishForm.value.enableImages && publishForm.value.imageSourceType === 'ai',  // ✅ AI自动生成配图
          num_images: publishForm.value.numImages  // ✅ 生成配图数量
        }
      }
    )
      
    if (response.data.status === 'success') {
      publishResult.value = response.data
      ElMessage.success(`🎉 文章发布成功！\n标题：${response.data.article_title}`)
        
      // 清空表单
      publishForm.value.topic = ''
      coverFile.value = null
      coverPreview.value = ''
      imageFiles.value = []
      imagePreviews.value = []
    } else {
      publishResult.value = response.data
      ElMessage.error('❌ 发布失败：' + (response.data.error || response.data.message || '未知错误'))
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
  ElMessage.info('请修改内容后重新提交')
}

/**
 * 确认发布
 */
const handleConfirmPublish = () => {
  ElMessage.success('确认发布')
}

/**
 * 关闭合规审查对话框
 */
const handleCloseCompliance = () => {
  // 清理逻辑
}

/**
 * ✅ 页面加载时自动加载账号列表
 */
onMounted(() => {
  loadAccounts()
})

/**
 * 🌟 加载推荐主题
 */
const loadRecommendedTopics = async () => {
  if (!currentAccountId.value) {
    ElMessage.warning('请先登录账号')
    return
  }
  
  loadingTopics.value = true
  try {
    const response = await apiClient.get('/content/recommended-topics', {
      params: {
        account_id: currentAccountId.value,
        count: 5
      }
    })
    
    if (response.data.status === 'success') {
      recommendedTopics.value = response.data.recommendations || []
      
      if (recommendedTopics.value.length > 0) {
        ElMessage.success(`✅ 获取到 ${recommendedTopics.value.length} 个推荐主题`)
      } else {
        ElMessage.info('ℹ️  暂无推荐主题，请稍后重试')
      }
    } else {
      ElMessage.error('❌ 获取推荐失败')
    }
  } catch (error: any) {
    console.error('获取推荐主题失败:', error)
    ElMessage.error('❌ 获取推荐失败：' + (error.response?.data?.detail || error.message))
  } finally {
    loadingTopics.value = false
  }
}

/**
 * 🌟 选择推荐主题
 */
const selectRecommendedTopic = (topic: any) => {
  publishForm.value.topic = topic.topic
  ElMessage.success(`✅ 已选择: ${topic.topic}`)
  
  // 滚动到发布按钮
  setTimeout(() => {
    const publishButton = document.querySelector('.el-button--success')
    if (publishButton) {
      publishButton.scrollIntoView({ behavior: 'smooth', block: 'center' })
    }
  }, 100)
}

/**
 * 🌟 获取置信度标签类型
 */
const getConfidenceType = (confidence: number): 'success' | 'warning' | 'danger' | '' => {
  if (confidence >= 0.8) return 'success'
  if (confidence >= 0.6) return 'warning'
  return 'danger'
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

.recommendation-item {
  &:hover {
    transform: translateX(5px);
  }
  
  &:active {
    transform: scale(0.98);
  }
}
</style>
