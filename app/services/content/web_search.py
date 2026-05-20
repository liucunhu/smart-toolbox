"""
网络素材搜索服务
从互联网获取实时素材用于文章创作
"""
import httpx
from typing import List, Dict, Optional
from app.utils.logger import logger


class WebSearchService:
    """网络素材搜索服务"""
    
    def __init__(self, db=None):
        self.db = db
        self.timeout = 10.0
    
    async def search_with_bing(
        self, 
        query: str, 
        num_results: int = 5,
        language: str = "zh-CN"
    ) -> List[Dict]:
        """
        使用 Bing Search API 搜索（需要API Key）
        
        Args:
            query: 搜索关键词
            num_results: 返回结果数量
            language: 语言设置
        
        Returns:
            搜索结果列表
        """
        try:
            from app.core.config import settings
            
            if not settings.BING_SEARCH_API_KEY:
                logger.warning("⚠️  Bing Search API Key 未配置，跳过Bing搜索")
                return []
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    "https://api.bing.microsoft.com/v7.0/search",
                    headers={
                        "Ocp-Apim-Subscription-Key": settings.BING_SEARCH_API_KEY
                    },
                    params={
                        "q": query,
                        "count": num_results,
                        "mkt": language,
                        "responseFilter": "Webpages"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    results = []
                    
                    for item in data.get("webPages", {}).get("value", [])[:num_results]:
                        results.append({
                            "title": item.get("name", ""),
                            "url": item.get("url", ""),
                            "snippet": item.get("snippet", ""),
                            "source": "bing"
                        })
                    
                    logger.info(f"✅ Bing搜索成功，找到 {len(results)} 条结果")
                    return results
                else:
                    logger.error(f"❌ Bing搜索失败: {response.status_code}")
                    return []
                    
        except Exception as e:
            logger.error(f"❌ Bing搜索异常: {str(e)}")
            return []
    
    async def search_with_duckduckgo(
        self,
        query: str,
        num_results: int = 5
    ) -> List[Dict]:
        """
        使用 DuckDuckGo 搜索（免费，无需API Key）
        
        Args:
            query: 搜索关键词
            num_results: 返回结果数量
        
        Returns:
            搜索结果列表
        """
        try:
            # DuckDuckGo HTML 搜索
            url = f"https://html.duckduckgo.com/html/"
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    url,
                    data={"q": query},
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                    }
                )
                
                if response.status_code == 200:
                    # 简单的HTML解析（实际项目中建议使用BeautifulSoup）
                    html_content = response.text
                    
                    # 这里简化处理，实际应该解析HTML提取标题、链接、摘要
                    # 由于DuckDuckGo反爬较严，建议使用其他方式
                    logger.warning("⚠️  DuckDuckGo HTML解析暂不支持，返回空结果")
                    return []
                else:
                    logger.error(f"❌ DuckDuckGo搜索失败: {response.status_code}")
                    return []
                    
        except Exception as e:
            logger.error(f"❌ DuckDuckGo搜索异常: {str(e)}")
            return []
    
    async def search_with_serpapi(
        self,
        query: str,
        num_results: int = 5,
        engine: str = "google"
    ) -> List[Dict]:
        """
        使用 SerpAPI（付费，但稳定可靠）
        
        Args:
            query: 搜索关键词
            num_results: 返回结果数量
            engine: 搜索引擎（google/bing/baidu）
        
        Returns:
            搜索结果列表
        """
        try:
            from app.core.config import settings
            
            if not settings.SERPAPI_API_KEY:
                logger.warning("⚠️  SerpAPI Key 未配置，跳过SerpAPI搜索")
                return []
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    "https://serpapi.com/search",
                    params={
                        "engine": engine,
                        "q": query,
                        "api_key": settings.SERPAPI_API_KEY,
                        "num": num_results,
                        "hl": "zh-cn"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    results = []
                    
                    for item in data.get("organic_results", [])[:num_results]:
                        results.append({
                            "title": item.get("title", ""),
                            "url": item.get("link", ""),
                            "snippet": item.get("snippet", ""),
                            "source": engine
                        })
                    
                    logger.info(f"✅ SerpAPI搜索成功，找到 {len(results)} 条结果")
                    return results
                else:
                    logger.error(f"❌ SerpAPI搜索失败: {response.status_code}")
                    return []
                    
        except Exception as e:
            logger.error(f"❌ SerpAPI搜索异常: {str(e)}")
            return []
    
    async def _generate_from_hot_topic(self, topic: str) -> str:
        """
        当网络搜索失败时，基于热点话题生成原创内容框架
        
        Args:
            topic: 热点话题
            
        Returns:
            生成的内容框架/建议
        """
        try:
            from openai import OpenAI
            from app.services.system.config_service import LLMConfigService
            
            if not self.db:
                logger.warning("⚠️  数据库会话未提供,无法生成内容框架")
                return None
            
            # ✅ 从数据库获取文案生成配置
            llm_service = LLMConfigService(self.db)
            config = llm_service.get_default_llm_config("copywriting")
            
            if not config:
                logger.warning("⚠️  数据库中未找到文案生成配置")
                return None
            
            client = OpenAI(
                api_key=config.api_key,
                base_url=config.base_url,
                timeout=float(config.timeout or 30)
            )
            
            prompt = f"""请针对热点话题 "{topic}" 生成一篇原创文章的内容框架和要点。

要求：
1. 提供3-5个核心观点
2. 每个观点包含具体的案例或数据支撑
3. 给出文章结构建议（开头、主体、结尾）
4. 提供写作角度建议（避免与现有文章雷同）
5. 总字数控制在800-1000字

请以简洁的要点形式输出，方便后续扩写成完整文章。"""
            
            response = client.chat.completions.create(
                model="Qwen/Qwen2.5-7B-Instruct",
                messages=[
                    {"role": "system", "content": "你是一位专业的内容创作者，擅长将热点话题转化为原创内容。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=1000
            )
            
            content_framework = response.choices[0].message.content
            
            if content_framework:
                logger.info(f"✅ 已为话题 '{topic}' 生成原创内容框架")
                return content_framework[:500]  # 返回前500字作为snippet
            else:
                return None
                
        except Exception as e:
            logger.error(f"❌ 生成内容框架失败: {e}")
            return None
    
    async def search_materials(
        self,
        topic: str,
        num_results: int = 5,
        prefer_free: bool = True
    ) -> List[Dict]:
        """
        智能搜索素材（自动选择可用的搜索引擎）
        
        Args:
            topic: 搜索主题
            num_results: 返回结果数量
            prefer_free: 优先使用免费方案
        
        Returns:
            搜索结果列表
        """
        logger.info(f"🔍 开始搜索素材: {topic}")
        
        results = []
        
        # 策略1: 尝试免费方案（DuckDuckGo - 暂不可用）
        # if prefer_free:
        #     results = await self.search_with_duckduckgo(topic, num_results)
        
        # 策略2: 尝试 Bing（需要API Key）
        if not results:
            results = await self.search_with_bing(topic, num_results)
        
        # 策略3: 尝试 SerpAPI（需要API Key）
        if not results:
            results = await self.search_with_serpapi(topic, num_results)
        
        # ✅ 策略4: 如果所有搜索引擎都失败，使用头条热搜作为备选
        if not results:
            try:
                logger.info(f"⚠️  所有搜索引擎失败，尝试使用头条热搜数据...")
                from app.services.content.hot_trend_injector import HotTrendInjector
                injector = HotTrendInjector()
                
                # 同步获取热搜
                hot_topics = injector.fetch_hot_topics("toutiao", num_results)
                
                if hot_topics:
                    for topic_item in hot_topics[:num_results]:
                        keyword = topic_item.get("keyword", "")
                        rank = topic_item.get("rank", 0)
                        heat = topic_item.get("heat", 0)
                        
                        if keyword:
                            results.append({
                                "title": keyword,
                                "url": f"https://www.toutiao.com/hot_word/{keyword}",
                                "snippet": f"今日头条热搜第{rank}名，热度 {heat:,}",
                                "source": "toutiao_hot"
                            })
                    
                    logger.info(f"✅ 从头条热搜获取到 {len(results)} 条素材")
                    
                    # ★★★ 关键增强：尝试基于头条热搜进行深度二次创作 ★★★
                    logger.info(f"🔄 检测到头条热搜，尝试深度二次创作...")
                    try:
                        from app.services.content.hot_article_rewriter import HotArticleRewriter
                        from app.services.content.toutiao_article_fetcher import fetch_toutiao_article
                        
                        rewriter = HotArticleRewriter()
                        
                        # 选择热度最高的话题进行二次创作
                        best_topic = max(hot_topics, key=lambda x: x.get("heat", 0))
                        topic_keyword = best_topic.get("keyword", "")
                        
                        if topic_keyword:
                            logger.info(f"   📰 选择热搜话题进行二次创作: {topic_keyword} (热度: {best_topic.get('heat', 0):,})")
                            
                            # 步骤1: 使用 Playwright 抓取真实文章内容
                            logger.info(f"   🔍 正在使用 Playwright 抓取真实文章...")
                            hot_article_data = await fetch_toutiao_article(topic_keyword, max_results=3)
                            
                            if hot_article_data:
                                logger.info(f"✅ 成功抓取真实文章")
                                logger.info(f"   标题: {hot_article_data['title'][:50]}...")
                                logger.info(f"   长度: {len(hot_article_data['content'])}字")
                                
                                # 步骤2: 使用 HotArticleRewriter 进行深度二次创作
                                logger.info(f"   🔄 开始深度二次创作...")
                                rewrite_result = await rewriter.rewrite_from_hot_article(
                                    hot_article_content=hot_article_data["content"],
                                    hot_article_title=hot_article_data["title"],
                                    target_platform="toutiao",
                                    rewrite_depth="deep"
                                )
                                
                                if rewrite_result.get("status") == "success":
                                    logger.info(f"✅ 热点文章二次创作成功")
                                    logger.info(f"   原创度: {rewrite_result['originality_score']:.0%}")
                                    logger.info(f"   新标题: {rewrite_result['new_title'][:50]}...")
                                    
                                    # 将二次创作结果添加到最前面（优先使用）
                                    results.insert(0, {
                                        "title": rewrite_result["new_title"],
                                        "url": "rewritten_from_real_article",
                                        "snippet": rewrite_result["content"],
                                        "source": "hot_article_deep_rewrite",
                                        "is_generated": True,
                                        "rewrite_type": "deep_rewrite",
                                        "originality_score": rewrite_result["originality_score"],
                                        "original_title": hot_article_data["title"]
                                    })
                                else:
                                    logger.warning(f"⚠️  二次创作失败: {rewrite_result.get('error')}")
                                    # 降级：直接使用抓取的原文
                                    results.insert(0, {
                                        "title": f"【热点文章】{hot_article_data['title']}",
                                        "url": hot_article_data["url"],
                                        "snippet": hot_article_data["content"],
                                        "source": "real_article_fetched",
                                        "is_generated": False
                                    })
                            else:
                                # 降级：无法抓取真实文章，使用LLM生成
                                logger.info(f"ℹ️  无法抓取真实文章，使用LLM基于话题生成...")
                                fallback_content = await self._generate_from_hot_topic(topic_keyword)
                                
                                if fallback_content:
                                    logger.info(f"✅ 基于热点话题完成深度原创")
                                    results.insert(0, {
                                        "title": f"【热点二创】{topic_keyword}",
                                        "url": "ai_deep_rewrite",
                                        "snippet": fallback_content,
                                        "source": "hot_topic_deep_rewrite",
                                        "is_generated": True,
                                        "rewrite_type": "deep_original"
                                    })
                                    
                    except Exception as e:
                        logger.warning(f"⚠️  热点二次创作失败: {e}，继续使用原始热搜数据")
                        import traceback
                        traceback.print_exc()
                        
            except Exception as e:
                logger.warning(f"⚠️  头条热搜获取也失败: {e}")
        
        # ★★★ 策略5: 如果仍然没有结果，使用热点文章二次创作引擎 ★★★
        if not results:
            try:
                logger.info(f"🔄 网络搜索完全失败，启动热点文章二次创作引擎...")
                
                # 步骤1: 获取热点话题对应的原文章内容
                from app.services.content.web_content_fetcher import get_web_content_fetcher
                from app.services.content.hot_article_rewriter import HotArticleRewriter
                
                fetcher = get_web_content_fetcher()
                rewriter = HotArticleRewriter()
                
                # 尝试从头条热搜获取相关文章URL并抓取内容
                hot_article_data = None
                try:
                    from app.services.content.hot_trend_injector import HotTrendInjector
                    injector = HotTrendInjector()
                    hot_topics = injector.fetch_hot_topics("toutiao", 3)
                    
                    if hot_topics:
                        # 尝试抓取第一个热点话题的相关文章
                        for hot_topic in hot_topics[:3]:
                            keyword = hot_topic.get("keyword", "")
                            if keyword:
                                logger.info(f"   📰 尝试抓取热点文章: {keyword}")
                                # 构造头条搜索URL（实际应该使用真实的头条文章URL）
                                search_url = f"https://www.toutiao.com/search/?keyword={keyword}"
                                
                                # 注意：这里简化处理，实际应该从搜索结果中提取真实文章URL
                                # 由于头条的反爬机制，我们直接使用话题生成内容
                                break
                except Exception as e:
                    logger.warning(f"⚠️  获取热点话题失败: {e}")
                
                # 步骤2: 如果有热点文章内容，进行深度二次创作
                if hot_article_data:
                    logger.info(f"✅ 找到热点原文章，开始深度二次创作...")
                    rewrite_result = await rewriter.rewrite_from_hot_article(
                        hot_article_content=hot_article_data["content"],
                        hot_article_title=hot_article_data["title"],
                        target_platform="toutiao",
                        rewrite_depth="deep"
                    )
                    
                    if rewrite_result.get("status") == "success":
                        logger.info(f"✅ 热点文章二次创作成功")
                        logger.info(f"   原创度: {rewrite_result['originality_score']:.0%}")
                        results.append({
                            "title": rewrite_result["new_title"],
                            "url": "rewritten_from_hot_article",
                            "snippet": rewrite_result["content"],
                            "source": "hot_article_rewrite",
                            "is_generated": True,
                            "originality_score": rewrite_result["originality_score"]
                        })
                    else:
                        logger.warning(f"⚠️  二次创作失败: {rewrite_result.get('error')}")
                        # 降级到基于话题生成
                        fallback_content = await self._generate_from_hot_topic(topic)
                        if fallback_content:
                            results.append({
                                "title": f"【二次创作】{topic}",
                                "url": "generated_by_ai",
                                "snippet": fallback_content,
                                "source": "ai_rewrite",
                                "is_generated": True
                            })
                else:
                    # 步骤3: 没有原文章，直接基于话题生成原创内容框架
                    logger.info(f"ℹ️  未找到热点原文章，基于话题生成原创内容框架...")
                    fallback_content = await self._generate_from_hot_topic(topic)
                    
                    if fallback_content:
                        logger.info(f"✅ 已生成原创内容框架")
                        results.append({
                            "title": f"【原创】{topic}",
                            "url": "generated_by_ai",
                            "snippet": fallback_content,
                            "source": "ai_original",
                            "is_generated": True
                        })
                        
            except Exception as e:
                logger.error(f"❌ 二次创作引擎也失败: {e}")
                import traceback
                traceback.print_exc()
        
        if results:
            logger.info(f"✅ 成功获取 {len(results)} 条素材")
        else:
            logger.warning("⚠️  所有数据源都失败，将仅使用LLM知识生成")
        
        return results
    
    def format_search_results_for_prompt(
        self,
        results: List[Dict],
        max_length: int = 2000
    ) -> str:
        """
        将搜索结果格式化为LLM提示词的一部分
        
        Args:
            results: 搜索结果列表
            max_length: 最大长度限制
        
        Returns:
            格式化后的文本
        """
        if not results:
            return ""
        
        formatted = "【网络素材参考】\n\n"
        total_length = len(formatted)
        
        for i, result in enumerate(results, 1):
            snippet = result.get("snippet", "")
            title = result.get("title", "")
            
            # 限制每个结果的长度
            if len(snippet) > 300:
                snippet = snippet[:300] + "..."
            
            entry = f"{i}. {title}\n   {snippet}\n\n"
            
            # 检查是否超过总长度限制
            if total_length + len(entry) > max_length:
                break
            
            formatted += entry
            total_length += len(entry)
        
        return formatted


def get_web_search_service(db=None) -> WebSearchService:
    """获取网络搜索服务实例
    
    Args:
        db: 数据库会话(可选,但推荐提供以支持LLM生成功能)
    """
    return WebSearchService(db=db)
