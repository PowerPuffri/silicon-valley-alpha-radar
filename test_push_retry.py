#!/usr/bin/env python3
"""
推送测试 - 重新测试推送功能
使用现有数据发送 Telegram 消息
"""

import os
import sys
import json
import sqlite3

# 添加项目根目录到 Python 路径
project_root = '/Users/zhipu_glm/.openclaw/workspace/silicon-valley-alpha-radar'
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))
sys.path.insert(0, os.path.join(project_root, 'src', 'utils'))


def main():
    """主程序"""
    print("\n" + "=" * 80)
    print("🧪 Silicon Valley Alpha Radar - 推送重新测试")
    print("=" * 80)

    # 1. 检查数据状态
    print("\n📊 [步骤 1/4] 检查数据状态...")
    databases = [
        ('collected_articles.db', '收集的 OpenAI 博客'),
        ('unified_activities.db', '统一活动数据库'),
        ('push_queue.db', '推送队列')
    ]

    for db_name, db_desc in databases:
        db_path = f"storage/data/{db_name}"
        if os.path.exists(db_path):
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()

                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]

                print(f"   📁 {db_desc}")
                print(f"      路径: {db_path}")
                print(f"      表: {tables}")

                for table in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    print(f"      • {table}: {count} 条")

                conn.close()
            except Exception as e:
                print(f"   ⚠️  {db_desc}: 无法读取 ({e})")
        else:
            print(f"   ⚠️  {db_desc}: 不存在")

    # 2. 生成测试消息（使用纯文本，避免 HTML 问题）
    print("\n📝 [步骤 2/4] 生成测试消息（纯文本）...")

    test_message = """🧪 SV Alpha Radar - 推送测试

📅 时间: 2026-03-09 21:32

✅ 测试内容:

[测试文章 1]
标题: GPT-5.1 Release
链接: https://openai.com/blog/gpt-5-1
来源: OpenAI Blog

[测试文章 2]
标题: GPT-5.2 Update
链接: https://openai.com/blog/gpt-5-2
来源: OpenAI Blog

---

⚠️ 这是纯文本测试消息
用于验证 Telegram 推送功能

测试时间: 2026-03-09 21:32
"""

    print(f"✅ 消息生成成功")
    print(f"   长度: {len(test_message)} 字符")

    # 3. 发送 Telegram 消息
    print("\n📤 [步骤 3/4] 发送 Telegram 消息...")

    try:
        from utils.telegram_test import TelegramTester

        # 读取配置
        with open("config/config.json", 'r') as f:
            config = json.load(f)

        telegram_config = config.get('telegram', {})
        bot_token = telegram_config.get('botToken', '')
        chat_id = telegram_config.get('chatId', '')

        # 创建客户端
        telegram_client = TelegramTester(bot_token, chat_id)

        # 发送纯文本消息
        result = telegram_client.send_message(test_message)

        if result.get('success'):
            print(f"✅ Telegram 消息发送成功！")
            print(f"   返回: {result.get('message', 'Success')}")
        else:
            print(f"❌ Telegram 消息发送失败: {result.get('error', 'Unknown')}")

    except Exception as e:
        print(f"❌ 发送失败: {e}")
        import traceback
        traceback.print_exc()

    # 4. 测试完成
    print("\n" + "=" * 80)
    print("✅ 推送测试完成！")
    print("=" * 80)
    print(f"\n💡 说明:")
    print(f"   1. 使用纯文本消息（避免 HTML 解析问题）")
    print(f"   2. 消息长度: {len(test_message)} 字符")
    print(f"   3. 请检查 Telegram 是否收到消息")


if __name__ == "__main__":
    main()
