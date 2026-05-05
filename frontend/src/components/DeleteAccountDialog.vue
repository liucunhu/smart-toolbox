<template>
  <el-dialog
    v-model="visible"
    title="Confirm Delete"
    width="500px"
    :close-on-click-modal="false"
  >
    <div class="delete-confirm-content">
      <el-alert
        type="warning"
        :closable="false"
        show-icon
      >
        <template #title>
          <strong>This action cannot be undone!</strong>
        </template>
        <template #default>
          <p>Are you sure you want to delete this account?</p>
          <div class="account-info">
            <el-descriptions :column="1" border size="small">
              <el-descriptions-item label="Platform">
                <el-tag size="small">{{ accountData?.platform }}</el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="Username">
                {{ accountData?.username }}
              </el-descriptions-item>
              <el-descriptions-item label="Account ID">
                {{ accountData?.id }}
              </el-descriptions-item>
            </el-descriptions>
          </div>
          <p class="warning-text">
            <el-icon><WarningFilled /></el-icon>
            All associated cookies and publish records will be deleted
          </p>
        </template>
      </el-alert>

      <div class="confirm-input">
        <el-input
          v-model="confirmText"
          placeholder="Type DELETE to confirm"
          clearable
        />
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleCancel">Cancel</el-button>
        <el-button
          type="danger"
          :disabled="confirmText !== 'DELETE'"
          :loading="deleting"
          @click="handleDelete"
        >
          <el-icon><Delete /></el-icon>
          Confirm Delete
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { WarningFilled, Delete } from '@element-plus/icons-vue'
import apiClient from '../utils/api'

interface AccountData {
  id: number
  platform: string
  username: string
}

const visible = ref(false)
const deleting = ref(false)
const confirmText = ref('')
const accountData = ref<AccountData | null>(null)

const emit = defineEmits<{
  (e: 'success'): void
  (e: 'cancel'): void
}>()

const open = (account: AccountData) => {
  accountData.value = account
  confirmText.value = ''
  visible.value = true
}

const handleDelete = async () => {
  if (!accountData.value) return

  deleting.value = true
  try {
    const response = await apiClient.delete(
      `/accounts/${accountData.value.id}`
    )

    if (response.data.status === 'success') {
      ElMessage.success('Account deleted successfully')
      visible.value = false
      emit('success')
    } else {
      ElMessage.error('Delete failed: ' + (response.data.message || 'Unknown error'))
    }
  } catch (error: any) {
    console.error('Delete failed:', error)
    ElMessage.error('Delete failed: ' + (error.response?.data?.detail || 'Check backend service'))
  } finally {
    deleting.value = false
  }
}

const handleCancel = () => {
  visible.value = false
  emit('cancel')
}

defineExpose({
  open
})
</script>

<style scoped lang="scss">
.delete-confirm-content {
  .account-info {
    margin: 16px 0;
  }

  .warning-text {
    display: flex;
    align-items: center;
    gap: 8px;
    color: #e6a23c;
    font-size: 14px;
    margin-top: 12px;

    .el-icon {
      font-size: 18px;
    }
  }

  .confirm-input {
    margin-top: 20px;
  }
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>
