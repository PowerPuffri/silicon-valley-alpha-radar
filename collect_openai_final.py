#!/usr/bin/env python3
"""
OpenAI 博客完整收集脚本（最终版）
使用正确的 jina 命令格式
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


def jina_read(url: str, timeout: int = 30) -> Dict:
    """
    使用 jina 读取 URL（正确的命令格式）

    正确的命令是：jina "URL"
    不是：jina read --url "URL"
    """
    try:
        print(f"   📡 jina '{url}'")

        # 使用正确的命令格式
        result = subprocess.run(
            ['jina', url],
            capture_output=True,
            text=True,
            timeout=timeout
        )

        if result.returncode != 0:
            print(f"      ❌ 失败: {result.stderr[:200]}")
            return None

        # 解析 JSON
        try:
            data = json.loads(result.stdout)
            return data
        except json.JSONDecodeError:
            # 可能是纯 markdown
            return {
                'url': url,
                'content': result.stdout,
                'success': True
            }

    except subprocess.TimeoutExpired:
        print(f"      ❌ 超时")
        return None
    except Exception as e:
        print(f"      ❌ 错误: {e}")
        return None


def extract_article_links(blog_data: Dict) -> List[str]:
    """
    从博客数据中提取文章链接

    主人给的格式：[文章标题 类型 日期](https://openai.com/index/文章slug/)
    """
    print(f"   🔍 提取文章链接...")

    if not blog_data:
        return []

    content = blog_data.get('data', {}).get('content', '')
    if not content:
        return []

    # 使用主人给的格式
    pattern = r'\[([^\]]+)\]\((https://openai\.com/index/[^\)]+)\)'
    links = re.findall(pattern, content)

    print(f"   ✅ 找到 {len(links)} 个链接")

    return links[:10]


def collect_article_details(article_url: str) -> Dict:
    """
    收集文章详细内容
    """
    print(f"\n   📡 收集: {article_url}")

    # 读取文章
    article_data = jina_read(article_url, timeout=15)

    if not article_data:
        return None

    # 提取内容
    content = article_data.get('data', {}).get('content', article_data.get('content', ''))

    # 从 URL 中提取标题
    url_parts = article_url.split('/')
    slug = url_parts[-1] if len(url_parts) > 1 else article_url

    # 从内容中提取描述
    lines = content.split('\n')
    description = ''
    for line in lines[:10]:
        line = line.strip()
        if len(line) > 20 and not line.startswith('#'):
            description = line
            break

    return {
        'id': f"openai_{hash(article_url)}",
        'source_type': 'official_blog',
        'source': "OpenAI Blog",
        'activity_type': 'blog_post',
        'title': slug.replace('-', ' ').title(),
        'description': description[:300],
        'author': 'OpenAI',
        'url': article_url,
        'score': 0,
        'comments': 0,
        'timestamp': datetime.now().isoformat(),
        'company': 'OpenAI',
        'priority': 'P0',
        'priority_score': 0
    }


def save_to_database(articles: List[Dict]) -> int:
    """
    保存到数据库
    """
    print(f"\n💾 保存到数据库...")

    conn = sqlite3.connect("storage/data/unified_activities.db")
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
    cursor.execute('DELETE FROM activities')

    saved = 0
    for article in articles:
        article['priority_score'] = calculate_priority(article)

        try:
            cursor.execute('''
                INSERT OR REPLACE INTO activities
                (id, source_type, source, activity_type, title, description, author, url,
                 score, comments, timestamp, priority_score, company, priority, collected_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                article['id'],
                article['source_type'],
                article['source'],
                article['activity_type'],
                article['title'],
                article['description'],
                article['author'],
                article['url'],
                article['score'],
                article['comments'],
                article['timestamp'],
                article['priority_score'],
                article['company'],
                article['priority'],
                datetime.now().isoformat()
            ))
            saved += 1
            print(f"   ✅ {article['title'][:40]}...")
        except Exception as e:
            print(f"   ⚠️  保存失败: {e}")

    conn.commit()
    conn.close()

    print(f"✅ 已保存 {saved} 条")

    return saved


def main():
    """主程序"""
    print("\n" + "=" * 80)
    print("🚀 Silicon Valley Alpha Radar - OpenAI 博客收集")
    print("=" * 80)

    # 1. 读取博客主页
    print(f"\n📡 步骤 1/4: 读取 OpenAI 博客主页")
    blog_data = jina_read("https://openai.com/blog")

    if not blog_data:
        print("\n❌ 读取失败")
        return

    print("✅ 读取成功")

    # 2. 提取文章链接
    print(f"\n🔍 步骤 2/4: 提取文章链接")
    links = extract_article_links(blog_data)

    if not links:
        print("\n❌ 没有找到链接")
        return

    print(f"✅ 找到 {len(links)} 个链接")

    # 3. 收集文章详细内容
    print(f"\n📡 步骤 3/4: 收集文章内容 ({len(links)} 篇）")
    articles = []

    for i, link in enumerate(links):
        print(f"\n  [{i+1}/{len(links)}] {link}")

        article = collect_article_details(link)

        if article:
            articles.append(article)

        # 延迟
        import time
        time.sleep(1)

    print(f"\n✅ 成功收集 {len(articles)} 篇文章")

    # 4. 保存到数据库
    print(f"\n💾 步骤 4/4: 保存到数据库")
    saved = save_to_database(articles)

    # 统计
    prioritized = sorted(articles, key=lambda x: x['priority_score'], reverse=True)
    high = len([a for a in prioritized if a['priority_score'] >= 100])
    medium = len([a for a in prioritized if 50 <= a['priority_score'] < 100])
    low = len([a for a in prioritized if a['priority_score'] < 50])

    print(f"\n📊 统计:")
    print(f"   总数: {len(articles)}")
    print(f"   🔴 高 (>=100): {high}")
    print(f"   🟠 中 (50-99): {medium}")
    print(f"   🟡 低 (<50): {low}")

    print(f"\n🔥 Top 10:")
    for i, article in enumerate(prioritized[:10], 1):
        score = article['priority_score']
        title = article['title']
        url = article['url']

        print(f"\n  [{i}] {score} - {title}")
        print(f"      {url}")

    # 完成
    print("\n" + "=" * 80)
    print("✅ 完成！")
    print("=" * 80)
    print(f"\n📁 数据库: storage/data/unified_activities.db")
    print(f"📊 文章数: {len(articles)}")
    print(f"🔴 高优先级: {high}")


if __name__ == "__main__":
    main()
