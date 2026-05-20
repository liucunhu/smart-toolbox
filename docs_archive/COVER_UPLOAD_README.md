# 头条自动发布上传封面图功能

## 🎯 功能说明

本功能实现了在头条文章自动发布时上传自定义封面图，让文章更具吸引力。

## 🚀 快速开始

### 1. 通过前端界面使用

#### 步骤1：启动服务
```bash
# 启动后端服务
python main.py

# 启动前端服务（新终端）
cd frontend
npm run dev
```

#### 步骤2：访问页面
打开浏览器访问：`http://localhost:5173`（或前端显示的地址）

#### 步骤3：登录头条账号
1. 进入"头条账号"页面
2. 输入账号ID、手机号/邮箱、密码
3. 点击"登录并保存 Cookie"
4. 系统会打开浏览器，完成登录后返回

#### 步骤4：发布文章（带封面图）
1. 在右侧"发布头条文章"区域
2. 输入文章主题
3. 选择文章分类
4. **点击"选择封面图"按钮，选择一张图片**
5. 预览封面图（可选）
6. 点击"🚀 一键发布（AI生成+自动发布）"
7. 等待发布完成

### 2. 通过API直接使用

#### 上传封面图
```bash
curl -X POST http://localhost:8000/api/v1/content/upload-image \
  -F "file=@/path/to/your/cover.jpg"
```

响应示例：
```json
{
  "status": "success",
  "file_path": "uploads/covers/abc123.jpg",
  "filename": "abc123.jpg"
}
```

#### 发布文章（带封面图）
```bash
curl -X POST http://localhost:8000/api/v1/content/toutiao/auto_publish \
  -d "account_id=1" \
  -d "topic=Python自动化办公技巧" \
  -d "username=your_username" \
  -d "password=your_password" \
  -d "category=科技" \
  -d "cover_image_path=uploads/covers/abc123.jpg"
```

### 3. 通过Python代码使用

```python
from app.services.publish.toutiao_publisher import ToutiaoPublisher

async def publish_with_cover():
    publisher = ToutiaoPublisher(account_id=1)
    
    try:
        await publisher.initialize_browser()
        
        # 登录
        await publisher.login_with_manual_input("username", "password")
        
        # 发布文章（带封面图）
        result = await publisher.publish_article(
            title="我的文章标题",
            content="文章内容...",
            category="科技",
            tags=["Python", "自动化"],
            cover_image_path="uploads/covers/my_cover.jpg"  # 封面图路径
        )
        
        print(f"发布结果: {result}")
        
    finally:
        await publisher.close()
```

## 📸 封面图要求

### 推荐规格
- **格式**：JPG 或 PNG
- **比例**：16:9（头条推荐）
- **尺寸**：1280x720 像素或更高
- **大小**：小于 2MB
- **内容**：清晰、与文章相关、无版权争议

### 注意事项
- ✅ 使用高质量、清晰的图片
- ✅ 图片内容与文章主题一致
- ✅ 避免文字过多，保持简洁
- ❌ 不要使用模糊、低分辨率图片
- ❌ 避免使用有版权争议的图片
- ❌ 不要包含违规内容

## 🧪 测试功能

项目提供了测试脚本 `test_cover_upload.py`：

```bash
# 1. 准备测试封面图
# 将一张jpg/png图片放在项目根目录，命名为 test_cover.jpg

# 2. 运行测试
python test_cover_upload.py
```

测试脚本会：
1. 检查测试封面图是否存在
2. 初始化浏览器
3. 提示手动登录
4. 发布一篇测试文章（带封面图）
5. 显示发布结果

## 🔧 技术实现

### 前端
- Vue 3 + TypeScript
- Element Plus UI组件库
- Axios HTTP客户端

### 后端
- FastAPI
- Playwright（浏览器自动化）
- Python异步编程

### 工作流程
```
用户选择封面图
    ↓
前端预览并缓存
    ↓
上传到服务器 (/api/v1/content/upload-image)
    ↓
服务器保存文件并返回路径
    ↓
调用发布API (传入cover_image_path)
    ↓
Playwright自动填充并发布
    ↓
完成
```

## ❓ 常见问题

### Q1: 封面图上传失败怎么办？
A: 
- 检查文件格式是否为JPG或PNG
- 检查文件大小是否超过限制
- 查看后端日志了解具体错误
- 如果上传失败，系统会使用默认封面继续发布

### Q2: 为什么看不到封面图预览？
A:
- 确保选择了有效的图片文件
- 检查浏览器控制台是否有错误
- 刷新页面重试

### Q3: 发布后封面图不显示？
A:
- 检查头条后台确认发布状态
- 等待几分钟让平台处理
- 确认封面图符合平台要求
- 查看后端日志了解上传过程

### Q4: 可以批量上传多张封面图吗？
A:
- 当前版本只支持单张封面图
- 如需多图功能，可以联系开发团队扩展

### Q5: 如何清理上传的封面图文件？
A:
- 文件保存在 `uploads/covers/` 目录
- 可以定期手动清理旧文件
- 或编写定时任务自动清理

## 📞 技术支持

如有问题或建议，请：
1. 查看日志文件（`logs/` 目录）
2. 检查浏览器控制台错误
3. 联系开发团队

## 📄 许可证

本项目遵循项目整体许可证。

---

**祝使用愉快！** 🎉
