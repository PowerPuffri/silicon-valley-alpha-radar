#!/usr/bin/env python3
"""
OpenAI 博客完整收集脚本
独立运行，完成所有步骤
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
    """
    try:
        result = subprocess.run(
            ['jina', url],
            capture_output=True,
            text=True,
            timeout=timeout
        )

        if result.returncode != 0:
            return None

        # 尝试解析 JSON
        try:
            return {
                'url': url,
                'content': result.stdout,
                'success': True
            }
        except:
            return None

    except subprocess.TimeoutExpired:
        return None
    except Exception as e:
        return None


def extract_all_links(markdown_content: str) -> List[str]:
    """
    提取所有文章链接（尝试多种格式）
    """
    links = []

    # 方法 1: 匹配 /index/xxx/
    pattern1 = r'https://openai\.com/index/[^/\)\s]*'
    links.extend(re.findall(pattern1, markdown_content))

    # 方法 2: 匹配 /xxx/
    pattern2 = r'https://openai\.com/[^/\)\s]+/'
    links.extend(re.findall(pattern2, markdown_content))

    # 去重
    unique_links = list(set(links))

    return unique_links[:10]


def extract_article_data(url: str, content: str) -> Dict:
    """
    从 URL 和内容中提取文章数据
    """
    # 从 URL 中提取 slug 作为标题
    url_parts = url.split('/')
    slug = url_parts[-1] if len(url_parts) > 1 else url

    # 从内容中提取日期
    date_match = re.search(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},\s+\d{4}', content)
    if date_match:
        date_str = date_match.group(0)
    else:
        date_str = datetime.now().strftime('%b %d, %Y')

    # 从内容中提取描述（前 300 字符）
    lines = content.split('\n')
    description = ''
    for line in lines[:20]:
        line = line.strip()
        if len(line) > 10 and not line.startswith('#') and not line.startswith('[') and not line.startswith('*'):
            description += line + ' '
            if len(description) > 300:
                break

    return {
        'title': slug,
        'description': description.strip(),
        'date': date_str,
        'url': url
    }


def collect_all_data() -> List[Dict]:
    """
    收集所有数据
    """
    articles = []

    print("\n📡 步骤 1/3: 读取 OpenAI 博客主页...")
    blog_data = jina_read_url("https://openai.com/blog")

    if not blog_data:
        print("❌ 读取博客主页失败")
        return []

    print(f"✅ 读取成功，内容长度: {len(blog_data['content'])}")

    print("\n🔍 步骤 2/3: 提取文章链接...")
    links = extract_all_links(blog_data['content'])
    print(f"✅ 找到 {len(links)} 个链接")

    if not links:
        print("❌ 没有找到链接")
        return []

    print("\n📡 步骤 3/3: 读取文章内容...")
    for i, link in enumerate(links):
        print(f"\n  [{i+1}/{len(links)}] 读取文章...")

        article_data = jina_read_url(link, timeout=10)

        if article_data:
            article_info = extract_article_data(link, article_data['content'])

            article = {
                'id': f"openai_{hash(link)}",
                'source_type': 'official_blog',
                'source': "OpenAI Blog",
                'activity_type': 'blog_post',
                'title': article_info['title'],
                'description': article_info['description'],
                'author': 'OpenAI',
                'url': article_info['url'],
                'date': article_info['date'],
                'score': 0,
                'comments': 0,
                'timestamp': datetime.now().isoformat(),
                'company': 'OpenAI',
                'priority': 'P0',
                'priority_score': 0
            }

            articles.append(article)
            print(f"    ✅ {article_info['title'][:40]}...")

    print(f"\n✅ 成功收集 {len(articles)} 篇文章")

    return articles


def save_to_database(articles: List[Dict], db_path: str = "storage/data/unified_activities.db"):
    """
    保存到数据库
    """
    print(f"\n💾 保存到数据库: {db_path}")

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
            date TEXT,
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
                 score, comments, date, timestamp, priority_score, company, priority, collected_at)
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
                article.get('date'),
                article.get('timestamp'),
                article.get('priority_score', 0),
                article.get('company'),
                article.get('priority'),
                datetime.now().isoformat()
            ))
            saved += 1
            print(f"    ✅ {article['title'][:30]}...")
        except Exception as e:
            print(f"    ⚠️  保存失败: {e}")

    conn.commit()
    conn.close()

    print(f"\n✅ 已保存 {saved} 条文章到数据库")


def print_summary(articles: List[Dict]):
    """
    打印统计摘要
    """
    print(f"\n📊 数据统计:")
    print(f"   总文章数: {len(articles)}")

    prioritized = sorted(articles, key=lambda x: x['priority_score'], 0), reverse=True)
    high = len([a for a in prioritized if a['priority_score'] >= 100])
    medium = len([a for a in prioritized if 50 <= a['priority_score'] < 100])
    low = len([a for a in prioritized if a['priority_score'] < 50])

    print(f"   🔴 高优先级 (>=100): {high}")
    print(f"   🟠 中优先级 (50-99): {medium}")
    print(f"   🟡 低优先级 (<50): {low}")

    print(f"\n🔥 高优先级文章 (Top 10):")
    for i, article in enumerate(prioritized[:10], 1):
        score = article.get('priority_score', 0)
        title = article.get('title', '')
        print(f"\n   [{i}] 优先级: {score}")
        print(f"      📄 {title}...")
        print(f"      🔗 {article['url']}")


def main():
    """主程序"""
    print("\n" + "=" * 80)
    print("🚀 Silicon Valley Alpha Radar - OpenAI 博客完整收集")
    print("=" * 80)

    # 收集数据
    articles = collect_all_data()

    if not articles:
        print("\n❌ 没有收集到数据")
        return

    # 保存到数据库
    save_to_database(articles)

    # 打印摘要
    print_summary(articles)

    # 完成
    print("\n" + "=" * 80)
    print("✅ 收集完成！")
    print("=" * 80)
    print(f"\n📁 数据库: storage/data/unified_activities.db")
    print(f"📊 文章数: {len(articles)}")
    print(f"🔴 高优先级: {len([a for a in articles if a['priority_score'] >= 100])}")


if __name__ == "__main__":
    main()
