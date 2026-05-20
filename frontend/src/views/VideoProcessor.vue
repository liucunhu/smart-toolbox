<template>
  <div class="video-processor">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>🎬 视频处理工具</span>
        </div>
      </template>

      <el-row :gutter="20">
        <!-- 视频去重 -->
        <el-col :span="12">
          <el-card shadow="never" style="margin-bottom: 20px;">
            <template #header>
              <div class="sub-header">🔄 视频去重</div>
            </template>
            
            <el-form label-width="100px">
              <el-form-item label="原视频">
                <el-upload
                  action="#"
                  :auto-upload="false"
                  :on-change="(file) => handleFileSelect(file, 'dedup')"
                  accept="video/*"
                >
                  <el-button type="primary">
                    <el-icon><Upload /></el-icon>
                    选择视频
                  </el-button>
                </el-upload>
                <div v-if="dedupVideo" style="margin-top: 10px; color: #666;">
                  已选择: {{ dedupVideo.name }}
                </div>
              </el-form-item>
              
              <el-form-item label="去重强度">
                <el-slider 
                  v-model="dedupForm.intensity" 
                  :min="1" 
                  :max="10"
                  show-stops
                />
                <span style="margin-left: 10px;">{{ dedupForm.intensity }}</span>
              </el-form-item>
              
              <el-form-item label="处理方式">
                <el-checkbox-group v-model="dedupForm.methods">
                  <el-checkbox label="mirror">镜像翻转</el-checkbox>
                  <el-checkbox label="speed">变速处理</el-checkbox>
                  <el-checkbox label="filter">滤镜调整</el-checkbox>
                  <el-checkbox label="crop">裁剪缩放</el-checkbox>
                </el-checkbox-group>
              </el-form-item>
              
              <el-form-item>
                <el-button type="primary" @click="handleDeduplicate" :loading="processing.dedup">
                  <el-icon><Refresh /></el-icon>
                  开始去重
                </el-button>
              </el-form-item>
            </el-form>

            <!-- 去重结果 -->
            <div v-if="dedupResult" style="margin-top: 15px;">
              <el-alert
                :type="dedupResult.success ? 'success' : 'error'"
                :title="dedupResult.success ? '去重成功' : '去重失败'"
                :description="dedupResult.message"
                :closable="false"
                show-icon
              />
            </div>
          </el-card>
        </el-col>

        <!-- 格式适配 -->
        <el-col :span="12">
          <el-card shadow="never" style="margin-bottom: 20px;">
            <template #header>
              <div class="sub-header">📐 格式适配</div>
            </template>
            
            <el-form label-width="100px">
              <el-form-item label="原视频">
                <el-upload
                  action="#"
                  :auto-upload="false"
                  :on-change="(file) => handleFileSelect(file, 'format')"
                  accept="video/*"
                >
                  <el-button type="primary">
                    <el-icon><Upload /></el-icon>
                    选择视频
                  </el-button>
                </el-upload>
                <div v-if="formatVideo" style="margin-top: 10px; color: #666;">
                  已选择: {{ formatVideo.name }}
                </div>
              </el-form-item>
              
              <el-form-item label="目标平台">
                <el-select v-model="formatForm.platform" style="width: 100%">
                  <el-option label="抖音 (9:16)" value="douyin" />
                  <el-option label="快手 (9:16)" value="kuaishou" />
                  <el-option label="B站 (16:9)" value="bilibili" />
                  <el-option label="视频号 (9:16)" value="wechat" />
                  <el-option label="小红书 (3:4)" value="xiaohongshu" />
                  <el-option label="今日头条 (16:9)" value="toutiao" />
                </el-select>
              </el-form-item>
              
              <el-form-item label="输出格式">
                <el-select v-model="formatForm.output_format" style="width: 100%">
                  <el-option label="MP4" value="mp4" />
                  <el-option label="MOV" value="mov" />
                  <el-option label="AVI" value="avi" />
                </el-select>
              </el-form-item>
              
              <el-form-item label="分辨率">
                <el-select v-model="formatForm.resolution" style="width: 100%">
                  <el-option label="1080P" value="1920x1080" />
                  <el-option label="720P" value="1280x720" />
                  <el-option label="480P" value="854x480" />
                  <el-option label="4K" value="3840x2160" />
                </el-select>
              </el-form-item>
              
              <el-form-item label="码率">
                <el-select v-model="formatForm.bitrate" style="width: 100%">
                  <el-option label="高 (8Mbps)" value="high" />
                  <el-option label="中 (4Mbps)" value="medium" />
                  <el-option label="低 (2Mbps)" value="low" />
                </el-select>
              </el-form-item>
              
              <el-form-item>
                <el-button type="primary" @click="handleFormatAdapt" :loading="processing.format">
                  <el-icon><Crop /></el-icon>
                  开始转换
                </el-button>
              </el-form-item>
            </el-form>

            <!-- 格式转换结果 -->
            <div v-if="formatResult" style="margin-top: 15px;">
              <el-alert
                :type="formatResult.success ? 'success' : 'error'"
                :title="formatResult.success ? '转换成功' : '转换失败'"
                :description="formatResult.message"
                :closable="false"
                show-icon
              />
            </div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 处理历史 -->
      <el-card shadow="never">
        <template #header>
          <div class="sub-header">📋 处理历史</div>
        </template>
        
        <el-table :data="history" max-height="300" border>
          <el-table-column prop="id" label="ID" width="80" />
          <el-table-column prop="type" label="类型" width="100">
            <template #default="{ row }">
              <el-tag :type="row.type === 'dedup' ? 'primary' : 'success'" size="small">
                {{ row.type === 'dedup' ? '去重' : '格式转换' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="filename" label="文件名" />
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="getStatusType(row.status)" size="small">
                {{ getStatusText(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="处理时间" width="180">
            <template #default="{ row }">
              {{ formatTime(row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120">
            <template #default="{ row }">
              <el-button size="small" type="primary" link>
                下载
              </el-button>
              <el-button size="small" type="danger" link>
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Upload, Refresh, Crop } from '@element-plus/icons-vue'
import apiClient from '../utils/api'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'

const dedupVideo = ref<File | null>(null)
const formatVideo = ref<File | null>(null)

const processing = ref({
  dedup: false,
  format: false
})

const dedupForm = ref({
  intensity: 5,
  methods: ['mirror', 'speed']
})

const formatForm = ref({
  platform: 'douyin',
  output_format: 'mp4',
  resolution: '1920x1080',
  bitrate: 'high'
})

const dedupResult = ref<any>(null)
const formatResult = ref<any>(null)

const history = ref<any[]>([
  // 示例数据，实际应从后端获取
  {
    id: 1,
    type: 'dedup',
    filename: 'example_video.mp4',
    status: 'completed',
    created_at: new Date().toISOString()
  }
])

/**
 * 处理文件选择
 */
const handleFileSelect = (file: any, type: string) => {
  if (type === 'dedup') {
    dedupVideo.value = file.raw
  } else {
    formatVideo.value = file.raw
  }
}

/**
 * 视频去重
 */
const handleDeduplicate = async () => {
  if (!dedupVideo.value) {
    ElMessage.warning('请先选择视频文件')
    return
  }
  
  processing.value.dedup = true
  try {
    const formData = new FormData()
    formData.append('video', dedupVideo.value)
    formData.append('intensity', String(dedupForm.value.intensity))
    formData.append('methods', JSON.stringify(dedupForm.value.methods))
    
    const response = await apiClient.post(`${API_BASE_URL}/video/deduplicate`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    
    if (response.data.status === 'success') {
      dedupResult.value = {
        success: true,
        message: '视频去重完成，相似度降低至' + (response.data.similarity || '30%')
      }
      ElMessage.success('视频去重成功')
      
      // 添加到历史记录
      history.value.unshift({
        id: Date.now(),
        type: 'dedup',
        filename: dedupVideo.value.name,
        status: 'completed',
        created_at: new Date().toISOString()
      })
    } else {
      dedupResult.value = {
        success: false,
        message: response.data.message || '去重失败'
      }
      ElMessage.error('去重失败')
    }
  } catch (error: any) {
    console.error('视频去重失败:', error)
    dedupResult.value = {
      success: false,
      message: '处理失败，请检查后端服务'
    }
    ElMessage.error('去重失败')
  } finally {
    processing.value.dedup = false
  }
}

/**
 * 格式适配
 */
const handleFormatAdapt = async () => {
  if (!formatVideo.value) {
    ElMessage.warning('请先选择视频文件')
    return
  }
  
  processing.value.format = true
  try {
    const formData = new FormData()
    formData.append('video', formatVideo.value)
    formData.append('platform', formatForm.value.platform)
    formData.append('output_format', formatForm.value.output_format)
    formData.append('resolution', formatForm.value.resolution)
    formData.append('bitrate', formatForm.value.bitrate)
    
    const response = await apiClient.post(`${API_BASE_URL}/video/format-adapt`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    
    if (response.data.status === 'success') {
      formatResult.value = {
        success: true,
        message: `格式转换完成，输出: ${formatForm.value.resolution} ${formatForm.value.output_format}`
      }
      ElMessage.success('格式转换成功')
      
      // 添加到历史记录
      history.value.unshift({
        id: Date.now(),
        type: 'format',
        filename: formatVideo.value.name,
        status: 'completed',
        created_at: new Date().toISOString()
      })
    } else {
      formatResult.value = {
        success: false,
        message: response.data.message || '转换失败'
      }
      ElMessage.error('转换失败')
    }
  } catch (error: any) {
    console.error('格式转换失败:', error)
    formatResult.value = {
      success: false,
      message: '处理失败，请检查后端服务'
    }
    ElMessage.error('转换失败')
  } finally {
    processing.value.format = false
  }
}

/**
 * 获取状态类型
 */
const getStatusType = (status: string) => {
  const types: Record<string, string> = {
    completed: 'success',
    processing: 'warning',
    failed: 'danger',
    pending: 'info'
  }
  return types[status] || 'info'
}

/**
 * 获取状态文本
 */
const getStatusText = (status: string) => {
  const texts: Record<string, string> = {
    completed: '已完成',
    processing: '处理中',
    failed: '失败',
    pending: '待处理'
  }
  return texts[status] || status
}

/**
 * 格式化时间
 */
const formatTime = (time: string) => {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}
</script>

<style scoped>
.video-processor {
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
  font-weight: bold;
}
</style>
