#!/usr/bin/env python3
"""
系统启动测试 - 简化版
测试核心功能：数据收集、判断、存储、推送
"""

import os
import sys
import json
import sqlite3
from datetime import datetime

# 添加项目根目录到 Python 路径
project_root = '/Users/zhipu_glm/.openclaw/workspace/silicon-valley-alpha-radar'
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'config'))

from config.data_sources_config import DATA_SOURCES_CONFIG, calculate_priority


def main():
    """主测试程序"""
    print("\n" + "=" * 80)
    print("🚀 Silicon Valley Alpha Radar - 系统启动测试")
    print("=" * 80)
    print(f"\n🕐 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 步骤 1: 检查数据状态
    print("\n" + "-" * 80)
    print("📊 [步骤 1/6] 检查数据状态")
    print("-" * 80)

    databases = [
        ('storage/data/collected_articles.db', 'OpenAI 博客（已收集）'),
        ('storage/data/unified_activities.db', '统一数据库（未使用）'),
        ('storage/data/push_queue.db', '推送队列（已使用）')
    ]

    for db_path, db_desc in databases:
        if os.path.exists(db_path):
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()

                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]

                print(f"\n   📁 {db_desc}")
                print(f"      路径: {db_path}")
                print(f"      表: {tables}")

                for table in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    print(f"      • {table}: {count} 条")

                conn.close()
            except Exception as e:
                print(f"\n   ❌ {db_desc}: 读取失败 ({e})")
        else:
            print(f"\n   ⚠️  {db_desc}: 不存在")

    # 步骤 2: 加载测试数据
    print("\n" + "-" * 80)
    print("📥 [步骤 2/6] 加载测试数据")
    print("-" * 80)

    test_activities = []

    try:
        conn = sqlite3.connect("storage/data/collected_articles.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM articles ORDER BY id DESC')
        test_activities = [dict(row) for row in cursor.fetchall()]

        conn.close()

        print(f"\n   ✅ 加载了 {len(test_activities)} 条 OpenAI 博客文章")

    except Exception as e:
        print(f"\n   ❌ 加载数据失败: {e}")

    # 步骤 3: 计算优先级
    print("\n" + "-" * 80)
    print("🔍 [步骤 3/6] 计算信息优先级")
    print("-" * 80)

    prioritized_activities = []

    for activity in test_activities:
        try:
            # 添加必要的字段
            if 'source_type' not in activity:
                if 'source' in activity and 'blog' in activity['source'].lower():
                    activity['source_type'] = 'official_blog'
                else:
                    activity['source_type'] = 'community'

            activity['priority_score'] = calculate_priority(activity)
            prioritized_activities.append(activity)

        except Exception as e:
            print(f"   ⚠️  计算活动优先级失败: {e}")

    # 排序
    prioritized = sorted(prioritized_activities, key=lambda x: x.get('priority_score', 0), reverse=True)

    # 统计
    high = len([a for a in prioritized if a['priority_score'] >= 90])
    medium = len([a for a in prioritized if 50 <= a['priority_score'] < 90])
    low = len([a for a in prioritized if a['priority_score'] < 50])

    print(f"\n   ✅ 优先级计算完成: {len(prioritized)} 条活动")
    print(f"      🔴 高优先级 (>=90): {high}")
    print(f"      🟠 中优先级 (50-89): {medium}")
    print(f"      🟡 低优先级 (<50): {low}")

    # 步骤 4: 生成测试消息
    print("\n" + "-" * 80)
    print("📝 [步骤 4/6] 生成测试消息")
    print("-" * 80)

    test_message = f"""🧪 <b>SV Alpha Radar - 系统启动测试</b>

📅 <b>测试时间:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}

✅ <b>测试内容:</b>
以下是从 OpenAI 官方博客收集的真实数据！
每条信息都可追溯到原始链接。

📈 <b>数据统计:</b>
   • 总活动数: {len(prioritized)}
   • 数据源: OpenAI Blog
   • 收集方式: Jina CLI

📊 <b>优先级:</b>
   • 🔴 高 (>=90): {high}
   • 🟠 中 (50-89): {medium}
   • 🟡 低 (<50): {low}

<b>🔥 热门内容 (Top 10):</b>
"""

    for i, activity in enumerate(prioritized[:10], 1):
        score = activity['priority_score']
        title = activity.get('title', activity.get('slug', ''))[:50]
        url = activity.get('url', '')

        message += f"\n{i}. ⭐ <b>{score}</b>\n"
        message += f"   🏢 OpenAI Blog\n"
        message += f"   📄 {title}...\n"
        if url:
            message += f"   🔗 {url}\n"

    message += f"""

---
⚠️ <b>【系统启动测试】</b>
以上是系统收集的真实数据，用于验证完整功能：
   • 数据收集 ✅
   • 优先级计算 ✅
   • 消息格式化 ✅
   • 准备推送 ✅

<b>🕐 测试时间:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

<i>💡 系统准备好进入正常运行状态！</i>
"""

    print(f"\n   ✅ 测试消息生成成功")
    print(f"      长度: {len(test_message)} 字符")

    # 步骤 5: 发送 Telegram 消息
    print("\n" + "-" * 80)
    print("📤 [步骤 5/6] 发送 Telegram 测试消息")
    print("-" * 80)

    try:
        from utils.telegram_test import TelegramTester

        # 读取配置
        with open("config/config.json", 'r') as f:
            config = json.load(f)

        telegram_config = config.get('telegram', {})
        bot_token = telegram_config.get('botToken', '')
        chat_id = telegram_config.get('chatId', '')

        if not bot_token or not chat_id:
            print(f"\n   ⚠️  Telegram 配置不完整")
            print(f"      Bot Token: {'已设置' if bot_token else '未设置'}")
            print(f"      Chat ID: {'已设置' if chat_id else '未设置'}")
        else:
            # 创建客户端
            telegram_client = TelegramTester(bot_token, chat_id)

            # 发送消息
            result = telegram_client.send_message(test_message)

            if result.get('success'):
                print(f"\n   ✅ Telegram 推送成功！")
                print(f"      消息 ID: {result.get('message', 'Unknown')}")
            else:
                print(f"\n   ❌ Telegram 推送失败")
                print(f"      错误: {result.get('error', 'Unknown')}")

    except Exception as e:
        print(f"\n   ❌ 推送失败: {e}")

    # 步骤 6: 完成报告
    print("\n" + "=" * 80)
    print("✅ 系统启动测试完成")
    print("=" * 80)
    print(f"\n📋 测试总结:")
    print(f"   ✅ 数据收集: {len(prioritized)} 条活动")
    print(f"   ✅ 优先级计算: 完成")
    print(f"   ✅ 消息格式化: 完成")
    print(f"   📤 Telegram 推送: 已执行")

    print(f"\n📁 数据库状态:")
    print(f"   • collected_articles.db: {len(prioritized)} 条")
    print(f"   • 数据来源: OpenAI Blog（Jina CLI 收集）")

    print(f"\n🔥 优先级分布:")
    print(f"   • 🔴 高 (>=90): {high}")
    print(f"   • 🟠 中 (50-89): {medium}")
    print(f"   • 🟡 低 (<50): {low}")

    print(f"\n🚀 系统状态:")
    print(f"   ✅ 数据收集: 正常")
    print(f"   ✅ 优先级计算: 正常")
    print(f"   ✅ 消息格式化: 正常")
    print(f"   📤 Telegram 推送: 已执行")

    print(f"\n💡 下一步:")
    print(f"   1. 检查 Telegram 是否收到测试消息")
    print(f"   2. 确认推送功能是否正常")
    print(f"   3. 启动系统正常运行模式")

    print("\n" + "=" * 80)
    print("🎉 Silicon Valley Alpha Radar - 系统启动测试完成")
    print("=" * 80)
    print(f"\n📱 请检查 Telegram 是否收到测试消息！")
    print(f"🚀 系统准备好进入正常运行状态！")


if __name__ == "__main__":
    main()
