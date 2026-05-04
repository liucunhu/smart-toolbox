import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { contentApi } from '../api/modules'
import type { ContentTask } from '../types/api'

export function useContentCreation() {
  const loading = ref(false)
  const result = ref<any>(null)
  const form = ref({
    topic: '',
    platform: 'douyin'
  })

  const handleGenerate = async () => {
    if (!form.value.topic) {
      ElMessage.warning('请输入创作主题')
      return
    }

    loading.value = true
    const loadingMsg = ElMessage({
      message: 'AI正在生成文案，请稍候...（可能需要1-2分钟）',
      type: 'info',
      duration: 0  // 不自动关闭
    })
    
    try {
      const res = await contentApi.generateScript(form.value.topic, form.value.platform)
      loadingMsg.close()
      result.value = res
      ElMessage.success('✅ 文案生成成功！')
    } catch (error: any) {
      loadingMsg.close()
      console.error('生成失败:', error)
      
      // 更详细的错误提示
      if (error.code === 'ECONNABORTED') {
        ElMessage.error('⏱️ 请求超时，AI生成时间较长，请稍后重试或检查网络连接')
      } else if (error.response?.status === 500) {
        ElMessage.error('❌ 服务器内部错误，请检查后端日志')
      } else {
        ElMessage.error('❌ 文案生成失败：' + (error.response?.data?.detail || error.message))
      }
    } finally {
      loading.value = false
    }
  }

  return {
    form,
    loading,
    result,
    handleGenerate
  }
}
