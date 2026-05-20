<template>
  <div class="article-analytics">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>📊 文章数据分析</span>
          <el-space>
            <el-select v-model="selectedAccountId" placeholder="选择账号" style="width: 200px;">
              <el-option
                v-for="account in accounts"
                :key="account.id"
                :label="account.username || `账号${account.id}`"
                :value="account.id"
              />
            </el-select>
            <el-button type="primary" @click="fetchAnalytics" :loading="loading">
              🔄 刷新数据
            </el-button>
          </el-space>
        </div>
      </template>

      <!-- 汇总统计 -->
      <el-row :gutter="20" v-if="analyticsData.articles && analyticsData.articles.length > 0">
        <el-col :span="6">
          <el-card shadow="hover" class="stat-card">
            <div class="stat-content">
              <div class="stat-icon" style="background: #409EFF;">
                <el-icon :size="30"><Document /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-label">文章总数</div>
                <div class="stat-value">{{ totalArticles }}</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="hover" class="stat-card">
            <div class="stat-content">
              <div class="stat-icon" style="background: #909399;">
                <el-icon :size="30"><View /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-label">总展现数</div>
                <div class="stat-value">{{ totalShows }}</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="hover" class="stat-card">
            <div class="stat-content">
              <div class="stat-icon" style="background: #67C23A;">
                <el-icon :size="30"><View /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-label">总阅读量</div>
                <div class="stat-value">{{ totalReads }}</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="hover" class="stat-card">
            <div class="stat-content">
              <div class="stat-icon" style="background: #E6A23C;">
                <el-icon :size="30"><Star /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-label">总点赞数</div>
                <div class="stat-value">{{ totalLikes }}</div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
      
      <!-- 第二行统计卡片 -->
      <el-row :gutter="20" v-if="analyticsData.articles && analyticsData.articles.length > 0">
        <el-col :span="6">
          <el-card shadow="hover" class="stat-card">
            <div class="stat-content">
              <div class="stat-icon" style="background: #F56C6C;">
                <el-icon :size="30"><ChatDotRound /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-label">总评论数</div>
                <div class="stat-value">{{ totalComments }}</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="hover" class="stat-card">
            <div class="stat-content">
              <div class="stat-icon" style="background: #9b59b6;">
                <el-icon :size="30"><Share /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-label">总转发数</div>
                <div class="stat-value">{{ totalShares }}</div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 文章列表 -->
      <el-table :data="analyticsData.articles || []" style="width: 100%; margin-top: 20px;" v-loading="loading">
        <el-table-column prop="title" label="文章标题" min-width="250">
          <template #default="{ row }">
            <el-tooltip :content="row.title" placement="top">
              <span>{{ truncateText(row.title, 40) }}</span>
            </el-tooltip>
          </template>
        </el-table-column>
        <el-table-column prop="publish_time" label="发布时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.publish_time) }}
          </template>
        </el-table-column>
        <el-table-column prop="show_count" label="展现数" width="100" sortable>
          <template #default="{ row }">
            <span style="color: #909399; font-weight: bold;">{{ row.show_count || 0 }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="read_count" label="阅读量" width="100" sortable>
          <template #default="{ row }">
            <span style="color: #409EFF; font-weight: bold;">{{ row.read_count || 0 }}</span>
          </template>
        </el-table-column>
        <el-table-column label="阅读率" width="100" sortable>
          <template #default="{ row }">
            <span :style="getReadRateStyle(row)">{{ calculateReadRate(row) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="like_count" label="点赞数" width="100" sortable>
          <template #default="{ row }">
            <span style="color: #67C23A; font-weight: bold;">{{ row.like_count || 0 }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="comment_count" label="评论数" width="100" sortable>
          <template #default="{ row }">
            <span style="color: #E6A23C; font-weight: bold;">{{ row.comment_count || 0 }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="share_count" label="转发数" width="100" sortable>
          <template #default="{ row }">
            <span style="color: #9b59b6;">{{ row.share_count || 0 }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="viewArticle(row)">
              查看详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 空状态 -->
      <el-empty v-if="!loading && (!analyticsData.articles || analyticsData.articles.length === 0)" description="暂无数据">
        <template #description>
          <p>可能的原因：</p>
          <ul style="text-align: left; color: #909399; font-size: 14px;">
            <li>1. 该账号尚未发布过文章</li>
            <li>2. Cookie 已过期，请重新登录账号</li>
            <li>3. 头条后台页面结构变化</li>
          </ul>
        </template>
        <el-button type="primary" @click="fetchAnalytics">刷新数据</el-button>
        <el-button type="success" @click="goToAccountManagement">去登录账号</el-button>
      </el-empty>

      <!-- 📊 智能分析结果 -->
      <el-card v-if="analyticsData.analysis" shadow="never" style="margin-top: 20px; border: 2px solid #409EFF;">
        <template #header>
          <div class="analysis-header">
            <span style="font-size: 18px; font-weight: bold;">🎯 智能分析与优化建议</span>
            <el-tag type="success" size="large">AI驱动</el-tag>
          </div>
        </template>

        <!-- 性能洞察 -->
        <el-descriptions :column="3" border v-if="analyticsData.analysis.performance_insights">
          <el-descriptions-item label="阅读率等级">
            <el-tag :type="getLevelTagType(analyticsData.analysis.performance_insights.read_rate_level)">
              {{ analyticsData.analysis.performance_insights.read_rate_level }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="互动率等级">
            <el-tag :type="getLevelTagType(analyticsData.analysis.performance_insights.interaction_level)">
              {{ analyticsData.analysis.performance_insights.interaction_level }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="内容稳定性">
            <el-tag :type="getContentStabilityType(analyticsData.analysis.performance_insights.content_consistency)">
              {{ analyticsData.analysis.performance_insights.content_consistency }}
            </el-tag>
          </el-descriptions-item>
        </el-descriptions>

        <!-- 详细建议 -->
        <el-divider content-position="left">💡 深度分析建议</el-divider>
        <el-alert
          v-for="(suggestion, index) in analyticsData.analysis.suggestions"
          :key="index"
          :title="suggestion"
          type="info"
          :closable="false"
          show-icon
          style="margin-bottom: 10px;"
        />

        <!-- 🚀 优化的提示词模板（最重要） -->
        <el-divider content-position="left">📝 优化的文章生成提示词</el-divider>
        <el-card shadow="hover" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;">
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <span style="font-weight: bold; font-size: 16px;">✨ AI生成的最佳实践提示词</span>
              <el-button type="primary" size="small" @click="copyPromptTemplate" plain>
                <el-icon><DocumentCopy /></el-icon>
                复制提示词
              </el-button>
            </div>
          </template>
          <div style="white-space: pre-wrap; line-height: 1.8; font-size: 14px; max-height: 500px; overflow-y: auto;">
            {{ analyticsData.analysis.optimized_prompt_template || '暂无优化提示词' }}
          </div>
        </el-card>

        <!-- 内容策略 -->
        <el-divider content-position="left" v-if="analyticsData.analysis.content_strategy">🎯 内容策略建议</el-divider>
        <el-row :gutter="20" v-if="analyticsData.analysis.content_strategy">
          <el-col :span="12">
            <el-card shadow="hover">
              <template #header>
                <span style="font-weight: bold;">推荐选题方向</span>
              </template>
              <el-tag
                v-for="topic in analyticsData.analysis.content_strategy.high_performing_topics"
                :key="topic"
                style="margin: 5px;"
                type="success"
              >
                {{ topic }}
              </el-tag>
            </el-card>
          </el-col>
          <el-col :span="12">
            <el-card shadow="hover">
              <template #header>
                <span style="font-weight: bold;">标题格式建议</span>
              </template>
              <el-tag
                v-for="format in analyticsData.analysis.content_strategy.recommended_title_formats"
                :key="format"
                style="margin: 5px;"
                type="warning"
              >
                {{ format }}
              </el-tag>
            </el-card>
          </el-col>
        </el-row>
      </el-card>

      <!-- 🚀 智能优化建议（新增） -->
      <el-card v-if="hasSmartOptimization" shadow="never" style="margin-top: 20px; border: 2px solid #67C23A;">
        <template #header>
          <div class="analysis-header">
            <span style="font-size: 18px; font-weight: bold;">🤖 智能内容优化建议</span>
            <el-tag type="success" size="large">AI驱动</el-tag>
          </div>
        </template>

        <!-- 标题优化分析 -->
        <el-divider content-position="left">✍️ 标题优化分析</el-divider>
        <el-descriptions :column="2" border v-if="currentArticle?.smart_optimization?.title_optimization">
          <el-descriptions-item label="当前长度">
            {{ currentArticle.smart_optimization.title_optimization.current_length }}字
          </el-descriptions-item>
          <el-descriptions-item label="最佳范围">
            {{ currentArticle.smart_optimization.title_optimization.optimal_range[0] }}-{{ currentArticle.smart_optimization.title_optimization.optimal_range[1] }}字
          </el-descriptions-item>
        </el-descriptions>
        
        <el-alert
          v-for="(suggestion, index) in currentArticle?.smart_optimization?.title_optimization?.suggestions"
          :key="'title-' + index"
          :title="suggestion.recommendation"
          :type="suggestion.issue ? 'warning' : 'success'"
          :closable="false"
          show-icon
          style="margin-bottom: 8px;"
        />

        <!-- 🖼️ 智能图片位置建议 -->
        <el-divider content-position="left" v-if="currentArticle?.smart_optimization?.image_suggestions">🖼️ 智能图片位置建议</el-divider>
        <el-timeline v-if="currentArticle?.smart_optimization?.image_suggestions">
          <el-timeline-item
            v-for="(img, index) in currentArticle.smart_optimization.image_suggestions"
            :key="index"
            :timestamp="`第${img.position + 1}段落后`"
            placement="top"
          >
            <el-card>
              <h4>{{ img.theme }}</h4>
              <p style="color: #606266; margin: 8px 0;">{{ img.rationale }}</p>
              <el-tag size="small" type="info">{{ img.location_type }}</el-tag>
              <p style="font-size: 12px; color: #909399; margin-top: 8px;">
                预览: {{ img.preview_text }}
              </p>
            </el-card>
          </el-timeline-item>
        </el-timeline>

        <!-- 💬 互动优化建议 -->
        <el-divider content-position="left" v-if="currentArticle?.smart_optimization?.engagement_tips">💬 互动优化建议</el-divider>
        <el-alert
          v-for="(tip, index) in currentArticle?.smart_optimization?.engagement_tips"
          :key="'engagement-' + index"
          :title="tip"
          type="success"
          :closable="false"
          show-icon
          style="margin-bottom: 8px;"
        />

        <!-- ⏰ 最佳发布时间 -->
        <el-divider content-position="left" v-if="currentArticle?.smart_optimization?.publishing_tips">⏰ 最佳发布时间</el-divider>
        <el-row :gutter="20" v-if="currentArticle?.smart_optimization?.publishing_tips">
          <el-col :span="8" v-for="(time_slot, index) in currentArticle.smart_optimization.publishing_tips.best_times" :key="index">
            <el-card shadow="hover">
              <div style="text-align: center;">
                <div style="font-size: 24px; font-weight: bold; color: #409EFF;">{{ time_slot.time }}</div>
                <div style="color: #606266; margin-top: 8px;">{{ time_slot.reason }}</div>
              </div>
            </el-card>
          </el-col>
        </el-row>
        <el-alert
          v-if="currentArticle?.smart_optimization?.publishing_tips?.recommendation"
          :title="currentArticle.smart_optimization.publishing_tips.recommendation"
          type="info"
          :closable="false"
          show-icon
          style="margin-top: 10px;"
        />
      </el-card>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import apiClient from '../utils/api'
import { ElMessage } from 'element-plus'
import { Document, View, Star, ChatDotRound, Share, DocumentCopy } from '@element-plus/icons-vue'

const loading = ref(false)
const accounts = ref<any[]>([])
const selectedAccountId = ref<number | null>(null)
const analyticsData = ref<any>({ articles: [] })

// 计算是否有智能优化数据
const hasSmartOptimization = computed(() => {
  return analyticsData.value.articles?.some((article: any) => 
    article.smart_optimization && Object.keys(article.smart_optimization).length > 0
  ) || false
})

// 获取当前文章（用于展示智能优化建议）
const currentArticle = computed(() => {
  // 返回第一有智能优化数据的文章
  return analyticsData.value.articles?.find((article: any) => 
    article.smart_optimization && Object.keys(article.smart_optimization).length > 0
  ) || null
})

// 计算汇总数据
const totalArticles = computed(() => analyticsData.value.articles?.length || 0)
const totalShows = computed(() => {
  return analyticsData.value.articles?.reduce((sum: number, article: any) => sum + (article.show_count || 0), 0) || 0
})
const totalReads = computed(() => {
  return analyticsData.value.articles?.reduce((sum: number, article: any) => sum + (article.read_count || 0), 0) || 0
})
const totalLikes = computed(() => {
  return analyticsData.value.articles?.reduce((sum: number, article: any) => sum + (article.like_count || 0), 0) || 0
})
const totalComments = computed(() => {
  return analyticsData.value.articles?.reduce((sum: number, article: any) => sum + (article.comment_count || 0), 0) || 0
})
const totalShares = computed(() => {
  return analyticsData.value.articles?.reduce((sum: number, article: any) => sum + (article.share_count || 0), 0) || 0
})

// 获取头条账号列表
const fetchAccounts = async () => {
  try {
    const response = await apiClient.get('/accounts/list', {
      params: {
        platform: 'toutiao',
        page: 1,
        page_size: 100
      }
    })
    accounts.value = response.data.data.items
    
    // 默认选择第一个账号
    if (accounts.value.length > 0 && !selectedAccountId.value) {
      selectedAccountId.value = accounts.value[0].id
    }
  } catch (error) {
    console.error('获取账号列表失败:', error)
    ElMessage.error('获取账号列表失败')
  }
}

// 获取文章数据分析
const fetchAnalytics = async () => {
  if (!selectedAccountId.value) {
    ElMessage.warning('请先选择账号')
    return
  }

  loading.value = true
  try {
    // 调用新的 API 端点
    const response = await apiClient.get(`/analytics/articles/${selectedAccountId.value}`)
    
    if (response.data.status === 'success') {
      analyticsData.value = response.data
      
      // 显示简要建议（可选）
      if (response.data.analysis?.suggestions && response.data.analysis.suggestions.length > 0) {
        ElMessage.success(`分析完成！获取到 ${response.data.analysis.suggestions.length} 条优化建议`)
      } else {
        ElMessage.success('数据刷新成功')
      }
    } else {
      ElMessage.error(response.data.message || '获取数据失败')
    }
  } catch (error: any) {
    console.error('获取文章数据分析失败:', error)
    ElMessage.error('获取数据失败：' + (error.response?.data?.detail || error.message))
  } finally {
    loading.value = false
  }
}

// 复制提示词模板
const copyPromptTemplate = () => {
  const template = analyticsData.value.analysis?.optimized_prompt_template
  if (!template) {
    ElMessage.warning('暂无优化的提示词模板')
    return
  }
  
  navigator.clipboard.writeText(template).then(() => {
    ElMessage.success('✅ 提示词已复制到剪贴板，可直接用于文章生成！')
  }).catch(() => {
    ElMessage.error('复制失败，请手动复制')
  })
}

// 获取等级标签类型
const getLevelTagType = (level: string) => {
  const typeMap: Record<string, string> = {
    '优秀': 'success',
    '良好': '',
    '需优化': 'warning',
    '较差': 'danger'
  }
  return typeMap[level] || ''
}

// 获取内容稳定性标签类型
const getContentStabilityType = (stability: string) => {
  const typeMap: Record<string, string> = {
    '稳定': 'success',
    '波动较大': 'warning',
    '数据不足': 'info'
  }
  return typeMap[stability] || ''
}

// 查看文章详情
const viewArticle = (article: any) => {
  ElMessage.info(`查看文章: ${article.title}`)
  // TODO: 可以跳转到文章详情页或头条原文链接
}

// 跳转到账号管理页面
const goToAccountManagement = () => {
  window.location.href = '/toutiao'
}

const truncateText = (text: string, maxLength: number) => {
  if (!text) return '-'
  return text.length > maxLength ? text.substring(0, maxLength) + '...' : text
}

const formatTime = (time: string | null) => {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

// 计算阅读率
const calculateReadRate = (article: any) => {
  const show = article.show_count || 0
  const read = article.read_count || 0
  if (show === 0) return '0.0%'
  return ((read / show) * 100).toFixed(1) + '%'
}

// 阅读率样式
const getReadRateStyle = (article: any) => {
  const show = article.show_count || 0
  const read = article.read_count || 0
  if (show === 0) return { color: '#909399' }
  
  const rate = (read / show) * 100
  if (rate > 10) return { color: '#67C23A', fontWeight: 'bold' }  // 高阅读率：绿色
  if (rate > 5) return { color: '#E6A23C', fontWeight: 'bold' }   // 中等：橙色
  return { color: '#F56C6C', fontWeight: 'bold' }                  // 低：红色
}

onMounted(() => {
  fetchAccounts()
  // 如果有默认选中的账号，自动获取分析数据
  setTimeout(() => {
    if (selectedAccountId.value) {
      fetchAnalytics()
    }
  }, 500)
})
</script>

<style scoped lang="scss">
.article-analytics {
  padding: 20px;

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-weight: bold;
  }

  .stat-card {
    margin-bottom: 20px;

    .stat-content {
      display: flex;
      align-items: center;
      gap: 15px;

      .stat-icon {
        width: 60px;
        height: 60px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #fff;
      }

      .stat-info {
        flex: 1;

        .stat-label {
          font-size: 14px;
          color: #909399;
          margin-bottom: 8px;
        }

        .stat-value {
          font-size: 28px;
          font-weight: bold;
          color: #303133;
        }
      }
    }
  }
}
</style>
