<template>
  <div class="content-creation">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>🎬 爆款内容智造局</span>
        </div>
      </template>
      
      <el-form :model="form" label-width="120px">
        <el-form-item label="创作主题">
          <el-input v-model="form.topic" placeholder="例如：Python 自动化办公技巧" />
        </el-form-item>
        
        <el-form-item label="目标平台">
          <el-select v-model="form.platform" placeholder="请选择平台">
            <el-option label="抖音" value="douyin" />
            <el-option label="小红书" value="xiaohongshu" />
            <el-option label="B站" value="bilibili" />
            <el-option label="今日头条" value="toutiao" />
          </el-select>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleGenerate" :loading="loading">
            ✨ AI 智能生成脚本
          </el-button>
        </el-form-item>
      </el-form>

      <el-divider />

      <div v-if="result" class="result-area">
        <h3>生成结果：</h3>
        <el-alert
          v-if="result.message"
          :title="result.message"
          :type="result.error ? 'error' : 'success'"
          :closable="false"
          style="margin-bottom: 15px;"
        />
        
        <!-- 头条文章展示 -->
        <div v-if="result.article_title">
          <el-descriptions :column="2" border style="margin-bottom: 15px;">
            <el-descriptions-item label="文章标题">{{ result.article_title }}</el-descriptions-item>
            <el-descriptions-item label="文章分类">{{ result.article_category || '未分类' }}</el-descriptions-item>
          </el-descriptions>
          
          <el-tag v-for="tag in result.tags" :key="tag" style="margin-right: 5px; margin-bottom: 5px;">{{ tag }}</el-tag>
          
          <el-input
            v-if="result.article_content"
            v-model="result.article_content"
            type="textarea"
            :rows="10"
            readonly
            style="margin-top: 10px;"
          />
          
          <!-- 头条文章发布按钮 -->
          <div style="margin-top: 15px;">
            <el-form :inline="true">
              <el-form-item label="选择账号">
                <el-select v-model="selectedAccountId" placeholder="选择头条账号" style="width: 200px;">
                  <el-option
                    v-for="account in toutiaoAccounts"
                    :key="account.id"
                    :label="account.username || `账号${account.id}`"
                    :value="account.id"
                  >
                    <span>{{ account.username || `账号${account.id}` }}</span>
                    <el-tag 
                      v-if="account.cookies" 
                      type="success" 
                      size="small" 
                      style="margin-left: 8px;"
                    >
                      已登录
                    </el-tag>
                    <el-tag 
                      v-else 
                      type="info" 
                      size="small" 
                      style="margin-left: 8px;"
                    >
                      未登录
                    </el-tag>
                  </el-option>
                </el-select>
              </el-form-item>
              <el-form-item>
                <el-button type="primary" @click="handlePublishToutiao" :loading="publishing">
                   发布到头条
                </el-button>
                <el-button type="success" @click="handleAutoPublishToutiao" :loading="autoPublishing">
                  🚀 一键全自动发布
                </el-button>
              </el-form-item>
            </el-form>
            <el-alert
              type="info"
              :closable="false"
              style="margin-top: 10px;"
            >
              <template #default>
                <p>📌 发布前请确保：</p>
                <ul style="margin: 5px 0 0 20px; padding: 0;">
                  <li>选择已登录的账号（下拉框中显示"已登录"标签）</li>
                  <li>如果账号未登录，请先在"头条账号管理"页面登录</li>
                  <li>或直接使用"🚀 一键全自动发布"功能自动完成登录+生成+发布</li>
                </ul>
              </template>
            </el-alert>
          </div>
        </div>
        
        <!-- 短视频脚本展示 -->
        <div v-else>
          <el-input
            v-if="result.script"
            v-model="result.script"
            type="textarea"
            :rows="10"
            readonly
            style="margin-bottom: 10px;"
          />
          <el-descriptions v-if="result.topic" :column="2" border>
            <el-descriptions-item label="创作主题">{{ result.topic }}</el-descriptions-item>
            <el-descriptions-item label="目标平台">{{ result.platform }}</el-descriptions-item>
          </el-descriptions>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useContentCreation } from '../composables/useContentCreation'
import apiClient from '../utils/api'
import { ElMessage } from 'element-plus'

const { form, loading, result, handleGenerate } = useContentCreation()
const publishing = ref(false)
const autoPublishing = ref(false)
const selectedAccountId = ref<number | null>(null)
const toutiaoAccounts = ref<any[]>([])

// 获取头条账号列表
const fetchToutiaoAccounts = async () => {
  try {
    const response = await apiClient.get('/accounts/list', {
      params: {
        platform: 'toutiao',
        page: 1,
        page_size: 100
      }
    })
    toutiaoAccounts.value = response.data.data.items
    
    // 默认选择第一个账号
    if (toutiaoAccounts.value.length > 0 && !selectedAccountId.value) {
      selectedAccountId.value = toutiaoAccounts.value[0].id
    }
  } catch (error) {
    console.error('获取账号列表失败:', error)
  }
}

// 检查账号是否已登录（有Cookie）
const isAccountLoggedIn = (accountId: number): boolean => {
  const account = toutiaoAccounts.value.find(acc => acc.id === accountId)
  return account && account.cookies ? true : false
}

const handlePublishToutiao = async () => {
  if (!result.value.article_title || !result.value.article_content) {
    ElMessage.warning('请先生成头条文章')
    return
  }
  
  if (!selectedAccountId.value) {
    ElMessage.warning('请选择要发布的账号')
    return
  }

  // 检查账号是否已登录
  if (!isAccountLoggedIn(selectedAccountId.value)) {
    ElMessage.warning('该账号尚未登录，请先在“头条账号管理”页面登录账号，或使用“一键全自动发布”功能')
    return
  }

  publishing.value = true
  try {
    const response = await apiClient.post('/content/toutiao/publish', null, {
      params: {
        account_id: selectedAccountId.value,
        title: result.value.article_title,
        content: result.value.article_content,
        category: result.value.article_category || '科技',
        tags: result.value.tags || [],
        auto_generate_cover: true,  // ✅ 启用AI自动生成封面图（使用数据库配置的默认提供商）
        cover_style: 'modern',       // ✅ 现代科技风格
        use_cdp: true,               // ✅ 使用CDP模式（推荐）
        cdp_port: 9222
      }
    })

    if (response.data.status === 'success') {
      ElMessage.success('✅ 文章发布成功！')
    } else {
      ElMessage.error('发布失败：' + (response.data.message || '未知错误'))
    }
  } catch (error: any) {
    console.error('发布失败:', error)
    ElMessage.error('发布失败：' + (error.response?.data?.detail || error.message))
  } finally {
    publishing.value = false
  }
}

const handleAutoPublishToutiao = async () => {
  if (!form.value.topic) {
    ElMessage.warning('请先输入创作主题')
    return
  }
  
  if (!selectedAccountId.value) {
    ElMessage.warning('请选择要发布的账号')
    return
  }

  // 自动发布需要用户名和密码
  const username = prompt('请输入头条账号的登录手机号/邮箱：')
  if (!username) return
  
  const password = prompt('请输入头条账号的登录密码：')
  if (!password) return

  autoPublishing.value = true
  try {
    const response = await apiClient.post('/content/toutiao/auto_publish', null, {
      params: {
        account_id: selectedAccountId.value,
        topic: form.value.topic,
        username: username,
        password: password,
        category: result.value.article_category || '科技',
        auto_generate_cover: true,  // ✅ 启用AI自动生成封面图（使用数据库配置的默认提供商）
        cover_style: 'modern',       // ✅ 现代科技风格
        use_cdp: true,               // ✅ 使用CDP模式（推荐）
        cdp_port: 9222
      }
    })

    if (response.data.status === 'success') {
      ElMessage.success(' 一键发布成功！')
      // 更新生成结果
      result.value = {
        message: '一键发布成功！',
        article_title: response.data.article_title,
        article_content: '已自动发布',
        article_category: response.data.category,
        tags: response.data.tags,
        platform: 'toutiao',
        topic: form.value.topic
      }
    } else {
      ElMessage.error(`发布失败：${response.data.error || '未知错误'}`)
    }
  } catch (error: any) {
    console.error('自动发布失败:', error)
    ElMessage.error('发布失败：' + (error.response?.data?.detail || error.message))
  } finally {
    autoPublishing.value = false
  }
}

onMounted(() => {
  fetchToutiaoAccounts()
})
</script>

<style scoped>
.content-creation { padding: 20px; }
.card-header { font-weight: bold; }
.result-area { margin-top: 20px; }
</style>
