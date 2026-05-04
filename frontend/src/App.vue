<template>
  <el-container style="height: 100vh;">
    <el-aside width="220px" style="background-color: #304156; color: white;">
      <div style="padding: 20px; font-size: 18px; font-weight: bold; text-align: center; border-bottom: 1px solid #43546b;">
        🚀 Smart-Toolbox
      </div>
      <el-menu
        background-color="#304156"
        text-color="#bfcbd9"
        active-text-color="#409EFF"
        :default-active="$route.path"
        router
      >
        <el-menu-item index="/dashboard">📊 数据大屏</el-menu-item>
        <el-menu-item index="/accounts">👥 账号管理</el-menu-item>
        <el-menu-item index="/content">🎬 内容创作</el-menu-item>
        <el-menu-item index="/hot-trend">🔥 热点监控</el-menu-item>
        <el-menu-item index="/visual-synthesis">🎨 视觉合成</el-menu-item>
        <el-menu-item index="/video-restructure">🔄 视频重组</el-menu-item>
        <el-menu-item index="/toutiao">📰 头条账号管理</el-menu-item>
        <el-menu-item index="/douyin">🎵 抖音账号管理</el-menu-item>
        <el-menu-item index="/publish-records">📤 发布记录</el-menu-item>
        <el-menu-item index="/schedule">⏰ 智能调度</el-menu-item>
        <el-menu-item index="/alert-center">🚨 报警中心</el-menu-item>
        <el-menu-item index="/sms-config">📱 SMS配置</el-menu-item>
      </el-menu>
    </el-aside>
    
    <el-main>
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup lang="ts">
// App root component
</script>
