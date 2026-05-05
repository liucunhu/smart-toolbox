<template>
  <div class="hot-trend-monitor">
    <el-row :gutter="20">
      <!-- 平台选择与热搜展示 -->
      <el-col :span="16">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>🔥 实时热搜监控</span>
              <el-button type="primary" size="small" @click="fetchHotTrends" :loading="loading">
                🔄 刷新
              </el-button>
            </div>
          </template>

          <!-- 平台选择 -->
          <el-radio-group v-model="selectedPlatform" @change="fetchHotTrends" style="margin-bottom: 20px;">
            <el-radio-button label="douyin">抖音</el-radio-button>
            <el-radio-button label="xiaohongshu">小红书</el-radio-button>
            <el-radio-button label="bilibili">B站</el-radio-button>
            <el-radio-button label="toutiao">今日头条</el-radio-button>
          </el-radio-group>

          <!-- 热搜列表 -->
          <el-table :data="hotTopics" style="width: 100%" v-loading="loading">
            <el-table-column prop="rank" label="排名" width="80">
              <template #default="{ row }">
                <el-tag :type="getRankType(row.rank)" effect="dark">
                  {{ row.rank }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="keyword" label="热点关键词" min-width="200">
              <template #default="{ row }">
                <span style="font-weight: bold;">{{ row.keyword }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="heat" label="热度值" width="150">
              <template #default="{ row }">
                <el-progress 
                  :percentage="Math.min(100, row.heat / 100000)" 
                  :color="getHeatColor(row.heat)"
                  :stroke-width="15"
                />
              </template>
            </el-table-column>
            <el-table-column label="操作" width="120">
              <template #default="{ row }">
                <el-button type="primary" size="small" @click="injectKeyword(row.keyword)">
                  植入文案
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <!-- 文案注入测试 -->
      <el-col :span="8">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>✍️ 热点文案注入测试</span>
            </div>
          </template>

          <el-form label-width="100px">
            <el-form-item label="原始文案">
              <el-input
                v-model="originalScript"
                type="textarea"
                :rows="6"
                placeholder="请输入原始文案..."
              />
            </el-form-item>

            <el-form-item label="已选关键词">
              <el-tag
                v-for="(keyword, index) in selectedKeywords"
                :key="index"
                closable
                @close="removeKeyword(index)"
                style="margin-right: 5px; margin-bottom: 5px;"
              >
                {{ keyword }}
              </el-tag>
              <el-tag v-if="selectedKeywords.length === 0" type="info">未选择关键词</el-tag>
            </el-form-item>

            <el-form-item>
              <el-button type="success" @click="handleInject" :loading="injecting" style="width: 100%;">
                ✨ 注入热点
              </el-button>
            </el-form-item>
          </el-form>

          <el-divider />

          <!-- 注入结果 -->
          <div v-if="injectedResult">
            <h4>注入结果：</h4>
            <el-alert
              v-if="injectedResult.status === 'success'"
              title="注入成功"
              type="success"
              :closable="false"
              style="margin-bottom: 10px;"
            />
            
            <el-descriptions :column="1" border style="margin-bottom: 10px;">
              <el-descriptions-item label="原文长度">{{ injectedResult.original_length }}</el-descriptions-item>
              <el-descriptions-item label="新文长度">{{ injectedResult.modified_length }}</el-descriptions-item>
              <el-descriptions-item label="权重分数">{{ injectedResult.weight_score }}分</el-descriptions-item>
            </el-descriptions>

            <el-input
              v-model="injectedResult.script"
              type="textarea"
              :rows="8"
              readonly
            />

            <div style="margin-top: 10px;">
              <h5>生成标签：</h5>
              <el-tag
                v-for="tag in injectedResult.hashtags"
                :key="tag"
                type="success"
                style="margin-right: 5px; margin-bottom: 5px;"
              >
                {{ tag }}
              </el-tag>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import apiClient from '../utils/api'
import { ElMessage } from 'element-plus'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'

const loading = ref(false)
const injecting = ref(false)
const selectedPlatform = ref('douyin')
const hotTopics = ref<any[]>([])
const originalScript = ref('')
const selectedKeywords = ref<string[]>([])
const injectedResult = ref<any>(null)

// 获取热搜
const fetchHotTrends = async () => {
  loading.value = true
  try {
    const response = await apiClient.get(`${API_BASE_URL}/content/hot-trends`, {
      params: { platform: selectedPlatform.value, count: 20 }
    })
    // 后端返回格式: { platform, total, hot_topics, updated_at }
    hotTopics.value = response.data.hot_topics || []
    ElMessage.success(`热搜更新成功，共${response.data.total || 0}条`)
  } catch (error) {
    console.error('获取热搜失败:', error)
    ElMessage.error('获取热搜失败')
  } finally {
    loading.value = false
  }
}

// 植入关键词
const injectKeyword = (keyword: string) => {
  if (!selectedKeywords.value.includes(keyword)) {
    if (selectedKeywords.value.length >= 3) {
      ElMessage.warning('最多选择3个关键词')
      return
    }
    selectedKeywords.value.push(keyword)
    ElMessage.success(`已添加关键词: ${keyword}`)
  }
}

// 移除关键词
const removeKeyword = (index: number) => {
  selectedKeywords.value.splice(index, 1)
}

// 执行注入
const handleInject = async () => {
  if (!originalScript.value) {
    ElMessage.warning('请输入原始文案')
    return
  }

  if (selectedKeywords.value.length === 0) {
    ElMessage.warning('请至少选择一个关键词')
    return
  }

  injecting.value = true
  try {
    const response = await apiClient.post(`${API_BASE_URL}/content/inject-hot-trend`, {
      script: originalScript.value,
      platform: selectedPlatform.value,
      keywords: selectedKeywords.value
    })

    injectedResult.value = response.data
    
    if (response.data.status === 'success') {
      ElMessage.success('热点注入成功')
    } else {
      ElMessage.error('注入失败: ' + response.data.error)
    }
  } catch (error) {
    console.error('热点注入失败:', error)
    ElMessage.error('热点注入失败')
  } finally {
    injecting.value = false
  }
}

// 排名样式
const getRankType = (rank: number) => {
  if (rank === 1) return 'danger'
  if (rank <= 3) return 'warning'
  if (rank <= 10) return 'primary'
  return 'info'
}

// 热度颜色
const getHeatColor = (heat: number) => {
  if (heat > 5000000) return '#f56c6c'
  if (heat > 1000000) return '#e6a23c'
  return '#67c23a'
}

onMounted(() => {
  fetchHotTrends()
})
</script>

<style scoped>
.hot-trend-monitor { padding: 20px; }
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
}
</style>
