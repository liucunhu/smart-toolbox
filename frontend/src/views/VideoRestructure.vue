<template>
  <div class="video-restructure">
    <el-row :gutter="20">
      <!-- 视频上传与分析 -->
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>🎬 AI视频结构重组</span>
            </div>
          </template>

          <el-form label-width="100px">
            <el-form-item label="视频文件">
              <el-upload
                action="#"
                :auto-upload="false"
                :on-change="handleVideoSelect"
                :limit="1"
                accept=".mp4,.avi,.mov"
              >
                <el-button type="primary">选择视频</el-button>
              </el-upload>
            </el-form-item>

            <el-form-item>
              <el-button type="primary" @click="analyzeVideo" :loading="analyzing" style="width: 100%;">
                🔍 分析视频片段
              </el-button>
            </el-form-item>
          </el-form>

          <!-- 片段分析结果 -->
          <div v-if="segments.length > 0" style="margin-top: 20px;">
            <h4>视频片段分析（共 {{ segments.length }} 个片段）：</h4>
            <el-table :data="segments" style="width: 100%" max-height="400">
              <el-table-column prop="index" label="序号" width="80" />
              <el-table-column prop="semantic_type" label="类型" width="120">
                <template #default="{ row }">
                  <el-tag :type="getSegmentTypeTag(row.semantic_type)">
                    {{ getSegmentTypeName(row.semantic_type) }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="duration" label="时长" width="100">
                <template #default="{ row }">
                  {{ row.duration.toFixed(1) }}s
                </template>
              </el-table-column>
              <el-table-column prop="start_time" label="起始时间" width="100">
                <template #default="{ row }">
                  {{ row.start_time.toFixed(1) }}s
                </template>
              </el-table-column>
              <el-table-column label="特征" min-width="150">
                <template #default="{ row }">
                  <div style="font-size: 12px;">
                    <div>亮度: {{ row.features.brightness.toFixed(0) }}</div>
                    <div>对比度: {{ row.features.contrast.toFixed(0) }}</div>
                    <div>运动: {{ row.features.motion.toFixed(0) }}</div>
                  </div>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-card>
      </el-col>

      <!-- 重组操作与预览 -->
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>🔄 重组操作</span>
            </div>
          </template>

          <el-form label-width="120px">
            <el-form-item label="打乱概率">
              <el-slider v-model="reorderProbability" :min="0" :max="100" show-input />
            </el-form-item>

            <el-form-item label="插帧间隔">
              <el-input-number v-model="insertInterval" :min="10" :max="100" />
            </el-form-item>

            <el-form-item>
              <el-button type="success" @click="restructureVideo" :loading="restructuring" style="width: 100%;">
                ✨ 执行重组
              </el-button>
            </el-form-item>
          </el-form>

          <el-divider />

          <!-- 重组结果 -->
          <div v-if="restructureResult">
            <el-alert
              v-if="restructureResult.status === 'success'"
              title="重组成功"
              type="success"
              :closable="false"
              style="margin-bottom: 15px;"
            />

            <el-descriptions :column="1" border>
              <el-descriptions-item label="原始片段数">{{ restructureResult.original_segments }}</el-descriptions-item>
              <el-descriptions-item label="重组后片段数">{{ restructureResult.reordered_segments }}</el-descriptions-item>
              <el-descriptions-item label="输出文件">
                <el-link :href="restructureResult.output_path" target="_blank" type="primary">
                  下载重组视频
                </el-link>
              </el-descriptions-item>
            </el-descriptions>

            <h4 style="margin-top: 15px;">重组后片段顺序：</h4>
            <el-timeline>
              <el-timeline-item
                v-for="(segment, index) in restructureResult.segments_detail"
                :key="index"
                :timestamp="`片段 ${segment.new_index}: ${segment.duration.toFixed(1)}s (${getSegmentTypeName(segment.semantic_type)})`"
                placement="top"
              >
                <el-card>
                  <p><strong>原位置:</strong> {{ segment.index }}</p>
                  <p><strong>新位置:</strong> {{ segment.new_index }}</p>
                  <p><strong>类型:</strong> {{ getSegmentTypeName(segment.semantic_type) }}</p>
                </el-card>
              </el-timeline-item>
            </el-timeline>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 功能说明 -->
    <el-card style="margin-top: 20px;">
      <template #header>
        <div class="card-header">
          <span>📖 功能说明</span>
        </div>
      </template>

      <el-row :gutter="20">
        <el-col :span="8">
          <h4>🔍 片段分析</h4>
          <ul>
            <li>自动检测场景切换点</li>
            <li>提取亮度、对比度、运动强度特征</li>
            <li>语义分类：静态/动作/普通场景</li>
          </ul>
        </el-col>

        <el-col :span="8">
          <h4>🔄 智能重组</h4>
          <ul>
            <li>非逻辑依赖片段自动打乱</li>
            <li>同类片段内部随机排序</li>
            <li>保持时间顺序连续性</li>
          </ul>
        </el-col>

        <el-col :span="8">
          <h4>🎞️ 插帧/抽帧</h4>
          <ul>
            <li>每N帧插入重复帧</li>
            <li>随机删除部分帧（5%概率）</li>
            <li>降低视频相似度，规避查重</li>
          </ul>
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'

const analyzing = ref(false)
const restructuring = ref(false)
const videoFile = ref<File | null>(null)
const segments = ref<any[]>([])
const reorderProbability = ref(70)
const insertInterval = ref(50)
const restructureResult = ref<any>(null)

// 选择视频文件
const handleVideoSelect = (file: any) => {
  videoFile.value = file.raw
}

// 分析视频
const analyzeVideo = async () => {
  if (!videoFile.value) {
    ElMessage.warning('请选择视频文件')
    return
  }

  analyzing.value = true
  try {
    const formData = new FormData()
    formData.append('video', videoFile.value)

    const response = await axios.post(`${API_BASE_URL}/content/analyze-segments`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })

    segments.value = response.data.segments
    ElMessage.success(`分析完成，共 ${segments.value.length} 个片段`)
  } catch (error) {
    console.error('视频分析失败:', error)
    ElMessage.error('视频分析失败')
  } finally {
    analyzing.value = false
  }
}

// 执行重组
const restructureVideo = async () => {
  if (!videoFile.value) {
    ElMessage.warning('请选择视频文件')
    return
  }

  restructuring.value = true
  try {
    const formData = new FormData()
    formData.append('video', videoFile.value)
    formData.append('reorder_probability', String(reorderProbability.value / 100))
    formData.append('insert_interval', String(insertInterval.value))

    const response = await axios.post(`${API_BASE_URL}/content/restructure-video`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })

    restructureResult.value = response.data
    
    if (response.data.status === 'success') {
      ElMessage.success('视频重组成功')
    } else {
      ElMessage.error('重组失败: ' + response.data.error)
    }
  } catch (error) {
    console.error('视频重组失败:', error)
    ElMessage.error('视频重组失败')
  } finally {
    restructuring.value = false
  }
}

// 片段类型标签
const getSegmentTypeTag = (type: string) => {
  const typeMap: any = {
    'static_bright': 'success',
    'static_dark': 'info',
    'action': 'danger',
    'normal': 'primary'
  }
  return typeMap[type] || 'info'
}

// 片段类型名称
const getSegmentTypeName = (type: string) => {
  const nameMap: any = {
    'static_bright': '静态明亮',
    'static_dark': '静态暗',
    'action': '动作场景',
    'normal': '普通场景'
  }
  return nameMap[type] || type
}
</script>

<style scoped>
.video-restructure { padding: 20px; }
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
}
ul {
  line-height: 1.8;
  color: #606266;
}
</style>
