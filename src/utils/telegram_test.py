"""
Telegram Test - 测试 Telegram 推送功能
验证 bot 是否能正常发送消息
"""

import requests
import json
from typing import Dict, Optional


class TelegramTester:
    def __init__(self, bot_token: str, chat_id: str):
        """
        初始化 Telegram 测试器

        Args:
            bot_token: Telegram Bot Token
            chat_id: 目标聊天 ID
        """
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"

    def send_message(self, text: str) -> Dict:
        """
        发送文本消息到 Telegram

        Args:
            text: 消息内容

        Returns:
            API 响应
        """
        url = f"{self.base_url}/sendMessage"

        payload = {
            'chat_id': self.chat_id,
            'text': text,
            'parse_mode': 'HTML'
        }

        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()

            result = response.json()
            
            if result.get('ok'):
                print(f"✅ 消息发送成功！")
                print(f"   消息 ID: {result.get('message_id', '')}")
                return {'success': True, 'message_id': result.get('message_id')}
            else:
                print(f"❌ 消息发送失败: {result.get('description', 'Unknown error')}")
                return {'success': False, 'error': result.get('description')}

        except requests.exceptions.RequestException as e:
            print(f"❌ 网络错误: {e}")
            return {'success': False, 'error': str(e)}
        except Exception as e:
            print(f"❌ 未知错误: {e}")
            return {'success': False, 'error': str(e)}

    def send_trend_alert(self, title: str, content: str) -> Dict:
        """
        发送趋势告警消息

        Args:
            title: 趋势标题
            content: 趋势内容

        Returns:
            API 响应
        """
        message = f"""
<b>🔍 Silicon Valley Alpha Radar - 趋势告警</b>

<b>{title}</b>
{content}

---
<i>📅 检测时间: 2026-03-09 00:23 UTC</i>
        """

        return self.send_message(message)

    def send_collection_summary(self, summary: Dict) -> Dict:
        """
        发送数据收集摘要

        Args:
            summary: 数据收集摘要

        Returns:
            API 响应
        """
        message = f"""
<b>📊 Silicon Valley Alpha Radar - 数据收集完成</b>

📈 数据概览:
• GitHub 活动: {summary.get('github_posts', 0)} 条
• Reddit 帖子: {summary.get('reddit_posts', 0)} 条
• Hacker News 故事: {summary.get('hackernews_stories', 0)} 条

⏱️  收集耗时: {summary.get('duration', 0):.2f} 秒

<i>📅 完成时间: 2026-03-09 00:25 UTC</i>
        """

        return self.send_message(message)


def main():
    """主程序"""
    import argparse

    parser = argparse.ArgumentParser(description="Telegram Test")
    parser.add_argument('--token', type=str, required=True, help='Telegram Bot Token')
    parser.add_argument('--chat-id', type=str, required=True, help='目标聊天 ID')
    parser.add_argument('--message', type=str, help='要发送的测试消息')
    parser.add_argument('--test-alert', action='store_true', help='发送测试趋势告警')
    parser.add_argument('--test-summary', action='store_true', help='发送测试数据收集摘要')

    args = parser.parse_args()

    # 初始化测试器
    tester = TelegramTester(args.token, args.chat_id)

    print("\n" + "=" * 60)
    print("📡 Telegram 推送测试")
    print("=" * 60)
    print(f"\n🔧 配置信息:")
    print(f"   Bot Token: {args.token[:20]}...")
    print(f"   Chat ID: {args.chat_id}")

    # 发送测试
    if args.message:
        print(f"\n📤 [测试 1/3] 发送自定义消息...")
        result = tester.send_message(args.message)
        print(f"   结果: {'✅ 成功' if result['success'] else '❌ 失败'}")

    elif args.test_alert:
        print(f"\n📤 [测试 2/3] 发送趋势告警...")
        result = tester.send_trend_alert(
            "测试趋势告警",
            "检测到关键词'AI'、'neural network'的频率上升，可能预示新的技术趋势。"
        )
        print(f"   结果: {'✅ 成功' if result['success'] else '❌ 失败'}")

    elif args.test_summary:
        print(f"\n📤 [测试 3/3] 发送数据收集摘要...")
        result = tester.send_collection_summary({
            'github_posts': 10,
            'reddit_posts': 5,
            'hackernews_stories': 3,
            'duration': 42.5
        })
        print(f"   结果: {'✅ 成功' if result['success'] else '❌ 失败'}")

    else:
        print(f"\n⚠️  未指定测试类型")
        print("\n📝 使用示例:")
        print("   --test-alert  发送趋势告警")
        print("   --test-summary  发送数据收集摘要")
        print("   --message '你好'  发送自定义消息")

    print("\n" + "=" * 60)
    print("✅ 测试完成！")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    main()
