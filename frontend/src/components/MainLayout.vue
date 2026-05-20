<template>
  <el-container class="app-layout">
    <!-- 侧边栏 -->
    <el-aside :width="isCollapse ? '64px' : '220px'" class="sidebar">
      <div class="logo">
        <h2 v-if="!isCollapse">Smart Toolbox</h2>
        <h2 v-else>ST</h2>
      </div>
      
      <el-menu
        :default-active="activeMenu"
        :collapse="isCollapse"
        :unique-opened="true"
        router
        background-color="#304156"
        text-color="#bfcbd9"
        active-text-color="#409EFF"
      >
        <!-- 数据大屏 -->
        <el-menu-item index="/dashboard">
          <el-icon><DataLine /></el-icon>
          <template #title>数据大屏</template>
        </el-menu-item>

        <!-- 账号管理 -->
        <el-sub-menu index="accounts">
          <template #title>
            <el-icon><User /></el-icon>
            <span>账号管理</span>
          </template>
          <el-menu-item index="/accounts">全部账号</el-menu-item>
          <el-menu-item index="/toutiao">头条账号</el-menu-item>
          <el-menu-item index="/douyin">抖音账号</el-menu-item>
          <el-menu-item index="/kuaishou">快手账号</el-menu-item>
          <el-menu-item index="/wechat">视频号</el-menu-item>
          <el-menu-item index="/bilibili">B站账号</el-menu-item>
          <el-menu-item index="/xiaohongshu">小红书</el-menu-item>
          <el-menu-item index="/fanqie">番茄小说</el-menu-item>
          <el-menu-item index="/batch-register">批量注册</el-menu-item>
        </el-sub-menu>

        <!-- 内容创作 -->
        <el-sub-menu index="content">
          <template #title>
            <el-icon><Edit /></el-icon>
            <span>内容创作</span>
          </template>
          <el-menu-item index="/content">AI文案生成</el-menu-item>
          <el-menu-item index="/image-generation">AI配图生成</el-menu-item>
          <el-menu-item index="/compliance-check">合规检查</el-menu-item>
          <el-menu-item index="/subtitle-editor">字幕编辑</el-menu-item>
          <el-menu-item index="/video-processor">视频处理</el-menu-item>
          <el-menu-item index="/visual-synthesis">视觉合成</el-menu-item>
          <el-menu-item index="/video-restructure">视频重组</el-menu-item>
        </el-sub-menu>

        <!-- 发布管理 -->
        <el-sub-menu index="publish">
          <template #title>
            <el-icon><Upload /></el-icon>
            <span>发布管理</span>
          </template>
          <el-menu-item index="/content-tasks">内容任务</el-menu-item>
          <el-menu-item index="/publish-records">发布记录</el-menu-item>
          <el-menu-item index="/schedule">智能调度</el-menu-item>
          <el-menu-item index="/ab-test">A/B测试</el-menu-item>
        </el-sub-menu>

        <!-- 运营监控 -->
        <el-sub-menu index="monitor">
          <template #title>
            <el-icon><TrendCharts /></el-icon>
            <span>运营监控</span>
          </template>
          <el-menu-item index="/hot-trend">热点监控</el-menu-item>
          <el-menu-item index="/article-analytics">文章数据分析</el-menu-item>
          <el-menu-item index="/account-nurturing">养号中心</el-menu-item>
          <el-menu-item index="/alert-center">报警中心</el-menu-item>
          <el-menu-item index="/agent-monitor">智能体监控</el-menu-item>
        </el-sub-menu>

        <!-- 系统配置 -->
        <el-sub-menu index="settings">
          <template #title>
            <el-icon><Setting /></el-icon>
            <span>系统配置</span>
          </template>
          <el-menu-item index="/llm-config">大模型配置</el-menu-item>
          <el-menu-item index="/api-usage">API用量监控</el-menu-item>
          <el-menu-item index="/sms-config">SMS配置</el-menu-item>
          <el-menu-item index="/proxy-management">代理管理</el-menu-item>
        </el-sub-menu>
      </el-menu>
    </el-aside>

    <!-- 主内容区 -->
    <el-container>
      <!-- 顶部导航栏 -->
      <el-header class="header">
        <div class="header-left">
          <el-icon class="collapse-btn" @click="toggleCollapse">
            <Fold v-if="!isCollapse" />
            <Expand v-else />
          </el-icon>
        </div>
        
        <div class="header-right">
          <el-dropdown @command="handleCommand">
            <span class="user-info">
              <el-icon><UserFilled /></el-icon>
              <span>管理员</span>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="logout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <!-- 主要内容 -->
      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import {
  DataLine,
  User,
  Edit,
  Upload,
  TrendCharts,
  Setting,
  Fold,
  Expand,
  UserFilled
} from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const isCollapse = ref(false)

const activeMenu = computed(() => route.path)

const toggleCollapse = () => {
  isCollapse.value = !isCollapse.value
}

const handleCommand = async (command: string) => {
  if (command === 'logout') {
    await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    localStorage.removeItem('access_token')
    router.push('/login')
  }
}
</script>

<style scoped lang="scss">
.app-layout {
  height: 100vh;
}

.sidebar {
  background-color: #304156;
  transition: width 0.3s;
  overflow-x: hidden;
  
  .logo {
    height: 60px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #fff;
    background-color: #2b3a4a;
    
    h2 {
      margin: 0;
      font-size: 18px;
      white-space: nowrap;
    }
  }
  
  .el-menu {
    border-right: none;
  }
}

.header {
  background-color: #fff;
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  
  .header-left {
    .collapse-btn {
      font-size: 20px;
      cursor: pointer;
      transition: color 0.3s;
      
      &:hover {
        color: #409EFF;
      }
    }
  }
  
  .header-right {
    .user-info {
      display: flex;
      align-items: center;
      gap: 8px;
      cursor: pointer;
      padding: 8px 12px;
      border-radius: 4px;
      transition: background-color 0.3s;
      
      &:hover {
        background-color: #f5f7fa;
      }
    }
  }
}

.main-content {
  background-color: #f0f2f5;
  padding: 20px;
  overflow-y: auto;
}
</style>
