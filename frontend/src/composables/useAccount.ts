import { ref } from 'vue'
import type { Ref } from 'vue'
import { registerAccount } from '../api/account'
import type { Account } from '../types'

interface UseAccountReturn {
  form: Ref<{ platform: string; phone_number: string; proxy_ip: string }>
  loading: Ref<boolean>
  handleRegister: () => Promise<void>
}

export function useAccount(): UseAccountReturn {
  const form = ref({
    platform: 'douyin',
    phone_number: '',
    proxy_ip: ''
  })
  const loading = ref(false)

  const handleRegister = async () => {
    if (!form.value.phone_number) {
      throw new Error('请输入手机号')
    }
    
    loading.value = true
    try {
      await registerAccount(form.value)
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
