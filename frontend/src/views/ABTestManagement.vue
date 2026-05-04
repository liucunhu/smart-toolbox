<template>
  <div class="ab-test-management">
    <el-row :gutter="20">
      <!-- 创建A/B测试 -->
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>🧪 创建A/B测试</span>
            </div>
          </template>

          <el-form :model="testForm" label-width="120px">
            <el-form-item label="测试ID">
              <el-input v-model="testForm.test_id" placeholder="例如: test_001" />
            </el-form-item>

            <el-form-item label="文章标题">
              <el-input v-model="testForm.article_title" placeholder="输入文章标题" />
            </el-form-item>

            <el-form-item label="测试描述">
              <el-input 
                v-model="testForm.description" 
                type="textarea"
                :rows="3"
                placeholder="测试描述（可选）"
              />
            </el-form-item>

            <el-form-item label="封面图变体">
              <div v-for="(variant, index) in testForm.cover_variants" :key="index" style="margin-bottom: 10px;">
                <el-row :gutter="10">
                  <el-col :span="18">
                    <el-input 
                      v-model="variant.file_path" 
                      :placeholder="`变体 ${variant.variant_id} 文件路径`"
                    />
                  </el-col>
                  <el-col :span="6">
                    <el-button 
                      type="danger" 
                      size="small" 
                      @click="removeVariant(index)"
                      :disabled="testForm.cover_variants.length <= 2"
                    >
                      删除
                    </el-button>
                  </el-col>
                </el-row>
                <el-input 
                  v-model="variant.description" 
                  placeholder="变体描述"
                  size="small"
                  style="margin-top: 5px;"
                />
              </div>
              <el-button type="primary" size="small" @click="addVariant" style="width: 100%;">
                + 添加变体
              </el-button>
            </el-form-item>

            <el-form-item>
              <el-button type="success" @click="createTest" :loading="creating" style="width: 100%;">
                ✨ 创建测试
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <!-- 测试列表 -->
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>📊 A/B测试列表</span>
              <el-button type="primary" size="small" @click="fetchTests" :loading="loading">
                🔄 刷新
              </el-button>
            </div>
          </template>

          <el-table :data="tests" style="width: 100%" v-loading="loading">
            <el-table-column prop="test_id" label="测试ID" width="150" />
            <el-table-column prop="article_title" label="文章标题" min-width="200" />
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="row.status === 'running' ? 'success' : 'info'">
                  {{ row.status === 'running' ? '进行中' : '已结束' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="variants_count" label="变体数" width="80" />
            <el-table-column label="操作" width="150">
              <template #default="{ row }">
                <el-button size="small" type="primary" @click="viewResults(row)">结果</el-button>
                <el-button 
                  v-if="row.status === 'running'" 
                  size="small" 
                  type="warning" 
                  @click="endTest(row.test_id)"
                >
                  结束
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <!-- 测试结果对话框 -->
    <el-dialog v-model="resultsVisible" title="测试结果" width="70%">
      <div v-if="currentResults">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="测试ID">{{ currentResults.test_id }}</el-descriptions-item>
          <el-descriptions-item label="文章标题">{{ currentResults.article_title }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="currentResults.status === 'running' ? 'success' : 'info'">
              {{ currentResults.status === 'running' ? '进行中' : '已结束' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="总曝光量">{{ currentResults.total_impressions }}</el-descriptions-item>
          <el-descriptions-item label="总点击量">{{ currentResults.total_clicks }}</el-descriptions-item>
          <el-descriptions-item label="整体CTR">{{ (currentResults.overall_ctr * 100).toFixed(2) }}%</el-descriptions-item>
        </el-descriptions>

        <h4 style="margin-top: 20px;">各变体表现：</h4>
        <el-table :data="currentResults.variants" style="width: 100%; margin-top: 10px;">
          <el-table-column prop="variant_id" label="变体ID" width="100" />
          <el-table-column prop="impressions" label="曝光量" width="100" />
          <el-table-column prop="clicks" label="点击量" width="100" />
          <el-table-column prop="ctr" label="CTR" width="100">
            <template #default="{ row }">
              {{ (row.ctr * 100).toFixed(2) }}%
            </template>
          </el-table-column>
          <el-table-column prop="description" label="描述" min-width="200" />
          <el-table-column label="最佳" width="80">
            <template #default="{ row }">
              <el-tag v-if="row.is_winner" type="success">🏆</el-tag>
            </template>
          </el-table-column>
        </el-table>

        <div v-if="currentResults.best_variant" style="margin-top: 20px;">
          <el-alert
            title="最佳变体"
            type="success"
            :closable="false"
          >
            <template #default>
              <p><strong>变体ID:</strong> {{ currentResults.best_variant.variant_id }}</p>
              <p><strong>CTR:</strong> {{ (currentResults.best_variant.ctr * 100).toFixed(2) }}%</p>
              <p><strong>描述:</strong> {{ currentResults.best_variant.description }}</p>
            </template>
          </el-alert>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'

const loading = ref(false)
const creating = ref(false)
const resultsVisible = ref(false)
const currentResults = ref<any>(null)

// 测试表单
const testForm = ref({
  test_id: `test_${Date.now()}`,
  article_title: '',
  description: '',
  cover_variants: [
    { variant_id: 'A', file_path: '', description: '现代风格' },
    { variant_id: 'B', file_path: '', description: '极简风格' }
  ]
})

// 测试列表
const tests = ref<any[]>([])

// 添加变体
const addVariant = () => {
  const variantId = String.fromCharCode(65 + testForm.value.cover_variants.length)
  testForm.value.cover_variants.push({
    variant_id: variantId,
    file_path: '',
    description: ''
  })
}

// 删除变体
const removeVariant = (index: number) => {
  if (testForm.value.cover_variants.length > 2) {
    testForm.value.cover_variants.splice(index, 1)
  }
}

// 创建测试
const createTest = async () => {
  if (!testForm.value.test_id || !testForm.value.article_title) {
    ElMessage.warning('请填写测试ID和文章标题')
    return
  }

  // 验证变体
  for (const variant of testForm.value.cover_variants) {
    if (!variant.file_path) {
      ElMessage.warning(`请填写变体 ${variant.variant_id} 的文件路径`)
      return
    }
  }

  creating.value = true
  try {
    const response = await axios.post(`${API_BASE_URL}/content/ab-test/create`, {
      test_id: testForm.value.test_id,
      article_title: testForm.value.article_title,
      cover_variants: testForm.value.cover_variants,
      description: testForm.value.description
    })

    if (response.data.status === 'success') {
      ElMessage.success('测试创建成功')
      fetchTests()
      
      // 重置表单
      testForm.value = {
        test_id: `test_${Date.now()}`,
        article_title: '',
        description: '',
        cover_variants: [
          { variant_id: 'A', file_path: '', description: '现代风格' },
          { variant_id: 'B', file_path: '', description: '极简风格' }
        ]
      }
    } else {
      ElMessage.error('创建失败: ' + response.data.error)
    }
  } catch (error: any) {
    console.error('创建测试失败:', error)
    ElMessage.error('创建失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    creating.value = false
  }
}

// 获取测试列表
const fetchTests = async () => {
  loading.value = true
  try {
    const response = await axios.get(`${API_BASE_URL}/content/ab-tests`)
    tests.value = response.data.tests || []
  } catch (error) {
    console.error('获取测试列表失败:', error)
    ElMessage.error('获取测试列表失败')
  } finally {
    loading.value = false
  }
}

// 查看结果
const viewResults = async (test: any) => {
  try {
    const response = await axios.get(`${API_BASE_URL}/content/ab-test/${test.test_id}`)
    currentResults.value = response.data
    resultsVisible.value = true
  } catch (error) {
    console.error('获取测试结果失败:', error)
    ElMessage.error('获取测试结果失败')
  }
}

// 结束测试
const endTest = async (testId: string) => {
  try {
    await ElMessageBox.confirm('确定要结束此测试吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    const response = await axios.post(`${API_BASE_URL}/content/ab-test/${testId}/end`)
    
    if (response.data.status === 'success') {
      ElMessage.success('测试已结束')
      fetchTests()
    } else {
      ElMessage.error('结束失败: ' + response.data.error)
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('结束测试失败:', error)
      ElMessage.error('结束测试失败')
    }
  }
}

onMounted(() => {
  fetchTests()
})
</script>

<style scoped>
.ab-test-management { padding: 20px; }
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
}
</style>
