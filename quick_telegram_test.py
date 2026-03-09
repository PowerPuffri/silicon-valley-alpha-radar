"""
Quick Telegram Test - 快速测试 Telegram 推送
"""

import requests
import json


def test_telegram():
    """测试 Telegram 推送"""
    # 读取配置
    try:
        with open("config/config.json", 'r', encoding='utf-8') as f:
            config = json.load(f)
            bot_token = config.get('telegram', {}).get('botToken', '')
            chat_id = "7974510481"
    except:
        bot_token = ''
        chat_id = "7974510481"

    if not bot_token:
        print("❌ 未找到 Telegram Bot Token")
        return False

    # 测试消息
    message = """<b>🔍 Silicon Valley Alpha Radar - 测试推送</b>

---

<b>📊 数据收集状态</b>
• GitHub: ✅ 正常工作（42 条活动）
• Twitter: 🔄 框架就绪
• Reddit: 🔄 框架就绪
• Hacker News: 🔄 框架就绪

<b>🧠 智能分析状态</b>
• 趋势检测: ✅ 已实现
• 隐性共识: ✅ 已实现
• 相关性分析: ✅ 已实现

<b>📡 推送系统</b>
• Telegram Bot: ✅ 已配置
• 自动调度: 🔄 框架就绪

---

<i>📅 测试时间: 2026-03-09 01:28</i>
"""

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    payload = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'HTML'
    }

    print("\n" + "=" * 60)
    print("📡 开始 Telegram 推送测试")
    print("=" * 60)

    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()

        result = response.json()

        if result.get('ok'):
            print("✅ 推送成功！")
            print(f"   消息 ID: {result.get('message_id', '')}")
            print(f"   收件人: {result.get('chat', {}).get('username', 'Unknown')}")
            print("\n" + "=" * 60)
            print("✅ Telegram 推送测试通过！")
            print("=" * 60)
            return True
        else:
            print(f"❌ 推送失败: {result.get('description', 'Unknown')}")
            return False

    except Exception as e:
        print(f"❌ 网络错误: {e}")
        return False


if __name__ == "__main__":
    success = test_telegram()
    exit(0 if success else 1)
