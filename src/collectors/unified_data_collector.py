"""
统一数据收集器 - 按照优先级收集所有数据源
"""

import os
import sys
from datetime import datetime, timedelta
from typing import List, Dict
from collections import Counter

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))
sys.path.insert(0, os.path.join(project_root, 'src', 'collectors'))
sys.path.insert(0, os.path.join(project_root, 'config'))

from data_sources_config import DATA_SOURCES_CONFIG, calculate_priority


class UnifiedDataCollector:
    def __init__(self, days: int = 7):
        """
        初始化统一数据收集器

        Args:
            days: 收集最近多少天的数据
        """
        self.days = days

        # 初始化各收集器
        self.twitter_collector = None
        self.blog_collector = None
        self.github_collector = None

        # 尝试加载收集器
        try:
            from twitter_collector import TwitterCollector
            self.twitter_collector = TwitterCollector()
            self.twitter_available = True
            print("✅ Twitter 收集器已加载")
        except Exception as e:
            self.twitter_available = False
            print(f"⚠️  Twitter 收集器不可用: {e}")

        try:
            from official_blog_collector import OfficialBlogCollector
            self.blog_collector = OfficialBlogCollector()
            self.blog_available = True
            print("✅ 官方博客收集器已加载")
        except Exception as e:
            self.blog_available = False
            print(f"⚠️  官方博客收集器不可用: {e}")

        try:
            from github_release_collector import GitHubReleaseCollector
            self.github_collector = GitHubReleaseCollector()
            self.github_available = True
            print("✅ GitHub Release 收集器已加载")
        except Exception as e:
            self.github_available = False
            print(f"⚠️  GitHub Release 收集器不可用: {e}")

        # 社区数据（Hacker News, Reddit）已收集
        print("✅ Hacker News 和 Reddit 数据已从之前收集（99 条 HN）")

    def collect_all_data(self) -> List[Dict]:
        """
        按照优先级顺序收集所有数据源

        Returns:
            统一格式的事件列表
        """
        print("\n" + "=" * 80)
        print(f"🚀 Silicon Valley Alpha Radar - 统一数据收集（最近 {self.days} 天）")
        print("=" * 80)

        all_events = []

        # 1. Twitter (优先级最高)
        if self.twitter_available:
            print(f"\n🟦 [优先级 1/3] 收集 X (Twitter) 数据...")
            try:
                tweets = self.twitter_collector.collect_all_twitter(days=self.days)
                all_events.extend(tweets)
                print(f"   ✅ Twitter: {len(tweets)} 条")
            except Exception as e:
                print(f"   ❌ Twitter 收集失败: {e}")

        # 2. 官方博客
        if self.blog_available:
            print(f"\n🏢 [优先级 2/3] 收集官方博客数据...")
            try:
                blogs = self.blog_collector.collect_all_blogs(days=self.days)
                all_events.extend(blogs)
                print(f"   ✅ 官方博客: {len(blogs)} 篇")
            except Exception as e:
                print(f"   ❌ 官方博客收集失败: {e}")

        # 3. GitHub Releases
        if self.github_available:
            print(f"\n🔗 [优先级 3/3] 收集 GitHub Releases...")
            try:
                releases = self.github_collector.collect_all_releases(days=self.days)
                all_events.extend(releases)
                print(f"   ✅ GitHub Releases: {len(releases)} 个")
            except Exception as e:
                print(f"   ❌ GitHub Releases 收集失败: {e}")

        # 4. 社区数据（已收集）
        print(f"\n📊 [补充] 添加社区数据（Hacker News, Reddit）...")
        try:
            community_events = self._load_community_data()
            all_events.extend(community_events)
            print(f"   ✅ 社区数据: {len(community_events)} 条")
        except Exception as e:
            print(f"   ❌ 社区数据加载失败: {e}")

        # 计算优先级
        print(f"\n📊 [排序] 计算信息优先级...")
        prioritized_events = self._prioritize_events(all_events)

        # 显示统计
        self._display_statistics(all_events, prioritized_events)

        return prioritized_events

    def _load_community_data(self) -> List[Dict]:
        """
        加载之前收集的社区数据（Hacker News, Reddit）

        Returns:
            社区事件列表
        """
        import sqlite3

        community_events = []

        # Hacker News
        try:
            hn_db = "storage/data/hacker_news.db"
            if os.path.exists(hn_db):
                conn = sqlite3.connect(hn_db)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute('SELECT * FROM hackernews ORDER BY time DESC')
                hn_events = [dict(row) for row in cursor.fetchall()]

                for event in hn_events:
                    # 转换为统一格式
                    unified_event = {
                        'id': f"hn_{event['id']}",
                        'source_type': 'community',
                        'source': 'Hacker News',
                        'activity_type': 'story',
                        'title': event.get('title', ''),
                        'description': event.get('text', event.get('url', ''))[:200],
                        'author': event.get('by', 'unknown'),
                        'url': f"https://news.ycombinator.com/item?id={event['id']}",
                        'score': event.get('score', 0),
                        'comments': event.get('descendants', 0),
                        'timestamp': event.get('time', datetime.now().isoformat()),
                        '_converted': True
                    }
                    community_events.append(unified_event)

                conn.close()
        except Exception as e:
            print(f"   ⚠️  Hacker News 数据加载失败: {e}")

        # Reddit（如果有的话）
        try:
            reddit_db = "storage/data/reddit_posts.db"
            if os.path.exists(reddit_db):
                conn = sqlite3.connect(reddit_db)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                # 获取表名
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]

                if tables:
                    table_name = tables[0]
                    cursor.execute(f'SELECT * FROM {table_name} ORDER BY created_at DESC')
                    reddit_events = [dict(row) for row in cursor.fetchall()]

                    for event in reddit_events:
                        unified_event = {
                            'id': f"reddit_{hash(str(event))}",
                            'source_type': 'community',
                            'source': event.get('subreddit', 'Reddit'),
                            'activity_type': 'post',
                            'title': event.get('title', ''),
                            'description': event.get('selftext', event.get('url', ''))[:200],
                            'author': event.get('author', 'unknown'),
                            'url': f"https://www.reddit.com{event.get('permalink', '')}",
                            'score': event.get('score', 0),
                            'comments': event.get('num_comments', 0),
                            'timestamp': event.get('created_at', datetime.now().isoformat()),
                            '_converted': True
                        }
                        community_events.append(unified_event)

                    conn.close()
        except Exception as e:
            print(f"   ⚠️  Reddit 数据加载失败: {e}")

        return community_events

    def _prioritize_events(self, events: List[Dict]) -> List[Dict]:
        """
        按照优先级排序事件

        Args:
            events: 事件列表

        Returns:
            排序后的事件列表
        """
        print(f"   📊 计算优先级: {len(events)} 个事件")

        # 为每个事件计算优先级
        for event in events:
            try:
                # 使用配置中的优先级计算函数
                event['priority_score'] = calculate_priority(event)
            except Exception as e:
                print(f"      ⚠️  计算优先级失败: {e}")
                event['priority_score'] = 0

        # 按优先级分数排序
        prioritized = sorted(events, key=lambda x: x.get('priority_score', 0), reverse=True)

        print(f"   ✅ 优先级计算完成")

        return prioritized

    def _display_statistics(self, all_events: List[Dict], prioritized: List[Dict]):
        """
        显示统计信息

        Args:
            all_events: 所有事件
            prioritized: 排序后的事件
        """
        print(f"\n📊 数据统计:")
        print(f"   总事件数: {len(all_events)}")

        # 按来源类型统计
        source_types = [e.get('source_type', 'unknown') for e in all_events]
        type_count = Counter(source_types)

        print(f"\n📊 按来源类型:")
        for source_type, count in type_count.most_common():
            print(f"   • {source_type}: {count} 条")

        # 显示前 20 个最高优先级事件
        print(f"\n🔥 高优先级事件 (Top 20):")
        for i, event in enumerate(prioritized[:20], 1):
            score = event.get('priority_score', 0)
            title = event.get('title', event.get('content', ''))[:60]
            source = event.get('source', event.get('handle', event.get('company', '')))

            print(f"\n   [{i}] 优先级: {score}")
            print(f"      📦 {source}")
            print(f"      📄 {title}...")
            print(f"      🕐 {event.get('timestamp', 'N/A')}")

        # 按优先级分组统计
        print(f"\n📊 按优先级分组:")
        high_priority = len([e for e in prioritized if e.get('priority_score', 0) >= 100])
        medium_priority = len([e for e in prioritized if 50 <= e.get('priority_score', 0) < 100])
        low_priority = len([e for e in prioritized if e.get('priority_score', 0) < 50])

        print(f"   🔴 高优先级 (>=100): {high_priority}")
        print(f"   🟠 中优先级 (50-99): {medium_priority}")
        print(f"   🟡 低优先级 (<50): {low_priority}")


def main():
    """主程序"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Silicon Valley Alpha Radar - 统一数据收集器"
    )
    parser.add_argument('--days', type=int, default=7, help='收集最近多少天的数据 (默认: 7)')
    parser.add_argument('--save', action='store_true', help='保存到数据库')

    args = parser.parse_args()

    # 创建收集器
    try:
        collector = UnifiedDataCollector(days=args.days)
        events = collector.collect_all_data()

        # 保存到数据库（如果需要）
        if args.save:
            print(f"\n💾 保存到数据库...")
            _save_to_unified_db(events)

        print(f"\n✅ 数据收集完成！")

    except Exception as e:
        print(f"\n❌ 数据收集失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def _save_to_unified_db(events: List[Dict], db_path: str = "storage/data/unified_activities.db"):
    """
    保存到统一数据库

    Args:
        events: 事件列表
        db_path: 数据库路径
    """
    import sqlite3

    print(f"\n💾 保存到统一数据库...")

    # 初始化数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS activities (
            id TEXT PRIMARY KEY,
            source_type TEXT,
            source TEXT,
            activity_type TEXT,
            title TEXT,
            description TEXT,
            author TEXT,
            url TEXT,
            score INTEGER DEFAULT 0,
            comments INTEGER DEFAULT 0,
            timestamp TEXT,
            priority_score INTEGER,
            collected_at TEXT
        )
    ''')

    conn.commit()

    # 清空旧数据
    cursor.execute('DELETE FROM activities')
    conn.commit()

    # 插入数据
    saved_count = 0
    for event in events:
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO activities
                (id, source_type, source, activity_type, title, description, author, url,
                 score, comments, timestamp, priority_score, collected_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                event.get('id', str(hash(str(event)))),
                event.get('source_type', 'unknown'),
                event.get('source', 'unknown'),
                event.get('activity_type', 'unknown'),
                event.get('title', ''),
                event.get('description', '')[:500],
                event.get('author', ''),
                event.get('url', ''),
                event.get('score', 0),
                event.get('comments', 0),
                event.get('timestamp', datetime.now().isoformat()),
                event.get('priority_score', 0),
                datetime.now().isoformat()
            ))

            saved_count += 1
        except Exception as e:
            print(f"   ⚠️  保存事件失败: {e}")

    conn.commit()
    conn.close()

    print(f"   ✅ 已保存 {saved_count} 条事件到数据库")


if __name__ == "__main__":
    main()
