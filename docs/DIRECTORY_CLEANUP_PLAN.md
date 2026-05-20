# 项目目录整理方案

## 📁 目标结构

```
smart-toolbox/
├── app/                          # 核心应用代码（保持不变）
├── frontend/                     # 前端代码（保持不变）
├── tests/                        # 单元测试和集成测试
│   ├── unit/                    # 单元测试
│   ├── integration/             # 集成测试
│   └── e2e/                     # 端到端测试
├── scripts/                      # 运维和工具脚本
│   ├── deployment/              # 部署相关脚本
│   ├── migration/               # 数据迁移脚本
│   ├── testing/                 # 测试脚本
│   ├── debugging/               # 调试诊断脚本
│   └── utilities/               # 实用工具脚本
├── docs/                         # 正式文档
│   ├── architecture/            # 架构设计文档
│   ├── api/                     # API 文档
│   ├── guides/                  # 使用指南
│   └── reports/                 # 项目报告
├── docs_archive/                 # 历史归档文档（保持不变）
├── configs/                      # 配置文件目录（新建）
│   ├── docker/                  # Docker 配置
│   └── nginx/                   # Nginx 配置
├── data/                         # 数据文件目录（新建）
│   ├── mysql/                   # MySQL 数据
│   ├── redis/                   # Redis 数据
│   └── uploads/                 # 上传文件
├── logs/                         # 日志目录（保持不变）
├── migrations/                   # 数据库迁移（保持不变）
├── alembic/                      # Alembic 配置（保持不变）
├── .env                          # 环境变量（根目录保留）
├── .gitignore                    # Git 忽略配置
├── pyproject.toml               # 项目配置
├── requirements.txt             # 依赖文件
├── docker-compose.yml           # Docker 编排
├── Dockerfile                   # Docker 镜像
├── main.py                      # 应用入口
└── README.md                    # 项目说明
```

## 🔄 具体整理步骤

### 第一步：移动根目录文档到 docs/reports/

**需要移动的文件**（约 30 个）：
- ADAPTIVE_CONTENT_EVOLUTION_GUIDE.md
- AGENT_PHASE2_PHASE3_IMPLEMENTATION.md
- AUTONOMOUS_AGENT_USER_GUIDE.md
- FIX_DUPLICATE_ACCOUNT_ERROR.md
- FRONTEND_COMPLETION_REPORT.md
- HOT_ARTICLE_REWRITE_GUIDE.md
- PHASE4_*.md (7 个文件)
- PHASE5_6_*.md (2 个文件)
- SERVICES_*.md (2 个文件)
- SMART_OPTIMIZATION_IMPLEMENTATION.md
- TOUTIAO_*.md (3 个文件)

**执行命令**：
```powershell
# 创建目标目录
New-Item -ItemType Directory -Force -Path "docs\reports"

# 移动所有报告和指南文档
Move-Item -Path "ADAPTIVE_CONTENT_EVOLUTION_GUIDE.md" -Destination "docs\reports\"
Move-Item -Path "AGENT_PHASE2_PHASE3_IMPLEMENTATION.md" -Destination "docs\reports\"
Move-Item -Path "AUTONOMOUS_AGENT_USER_GUIDE.md" -Destination "docs\reports\"
Move-Item -Path "FIX_DUPLICATE_ACCOUNT_ERROR.md" -Destination "docs\reports\"
Move-Item -Path "FRONTEND_COMPLETION_REPORT.md" -Destination "docs\reports\"
Move-Item -Path "HOT_ARTICLE_REWRITE_GUIDE.md" -Destination "docs\reports\"
Move-Item -Path "PHASE4_*.md" -Destination "docs\reports\"
Move-Item -Path "PHASE5_6_*.md" -Destination "docs\reports\"
Move-Item -Path "SERVICES_*.md" -Destination "docs\reports\"
Move-Item -Path "SMART_OPTIMIZATION_IMPLEMENTATION.md" -Destination "docs\reports\"
Move-Item -Path "TOUTIAO_*.md" -Destination "docs\reports\"
```

### 第二步：移动根目录测试文件到 scripts/testing/

**需要移动的文件**（约 15 个）：
- test_*.py (所有测试脚本)
- verify_*.py (所有验证脚本)
- check_*.py (检查脚本)
- analyze_coverage.py

**执行命令**：
```powershell
# 创建目标目录
New-Item -ItemType Directory -Force -Path "scripts\testing"

# 移动所有测试和验证脚本
Get-ChildItem -Path "*.py" -Filter "test_*" | Move-Item -Destination "scripts\testing\"
Get-ChildItem -Path "*.py" -Filter "verify_*" | Move-Item -Destination "scripts\testing\"
Get-ChildItem -Path "*.py" -Filter "check_*" | Move-Item -Destination "scripts\testing\"
Move-Item -Path "analyze_coverage.py" -Destination "scripts\testing\"
```

### 第三步：分类 scripts 目录

**scripts 目录现有 92 个文件，建议分类**：

```powershell
# 创建子目录
New-Item -ItemType Directory -Force -Path "scripts\deployment"
New-Item -ItemType Directory -Force -Path "scripts\migration"
New-Item -ItemType Directory -Force -Path "scripts\debugging"
New-Item -ItemType Directory -Force -Path "scripts\utilities"

# 部署相关脚本
Move-Item -Path "scripts\start_*.ps1" -Destination "scripts\deployment\"
Move-Item -Path "scripts\run_*.ps1" -Destination "scripts\deployment\"
Move-Item -Path "scripts\fix_api_urls.ps1" -Destination "scripts\deployment\"
Move-Item -Path "scripts\verify_fixes.ps1" -Destination "scripts\deployment\"

# 迁移相关脚本
Move-Item -Path "scripts\migrate_configs_to_db.py" -Destination "scripts\migration\"
Move-Item -Path "scripts\alter_enum_definitions.py" -Destination "scripts\migration\"
Move-Item -Path "scripts\fix_platform_enum.py" -Destination "scripts\migration\"
Move-Item -Path "scripts\fix_status_enum.py" -Destination "scripts\migration\"
Move-Item -Path "scripts\fix_status.sql" -Destination "scripts\migration\"

# 调试诊断脚本
Move-Item -Path "scripts\debug_*.py" -Destination "scripts\debugging\"
Move-Item -Path "scripts\diagnose_*.py" -Destination "scripts\debugging\"
Move-Item -Path "scripts\analyze_*.py" -Destination "scripts\debugging\"
Move-Item -Path "scripts\inspect_*.py" -Destination "scripts\debugging\"
Move-Item -Path "scripts\find_*.py" -Destination "scripts\debugging\"
Move-Item -Path "scripts\compare_*.py" -Destination "scripts\debugging\"

# 账号创建脚本移到 utilities
Move-Item -Path "scripts\create_*.py" -Destination "scripts\utilities\"
Move-Item -Path "scripts\fix_vue_*.py" -Destination "scripts\utilities\"
Move-Item -Path "scripts\fix_vue_encoding.py" -Destination "scripts\utilities\"
```

### 第四步：清理临时文件

```powershell
# 删除临时文件
Remove-Item -Path "temp_insert_method.txt" -ErrorAction SilentlyContinue
Remove-Item -Path "es_check_app_pay_info_temp_20260519.log" -ErrorAction SilentlyContinue

# 清理 __pycache__
Get-ChildItem -Path "__pycache__" -Recurse -Directory | Remove-Item -Recurse -Force

# 清理 .pytest_cache
Remove-Item -Path ".pytest_cache" -Recurse -Force -ErrorAction SilentlyContinue
```

### 第五步：更新 .gitignore

确保以下目录被正确忽略：

```gitignore
# 临时文件
*.tmp
*.temp
temp_*.txt
*_temp_*.log

# Python
__pycache__/
*.py[cod]
*$py.class
.pytest_cache/

# 日志
logs/*.log

# 数据库
*.db
*.sqlite

# 上传文件
uploads/*
!uploads/.gitkeep

# 浏览器配置文件
edge_profile*/
output/

# IDE
.idea/
.vscode/
```

### 第六步：创建 README.md

在项目根目录创建清晰的 README，包含：
- 项目简介
- 快速开始
- 目录结构说明
- 开发指南
- 部署说明

## ✅ 整理后的优势

1. **根目录清爽**：只保留核心配置和入口文件
2. **文档归类**：正式文档在 `docs/`，历史归档在 `docs_archive/`
3. **脚本分类**：按功能分类，便于查找和维护
4. **测试集中**：所有测试相关文件统一管理
5. **易于维护**：清晰的目录结构降低维护成本

## ⚠️ 注意事项

1. **移动前备份**：建议先提交 Git，确保可以回滚
2. **更新引用路径**：检查代码中对脚本路径的引用
3. **更新文档链接**：确保文档间的相互引用正确
4. **测试验证**：整理后运行测试确保功能正常

## 📝 执行顺序

1. ✅ 提交当前代码到 Git
2. ✅ 执行第一步：移动根目录文档
3. ✅ 执行第二步：移动测试文件
4. ✅ 执行第三步：分类 scripts
5. ✅ 执行第四步：清理临时文件
6. ✅ 执行第五步：更新 .gitignore
7. ✅ 执行第六步：创建 README.md
8. ✅ 验证项目正常运行
9. ✅ 提交整理后的代码
