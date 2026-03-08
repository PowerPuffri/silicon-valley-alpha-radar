"""
Reddit Collector - 监控 Reddit 的 AI 相关讨论
追踪 r/MachineLearning, r/artificial 等子版块
"""

import requests
from datetime import datetime, timedelta
import sqlite3
from typing import List, Dict, Optional
import json
import os


class RedditCollector:
    def __init__(self, config_path: str = "config/config.json"):
        """
        初始化 Reddit 收集器

        Args:
            config_path: 配置文件路径
        """
        self.config = self._load_config(config_path)
        self.storage_path = "storage/data/reddit_posts.db"
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
            CREATE TABLE IF NOT EXISTS reddit_posts (
                id TEXT PRIMARY KEY,
                subreddit TEXT,
                company TEXT,
                title TEXT,
                author TEXT,
                score INTEGER,
                num_comments INTEGER,
                url TEXT,
                content TEXT,
                keywords_found TEXT,
                timestamp DATETIME,
                collected_at DATETIME
            )
        ''')

        conn.commit()
        conn.close()

    def fetch_subreddit_posts(self, subreddit: str, limit: int = 50,
                                time_filter: str = "week") -> List[Dict]:
        """
        获取子版块的帖子

        Args:
            subreddit: 子版块名称（如 "MachineLearning"）
            limit: 获取的帖子数
            time_filter: 时间过滤器（"week", "month", "year", "all"）

        Returns:
            帖子列表
        """
        print(f"\n📱 正在获取 r/{subreddit} 的热门帖子（{time_filter}）...")

        # 注意：Reddit API 需要 OAuth，这里使用公开的 JSON 接口
        url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit={limit}"
        
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            data = response.json()
            posts = []

            for post in data.get('data', {}).get('children', []):
                post_data = post.get('data', {})
                
                # 提取关键词
                title = post_data.get('title', '')
                selftext = post_data.get('selftext', '')
                keywords_found = self._extract_keywords(title + ' ' + selftext)

                posts.append({
                    'id': f"reddit_{post_data.get('id', '')}",
                    'subreddit': subreddit,
                    'company': 'reddit',
                    'title': title,
                    'author': post_data.get('author', ''),
                    'score': post_data.get('score', 0),
                    'num_comments': post_data.get('num_comments', 0),
                    'url': f"https://www.reddit.com{post_data.get('permalink', '')}",
                    'content': selftext,
                    'keywords_found': ','.join(keywords_found),
                    'timestamp': datetime.now(),
                    'collected_at': datetime.now()
                })

            print(f"✅ 成功获取 {len(posts)} 条帖子")
            return posts

        except Exception as e:
            print(f"❌ 获取 Reddit 帖子失败: {e}")
            return []

    def _extract_keywords(self, text: str) -> List[str]:
        """
        从文本中提取关键词

        Args:
            text: 要分析的文本

        Returns:
            匹配的关键词列表
        """
        if not text:
            return []

        keywords = []
        text_lower = text.lower()

        # 从配置中加载关键词
        config_keywords = self.config.get('keywords', [])

        for keyword in config_keywords:
            if keyword.lower() in text_lower:
                keywords.append(keyword)

        return keywords

    def collect_all_subreddits(self, days: int = 7) -> List[Dict]:
        """
        收集所有配置的子版块数据

        Args:
            days: 收集最近多少天的数据

        Returns:
            所有帖子列表
        """
        all_posts = []

        # 获取配置的子版块列表
        reddit_config = self.config.get('reddit', {})

        # 如果没有配置，使用默认的 AI 相关子版块
        if not reddit_config:
            default_subreddits = [
                'MachineLearning',
                'artificial',
                'deeplearning',
                'singularity',
                'ArtificialIntelligence'
            ]
            print(f"⚠️  未配置 Reddit 子版块，使用默认的 {len(default_subreddits)} 个 AI 相关子版块")
        else:
            default_subreddits = reddit_config.get('subreddits', [])
            print(f"✅ 使用配置的 {len(default_subreddits)} 个子版块")

        # 收集每个子版块的帖子
        for subreddit in default_subreddits:
            posts = self.fetch_subreddit_posts(subreddit, limit=20)
            all_posts.extend(posts)

        # 保存到数据库
        if all_posts:
            self._save_posts(all_posts)

        return all_posts

    def _save_posts(self, posts: List[Dict]):
        """
        保存帖子到 SQLite 数据库

        Args:
            posts: 帖子列表
        """
        conn = sqlite3.connect(self.storage_path)
        cursor = conn.cursor()

        for post in posts:
            cursor.execute('''
                INSERT OR REPLACE INTO reddit_posts
                (id, subreddit, company, title, author, score, num_comments,
                 url, content, keywords_found, timestamp, collected_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                post['id'],
                post['subreddit'],
                post['company'],
                post['title'],
                post['author'],
                post['score'],
                post['num_comments'],
                post['url'],
                post['content'],
                post['keywords_found'],
                post['timestamp'],
                post['collected_at']
            ))

        conn.commit()
        conn.close()

        print(f"✅ 已保存 {len(posts)} 条 Reddit 帖子到数据库")

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
            SELECT COUNT(*) as total_posts,
                   COUNT(DISTINCT subreddit) as active_subreddits,
                   COUNT(*) FILTER (WHERE timestamp >= ?) as recent_posts
            FROM reddit_posts
            WHERE timestamp >= ?
        ''', (since,))

        row = cursor.fetchone()
        conn.close()

        return {
            'total_posts': row[0] or 0,
            'active_subreddits': row[1] or 0,
            'recent_posts': row[2] or 0,
            'period_hours': hours
        }


if __name__ == "__main__":
    print("📱 Reddit Collector - 测试模式")
    
    collector = RedditCollector()
    posts = collector.collect_all_subreddits(days=1)
    
    stats = collector.get_recent_stats(hours=24)
    print(f"\n📊 统计信息:")
    print(f"   总帖子数: {stats['total_posts']}")
    print(f"   活跃子版块: {stats['active_subreddits']}")
    print(f"   最近帖子数: {stats['recent_posts']}")
