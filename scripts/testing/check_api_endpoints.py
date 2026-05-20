import re
import os

files = [
    'app/api/v1/endpoints.py',
    'app/api/v1/auth.py',
    'app/api/v1/content_tasks.py',
    'app/api/v1/batch_register.py',
    'app/api/v1/new_features.py'
]

endpoints = []

for f in files:
    if os.path.exists(f):
        with open(f, encoding='utf-8') as file:
            content = file.read()
            matches = re.finditer(r'@router\.(get|post|put|delete)\(["\']([^"\']+)["\']', content)
            for m in matches:
                endpoints.append((os.path.basename(f), m.group(1), m.group(2)))

print(f'总共找到 {len(endpoints)} 个API端点\n')
print('=' * 80)

# 按路径排序
sorted_endpoints = sorted(endpoints, key=lambda x: x[2])

for file, method, path in sorted_endpoints:
    print(f'{method.upper():6} {path:50} [{file}]')

print('=' * 80)
print(f'\n总计: {len(endpoints)} 个API端点')
