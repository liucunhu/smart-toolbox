<template>
  <div class="proxy-management">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>🌐 代理IP管理</span>
          <el-button type="primary" @click="showAddDialog">
            <el-icon><Plus /></el-icon>
            添加代理
          </el-button>
        </div>
      </template>

      <!-- 代理统计 -->
      <el-row :gutter="20" style="margin-bottom: 20px;">
        <el-col :span="6">
          <el-card shadow="hover" class="stat-card">
            <div class="stat-item">
              <div class="stat-label">总代理数</div>
              <div class="stat-value">{{ statistics.total }}</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="hover" class="stat-card">
            <div class="stat-item">
              <div class="stat-label">健康</div>
              <div class="stat-value success">{{ statistics.healthy }}</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="hover" class="stat-card">
            <div class="stat-item">
              <div class="stat-label">异常</div>
              <div class="stat-value danger">{{ statistics.unhealthy }}</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="hover" class="stat-card">
            <div class="stat-item">
              <div class="stat-label">待检测</div>
              <div class="stat-value warning">{{ statistics.pending }}</div>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 代理列表 -->
      <el-table
        :data="proxies"
        style="width: 100%"
        v-loading="loading"
        stripe
      >
        <el-table-column prop="id" label="ID" width="80" />
        
        <el-table-column prop="ip" label="IP地址" width="180">
          <template #default="{ row }">
            {{ row.ip }}:{{ row.port }}
          </template>
        </el-table-column>
        
        <el-table-column prop="protocol" label="协议" width="100">
          <template #default="{ row }">
            <el-tag size="small">{{ row.protocol || 'HTTP' }}</el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="location" label="地区" width="150" />
        
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="response_time" label="响应时间" width="120">
          <template #default="{ row }">
            {{ row.response_time ? row.response_time + 'ms' : '-' }}
          </template>
        </el-table-column>
        
        <el-table-column prop="last_check" label="最后检测" width="180">
          <template #default="{ row }">
            {{ formatTime(row.last_check) }}
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="250" fixed="right">
          <template #default="{ row }">
            <el-button 
              size="small" 
              type="primary" 
              link
              @click="handleCheckHealth(row)"
            >
              检测
            </el-button>
            <el-button 
              size="small" 
              type="danger" 
              link
              @click="handleDelete(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <el-pagination
        v-if="total > 0"
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="total"
        layout="total, sizes, prev, pager, next, jumper"
        :page-sizes="[10, 20, 50, 100]"
        style="margin-top: 20px; justify-content: flex-end"
        @size-change="handleSizeChange"
        @current-change="handlePageChange"
      />
    </el-card>

    <!-- 添加代理对话框 -->
    <el-dialog
      v-model="addDialogVisible"
      title="添加代理IP"
      width="500px"
    >
      <el-form :model="proxyForm" label-width="100px">
        <el-form-item label="IP地址" required>
          <el-input v-model="proxyForm.ip" placeholder="例如: 192.168.1.1" />
        </el-form-item>
        <el-form-item label="端口" required>
          <el-input-number v-model="proxyForm.port" :min="1" :max="65535" style="width: 100%" />
        </el-form-item>
        <el-form-item label="协议">
          <el-select v-model="proxyForm.protocol" style="width: 100%">
            <el-option label="HTTP" value="HTTP" />
            <el-option label="HTTPS" value="HTTPS" />
            <el-option label="SOCKS5" value="SOCKS5" />
          </el-select>
        </el-form-item>
        <el-form-item label="用户名">
          <el-input v-model="proxyForm.username" placeholder="可选" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="proxyForm.password" type="password" placeholder="可选" />
        </el-form-item>
        <el-form-item label="地区">
          <el-input v-model="proxyForm.location" placeholder="例如: 北京" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="addDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleAddProxy" :loading="adding">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import apiClient from '../utils/api'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'

const loading = ref(false)
const adding = ref(false)
const proxies = ref<any[]>([])
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)
const addDialogVisible = ref(false)

const statistics = ref({
  total: 0,
  healthy: 0,
  unhealthy: 0,
  pending: 0
})

const proxyForm = ref({
  ip: '',
  port: 8080,
  protocol: 'HTTP',
  username: '',
  password: '',
  location: ''
})

/**
 * 获取状态类型
 */
const getStatusType = (status: string) => {
  const types: Record<string, string> = {
    healthy: 'success',
    unhealthy: 'danger',
    pending: 'warning'
  }
  return types[status] || 'info'
}

/**
 * 获取状态文本
 */
const getStatusText = (status: string) => {
  const texts: Record<string, string> = {
    healthy: '健康',
    unhealthy: '异常',
    pending: '待检测'
  }
  return texts[status] || status
}

/**
 * 格式化时间
 */
const formatTime = (time: string) => {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

/**
 * 加载代理列表
 */
const loadProxies = async () => {
  loading.value = true
  try {
    const response = await apiClient.get(`${API_BASE_URL}/proxy/list`)
    
    if (response.data.status === 'success' || response.data.proxies) {
      proxies.value = response.data.proxies || response.data.data || []
      total.value = proxies.value.length
      
      // 计算统计数据
      statistics.value = {
        total: proxies.value.length,
        healthy: proxies.value.filter((p: any) => p.status === 'healthy').length,
        unhealthy: proxies.value.filter((p: any) => p.status === 'unhealthy').length,
        pending: proxies.value.filter((p: any) => !p.status || p.status === 'pending').length
      }
    } else {
      ElMessage.error('加载失败：' + (response.data.message || '未知错误'))
    }
  } catch (error: any) {
    console.error('加载代理列表失败:', error)
    ElMessage.error('加载失败，请检查后端服务')
  } finally {
    loading.value = false
  }
}

/**
 * 显示添加对话框
 */
const showAddDialog = () => {
  proxyForm.value = {
    ip: '',
    port: 8080,
    protocol: 'HTTP',
    username: '',
    password: '',
    location: ''
  }
  addDialogVisible.value = true
}

/**
 * 添加代理
 */
const handleAddProxy = async () => {
  if (!proxyForm.value.ip) {
    ElMessage.warning('请输入IP地址')
    return
  }
  
  adding.value = true
  try {
    const response = await apiClient.post(`${API_BASE_URL}/proxy/add`, proxyForm.value)
    
    if (response.data.status === 'success') {
      ElMessage.success('代理添加成功')
      addDialogVisible.value = false
      loadProxies()
    } else {
      ElMessage.error('添加失败：' + (response.data.message || '未知错误'))
    }
  } catch (error: any) {
    console.error('添加代理失败:', error)
    ElMessage.error('添加失败')
  } finally {
    adding.value = false
  }
}

/**
 * 检测代理健康状态
 */
const handleCheckHealth = async (proxy: any) => {
  try {
    const response = await apiClient.post(`${API_BASE_URL}/proxy/check-health`, {
      proxy_id: proxy.id
    })
    
    if (response.data.status === 'success') {
      ElMessage.success('检测完成')
      loadProxies()
    } else {
      ElMessage.error('检测失败：' + (response.data.message || '未知错误'))
    }
  } catch (error: any) {
    console.error('检测代理失败:', error)
    ElMessage.error('检测失败')
  }
}

/**
 * 删除代理
 */
const handleDelete = async (proxy: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除代理 ${proxy.ip}:${proxy.port} 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const response = await apiClient.delete(`${API_BASE_URL}/proxy/remove`, {
      data: { proxy_id: proxy.id }
    })
    
    if (response.data.status === 'success') {
      ElMessage.success('删除成功')
      loadProxies()
    } else {
      ElMessage.error('删除失败：' + (response.data.message || '未知错误'))
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('删除代理失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

/**
 * 分页大小变化
 */
const handleSizeChange = () => {
  currentPage.value = 1
  loadProxies()
}

/**
 * 页码变化
 */
const handlePageChange = () => {
  loadProxies()
}

onMounted(() => {
  loadProxies()
})
</script>

<style scoped>
.proxy-management {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
}

.stat-card {
  text-align: center;
  cursor: pointer;
  transition: transform 0.3s;
}

.stat-card:hover {
  transform: translateY(-5px);
}

.stat-item {
  padding: 15px 0;
}

.stat-label {
  color: #666;
  font-size: 14px;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #333;
}

.stat-value.success {
  color: #67c23a;
}

.stat-value.danger {
  color: #f56c6c;
}

.stat-value.warning {
  color: #e6a23c;
}
</style>
