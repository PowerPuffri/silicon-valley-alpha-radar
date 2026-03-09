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
from collectors.twitter_collector import TwitterCollector
from collectors.jina_twitter_collector import JinaTwitterCollector
# 新的数据源
from collectors.redditor_collector import RedditCollector
from collectors.hackernews_collector import HackerNewsCollector


class DataOrchestrator:
    def __init__(self, config_path: str = "config/config.json", use_jina: bool = True, use_reddit: bool = False, use_hackernews: bool = False):
        """
        初始化数据编排器

        Args:
            config_path: 配置文件路径
            use_jina: 是否使用 jina-cli 替代 Twitter API（默认 True）
            use_reddit: 是否使用 Reddit（默认 False）
            use_hackernews: 是否使用 Hacker News（默认 False）
        """
        self.config_path = config_path
        self.config = self._load_config()
        self.use_jina = use_jina
        self.use_reddit = use_reddit
        self.use_hackernews = use_hackernews

        # 初始化 GitHub 监控器
        self.github_monitor = GitHubMonitor(config_path)

        # 初始化数据源
        self.jina_twitter_collector = None
        self.reddit_collector = None
        self.hackernews_collector = None

        # 初始化 Jina 收集器
        if self.use_jina:
            try:
                from collectors.jina_twitter_collector import JinaTwitterCollector
                self.jina_twitter_collector = JinaTwitterCollector(config_path)
                print("✅ Jina Twitter Collector 已加载")
            except ImportError as e:
                print(f"⚠️  JinaTwitterCollector 导入失败: {e}")
                self.use_jina = False

        # 初始化 Reddit 收集器
        if self.use_reddit:
            try:
                from collectors.redditor_collector import RedditCollector
                self.reddit_collector = RedditCollector(config_path)
                print("✅ Reddit Collector 已加载")
            except ImportError as e:
                print(f"⚠️  Reddit Collector 导入失败: {e}")
                self.use_reddit = False

        # 初始化 Hacker News 收集器
        if self.use_hackernews:
            try:
                from collectors.hackernews_collector import HackerNewsCollector
                self.hackernews_collector = HackerNewsCollector(config_path)
                print("✅ Hacker News Collector 已加载")
            except ImportError as e:
                print(f"⚠️  Hacker News Collector 导入失败: {e}")
                self.use_hackernews = False

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

    def collect_all_data(self, days: int = 7) -> Dict:
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
        mode = "Jina CLI (推荐)"
        if self.use_reddit:
            mode += " + Reddit"
        if self.use_hackernews:
            mode += " + Hacker News"

        print(f"\n📌 使用模式: {mode}")

        summary = {
            'start_time': datetime.now(),
            'github_posts': 0,
            'reddit_posts': 0,
            'hackernews_stories': 0,
            'twitter_posts': 0,
            'jina_twitter_posts': 0,
            'errors': []
        }

        try:
            # 1. 收集 GitHub 数据
            print(f"\n📊 [1/6] 收集 GitHub 活动（最近 {days} 天）...")
            github_activities = self.github_monitor.monitor_all_repos(days=days)
            summary['github_posts'] = len(github_activities)

            # 2. 收集 Reddit 数据
            if self.use_reddit and self.reddit_collector:
                print(f"\n📱 [2/6] 收集 Reddit 帖子（最近 {days} 天）...")
                reddit_posts = self.reddit_collector.collect_all_subreddits(days=days)
                summary['reddit_posts'] = len(reddit_posts)

            # 3. 收集 Hacker News 数据
            if self.use_hackernews and self.hackernews_collector:
                print(f"\n🕶️ [3/6] 收集 Hacker News 故事（最近 {days} 天）...")
                hackernews_stories = self.hackernews_collector.collect_all_stories(days=days)
                summary['hackernews_stories'] = len(hackernews_stories)

            # 4. 收集 Jina Twitter 数据（如果启用）
            if self.use_jina and self.jina_twitter_collector:
                print(f"\n📱 [4/6] 收集 Jina Twitter 推文（最近 {days} 天）...")
                jina_twitter_posts = self.jina_twitter_collector.collect_all_accounts(days=days)
                summary['jina_twitter_posts'] = len(jina_twitter_posts)

            # 5. 保存数据摘要
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

        print(f"\n📊 GitHub 活动:")
        print(f"   总数: {summary['github_posts']}")

        if summary['reddit_posts'] > 0:
            print(f"\n📱 Reddit 帖子:")
            print(f"   总数: {summary['reddit_posts']}")

        if summary['hackernews_stories'] > 0:
            print(f"\n🕶️ Hacker News 故事:")
            print(f"   总数: {summary['hackernews_stories']}")

        if summary['jina_twitter_posts'] > 0:
            print(f"\n📱 Jina Twitter 推文:")
            print(f"   总数: {summary['jina_twitter_posts']}")

        total_data_sources = 1  # GitHub
        if summary['reddit_posts'] > 0:
            total_data_sources += 1
        if summary['hackernews_stories'] > 0:
            total_data_sources += 1
        if summary['jina_twitter_posts'] > 0:
            total_data_sources += 1

        print(f"\n📊 数据源总数: {total_data_sources}")

        print(f"\n⏱️  耗时时间: {summary['duration']:.2f} 秒")

        if summary['errors']:
            print(f"\n❌ 错误: {len(summary['errors'])}")
            for error in summary['errors']:
                print(f"   - {error}")

        print("=" * 80)

    def collect_reddit_only(self, days: int = 7) -> Dict:
        """只收集 Reddit 数据"""
        if not self.use_reddit or not self.reddit_collector:
            print("⚠️  Reddit Collector 未启用，无法收集")
            return {
                'start_time': datetime.now(),
                'reddit_posts': 0,
                'errors': ['Reddit collector not enabled']
            }

        print(f"\n📱 [1/1] 收集 Reddit 帖子（最近 {days} 天）...")
        reddit_posts = self.reddit_collector.collect_all_subreddits(days=days)

        summary = {
            'start_time': datetime.now(),
            'reddit_posts': len(reddit_posts),
            'errors': []
        }

        self._display_summary(summary)
        return summary

    def collect_hackernews_only(self, days: int = 7) -> Dict:
        """只收集 Hacker News 数据"""
        if not self.use_hackernews or not self.hackernews_collector:
            print("⚠️  Hacker News Collector 未启用，无法收集")
            return {
                'start_time': datetime.now(),
                'hackernews_stories': 0,
                "errors": ['Hacker News collector not enabled']
            }

        print(f"\n🕶️ [1/1] 收集 Hacker News 故事（最近 {days} 天）...")
        stories = self.hackernews_collector.collect_all_stories(days=days)

        summary = {
            'start_time': datetime.now(),
            'hackernews_stories': len(stories),
            'errors': []
        }

        self._display_summary(summary)
        return summary

    def collect_reddit_and_hackernews(self, days: int = 7) -> Dict:
        """收集 Reddit 和 Hacker News 数据"""
        if not self.use_reddit or not self.use_hackernews:
            print("⚠️  Reddit 和 Hacker News Collector 都未启用，无法收集")
            return {
                'start_time': datetime.now(),
                'reddit_posts': 0,
                'hackernews_stories': 0,
                'errors': ['Reddit and Hacker News collectors not enabled']
            }

        print(f"\n📱 [1/2] 收集 Reddit 帖子（最近 {days} 天）...")
        reddit_posts = self.reddit_collector.collect_all_subreddits(days=days)

        print(f"\n🕶️ [2/2] 收集 Hacker News 故事（最近 {days} 天）...")
        hackernews_stories = self.hackernews_collector.collect_all_stories(days=days)

        summary = {
            'start_time': datetime.now(),
            'reddit_posts': len(reddit_posts),
            'hackernews_stories': len(hackernews_stories),
            'errors': []
        }

        self._display_summary(summary)
        return summary


def main():
    """主程序"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Silicon Valley Alpha Radar - 数据收集和编排"
    )
    parser.add_argument('--days', type=int, default=7, help="收集最近多少天的数据 (默认: 7)")
    parser.add_argument('--github-only', action='store_true', help='只收集 GitHub 数据')
    parser.add_argument('--reddit-only', action='store_true', help='只收集 Reddit 数据')
    parser.add_argument('--hackernews-only', action='store_true', help='只收集 Hacker News 数据')
    parser.add_argument('--reddit-hackernews', action='store_true', help='收集 Reddit 和 Hacker News 数据')
    parser.add_argument('--stats', action='store_true', help='显示最近统计信息')

    args = parser.parse_args()

    # 初始化编排器
    try:
        orchestrator = DataOrchestrator()

        if args.stats:
            # 显示统计信息
            print("\n📊 所有数据源统计:")
            
            # GitHub 统计
            github_stats = orchestrator.github_monitor.get_recent_stats(hours=24)
            print(f"\n📊 GitHub 统计:")
            print(f"   总活动数: {github_stats['total_activities']}")
            print(f"   活跃仓库数: {github_stats['active_repos']}")
            print(f"   统计周期: {github_stats['period_hours']} 小时")

        elif args.github_only:
            # 只收集 GitHub 数据
            summary = orchestrator.collect_all_data(days=args.days)
            print(f"\n✅ GitHub 数据收集完成！")

        elif args.reddit_only:
            # 只收集 Reddit 数据
            summary = orchestrator.collect_reddit_only(days=args.days)
            print(f"\n✅ Reddit 数据收集完成！")

        elif args.hackernews_only:
            # 只收集 Hacker News 数据
            summary = orchestrator.collect_hackernews_only(days=args.days)
            print(f"\n✅ Hacker News 数据收集完成！")

        elif args.reddit_hackernews:
            # 收集 Reddit 和 Hacker News 数据
            summary = orchestrator.collect_reddit_and_hackernews(days=args.days)
            print(f"\n✅ Reddit 和 Hacker News 数据收集完成！")

        else:
            # 收集所有数据源
            summary = orchestrator.collect_all_data(days=args.days)
            print(f"\n✅ 所有数据源收集完成！")

    except Exception as e:
        print(f"\n❌ 程序错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
