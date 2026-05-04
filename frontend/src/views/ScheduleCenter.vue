<template>
  <div class="schedule-center">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>⏰ 智能调度中心</span>
        </div>
      </template>

      <el-descriptions title="系统建议" :column="1" border>
        <el-descriptions-item label="下一个最佳发布时间">
          <el-tag type="success" v-loading="loading">{{ nextTime || '计算中...' }}</el-tag>
          <el-button size="small" @click="fetchNextTime" style="margin-left: 10px;">刷新</el-button>
        </el-descriptions-item>
        <el-descriptions-item label="活跃账号数量">
          {{ healthyCount }} 个
        </el-descriptions-item>
      </el-descriptions>

      <el-divider />

      <h3>📅 发布策略说明：</h3>
      <ul>
        <li>系统会自动避开凌晨时段（22:00 - 08:00）。</li>
        <li>每个账号每日发布上限为 5 条，防止触发平台风控。</li>
        <li>发布时间会在整点附近进行随机偏移，模拟人类行为。</li>
      </ul>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { useScheduleCenter } from '../composables/useScheduleCenter'

const { nextTime, healthyCount, loading, fetchNextTime } = useScheduleCenter()
</script>

<style scoped>
.schedule-center { padding: 20px; }
.card-header { font-weight: bold; }
ul { line-height: 1.8; color: #606266; }
</style>
