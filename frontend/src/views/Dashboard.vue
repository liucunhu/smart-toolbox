<template>
  <div class="dashboard-container">
    <el-row :gutter="20">
      <!-- 账号统计 -->
      <el-col :span="8">
        <el-card shadow="hover" class="stat-card">
          <template #header>
            <div class="card-header">
              <span>👥 账号统计</span>
            </div>
          </template>
          <div class="stat-item">
            <div class="stat-label">总账号数</div>
            <div class="stat-value">{{ stats.accounts?.total || 0 }}</div>
          </div>
          <div class="stat-item">
            <div class="stat-label">活跃账号</div>
            <div class="stat-value success">{{ stats.accounts?.active || 0 }}</div>
          </div>
          <div class="stat-item">
            <div class="stat-label">养号中</div>
            <div class="stat-value warning">{{ stats.accounts?.nurturing || 0 }}</div>
          </div>
        </el-card>
      </el-col>

      <!-- 内容任务统计 -->
      <el-col :span="8">
        <el-card shadow="hover" class="stat-card">
          <template #header>
            <div class="card-header">
              <span>📝 内容任务</span>
            </div>
          </template>
          <div class="stat-item">
            <div class="stat-label">总任务数</div>
            <div class="stat-value">{{ stats.content_tasks?.total || 0 }}</div>
          </div>
          <div class="stat-item">
            <div class="stat-label">已完成</div>
            <div class="stat-value success">{{ stats.content_tasks?.completed || 0 }}</div>
          </div>
          <div class="stat-item">
            <div class="stat-label">完成率</div>
            <div class="stat-value">
              {{ stats.content_tasks?.total ? Math.round((stats.content_tasks.completed / stats.content_tasks.total) * 100) : 0 }}%
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 发布记录统计 -->
      <el-col :span="8">
        <el-card shadow="hover" class="stat-card">
          <template #header>
            <div class="card-header">
              <span>📤 发布记录</span>
            </div>
          </template>
          <div class="stat-item">
            <div class="stat-label">总发布数</div>
            <div class="stat-value">{{ stats.publish_records?.total || 0 }}</div>
          </div>
          <div class="stat-item">
            <div class="stat-label">成功发布</div>
            <div class="stat-value success">{{ stats.publish_records?.successful || 0 }}</div>
          </div>
          <div class="stat-item">
            <div class="stat-label">成功率</div>
            <div class="stat-value">
              {{ stats.publish_records?.total ? Math.round((stats.publish_records.successful / stats.publish_records.total) * 100) : 0 }}%
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card style="margin-top: 20px;">
      <template #header>
        <div class="card-header">
          <span>⚡ 快速开始</span>
        </div>
      </template>
      <el-button type="primary" @click="$router.push('/accounts')"> 新建账号</el-button>
      <el-button type="success" @click="$router.push('/content')">📝 生成文案</el-button>
      <el-button type="warning" @click="$router.push('/publish-records')">📤 查看记录</el-button>
      <el-button type="info" @click="$router.push('/toutiao')">📰 头条管理</el-button>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import apiClient from '../utils/api'
import { ElMessage } from 'element-plus'

interface DashboardStats {
  accounts?: {
    total: number
    active: number
    nurturing: number
  }
  content_tasks?: {
    total: number
    completed: number
  }
  publish_records?: {
    total: number
    successful: number
  }
}

const stats = ref<DashboardStats>({
  accounts: { total: 0, active: 0, nurturing: 0 },
  content_tasks: { total: 0, completed: 0 },
  publish_records: { total: 0, successful: 0 }
})

const fetchStats = async () => {
  try {
    const response = await apiClient.get('/dashboard/stats')
    // ✅ 修复：axios拦截器已经解包，直接访问response.data，并处理可能的undefined
    if (response.data) {
      stats.value = response.data
    } else {
      stats.value = {
        accounts: { total: 0, active: 0, nurturing: 0 },
        content_tasks: { total: 0, completed: 0 },
        publish_records: { total: 0, successful: 0 }
      }
    }
  } catch (error) {
    console.error('获取统计数据失败:', error)
    // 保持默认值不变
  }
}

onMounted(() => {
  fetchStats()
  // 每 30 秒刷新一次数据
  setInterval(fetchStats, 30000)
})
</script>

<style scoped>
.dashboard-container { padding: 20px; }
.stat-card { text-align: center; }
.card-header { 
  display: flex; 
  justify-content: space-between; 
  align-items: center;
  font-weight: bold;
}
.stat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 0;
  border-bottom: 1px solid #eee;
}
.stat-item:last-child {
  border-bottom: none;
}
.stat-label {
  color: #666;
  font-size: 14px;
}
.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #333;
}
.stat-value.success {
  color: #67c23a;
}
.stat-value.warning {
  color: #e6a23c;
}
</style>
