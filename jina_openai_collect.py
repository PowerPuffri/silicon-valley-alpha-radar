"""
正确的 OpenAI 博客链接提取和收集脚本
"""

import os
import sys
import subprocess
import json
import re
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict

# 添加项目根目录到 Python 路径
project_root = '/Users/zhipu_glm/.openclaw/workspace/silicon-valley-alpha-radar'
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'config'))

from data_sources_config import calculate_priority


def jina_read_url(url: str, timeout: int = 30) -> Dict:
    """
    使用 jina read 读取 URL

    Args:
        url: 要读取的 URL
        timeout: 超时时间（秒）

    Returns:
        解析后的数据
    """
    try:
        print(f"   📡 jina read --url '{url}'")

        # 调用 jina
        result = subprocess.run(
            ['jina', 'read', '--url', url],
            capture_output=True,
            text=True,
            timeout=timeout
        )

        if result.returncode != 0:
            print(f"      ❌ jina read 失败: {result.stderr[:200]}")
            return None

        # 返回 JSON 数据
        content = result.stdout

        return {
            'url': url,
            'content': content,
            'success': True
        }

    except subprocess.TimeoutExpired:
        print(f"      ❌ 超时: {timeout} 秒")
        return None
    except Exception as e:
        print(f"      ❌ jina read 错误: {e}")
        return None


def extract_openai_links_correct(markdown_content: str) -> List[str]:
    """
    使用正确的正则表达式提取 OpenAI 博客文章链接

    Args:
        markdown_content: 博客主页内容（markdown)

    Returns:
        文章链接列表
    """
    print(f"   🔍 提取 OpenAI 博客文章链接（正确格式）...")

    # 正确的正则：[文章标题 类型 日期](https://openai.com/index/文章slug/)
    pattern = r'\[[^\]]+\]\((https://openai\.com/index/[^\)]+)\)'
    links = re.findall(pattern, markdown_content)

    print(f"   ✅ 找到 {len(links)} 个文章链接")

    return links


def collect_article_details(article_url: str) -> Dict:
    """
    收集文章详细内容

    Args:
        article_url: 文章 URL

    Returns:
        文章详细信息
    """
    print(f"\n   📡 收集文章: {article_url}...")

    # 从 URL 中提取文章 slug
    url_parts = article_url.split('/')
    article_slug = url_parts[-1]  # 最后一部分

    # 读取文章页面
    article_data = jina_read_url(article_url, timeout=15)

    if not article_data or not article_data.get('success'):
        print(f"      ❌ 读取文章失败")
        return None

    content = article_data['content']

    # 从内容中提取标题（简化版本：第一行）
    lines = content.split('\n')
    title = article_slug  # 先用 slug 作为标题

    # 尝试从内容中提取更详细的标题
    for line in lines[:10]:
        line = line.strip()

        # 跳过空行和特殊行
        if not line or line.startswith('[') or line.startswith('---') or line.startswith('#'):
            continue

        # 如果行比较长且不是链接，可能是标题
        if len(line) > 10 and not line.startswith('http'):
            title = line
            break

    # 提取描述（内容的前 500 字符）
    description = content[:500]

    return {
        'id': f"openai_blog_{hash(article_url)}",
        'source_type': 'official_blog',
        'source': "OpenAI Blog",
        'activity_type': 'blog_post',
        'title': title,
        'description': description,
        'author': 'OpenAI',
        'url': article_url,
        'score': 0,
        'comments': 0,
        'timestamp': datetime.now().isoformat(),
        'company': 'OpenAI',
        'priority': 'P0'
    }


def collect_openai_blog_articles(days: int = 7) -> List[Dict]:
    """
    收集 OpenAI 博客文章

    Args:
        days: 收集最近多少天的数据

    Returns:
        文章列表
    """
    print("\n📝 收集 OpenAI 博客文章...")
    print("   使用 jina-cli 读取内容")
    print("   URL: https://openai.com/blog")

    articles = []

    # 1. 读取博客主页
    print(f"\n   📡 步骤 1/3: 读取 OpenAI 博客主页...")
    blog_data = jina_read_url("https://openai.com/blog")

    if not blog_data or not blog_data.get('success'):
        print("      ❌ 读取博客主页失败")
        return []

    blog_content = blog_data['content']

    # 2. 提取文章链接
    print(f"\n   🔍 步骤 2/3: 提取文章链接...")
    article_urls = extract_openai_links_correct(blog_content)

    if not article_urls:
        print("      ❌ 没有找到文章链接")
        return []

    print(f"      ✅ 提取了 {len(article_urls)} 个文章链接")

    # 限制数量（只取最近 10 篇）
    article_urls = article_urls[:10]

    # 3. 读取每篇文章的详细内容
    print(f"\n   📡 步骤 3/3: 读取文章详细内容...")
    print(f"      需要读取: {len(article_urls)} 篇文章")

    for i, article_url in enumerate(article_urls):
        print(f"\n      [{i+1}/{len(article_urls)}] {article_url.split('/')[-1]}...")

        article = collect_article_details(article_url)

        if article:
            articles.append(article)

            # 延迟一下，避免请求过快
            import time
            time.sleep(1)

    print(f"\n   ✅ 成功收集 {len(articles)} 篇文章")

    return articles


def save_to_database(articles: List[Dict], db_path: str = "storage/data/unified_activities.db"):
    """
    保存到数据库

    Args:
        articles: 文章列表
        db_path: 数据库路径
    """
    print(f"\n💾 保存到数据库...")
    print(f"   数据库: {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS activities (
            id TEXT PRIMARY KEY,
            source_type TEXT,
            source TEXT,
            activity_type TEXT,
            title TEXT,
            description TEXT,
            author TEXT,
            url TEXT,
            score INTEGER DEFAULT 0,
            comments INTEGER DEFAULT 0,
            timestamp TEXT,
            priority_score INTEGER,
            company TEXT,
            priority TEXT,
            collected_at TEXT
        )
    ''')

    conn.commit()

    # 清空旧数据
    cursor.execute('DELETE FROM activities')
    conn.commit()

    # 计算优先级并插入
    saved_count = 0
    for article in articles:
        try:
            # 计算优先级
            article['priority_score'] = calculate_priority(article)

            cursor.execute('''
                INSERT OR REPLACE INTO activities
                (id, source_type, source, activity_type, title, description, author, url,
                 score, comments, timestamp, priority_score, company, priority, collected_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                article.get('id'),
                article.get('source_type'),
                article.get('source'),
                article.get('activity_type'),
                article.get('title'),
                article.get('description'),
                article.get('author'),
                article.get('url'),
                article.get('score', 0),
                article.get('comments', 0),
                article.get('timestamp'),
                article.get('priority_score', 0),
                article.get('company'),
                article.get('priority'),
                datetime.now().isoformat()
            ))

            saved_count += 1
            print(f"   ✅ 已保存: {article['title'][:40]}...")

        except Exception as e:
            print(f"   ⚠️  保存文章失败: {e}")

    conn.commit()
    conn.close()

    print(f"   ✅ 已保存 {saved_count} 条文章到数据库")


def main():
    """主程序"""
    print("\n" + "=" * 80)
    print("🚀 Silicon Valley Alpha Radar - 使用 jina 收集 OpenAI 博客")
    print("=" * 80)

    # 收集文章
    articles = collect_openai_blog_articles(days=7)

    if not articles:
        print("\n❌ 没有收集到任何文章")
        return

    # 保存到数据库
    save_to_database(articles)

    # 显示统计
    print(f"\n📊 数据统计:")
    print(f"   总文章数: {len(articles)}")

    # 按优先级排序
    prioritized = sorted(articles, key=lambda x: x.get('priority_score', 0), reverse=True)

    # 按优先级统计
    priorities = [a['priority_score'] for a in prioritized]
    high_priority = len([p for p in priorities if p >= 100])
    medium_priority = len([p for p in priorities if 50 <= p < 100])
    low_priority = len([p for p in priorities if p < 50])

    print(f"\n📊 按优先级:")
    print(f"   🔴 高优先级 (>=100): {high_priority}")
    print(f"   🟠 中优先级 (50-99): {medium_priority}")
    print(f"   🟡 低优先级 (<50): {low_priority}")

    # 显示前 10 个
    print(f"\n🔥 高优先级文章 (Top 10):")
    for i, article in enumerate(prioritized[:10], 1):
        score = article.get('priority_score', 0)
        title = article.get('title', '')
        url = article.get('url', '')

        print(f"\n   [{i}] 优先级: {score}")
        print(f"      🏢 OpenAI Blog")
        print(f"      📄 {title}...")
        print(f"      🔗 {url}")

    # 完成
    print("\n" + "=" * 80)
    print("✅ OpenAI 博客文章收集完成！")
    print("=" * 80)
    print(f"\n📁 数据库: storage/data/unified_activities.db")
    print(f"📊 总文章数: {len(articles)}")
    print(f"🔴 高优先级: {high_priority}")
    print(f"🟠 中优先级: {medium_priority}")
    print(f"🟡 低优先级: {low_priority}")


if __name__ == "__main__":
    main()
