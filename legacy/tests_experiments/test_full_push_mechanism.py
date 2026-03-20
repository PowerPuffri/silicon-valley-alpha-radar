"""
完整测试脚本 - 测试整个推送机制流程
1. 收集数据
2. 判断级别
3. 添加到队列
4. 格式化推送
"""

import os
import sys

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

from collectors.github_monitor import GitHubMonitor
from judges.info_judge import InfoJudge
from queues.push_queue_manager import PushQueueManager
from formatters.push_formatter import PushFormatter


def test_full_workflow():
    """测试完整工作流程"""
    print("\n" + "=" * 70)
    print("🧪 Silicon Valley Alpha Radar - 完整推送机制测试")
    print("=" * 70)

    # 1. 收集数据
    print("\n📊 [步骤 1/5] 收集 GitHub 数据...")
    try:
        github_monitor = GitHubMonitor("config/config.json")
        activities = github_monitor.monitor_all_repos(days=3)
        print(f"✅ 收集到 {len(activities)} 个活动")

        if len(activities) == 0:
            print("⚠️  没有收集到数据，使用模拟数据...")

            # 使用模拟数据
            activities = [
                {
                    'id': 1,
                    'activity_type': 'release',
                    'repo_name': 'openai/gpt-5',
                    'author': 'sama',
                    'title': 'GPT-5 Technical Preview Released',
                    'description': 'Breaking: We are excited to announce GPT-5, a revolutionary AGI breakthrough with unprecedented capabilities.',
                    'timestamp': '2026-03-09T10:00:00Z',
                    'url': 'https://github.com/openai/gpt-5/releases',
                    'likes': 500,
                    'comments': 200
                },
                {
                    'id': 2,
                    'activity_type': 'pull_request',
                    'repo_name': 'deepmind/alpha',
                    'author': 'demishassabis',
                    'title': 'Optimize transformer architecture',
                    'description': 'Improvement: Add better attention mechanism and optimization improvements.',
                    'state': 'merged',
                    'timestamp': '2026-03-09T09:00:00Z',
                    'url': 'https://github.com/deepmind/alpha/pull/123',
                    'likes': 50,
                    'comments': 20
                },
                {
                    'id': 3,
                    'activity_type': 'issue',
                    'repo_name': 'openai/whisper',
                    'author': 'randomuser',
                    'title': 'Bug in whisper model',
                    'description': 'There is a small bug in the whisper model.',
                    'timestamp': '2026-03-09T08:00:00Z',
                    'url': 'https://github.com/openai/whisper/issues/456',
                    'likes': 2,
                    'comments': 1
                },
                {
                    'id': 4,
                    'activity_type': 'discussion',
                    'repo_name': 'anthropic/claude',
                    'author': 'ilyasut',
                    'title': 'New embedding approach',
                    'description': 'Paper: A novel approach to embeddings using mixture-of-experts.',
                    'timestamp': '2026-03-09T07:00:00Z',
                    'url': 'https://github.com/anthropic/claude/discussions/789',
                    'likes': 30,
                    'comments': 10
                },
                {
                    'id': 5,
                    'activity_type': 'comment',
                    'repo_name': 'unknown/repo',
                    'author': 'randomuser',
                    'title': 'Random comment',
                    'description': 'Just a random comment without much value.',
                    'timestamp': '2026-03-09T06:00:00Z',
                    'url': 'https://github.com/unknown/repo/issues/111',
                    'likes': 0,
                    'comments': 0
                }
            ]

            print(f"📋 使用 {len(activities)} 个模拟活动")

    except Exception as e:
        print(f"❌ 数据收集失败: {e}")
        import traceback
        traceback.print_exc()
        return

    # 2. 判断级别
    print("\n🔍 [步骤 2/5] 判断信息级别...")
    try:
        judge = InfoJudge("config/push_config.json")
        judged_activities = judge.judge_activities_batch(activities)

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

    # 3. 添加到队列
    print("\n📥 [步骤 3/5] 添加到推送队列...")
    try:
        queue_manager = PushQueueManager("config/push_config.json", "storage/data/push_queue_test.db")

        for activity in judged_activities:
            level = activity.get('level', 'ignore')
            if level != 'ignore':
                success = queue_manager.add_to_queue(activity, level)
                if success:
                    print(f"✅ 已添加 [{level.upper()}] {activity.get('title', 'N/A')[:40]}...")

    except Exception as e:
        print(f"❌ 添加队列失败: {e}")
        import traceback
        traceback.print_exc()
        return

    # 4. 格式化推送消息
    print("\n📝 [步骤 4/5] 格式化推送消息...")
    try:
        formatter = PushFormatter()

        # 分组
        breaking_activities = [a for a in judged_activities if a.get('level') == 'breaking']
        important_activities = [a for a in judged_activities if a.get('level') == 'important']
        normal_activities = [a for a in judged_activities if a.get('level') == 'normal']

        # 格式化
        print(f"\n🔴 重磅消息示例:")
        if breaking_activities:
            msg = formatter.format_breaking(breaking_activities[:1])
            print("-" * 70)
            print(msg)
            print("-" * 70)
        else:
            print("   (无)")

        print(f"\n🟠 重要消息示例:")
        if important_activities:
            msg = formatter.format_important_batch(important_activities)
            print("-" * 70)
            print(msg)
            print("-" * 70)
        else:
            print("   (无)")

        print(f"\n🟡 普通消息示例:")
        if normal_activities:
            msg = formatter.format_normal_batch(normal_activities)
            print("-" * 70)
            print(msg)
            print("-" * 70)
        else:
            print("   (无)")

    except Exception as e:
        print(f"❌ 格式化失败: {e}")
        import traceback
        traceback.print_exc()
        return

    # 5. 显示队列状态
    print("\n📊 [步骤 5/5] 队列状态...")
    try:
        status = queue_manager.get_queue_status()
        print(f"   🔴 紧急队列: {status['urgent_queue_size']}")
        print(f"   🟠 每小时队列: {status['hourly_queue_size']}")
        print(f"   🟡 普通队列: {status['normal_queue_size']}")
        print(f"   📋 总计排队: {status['stats']['total_queued']}")

    except Exception as e:
        print(f"❌ 获取状态失败: {e}")

    # 清理
    print("\n🧹 清理测试数据库...")
    queue_manager.stop()
    import os
    if os.path.exists("storage/data/push_queue_test.db"):
        os.remove("storage/data/push_queue_test.db")
        print("✅ 测试数据库已删除")

    # 完成
    print("\n" + "=" * 70)
    print("✅ 完整推送机制测试完成！")
    print("=" * 70)


if __name__ == "__main__":
    test_full_workflow()
