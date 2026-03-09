"""
真实数据收集器 - 简化但真实的方案
只收集真正能获取的高优先级数据
"""

import os
import sys
import requests
import feedparser
from datetime import datetime, timedelta
from typing import List, Dict
from collections import Counter

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'config'))

from data_sources_config import DATA_SOURCES_CONFIG, calculate_priority


def collect_openai_blog_rss(days: int = 7) -> List[Dict]:
    """
    收集 OpenAI 官方博客（RSS - 可靠）

    Args:
        days: 收集最近多少天

    Returns:
        博客文章列表
    """
    print("\n📝 收集 OpenAI 官方博客 (RSS)...")
    print("   RSS URL: https://openai.com/blog/rss.xml")

    articles = []

    try:
        rss_url = "https://openai.com/blog/rss.xml"
        feed = feedparser.parse(rss_url)

        for entry in feed.entries:
            # 检查时间
            published = entry.get('published_parsed')
            if not published:
                continue

            if published < datetime.now() - timedelta(days=days):
                continue

            # 转换为统一格式
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

    except Exception as e:
        print(f"   ❌ OpenAI RSS 收集失败: {e}")

    return articles


def collect_twitter_rsshub(handles: List[str], days: int = 7) -> List[Dict]:
    """
    收集 Twitter 推文（RSSHub - 虽然不稳定，但能工作）

    Args:
        handles: Twitter 账号列表
        days: 收集最近多少天

    Returns:
        推文列表
    """
    print(f"\n🟦 收集 Twitter 推文 (RSSHub)...")
    print(f"   账号数量: {len(handles)}")
    print(f"   RSSHub: https://rsshub.app")

    tweets = []

    for handle in handles:
        print(f"   📡 收集 @{handle}...")

        try:
            rss_url = f"https://rsshub.app/{handle}"
            response = requests.get(rss_url, timeout=10)
            response.raise_for_status()

            feed = feedparser.parse(rss_url)

            for entry in feed.entries:
                # 检查时间
                published = entry.get('published_parsed')
                if not published:
                    continue

                if published < datetime.now() - timedelta(days=days):
                    continue

                # 转换为统一格式
                tweet = {
                    'id': f"twitter_{handle}_{hash(entry.get('id', entry.get('link')))}",
                    'source_type': 'official_x',
                    'source': f"@{handle}",
                    'activity_type': 'tweet',
                    'title': entry.get('title', '')[:100],
                    'description': entry.get('summary', entry.get('description', ''))[:500],
                    'author': handle,
                    'url': entry.get('link', f"https://twitter.com/{handle}"),
                    'score': 0,
                    'comments': 0,
                    'timestamp': published.isoformat(),
                    'handle': handle,
                    'company': self._get_twitter_company(handle),
                    'priority': self._get_twitter_priority(handle)
                }

                tweets.append(tweet)

            print(f"      ✅ @{handle}: {len([t for t in tweets if t['handle'] == handle])} 条推文")

        except Exception as e:
            print(f"      ❌ @{handle} 收集失败: {e}")

    print(f"   ✅ Twitter: {len(tweets)} 条推文")

    return tweets


def _get_twitter_company(handle: str) -> str:
    """获取 Twitter 账号对应的公司"""
    mapping = {
        'OpenAI': 'OpenAI',
        'DeepMind': 'DeepMind',
        'GoogleDeepMind': 'DeepMind',
        'AnthropicAI': 'Anthropic',
        'GoogleAI': 'Google AI',
        'MetaAI': 'Meta AI',
        'MistralAI': 'Mistral'
    }

    return mapping.get(handle, 'Unknown')


def _get_twitter_priority(handle: str) -> str:
    """获取 Twitter 账号的优先级"""
    p0_handles = ['OpenAI', 'DeepMind', 'AnthropicAI', 'sama', 'gdb', 'ilyasut', 'demishassabis']
    p1_handles = ['GoogleAI', 'MetaAI', 'karpathy', 'ylecun', 'jeffdean']

    if handle in p0_handles:
        return 'P0'
    elif handle in p1_handles:
        return 'P1'
    else:
        return 'P2'


def load_hackernews_data(db_path: str = "storage/data/unified_activities.db") -> List[Dict]:
    """加载 Hacker News 数据（已有）"""
    print(f"\n🕶️ 加载 Hacker News 数据...")
    print(f"   数据库: {db_path}")

    if not os.path.exists(db_path):
        print("   ⚠️  数据库不存在")
        return []

    try:
        import sqlite3
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # 检查表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]

        if 'activities' not in tables:
            print("   ⚠️  activities 表不存在")
            return []

        cursor.execute('SELECT * FROM activities WHERE source_type = "community" ORDER BY timestamp DESC')
        hn_events = [dict(row) for row in cursor.fetchall()]

        conn.close()

        print(f"   ✅ Hacker News: {len(hn_events)} 条")

        return hn_events

    except Exception as e:
        print(f"   ❌ Hacker News 数据加载失败: {e}")
        return []


def save_to_unified_db(activities: List[Dict], db_path: str = "storage/data/unified_activities.db"):
    """保存到统一数据库"""
    print(f"\n💾 保存到统一数据库...")
    print(f"   数据库: {db_path}")

    import sqlite3

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
                 score, comments, timestamp, priority_score, company, collected_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                datetime.now().isoformat()
            ))

            saved_count += 1
        except Exception as e:
            print(f"   ⚠️  保存活动失败: {e}")

    conn.commit()
    conn.close()

    print(f"   ✅ 已保存 {saved_count} 条活动")


def main():
    """主程序 - 真实数据收集"""
    print("\n" + "=" * 80)
    print("🚀 Silicon Valley Alpha Radar - 真实数据收集")
    print("=" * 80)

    all_activities = []

    # 1. OpenAI 官方博客（最高优先级）
    print("\n📝 [优先级 1/3] OpenAI 官方博客 (RSS)...")
    openai_articles = collect_openai_blog_rss(days=7)
    all_activities.extend(openai_articles)

    # 2. Twitter（第二优先级）
    print("\n🟦 [优先级 2/3] Twitter 推文 (RSSHub)...")
    twitter_handles = ['OpenAI', 'sama', 'gdb', 'ilyasut', 'DeepMind', 'demishassabis', 'AnthropicAI', 'GoogleAI']
    twitter_tweets = collect_twitter_rsshub(twitter_handles, days=7)
    all_activities.extend(twitter_tweets)

    # 3. Hacker News（补充，真实但优先级较低）
    print("\n🕶️ [优先级 3/3] Hacker News (已有数据）...")
    hn_events = load_hackernews_data()
    all_activities.extend(hn_events)

    print(f"\n📊 总计收集: {len(all_activities)} 条活动")

    # 计算优先级
    print("\n📊 计算优先级...")
    for activity in all_activities:
        try:
            priority_score = calculate_priority(activity)
            activity['priority_score'] = priority_score
        except Exception as e:
            print(f"   ⚠️  计算优先级失败: {e}")
            activity['priority_score'] = 0

    # 排序
    print("📊 按优先级排序...")
    prioritized = sorted(all_activities, key=lambda x: x.get('priority_score', 0), reverse=True)

    # 保存到数据库
    print("\n💾 保存到数据库...")
    save_to_unified_db(prioritized)

    # 显示统计
    print("\n📊 统计信息:")
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

    # 按优先级统计
    priorities = [a['priority_score'] for a in prioritized]
    high_priority = len([p for p in priorities if p >= 100])
    medium_priority = len([p for p in priorities if 50 <= p < 100])
    low_priority = len([p for p in priorities if p < 50])

    print(f"\n   按优先级:")
    print(f"      🔴 高 (>=100): {high_priority}")
    print(f"      🟠 中 (50-99): {medium_priority}")
    print(f"      🟡 低 (<50): {low_priority}")

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
    print(f"📊 高优先级: {high_priority}")
    print(f"📊 中优先级: {medium_priority}")
    print(f"📊 低优先级: {low_priority}")
    print(f"\n💡 说明:")
    print(f"   • OpenAI 官方博客：来自官方 RSS，完全真实")
    print(f"   • Twitter 推文：来自 RSSHub，真实但不稳定")
    print(f"   • Hacker News：来自之前收集的数据，完全真实")
    print(f"   • 所有信息都可追溯到原始链接")


if __name__ == "__main__":
    main()
