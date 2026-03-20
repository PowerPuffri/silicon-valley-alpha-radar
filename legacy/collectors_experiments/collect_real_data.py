"""
收集真实数据并整理存储
从 Hacker News, Reddit 收集完全真实且可追溯的信息（七天前）
"""

import os
import sys
import sqlite3
import requests
from datetime import datetime, timedelta
from typing import List, Dict

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))


def collect_hacker_news_real_data(days: int = 7) -> List[Dict]:
    """
    从 Hacker News 官方 API 收集真实数据

    Args:
        days: 收集最近多少天

    Returns:
        真实的故事列表
    """
    print(f"\n🕶️ 收集 Hacker News 真实数据（最近 {days} 天）...")

    # Hacker News 官方 API
    base_url = "https://hacker-news.firebaseio.com/v0"

    stories = []

    try:
        # 获取新故事列表
        print("   📡 获取新故事列表...")
        new_stories_url = f"{base_url}/newstories.json"
        response = requests.get(new_stories_url, timeout=10)
        response.raise_for_status()

        story_ids = response.json()
        print(f"   ✅ 获取到 {len(story_ids)} 个故事 ID")

        # 获取每个故事的详细信息
        print(f"   📥 获取故事详情...")
        collected = 0
        for story_id in story_ids[:100]:  # 限制前 100 个
            try:
                story_url = f"{base_url}/item/{story_id}.json"
                story_response = requests.get(story_url, timeout=5)
                story_data = story_response.json()

                # 检查时间
                if 'time' in story_data:
                    timestamp = story_data['time']
                    story_time = datetime.fromtimestamp(timestamp)

                    # 只保留 7 天内的
                    if story_time >= datetime.now() - timedelta(days=days):
                        # 转换为统一格式
                        story = {
                            'id': story_data.get('id'),
                            'source': 'Hacker News',
                            'activity_type': 'story',
                            'title': story_data.get('title', ''),
                            'description': story_data.get('text', '') or story_data.get('url', ''),
                            'author': story_data.get('by', 'unknown'),
                            'url': story_data.get('url', f"https://news.ycombinator.com/item?id={story_data.get('id')}"),
                            'score': story_data.get('score', 0),
                            'comments': story_data.get('descendants', 0),
                            'timestamp': story_time.isoformat(),
                        }
                        stories.append(story)
                        collected += 1

                if collected % 20 == 0:
                    print(f"      已收集 {collected} 条...")

            except Exception as e:
                print(f"      ⚠️  获取故事 {story_id} 失败: {e}")

        print(f"   ✅ Hacker News 收集完成：{len(stories)} 条真实故事")

    except Exception as e:
        print(f"   ❌ Hacker News 收集失败: {e}")
        import traceback
        traceback.print_exc()

    return stories


def collect_reddit_real_data(days: int = 7) -> List[Dict]:
    """
    从 Reddit 官方 API 收集真实数据

    Args:
        days: 收集最近多少天

    Returns:
        真实的帖子列表
    """
    print(f"\n📱 收集 Reddit 真实数据（最近 {days} 天）...")

    # Reddit 子版块
    subreddits = [
        'MachineLearning',
        'artificial',
        'deeplearning',
        'ArtificialIntelligence',
        'singularity'
    ]

    posts = []

    try:
        # Reddit 官方 API（无需认证）
        for subreddit in subreddits:
            try:
                print(f"   📡 获取 r/{subreddit} 热门帖子...")

                url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit=25"
                headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()

                data = response.json()

                if 'data' in data and 'children' in data['data']:
                    for child in data['data']['children']:
                        try:
                            post_data = child['data']

                            # 检查时间
                            if 'created_utc' in post_data:
                                created_time = datetime.fromtimestamp(post_data['created_utc'])

                                # 只保留 7 天内的
                                if created_time >= datetime.now() - timedelta(days=days):
                                    # 转换为统一格式
                                    post = {
                                        'id': post_data.get('id'),
                                        'source': f'r/{subreddit}',
                                        'activity_type': 'post',
                                        'title': post_data.get('title', ''),
                                        'description': post_data.get('selftext', '') or post_data.get('url', ''),
                                        'author': post_data.get('author', 'unknown'),
                                        'url': f"https://www.reddit.com{post_data.get('permalink', '')}",
                                        'score': post_data.get('score', 0),
                                        'comments': post_data.get('num_comments', 0),
                                        'timestamp': created_time.isoformat(),
                                    }
                                    posts.append(post)

                        except Exception as e:
                            print(f"      ⚠️  处理帖子失败: {e}")

                    print(f"      ✅ r/{subreddit}: 收集了 {len([p for p in posts if p['source'] == f'r/{subreddit}'])} 条")

            except Exception as e:
                print(f"      ❌ r/{subreddit} 收集失败: {e}")

        print(f"   ✅ Reddit 收集完成：{len(posts)} 条真实帖子")

    except Exception as e:
        print(f"   ❌ Reddit 收集失败: {e}")
        import traceback
        traceback.print_exc()

    return posts


def save_to_unified_db(activities: List[Dict], db_path: str = "storage/data/unified_activities.db"):
    """保存到统一数据库"""
    print(f"\n💾 保存真实数据到统一数据库...")

    # 初始化数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS activities (
            id TEXT PRIMARY KEY,
            source TEXT NOT NULL,
            activity_type TEXT,
            title TEXT,
            description TEXT,
            author TEXT,
            url TEXT,
            score INTEGER DEFAULT 0,
            comments INTEGER DEFAULT 0,
            timestamp TEXT,
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
                (id, source, activity_type, title, description, author, url, score, comments,
                 timestamp, collected_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                activity.get('id', str(hash(str(activity)))),
                activity.get('source', 'unknown'),
                activity.get('activity_type', 'unknown'),
                activity.get('title', ''),
                activity.get('description', '')[:500],  # 限制长度
                activity.get('author', 'unknown'),
                activity.get('url', ''),
                activity.get('score', 0),
                activity.get('comments', 0),
                activity.get('timestamp', datetime.now().isoformat()),
                datetime.now().isoformat()
            ))

            saved_count += 1
        except Exception as e:
            print(f"⚠️  保存活动失败：{e}")

    conn.commit()
    conn.close()

    print(f"✅ 已保存 {saved_count} 条真实活动到统一数据库")


def sort_and_display(db_path: str = "storage/data/unified_activities.db"):
    """排序和显示数据"""
    print(f"\n📊 排序和显示真实数据...")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 获取所有活动，按分数排序
    cursor.execute('''
        SELECT * FROM activities
        ORDER BY score DESC, timestamp DESC
    ''')

    activities = [dict(row) for row in cursor.fetchall()]

    print(f"\n📋 数据统计：")
    print(f"   总活动数：{len(activities)}")

    # 按来源统计
    cursor.execute('''
        SELECT source, COUNT(*) as count
        FROM activities
        GROUP BY source
        ORDER BY count DESC
    ''')

    source_stats = cursor.fetchall()
    print(f"\n📊 按来源统计：")
    for row in source_stats:
        print(f"   {row[0]}: {row[1]} 条")

    # 按类型统计
    cursor.execute('''
        SELECT activity_type, COUNT(*) as count
        FROM activities
        GROUP BY activity_type
        ORDER BY count DESC
    ''')

    type_stats = cursor.fetchall()
    print(f"\n📊 按类型统计：")
    for row in type_stats:
        print(f"   {row[0]}: {row[1]} 条")

    # 显示前 20 条真实数据
    print(f"\n🔥 热门真实内容 (Top 20):")
    for i, activity in enumerate(activities[:20], 1):
        print(f"\n   [{i}] ⭐ {activity['score']} | 💬 {activity['comments']}")
        print(f"       📦 {activity['source']}")
        print(f"       👤 {activity['author']}")
        print(f"       📄 {activity['title'][:70]}...")
        print(f"       🔗 {activity['url']}")

    conn.close()

    return activities


def main():
    """主程序"""
    print("\n" + "=" * 80)
    print("🚀 Silicon Valley Alpha Radar - 收集完全真实的数据")
    print("=" * 80)

    # 步骤 1: 收集真实数据
    print("\n📡 [步骤 1/4] 收集真实数据...")

    all_activities = []

    # Hacker News
    hn_activities = collect_hacker_news_real_data(days=7)
    all_activities.extend(hn_activities)

    # Reddit
    reddit_activities = collect_reddit_real_data(days=7)
    all_activities.extend(reddit_activities)

    print(f"\n📊 总计收集: {len(all_activities)} 条真实活动")

    # 步骤 2: 保存到统一数据库
    print("\n💾 [步骤 2/4] 保存到统一数据库...")
    save_to_unified_db(all_activities)

    # 步骤 3: 排序和显示
    print("\n📊 [步骤 3/4] 排序和显示数据...")
    sorted_activities = sort_and_display()

    # 步骤 4: 完成
    print("\n" + "=" * 80)
    print("✅ 真实数据收集完成！")
    print("=" * 80)
    print(f"\n📁 数据库: storage/data/unified_activities.db")
    print(f"📊 总活动数: {len(sorted_activities)}")
    print(f"\n💡 重要:")
    print("   • 所有数据均来自 Hacker News 和 Reddit 官方 API")
    print("   • 每条信息都可追溯到原始链接")
    print("   • 数据完全真实，非虚构")


if __name__ == "__main__":
    main()
