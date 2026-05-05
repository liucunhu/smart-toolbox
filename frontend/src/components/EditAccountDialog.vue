<template>
  <el-dialog
    v-model="visible"
    title="Edit Account"
    width="600px"
    :close-on-click-modal="false"
  >
    <el-form
      ref="formRef"
      :model="formData"
      :rules="rules"
      label-width="120px"
    >
      <el-form-item label="Platform" prop="platform">
        <el-select v-model="formData.platform" disabled>
          <el-option label="Toutiao" value="toutiao" />
          <el-option label="Douyin" value="douyin" />
          <el-option label="Kuaishou" value="kuaishou" />
          <el-option label="Wechat" value="wechat" />
          <el-option label="Bilibili" value="bilibili" />
          <el-option label="Xiaohongshu" value="xiaohongshu" />
        </el-select>
      </el-form-item>

      <el-form-item label="Username/Phone" prop="username">
        <el-input
          v-model="formData.username"
          placeholder="Enter username or phone"
          clearable
        />
      </el-form-item>

      <el-form-item label="Password" prop="password">
        <el-input
          v-model="formData.password"
          type="password"
          placeholder="Leave empty to keep current password"
          show-password
          clearable
        />
        <div class="form-tip">
          <el-icon><InfoFilled /></el-icon>
          <span>Leave empty if not changing password</span>
        </div>
      </el-form-item>

      <el-form-item label="Proxy IP" prop="proxy_ip">
        <el-input
          v-model="formData.proxy_ip"
          placeholder="e.g., 192.168.1.100:8080"
          clearable
        />
        <div class="form-tip">
          <el-icon><InfoFilled /></el-icon>
          <span>Optional, for multi-account isolation</span>
        </div>
      </el-form-item>

      <el-form-item label="Remark">
        <el-input
          v-model="formData.remark"
          type="textarea"
          :rows="3"
          placeholder="Optional remarks"
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleCancel">Cancel</el-button>
        <el-button
          type="primary"
          :loading="saving"
          @click="handleSave"
        >
          <el-icon><Check /></el-icon>
          Save
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { InfoFilled, Check } from '@element-plus/icons-vue'
import apiClient from '../utils/api'

interface AccountData {
  id: number
  platform: string
  username: string
  password?: string
  proxy_ip?: string
  remark?: string
}

const visible = ref(false)
const saving = ref(false)
const formRef = ref<FormInstance>()

const formData = reactive<AccountData>({
  id: 0,
  platform: '',
  username: '',
  password: '',
  proxy_ip: '',
  remark: ''
})

const rules = reactive<FormRules>({
  username: [
    { required: true, message: 'Please enter username', trigger: 'blur' },
    { min: 3, max: 50, message: 'Length should be 3 to 50 characters', trigger: 'blur' }
  ],
  password: [
    { min: 6, max: 100, message: 'Password must be at least 6 characters', trigger: 'blur' }
  ]
})

const emit = defineEmits<{
  (e: 'success'): void
  (e: 'cancel'): void
}>()

const open = (account: AccountData) => {
  formData.id = account.id
  formData.platform = account.platform
  formData.username = account.username
  formData.password = ''
  formData.proxy_ip = account.proxy_ip || ''
  formData.remark = account.remark || ''
  visible.value = true
}

const handleSave = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    saving.value = true
    try {
      const response = await apiClient.put(
        `/accounts/${formData.id}`,
        null,
        {
          params: {
            username: formData.username,
            password: formData.password || undefined,
            proxy_ip: formData.proxy_ip || undefined
          }
        }
      )

      if (response.data.status === 'success') {
        ElMessage.success('Account updated successfully')
        visible.value = false
        emit('success')
      } else {
        ElMessage.error('Update failed: ' + (response.data.message || 'Unknown error'))
      }
    } catch (error: any) {
      console.error('Update failed:', error)
      ElMessage.error('Update failed: ' + (error.response?.data?.detail || 'Check backend service'))
    } finally {
      saving.value = false
    }
  })
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
.form-tip {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #909399;
  margin-top: 4px;

  .el-icon {
    font-size: 14px;
  }
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>
