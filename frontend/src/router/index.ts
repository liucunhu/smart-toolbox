import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '../components/MainLayout.vue'
import AccountManagement from '../views/AccountManagement.vue'
import ContentCreation from '../views/ContentCreation.vue'
import Dashboard from '../views/Dashboard.vue'
import ScheduleCenter from '../views/ScheduleCenter.vue'
import ToutiaoAccount from '../views/ToutiaoAccount.vue'
import DouyinAccount from '../views/DouyinAccount.vue'
import PublishRecords from '../views/PublishRecords.vue'
import Login from '../views/Login.vue'
import Register from '../views/Register.vue'
import HotTrendMonitor from '../views/HotTrendMonitor.vue'
import VisualSynthesis from '../views/VisualSynthesis.vue'
import AlertCenter from '../views/AlertCenter.vue'
import VideoRestructure from '../views/VideoRestructure.vue'
import SmsConfig from '../views/SmsConfig.vue'
// Phase 1-2: 多平台发布
import KuaishouAccount from '../views/KuaishouAccount.vue'
import WechatAccount from '../views/WechatAccount.vue'
import BilibiliPublish from '../views/BilibiliPublish.vue'
import XiaohongshuPublish from '../views/XiaohongshuPublish.vue'
// Phase 3: 批量注册
import BatchRegister from '../views/BatchRegister.vue'
// Phase 6: AI配图生成
import ImageGeneration from '../views/ImageGeneration.vue'
// A/B测试管理
import ABTestManagement from '../views/ABTestManagement.vue'
// 养号中心
import AccountNurturing from '../views/AccountNurturing.vue'

const routes = [
  { path: '/', redirect: '/dashboard' },
  { path: '/login', component: Login, meta: { title: '登录', requiresAuth: false } },
  { path: '/register', component: Register, meta: { title: '注册', requiresAuth: false } },
  
  // 主布局（需要认证）
  {
    path: '/',
    component: MainLayout,
    meta: { requiresAuth: true },
    children: [
      { path: 'dashboard', component: Dashboard, meta: { title: '数据大屏' } },
      { path: 'accounts', component: AccountManagement, meta: { title: '账号管理' } },
      { path: 'content', component: ContentCreation, meta: { title: '内容创作' } },
      { path: 'schedule', component: ScheduleCenter, meta: { title: '智能调度' } },
      { path: 'toutiao', component: ToutiaoAccount, meta: { title: '头条账号管理' } },
      { path: 'douyin', component: DouyinAccount, meta: { title: '抖音账号管理' } },
      // Phase 1-2: 多平台发布页面
      { path: 'kuaishou', component: KuaishouAccount, meta: { title: '快手账号管理' } },
      { path: 'wechat', component: WechatAccount, meta: { title: '视频号账号管理' } },
      { path: 'bilibili', component: BilibiliPublish, meta: { title: 'B站发布' } },
      { path: 'xiaohongshu', component: XiaohongshuPublish, meta: { title: '小红书发布' } },
      // Phase 3: 批量注册
      { path: 'batch-register', component: BatchRegister, meta: { title: '批量注册' } },
      // Phase 6: AI配图生成
      { path: 'image-generation', component: ImageGeneration, meta: { title: 'AI配图生成' } },
      // A/B测试管理
      { path: 'ab-test', component: ABTestManagement, meta: { title: 'A/B测试管理' } },
      { path: 'publish-records', component: PublishRecords, meta: { title: '发布记录' } },
      { path: 'hot-trend', component: HotTrendMonitor, meta: { title: '热点监控' } },
      { path: 'visual-synthesis', component: VisualSynthesis, meta: { title: '视觉合成' } },
      { path: 'alert-center', component: AlertCenter, meta: { title: '报警中心' } },
      { path: 'video-restructure', component: VideoRestructure, meta: { title: '视频重组' } },
      { path: 'sms-config', component: SmsConfig, meta: { title: 'SMS配置' } },
      { path: 'account-nurturing', component: AccountNurturing, meta: { title: '养号中心' } },
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  document.title = `${to.meta.title || 'Smart-Toolbox'} - 智能运营控制台`
  
  // 检查是否需要认证
  const requiresAuth = to.meta.requiresAuth !== false
  const token = localStorage.getItem('access_token')
  
  if (requiresAuth && !token) {
    // 需要认证但没有token，跳转到登录页
    next('/login')
  } else if (!requiresAuth && token) {
    // 已登录用户访问登录/注册页，跳转到首页
    next('/dashboard')
  } else {
    next()
  }
})

export default router
