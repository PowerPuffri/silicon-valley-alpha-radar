"""
OpenAI 博客详细数据收集
使用 jina 读取文章列表，然后逐个读取文章详细内容
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
    使用 jina 读取 URL

    Args:
        url: 要读取的 URL
        timeout: 超时时间（秒）

    Returns:
        解析后的数据
    """
    try:
        print(f"   📡 jina read {url}")

        # 调用 jina
        result = subprocess.run(
            ['jina', url],
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


def extract_article_links(blog_content: str) -> List[str]:
    """
    从博客主页内容中提取文章链接

    Args:
        blog_content: 博客主页内容（markdown)

    Returns:
        文章链接列表
    """
    print(f"   🔍 提取文章链接...")

    # 查找所有 openai.com/index/ 开头的链接
    pattern = r'https://openai\.com/index/[^/\)\]]*'
    links = re.findall(pattern, blog_content)

    # 去重
    unique_links = list(set(links))

    print(f"      ✅ 找到 {len(unique_links)} 个唯一链接")

    # 限制数量（只取最近 10 篇）
    return unique_links[:10]


def extract_article_details(article_url: str, article_content: str) -> Dict:
    """
    从文章内容中提取详细信息

    Args:
        article_url: 文章 URL
        article_content: 文章内容（markdown）

    Returns:
        文章详细信息
    """
    # 简化版本：从内容中提取前几行
    lines = article_content.split('\n')

    title = article_url.split('/')[-2]  # 从 URL 中提取标题
    description = ''

    # 尝试找到第一段有意义的文本
    for line in lines[:20]:
        line = line.strip()

        # 跳过空行和链接
        if not line or line.startswith('http') or line.startswith('['):
            continue

        # 跳过特殊字符
        if len(line) < 10:
            continue

        # 找到第一段有意义的文本
        description = line
        break

    return {
        'title': title,
        'description': description[:300],
        'url': article_url
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
    print("   URL: https://openai.com/blog")

    articles = []

    # 1. 读取博客主页
    print(f"\n   📡 步骤 1/3: 读取博客主页...")
    blog_data = jina_read_url("https://openai.com/blog")

    if not blog_data or not blog_data.get('success'):
        print("      ❌ 读取博客主页失败")
        return []

    blog_content = blog_data['content']

    # 2. 提取文章链接
    print(f"\n   🔍 步骤 2/3: 提取文章链接...")
    article_urls = extract_article_links(blog_content)

    if not article_urls:
        print("      ❌ 没有找到文章链接")
        return []

    # 3. 读取每篇文章的详细内容
    print(f"\n   📡 步骤 3/3: 读取文章详细内容...")
    print(f"      需要读取: {len(article_urls)} 篇文章")

    for i, article_url in enumerate(article_urls[:10]):  # 限制 10 篇
        print(f"\n      [{i+1}/{len(article_urls)}] {article_url.split('/')[-2]}...")

        # 读取文章页面
        article_data = jina_read_url(article_url, timeout=10)

        if article_data and article_data.get('success'):
            article_content = article_data['content']

            # 提取详细信息
            details = extract_article_details(article_url, article_content)

            # 转换为统一格式
            article = {
                'id': f"openai_blog_{hash(article_url)}",
                'source_type': 'official_blog',
                'source': "OpenAI Blog",
                'activity_type': 'blog_post',
                'title': details['title'],
                'description': details['description'],
                'author': 'OpenAI',
                'url': details['url'],
                'score': 0,
                'comments': 0,
                'timestamp': datetime.now().isoformat(),
                'company': 'OpenAI',
                'priority': 'P0',
                'priority_score': 0  # 稍后计算
            }

            articles.append(article)
            print(f"         ✅ 文章: {details['title'][:40]}...")

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
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
        except Exception as e:
            print(f"      ⚠️  保存文章失败: {e}")

    conn.commit()
    conn.close()

    print(f"   ✅ 已保存 {saved_count} 条文章到数据库")


def main():
    """主程序"""
    print("\n" + "=" * 80)
    print("🚀 Silicon Valley Alpha Radar - 收集 OpenAI 博客文章")
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

    print(f"\n🔥 高优先级文章 (Top 10):")
    for i, article in enumerate(prioritized[:10], 1):
        score = article.get('priority_score', 0)
        title = article.get('title', '')

        print(f"\n   [{i}] 优先级: {score}")
        print(f"      🏢 OpenAI Blog")
        print(f"      📄 {title}...")

    # 完成
    print("\n" + "=" * 80)
    print("✅ OpenAI 博客文章收集完成！")
    print("=" * 80)
    print(f"\n📁 数据库: storage/data/unified_activities.db")
    print(f"📊 总文章数: {len(articles)}")
    print(f"🔴 高优先级: {len([a for a in articles if a.get('priority_score', 0) >= 90])}")
    print(f"🟠 中优先级: {len([a for a in articles if 50 <= a.get('priority_score', 0) < 90])}")
    print(f"🟡 低优先级: {len([a for a in articles if a.get('priority_score', 0) < 50])}")
    print(f"\n💡 说明:")
    print(f"   • 文章来自 OpenAI 博客（官方博客）")
    print(f"   • 每篇都使用 jina 读取详细内容")
    print(f"   • 所有文章都可追溯到原始链接")
    print(f"   • 优先级已计算并排序")


if __name__ == "__main__":
    main()
