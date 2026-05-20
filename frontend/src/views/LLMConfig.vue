<template>
  <div class="llm-config">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>🤖 大模型配置管理</span>
          <el-button type="primary" @click="showCreateDialog">
            <el-icon><Plus /></el-icon>
            新增配置
          </el-button>
        </div>
      </template>

      <!-- 筛选器 -->
      <el-form :inline="true" class="filter-form">
        <el-form-item label="提供商">
          <el-select v-model="filters.provider" placeholder="全部" clearable @change="loadConfigs">
            <el-option label="硅基流动" value="siliconflow" />
            <el-option label="魔搭社区" value="modelscope" />
            <el-option label="通义千问" value="dashscope" />
            <el-option label="DeepSeek" value="deepseek" />
            <el-option label="OpenAI" value="openai" />
          </el-select>
        </el-form-item>
        <el-form-item label="功能类型">
          <el-select v-model="filters.functionType" placeholder="全部" clearable @change="loadConfigs">
            <el-option label="文案生成" value="copywriting" />
            <el-option label="封面图生成" value="cover_generation" />
            <el-option label="图像生成" value="image_generation" />
            <el-option label="内容分析" value="content_analysis" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button @click="loadConfigs">刷新</el-button>
        </el-form-item>
      </el-form>

      <!-- 配置列表 -->
      <el-table :data="configs" style="width: 100%" v-loading="loading">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="name" label="配置名称" width="150" />
        <el-table-column prop="provider" label="提供商" width="120">
          <template #default="{ row }">
            <el-tag :type="getProviderTagType(row.provider)">
              {{ getProviderName(row.provider) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="function_type" label="功能类型" width="120">
          <template #default="{ row }">
            <el-tag>{{ getFunctionTypeName(row.function_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="model_name" label="模型名称" min-width="180" show-overflow-tooltip />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-switch
              v-model="row.is_active"
              @change="toggleActive(row)"
            />
          </template>
        </el-table-column>
        <el-table-column label="默认" width="80">
          <template #default="{ row }">
            <el-tag v-if="row.is_default" type="success" size="small">默认</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="测试状态" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.last_test_status === 'success'" type="success" size="small">成功</el-tag>
            <el-tag v-else-if="row.last_test_status === 'failed'" type="danger" size="small">失败</el-tag>
            <el-tag v-else type="info" size="small">未测试</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="250" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="testConfig(row)">测试</el-button>
            <el-button size="small" type="primary" @click="editConfig(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="deleteConfig(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 创建/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑配置' : '新增配置'"
      width="600px"
    >
      <el-form :model="form" label-width="120px">
        <el-form-item label="配置名称" required>
          <el-input v-model="form.name" placeholder="例如：硅基流动-文案生成" />
        </el-form-item>
        <el-form-item label="提供商" required>
          <el-select v-model="form.provider" placeholder="请选择" style="width: 100%;">
            <el-option label="硅基流动 (SiliconFlow)" value="siliconflow" />
            <el-option label="魔搭社区 (ModelScope)" value="modelscope" />
            <el-option label="通义千问 (DashScope)" value="dashscope" />
            <el-option label="DeepSeek" value="deepseek" />
            <el-option label="OpenAI" value="openai" />
          </el-select>
        </el-form-item>
        <el-form-item label="功能类型" required>
          <el-select v-model="form.function_type" placeholder="请选择" style="width: 100%;">
            <el-option label="文案生成" value="copywriting" />
            <el-option label="封面图生成" value="cover_generation" />
            <el-option label="图像生成" value="image_generation" />
            <el-option label="内容分析" value="content_analysis" />
          </el-select>
        </el-form-item>
        <el-form-item label="API密钥" required>
          <el-input v-model="form.api_key" type="password" show-password placeholder="请输入API密钥" />
        </el-form-item>
        <el-form-item label="Base URL" required>
          <el-input v-model="form.base_url" placeholder="例如：https://api.siliconflow.cn/v1" />
        </el-form-item>
        <el-form-item label="模型名称" required>
          <el-input v-model="form.model_name" placeholder="例如：Qwen/Qwen2.5-72B-Instruct" />
        </el-form-item>
        <el-form-item label="图像模型">
          <el-input v-model="form.image_model_name" placeholder="图像生成时使用（可选）" />
          <div style="font-size: 12px; color: #909399;">仅当功能类型为图像生成或封面图生成时需要</div>
        </el-form-item>
        <el-form-item label="超时时间(秒)">
          <el-input-number v-model="form.timeout" :min="10" :max="300" />
        </el-form-item>
        <el-form-item label="设为默认">
          <el-switch v-model="form.is_default" />
        </el-form-item>
        <el-form-item label="优先级">
          <el-input-number v-model="form.priority" :min="0" :max="100" />
          <div style="font-size: 12px; color: #909399;">数字越大优先级越高</div>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="3" placeholder="配置说明（可选）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveConfig" :loading="saving">保存</el-button>
      </template>
    </el-dialog>

    <!-- 测试结果对话框 -->
    <el-dialog v-model="testResultVisible" title="测试结果" width="500px">
      <el-alert
        :title="testResult.status === 'success' ? '✅ 测试成功' : '❌ 测试失败'"
        :type="testResult.status === 'success' ? 'success' : 'error'"
        :closable="false"
        style="margin-bottom: 15px;"
      />
      <div v-if="testResult.response_time_ms">
        <p><strong>响应时间：</strong>{{ testResult.response_time_ms }} ms</p>
      </div>
      <div v-if="testResult.error">
        <p><strong>错误信息：</strong></p>
        <pre style="background: #f5f5f5; padding: 10px; border-radius: 4px; overflow-x: auto;">{{ testResult.error }}</pre>
      </div>
      <div v-if="testResult.message">
        <p><strong>消息：</strong>{{ testResult.message }}</p>
      </div>
      <template #footer>
        <el-button @click="testResultVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import apiClient from '../utils/api'

const loading = ref(false)
const saving = ref(false)
const configs = ref<any[]>([])
const dialogVisible = ref(false)
const testResultVisible = ref(false)
const isEdit = ref(false)
const currentConfigId = ref<number | null>(null)

const filters = ref({
  provider: '',
  functionType: ''
})

const form = ref({
  name: '',
  provider: '',
  function_type: '',
  api_key: '',
  base_url: '',
  model_name: '',
  image_model_name: '',
  timeout: 60,
  is_default: false,
  priority: 0,
  description: ''
})

const testResult = ref<any>({})

// 提供商名称映射
const providerNames: Record<string, string> = {
  siliconflow: '硅基流动',
  modelscope: '魔搭社区',
  dashscope: '通义千问',
  deepseek: 'DeepSeek',
  openai: 'OpenAI'
}

// 功能类型名称映射
const functionTypeNames: Record<string, string> = {
  copywriting: '文案生成',
  cover_generation: '封面图生成',
  image_generation: '图像生成',
  content_analysis: '内容分析'
}

// 提供商标签类型
const providerTagTypes: Record<string, any> = {
  siliconflow: 'primary',
  modelscope: 'success',
  dashscope: 'warning',
  deepseek: 'danger',
  openai: 'info'
}

const getProviderName = (provider: string) => providerNames[provider] || provider
const getFunctionTypeName = (type: string) => functionTypeNames[type] || type
const getProviderTagType = (provider: string) => providerTagTypes[provider] || 'info'

/**
 * 加载配置列表
 */
const loadConfigs = async () => {
  loading.value = true
  try {
    const params: any = {}
    if (filters.value.provider) params.provider = filters.value.provider
    if (filters.value.functionType) params.function_type = filters.value.functionType

    const response = await apiClient.get('/llm-configs', { params })
    
    if (response.data.status === 'success') {
      configs.value = response.data.data
    } else {
      ElMessage.error('加载配置失败')
    }
  } catch (error: any) {
    console.error('加载配置失败:', error)
    ElMessage.error('加载配置失败：' + (error.response?.data?.detail || '未知错误'))
  } finally {
    loading.value = false
  }
}

/**
 * 显示创建对话框
 */
const showCreateDialog = () => {
  isEdit.value = false
  currentConfigId.value = null
  resetForm()
  dialogVisible.value = true
}

/**
 * 编辑配置
 */
const editConfig = (config: any) => {
  isEdit.value = true
  currentConfigId.value = config.id
  form.value = {
    name: config.name,
    provider: config.provider,
    function_type: config.function_type,
    api_key: config.api_key || '',
    base_url: config.base_url || '',
    model_name: config.model_name,
    image_model_name: config.image_model_name || '',
    timeout: config.timeout || 60,
    is_default: config.is_default,
    priority: config.priority || 0,
    description: config.description || ''
  }
  dialogVisible.value = true
}

/**
 * 保存配置
 */
const saveConfig = async () => {
  // 验证必填字段
  if (!form.value.name || !form.value.provider || !form.value.function_type || 
      !form.value.api_key || !form.value.base_url || !form.value.model_name) {
    ElMessage.warning('请填写所有必填字段')
    return
  }

  saving.value = true
  try {
    if (isEdit.value && currentConfigId.value) {
      // 更新
      const response = await apiClient.put(`/llm-configs/${currentConfigId.value}`, form.value)
      if (response.data.status === 'success') {
        ElMessage.success('配置更新成功')
        dialogVisible.value = false
        await loadConfigs()
      }
    } else {
      // 创建
      const response = await apiClient.post('/llm-configs', form.value)
      if (response.data.status === 'success') {
        ElMessage.success('配置创建成功')
        dialogVisible.value = false
        await loadConfigs()
      }
    }
  } catch (error: any) {
    console.error('保存配置失败:', error)
    ElMessage.error('保存失败：' + (error.response?.data?.detail || '未知错误'))
  } finally {
    saving.value = false
  }
}

/**
 * 删除配置
 */
const deleteConfig = async (config: any) => {
  try {
    await ElMessageBox.confirm(`确定要删除配置 "${config.name}" 吗？`, '确认删除', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    const response = await apiClient.delete(`/llm-configs/${config.id}`)
    if (response.data.status === 'success') {
      ElMessage.success('删除成功')
      loadConfigs()
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('删除配置失败:', error)
      ElMessage.error('删除失败：' + (error.response?.data?.detail || '未知错误'))
    }
  }
}

/**
 * 切换激活状态
 */
const toggleActive = async (config: any) => {
  try {
    const response = await apiClient.patch(`/llm-configs/${config.id}/toggle-active`)
    if (response.data.status === 'success') {
      ElMessage.success(config.is_active ? '已启用' : '已禁用')
    }
  } catch (error: any) {
    console.error('切换状态失败:', error)
    ElMessage.error('操作失败：' + (error.response?.data?.detail || '未知错误'))
    // 恢复原状态
    config.is_active = !config.is_active
  }
}

/**
 * 测试配置
 */
const testConfig = async (config: any) => {
  ElMessage.info('正在测试配置...')
  try {
    const response = await apiClient.post(`/llm-configs/${config.id}/test`)
    testResult.value = response.data
    testResultVisible.value = true
    
    if (response.data.status === 'success') {
      ElMessage.success('测试成功！')
      // 刷新列表以更新测试状态
      loadConfigs()
    } else {
      ElMessage.error('测试失败')
    }
  } catch (error: any) {
    console.error('测试配置失败:', error)
    testResult.value = {
      status: 'failed',
      error: error.response?.data?.detail || '测试失败，请检查网络连接'
    }
    testResultVisible.value = true
    ElMessage.error('测试失败')
  }
}

/**
 * 重置表单
 */
const resetForm = () => {
  form.value = {
    name: '',
    provider: '',
    function_type: '',
    api_key: '',
    base_url: '',
    model_name: '',
    image_model_name: '',
    timeout: 60,
    is_default: false,
    priority: 0,
    description: ''
  }
}

onMounted(() => {
  loadConfigs()
})
</script>

<style scoped lang="scss">
.llm-config {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.filter-form {
  margin-bottom: 20px;
}
</style>
