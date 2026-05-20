"""
网页内容抓取服务
用于从URL提取文章完整内容，支持多种网站结构
"""
import httpx
from typing import Optional, Dict
from app.utils.logger import logger
from bs4 import BeautifulSoup


class WebContentFetcher:
    """网页内容抓取服务"""
    
    def __init__(self):
        self.timeout = 15.0
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }
    
    async def fetch_article_content(self, url: str) -> Optional[Dict]:
        """
        从URL抓取文章完整内容
        
        Args:
            url: 文章URL
            
        Returns:
            {
                "title": "文章标题",
                "content": "文章内容",
                "author": "作者",
                "publish_date": "发布日期"
            }
        """
        try:
            logger.info(f"🌐 开始抓取文章内容: {url}")
            
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                response = await client.get(url, headers=self.headers)
                
                if response.status_code != 200:
                    logger.error(f"❌ 请求失败，状态码: {response.status_code}")
                    return None
                
                # 解析HTML
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 提取标题
                title = self._extract_title(soup)
                
                # 提取正文内容
                content = self._extract_content(soup)
                
                # 提取作者（可选）
                author = self._extract_author(soup)
                
                # 提取发布日期（可选）
                publish_date = self._extract_publish_date(soup)
                
                if not title or not content:
                    logger.warning(f"⚠️  未能提取到有效的标题或内容")
                    return None
                
                logger.info(f"✅ 文章抓取成功")
                logger.info(f"   标题: {title[:50]}...")
                logger.info(f"   内容长度: {len(content)}字")
                
                return {
                    "title": title,
                    "content": content,
                    "author": author,
                    "publish_date": publish_date,
                    "url": url
                }
                
        except Exception as e:
            logger.error(f"❌ 抓取文章内容失败: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        """提取文章标题"""
        # 策略1: og:title
        og_title = soup.find('meta', property='og:title')
        if og_title and og_title.get('content'):
            return og_title['content'].strip()
        
        # 策略2: <title>标签
        title_tag = soup.find('title')
        if title_tag and title_tag.string:
            return title_tag.string.strip()
        
        # 策略3: <h1>标签
        h1_tag = soup.find('h1')
        if h1_tag and h1_tag.get_text():
            return h1_tag.get_text().strip()
        
        return None
    
    def _extract_content(self, soup: BeautifulSoup) -> Optional[str]:
        """提取文章正文内容"""
        # 尝试常见的文章内容容器
        content_selectors = [
            'article',
            '[class*="article-content"]',
            '[class*="post-content"]',
            '[class*="entry-content"]',
            '#article-content',
            '.article-body',
            '.post-body',
            '.content',
            'main article',
        ]
        
        for selector in content_selectors:
            container = soup.select_one(selector)
            if container:
                # 移除脚本和样式
                for script in container(['script', 'style', 'nav', 'header', 'footer']):
                    script.decompose()
                
                # 提取文本
                paragraphs = container.find_all('p')
                if paragraphs:
                    content = '\n\n'.join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
                    if len(content) > 200:  # 确保有足够的内容
                        return content
        
        # 降级方案：提取所有段落
        all_paragraphs = soup.find_all('p')
        if all_paragraphs:
            content = '\n\n'.join([p.get_text().strip() for p in all_paragraphs if p.get_text().strip()])
            if len(content) > 200:
                return content
        
        return None
    
    def _extract_author(self, soup: BeautifulSoup) -> Optional[str]:
        """提取作者信息"""
        # 策略1: meta标签
        author_meta = soup.find('meta', attrs={'name': 'author'})
        if author_meta and author_meta.get('content'):
            return author_meta['content'].strip()
        
        # 策略2: article中的author元素
        author_elem = soup.find('span', class_='author') or soup.find('a', class_='author')
        if author_elem and author_elem.get_text():
            return author_elem.get_text().strip()
        
        return None
    
    def _extract_publish_date(self, soup: BeautifulSoup) -> Optional[str]:
        """提取发布日期"""
        # 策略1: meta标签
        date_meta = soup.find('meta', property='article:published_time')
        if date_meta and date_meta.get('content'):
            return date_meta['content']
        
        # 策略2: time标签
        time_tag = soup.find('time')
        if time_tag and time_tag.get('datetime'):
            return time_tag['datetime']
        
        return None


def get_web_content_fetcher() -> WebContentFetcher:
    """获取网页内容抓取服务实例"""
    return WebContentFetcher()
