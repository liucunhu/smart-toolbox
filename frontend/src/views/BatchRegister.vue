<template>
  <div class="batch-register">
    <el-row :gutter="20">
      <!-- 批量注册表单 -->
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>📱 批量账号注册</span>
            </div>
          </template>

          <el-form :model="form" label-width="120px">
            <el-form-item label="目标平台">
              <el-select v-model="form.platform" placeholder="选择平台">
                <el-option label="抖音" value="douyin" />
                <el-option label="快手" value="kuaishou" />
                <el-option label="小红书" value="xiaohongshu" />
                <el-option label="B站" value="bilibili" />
              </el-select>
            </el-form-item>

            <el-form-item label="注册数量">
              <el-input-number v-model="form.count" :min="1" :max="50" />
            </el-form-item>

            <el-form-item label="SMS平台">
              <el-select v-model="form.sms_platform" placeholder="选择接码平台">
                <el-option label="SMS Activate" value="sms_activate" />
                <el-option label="5SIM" value="5sim" />
                <el-option label="SMSHub" value="smshub" />
              </el-select>
            </el-form-item>

            <el-form-item label="SMS API密钥">
              <el-input 
                v-model="form.sms_api_key" 
                type="password"
                placeholder="输入SMS平台API密钥"
                show-password
              />
            </el-form-item>

            <el-form-item label="验证码API密钥">
              <el-input 
                v-model="form.captcha_api_key" 
                type="password"
                placeholder="输入验证码识别API密钥"
                show-password
              />
            </el-form-item>

            <el-form-item>
              <el-button 
                type="primary" 
                @click="handleBatchRegister" 
                :loading="registering"
                style="width: 100%;"
              >
                🚀 开始批量注册
              </el-button>
            </el-form-item>
          </el-form>

          <!-- 注册结果 -->
          <div v-if="registerResult" class="result-area">
            <el-alert
              :title="registerResult.message"
              :type="registerResult.success > 0 ? 'success' : 'error'"
              :closable="false"
            >
              <template #default>
                <p>总计: {{ registerResult.total }} | 成功: {{ registerResult.success }}</p>
                <div v-if="registerResult.tasks && registerResult.tasks.length > 0">
                  <h4>任务列表：</h4>
                  <el-table :data="registerResult.tasks" border style="margin-top: 10px;">
                    <el-table-column prop="account_id" label="账号ID" width="100" />
                    <el-table-column prop="phone" label="手机号" width="150" />
                    <el-table-column prop="status" label="状态" width="100" />
                    <el-table-column prop="task_id" label="任务ID" />
                  </el-table>
                </div>
              </template>
            </el-alert>
          </div>
        </el-card>
      </el-col>

      <!-- 账号列表 -->
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>📋 已注册账号列表</span>
              <el-button size="small" @click="fetchAccounts" style="float: right;">刷新</el-button>
            </div>
          </template>

          <el-table :data="accounts" border style="width: 100%">
            <el-table-column prop="id" label="ID" width="80" />
            <el-table-column prop="username" label="用户名" width="150" />
            <el-table-column prop="platform" label="平台" width="120" />
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="row.status === 'active' ? 'success' : 'info'">
                  {{ row.status }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="创建时间" />
          </el-table>

          <el-pagination
            v-model:current-page="pagination.page"
            v-model:page-size="pagination.pageSize"
            :page-sizes="[10, 20, 50]"
            :total="pagination.total"
            layout="total, sizes, prev, pager, next"
            @size-change="fetchAccounts"
            @current-change="fetchAccounts"
            style="margin-top: 20px; justify-content: flex-end;"
          />
        </el-card>
      </el-col>
    </el-row>

    <!-- 功能说明 -->
    <el-card style="margin-top: 20px;">
      <template #header>
        <div class="card-header">
          <span>💡 使用说明</span>
        </div>
      </template>

      <el-row :gutter="20">
        <el-col :span="8">
          <h4>🔑 SMS接码平台</h4>
          <ul>
            <li>SMS Activate - 推荐</li>
            <li>5SIM - 备选方案</li>
            <li>SMSHub - 备用选项</li>
          </ul>
        </el-col>

        <el-col :span="8">
          <h4>⚙️ 配置要求</h4>
          <ul>
            <li>需要SMS API密钥</li>
            <li>需要验证码API密钥</li>
            <li>支持最多50个账号</li>
          </ul>
        </el-col>

        <el-col :span="8">
          <h4>📊 注册流程</h4>
          <ol>
            <li>获取手机号</li>
            <li>接收验证码</li>
            <li>自动完成注册</li>
            <li>保存账号信息</li>
          </ol>
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import apiClient from '../utils/api'
import { ElMessage } from 'element-plus'

const registering = ref(false)
const registerResult = ref<any>(null)
const accounts = ref<any[]>([])

const form = ref({
  platform: 'douyin',
  count: 1,
  sms_platform: 'sms_activate',
  sms_api_key: '',
  captcha_api_key: ''
})

const pagination = ref({
  page: 1,
  pageSize: 10,
  total: 0
})

// 批量注册
const handleBatchRegister = async () => {
  if (!form.value.sms_api_key) {
    ElMessage.warning('请输入SMS API密钥')
    return
  }

  registering.value = true
  try {
    const response = await apiClient.post('/batch/register', null, {
      params: {
        platform: form.value.platform,
        count: form.value.count,
        sms_platform: form.value.sms_platform,
        sms_api_key: form.value.sms_api_key,
        captcha_api_key: form.value.captcha_api_key
      }
    })

    registerResult.value = response.data
    
    if (response.data.success > 0) {
      ElMessage.success(`批量注册成功！共${response.data.success}个账号`)
      fetchAccounts()
    } else {
      ElMessage.error('注册失败，请检查API密钥和网络连接')
    }
  } catch (error: any) {
    console.error('注册失败:', error)
    ElMessage.error('注册失败：' + (error.response?.data?.detail || error.message))
  } finally {
    registering.value = false
  }
}

// 获取账号列表
const fetchAccounts = async () => {
  try {
    const response = await apiClient.get('/accounts/list', {
      params: {
        page: pagination.value.page,
        page_size: pagination.value.pageSize
      }
    })

    accounts.value = response.data.data.items
    pagination.value.total = response.data.data.total
  } catch (error) {
    console.error('获取账号列表失败:', error)
  }
}

onMounted(() => {
  fetchAccounts()
})
</script>

<style scoped>
.batch-register { padding: 20px; }
.card-header { font-weight: bold; }
.result-area { margin-top: 20px; }
</style>
