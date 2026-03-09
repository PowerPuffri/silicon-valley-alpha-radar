"""
简化版数据收集测试 - 只测试已收集的 Hacker News 数据
"""

import os
import sys
from datetime import datetime, timedelta
from typing import List, Dict
from collections import Counter

# 添加项目根目录到 Python 路径
project_root = '/Users/zhipu_glm/.openclaw/workspace/silicon-valley-alpha-radar'
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'config'))

from data_sources_config import DATA_SOURCES_CONFIG, calculate_priority


def main():
    """主程序 - 测试数据收集"""
    print("\n" + "=" * 80)
    print("🧪 Silicon Valley Alpha Radar - 数据收集测试（简化版）")
    print("=" * 80)

    all_events = []

    # 1. 加载 Hacker News 数据（之前收集的 99 条）
    print("\n📊 [1/2] 加载 Hacker News 数据...")
    try:
        import sqlite3

        hn_db = "storage/data/hacker_news.db"
        if os.path.exists(hn_db):
            conn = sqlite3.connect(hn_db)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute('SELECT * FROM hacker_news ORDER BY timestamp DESC')
            hn_events = [dict(row) for row in cursor.fetchall()]

            # 转换为统一格式
            for event in hn_events:
                unified_event = {
                    'id': f"hn_{event['id']}",
                    'source_type': 'community',
                    'source': 'Hacker News',
                    'activity_type': 'story',
                    'title': event.get('title', ''),
                    'description': event.get('text', '')[:200],
                    'author': event.get('by', 'unknown'),
                    'url': event.get('url', f"https://news.ycombinator.com/item?id={event['id']}"),
                    'score': event.get('score', 0),
                    'comments': event.get('descendants', 0),
                    'timestamp': event.get('time', datetime.now().isoformat()),
                    '_converted': True
                }
                all_events.append(unified_event)

            conn.close()
            print(f"   ✅ Hacker News: {len(hn_events)} 条")
    except Exception as e:
        print(f"   ❌ Hacker News 加载失败: {e}")

    # 2. 计算优先级
    print("\n📊 [2/2] 计算信息优先级...")
    prioritized_events = []

    for event in all_events:
        try:
            # 为每个事件计算优先级
            priority_score = calculate_priority(event)
            event['priority_score'] = priority_score
            prioritized_events.append(event)
        except Exception as e:
            print(f"   ⚠️  计算优先级失败: {e}")
            event['priority_score'] = 0

    # 排序
    prioritized = sorted(prioritized_events, key=lambda x: x.get('priority_score', 0), reverse=True)

    print(f"   ✅ 优先级计算完成: {len(prioritized)} 个事件")

    # 3. 显示统计
    print(f"\n📊 数据统计:")
    print(f"   总事件数: {len(all_events)}")

    # 按优先级分组
    high_priority = len([e for e in prioritized if e.get('priority_score', 0) >= 100])
    medium_priority = len([e for e in prioritized if 50 <= e.get('priority_score', 0) < 100])
    low_priority = len([e for e in prioritized if e.get('priority_score', 0) < 50])

    print(f"\n📊 按优先级分组:")
    print(f"   🔴 高优先级 (>=100): {high_priority}")
    print(f"   🟠 中优先级 (50-99): {medium_priority}")
    print(f"   🟡 低优先级 (<50): {low_priority}")

    # 显示前 20 个
    print(f"\n🔥 高优先级事件 (Top 20):")
    for i, event in enumerate(prioritized[:20], 1):
        score = event.get('priority_score', 0)
        title = event.get('title', event.get('content', ''))[:70]

        print(f"\n   [{i}] 优先级: {score}")
        print(f"      📦 {event['source']}")
        print(f"      📄 {title}...")
        print(f"      🕐 {event['timestamp']}")

    # 4. 保存到测试数据库
    print(f"\n💾 保存到测试数据库...")
    try:
        import sqlite3

        test_db = "storage/data/test_collected.db"
        conn = sqlite3.connect(test_db)
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
                collected_at TEXT
            )
        ''')

        conn.commit()

        # 插入数据
        for event in prioritized:
            try:
                cursor.execute('''
                    INSERT OR REPLACE INTO activities
                    (id, source_type, source, activity_type, title, description, author, url,
                     score, comments, timestamp, priority_score, collected_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    event.get('id', str(hash(str(event)))),
                    event.get('source_type', 'unknown'),
                    event.get('source', 'unknown'),
                    event.get('activity_type', 'unknown'),
                    event.get('title', ''),
                    event.get('description', '')[:500],
                    event.get('author', ''),
                    event.get('url', ''),
                    event.get('score', 0),
                    event.get('comments', 0),
                    event.get('timestamp', datetime.now().isoformat()),
                    event.get('priority_score', 0),
                    datetime.now().isoformat()
                ))
            except Exception as e:
                print(f"   ⚠️  保存事件失败: {e}")

        conn.commit()
        conn.close()

        print(f"   ✅ 已保存 {len(prioritized)} 条事件到测试数据库")

    except Exception as e:
        print(f"   ❌ 保存到数据库失败: {e}")

    # 完成
    print("\n" + "=" * 80)
    print("✅ 数据收集测试完成！")
    print("=" * 80)
    print(f"\n📁 测试数据库: storage/data/test_collected.db")
    print(f"📊 总事件数: {len(prioritized)}")
    print(f"🔥 高优先级: {high_priority} 条")


if __name__ == "__main__":
    main()
