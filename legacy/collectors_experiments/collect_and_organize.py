"""
收集真实数据并整理存储（修复版）
正确处理 Twitter 数据结构，收集 Hacker News 数据
"""

import os
import sys
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))


def load_twitter_data(db_path: str = "storage/data/twitter_posts_jina.db") -> List[Dict]:
    """从 Twitter 数据库加载真实数据"""
    print("\n🐦 从 Twitter 数据库加载数据...")

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM twitter_posts')
        posts = [dict(row) for row in cursor.fetchall()]

        conn.close()

        print(f"✅ Twitter 数据库加载完成：{len(posts)} 条")

        # 转换为统一格式
        activities = []
        for post in posts:
            activity = {
                'id': post.get('id'),
                'source': f'@{post.get("handle", "unknown")}',
                'activity_type': 'tweet',
                'title': post.get('content', '')[:100] + '...',  # 使用内容作为标题
                'description': post.get('content', ''),
                'author': post.get('handle', 'unknown'),
                'url': post.get('url', ''),
                'score': post.get('likes', 0),
                'comments': post.get('replies', 0),
                'timestamp': post.get('timestamp', datetime.now().isoformat()),
            }
            activities.append(activity)

        return activities

    except Exception as e:
        print(f"❌ 加载 Twitter 数据失败：{e}")
        return []


def load_hacker_news_data(db_path: str = "storage/data/hacker_news.db") -> List[Dict]:
    """从 Hacker News 数据库加载数据"""
    print("\n🕶️ 从 Hacker News 数据库加载数据...")

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # 获取表名
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]

        if not tables:
            print("⚠️  Hacker News 数据库为空")
            return []

        # 查询数据
        table_name = tables[0]
        cursor.execute(f'SELECT * FROM {table_name}')
        stories = [dict(row) for row in cursor.fetchall()]

        conn.close()

        print(f"✅ Hacker News 数据库加载完成：{len(stories)} 条")

        # 转换为统一格式
        activities = []
        for story in stories:
            activity = {
                'id': story.get('id'),
                'source': 'Hacker News',
                'activity_type': 'story',
                'title': story.get('title', ''),
                'description': story.get('text', story.get('url', ''))[:200] + '...',
                'author': story.get('by', 'unknown'),
                'url': f"https://news.ycombinator.com/item?id={story.get('id', '')}",
                'score': story.get('score', 0),
                'comments': story.get('descendants', 0),
                'timestamp': story.get('time', datetime.now().isoformat()),
            }
            activities.append(activity)

        return activities

    except Exception as e:
        print(f"❌ 加载 Hacker News 数据失败：{e}")
        return []


def save_to_unified_db(activities: List[Dict], db_path: str = "storage/data/unified_activities.db"):
    """保存到统一数据库"""
    print(f"\n💾 保存数据到统一数据库...")

    # 初始化数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            activity_type TEXT,
            title TEXT,
            description TEXT,
            author TEXT,
            url TEXT,
            score INTEGER DEFAULT 0,
            comments INTEGER DEFAULT 0,
            timestamp TEXT,
            collected_at TEXT,
            raw_data TEXT
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
            # 获取分数
            score = activity.get('score', 0) or 0
            comments = activity.get('comments', 0) or 0

            cursor.execute('''
                INSERT OR REPLACE INTO activities
                (source, activity_type, title, description, author, url, score, comments,
                 timestamp, collected_at, raw_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                activity.get('source', 'unknown'),
                activity.get('activity_type', 'unknown'),
                activity.get('title', ''),
                activity.get('description', ''),
                activity.get('author', 'unknown'),
                activity.get('url', ''),
                score,
                comments,
                activity.get('timestamp', datetime.now().isoformat()),
                datetime.now().isoformat(),
                str(activity)
            ))

            saved_count += 1
        except Exception as e:
            print(f"⚠️  保存活动失败：{e}")

    conn.commit()
    conn.close()

    print(f"✅ 已保存 {saved_count} 条活动到统一数据库")


def sort_and_analyze(db_path: str = "storage/data/unified_activities.db"):
    """排序和分析数据"""
    print(f"\n📊 排序和分析数据...")

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

    # 显示前 10 条热门活动
    print(f"\n🔥 热门活动 (Top 10):")
    for i, activity in enumerate(activities[:10], 1):
        print(f"\n   [{i}] ⭐ {activity['score']} | 💬 {activity['comments']}")
        print(f"       {activity['source']}")
        print(f"       {activity['title'][:60]}...")

    conn.close()

    return activities


def create_test_summary(activities: List[Dict]) -> str:
    """创建测试信息摘要"""
    if not activities:
        return "没有可用的测试数据"

    message = f"""🧪 <b>SV Alpha Radar - 测试信息摘要</b>

📅 <b>收集时间:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}

⚠️ <b>警告:</b> 以下是真实收集的测试数据，用于验证推送功能！

📈 <b>统计信息:</b>
"""

    # 按来源统计
    from collections import Counter
    sources = [a['source'] for a in activities]
    source_count = Counter(sources)

    for source, count in source_count.most_common():
        message += f"   • {source}: {count} 条\n"

    # 按类型统计
    types = [a['activity_type'] for a in activities]
    type_count = Counter(types)

    message += f"\n<b>按类型:</b>\n"
    for activity_type, count in type_count.most_common():
        message += f"   • {activity_type}: {count} 条\n"

    # 显示前 5 条
    message += f"\n<b>🔥 热门内容 (Top 5):</b>\n"

    # 按分数排序
    sorted_activities = sorted(activities, key=lambda x: x['score'], reverse=True)[:5]

    for i, activity in enumerate(sorted_activities, 1):
        message += f"\n{i}. <b>{activity['title'][:50]}...</b>\n"
        message += f"   📦 来源: {activity['source']}\n"
        message += f"   👤 作者: {activity['author']}\n"
        message += f"   ⭐ 分数: {activity['score']} | 💬 {activity['comments']}\n"
        if activity.get('url'):
            message += f"   🔗 <a href=\"{activity['url']}\">链接</a>\n"

    # 免责声明
    message += f"""

---
⚠️ <b>【测试信息】</b>
此消息用于验证推送功能，所有内容均为真实收集的测试数据，不代表最新事件。

🧪 <i>This is a TEST MESSAGE. All content is real collected data for functionality validation only.</i>

<i>🕐 发送时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}</i>
"""

    return message


def main():
    """主程序"""
    print("\n" + "=" * 80)
    print("🚀 Silicon Valley Alpha Radar - 真实数据收集和整理")
    print("=" * 80)

    # 步骤 1: 加载现有数据
    print("\n📡 [步骤 1/4] 加载真实数据...")

    all_activities = []

    # Hacker News
    hn_activities = load_hacker_news_data()
    all_activities.extend(hn_activities)

    # Twitter
    twitter_activities = load_twitter_data()
    all_activities.extend(twitter_activities)

    print(f"\n📊 总计收集: {len(all_activities)} 条活动")

    # 步骤 2: 保存到统一数据库
    print("\n💾 [步骤 2/4] 保存到统一数据库...")
    save_to_unified_db(all_activities)

    # 步骤 3: 排序和分析
    print("\n📊 [步骤 3/4] 排序和分析数据...")
    sorted_activities = sort_and_analyze()

    # 步骤 4: 发送测试信息
    print("\n📡 [步骤 4/4] 发送测试信息...")
    try:
        from utils.telegram_test import TelegramTester
        import json

        with open("config/config.json", 'r') as f:
            config = json.load(f)

        telegram_config = config.get('telegram', {})
        bot_token = telegram_config.get('botToken', '')
        chat_id = telegram_config.get('chatId', '')

        telegram_client = TelegramTester(bot_token, chat_id)

        # 生成测试信息
        test_message = create_test_summary(sorted_activities)

        # 发送
        print("\n📤 发送测试信息到 Telegram...")
        result = telegram_client.send_message(test_message)

        if result.get('success'):
            print("✅ 测试信息发送成功！")
        else:
            print(f"❌ 发送失败: {result.get('error', 'Unknown')}")

    except Exception as e:
        print(f"❌ 发送测试信息失败: {e}")
        import traceback
        traceback.print_exc()

    # 完成
    print("\n" + "=" * 80)
    print("✅ 数据收集和整理完成！")
    print("=" * 80)
    print(f"\n📁 数据库: storage/data/unified_activities.db")
    print(f"📊 总活动数: {len(sorted_activities)}")
    print(f"\n💡 提示: 启动装置时会自动加载这些测试数据")


if __name__ == "__main__":
    main()
