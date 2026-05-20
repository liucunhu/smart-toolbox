import re
import os

# 后端API端点
api_files = [
    'app/api/v1/endpoints.py',
    'app/api/v1/auth.py',
    'app/api/v1/content_tasks.py',
    'app/api/v1/batch_register.py',
    'app/api/v1/new_features.py'
]

backend_endpoints = []
for f in api_files:
    if os.path.exists(f):
        with open(f, encoding='utf-8') as file:
            content = file.read()
            matches = re.finditer(r'@router\.(get|post|put|delete)\(["\']([^"\']+)["\']', content)
            for m in matches:
                backend_endpoints.append((m.group(1).upper(), m.group(2)))

# 前端页面
frontend_views = []
views_dir = 'frontend/src/views'
if os.path.exists(views_dir):
    for file in os.listdir(views_dir):
        if file.endswith('.vue'):
            frontend_views.append(file.replace('.vue', ''))

# 前端路由
routes_file = 'frontend/src/router/index.ts'
frontend_routes = []
if os.path.exists(routes_file):
    with open(routes_file, encoding='utf-8') as file:
        content = file.read()
        route_matches = re.finditer(r"path:\s*['\"]([^'\"]+)['\"]", content)
        for m in route_matches:
            path = m.group(1)
            if path and not path.startswith('/'):
                frontend_routes.append(path)

print('=' * 100)
print('后端 API 端点统计')
print('=' * 100)
print(f'总计: {len(backend_endpoints)} 个API端点\n')

# 按模块分类API
api_modules = {}
for method, path in backend_endpoints:
    # 提取模块名
    parts = path.strip('/').split('/')
    module = parts[0] if parts else 'root'
    if module not in api_modules:
        api_modules[module] = []
    api_modules[module].append((method, path))

for module in sorted(api_modules.keys()):
    print(f'\n【{module.upper()}】模块 ({len(api_modules[module])}个API):')
    for method, path in sorted(api_modules[module], key=lambda x: x[1]):
        print(f'  {method:6} {path}')

print('\n' + '=' * 100)
print('前端页面统计')
print('=' * 100)
print(f'总计: {len(frontend_views)} 个Vue页面\n')

for view in sorted(frontend_views):
    print(f'  - {view}')

print('\n' + '=' * 100)
print('前端路由统计')
print('=' * 100)
print(f'总计: {len(frontend_routes)} 个路由\n')

for route in sorted(frontend_routes):
    print(f'  - /{route}')

print('\n' + '=' * 100)
print('功能覆盖分析')
print('=' * 100)

# 分析哪些后端功能有对应的前端页面
module_mapping = {
    'accounts': ['AccountManagement', 'ToutiaoAccount', 'DouyinAccount', 'KuaishouAccount', 'WechatAccount', 'BilibiliPublish', 'XiaohongshuPublish', 'BatchRegister'],
    'auth': ['Login', 'Register'],
    'content': ['ContentCreation', 'ContentTasks', 'ImageGeneration', 'VideoRestructure', 'VisualSynthesis', 'ABTestManagement'],
    'publish': ['PublishRecords'],
    'schedule': ['ScheduleCenter'],
    'hot-trends': ['HotTrendMonitor'],
    'alerts': ['AlertCenter'],
    'nurturing': ['AccountNurturing'],
    'llm-configs': ['LLMConfig'],
    'sms': ['SmsConfig'],
    'dashboard': ['Dashboard'],
    'compliance': [],  # 合规检查，可能集成在其他页面中
    'behavior': [],  # 行为模拟，可能是后台功能
    'captcha': [],  # 验证码处理，可能是后台功能
    'fingerprint': [],  # 指纹管理，可能是后台功能
    'proxy': [],  # 代理管理，可能是后台功能
    'subtitle': [],  # 字幕处理，可能集成在视频重组中
    'video': [],  # 视频处理，可能集成在其他页面中
    'visual': [],  # 视觉处理，可能集成在视觉合成中
}

print('\n后端模块 -> 前端页面对应关系:')
for module, pages in sorted(module_mapping.items()):
    api_count = len(api_modules.get(module, []))
    page_status = '✅ ' + ', '.join(pages) if pages else '❌ 无对应页面'
    print(f'  {module:20} ({api_count:2} APIs) -> {page_status}')

print('\n' + '=' * 100)
print('可能缺失的前端功能')
print('=' * 100)

missing_features = []
for module in api_modules:
    if module not in module_mapping or not module_mapping.get(module):
        missing_features.append((module, len(api_modules[module])))

if missing_features:
    for module, count in sorted(missing_features, key=lambda x: x[1], reverse=True):
        print(f'  ⚠️  {module:20} ({count}个API) - 可能需要新增前端页面')
else:
    print('  ✅ 所有后端模块都有对应的前端页面')

print('\n' + '=' * 100)
