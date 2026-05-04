<template>
  <el-dialog
    v-model="visible"
    title="Compliance Check Result"
    width="700px"
    :close-on-click-modal="false"
    class="compliance-dialog"
  >
    <div v-if="loading" class="loading-container">
      <el-icon class="is-loading"><Loading /></el-icon>
      <p>Checking compliance...</p>
    </div>

    <div v-else-if="!passed" class="compliance-failed">
      <el-alert
        type="error"
        :title="errorMessage"
        show-icon
        :closable="false"
        class="error-alert"
      />
      
      <div class="violations-section">
        <h4 class="section-title">
          <el-icon><WarningFilled /></el-icon>
          Detected {{ violations.length }} violation(s)
        </h4>
        <div class="violations-list">
          <el-tag
            v-for="(word, index) in violations"
            :key="index"
            type="danger"
            size="large"
            effect="dark"
            class="violation-tag"
          >
            {{ word }}
          </el-tag>
        </div>
      </div>
      
      <div class="suggestions-section">
        <h4 class="section-title">
          <el-icon><InfoFilled /></el-icon>
          Suggestions
        </h4>
        <ul class="suggestions-list">
          <li>Use more objective and neutral descriptions</li>
          <li>Avoid absolute terms (e.g., best, #1, top)</li>
          <li>Avoid exaggerated promotional words</li>
          <li>Refer to platform content guidelines</li>
          <li>Use factual descriptions instead of subjective opinions</li>
        </ul>
      </div>

      <div class="field-info" v-if="failedField">
        <el-icon><InfoFilled /></el-icon>
        <span>Issue in: <strong>{{ failedField === 'title' ? 'Title' : 'Content' }}</strong></span>
      </div>
    </div>
    
    <div v-else class="compliance-passed">
      <el-result
        icon="success"
        title="Compliance Check Passed"
        sub-title="Content meets platform guidelines, safe to publish"
      >
        <template #extra>
          <el-tag type="success" size="large">Approved</el-tag>
        </template>
      </el-result>
    </div>
    
    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">Close</el-button>
        <el-button
          v-if="!passed && !loading"
          type="warning"
          @click="$emit('modify')"
        >
          <el-icon><Edit /></el-icon>
          Modify
        </el-button>
        <el-button
          v-if="!passed && !loading"
          type="primary"
          @click="$emit('retry')"
        >
          <el-icon><Refresh /></el-icon>
          Recheck
        </el-button>
        <el-button
          v-if="passed"
          type="success"
          @click="$emit('confirm')"
        >
          <el-icon><Check /></el-icon>
          Confirm Publish
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Loading, WarningFilled, InfoFilled, Edit, Refresh, Check } from '@element-plus/icons-vue'

interface ComplianceResult {
  passed: boolean
  error?: string
  violations?: string[]
  field?: 'title' | 'content'
}

const visible = ref(false)
const loading = ref(false)
const passed = ref(true)
const errorMessage = ref('')
const violations = ref<string[]>([])
const failedField = ref<'title' | 'content' | undefined>(undefined)

const emit = defineEmits<{
  (e: 'retry'): void
  (e: 'modify'): void
  (e: 'confirm'): void
  (e: 'close'): void
}>()

const showResult = (result: ComplianceResult) => {
  passed.value = result.passed
  errorMessage.value = result.error || ''
  violations.value = result.violations || []
  failedField.value = result.field
  visible.value = true
}

const showLoading = () => {
  loading.value = true
  visible.value = true
}

const hideLoading = (result: ComplianceResult) => {
  loading.value = false
  showResult(result)
}

const handleClose = () => {
  visible.value = false
  emit('close')
}

defineExpose({
  showResult,
  showLoading,
  hideLoading
})
</script>

<style scoped lang="scss">
.compliance-dialog {
  :deep(.el-dialog__body) {
    padding: 20px;
  }
}

.loading-container {
  text-align: center;
  padding: 40px 0;
  
  .el-icon {
    font-size: 48px;
    color: #409eff;
    margin-bottom: 16px;
  }
  
  p {
    font-size: 16px;
    color: #606266;
  }
}

.compliance-failed {
  .error-alert {
    margin-bottom: 24px;
  }
  
  .violations-section,
  .suggestions-section {
    margin-bottom: 24px;
    
    .section-title {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 16px;
      font-weight: 600;
      color: #303133;
      margin-bottom: 16px;
      
      .el-icon {
        font-size: 20px;
        color: #e6a23c;
      }
    }
  }
  
  .violations-list {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    
    .violation-tag {
      font-size: 14px;
      padding: 8px 16px;
    }
  }
  
  .suggestions-list {
    background: #f5f7fa;
    border-left: 4px solid #409eff;
    padding: 16px 20px;
    border-radius: 4px;
    
    li {
      margin: 8px 0;
      line-height: 1.6;
      color: #606266;
      font-size: 14px;
    }
  }
  
  .field-info {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 12px 16px;
    background: #fef0f0;
    border-radius: 4px;
    color: #f56c6c;
    font-size: 14px;
    
    .el-icon {
      font-size: 18px;
    }
  }
}

.compliance-passed {
  padding: 20px 0;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  
  .el-button {
    min-width: 100px;
  }
}
</style>
