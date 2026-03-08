"""
简化测试：仅测试 GitHub 收集
避免 Twitter 相关依赖问题
"""

import os
import sys
from datetime import datetime

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.abspath(__file__))
src_root = os.path.join(project_root, 'src')
sys.path.insert(0, project_root)
sys.path.insert(0, src_root)

from collectors.github_monitor import GitHubMonitor

def main():
    """测试 GitHub 收集"""
    print("\n" + "=" * 80)
    print("🎯 Silicon Valley Alpha Radar - GitHub 收集测试")
    print("=" * 80)

    try:
        # 初始化监控器
        monitor = GitHubMonitor("config/config.json")

        # 收集最近 30 天的数据
        print(f"\n📊 收集 GitHub 活动（最近 30 天）...")
        activities = monitor.monitor_all_repos(days=30)

        print(f"\n✅ 成功收集 {len(activities)} 条 GitHub 活动")

        # 显示前 5 条
        print("\n📋 最新活动（前 5 条）：")
        for i, activity in enumerate(activities[:5], 1):
            print(f"\n{i}. {activity.get('repo_name', 'Unknown')}")
            print(f"   类型: {activity.get('event_type', 'Unknown')}")
            print(f"   时间: {activity.get('created_at', 'Unknown')}")
            print(f"   描述: {activity.get('description', 'No description')[:100]}...")

        print("\n" + "=" * 80)
        print("✅ 测试成功！")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
