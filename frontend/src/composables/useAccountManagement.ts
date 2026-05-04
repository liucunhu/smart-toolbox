import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { accountApi } from '../api/modules'
import type { Account } from '../types/api'

export function useAccountManagement() {
  const loading = ref(false)
  const form = ref<Partial<Account>>({
    platform: 'douyin',
    phone_number: '',
    proxy_ip: ''
  })

  const handleRegister = async () => {
    if (!form.value.phone_number) {
      ElMessage.warning('请输入手机号')
      return
    }

    loading.value = true
    try {
      const res = await accountApi.register(form.value)
      ElMessage.success(`任务已启动，ID: ${res.task_id}`)
      // 重置表单
      form.value.phone_number = ''
    } catch (error) {
      // 错误已在 request.ts 中统一处理
      console.error('注册失败:', error)
    } finally {
      loading.value = false
    }
  }

  return {
    form,
    loading,
    handleRegister
  }
}
