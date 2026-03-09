"""
完整推送功能测试 - 使用虚构的测试数据
**注意：这些是测试数据，不是真实信息！**
**数据源：Reddit, Hacker News, Twitter（无 GitHub）**
"""

import sys
import os

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

from judges.info_judge import InfoJudge
from queues.push_queue_manager import PushQueueManager
from formatters.push_formatter import PushFormatter
from utils.telegram_test import TelegramTester


def create_fictional_test_activities():
    """创建明显虚构的测试数据（不会与真实信息混淆）"""
    return [
        {
            'id': 101,
            'activity_type': 'post',
            'source': 'reddit',
            'subreddit': 'test-subreddit',
            'author': 'test-reddit-user',
            'title': '[TEST] Mock Reddit post about AI research',
            'description': 'This is a test Reddit post to validate push functionality from Reddit data source.',
            'timestamp': '2026-03-09T10:00:00Z',
            'url': 'https://reddit.com/r/test/test123',
            'upvotes': 5,
            'comments': 2
        },
        {
            'id': 102,
            'activity_type': 'story',
            'source': 'hackernews',
            'author': 'test-hn-user',
            'title': '[DEMO] Mock Hacker News story about LLM optimization',
            'description': 'Test story to verify Hacker News data source integration.',
            'timestamp': '2026-03-09T09:00:00Z',
            'url': 'https://news.ycombinator.com/item?id=123456',
            'upvotes': 3,
            'comments': 1
        },
        {
            'id': 103,
            'activity_type': 'tweet',
            'source': 'twitter',
            'author': 'test-twitter-account',
            'title': '[TEST] Mock tweet about AI breakthrough',
            'description': 'This is a test tweet to validate Twitter data source functionality.',
            'timestamp': '2026-03-09T08:00:00Z',
            'url': 'https://twitter.com/test/status/789',
            'likes': 2,
            'comments': 0
        },
        {
            'id': 104,
            'activity_type': 'post',
            'source': 'reddit',
            'subreddit': 'r/test',
            'author': 'demo-user',
            'title': '[TEST] Mock Reddit post for normal level classification',
            'description': 'Test post to verify normal level classification from Reddit.',
            'timestamp': '2026-03-09T07:00:00Z',
            'url': 'https://reddit.com/r/test/456',
            'upvotes': 1,
            'comments': 1
        }
    ]


def add_test_disclaimer(message: str) -> str:
    """在消息中添加测试免责声明"""
    disclaimer = """

---

⚠️ <b>【测试消息】</b>
此消息用于验证推送功能，所有内容均为虚构的测试数据，不代表真实事件。

🧪 <i>This is a TEST MESSAGE. All content is fictional for functionality validation only.</i>
"""
    return message + disclaimer


def main():
    """主程序"""
    print("\n" + "=" * 80)
    print("🧪 Silicon Valley Alpha Radar - 推送功能测试（无 GitHub）")
    print("=" * 80)
    print("\n⚠️  警告：以下是测试数据，不是真实信息！\n")
    print("📊 数据源：Reddit, Hacker News, Twitter")

    # 步骤 1: 创建虚构测试数据
    print("\n🎯 [步骤 1/5] 创建虚构的测试数据...")
    test_activities = create_fictional_test_activities()
    print(f"✅ 创建了 {len(test_activities)} 个测试活动（均为虚构内容）")

    # 步骤 2: 判断级别
    print("\n🔍 [步骤 2/5] 判断信息级别...")
    try:
        judge = InfoJudge("config/push_config.json")
        judged_activities = judge.judge_activities_batch(test_activities)

        summary = judge.get_judgment_summary(judged_activities)
        print(f"✅ 判断完成:")
        print(f"   🔴 重磅: {summary['breaking']}")
        print(f"   🟠 重要: {summary['important']}")
        print(f"   🟡 普通: {summary['normal']}")
        print(f"   ⚪ 忽略: {summary['ignored']}")

    except Exception as e:
        print(f"❌ 判断失败: {e}")
        import traceback
        traceback.print_exc()
        return

    # 步骤 3: 格式化推送消息
    print("\n📝 [步骤 3/5] 格式化推送消息...")
    try:
        formatter = PushFormatter()

        # 分组
        breaking_activities = [a for a in judged_activities if a.get('level') == 'breaking']
        important_activities = [a for a in judged_activities if a.get('level') == 'important']
        normal_activities = [a for a in judged_activities if a.get('level') == 'normal']

        # 格式化重磅消息
        if breaking_activities:
            print(f"\n🔴 重磅消息 ({len(breaking_activities)} 条):")
            for activity in breaking_activities[:2]:
                print(f"   • {activity.get('title', 'N/A')[:60]}...")

        # 格式化重要消息
        if important_activities:
            print(f"\n🟠 重要消息 ({len(important_activities)} 条):")
            for activity in important_activities[:3]:
                print(f"   • {activity.get('title', 'N/A')[:60]}...")

        # 格式化普通消息
        if normal_activities:
            print(f"\n🟡 普通消息 ({len(normal_activities)} 条):")
            for activity in normal_activities[:3]:
                print(f"   • {activity.get('title', 'N/A')[:60]}...")

    except Exception as e:
        print(f"❌ 格式化失败: {e}")
        import traceback
        traceback.print_exc()
        return

    # 步骤 4: 发送 Telegram 测试消息
    print("\n📡 [步骤 4/5] 发送 Telegram 测试消息...")
    try:
        # 从配置文件读取 Telegram 配置
        import json
        with open("config/config.json", 'r') as f:
            config = json.load(f)

        telegram_config = config.get('telegram', {})
        bot_token = telegram_config.get('botToken', '')
        chat_id = telegram_config.get('chatId', '')

        # 初始化 Telegram 客户端
        telegram_client = TelegramTester(bot_token, chat_id)

        # 发送重磅消息
        if breaking_activities:
            msg = formatter.format_breaking(breaking_activities[:1])
            msg = add_test_disclaimer(msg)  # 添加免责声明

            print(f"\n📤 发送重磅消息（带免责声明）...")
            result = telegram_client.send_message(msg)

            if result.get('success'):
                print(f"✅ 重磅消息发送成功！")
            else:
                print(f"❌ 发送失败: {result.get('error', 'Unknown')}")

        # 发送汇总消息
        if important_activities or normal_activities:
            print(f"\n📤 发送汇总消息（带免责声明）...")

            # 生成汇总
            message = f"""🧪 <b>SV Alpha Radar - 测试推送（无 GitHub）</b>

📅 <b>测试时间:</b> 2026-03-09 11:55

⚠️ <b>警告：</b> 以下是虚构的测试数据，不代表真实事件！

📈 <b>统计信息:</b>
   🔴 重磅: {len(breaking_activities)}
   🟠 重要: {len(important_activities)}
   🟡 普通: {len(normal_activities)}
   📊 总计: {len(judged_activities)}

<b>📊 数据源:</b>
   • Reddit
   • Hacker News
   • Twitter

<b>🔥 测试消息示例:</b>
"""

            for activity in breaking_activities[:3]:
                message += f"• {activity.get('title', 'N/A')}\n"

            if important_activities:
                message += f"\n<b>📋 重要消息示例:</b>\n"
                for activity in important_activities[:3]:
                    message += f"• {activity.get('title', 'N/A')}\n"

            message += add_test_disclaimer("")  # 添加免责声明

            result = telegram_client.send_message(message)

            if result.get('success'):
                print(f"✅ 汇总消息发送成功！")
            else:
                print(f"❌ 发送失败: {result.get('error', 'Unknown')}")

    except Exception as e:
        print(f"❌ 推送失败: {e}")
        import traceback
        traceback.print_exc()

    # 步骤 5: 显示功能说明
    print("\n📋 [步骤 5/5] 功能说明...")
    print("\n✅ 推送功能测试完成！")
    print("\n📚 工作流程:")
    print("   1. 从数据库收集活动（Reddit, Hacker News, Twitter）")
    print("   2. 信息判断层分级（🔴🟠🟡）")
    print("   3. 添加到对应队列")
    print("   4. 定时推送（立即/每小时/每3小时）")
    print("   5. Telegram 推送")
    print("\n🎯 重要说明:")
    print("   • 推送系统只推送真实数据源的活动")
    print("   • 数据源：Reddit, Hacker News, Twitter（已移除 GitHub）")
    print("   • 所有推送都来自这些官方渠道")
    print("   • 测试时使用虚构数据，明确标注【测试消息】")

    # 完成
    print("\n" + "=" * 80)
    print("✅ 测试完成")
    print("=" * 80)
    print("\n📱 请检查 Telegram 是否收到测试消息（已标注【测试消息】）")
    print("\n🚀 系统准备好运行，将推送真实的数据源活动！")


if __name__ == "__main__":
    main()
