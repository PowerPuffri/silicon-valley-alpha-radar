"""
使用正确格式的 jina read 命令收集 OpenAI 博客
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


def jina_read_correct(url: str, timeout: int = 30) -> Dict:
    """
    使用正确的 jina read --url 命令

    Args:
        url: 要读取的 URL
        timeout: 超时时间（秒）

    Returns:
        解析后的数据
    """
    try:
        print(f"   📡 jina read --url '{url}'")

        # 使用正确的命令格式：jina read --url
        result = subprocess.run(
            ['jina', 'read', '--url', url],
            capture_output=True,
            text=True,
            timeout=timeout
        )

        if result.returncode != 0:
            print(f"      ❌ jina read 失败: {result.stderr[:200]}")
            return None

        # 返回数据
        return {
            'url': url,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'success': True
        }

    except subprocess.TimeoutExpired:
        print(f"      ❌ 超时: {timeout} 秒")
        return None
    except Exception as e:
        print(f"      ❌ jina read 错误: {e}")
        return None


def extract_openai_blog_links_v2(markdown_content: str) -> List[str]:
    """
    尝试多种方式提取 OpenAI 博客链接

    Args:
        markdown_content: 博客主页内容（markdown)

    Returns:
        文章链接列表
    """
    print(f"   🔍 提取 OpenAI 博客文章链接（多种方式）...")

    articles = []

    # 方法 1: 匹配 markdown 链接格式 [text](url)
    # 主人给的格式：[文章标题 类型 日期](https://openai.com/index/文章slug/)
    md_links = re.findall(r'\[([^\]]+)\]\((https://openai\.com/index/[^\)]+)\)', markdown_content)
    articles.extend(md_links)
    print(f"      方法 1 (Markdown 链接): 找到 {len(md_links)} 个")

    # 方法 2: 匹配直接的链接
    direct_links = re.findall(r'https://openai\.com/index/[^\s\)]+', markdown_content)
    articles.extend(direct_links)
    print(f"      方法 2 (直接链接): 找到 {len(direct_links)} 个")

    # 去重
    unique_articles = list(set(articles))

    print(f"      ✅ 总计 {len(unique_articles)} 个唯一链接")

    return unique_articles[:10]  # 限制最近 10 篇


def collect_article_details_v2(article_url: str) -> Dict:
    """
    收集文章详细内容（使用正确的 jina read 命令）

    Args:
        article_url: 文章 URL

    Returns:
        文章详细信息
    """
    print(f"\n   📡 收集文章: {article_url}...")

    # 读取文章页面
    article_data = jina_read_correct(article_url, timeout=15)

    if not article_data or not article_data.get('success'):
        print(f"      ❌ 读取文章失败")
        return None

    content = article_data['stdout']

    # 从 URL 中提取 slug
    url_parts = article_url.split('/')
    article_slug = url_parts[-1]

    # 尝试提取标题和描述
    lines = content.split('\n')

    title = article_slug
    description = ''

    # 查找标题（可能在前几行）
    for line in lines[:20]:
        line = line.strip()

        # 跳过特殊行
        if not line or line.startswith('[') or line.startswith('*') or line.startswith('#'):
            continue

        # 跳过链接
        if line.startswith('http') or line.startswith('https'):
            continue

        # 如果行比较长且有内容，可能是标题
        if len(line) > 5 and len(line) < 100:
            title = line
            break

    description = content[:500].replace('\n', ' ').strip()

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
            article['priority_score'] = calculate_priority(article)

            cursor.execute('''
                INSERT OR REPLACE INTO activities
                (id, source_type, source, activity_type, title, description, author, url,
                 score, comments, timestamp, priority_score, company, priority, collected_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
    print("🚀 Silicon Valley Alpha Radar - 使用正确的 jina 命令收集 OpenAI 博客")
    print("=" * 80)

    # 1. 读取 OpenAI 博客主页
    print("\n📡 步骤 1/3: 读取 OpenAI 博客主页...")
    blog_result = jina_read_correct("https://openai.com/blog")

    if not blog_result or not blog_result.get('success'):
        print("❌ 读取博客主页失败")
        return

    blog_content = blog_result['stdout']
    print(f"   ✅ 读取到 {len(blog_content)} 字符的 markdown")

    # 2. 提取文章链接
    print("\n🔍 步骤 2/3: 提取文章链接...")
    article_urls = extract_openai_blog_links_v2(blog_content)

    if not article_urls:
        print("❌ 没有找到文章链接")
        return

    print(f"   ✅ 提取了 {len(article_urls)} 个文章链接")

    # 3. 读取每篇文章的详细内容
    print(f"\n📡 步骤 3/3: 读取文章详细内容...")
    articles = []

    for i, article_url in enumerate(article_urls):
        print(f"\n   [{i+1}/{len(article_urls)}] 开始...")

        article = collect_article_details_v2(article_url)

        if article:
            articles.append(article)

        # 延迟一下
        import time
        time.sleep(1)

    print(f"\n   ✅ 成功收集 {len(articles)} 篇文章")

    # 保存到数据库
    save_to_database(articles)

    # 显示统计
    print(f"\n📊 数据统计:")
    print(f"   总文章数: {len(articles)}")

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


if __name__ == "__main__":
    main()
