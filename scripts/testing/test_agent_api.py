import requests

base_url = "http://localhost:8000"
paths = [
    '/api/v1/agents/system/status',
    '/api/v1/agents/list',
    '/api/v1/agents/workflows',
]

print("测试智能体API端点:\n")
for path in paths:
    try:
        resp = requests.get(f"{base_url}{path}")
        print(f"{path}: {resp.status_code}")
        if resp.status_code == 200:
            print(f"  响应: {resp.json()}")
    except Exception as e:
        print(f"{path}: ERROR - {e}")
