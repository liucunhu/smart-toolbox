<template>
  <div class="compliance-check">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>🛡️ 违禁词检测</span>
        </div>
      </template>

      <el-row :gutter="20">
        <!-- 左侧：输入区域 -->
        <el-col :span="14">
          <el-card shadow="never">
            <template #header>
              <div class="sub-header">待检测文本</div>
            </template>
            
            <el-input
              v-model="inputText"
              type="textarea"
              :rows="15"
              placeholder="请输入要检测的文案内容..."
              style="margin-bottom: 15px"
            />
            
            <div style="display: flex; gap: 10px;">
              <el-button type="primary" @click="handleCheck" :loading="checking">
                <el-icon><Search /></el-icon>
                开始检测
              </el-button>
              <el-button @click="handleClear">清空</el-button>
              <el-button @click="handleEnhancedCheck" :loading="checking">
                <el-icon><Monitor /></el-icon>
                增强检测
              </el-button>
            </div>
          </el-card>
        </el-col>

        <!-- 右侧：检测结果 -->
        <el-col :span="10">
          <el-card shadow="never">
            <template #header>
              <div class="sub-header">
                检测结果
                <el-tag v-if="result" :type="result.is_safe ? 'success' : 'danger'" size="small">
                  {{ result.is_safe ? '安全' : '存在风险' }}
                </el-tag>
              </div>
            </template>
            
            <div v-if="!result" class="empty-result">
              <el-empty description="暂无检测结果" />
            </div>
            
            <div v-else>
              <!-- 统计信息 -->
              <el-descriptions :column="1" border size="small" style="margin-bottom: 15px">
                <el-descriptions-item label="违禁词数量">
                  <el-tag type="danger">{{ result.violation_count || 0 }}</el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="敏感词数量">
                  <el-tag type="warning">{{ result.sensitive_count || 0 }}</el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="安全评分">
                  <el-progress 
                    :percentage="result.safety_score || 100"
                    :color="getScoreColor(result.safety_score)"
                    :stroke-width="8"
                  />
                </el-descriptions-item>
              </el-descriptions>

              <!-- 违禁词列表 -->
              <div v-if="result.violations && result.violations.length > 0" style="margin-bottom: 15px">
                <div class="result-section-title">⚠️ 违禁词列表</div>
                <el-table :data="result.violations" size="small" border max-height="200">
                  <el-table-column prop="word" label="违禁词" width="120" />
                  <el-table-column prop="position" label="位置" width="80" />
                  <el-table-column prop="severity" label="严重程度" width="100">
                    <template #default="{ row }">
                      <el-tag :type="getSeverityType(row.severity)" size="small">
                        {{ row.severity }}
                      </el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column prop="suggestion" label="建议替换" />
                </el-table>
              </div>

              <!-- 敏感词列表 -->
              <div v-if="result.sensitive_words && result.sensitive_words.length > 0">
                <div class="result-section-title">⚡ 敏感词列表</div>
                <el-table :data="result.sensitive_words" size="small" border max-height="200">
                  <el-table-column prop="word" label="敏感词" width="120" />
                  <el-table-column prop="category" label="分类" width="100" />
                  <el-table-column prop="context" label="上下文" show-overflow-tooltip />
                </el-table>
              </div>

              <!-- 修改建议 -->
              <div v-if="result.suggestions" style="margin-top: 15px">
                <div class="result-section-title">💡 修改建议</div>
                <el-alert
                  type="info"
                  :closable="false"
                  show-icon
                >
                  <div style="white-space: pre-wrap">{{ result.suggestions }}</div>
                </el-alert>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Monitor } from '@element-plus/icons-vue'
import apiClient from '../utils/api'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'

const inputText = ref('')
const checking = ref(false)
const result = ref<any>(null)

/**
 * 获取评分颜色
 */
const getScoreColor = (score: number) => {
  if (score >= 90) return '#67c23a'
  if (score >= 70) return '#e6a23c'
  return '#f56c6c'
}

/**
 * 获取严重程度类型
 */
const getSeverityType = (severity: string) => {
  const types: Record<string, string> = {
    high: 'danger',
    medium: 'warning',
    low: 'info'
  }
  return types[severity] || 'info'
}

/**
 * 执行违禁词检测
 */
const handleCheck = async () => {
  if (!inputText.value.trim()) {
    ElMessage.warning('请输入要检测的文本')
    return
  }
  
  checking.value = true
  try {
    const response = await apiClient.post(`${API_BASE_URL}/compliance/check`, {
      text: inputText.value
    })
    
    if (response.data.status === 'success' || response.data.result) {
      result.value = response.data.result || response.data.data
      ElMessage.success('检测完成')
    } else {
      ElMessage.error('检测失败：' + (response.data.message || '未知错误'))
    }
  } catch (error: any) {
    console.error('违禁词检测失败:', error)
    ElMessage.error('检测失败，请检查后端服务')
  } finally {
    checking.value = false
  }
}

/**
 * 执行增强检测
 */
const handleEnhancedCheck = async () => {
  if (!inputText.value.trim()) {
    ElMessage.warning('请输入要检测的文本')
    return
  }
  
  checking.value = true
  try {
    const response = await apiClient.post(`${API_BASE_URL}/compliance/enhanced-check`, {
      text: inputText.value
    })
    
    if (response.data.status === 'success' || response.data.result) {
      result.value = response.data.result || response.data.data
      ElMessage.success('增强检测完成')
    } else {
      ElMessage.error('检测失败：' + (response.data.message || '未知错误'))
    }
  } catch (error: any) {
    console.error('增强检测失败:', error)
    ElMessage.error('检测失败，请检查后端服务')
  } finally {
    checking.value = false
  }
}

/**
 * 清空输入和结果
 */
const handleClear = () => {
  inputText.value = ''
  result.value = null
}
</script>

<style scoped>
.compliance-check {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
  font-size: 16px;
}

.sub-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
}

.empty-result {
  padding: 40px 0;
}

.result-section-title {
  font-weight: bold;
  margin-bottom: 10px;
  color: #333;
  font-size: 14px;
}
</style>
