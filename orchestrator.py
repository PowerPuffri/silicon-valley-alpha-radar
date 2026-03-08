"""
Orchestrator - 协调所有模块的执行和数据流动
负责调度数据收集、分析和报告生成
"""

import os
import sys
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.abspath(__file__))
src_root = os.path.join(project_root, 'src')
sys.path.insert(0, project_root)
sys.path.insert(0, src_root)

from collectors.github_monitor import GitHubMonitor

# Twitter 收集器（根据配置动态导入）
TwitterCollector = None
JinaTwitterCollector = None
TwintCollector = None


class DataOrchestrator:
    def __init__(self, config_path: str = "config/config.json", use_twint: bool = False, use_jina: bool = True):
        """
        初始化数据编排器

        Args:
            config_path: 配置文件路径
            use_twint: 是否使用 twint 替代 Twitter API（默认 False）
            use_jina: 是否使用 jina-cli 替代 Twitter API（默认 True）
        """
        self.config_path = config_path
        self.config = self._load_config()
        self.use_twint = use_twint
        self.use_jina = use_jina

        # 初始化 GitHub 监控器
        self.github_monitor = GitHubMonitor(config_path)

        # 动态导入 Twitter 收集器
        self.twitter_collector = None
        self.jina_twitter_collector = None
        self.twint_collector = None

        # 初始化 Jina 收集器
        if self.use_jina:
            try:
                from collectors.jina_twitter_collector import JinaTwitterCollector
                self.jina_twitter_collector = JinaTwitterCollector(config_path)
                print("✅ Jina Twitter Collector 已加载")
            except ImportError as e:
                print(f"⚠️  JinaTwitterCollector 导入失败: {e}")
                self.use_jina = False

        # 如果使用 twint，延迟导入
        if use_twint:
            try:
                from collectors.twint_collector import TwintCollector
                self.twint_collector = TwintCollector(config_path)
                print("✅ Twint Collector 已加载")
            except ImportError:
                print("⚠️  TwintCollector 导入失败，将使用 Jina")
                self.use_twint = False

        # 如果都不使用，尝试加载 Twitter API 收集器
        if not self.use_jina and not self.use_twint:
            try:
                from collectors.twitter_collector import TwitterCollector
                self.twitter_collector = TwitterCollector(config_path)
                print("✅ Twitter API Collector 已加载")
            except ImportError as e:
                print(f"⚠️  TwitterCollector 导入失败: {e}")

        # 初始化存储目录
        self.storage_data = "storage/data"
        self.storage_processed = "storage/processed"
        self.output_reports = "output/reports"

        # 确保目录存在
        self._init_directories()

    def _load_config(self) -> Dict:
        """加载配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"配置文件未找到: {self.config_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"配置文件格式错误: {e}")

    def _init_directories(self):
        """初始化必要的目录"""
        directories = [
            self.storage_data,
            self.storage_processed,
            self.output_reports,
            "config",
            "src/collectors",
            "src/analyzers",
            "src/generators"
        ]

        for directory in directories:
            full_path = os.path.join(project_root, directory)
            os.makedirs(full_path, exist_ok=True)

    def collect_all_data(self, days: int = 7):
        """
        收集所有数据源的数据

        Args:
            days: 收集最近多少天的数据

        Returns:
            收集的数据摘要
        """
        print("\n" + "=" * 80)
        print("🎯 Silicon Valley Alpha Radar - 数据收集流程")
        print("=" * 80)

        # 确定使用模式
        if self.use_jina:
            mode = "Jina CLI (开源推荐)"
        elif self.use_twint:
            mode = "Twint (开源)"
        else:
            mode = "Twitter API (官方)"

        print(f"\n📌 使用模式: {mode}")

        summary = {
            'start_time': datetime.now(),
            'twitter_posts': 0,
            'github_activities': 0,
            'errors': [],
            'collector_mode': 'jina' if self.use_jina else ('twint' if self.use_twint else 'api')
        }

        try:
            # 1. 收集 Twitter 数据
            print(f"\n📱 [1/3] 收集 Twitter 推文（最近 {days} 天）...")
            if self.use_jina and hasattr(self, 'jina_twitter_collector'):
                twitter_posts = self.jina_twitter_collector.collect_all_accounts(days=days)
                summary['twitter_posts'] = len(twitter_posts)
            elif self.use_twint and hasattr(self, 'twint_collector'):
                twitter_posts = self.twint_collector.collect_all_accounts(days=days)
                summary['twitter_posts'] = len(twitter_posts)
            else:
                twitter_posts = self.twitter_collector.collect_all_accounts(days=days)
                summary['twitter_posts'] = len(twitter_posts)

            # 2. 收集 GitHub 数据
            print(f"\n📊 [2/3] 收集 GitHub 活动（最近 {days} 天）...")
            github_activities = self.github_monitor.monitor_all_repos(days=days)
            summary['github_activities'] = len(github_activities)

            # 3. 保存数据摘要
            self._save_collection_summary(summary)

            summary['end_time'] = datetime.now()
            summary['duration'] = (summary['end_time'] - summary['start_time']).total_seconds()

            # 显示摘要
            self._display_summary(summary)

        except Exception as e:
            print(f"\n❌ 数据收集失败: {e}")
            import traceback
            traceback.print_exc()
            summary['errors'].append(str(e))
            return summary

        return summary

    def _save_collection_summary(self, summary: Dict):
        """保存数据收集摘要"""
        summary_file = os.path.join(
            self.output_reports,
            f"collection_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )

        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False, default=str)

        print(f"\n✅ 数据收集摘要已保存到: {summary_file}")

    def _display_summary(self, summary: Dict):
        """显示数据收集摘要"""
        print("\n" + "=" * 80)
        print("📊 数据收集摘要")
        print("=" * 80)

        print(f"\n📱 Twitter 推文:")
        print(f"   总数: {summary['twitter_posts']}")
        print(f"   模式: {summary.get('collector_mode', 'unknown')}")

        print(f"\n📊 GitHub 活动:")
        print(f"   总数: {summary['github_activities']}")

        print(f"\n⏱️  耗时: {summary['duration']:.2f} 秒")

        if summary['errors']:
            print(f"\n❌ 错误: {len(summary['errors'])}")
            for error in summary['errors']:
                print(f"   - {error}")

        print("=" * 80)


def main():
    """主程序"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Silicon Valley Alpha Radar - 数据收集和编排"
    )
    parser.add_argument('--days', type=int, default=7, help="收集最近多少天的数据 (默认: 7)")
    parser.add_argument('--twitter-only', action='store_true', help='只收集 Twitter 数据')
    parser.add_argument('--github-only', action='store_true', help='只收集 GitHub 数据')
    parser.add_argument('--stats', action='store_true', help='显示最近统计信息')
    parser.add_argument('--use-twint', action='store_true',
                    help='使用 twint 开源工具替代 Twitter API（免费但较慢）')
    parser.add_argument('--use-jina', action='store_true', default=True,
                    help='使用 jina-cli 替代 Twitter API（推荐，完全免费）')

    args = parser.parse_args()

    # 初始化编排器
    try:
        orchestrator = DataOrchestrator(
            use_twint=args.use_twint,
            use_jina=args.use_jina
        )

        if args.stats:
            # 显示统计信息
            print("\n📊 最近 24 小时统计:")
            if orchestrator.use_jina and hasattr(orchestrator, 'jina_twitter_collector'):
                twitter_stats = orchestrator.jina_twitter_collector.get_recent_stats(hours=24)
                print(f"\nTwitter 推文:")
                print(f"   总数: {twitter_stats['total_tweets']}")
                print(f"   低关注度推文: {twitter_stats['low_engagement_tweets']}")
                print(f"   活跃账号数: {twitter_stats['active_handles']}")
                print(f"   统计周期: {twitter_stats['period_hours']} 小时")
            else:
                twitter_stats = orchestrator.twitter_collector.get_recent_stats(hours=24)
                print(f"\nTwitter 推文:")
                print(f"   总数: {twitter_stats['total_tweets']}")
                print(f"   低关注度推文: {twitter_stats['low_engagement_tweets']}")
                print(f"   活跃账号数: {twitter_stats['active_handles']}")
                print(f"   统计周期: {twitter_stats['period_hours']} 小时")

        else:
            # 执行数据收集
            if args.twitter_only:
                print("\n📱 仅收集 Twitter 数据...")
                if args.use_jina and hasattr(orchestrator, 'jina_twitter_collector'):
                    summary = {
                        'start_time': datetime.now(),
                        'twitter_posts': len(orchestrator.jina_twitter_collector.collect_all_accounts(days=args.days)),
                        'github_activities': 0,
                        'errors': [],
                        'end_time': datetime.now(),
                        'collector_mode': 'jina'
                    }
                elif args.use_twint and hasattr(orchestrator, 'twint_collector'):
                    summary = {
                        'start_time': datetime.now(),
                        'twitter_posts': len(orchestrator.twint_collector.collect_all_accounts(days=args.days)),
                        'github_activities': 0,
                        'errors': [],
                        'end_time': datetime.now(),
                        'collector_mode': 'twint'
                    }
                else:
                    summary = {
                        'start_time': datetime.now(),
                        'twitter_posts': len(orchestrator.twitter_collector.collect_all_accounts(days=args.days)),
                        'github_activities': 0,
                        'errors': [],
                        'end_time': datetime.now(),
                        'collector_mode': 'api'
                    }
                summary['duration'] = (summary['end_time'] - summary['start_time']).total_seconds()
                orchestrator._display_summary(summary)

            elif args.github_only:
                print("\n📊 仅收集 GitHub 数据...")
                summary = {
                    'start_time': datetime.now(),
                    'twitter_posts': 0,
                    'github_activities': len(orchestrator.github_monitor.monitor_all_repos(days=args.days)),
                    'errors': [],
                    'end_time': datetime.now(),
                    'collector_mode': 'github'
                }
                summary['duration'] = (summary['end_time'] - summary['start_time']).total_seconds()
                orchestrator._display_summary(summary)

            else:
                # 收集所有数据
                orchestrator.collect_all_data(days=args.days)

    except Exception as e:
        print(f"\n❌ 程序错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
