# 头条封面图上传功能 - 快速测试指南

## 🚀 5分钟快速测试

### 准备工作（1分钟）

1. **准备测试图片**
   ```bash
   # 找一张jpg或png图片，复制到项目根目录
   # 命名为: test_cover.jpg
   ```

2. **确保服务运行**
   ```bash
   # 终端1: 启动后端
   python main.py
   
   # 终端2: 启动前端（如果需要测试UI）
   cd frontend
   npm run dev
   ```

### 方法1：通过测试脚本（推荐）⭐

```bash
# 直接运行测试脚本
python test_cover_upload.py
```

**测试流程：**
1. ✅ 脚本检查测试图片是否存在
2. ✅ 自动打开浏览器
3. ⏸️ 暂停等待你手动登录头条
4. ✅ 自动发布带封面图的文章
5. ✅ 显示测试结果

**预期输出：**
```
================================================================================
🧪 测试头条自动发布上传封面图功能
================================================================================

✅ 找到测试封面图: test_cover.jpg
   文件大小: 123456 bytes

[步骤 1] 初始化浏览器...
✅ 浏览器初始化成功

[步骤 2] 请登录头条账号...
   系统会打开浏览器，请手动完成登录
   登录完成后，按回车继续...
   [按回车]

[步骤 3] 发布文章（带封面图）...
...
================================================================================
📊 发布结果:
================================================================================
状态: success
标题: 测试封面图上传功能
消息: 文章发布成功
================================================================================

🎉 测试成功！封面图上传功能正常工作
```

### 方法2：通过前端界面

1. **访问页面**
   ```
   http://localhost:5173
   ```

2. **登录头条账号**
   - 点击"头条账号"菜单
   - 输入账号信息
   - 点击"登录并保存 Cookie"
   - 在打开的浏览器中完成登录

3. **上传封面图并发布**
   - 在右侧"发布头条文章"区域
   - 点击"选择封面图"按钮
   - 选择一张图片
   - 看到预览后，输入文章主题
   - 点击"🚀 一键发布"
   - 等待发布完成

4. **验证结果**
   - 查看成功提示
   - 登录头条后台确认
   - 检查文章是否有封面图

### 方法3：通过API测试

#### 步骤1：上传封面图
```bash
curl -X POST http://localhost:8000/api/v1/content/upload-image \
  -F "file=@test_cover.jpg" \
  -H "Content-Type: multipart/form-data"
```

**预期响应：**
```json
{
  "status": "success",
  "file_path": "uploads/covers/abc123def456.jpg",
  "filename": "abc123def456.jpg"
}
```

#### 步骤2：发布文章
```bash
curl -X POST "http://localhost:8000/api/v1/content/toutiao/auto_publish" \
  -d "account_id=1" \
  -d "topic=测试封面图功能" \
  -d "username=你的账号" \
  -d "password=你的密码" \
  -d "category=科技" \
  -d "cover_image_path=uploads/covers/abc123def456.jpg"
```

**预期响应：**
```json
{
  "status": "success",
  "message": "文章发布成功！",
  "article_title": "测试封面图功能的深度解析",
  "article_content_length": 1234,
  "tags": ["测试", "封面图"],
  "category": "科技"
}
```

## ✅ 验证清单

### 基础功能验证
- [ ] 可以选择图片文件
- [ ] 前端显示图片预览
- [ ] 图片成功上传到服务器
- [ ] `uploads/covers/` 目录下有文件
- [ ] Playwright找到文件上传元素
- [ ] 封面图成功上传到头条
- [ ] 发布成功后头条后台能看到封面

### 错误处理验证
- [ ] 不选封面图也能发布（使用默认封面）
- [ ] 上传失败时有友好提示
- [ ] 网络错误时能正确处理
- [ ] 文件格式错误时能提示

### 用户体验验证
- [ ] 操作流程简单直观
- [ ] 提示信息清晰易懂
- [ ] 加载状态有反馈
- [ ] 成功后表单清空

## 🔍 调试技巧

### 1. 查看后端日志
```bash
# 实时查看日志
tail -f logs/app.log

# 搜索封面图相关日志
grep "封面" logs/app.log
grep "cover" logs/app.log
```

### 2. 查看浏览器控制台
- 打开浏览器开发者工具（F12）
- 切换到 Console 标签
- 查看是否有JavaScript错误
- 查看Network请求详情

### 3. 检查上传目录
```bash
# 查看上传的文件
ls -lh uploads/covers/

# 查看最新文件
ls -lt uploads/covers/ | head -5
```

### 4. 验证头条后台
1. 登录 https://mp.toutiao.com/
2. 进入"内容管理"
3. 找到刚发布的文章
4. 检查是否有封面图显示

## ❌ 常见问题排查

### 问题1：找不到测试图片
**现象：** `⚠️ 测试封面图文件不存在`

**解决：**
```bash
# 确认图片存在
ls -l test_cover.jpg

# 或者复制一张图片
cp /path/to/your/image.jpg test_cover.jpg
```

### 问题2：上传接口404
**现象：** `POST /api/v1/content/upload-image 404 Not Found`

**解决：**
```bash
# 重启后端服务
# Ctrl+C 停止
python main.py
```

### 问题3：Playwright找不到上传元素
**现象：** 日志显示 `⚠️ 未找到文件上传元素`

**解决：**
- 检查头条发布页面是否完全加载
- 查看截图 `logs/toutiao_*.png`
- 可能需要更新选择器

### 问题4：封面图上传成功但头条不显示
**现象：** API返回成功，但头条后台没有封面

**解决：**
- 等待几分钟让平台处理
- 检查图片格式和大小是否符合要求
- 尝试手动在头条后台上传同一张图片
- 查看头条平台的错误提示

## 📊 性能测试

### 测试上传速度
```python
import time
import requests

start = time.time()
response = requests.post(
    'http://localhost:8000/api/v1/content/upload-image',
    files={'file': open('test_cover.jpg', 'rb')}
)
end = time.time()

print(f"上传耗时: {end - start:.2f} 秒")
print(f"响应: {response.json()}")
```

### 测试完整流程
```python
# 记录从选择图片到发布完成的总时间
# 包括：上传 + AI生成 + 自动化发布
```

## 🎯 成功标准

测试通过的标准：
1. ✅ 能够成功上传图片
2. ✅ 图片保存到 `uploads/covers/` 目录
3. ✅ Playwright能够找到并操作上传元素
4. ✅ 头条发布接口接收到封面图路径
5. ✅ 发布成功后头条后台显示封面图
6. ✅ 整个过程无报错或异常
7. ✅ 用户体验流畅自然

## 📞 需要帮助？

如果遇到问题：
1. 查看详细文档：`COVER_UPLOAD_IMPLEMENTATION.md`
2. 查看使用说明：`COVER_UPLOAD_README.md`
3. 查看实现总结：`COVER_UPLOAD_SUMMARY.md`
4. 检查日志文件：`logs/` 目录
5. 联系开发团队

---

**祝测试顺利！** 🎉
