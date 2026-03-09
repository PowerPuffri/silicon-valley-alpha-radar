"""
Twitter 收集器 - 收集官方账号和知名人物的推文
优先级最高的数据源
"""

import requests
from datetime import datetime, timedelta
from typing import List, Dict
import sys
import os

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'config'))

from data_sources_config import DATA_SOURCES_CONFIG


class TwitterCollector:
    def __init__(self):
        """初始化 Twitter 收集器"""
        self.accounts = DATA_SOURCES_CONFIG["x_accounts"]
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'
        })

    def fetch_from_rsshub(self, handle: str, account_info: Dict, days: int = 7) -> List[Dict]:
        """
        从 RSSHub 收集 Twitter 推文（推荐）

        Args:
            handle: Twitter 账号（@sama）
            account_info: 账号信息
            days: 收集最近多少天

        Returns:
            推文列表
        """
        print(f"   📡 从 RSSHub 收集 @{handle}...")

        tweets = []

        try:
            # RSSHub Twitter RSS URL
            rss_url = f"https://rsshub.app/{handle}"

            response = self.session.get(rss_url, timeout=10)
            response.raise_for_status()

            # 解析 RSS
            import feedparser
            feed = feedparser.parse(rss_url)

            for entry in feed.entries:
                # 检查时间
                published = entry.get('published_parsed')
                if not published:
                    continue

                if published < datetime.now() - timedelta(days=days):
                    continue

                # 提取信息
                tweet = {
                    'id': f"tweet_{handle}_{hash(entry.get('id', entry.get('link')))}",
                    'source_type': 'official_x' if account_info.get('priority') in ['P0', 'P1'] else 'notable_person',
                    'source': f"@{handle}",
                    'activity_type': 'tweet',
                    'title': entry.get('title', '')[:100],
                    'description': entry.get('summary', entry.get('description', ''))[:500],
                    'author': handle,
                    'url': entry.get('link', f"https://twitter.com/{handle}"),
                    'score': 0,  # Twitter 在 RSS 中没有原生分数
                    'comments': 0,  # RSS 中可能没有评论数
                    'timestamp': published.isoformat(),
                    'handle': handle,
                    'name': account_info.get('name', handle),
                    'company': account_info.get('company', ''),
                    'priority': account_info.get('priority', 'P2')
                }

                tweets.append(tweet)

            print(f"      ✅ 收集了 {len(tweets)} 条推文")

        except Exception as e:
            print(f"      ❌ RSSHub 收集失败: {e}")

        return tweets

    def collect_official_accounts(self, days: int = 7) -> List[Dict]:
        """
        收集官方账号推文

        Args:
            days: 收集最近多少天

        Returns:
            推文列表
        """
        print("\n🟦 [2/4] 收集 X (Twitter) 官方账号...")

        all_tweets = []

        official = self.accounts['official']

        for priority in ['P0', 'P1']:
            accounts = official.get(priority, [])
            print(f"\n   优先级 {priority}: {len(accounts)} 个账号")

            for account_info in accounts:
                handle = account_info['handle']
                company = account_info['company']

                print(f"   📦 @{handle} ({company})")

                tweets = self.fetch_from_rsshub(handle, account_info, days)
                all_tweets.extend(tweets)

        print(f"\n   ✅ 官方账号收集完成: {len(all_tweets)} 条推文")

        return all_tweets

    def collect_notable_persons(self, days: int = 7) -> List[Dict]:
        """
        收集知名人物推文

        Args:
            days: 收集最近多少天

        Returns:
            推文列表
        """
        print("\n👤 [3/4] 收集 X (Twitter) 知名人物...")

        all_tweets = []

        notable_persons = self.accounts['notable_persons']

        for priority in ['P0', 'P1', 'P2']:
            persons = notable_persons.get(priority, [])
            print(f"\n   优先级 {priority}: {len(persons)} 个账号")

            for person_info in persons:
                handle = person_info['handle']
                name = person_info.get('name', handle)

                print(f"   👤 @{handle} ({name})")

                tweets = self.fetch_from_rsshub(handle, person_info, days)
                all_tweets.extend(tweets)

        print(f"\n   ✅ 知名人物收集完成: {len(all_tweets)} 条推文")

        return all_tweets

    def collect_all_twitter(self, days: int = 7) -> List[Dict]:
        """
        收集所有 Twitter 数据

        Args:
            days: 收集最近多少天

        Returns:
            所有推文列表
        """
        print("\n🟦 [优先级 1] 收集 X (Twitter) 数据...")
        print(f"   总计账号: {len(self.accounts['official']['P0']) + len(self.accounts['official']['P1']) + len(self.accounts['notable_persons']['P0']) + len(self.accounts['notable_persons']['P1']) + len(self.accounts['notable_persons']['P2'])}")

        all_tweets = []

        # 1. 官方账号
        official_tweets = self.collect_official_accounts(days)
        all_tweets.extend(official_tweets)

        # 2. 知名人物
        person_tweets = self.collect_notable_persons(days)
        all_tweets.extend(person_tweets)

        print(f"\n   ✅ Twitter 收集完成: {len(all_tweets)} 条推文")

        return all_tweets


if __name__ == "__main__":
    # 测试 Twitter 收集器
    print("🧪 Silicon Valley Alpha Radar - Twitter 收集器测试")

    collector = TwitterCollector()
    tweets = collector.collect_all_twitter(days=7)

    print(f"\n📊 统计: {len(tweets)} 条推文")

    # 按类型分组
    from collections import Counter
    source_types = [t['source_type'] for t in tweets]
    type_count = Counter(source_types)

    print(f"\n📊 按类型统计:")
    for source_type, count in type_count.most_common():
        print(f"   {source_type}: {count} 条")

    # 按优先级分组
    priorities = [t['priority'] for t in tweets]
    priority_count = Counter(priorities)

    print(f"\n📊 按优先级统计:")
    for priority, count in priority_count.most_common():
        print(f"   {priority}: {count} 条")

    # 显示前 10 条
    print(f"\n🔥 最新 10 条:")
    for i, tweet in enumerate(tweets[:10], 1):
        print(f"\n   [{i}] {tweet['title'][:60]}...")
        print(f"       🟦 {tweet['source']}")
        print(f"       👤 {tweet['name']}")
        print(f"       🔗 {tweet['url']}")
        print(f"       🕐 {tweet['timestamp']}")
