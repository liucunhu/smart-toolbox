<template>
  <div class="visual-synthesis">
    <el-row :gutter="20">
      <!-- 封面生成 -->
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>🎨 智能封面生成</span>
            </div>
          </template>

          <el-form label-width="100px">
            <el-form-item label="视频文件">
              <el-upload
                action="#"
                :auto-upload="false"
                :on-change="handleVideoSelect"
                :limit="1"
              >
                <el-button type="primary">选择视频</el-button>
              </el-upload>
            </el-form-item>

            <el-form-item label="目标平台">
              <el-select v-model="coverForm.platform" placeholder="请选择平台">
                <el-option label="抖音 (9:16)" value="douyin" />
                <el-option label="小红书 (3:4)" value="xiaohongshu" />
                <el-option label="B站 (16:9)" value="bilibili" />
                <el-option label="头条 (16:9)" value="toutiao" />
              </el-select>
            </el-form-item>

            <el-form-item label="封面标题">
              <el-input v-model="coverForm.title" placeholder="输入封面标题（可选）" />
            </el-form-item>

            <el-form-item>
              <el-button type="primary" @click="generateCover" :loading="generating" style="width: 100%;">
                ✨ 生成封面
              </el-button>
            </el-form-item>
          </el-form>

          <!-- 封面预览 -->
          <div v-if="coverPreview" class="preview-area">
            <h4>封面预览：</h4>
            <img :src="coverPreview" alt="封面预览" style="max-width: 100%; border-radius: 8px;" />
            <el-button type="success" @click="downloadCover" style="margin-top: 10px;">
              💾 下载封面
            </el-button>
          </div>
        </el-card>
      </el-col>

      <!-- 情绪字幕编辑 -->
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>💬 情绪字幕系统</span>
            </div>
          </template>

          <el-form label-width="100px">
            <el-form-item label="视频文件">
              <el-upload
                action="#"
                :auto-upload="false"
                :on-change="handleSubtitleVideoSelect"
                :limit="1"
              >
                <el-button type="primary">选择视频</el-button>
              </el-upload>
            </el-form-item>

            <el-form-item label="字幕内容">
              <el-input
                v-model="subtitleText"
                type="textarea"
                :rows="4"
                placeholder="输入字幕文本，每行一条..."
              />
            </el-form-item>

            <el-form-item label="情绪类型">
              <el-select v-model="subtitleEmotion" placeholder="选择情绪">
                <el-option label="积极 (绿色)" value="positive" />
                <el-option label="兴奋 (红色)" value="excited" />
                <el-option label="中性 (白色)" value="neutral" />
                <el-option label="悲伤 (灰色)" value="sad" />
              </el-select>
            </el-form-item>

            <el-form-item>
              <el-button type="primary" @click="addSubtitles" :loading="adding" style="width: 100%;">
                ➕ 添加字幕
              </el-button>
            </el-form-item>
          </el-form>

          <!-- 字幕列表 -->
          <div v-if="subtitles.length > 0" style="margin-top: 20px;">
            <h4>字幕列表：</h4>
            <el-table :data="subtitles" style="width: 100%">
              <el-table-column prop="text" label="字幕文本" min-width="200" />
              <el-table-column prop="emotion" label="情绪" width="100">
                <template #default="{ row }">
                  <el-tag :type="getEmotionType(row.emotion)">{{ row.emotion }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="100">
                <template #default="{ $index }">
                  <el-button type="danger" size="small" @click="removeSubtitle($index)">删除</el-button>
                </template>
              </el-table-column>
            </el-table>

            <el-button type="success" @click="applySubtitles" :loading="applying" style="margin-top: 10px; width: 100%;">
              ✅ 应用字幕到视频
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- BGM匹配 -->
    <el-row style="margin-top: 20px;">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>🎵 BGM智能匹配</span>
            </div>
          </template>

          <el-form :inline="true">
            <el-form-item label="视频文件">
              <el-upload
                action="#"
                :auto-upload="false"
                :on-change="handleBgmVideoSelect"
                :limit="1"
              >
                <el-button type="primary">选择视频</el-button>
              </el-upload>
            </el-form-item>

            <el-form-item>
              <el-button type="primary" @click="matchBGM" :loading="matching">
                🎼 自动匹配BGM
              </el-button>
            </el-form-item>
          </el-form>

          <el-alert
            v-if="bgmResult"
            :title="`BGM匹配成功: ${bgmResult.output_path}`"
            type="success"
            :closable="false"
            style="margin-top: 10px;"
          />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'

// 封面生成
const generating = ref(false)
const coverForm = ref({
  videoFile: null as File | null,
  platform: 'douyin',
  title: ''
})
const coverPreview = ref('')

// 字幕编辑
const adding = ref(false)
const applying = ref(false)
const subtitleVideoFile = ref<File | null>(null)
const subtitleText = ref('')
const subtitleEmotion = ref('positive')
const subtitles = ref<any[]>([])

// BGM匹配
const matching = ref(false)
const bgmVideoFile = ref<File | null>(null)
const bgmResult = ref<any>(null)

// 选择视频文件
const handleVideoSelect = (file: any) => {
  coverForm.value.videoFile = file.raw
}

const handleSubtitleVideoSelect = (file: any) => {
  subtitleVideoFile.value = file.raw
}

const handleBgmVideoSelect = (file: any) => {
  bgmVideoFile.value = file.raw
}

// 生成封面
const generateCover = async () => {
  if (!coverForm.value.videoFile) {
    ElMessage.warning('请选择视频文件')
    return
  }

  generating.value = true
  try {
    const formData = new FormData()
    formData.append('video', coverForm.value.videoFile)
    formData.append('platform', coverForm.value.platform)
    formData.append('title', coverForm.value.title)

    const response = await axios.post(`${API_BASE_URL}/content/generate-cover`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })

    coverPreview.value = response.data.cover_url
    ElMessage.success('封面生成成功')
  } catch (error) {
    console.error('封面生成失败:', error)
    ElMessage.error('封面生成失败')
  } finally {
    generating.value = false
  }
}

// 下载封面
const downloadCover = () => {
  if (coverPreview.value) {
    const link = document.createElement('a')
    link.href = coverPreview.value
    link.download = 'cover.jpg'
    link.click()
  }
}

// 添加字幕
const addSubtitles = async () => {
  if (!subtitleText.value) {
    ElMessage.warning('请输入字幕文本')
    return
  }

  const lines = subtitleText.value.split('\n').filter(line => line.trim())
  
  lines.forEach((line, index) => {
    subtitles.value.push({
      text: line,
      start: index * 3,
      end: (index + 1) * 3,
      emotion: subtitleEmotion.value
    })
  })

  subtitleText.value = ''
  ElMessage.success(`已添加 ${lines.length} 条字幕`)
}

// 移除字幕
const removeSubtitle = (index: number) => {
  subtitles.value.splice(index, 1)
}

// 应用字幕
const applySubtitles = async () => {
  if (!subtitleVideoFile.value) {
    ElMessage.warning('请选择视频文件')
    return
  }

  if (subtitles.value.length === 0) {
    ElMessage.warning('请至少添加一条字幕')
    return
  }

  applying.value = true
  try {
    const formData = new FormData()
    formData.append('video', subtitleVideoFile.value)
    formData.append('subtitles', JSON.stringify(subtitles.value))

    const response = await axios.post(`${API_BASE_URL}/content/add-subtitles`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })

    ElMessage.success('字幕添加成功')
  } catch (error) {
    console.error('字幕添加失败:', error)
    ElMessage.error('字幕添加失败')
  } finally {
    applying.value = false
  }
}

// 匹配BGM
const matchBGM = async () => {
  if (!bgmVideoFile.value) {
    ElMessage.warning('请选择视频文件')
    return
  }

  matching.value = true
  try {
    const formData = new FormData()
    formData.append('video', bgmVideoFile.value)
    formData.append('platform', 'douyin')

    const response = await axios.post(`${API_BASE_URL}/content/match-bgm`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })

    bgmResult.value = response.data
    ElMessage.success('BGM匹配成功')
  } catch (error) {
    console.error('BGM匹配失败:', error)
    ElMessage.error('BGM匹配失败')
  } finally {
    matching.value = false
  }
}

// 情绪类型映射
const getEmotionType = (emotion: string) => {
  const typeMap: any = {
    'positive': 'success',
    'excited': 'danger',
    'neutral': 'info',
    'sad': 'warning'
  }
  return typeMap[emotion] || 'info'
}
</script>

<style scoped>
.visual-synthesis { padding: 20px; }
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
}
.preview-area {
  margin-top: 20px;
  text-align: center;
}
</style>
