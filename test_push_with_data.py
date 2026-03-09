"""
测试推送：使用现有数据发送 Telegram 消息
"""

import os
import sys
import sqlite3
from datetime import datetime
from typing import List, Dict

# 添加项目根目录到 Python 路径
project_root = '/Users/zhipu_glm/.openclaw/workspace/silicon-valley-alpha-radar'
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))
sys.path.insert(0, os.path.join(project_root, 'src', 'formatters'))
sys.path.insert(0, os.path.join(project_root, 'src', 'utils'))
sys.path.insert(0, os.path.join(project_root, 'config'))

from formatters.push_formatter import PushFormatter
from utils.telegram_test import TelegramTester


def load_collected_articles(db_path: str = "storage/data/collected_articles.db") -> List[Dict]:
    """
    加载收集的文章数据

    Args:
        db_path: 数据库路径

    Returns:
        文章列表
    """
    print("\n📥 加载收集的文章...")

    if not os.path.exists(db_path):
        print(f"❌ 数据库不存在: {db_path}")
        return []

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM articles ORDER BY id DESC')
        articles = [dict(row) for row in cursor.fetchall()]

        conn.close()

        print(f"✅ 加载了 {len(activities)} 篇文章")

        return activities

    except Exception as e:
        print(f"❌ 加载数据失败: {e}")
        return []


def generate_test_message(activities: List[Dict]) -> str:
    """
    生成测试推送消息

    Args:
        activities: 文章列表

    Returns:
        Telegram 消息
    """
    print(f"\n📝 生成测试消息 ({len(activities)} 篇文章）...")

    # 使用推送格式化器
    formatter = PushFormatter()

    # 生成重磅格式（只发 1 篇）
    if activities:
        message = formatter.format_breaking(activities[:1])
    else:
        message = "没有可用的数据"

    # 截断
    message = formatter.truncate_message(message)

    return message


def send_telegram_test(message: str):
    """
    发送测试消息到 Telegram

    Args:
        message: 消息内容

    Returns:
        是否发送成功
    """
    print(f"\n📤 发送 Telegram 测试消息...")
    print(f"   消息长度: {len(message)} 字符")

    try:
        # 读取 Telegram 配置
        import json
        with open("config/config.json", 'r') as f:
            config = json.load(f)

        telegram_config = config.get('telegram', {})
        bot_token = telegram_config.get('botToken', '')
        chat_id = telegram_config.get('chatId', '')

        # 创建客户端
        telegram_client = TelegramTester(bot_token, chat_id)

        # 发送消息
        result = telegram_client.send_message(message)

        if result.get('success'):
            print(f"✅ Telegram 消息发送成功！")
            print(f"   返回: {result.get('message', 'Success')}")
            return True
        else:
            print(f"❌ Telegram 消息发送失败: {result.get('error', 'Unknown')}")
            return False

    except Exception as e:
        print(f"❌ 发送失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主程序"""
    print("\n" + "=" * 80)
    print("🧪 Silicon Valley Alpha Radar - 推送测试")
    print("=" * 80)

    # 1. 加载数据
    print("\n📡 [步骤 1/3] 加载收集的文章...")
    activities = load_collected_articles()

    if not activities:
        print("\n❌ 没有可用的数据")
        return

    # 2. 生成消息
    print("\n📝 [步骤 2/3] 生成测试消息...")
    message = generate_test_message(activities)

    if not message:
        print("\n❌ 消息生成失败")
        return

    print(f"✅ 消息生成成功")
    print(f"\n📄 消息预览:")
    print("-" * 80)
    print(message[:500])
    print("-" * 80)

    # 3. 发送消息
    print("\n📤 [步骤 3/3] 发送 Telegram 消息...")
    success = send_telegram_test(message)

    # 完成
    print("\n" + "=" * 80)
    print("✅ 推送测试完成！")
    print("=" * 80)

    if success:
        print(f"\n📱 请检查 Telegram 是否收到消息")
        print(f"📊 数据库: storage/data/collected_articles.db")
        print(f"📊 文章数: {len(activities)}")
    else:
        print(f"\n❌ 推送发送失败，请检查:")
        print(f"   1. Bot Token 是否正确")
        print(f"   2. Chat ID 是否正确")
        print(f"   3. Bot 是否有发送权限")


if __name__ == "__main__":
    main()
