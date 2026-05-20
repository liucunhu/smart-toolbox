#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""创建AccountManagement.vue文件"""

content = '''<template>
  <div class="account-management">
    <!-- 编辑账号对话框 -->
    <EditAccountDialog
      ref="editDialog"
      @success="handleEditSuccess"
      @cancel="handleEditCancel"
    />
    
    <!-- 删除确认对话框 -->
    <DeleteAccountDialog
      ref="deleteDialog"
      @success="handleDeleteSuccess"
      @cancel="handleDeleteCancel"
    />
    
    <el-card>
      <template #header>
        <div class="card-header">
          <span>👥 账号管理</span>
          <el-button type="primary" @click="handleAddAccount">
            <el-icon><Plus /></el-icon>
            添加账号
          </el-button>
        </div>
      </template>

      <!-- 账号列表 -->
      <el-table
        :data="accounts"
        style="width: 100%"
        v-loading="loading"
      >
        <el-table-column prop="id" label="ID" width="80" />
        
        <el-table-column prop="platform" label="平台" width="120">
          <template #default="{ row }">
            <el-tag :type="getPlatformType(row.platform)">
              {{ getPlatformName(row.platform) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="username" label="用户名" min-width="150" />
        
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'info'">
              {{ row.status === 'active' ? '活跃' : '未激活' }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="last_login" label="最后登录" width="180">
          <template #default="{ row }">
            {{ formatTime(row.last_login) }}
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="250" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" @click="handleLogin(row)">
              登录
            </el-button>
            <el-button size="small" type="warning" @click="handleEdit(row)">
              编辑
            </el-button>
            <el-button size="small" type="danger" @click="handleDelete(row)">
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
        layout="total, prev, pager, next"
        style="margin-top: 20px; justify-content: flex-end"
      />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import axios from 'axios'
import EditAccountDialog from '@/components/EditAccountDialog.vue'
import DeleteAccountDialog from '@/components/DeleteAccountDialog.vue'

const loading = ref(false)
const accounts = ref<any[]>([])
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)

const editDialog = ref<InstanceType<typeof EditAccountDialog> | null>(null)
const deleteDialog = ref<InstanceType<typeof DeleteAccountDialog> | null>(null)

/**
 * 获取平台名称
 */
const getPlatformName = (platform: string) => {
  const names: Record<string, string> = {
    toutiao: '今日头条',
    douyin: '抖音',
    kuaishou: '快手',
    wechat: '视频号',
    bilibili: 'B站',
    xiaohongshu: '小红书'
  }
  return names[platform] || platform
}

/**
 * 获取平台标签类型
 */
const getPlatformType = (platform: string) => {
  const types: Record<string, string> = {
    toutiao: 'danger',
    douyin: 'primary',
    kuaishou: 'success',
    wechat: 'warning',
    bilibili: '',
    xiaohongshu: 'danger'
  }
  return types[platform] || 'info'
}

/**
 * 格式化时间
 */
const formatTime = (time: string) => {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

/**
 * 加载账号列表
 */
const loadAccounts = async () => {
  loading.value = true
  try {
    const response = await axios.get('http://localhost:8000/api/v1/accounts/list', {
      params: {
        page: currentPage.value,
        page_size: pageSize.value
      }
    })

    if (response.data.status === 'success') {
      accounts.value = response.data.data.items || []
      total.value = response.data.data.total || 0
    } else {
      ElMessage.error('加载失败：' + (response.data.message || '未知错误'))
    }
  } catch (error: any) {
    console.error('加载账号列表失败:', error)
    ElMessage.error('加载失败，请检查后端服务')
  } finally {
    loading.value = false
  }
}

/**
 * 添加账号
 */
const handleAddAccount = () => {
  ElMessage.info('请使用各平台的登录功能添加账号')
}

/**
 * 登录账号
 */
const handleLogin = (account: any) => {
  ElMessage.success(`正在启动${getPlatformName(account.platform)}登录流程...`)
  // 跳转到对应平台的登录页面
  window.location.href = `/${account.platform}/account`
}

/**
 * 编辑账号
 */
const handleEdit = (account: any) => {
  editDialog.value?.open(account)
}

/**
 * 编辑成功
 */
const handleEditSuccess = () => {
  loadAccounts()
}

/**
 * 编辑取消
 */
const handleEditCancel = () => {
  // 清理逻辑
}

/**
 * 删除账号
 */
const handleDelete = (account: any) => {
  deleteDialog.value?.open(account)
}

/**
 * 删除成功
 */
const handleDeleteSuccess = () => {
  loadAccounts()
}

/**
 * 删除取消
 */
const handleDeleteCancel = () => {
  // 清理逻辑
}

// 组件挂载时加载数据
onMounted(() => {
  loadAccounts()
})
</script>

<style scoped lang="scss">
.account-management {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
'''

with open('frontend/src/views/AccountManagement.vue', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ AccountManagement.vue 创建成功！")
print(f"文件大小: {len(content)} 字符")
