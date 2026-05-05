<template>
  <div class="image-generation">
    <el-row :gutter="20">
      <!-- 单张图像生成 -->
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>🎨 AI单张配图生成</span>
            </div>
          </template>

          <el-form label-width="100px">
            <el-form-item label="图像描述">
              <el-input 
                v-model="singleForm.prompt" 
                type="textarea"
                :rows="3"
                placeholder="例如：A beautiful sunset over mountains with clouds"
              />
            </el-form-item>

            <el-form-item label="风格">
              <el-select v-model="singleForm.style" placeholder="选择风格">
                <el-option label="写实" value="realistic" />
                <el-option label="插画" value="illustration" />
                <el-option label="卡通" value="cartoon" />
                <el-option label="动漫" value="anime" />
                <el-option label="油画" value="oil_painting" />
                <el-option label="水彩" value="watercolor" />
                <el-option label="极简" value="minimalist" />
              </el-select>
            </el-form-item>

            <el-form-item label="宽高比">
              <el-select v-model="singleForm.aspect_ratio" placeholder="选择比例">
                <el-option label="16:9 (横屏)" value="16:9" />
                <el-option label="9:16 (竖屏)" value="9:16" />
                <el-option label="1:1 (方形)" value="1:1" />
                <el-option label="3:4 (小红书)" value="3:4" />
              </el-select>
            </el-form-item>

            <el-form-item>
              <el-button 
                type="primary" 
                @click="generateSingleImage" 
                :loading="generating"
                style="width: 100%;"
              >
                ✨ 生成图像
              </el-button>
            </el-form-item>
          </el-form>

          <!-- 预览 -->
          <div v-if="singleResult" class="preview-area">
            <h4>生成结果：</h4>
            <img 
              v-if="singleResult.image_url" 
              :src="'http://localhost:8000' + singleResult.image_url" 
              alt="生成的图像" 
              style="max-width: 100%; border-radius: 8px;" 
            />
            <el-alert
              v-if="singleResult.status === 'failed'"
              :title="singleResult.error"
              type="error"
              :closable="false"
            />
          </div>
        </el-card>
      </el-col>

      <!-- 文章自动配图 -->
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>📝 文章自动配图</span>
            </div>
          </template>

          <el-form label-width="100px">
            <el-form-item label="文章内容">
              <el-input 
                v-model="articleForm.content" 
                type="textarea"
                :rows="8"
                placeholder="粘贴文章内容，系统将自动提取关键点并生成配图"
              />
            </el-form-item>

            <el-form-item label="配图数量">
              <el-input-number v-model="articleForm.num_images" :min="1" :max="10" />
            </el-form-item>

            <el-form-item label="风格">
              <el-select v-model="articleForm.style" placeholder="选择风格">
                <el-option label="写实" value="realistic" />
                <el-option label="插画" value="illustration" />
                <el-option label="极简" value="minimalist" />
              </el-select>
            </el-form-item>

            <el-form-item>
              <el-button 
                type="success" 
                @click="generateArticleImages" 
                :loading="generatingArticle"
                style="width: 100%;"
              >
                🚀 自动生成配图
              </el-button>
            </el-form-item>
          </el-form>

          <!-- 结果展示 -->
          <div v-if="articleResults.length > 0" class="results-grid">
            <h4>生成的配图（{{ articleResults.length }}张）：</h4>
            <el-row :gutter="10">
              <el-col 
                v-for="(img, index) in articleResults" 
                :key="index" 
                :span="8"
                style="margin-bottom: 10px;"
              >
                <el-card :body-style="{ padding: '0px' }">
                  <img 
                    v-if="img.image_url"
                    :src="'http://localhost:8000' + img.image_url" 
                    style="width: 100%; display: block;"
                  />
                  <div style="padding: 5px;">
                    <el-text size="small">{{ img.related_text?.substring(0, 30) }}...</el-text>
                  </div>
                </el-card>
              </el-col>
            </el-row>
          </div>
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
          <h4>🎯 单张生成</h4>
          <ul>
            <li>输入详细的图像描述</li>
            <li>选择合适的风格和比例</li>
            <li>支持7种艺术风格</li>
            <li>生成时间约10-30秒</li>
          </ul>
        </el-col>

        <el-col :span="8">
          <h4>📄 文章配图</h4>
          <ul>
            <li>自动提取文章关键点</li>
            <li>为每个关键点生成配图</li>
            <li>智能匹配内容主题</li>
            <li>适合长文插图需求</li>
          </ul>
        </el-col>

        <el-col :span="8">
          <h4>⚙️ 配置说明</h4>
          <ul>
            <li>需配置AI API密钥</li>
            <li>支持Stability AI</li>
            <li>支持DALL-E 3</li>
            <li>图片保存在output/images</li>
          </ul>
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import apiClient from '../utils/api'
import { ElMessage } from 'element-plus'

// 单张生成
const generating = ref(false)
const singleForm = ref({
  prompt: '',
  style: 'realistic',
  aspect_ratio: '16:9'
})
const singleResult = ref<any>(null)

// 文章配图
const generatingArticle = ref(false)
const articleForm = ref({
  content: '',
  num_images: 3,
  style: 'realistic'
})
const articleResults = ref<any[]>([])

// 生成单张图像
const generateSingleImage = async () => {
  if (!singleForm.value.prompt) {
    ElMessage.warning('请输入图像描述')
    return
  }

  generating.value = true
  try {
    const response = await apiClient.post('/content/generate-image', null, {
      params: {
        prompt: singleForm.value.prompt,
        style: singleForm.value.style,
        aspect_ratio: singleForm.value.aspect_ratio
      }
    })

    singleResult.value = response.data

    if (response.data.status === 'success') {
      ElMessage.success('图像生成成功！')
    } else {
      ElMessage.error('生成失败：' + response.data.error)
    }
  } catch (error: any) {
    console.error('生成失败:', error)
    ElMessage.error('生成失败：' + (error.response?.data?.detail || error.message))
  } finally {
    generating.value = false
  }
}

// 生成文章配图
const generateArticleImages = async () => {
  if (!articleForm.value.content) {
    ElMessage.warning('请输入文章内容')
    return
  }

  generatingArticle.value = true
  articleResults.value = []

  try {
    const response = await apiClient.post('/content/generate-article-images', null, {
      params: {
        article_content: articleForm.value.content,
        num_images: articleForm.value.num_images,
        style: articleForm.value.style
      }
    })

    if (response.data.images && response.data.images.length > 0) {
      articleResults.value = response.data.images
      ElMessage.success(`成功生成${response.data.total}张配图！`)
    } else {
      ElMessage.warning('未生成任何配图')
    }
  } catch (error: any) {
    console.error('生成失败:', error)
    ElMessage.error('生成失败：' + (error.response?.data?.detail || error.message))
  } finally {
    generatingArticle.value = false
  }
}
</script>

<style scoped>
.image-generation { padding: 20px; }
.card-header { font-weight: bold; }
.preview-area { margin-top: 20px; }
.results-grid { margin-top: 20px; }
</style>
