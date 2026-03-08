"""
Jina Twitter Collector - 使用 jina-cli 开源工具收集 Twitter 数据
替代官方 API，无需 API 密钥，完全免费
"""

import subprocess
import json
from datetime import datetime, timedelta
import sqlite3
from typing import List, Dict, Optional
import os


class JinaTwitterCollector:
    def __init__(self, config_path: str = "config/config.json"):
        """
        初始化 Jina Twitter 收集器

        Args:
            config_path: 配置文件路径
        """
        self.config = self._load_config(config_path)
        self.storage_path = "storage/data/twitter_posts_jina.db"
        self._init_storage()

    def _load_config(self, config_path: str) -> Dict:
        """加载配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"配置文件未找到: {config_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"配置文件格式错误: {e}")

    def _init_storage(self):
        """初始化 SQLite 存储"""
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)

        conn = sqlite3.connect(self.storage_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS twitter_posts (
                id TEXT PRIMARY KEY,
                handle TEXT,
                company TEXT,
                content TEXT,
                url TEXT,
                likes INTEGER,
                retweets INTEGER,
                replies INTEGER,
                timestamp DATETIME,
                collected_at DATETIME
            )
        ''')

        conn.commit()
        conn.close()

    def _check_jina_installed(self) -> bool:
        """检查 jina-cli 是否已安装"""
        try:
            result = subprocess.run(
                ['jina', '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False

    def _install_jina(self) -> bool:
        """安装 jina-cli"""
        try:
            print("📦 正在安装 jina-cli...")
            result = subprocess.run(
                'curl -fsSL https://raw.githubusercontent.com/geekjourneyx/jina-cli/main/scripts/install.sh | bash',
                shell=True,
                capture_output=True,
                text=True,
                timeout=120
            )
            if result.returncode == 0:
                print("✅ jina-cli 安装成功！")
                return True
            else:
                print(f"❌ jina-cli 安装失败: {result.stderr}")
                return False
        except Exception as e:
            print(f"❌ 安装过程出错: {e}")
            return False

    def read_tweet_url(self, url: str) -> Optional[Dict]:
        """
        使用 jina read 读取 Twitter 帖子

        Args:
            url: Twitter 帖子 URL

        Returns:
            帖子内容字典
        """
        try:
            result = subprocess.run(
                ['jina', 'read', '--url', url, '--output', 'json'],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode != 0:
                print(f"⚠️  jina read 失败: {result.stderr}")
                return None

            # 解析 JSON 输出
            data = json.loads(result.stdout)
            if data.get('success') and 'data' in data:
                tweet_data = data['data']
                return {
                    'id': url.split('/')[-1],  # 从 URL 提取 ID
                    'handle': None,  # 需要从内容提取
                    'company': None,
                    'content': tweet_data.get('content', ''),
                    'url': url,
                    'likes': 0,
                    'retweets': 0,
                    'replies': 0,
                    'timestamp': datetime.now(),
                    'collected_at': datetime.now()
                }

            return None

        except json.JSONDecodeError as e:
            print(f"⚠️  解析 jina 输出失败: {e}")
            return None
        except Exception as e:
            print(f"⚠️  读取推文失败: {e}")
            return None

    def collect_user_tweets(self, handle: str, days: int = 7) -> List[Dict]:
        """
        收集指定用户的推文

        Args:
            handle: Twitter 用户名
            days: 收集最近多少天的数据

        Returns:
            推文列表
        """
        print(f"\n📱 收集 @{handle} 的推文...")

        # 由于 jina CLI 无法获取用户主页的推文列表，我们需要其他方式
        # 这里只是一个示例框架

        tweets = []

        # 临时方案：构造几个示例推文 URL
        # 实际使用时，需要从用户主页获取推文链接
        example_tweet_urls = [
            f"https://x.com/{handle}/status/123456789",
            f"https://x.com/{handle}/status/123456790"
        ]

        for url in example_tweet_urls:
            tweet = self.read_tweet_url(url)
            if tweet:
                tweet['handle'] = handle
                tweets.append(tweet)

        print(f"✅ 收集到 {len(tweets)} 条推文")
        return tweets

    def collect_all_accounts(self, days: int = 7) -> List[Dict]:
        """
        收集所有配置账户的推文

        Args:
            days: 收集最近多少天的数据

        Returns:
            所有推文列表
        """
        # 检查和安装 jina-cli
        if not self._check_jina_installed():
            if not self._install_jina():
                print("❌ jina-cli 安装失败，无法继续")
                return []

        all_tweets = []

        # 遍历所有公司
        for company, config in self.config['monitored_accounts'].items():
            handles = config.get('handles', [])
            if not handles:
                print(f"⚠️  {config['name']} 没有配置 Twitter handles")
                continue

            # 收集每个 handle 的推文
            company_tweets = []
            for handle in handles:
                tweets = self.collect_user_tweets(handle, days)
                company_tweets.extend(tweets)

            all_tweets.extend(company_tweets)

        # 保存到数据库
        if all_tweets:
            self._save_tweets(all_tweets)

        return all_tweets

    def _save_tweets(self, tweets: List[Dict]):
        """
        保存推文到 SQLite 数据库

        Args:
            tweets: 推文列表
        """
        conn = sqlite3.connect(self.storage_path)
        cursor = conn.cursor()

        for tweet in tweets:
            cursor.execute('''
                INSERT OR REPLACE INTO twitter_posts
                (id, handle, company, content, url, likes, retweets,
                 replies, timestamp, collected_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                tweet['id'],
                tweet['handle'],
                tweet['company'],
                tweet['content'],
                tweet['url'],
                tweet['likes'],
                tweet['retweets'],
                tweet['replies'],
                tweet['timestamp'],
                tweet['collected_at']
            ))

        conn.commit()
        conn.close()

        print(f"✅ 已保存 {len(tweets)} 条推文到数据库")

    def get_recent_stats(self, hours: int = 24) -> Dict:
        """
        获取最近统计信息

        Args:
            hours: 最近多少小时的统计

        Returns:
            统计信息字典
        """
        since = datetime.now() - timedelta(hours=hours)

        conn = sqlite3.connect(self.storage_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT COUNT(*) as total_tweets,
                   COUNT(DISTINCT handle) as active_handles,
                   COUNT(*) FILTER (WHERE likes < 50) as low_engagement_tweets
            FROM twitter_posts
            WHERE collected_at >= ?
        ''', (since,))

        row = cursor.fetchone()
        conn.close()

        return {
            'total_tweets': row[0] or 0,
            'active_handles': row[1] or 0,
            'low_engagement_tweets': row[2] or 0,
            'period_hours': hours
        }
