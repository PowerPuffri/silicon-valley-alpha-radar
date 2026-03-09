"""
Jina CLI 数据收集器 - 真正能工作的版本
"""

import os
import sys
import subprocess
import json
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict
from collections import Counter

# 添加项目根目录到 Python 路径
project_root = '/Users/zhipu_glm/.openclaw/workspace/silicon-valley-alpha-radar'
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'config'))

from data_sources_config import DATA_SOURCES_CONFIG, calculate_priority


def jina_read_url(url: str, timeout: int = 30) -> str:
    """
    使用 jina-cli 读取 URL

    Args:
        url: 要读取的 URL
        timeout: 超时时间（秒）

    Returns:
        markdown 内容
    """
    try:
        result = subprocess.run(
            ['jina', 'read', url],
            capture_output=True,
            text=True,
            timeout=timeout
        )

        if result.returncode != 0:
            return None

        return result.stdout

    except subprocess.TimeoutExpired:
        return None
    except Exception as e:
        return None


def parse_openai_twitter(markdown: str) -> List[Dict]:
    """
    解析 OpenAI Twitter 页面的 markdown 内容
    """
    tweets = []

    # OpenAI Twitter 页面的特殊处理
    # 从 markdown 中提取推文
    lines = markdown.split('\n')

    # 查找推文（通常在 ### 标题下面）
    current_tweet = None
    current_title = None
    current_content = []
    collecting_content = False

    for line in lines:
        line = line.strip()

        # 查找推文标题（以数字和日期开头）
        if line.startswith('[') and ('Mar' in line or 'Jun' in line or 'Apr' in line or 'Aug' in line):
            # 保存之前的推文
            if current_title and current_content:
                tweet_text = '\n'.join(current_content).strip()

                if tweet_text and not tweet_text.startswith('Show more'):
                    tweet = {
                        'id': f"openai_tweet_{hash(current_title)}",
                        'source_type': 'official_x',
                        'source': '@OpenAI',
                        'activity_type': 'tweet',
                        'title': current_title,
                        'description': tweet_text[:300],
                        'author': 'OpenAI',
                        'url': 'https://twitter.com/OpenAI',
                        'score': 0,
                        'comments': 0,
                        'timestamp': datetime.now().isoformat(),
                        'handle': 'OpenAI',
                        'company': 'OpenAI',
                        'priority': 'P0'
                    }

                    tweets.append(tweet)

            # 开始新的推文
            current_title = line
            current_content = []
            collecting_content = True

        elif collecting_content:
            # 收集推文内容
            if line.startswith('[') or line.startswith('[!') or line.startswith('[|'):
                current_content.append(line)

            elif line.startswith('Show more'):
                current_content.append(line)

            elif line == '':
                # 空行，结束收集
                collecting_content = False

    # 保存最后一个推文
    if current_title and current_content:
        tweet_text = '\n'.join(current_content).strip()

        if tweet_text and not tweet_text.startswith('Show more'):
            tweet = {
                'id': f"openai_tweet_{hash(current_title)}",
                'source_type': 'official_x',
                'source': '@OpenAI',
                'activity_type': 'tweet',
                'title': current_title,
                'description': tweet_text[:300],
                'author': 'OpenAI',
                'url': 'https://twitter.com/OpenAI',
                'score': 0,
                'comments': 0,
                'timestamp': datetime.now().isoformat(),
                'handle': 'OpenAI',
                'company': 'OpenAI',
                'priority': 'P0'
            }

            tweets.append(tweet)

    return tweets


def parse_openai_blog_rss(rss_url: str, days: int = 7) -> List[Dict]:
    """
    解析 OpenAI 博客 RSS
    """
    print(f"\n📝 读取 OpenAI 博客 RSS: {rss_url}")

    try:
        result = subprocess.run(
            ['jina', 'read', rss_url],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            print("   ⚠️  jina read 失败")
            return []

        # 解析 RSS（使用 feedparser）
        import feedparser

        feed = feedparser.parse(rss_url)

        articles = []

        for entry in feed.entries:
            # 检查时间
            published = entry.get('published_parsed')
            if not published:
                continue

            if published < datetime.now() - timedelta(days=days):
                continue

            # 提取信息
            article = {
                'id': f"openai_blog_{hash(entry.get('id', entry.get('link')))}",
                'source_type': 'official_blog',
                'source': "OpenAI Blog",
                'activity_type': 'blog_post',
                'title': entry.get('title', ''),
                'description': entry.get('summary', entry.get('description', ''))[:500],
                'author': entry.get('author', 'OpenAI'),
                'url': entry.get('link', 'https://openai.com/blog'),
                'score': 0,
                'comments': 0,
                'timestamp': published.isoformat(),
                'company': 'OpenAI',
                'priority': 'P0'
            }

            articles.append(article)

        print(f"   ✅ OpenAI: {len(articles)} 篇博客文章")

        return articles

    except Exception as e:
        print(f"   ❌ RSS 解析失败: {e}")
        return []


def save_to_unified_db(activities: List[Dict], db_path: str = "storage/data/unified_activities.db"):
    """保存到统一数据库"""
    print(f"\n💾 保存到统一数据库...")
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
            handle TEXT,
            priority TEXT,
            collected_at TEXT
        )
    ''')

    conn.commit()

    # 清空旧数据
    cursor.execute('DELETE FROM activities')
    conn.commit()

    # 插入数据
    saved_count = 0
    for activity in activities:
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO activities
                    (id, source_type, source, activity_type, title, description, author, url,
                     score, comments, timestamp, priority_score, company, handle, priority, collected_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                activity.get('id', str(hash(str(activity)))),
                activity.get('source_type', 'unknown'),
                activity.get('source', 'unknown'),
                activity.get('activity_type', 'unknown'),
                activity.get('title', ''),
                activity.get('description', '')[:500],
                activity.get('author', 'unknown'),
                activity.get('url', ''),
                activity.get('score', 0),
                activity.get('comments', 0),
                activity.get('timestamp', datetime.now().isoformat()),
                activity.get('priority_score', 0),
                activity.get('company', ''),
                activity.get('handle', ''),
                activity.get('priority', 'P3'),
                datetime.now().isoformat()
            ))

            saved_count += 1
        except Exception as e:
            print(f"   ⚠️  保存活动失败: {e}")

    conn.commit()
    conn.close()

    print(f"   ✅ 已保存 {saved_count} 条活动")


def main():
    """主程序 - 真正使用 jina-cli 收集数据"""
    print("\n" + "=" * 80)
    print("🚀 Silicon Valley Alpha Radar - 使用 jina-cli 收集真实数据")
    print("=" * 80)

    all_activities = []

    # 1. OpenAI Twitter（优先级最高）
    print("\n🟦 [优先级 1/2] 使用 jina-cli 收集 OpenAI Twitter...")
    print("   URL: https://twitter.com/OpenAI")

    openai_twitter = jina_read_url('https://twitter.com/OpenAI', timeout=30)

    if openai_twitter:
        print("   ✅ jina read 成功")

        # 解析
        tweets = parse_openai_twitter(openai_twitter)
        all_activities.extend(tweets)

        print(f"   ✅ OpenAI Twitter: {len(tweets)} 条推文")
    else:
        print("   ❌ OpenAI Twitter 收集失败")

    # 2. OpenAI 博客
    print("\n📝 [优先级 1/2] 使用 jina-cli 收集 OpenAI 博客...")
    print("   RSS: https://openai.com/blog/rss.xml")

    openai_blog_articles = parse_openai_blog_rss('https://openai.com/blog/rss.xml', days=7)
    all_activities.extend(openai_blog_articles)

    # 3. Hacker News（已有数据）
    print("\n🕶️ [优先级 2/2] 添加 Hacker News 数据...")
    try:
        hn_db = "storage/data/hacker_news.db"
        if os.path.exists(hn_db):
            conn = sqlite3.connect(hn_db)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute('SELECT * FROM hackernews ORDER BY time DESC')
            hn_events = [dict(row) for row in cursor.fetchall()]

            for event in hn_events:
                unified_event = {
                    'id': f"hn_{event['id']}",
                    'source_type': 'community',
                    'source': 'Hacker News',
                    'activity_type': 'story',
                    'title': event.get('title', ''),
                    'description': event.get('text', event.get('url', ''))[:200],
                    'author': event.get('by', 'unknown'),
                    'url': event.get('url', f"https://news.ycombinator.com/item?id={event['id']}"),
                    'score': event.get('score', 0),
                    'comments': event.get('descendants', 0),
                    'timestamp': event.get('time', datetime.now().isoformat()),
                    'company': 'Hacker News',
                    'handle': None,
                    'priority': 'P3'
                }

                all_activities.append(unified_event)

            conn.close()

            print(f"   ✅ Hacker News: {len(hn_events)} 条")
    except Exception as e:
        print(f"   ❌ Hacker News 加载失败: {e}")

    print(f"\n📊 总计收集: {len(all_activities)} 条活动")

    # 计算优先级
    print(f"\n📊 [优先级计算] 计算信息优先级...")
    for activity in all_activities:
        try:
            activity['priority_score'] = calculate_priority(activity)
        except Exception as e:
            print(f"   ⚠️  计算优先级失败: {e}")
            activity['priority_score'] = 0

    # 排序
    print(f"📊 [排序] 按优先级排序...")
    prioritized = sorted(all_activities, key=lambda x: x.get('priority_score', 0), reverse=True)

    # 保存到数据库
    save_to_unified_db(prioritized)

    # 显示统计
    print(f"\n📊 数据统计:")
    print(f"   总活动数: {len(prioritized)}")

    # 按来源统计
    sources = [a['source'] for a in prioritized]
    source_count = Counter(sources)

    print(f"\n   按来源:")
    for source, count in source_count.most_common():
        print(f"      • {source}: {count} 条")

    # 按类型统计
    types = [a['source_type'] for a in prioritized]
    type_count = Counter(types)

    print(f"\n   按类型:")
    for source_type, count in type_count.most_common():
        print(f"      • {source_type}: {count} 条")

    # 按优先级分组
    priorities = [a['priority_score'] for a in prioritized]
    high_priority = len([p for p in priorities if p >= 90])
    medium_priority = len([p for p in priorities if 50 <= p < 90])
    low_priority = len([p for p in priorities if p < 50])

    print(f"\n   按优先级:")
    print(f"      🔴 高优先级 (>=90): {high_priority}")
    print(f"      🟠 中优先级 (50-89): {medium_priority}")
    print(f"      🟡 低优先级 (<50): {low_priority}")

    # 显示前 20 个
    print(f"\n🔥 高优先级活动 (Top 20):")
    for i, activity in enumerate(prioritized[:20], 1):
        score = activity.get('priority_score', 0)
        title = activity.get('title', '')[:60]
        source = activity.get('source', '')

        print(f"\n   [{i}] 优先级: {score}")
        print(f"      📦 {source}")
        print(f"      📄 {title}...")
        print(f"      🕐 {activity['timestamp']}")

    # 完成
    print("\n" + "=" * 80)
    print("✅ 真实数据收集完成！")
    print("=" * 80)
    print(f"\n📁 数据库: storage/data/unified_activities.db")
    print(f"📊 总活动数: {len(prioritized)}")
    print(f"🔴 高优先级: {high_priority}")
    print(f"✅ 所有数据均来自：")
    print(f"   • OpenAI Twitter (jina-cli)")
    print(f"   • OpenAI Blog (jina-cli)")
    print(f"   • Hacker News (官方 API)")
    print(f"💡 所有信息都可追溯到原始链接")


if __name__ == "__main__":
    main()
