# Git 历史敏感信息清理指南

**警告**: ⚠️ 此操作会重写 Git 历史，影响所有协作者！请在执行前仔细阅读。

---

## 📋 清理前的准备

### 1. 通知团队成员

如果项目有多个协作者，必须：
- ✅ 通知所有人即将进行历史重写
- ✅ 确保所有人都已推送本地更改
- ✅ 约定统一时间执行清理
- ✅ 清理后所有人需要重新克隆仓库

### 2. 备份当前状态

```powershell
# 创建备份分支
git branch backup-before-cleanup-$(Get-Date -Format "yyyyMMdd")

# 导出当前提交记录
git log --all --oneline > git_log_backup.txt

# 备份整个仓库（可选）
Copy-Item -Path . -Destination ..\smart-toolbox-backup -Recurse
```

### 3. 确认要清理的内容

本次需要清理的敏感信息：
- ❌ DashScope API Key: `sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
- ❌ SiliconFlow API Key: `sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
- ❌ MySQL 密码: `YourDBPassword`
- ❌ Redis 密码: `YourRedisPassword`
- ❌ 头条密码: `YourToutiaoPassword`

---

## 🔧 方法一：使用 BFG Repo-Cleaner（推荐）

### 优点
- ✅ 速度快（比 filter-branch 快 10-720 倍）
- ✅ 操作简单
- ✅ 自动处理各种边缘情况

### 步骤

#### 1. 下载 BFG

```powershell
# 方法1: 直接下载
Invoke-WebRequest -Uri "https://repo1.maven.org/maven2/com/madgag/bfg/1.14.0/bfg-1.14.0.jar" -OutFile "bfg.jar"

# 方法2: 使用 Chocolatey（如果已安装）
choco install bfg-repo-cleaner
```

#### 2. 创建替换规则文件

已创建 `passwords.txt`，内容如下：
```
sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx==>REMOVED_DASHSCOPE_KEY
sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx==>REMOVED_SILICONFLOW_KEY
YourDBPassword==>REMOVED_DB_PASSWORD
YourRedisPassword==>REMOVED_REDIS_PASSWORD
YourToutiaoPassword==>REMOVED_TOUTIAO_PASSWORD
```

#### 3. 克隆镜像仓库

```powershell
# 克隆为镜像（保留所有引用）
git clone --mirror D:\code\smart-toolbox smart-toolbox-clean.git

# 进入克隆的目录
cd smart-toolbox-clean.git
```

#### 4. 执行清理

```powershell
# 替换敏感字符串
java -jar ..\bfg.jar --replace-text ..\passwords.txt .

# 或者删除特定文件
java -jar ..\bfg.jar --delete-files test_dashscope_pro.py .
```

#### 5. 清理和推送

```powershell
# 清理 Git 对象
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# 验证清理结果
git log -p --all | Select-String "sk-[a-z0-9]{20,}"

# 强制推送到远程（⚠️ 危险！）
git push origin --force --all
git push origin --force --tags

# 返回并清理
cd ..
Remove-Item -Recurse -Force smart-toolbox-clean.git
```

---

## 🔧 方法二：使用 git filter-branch（无需额外工具）

### 优点
- ✅ 无需安装额外工具
- ✅ Git 内置功能

### 缺点
- ❌ 速度慢
- ❌ 操作复杂
- ❌ 容易出错

### 步骤

#### 1. 运行自动化脚本

```powershell
.\scripts\utilities\cleanup_git_history.ps1
```

#### 2. 手动执行（如果需要自定义）

```powershell
# 备份
git branch backup-before-cleanup

# 从历史中删除特定文件
git filter-branch --force --index-filter `
  "git rm --cached --ignore-unmatch scripts/test_dashscope_pro.py" `
  --prune-empty --tag-name-filter cat -- --all

# 清理引用
git for-each-ref --format='delete %(refname)' refs/original | git update-ref --stdin
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# 强制推送
git push origin --force --all
git push origin --force --tags
```

---

## 🔧 方法三：完全重新开始（最彻底）

如果历史记录不 important，可以完全重新开始：

```powershell
# 1. 保存当前代码
git checkout master
git archive --format=zip --output=../smart-toolbox-code.zip HEAD

# 2. 删除 .git 目录
Remove-Item -Recurse -Force .git

# 3. 重新初始化
git init
git add .
git commit -m "Initial commit - Clean start after security audit"

# 4. 添加远程仓库
git remote add origin https://github.com/liucunhu/smart-toolbox.git

# 5. 强制推送
git push -u origin master --force
```

**注意**: 这会丢失所有历史提交记录、标签和分支！

---

## ✅ 清理后的验证

### 1. 检查是否还有敏感信息

```powershell
# 搜索 API Key
git log -p --all | Select-String "sk-[a-z0-9]{20,}"

# 搜索密码
git log -p --all | Select-String "YourDBPassword|YourRedisPassword|YourToutiaoPassword"

# 搜索特定文件
git log --all --full-history -- "**/test_dashscope_pro.py"
```

### 2. 验证仓库完整性

```powershell
# 检查对象数据库
git fsck --full

# 查看所有分支
git branch -a

# 查看标签
git tag
```

### 3. 测试克隆

```powershell
# 在新目录测试克隆
cd ..
git clone https://github.com/liucunhu/smart-toolbox.git test-clean-repo
cd test-clean-repo

# 检查是否有敏感信息
Get-ChildItem -Recurse -Include "*.py","*.env" | Select-String "sk-[a-z0-9]{20,}"

# 清理测试目录
cd ..
Remove-Item -Recurse -Force test-clean-repo
```

---

## 🔄 团队成员后续操作

清理完成后，**所有协作者**必须：

### 1. 删除旧仓库

```powershell
# 备份重要分支（如果有未推送的更改）
git checkout -b my-backup-branch

# 删除旧仓库
Remove-Item -Recurse -Force smart-toolbox
```

### 2. 重新克隆

```powershell
git clone https://github.com/liucunhu/smart-toolbox.git
cd smart-toolbox
```

### 3. 恢复本地分支（如果有）

```powershell
# 从备份分支 cherry-pick 提交
git cherry-pick <commit-hash>
```

---

## 🛡️ 防止未来泄露

### 1. 安装 pre-commit hooks

```powershell
# 安装 pre-commit
pip install pre-commit detect-secrets

# 初始化
pre-commit install

# 创建基线
detect-secrets scan > .secrets.baseline

# 添加到 Git
git add .pre-commit-config.yaml .secrets.baseline
git commit -m "Add pre-commit hooks for secret detection"
```

### 2. 配置 GitHub Secret Scanning

1. 访问仓库 Settings → Security & analysis
2. 启用 "Secret scanning"
3. 启用 "Push protection"

### 3. 更新 .gitignore

确保以下文件被忽略：
```gitignore
.env
.env.local
.env.*.local
*.key
*.pem
secrets/
```

### 4. 团队培训

- 永远不要硬编码敏感信息
- 使用环境变量或密钥管理服务
- 提交前运行 `detect-secrets scan`
- 定期审计代码库

---

## 📊 方法对比

| 方法 | 速度 | 难度 | 风险 | 适用场景 |
|------|------|------|------|---------|
| **BFG Repo-Cleaner** | ⭐⭐⭐⭐⭐ | ⭐⭐ | 中 | 大型仓库，多个敏感信息 |
| **git filter-branch** | ⭐⭐ | ⭐⭐⭐⭐ | 高 | 小型仓库，简单清理 |
| **完全重新开始** | ⭐⭐⭐⭐⭐ | ⭐ | 极高 | 历史不重要，全新开始 |

---

## ⚠️ 常见问题

### Q1: 强制推送后其他人无法推送怎么办？

**A**: 他们必须重新克隆仓库，或者：
```bash
git fetch origin
git reset --hard origin/master
```

### Q2: 清理后发现还需要删除其他敏感信息怎么办？

**A**: 可以再次运行清理流程，但建议一次性清理所有内容。

### Q3: GitHub 会保留旧的 commit 吗？

**A**: 不会，强制推送后旧的 commit 会被垃圾回收。但 GitHub 可能需要一些时间来清理。

### Q4: 如何确认敏感信息真的被清除了？

**A**: 
```bash
# 检查 GitHub API
curl -H "Authorization: token YOUR_TOKEN" \
  https://api.github.com/repos/liucunhu/smart-toolbox/git/trees/master?recursive=1
```

---

## 📞 需要帮助？

如果在清理过程中遇到问题：

1. 查看 Git 官方文档: https://git-scm.com/docs/git-filter-branch
2. BFG 文档: https://rtyley.github.io/bfg-repo-cleaner/
3. GitHub 帮助: https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository

---

**最后提醒**: 
- ⚠️ 此操作不可逆！
- ⚠️ 务必先备份！
- ⚠️ 通知所有协作者！
- ⚠️ 清理后立即轮换所有密钥！
