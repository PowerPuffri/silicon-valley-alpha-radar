"""
官方博客收集器 - 收集顶级AI公司的官方博客
"""

import feedparser
import requests
from datetime import datetime, timedelta
from typing import List, Dict
import sys
import os

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'config'))

from data_sources_config import DATA_SOURCES_CONFIG


class OfficialBlogCollector:
    def __init__(self):
        """初始化官方博客收集器"""
        self.blogs = DATA_SOURCES_CONFIG["official_blogs"]
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'
        })

    def fetch_from_rss(self, blog_url: str, rss_url: str, company: str, days: int = 7) -> List[Dict]:
        """
        从 RSS Feed 收集博客文章

        Args:
            blog_url: 博客 URL
            rss_url: RSS Feed URL
            company: 公司名称
            days: 收集最近多少天

        Returns:
            文章列表
        """
        print(f"   📡 从 RSS 收集 {company} 博客...")

        if not rss_url:
            print(f"      ⚠️  {company} 没有提供 RSS URL")
            return []

        articles = []

        try:
            feed = feedparser.parse(rss_url)

            for entry in feed.entries:
                # 检查时间
                published = entry.get('published_parsed')
                if not published:
                    continue

                if published < datetime.now() - timedelta(days=days):
                    continue

                # 提取信息
                article = {
                    'id': f"blog_{company}_{hash(entry.get('id', entry.get('link')))}",
                    'source_type': 'official_blog',
                    'source': f"{company} Blog",
                    'activity_type': 'blog_post',
                    'title': entry.get('title', ''),
                    'description': entry.get('summary', entry.get('description', ''))[:500],
                    'author': entry.get('author', company),
                    'url': entry.get('link', blog_url),
                    'score': 0,  # 博客文章没有原生分数
                    'comments': 0,
                    'timestamp': published.isoformat(),
                    'company': company,
                    'priority': next((b['priority'] for b in self.blogs if b['company'] == company), 'P3')
                }

                articles.append(article)

            print(f"      ✅ 收集了 {len(articles)} 篇文章")

        except Exception as e:
            print(f"      ❌ RSS 收集失败: {e}")

        return articles

    def fetch_from_web(self, blog_url: str, company: str, days: int = 7) -> List[Dict]:
        """
        从网页爬取博客文章（备用方案）

        Args:
            blog_url: 博客 URL
            company: 公司名称
            days: 收集最近多少天

        Returns:
            文章列表
        """
        print(f"   🌐 从网页爬取 {company} 博客（备用）...")

        articles = []

        try:
            response = self.session.get(blog_url, timeout=10)
            response.raise_for_status()

            # 简单的HTML解析（使用 BeautifulSoup）
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(response.content, 'html.parser')

            # 查找博客文章链接
            # 这里需要根据每个网站的具体结构来调整
            article_links = soup.find_all('a', href=True)

            for link in article_links[:20]:  # 限制前 20 个
                href = link['href']
                if not href.startswith('http'):
                    if href.startswith('/'):
                        href = blog_url.rstrip('/') + href
                    else:
                        continue

                article = {
                    'id': f"blog_{company}_{hash(href)}",
                    'source_type': 'official_blog',
                    'source': f"{company} Blog",
                    'activity_type': 'blog_post',
                    'title': link.get_text(strip=True)[:100],
                    'description': '',
                    'author': company,
                    'url': href,
                    'score': 0,
                    'comments': 0,
                    'timestamp': datetime.now().isoformat(),
                    'company': company,
                    'priority': next((b['priority'] for b in self.blogs if b['company'] == company), 'P3')
                }

                articles.append(article)

            print(f"      ✅ 爬取了 {len(articles)} 个链接")

        except Exception as e:
            print(f"      ❌ 网页爬取失败: {e}")

        return articles

    def collect_all_blogs(self, days: int = 7) -> List[Dict]:
        """
        收集所有官方博客

        Args:
            days: 收集最近多少天

        Returns:
            所有文章列表
        """
        print("\n📡 [1/4] 收集官方博客...")
        print(f"   监控公司数量: {len(self.blogs)}")

        all_articles = []

        for blog_config in self.blogs:
            company = blog_config['company']
            rss_url = blog_config['rss_url']
            blog_url = blog_config['blog_url']

            print(f"\n   📦 {company} ({blog_config['priority']})")

            # 优先使用 RSS
            if rss_url:
                articles = self.fetch_from_rss(blog_url, rss_url, company, days)
                all_articles.extend(articles)

                # 如果 RSS 收集结果太少，尝试网页爬取
                if len(articles) < 3:
                    print(f"      ⚠️  RSS 数据较少，尝试网页爬取...")
                    web_articles = self.fetch_from_web(blog_url, company, days)
                    all_articles.extend(web_articles)
            else:
                # 没有 RSS，直接爬取网页
                articles = self.fetch_from_web(blog_url, company, days)
                all_articles.extend(articles)

        print(f"\n   ✅ 官方博客收集完成: {len(all_articles)} 篇文章")

        return all_articles


if __name__ == "__main__":
    # 测试官方博客收集器
    print("🧪 Silicon Valley Alpha Radar - 官方博客收集器测试")

    collector = OfficialBlogCollector()
    articles = collector.collect_all_blogs(days=7)

    print(f"\n📊 统计: {len(articles)} 篇文章")

    # 按公司分组
    from collections import Counter
    companies = [a['company'] for a in articles]
    company_count = Counter(companies)

    print(f"\n📊 按公司统计:")
    for company, count in company_count.most_common():
        print(f"   {company}: {count} 篇")

    # 显示前 10 篇
    print(f"\n🔥 最新 10 篇:")
    for i, article in enumerate(articles[:10], 1):
        print(f"\n   [{i}] {article['title'][:60]}...")
        print(f"       📦 {article['source']}")
        print(f"       🔗 {article['url']}")
        print(f"       🕐 {article['timestamp']}")
