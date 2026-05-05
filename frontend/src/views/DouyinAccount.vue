<template>
  <div class="douyin-account">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>🎵 抖音账号管理</span>
        </div>
      </template>
      
      <!-- 添加抖音账号 -->
      <el-form :model="form" label-width="120px">
        <el-form-item label="账号 ID">
          <el-input-number v-model="form.accountId" :min="1" />
        </el-form-item>
        
        <el-form-item label="手机号/邮箱">
          <el-input v-model="form.username" placeholder="请输入抖音账号" />
        </el-form-item>
        
        <el-form-item label="密码">
          <el-input v-model="form.password" type="password" placeholder="请输入密码" show-password />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleLogin" :loading="loading">
             登录并保存 Cookie
          </el-button>
          <el-tag type="info" style="margin-left: 10px;">
            系统将打开浏览器，自动填充账号密码，请手动完成验证码
          </el-tag>
        </el-form-item>
      </el-form>

      <el-divider />

      <!-- 登录状态 -->
      <div v-if="loginResult" class="result-area">
        <el-alert
          :title="loginResult.message || loginResult.error"
          :type="loginResult.status === 'success' ? 'success' : 'error'"
          :closable="false"
        />
      </div>

      <el-divider />

      <!-- 视频发布 -->
      <el-form :model="publishForm" label-width="120px">
        <el-form-item label="账号 ID">
          <el-input-number v-model="publishForm.accountId" :min="1" />
        </el-form-item>
        
        <el-form-item label="视频标题">
          <el-input v-model="publishForm.title" placeholder="请输入视频标题" />
        </el-form-item>
        
        <el-form-item label="视频路径">
          <el-input v-model="publishForm.videoPath" placeholder="请输入视频文件路径" />
        </el-form-item>
        
        <el-form-item label="视频描述">
          <el-input v-model="publishForm.description" type="textarea" :rows="3" placeholder="可选" />
        </el-form-item>

        <el-form-item>
          <el-button type="success" @click="handlePublish" :loading="publishing">
             发布视频
          </el-button>
        </el-form-item>
      </el-form>

      <!-- 发布结果 -->
      <div v-if="publishResult" class="result-area">
        <el-alert
          :title="publishResult.message || publishResult.error"
          :type="publishResult.status === 'success' ? 'success' : (publishResult.status === 'pending' ? 'warning' : 'error')"
          :closable="false"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import apiClient from '../utils/api'

const loading = ref(false)
const loginResult = ref<any>(null)
const form = ref({
  accountId: 1,
  username: '',
  password: ''
})

const publishing = ref(false)
const publishResult = ref<any>(null)
const publishForm = ref({
  accountId: 1,
  title: '',
  videoPath: '',
  description: ''
})

const handleLogin = async () => {
  if (!form.value.username || !form.value.password) {
    ElMessage.warning('请输入账号和密码')
    return
  }

  loading.value = true
  try {
    const response = await apiClient.post('/accounts/douyin/login', null, {
      params: {
        account_id: form.value.accountId,
        username: form.value.username,
        password: form.value.password
      }
    })
    
    loginResult.value = response.data
    
    if (response.data.status === 'success') {
      ElMessage.success('登录成功！Cookie 已保存')
    } else {
      ElMessage.error('登录失败：' + (response.data.error || '未知错误'))
    }
  } catch (error) {
    console.error('登录失败:', error)
    ElMessage.error('登录失败，请检查后端服务')
  } finally {
    loading.value = false
  }
}

const handlePublish = async () => {
  if (!publishForm.value.title || !publishForm.value.videoPath) {
    ElMessage.warning('请输入视频标题和路径')
    return
  }

  publishing.value = true
  try {
    const response = await apiClient.post('/content/douyin/publish', null, {
      params: {
        account_id: publishForm.value.accountId,
        title: publishForm.value.title,
        video_path: publishForm.value.videoPath,
        description: publishForm.value.description
      }
    })
    
    publishResult.value = response.data
    
    if (response.data.status === 'success') {
      ElMessage.success('视频发布成功！')
    } else if (response.data.status === 'pending') {
      ElMessage.warning('发布任务已提交，请手动确认')
    } else {
      ElMessage.error('发布失败：' + (response.data.error || '未知错误'))
    }
  } catch (error) {
    console.error('发布失败:', error)
    ElMessage.error('发布失败，请检查后端服务')
  } finally {
    publishing.value = false
  }
}
</script>

<style scoped>
.douyin-account { padding: 20px; }
.card-header { font-weight: bold; }
.result-area { margin-top: 20px; }
</style>
