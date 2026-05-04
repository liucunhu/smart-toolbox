import { ref, onMounted } from 'vue'
import { scheduleApi, accountApi } from '../api/modules'

export function useScheduleCenter() {
  const nextTime = ref('')
  const healthyCount = ref(0)
  const loading = ref(false)

  const fetchNextTime = async () => {
    loading.value = true
    try {
      // 获取下一个最佳发布时间
      const res = await scheduleApi.getNextPublishTime()
      nextTime.value = new Date(res.suggested_time).toLocaleString()
      
      // 获取健康账号数量
      const accRes = await accountApi.getHealthyAccounts()
      healthyCount.value = accRes.count
    } catch (error) {
      console.error('获取调度信息失败', error)
    } finally {
      loading.value = false
    }
  }

  onMounted(() => {
    fetchNextTime()
  })

  return {
    nextTime,
    healthyCount,
    loading,
    fetchNextTime
  }
}
