"""
查找头条的内部上传API
通过分析页面的全局对象和函数
"""
import asyncio
from playwright.async_api import async_playwright
import json

async def find_upload_api():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        context = browser.contexts[0]
        page = context.pages[0] if context.pages else await context.new_page()
        
        if "publish" not in page.url:
            print("跳转到发布页面...")
            await page.goto("https://mp.toutiao.com/profile_v4/graphic/publish", wait_until="domcontentloaded")
            await asyncio.sleep(3)
        
        print("=" * 80)
        print("查找头条内部上传API")
        print("=" * 80)
        
        # 步骤1：列出所有全局对象中包含upload/image/cover的
        print("\n【步骤1】查找全局对象中的上传相关函数...")
        global_objects = await page.evaluate("""
            () => {
                const results = {
                    functions: [],
                    objects: []
                };
                
                // 检查window对象的所有属性
                for (const key of Object.keys(window)) {
                    const lowerKey = key.toLowerCase();
                    if (lowerKey.includes('upload') || lowerKey.includes('image') || lowerKey.includes('cover') || lowerKey.includes('file')) {
                        const value = window[key];
                        if (typeof value === 'function') {
                            results.functions.push(key);
                        } else if (typeof value === 'object' && value !== null) {
                            results.objects.push(key);
                        }
                    }
                }
                
                return results;
            }
        """)
        
        print(f"   找到 {len(global_objects['functions'])} 个相关函数:")
        for func in global_objects['functions'][:20]:  # 只显示前20个
            print(f"      - {func}")
        
        print(f"\n   找到 {len(global_objects['objects'])} 个相关对象:")
        for obj in global_objects['objects'][:20]:
            print(f"      - {obj}")
        
        # 步骤2：查找常见的上传SDK
        print("\n【步骤2】查找上传SDK...")
        upload_sdks = await page.evaluate("""
            () => {
                const sdks = [];
                
                // 常见的上传库
                const candidates = [
                    'Uploader', 'UploadService', 'ImageUploader', 
                    'FileUploader', 'CoverUploader', 'MediaUploader',
                    '__upload__', 'uploadManager', 'uploadController'
                ];
                
                for (const name of candidates) {
                    if (window[name]) {
                        sdks.push({
                            name: name,
                            type: typeof window[name],
                            methods: Object.getOwnPropertyNames(window[name]).filter(m => !m.startsWith('_'))
                        });
                    }
                }
                
                // 也检查一些可能的命名空间
                const namespaces = ['Toutiao', 'MP', 'PGC', 'Editor'];
                for (const ns of namespaces) {
                    if (window[ns]) {
                        for (const key of Object.keys(window[ns])) {
                            if (key.toLowerCase().includes('upload') || key.toLowerCase().includes('image')) {
                                sdks.push({
                                    namespace: ns,
                                    name: key,
                                    type: typeof window[ns][key]
                                });
                            }
                        }
                    }
                }
                
                return sdks;
            }
        """)
        
        if upload_sdks:
            print(f"   找到 {len(upload_sdks)} 个上传SDK:")
            for sdk in upload_sdks:
                print(f"      - {sdk.get('namespace', '')}.{sdk.get('name', sdk.get('namespace', ''))}: {sdk['type']}")
                if 'methods' in sdk:
                    print(f"         方法: {', '.join(sdk['methods'][:10])}")
        else:
            print("   未找到明显的上传SDK")
        
        # 步骤3：分析网络请求历史，找到上传接口
        print("\n【步骤3】分析已发送的网络请求...")
        network_history = await page.evaluate("""
            () => {
                // 这个需要通过Performance API获取
                const entries = performance.getEntriesByType('resource');
                const uploads = [];
                
                for (const entry of entries) {
                    if (entry.name && (
                        entry.name.includes('upload') || 
                        entry.name.includes('image') ||
                        entry.name.includes('cover')
                    )) {
                        uploads.push({
                            url: entry.name,
                            type: entry.initiatorType,
                            duration: entry.duration
                        });
                    }
                }
                
                return uploads;
            }
        """)
        
        if network_history:
            print(f"   找到 {len(network_history)} 个相关网络请求:")
            for req in network_history[:10]:
                print(f"      - [{req['type']}] {req['url'][:100]}")
        else:
            print("   未找到历史上传请求")
        
        # 步骤4：查找页面中的所有fetch/XMLHttpRequest调用点
        print("\n【步骤4】拦截未来的网络请求...")
        
        request_log = []
        
        def log_request(request):
            if any(keyword in request.url.lower() for keyword in ['api', 'upload', 'image']):
                request_log.append({
                    'url': request.url,
                    'method': request.method,
                    'resource_type': request.resource_type
                })
        
        page.on("request", log_request)
        
        # 触发一些操作来产生网络请求
        print("   触发页面交互以产生网络请求...")
        
        # 点击标题输入框
        await page.click('[contenteditable="true"]', timeout=5000, force=True)
        await asyncio.sleep(1)
        
        # 滚动页面
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(1)
        
        await page.evaluate("window.scrollTo(0, 0)")
        await asyncio.sleep(1)
        
        print(f"   捕获到 {len(request_log)} 个API请求:")
        for req in request_log[:20]:
            print(f"      - {req['method']} {req['url'][:120]}")
        
        # 步骤5：保存完整的分析结果
        analysis_result = {
            'global_objects': global_objects,
            'upload_sdks': upload_sdks,
            'network_history': network_history,
            'recent_requests': request_log
        }
        
        with open('logs/upload_api_analysis.json', 'w', encoding='utf-8') as f:
            json.dump(analysis_result, f, ensure_ascii=False, indent=2)
        
        print(f"\n   [OK] 完整分析结果已保存: logs/upload_api_analysis.json")
        
        print("\n" + "=" * 80)
        print("分析完成！")
        print("=" * 80)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(find_upload_api())
