#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""创建BilibiliPublish.vue文件"""

content = '''<template>
  <div class="bilibili-publish">
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
              <span>📝 B站账号登录</span>
            </div>
          </template>
          
          <el-form :model="form" label-width="120px">
            <el-form-item label="账号ID">
              <el-input-number v-model="form.accountId" :min="1" />
            </el-form-item>
            
            <el-form-item label="用户名/邮箱">
              <el-input v-model="form.username" placeholder="请输入B站账号" />
            </el-form-item>
            
            <el-form-item label="密码">
              <el-input v-model="form.password" type="password" placeholder="请输入密码" show-password />
            </el-form-item>

            <el-form-item>
              <el-button type="primary" @click="handleLogin" :loading="loading">
                🔐 登录并保存Cookie
              </el-button>
            </el-form-item>
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

      <!-- 右侧：发布视频区域 -->
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>🎬 发布B站视频</span>
              <el-tag v-if="isLoggedIn" type="success" size="small">已登录</el-tag>
              <el-tag v-else type="info" size="small">未登录</el-tag>
            </div>
          </template>

          <el-form :model="publishForm" label-width="100px">
            <el-form-item label="视频文件">
              <el-upload
                action="#"
                :auto-upload="false"
                :on-change="handleVideoSelect"
                :limit="1"
                accept="video/*"
              >
                <el-button size="small">选择视频文件</el-button>
                <template #tip>
                  <div class="el-upload__tip">支持mp4/flv格式，最大4GB</div>
                </template>
              </el-upload>
            </el-form-item>

            <el-form-item label="视频标题">
              <el-input 
                v-model="publishForm.title" 
                placeholder="请输入视频标题"
                maxlength="80"
                show-word-limit
              />
            </el-form-item>

            <el-form-item label="视频简介">
              <el-input 
                v-model="publishForm.description" 
                placeholder="请输入视频简介"
                type="textarea"
                :rows="4"
                maxlength="2000"
                show-word-limit
              />
            </el-form-item>

            <el-form-item label="分区">
              <el-select v-model="publishForm.tid" placeholder="请选择分区">
                <el-option label="生活" :value="160" />
                <el-option label="知识" :value="201" />
                <el-option label="科技" :value="188" />
                <el-option label="游戏" :value="4" />
                <el-option label="娱乐" :value="5" />
              </el-select>
            </el-form-item>

            <el-form-item label="标签">
              <el-input 
                v-model="publishForm.tags" 
                placeholder="例如：教程,编程,Python（用逗号分隔）"
              />
            </el-form-item>

            <el-form-item>
              <el-button 
                type="success" 
                @click="handlePublish" 
                :loading="publishing"
                :disabled="!isLoggedIn || !publishForm.videoPath"
              >
                🚀 发布视频
              </el-button>
            </el-form-item>
          </el-form>

          <div v-if="publishResult" class="result-area">
            <el-alert
              :title="publishResult.message || publishResult.error"
              :type="publishResult.status === 'success' ? 'success' : 'error'"
              :closable="false"
              show-icon
            />
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'
import ComplianceCheckDialog from '@/components/ComplianceCheckDialog.vue'
import { checkContentCompliance } from '@/api/compliance'

const loading = ref(false)
const publishing = ref(false)
const loginResult = ref<any>(null)
const publishResult = ref<any>(null)
const complianceDialog = ref<InstanceType<typeof ComplianceCheckDialog> | null>(null)
const pendingPublishData = ref<any>(null)

const form = ref({
  accountId: 1,
  username: '',
  password: ''
})

const publishForm = ref({
  videoPath: '',
  title: '',
  description: '',
  tid: 160,
  tags: ''
})

const isLoggedIn = computed(() => {
  return loginResult.value?.status === 'success'
})

/**
 * 处理视频文件选择
 */
const handleVideoSelect = (file: any) => {
  publishForm.value.videoPath = file.raw.path
  ElMessage.success('✅ 视频文件已选择')
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
      'http://localhost:8000/api/v1/accounts/login',
      null,
      {
        params: {
          account_id: form.value.accountId,
          username: form.value.username,
          password: form.value.password,
          platform: 'bilibili'
        }
      }
    )

    if (response.data.status === 'success') {
      loginResult.value = response.data
      ElMessage.success('✅ 登录成功！Cookie已保存')
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
 * 发布视频
 */
const handlePublish = async () => {
  if (!publishForm.value.title) {
    ElMessage.warning('请输入视频标题')
    return
  }

  // 步骤1: 显示加载状态
  complianceDialog.value?.showLoading()

  try {
    // 步骤2: 调用合规审查
    const complianceResult = await checkContentCompliance({
      title: publishForm.value.title,
      content: publishForm.value.description,
      platform: 'bilibili'
    })
    
    // 步骤3: 显示结果
    complianceDialog.value?.hideLoading(complianceResult)
    
    if (complianceResult.passed) {
      await executePublish()
    } else {
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
    
    const response = await axios.post(
      'http://localhost:8000/api/v1/content/bilibili/publish',
      null,
      {
        params: {
          account_id: form.value.accountId,
          video_path: data.videoPath,
          title: data.title,
          description: data.description,
          tid: data.tid,
          tags: data.tags
        }
      }
    )
    
    if (response.data.status === 'success') {
      publishResult.value = response.data
      ElMessage.success('🎉 视频发布成功！')
      pendingPublishData.value = null
      publishForm.value.title = ''
      publishForm.value.description = ''
      publishForm.value.tags = ''
      publishForm.value.videoPath = ''
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
  handlePublish()
}

/**
 * 修改内容
 */
const handleModifyContent = () => {
  ElMessage.info('请修改内容后重新提交')
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
.bilibili-publish {
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
</style>
'''

with open('frontend/src/views/BilibiliPublish.vue', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ BilibiliPublish.vue 创建成功！")
print(f"文件大小: {len(content)} 字符")
