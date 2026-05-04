# 高级封面图功能 - 快速测试指南

## 🚀 5分钟快速测试所有功能

### 准备工作

确保服务正在运行：
```bash
python main.py
```

---

## 1️⃣ 测试图片压缩

### 方法1：通过API测试

```bash
# 上传并压缩图片
curl -X POST http://localhost:8000/api/v1/content/upload-image \
  -F "file=@test_cover.jpg" \
  -F "compress=true" \
  -F "quality=85" \
  -F "output_format=webp"
```

**预期响应**：
```json
{
  "status": "success",
  "file_path": "uploads/covers/abc123.webp",
  "compressed": true,
  "compression_info": {
    "original_size_kb": 500.25,
    "compressed_size_kb": 125.50,
    "compression_ratio_percent": 74.91
  }
}
```

### 验证
```bash
# 查看压缩后的文件
ls -lh uploads/covers/

# 对比文件大小
# 原始文件 vs 压缩文件
```

---

## 2️⃣ 测试AI生成封面图

### 方法1：生成单个封面

```bash
curl -X POST http://localhost:8000/api/v1/content/generate-ai-cover \
  -d "title=Python自动化办公技巧" \
  -d "subtitle=10个实用方法" \
  -d "category=科技" \
  -d "style=modern"
```

### 方法2：生成多个版本

```bash
curl -X POST http://localhost:8000/api/v1/content/generate-ai-cover \
  -d "title=人工智能发展趋势" \
  -d "category=科技" \
  -d "count=3"
```

**预期响应**：
```json
{
  "status": "success",
  "file_path": "uploads/ai_covers/ai_cover_xxx.jpg",
  "style": "modern",
  "color_scheme": "科技蓝",
  "dimensions": [1280, 720]
}
```

### 验证
```bash
# 查看生成的封面图
ls -lh uploads/ai_covers/

# 打开图片查看效果
# Windows: start uploads/ai_covers/xxx.jpg
# Mac: open uploads/ai_covers/xxx.jpg
```

---

## 3️⃣ 测试封面模板库

### 获取所有模板

```bash
curl http://localhost:8000/api/v1/content/cover-templates
```

**预期响应**：
```json
{
  "status": "success",
  "total": 5,
  "templates": [
    {
      "id": "tech_news",
      "name": "科技资讯",
      "category": "科技",
      "style": "modern",
      "color_scheme": "科技蓝"
    },
    ...
  ]
}
```

### 使用模板生成

```bash
curl -X POST http://localhost:8000/api/v1/content/generate-cover-from-template \
  -d "template_id=tech_news" \
  -d "title=Python教程" \
  -d "subtitle=从入门到精通"
```

### 添加自定义模板

```bash
curl -X POST http://localhost:8000/api/v1/content/add-custom-template \
  -d "template_id=my_custom" \
  -d "name=我的模板" \
  -d "category=科技" \
  -d "style=modern" \
  -d "color_scheme=科技蓝" \
  -d "layout=title_center" \
  -d "description=自定义模板"
```

---

## 4️⃣ 测试A/B测试框架

### 步骤1：创建测试

```bash
curl -X POST http://localhost:8000/api/v1/content/ab-test/create \
  -H "Content-Type: application/json" \
  -d '{
    "test_id": "test_001",
    "article_title": "Python教程",
    "cover_variants": [
      {
        "variant_id": "A",
        "file_path": "uploads/ai_covers/cover_a.jpg",
        "style": "modern",
        "description": "现代风格"
      },
      {
        "variant_id": "B",
        "file_path": "uploads/ai_covers/cover_b.jpg",
        "style": "minimal",
        "description": "极简风格"
      }
    ],
    "description": "测试不同风格的点击率"
  }'
```

### 步骤2：模拟用户行为

```bash
# 记录曝光（变体A）
curl -X POST http://localhost:8000/api/v1/content/ab-test/test_001/impression \
  -d "variant_id=A" \
  -d "user_id=user1"

# 记录点击（变体A）
curl -X POST http://localhost:8000/api/v1/content/ab-test/test_001/click \
  -d "variant_id=A" \
  -d "user_id=user1"

# 记录曝光（变体B）
curl -X POST http://localhost:8000/api/v1/content/ab-test/test_001/impression \
  -d "variant_id=B" \
  -d "user_id=user2"

# 记录点击（变体B）
curl -X POST http://localhost:8000/api/v1/content/ab-test/test_001/click \
  -d "variant_id=B" \
  -d "user_id=user2"
```

### 步骤3：查看结果

```bash
curl http://localhost:8000/api/v1/content/ab-test/test_001
```

**预期响应**：
```json
{
  "status": "success",
  "test_id": "test_001",
  "metrics": {
    "A": {
      "impressions": 1,
      "clicks": 1,
      "ctr": 100.0
    },
    "B": {
      "impressions": 1,
      "clicks": 1,
      "ctr": 100.0
    }
  },
  "best_variant": "A"
}
```

### 步骤4：结束测试

```bash
curl -X POST http://localhost:8000/api/v1/content/ab-test/test_001/end
```

### 步骤5：生成报告

```bash
curl http://localhost:8000/api/v1/content/ab-test/test_001/report
```

**预期响应**：
```
================================================================================
A/B测试报告: test_001
================================================================================
文章标题: Python教程
测试状态: completed
...
🏆 最佳变体: A
   点击率: 100.0%
================================================================================
```

---

## ✅ 完整测试清单

### 图片压缩
- [ ] 上传图片成功
- [ ] 文件被压缩
- [ ] 压缩率合理（>50%）
- [ ] 质量可接受
- [ ] 格式转换正确

### AI生成
- [ ] 生成单个封面成功
- [ ] 生成多个版本成功
- [ ] 文件保存到正确目录
- [ ] 尺寸符合要求（1280x720）
- [ ] 文字清晰可读

### 模板库
- [ ] 获取模板列表成功
- [ ] 按分类筛选成功
- [ ] 使用模板生成成功
- [ ] 添加自定义模板成功
- [ ] 模板配置保存成功

### A/B测试
- [ ] 创建测试成功
- [ ] 记录曝光成功
- [ ] 记录点击成功
- [ ] 计算CTR正确
- [ ] 选择最佳变体正确
- [ ] 生成报告成功

---

## 🔍 调试技巧

### 查看日志
```bash
# 实时查看日志
tail -f logs/app.log

# 搜索特定功能日志
grep "压缩" logs/app.log
grep "AI封面" logs/app.log
grep "A/B测试" logs/app.log
```

### 检查文件
```bash
# 查看上传目录
ls -lh uploads/covers/
ls -lh uploads/ai_covers/
ls -lh uploads/template_covers/

# 查看测试数据
cat tests/ab_tests/test_results.json
```

### 数据库检查（如果使用）
```sql
-- 查看封面图记录
SELECT * FROM cover_images ORDER BY created_at DESC LIMIT 10;

-- 查看A/B测试结果
SELECT * FROM ab_tests WHERE status = 'active';
```

---

## ❌ 常见问题

### Q1: 图片压缩失败
**现象**: `压缩失败` 错误

**解决**:
```bash
# 检查PIL库是否安装
pip install Pillow

# 检查文件格式是否支持
# 支持: jpg, jpeg, png, webp
```

### Q2: AI生成中文乱码
**现象**: 生成的图片中文显示为方框

**解决**:
```bash
# 确保系统有中文字体
# Windows: 已内置
# Linux: sudo apt-get install fonts-wqy-zenith

# 检查字体路径是否正确
# 在代码中修改字体路径
```

### Q3: 模板加载失败
**现象**: `模板不存在` 错误

**解决**:
```bash
# 检查模板配置文件
cat templates/covers/templates_config.json

# 重新初始化模板
# 删除配置文件，重启服务会自动重建
rm templates/covers/templates_config.json
```

### Q4: A/B测试数据不更新
**现象**: CTR始终为0

**解决**:
```bash
# 确认是否正确调用record_impression和record_click
# 检查test_id和variant_id是否正确
# 查看测试结果文件
cat tests/ab_tests/test_results.json
```

---

## 📊 性能测试

### 压缩性能
```python
import time
import requests

start = time.time()
response = requests.post(
    'http://localhost:8000/api/v1/content/upload-image',
    files={'file': open('large_image.jpg', 'rb')},
    data={'compress': 'true'}
)
end = time.time()

print(f"压缩耗时: {end - start:.2f}秒")
print(f"压缩率: {response.json()['compression_info']['compression_ratio_percent']}%")
```

### AI生成性能
```python
start = time.time()
response = requests.post(
    'http://localhost:8000/api/v1/content/generate-ai-cover',
    data={
        'title': '测试标题',
        'category': '科技',
        'style': 'modern'
    }
)
end = time.time()

print(f"生成耗时: {end - start:.2f}秒")
```

---

## 🎯 成功标准

所有功能测试通过的标准：

### 图片压缩
- ✅ 压缩率 > 50%
- ✅ 质量损失 < 10%
- ✅ 处理时间 < 2秒

### AI生成
- ✅ 生成成功率 100%
- ✅ 尺寸符合规范
- ✅ 文字清晰可读
- ✅ 生成时间 < 3秒

### 模板库
- ✅ 默认模板加载成功
- ✅ 自定义模板保存成功
- ✅ 模板生成成功率 100%

### A/B测试
- ✅ 数据记录准确
- ✅ CTR计算正确
- ✅ 最佳变体选择合理
- ✅ 报告生成完整

---

## 📞 需要帮助？

如果遇到问题：
1. 查看详细文档：`ADVANCED_COVER_FEATURES.md`
2. 检查日志文件：`logs/` 目录
3. 查看测试数据：`tests/ab_tests/` 目录
4. 联系开发团队

---

**祝测试顺利！** 🎉
