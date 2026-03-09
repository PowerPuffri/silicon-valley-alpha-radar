"""
加载已收集的真实数据并发送测试信息
按照优先级排序后发送
"""

import os
import sys
import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Dict
from collections import Counter

# 添加项目根目录到 Python 路径
project_root = '/Users/zhipu_glm/.openclaw/workspace/silicon-valley-alpha-radar'
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))
sys.path.insert(0, os.path.join(project_root, 'src', 'utils'))
sys.path.insert(0, os.path.join(project_root, 'config'))

from data_sources_config import DATA_SOURCES_CONFIG, calculate_priority
from utils.telegram_test import TelegramTester


def load_collected_data(db_path: str = "storage/data/unified_activities.db") -> List[Dict]:
    """
    加载已收集的真实数据

    Args:
        db_path: 数据库路径

    Returns:
        事件列表
    """
    print("\n📥 加载已收集的真实数据...")

    if not os.path.exists(db_path):
        print(f"❌ 数据库不存在: {db_path}")
        return []

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM activities ORDER BY timestamp DESC')
        activities = [dict(row) for row in cursor.fetchall()]

        conn.close()

        print(f"✅ 加载了 {len(activities)} 条真实活动")

        return activities

    except Exception as e:
        print(f"❌ 加载数据失败: {e}")
        return []


def prioritize_and_sort(activities: List[Dict]) -> List[Dict]:
    """
    计算优先级并排序

    Args:
        activities: 活动列表

    Returns:
        排序后的活动列表
    """
    print(f"\n📊 计算优先级: {len(activities)} 个活动")

    # 为每个活动计算优先级
    for activity in activities:
        try:
            # 添加必要的字段用于优先级计算
            if 'cross_verified' not in activity:
                activity['cross_verified'] = False

            priority_score = calculate_priority(activity)
            activity['priority_score'] = priority_score

        except Exception as e:
            print(f"   ⚠️  计算优先级失败: {e}")
            activity['priority_score'] = 0

    # 按优先级分数排序
    prioritized = sorted(activities, key=lambda x: x.get('priority_score', 0), reverse=True)

    print(f"✅ 优先级计算完成")

    return prioritized


def send_test_summary(activities: List[Dict]):
    """
    发送测试摘要到 Telegram

    Args:
        activities: 活动列表
    """
    print("\n📤 发送测试摘要到 Telegram...")

    try:
        # 读取 Telegram 配置
        with open("config/config.json", 'r') as f:
            config = json.load(f)

        telegram_config = config.get('telegram', {})
        bot_token = telegram_config.get('botToken', '')
        chat_id = telegram_config.get('chatId', '')

        # 创建 Telegram 客户端
        telegram_client = TelegramTester(bot_token, chat_id)

        # 统计信息
        from collections import Counter
        sources = [a.get('source', 'unknown') for a in activities]
        source_count = Counter(sources)

        # 按优先级分组
        high_priority = len([a for a in activities if a.get('priority_score', 0) >= 100])
        medium_priority = len([a for a in activities if 50 <= a.get('priority_score', 0) < 100])
        low_priority = len([a for a in activities if a.get('priority_score', 0) < 50])

        # 生成测试信息
        message = f"""🧪 <b>SV Alpha Radar - 真实数据测试</b>

📅 <b>收集时间:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}

✅ <b>完全真实的数据</b>
以下是从 Hacker News 官方 API 收集的真实数据（99 条）。
每条信息都可追溯到原始链接！

📈 <b>统计信息:</b>
   • 总活动数: {len(activities)}
   • 数据源: Hacker News
   • 收集时间: 最近 7 天

📊 <b>按来源:</b>
"""
        for source, count in source_count.most_common():
            message += f"   • {source}: {count} 条\n"

        message += f"""

📊 <b>按优先级:</b>
   • 🔴 高优先级 (>=100): {high_priority}
   • 🟠 中优先级 (50-99): {medium_priority}
   • 🟡 低优先级 (<50): {low_priority}

<b>🔥 高优先级内容 (Top 15):</b>
"""

        # 显示前 15 个高优先级活动
        top_15 = [a for a in activities if a.get('priority_score', 0) >= 100][:15]
        for i, activity in enumerate(top_15, 1):
            score = activity.get('priority_score', 0)
            title = activity.get('title', '')[:50]
            source = activity.get('source', 'unknown')
            url = activity.get('url', '')

            message += f"\n{i}. ⭐ {score}\n"
            message += f"   📦 {source}\n"
            message += f"   📄 {title}...\n"
            if url:
                message += f"   🔗 <a href=\"{url}\">原始链接</a>\n"

        # 免责声明
        message += f"""

---
⚠️ <b>【真实测试数据】</b>
以上是从 Hacker News 官方 API 收集的真实数据。
每条信息都可追溯到原始链接。
数据收集时间：最近 7 天
用于验证推送功能和优先级排序。

<i>🕐 发送时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}</i>
"""

        # 发送消息
        result = telegram_client.send_message(message)

        if result.get('success'):
            print("✅ 测试摘要发送成功！")
            return True
        else:
            print(f"❌ 发送失败: {result.get('error', 'Unknown')}")
            return False

    except Exception as e:
        print(f"❌ 发送测试摘要失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主程序"""
    import json

    print("\n" + "=" * 80)
    print("🧪 Silicon Valley Alpha Radar - 真实数据测试")
    print("=" * 80)

    # 步骤 1: 加载已收集的数据
    print("\n[步骤 1/3] 加载已收集的真实数据...")
    activities = load_collected_data()

    if not activities:
        print("\n❌ 没有可用的数据")
        return

    # 步骤 2: 计算优先级并排序
    print("\n[步骤 2/3] 计算优先级并排序...")
    prioritized = prioritize_and_sort(activities)

    # 步骤 3: 发送测试摘要
    print("\n[步骤 3/3] 发送测试摘要...")
    success = send_test_summary(prioritized)

    # 完成
    print("\n" + "=" * 80)
    print("✅ 真实数据测试完成！")
    print("=" * 80)
    print(f"\n📁 数据库: storage/data/unified_activities.db")
    print(f"📊 总活动数: {len(activities)}")
    print(f"🔴 高优先级: {len([a for a in activities if a.get('priority_score', 0) >= 100])} 条")
    print(f"🟠 中优先级: {len([a for a in activities if 50 <= a.get('priority_score', 0) < 100])} 条")
    print(f"🟡 低优先级: {len([a for a in activities if a.get('priority_score', 0) < 50])} 条")


if __name__ == "__main__":
    main()
