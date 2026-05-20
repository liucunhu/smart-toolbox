<template>
  <div class="subtitle-editor">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>📝 字幕编辑器</span>
        </div>
      </template>

      <el-row :gutter="20">
        <!-- 左侧：字幕生成 -->
        <el-col :span="12">
          <el-card shadow="never">
            <template #header>
              <div class="sub-header">字幕生成</div>
            </template>
            
            <el-form label-width="100px">
              <el-form-item label="视频文件">
                <el-upload
                  action="#"
                  :auto-upload="false"
                  :on-change="handleVideoSelect"
                  accept="video/*"
                >
                  <el-button type="primary">
                    <el-icon><Upload /></el-icon>
                    选择视频
                  </el-button>
                </el-upload>
                <div v-if="selectedVideo" style="margin-top: 10px; color: #666;">
                  已选择: {{ selectedVideo.name }}
                </div>
              </el-form-item>
              
              <el-form-item label="语言">
                <el-select v-model="subtitleForm.language" style="width: 100%">
                  <el-option label="中文" value="zh" />
                  <el-option label="英文" value="en" />
                  <el-option label="日语" value="ja" />
                  <el-option label="韩语" value="ko" />
                </el-select>
              </el-form-item>
              
              <el-form-item>
                <el-button type="primary" @click="handleGenerateSubtitle" :loading="generating">
                  <el-icon><VideoCamera /></el-icon>
                  生成字幕
                </el-button>
              </el-form-item>
            </el-form>

            <!-- 字幕编辑区 -->
            <div v-if="subtitles.length > 0" style="margin-top: 20px;">
              <div class="section-title">字幕列表</div>
              <el-table :data="subtitles" max-height="400" border>
                <el-table-column prop="index" label="序号" width="60" />
                <el-table-column prop="start_time" label="开始时间" width="100" />
                <el-table-column prop="end_time" label="结束时间" width="100" />
                <el-table-column prop="text" label="字幕内容">
                  <template #default="{ row }">
                    <el-input v-model="row.text" size="small" />
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="80">
                  <template #default="{ $index }">
                    <el-button 
                      size="small" 
                      type="danger" 
                      link
                      @click="handleDeleteSubtitle($index)"
                    >
                      删除
                    </el-button>
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </el-card>
        </el-col>

        <!-- 右侧：背景音乐和音效 -->
        <el-col :span="12">
          <el-card shadow="never" style="margin-bottom: 20px;">
            <template #header>
              <div class="sub-header">🎵 背景音乐匹配</div>
            </template>
            
            <el-form label-width="100px">
              <el-form-item label="视频情感">
                <el-select v-model="bgmForm.emotion" style="width: 100%">
                  <el-option label="欢快" value="happy" />
                  <el-option label="悲伤" value="sad" />
                  <el-option label="激昂" value="excited" />
                  <el-option label="平静" value="calm" />
                  <el-option label="悬疑" value="suspense" />
                </el-select>
              </el-form-item>
              
              <el-form-item label="视频时长">
                <el-input-number 
                  v-model="bgmForm.duration" 
                  :min="1" 
                  :max="3600"
                  style="width: 100%"
                />
                <span style="margin-left: 10px;">秒</span>
              </el-form-item>
              
              <el-form-item>
                <el-button type="primary" @click="handleMatchBGM" :loading="matching">
                  <el-icon><Headset /></el-icon>
                  匹配音乐
                </el-button>
              </el-form-item>
            </el-form>

            <!-- 音乐推荐列表 -->
            <div v-if="bgmRecommendations.length > 0" style="margin-top: 15px;">
              <div class="section-title">推荐音乐</div>
              <el-table :data="bgmRecommendations" max-height="200" border>
                <el-table-column prop="name" label="音乐名称" />
                <el-table-column prop="duration" label="时长" width="80">
                  <template #default="{ row }">
                    {{ row.duration }}s
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="100">
                  <template #default="{ row }">
                    <el-button size="small" type="primary" link>
                      试听
                    </el-button>
                    <el-button size="small" type="success" link>
                      应用
                    </el-button>
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </el-card>

          <el-card shadow="never">
            <template #header>
              <div class="sub-header">🔊 音效添加</div>
            </template>
            
            <el-form label-width="100px">
              <el-form-item label="音效类型">
                <el-select v-model="soundEffectForm.type" style="width: 100%">
                  <el-option label="转场音效" value="transition" />
                  <el-option label="强调音效" value="emphasis" />
                  <el-option label="环境音效" value="ambient" />
                  <el-option label="提示音效" value="notification" />
                </el-select>
              </el-form-item>
              
              <el-form-item label="添加位置">
                <el-input-number 
                  v-model="soundEffectForm.position" 
                  :min="0" 
                  :max="3600"
                  style="width: 100%"
                />
                <span style="margin-left: 10px;">秒</span>
              </el-form-item>
              
              <el-form-item>
                <el-button type="primary" @click="handleAddSoundEffect" :loading="adding">
                  <el-icon><Bell /></el-icon>
                  添加音效
                </el-button>
              </el-form-item>
            </el-form>

            <!-- 已添加音效列表 -->
            <div v-if="addedEffects.length > 0" style="margin-top: 15px;">
              <div class="section-title">已添加音效</div>
              <el-table :data="addedEffects" max-height="200" border>
                <el-table-column prop="type" label="类型" width="100" />
                <el-table-column prop="position" label="位置" width="80">
                  <template #default="{ row }">
                    {{ row.position }}s
                  </template>
                </el-table-column>
                <el-table-column prop="name" label="音效名称" />
                <el-table-column label="操作" width="80">
                  <template #default="{ $index }">
                    <el-button 
                      size="small" 
                      type="danger" 
                      link
                      @click="handleDeleteEffect($index)"
                    >
                      删除
                    </el-button>
                  </template>
                </el-table-column>
              </el-table>
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
import { Upload, VideoCamera, Headset, Bell } from '@element-plus/icons-vue'
import apiClient from '../utils/api'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'

const selectedVideo = ref<File | null>(null)
const generating = ref(false)
const matching = ref(false)
const adding = ref(false)

const subtitleForm = ref({
  language: 'zh'
})

const bgmForm = ref({
  emotion: 'happy',
  duration: 60
})

const soundEffectForm = ref({
  type: 'transition',
  position: 0
})

const subtitles = ref<any[]>([])
const bgmRecommendations = ref<any[]>([])
const addedEffects = ref<any[]>([])

/**
 * 处理视频选择
 */
const handleVideoSelect = (file: any) => {
  selectedVideo.value = file.raw
}

/**
 * 生成字幕
 */
const handleGenerateSubtitle = async () => {
  if (!selectedVideo.value) {
    ElMessage.warning('请先选择视频文件')
    return
  }
  
  generating.value = true
  try {
    const formData = new FormData()
    formData.append('video', selectedVideo.value)
    formData.append('language', subtitleForm.value.language)
    
    const response = await apiClient.post(`${API_BASE_URL}/subtitle/generate`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    
    if (response.data.status === 'success' || response.data.subtitles) {
      subtitles.value = response.data.subtitles || response.data.data || []
      ElMessage.success('字幕生成成功')
    } else {
      ElMessage.error('生成失败：' + (response.data.message || '未知错误'))
    }
  } catch (error: any) {
    console.error('生成字幕失败:', error)
    ElMessage.error('生成失败，请检查后端服务')
  } finally {
    generating.value = false
  }
}

/**
 * 删除字幕
 */
const handleDeleteSubtitle = (index: number) => {
  subtitles.value.splice(index, 1)
}

/**
 * 匹配背景音乐
 */
const handleMatchBGM = async () => {
  matching.value = true
  try {
    const response = await apiClient.post(`${API_BASE_URL}/subtitle/match-bgm`, {
      emotion: bgmForm.value.emotion,
      duration: bgmForm.value.duration
    })
    
    if (response.data.status === 'success' || response.data.recommendations) {
      bgmRecommendations.value = response.data.recommendations || response.data.data || []
      ElMessage.success('音乐匹配成功')
    } else {
      ElMessage.error('匹配失败：' + (response.data.message || '未知错误'))
    }
  } catch (error: any) {
    console.error('匹配音乐失败:', error)
    ElMessage.error('匹配失败，请检查后端服务')
  } finally {
    matching.value = false
  }
}

/**
 * 添加音效
 */
const handleAddSoundEffect = async () => {
  adding.value = true
  try {
    const response = await apiClient.post(`${API_BASE_URL}/subtitle/add-sound-effect`, {
      effect_type: soundEffectForm.value.type,
      position: soundEffectForm.value.position
    })
    
    if (response.data.status === 'success' || response.data.effect) {
      addedEffects.value.push(response.data.effect || response.data.data)
      ElMessage.success('音效添加成功')
    } else {
      ElMessage.error('添加失败：' + (response.data.message || '未知错误'))
    }
  } catch (error: any) {
    console.error('添加音效失败:', error)
    ElMessage.error('添加失败，请检查后端服务')
  } finally {
    adding.value = false
  }
}

/**
 * 删除音效
 */
const handleDeleteEffect = (index: number) => {
  addedEffects.value.splice(index, 1)
}
</script>

<style scoped>
.subtitle-editor {
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

.section-title {
  font-weight: bold;
  margin-bottom: 10px;
  color: #333;
  font-size: 14px;
}
</style>
