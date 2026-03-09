"""
快速测试 - 发送测试消息到 Telegram
"""

import sys
import os

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

from utils.telegram_test import TelegramTester


def main():
    print("\n" + "=" * 70)
    print("📡 Silicon Valley Alpha Radar - Telegram 推送测试")
    print("=" * 70)

    # 从配置文件读取
    import json
    with open("config/config.json", 'r') as f:
        config = json.load(f)

    telegram_config = config.get('telegram', {})
    bot_token = telegram_config.get('botToken', '')
    chat_id = telegram_config.get('chatId', '')

    print(f"\n🔧 配置信息:")
    print(f"   Bot Token: {bot_token[:20]}...")
    print(f"   Chat ID: {chat_id}")

    # 初始化客户端
    tester = TelegramTester(bot_token, chat_id)

    # 发送测试消息
    print(f"\n📤 发送测试消息...")

    message = """
<b>🚀 Silicon Valley Alpha Radar - 系统启动</b>

✅ 推送机制已配置完成
✅ Telegram 推送已启用
✅ 信息判断层已激活

<b>📊 数据源:</b>
• Reddit
• Hacker News
• Twitter

<b>⚙️ 配置:</b>
• 监控对象：AI 界大佬（Reddit, HN, Twitter）
• 数据源：Reddit, Hacker News, Twitter（已移除 GitHub）
• 检查间隔: 30 分钟

<i>💡 信息不对称是终极力量。保持优势！</i>
<i>🕐 启动时间: 2026-03-09 10:37</i>
    """

    result = tester.send_message(message)

    if result.get('success'):
        print(f"\n✅ 测试消息发送成功！")
        print(f"   请检查 Telegram 是否收到消息")
    else:
        print(f"\n❌ 测试消息发送失败: {result.get('error', 'Unknown error')}")

    print("\n" + "=" * 70)
    print("✅ 测试完成")
    print("=" * 70)


if __name__ == "__main__":
    main()
