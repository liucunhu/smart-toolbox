# 自动化注册引擎 (Auto Registration Engine)

## 1. 功能描述
实现多平台账号的无人值守自动化注册，解决人工注册效率低、成本高的问题。

## 2. 技术实现方案

### 2.1 环境指纹隔离 (Fingerprint Isolation)
*   **实现逻辑**: 
    *   使用 `playwright-stealth` 库隐藏自动化测试特征（如 `navigator.webdriver`）。
    *   动态生成设备指纹：包括屏幕分辨率、时区、语言、字体列表等。
    *   **IP 代理绑定**: 每个注册会话强制绑定一个独立的住宅代理 IP，确保 IP 与地理位置匹配。

### 2.2 验证码处理 (CAPTCHA Solver)
*   **滑块验证**: 
    *   利用 OpenCV 进行边缘检测定位缺口坐标。
    *   通过贝塞尔曲线算法生成模拟人类的滑动轨迹（包含加速、减速及微小抖动）。
*   **短信验证**: 
    *   对接 SMS 接码平台 API，自动监听并提取验证码。

### 2.3 流程控制
*   **状态机管理**: 定义注册流程的各个节点（打开页面 -> 填写信息 -> 验证 -> 完成），支持断点续传。
*   **异常重试**: 针对网络波动或临时风控，设置指数退避重试机制。

## 3. 数据结构设计
```json
{
  "task_id": "uuid",
  "platform": "douyin",
  "proxy_ip": "192.168.x.x",
  "fingerprint_seed": "random_string",
  "status": "processing" // pending, processing, success, failed
}
```
