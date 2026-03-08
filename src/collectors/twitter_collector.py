"""
Twitter Collector - 监控大佬们的推文
收集最近 7 天的推文，过滤关键词和低关注度的隐性趋势
"""

import tweepy
import pandas as pd
from datetime import datetime, timedelta
import json
import sqlite3
from typing import List, Dict, Optional
import os


class TwitterCollector:
    def __init__(self, config_path: str = "config/config.json"):
        """
        初始化 Twitter 收集器
        
        Args:
            config_path: 配置文件路径
        """
        self.config = self._load_config(config_path)
        self.api_client = None
        self.storage_path = "storage/data/twitter_posts.db"
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
                author TEXT,
                handle TEXT,
                content TEXT,
                likes INTEGER,
                retweets INTEGER,
                timestamp DATETIME,
                keywords TEXT,
                collected_at DATETIME,
                is_low_engagement INTEGER
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def authenticate(self, api_key: str, api_secret: str, bearer_token: str):
        """
        认证 Twitter API
        
        Args:
            api_key: Twitter API Key
            api_secret: Twitter API Secret
            bearer_token: Twitter Bearer Token
        """
        client = tweepy.Client(
            bearer_token=bearer_token,
            consumer_key=api_key,
            consumer_secret=api_secret,
            wait_on_rate_limit=True
        )
        
        # 测试连接
        try:
            me = client.get_me()
            print(f"✅ Twitter API 认证成功！用户: @{me.data.username}")
            self.api_client = client
            return True
        except Exception as e:
            print(f"❌ Twitter API 认证失败: {e}")
            return False
    
    def collect_recent_posts(self, handle: str, days: int = 7) -> List[Dict]:
        """
        收集指定用户的最近推文
        
        Args:
            handle: Twitter 用户名（不含 @）
            days: 收集最近多少天的推文
            
        Returns:
            推文列表
        """
        if not self.api_client:
            raise RuntimeError("未认证 Twitter API，请先调用 authenticate()")
        
        try:
            # 获取用户最近的推文
            tweets = []
            since_id = None
            
            while len(tweets) < 100:  # 最多获取 100 条
                response = self.api_client.get_users_tweets(
                    id=handle,
                    max_results=100,
                    since_id=since_id,
                    tweet_fields=['created_at', 'public_metrics', 'text', 'referenced_tweets'],
                    exclude=['retweets', 'replies']
                )
                
                if not response.data:
                    break
                
                tweets.extend(response.data)
                
                # 检查时间窗口
                if response.data:
                    last_tweet = response.data[-1]
                    last_time = datetime.strptime(last_tweet['created_at'], '%Y-%m-%dT%H:%M:%S.%fZ')
                    cutoff_time = datetime.now() - timedelta(days=days)
                    
                    if last_time < cutoff_time:
                        break
            
            print(f"✅ 收集到 @{handle} 的 {len(tweets)} 条推文（最近 {days} 天）")
            return tweets
            
        except tweepy.errors.NotFound:
            print(f"❌ 用户 @{handle} 不存在")
            return []
        except Exception as e:
            print(f"❌ 收集 @{handle} 推文失败: {e}")
            return []
    
    def filter_keywords(self, tweets: List[Dict], keywords: List[str]) -> List[Dict]:
        """
        过滤包含关键词的推文
        
        Args:
            tweets: 推文列表
            keywords: 关键词列表
            
        Returns:
            过滤后的推文列表
        """
        filtered_tweets = []
        keywords_lower = [k.lower() for k in keywords]
        
        for tweet in tweets:
            text = tweet['text'].lower()
            
            # 检查是否包含任何关键词
            for keyword in keywords_lower:
                if keyword in text:
                    tweet['matched_keywords'] = [keyword]
                    filtered_tweets.append(tweet)
                    break
        
        print(f"✅ 过滤后剩余 {len(filtered_tweets)} 条推文（关键词匹配）")
        return filtered_tweets
    
    def filter_low_engagement(self, tweets: List[Dict], max_likes: int = 100) -> List[Dict]:
        """
        过滤低关注度的推文（潜在隐性趋势）
        
        Args:
            tweets: 推文列表
            max_likes: 最大点赞数阈值
            
        Returns:
            低关注度推文列表
        """
        low_engagement_tweets = []
        
        for tweet in tweets:
            likes = tweet['public_metrics']['like_count']
            
            if likes < max_likes:
                tweet['is_low_engagement'] = True
                low_engagement_tweets.append(tweet)
            else:
                tweet['is_low_engagement'] = False
        
        print(f"✅ 发现 {len(low_engagement_tweets)} 条低关注度推文（likes < {max_likes}）")
        return low_engagement_tweets
    
    def save_tweets(self, tweets: List[Dict]):
        """
        保存推文到 SQLite 数据库
        
        Args:
            tweets: 推文列表
        """
        conn = sqlite3.connect(self.storage_path)
        cursor = conn.cursor()
        collected_at = datetime.now()
        
        for tweet in tweets:
            cursor.execute('''
                INSERT OR REPLACE INTO twitter_posts 
                (id, author, handle, content, likes, retweets, timestamp, 
                 keywords, collected_at, is_low_engagement)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                tweet['id'],
                tweet.get('author_name', ''),
                tweet.get('username', ''),
                tweet['text'],
                tweet['public_metrics']['like_count'],
                tweet['public_metrics']['retweet_count'],
                datetime.strptime(tweet['created_at'], '%Y-%m-%dT%H:%M:%S.%fZ'),
                json.dumps(tweet.get('matched_keywords', [])),
                collected_at,
                tweet.get('is_low_engagement', 0)
            ))
        
        conn.commit()
        conn.close()
        
        print(f"✅ 已保存 {len(tweets)} 条推文到数据库")
    
    def collect_all_accounts(self, days: int = 7):
        """
        收集所有监控账号的推文
        
        Args:
            days: 收集最近多少天的推文
        """
        all_tweets = []
        keywords = self.config.get('keywords', [])
        max_likes = self.config.get('trend_detection', {}).get('max_public_likes', 100)
        
        # 遍历所有公司
        for company, config in self.config['monitored_accounts'].items():
            print(f"\n📊 正在收集 {config['name']} 的推文...")
            
            # 收集每个 handle 的推文
            company_tweets = []
            for handle in config.get('handles', []):
                tweets = self.collect_recent_posts(handle, days)
                company_tweets.extend(tweets)
            
            # 过滤关键词
            if keywords:
                company_tweets = self.filter_keywords(company_tweets, keywords)
            
            # 过滤低关注度
            low_engagement_tweets = self.filter_low_engagement(company_tweets, max_likes)
            
            all_tweets.extend(low_engagement_tweets)
        
        # 保存所有推文
        if all_tweets:
            self.save_tweets(all_tweets)
        
        return all_tweets
    
    def get_recent_stats(self, hours: int = 24) -> Dict:
        """
        获取最近的统计数据
        
        Args:
            hours: 最近多少小时
            
        Returns:
            统计数据字典
        """
        conn = sqlite3.connect(self.storage_path)
        cursor = conn.cursor()
        
        since = datetime.now() - timedelta(hours=hours)
        
        cursor.execute('''
            SELECT 
                COUNT(*) as total_tweets,
                COUNT(CASE WHEN is_low_engagement = 1 THEN 1 END) as low_engagement_tweets,
                COUNT(DISTINCT handle) as active_handles
            FROM twitter_posts
            WHERE collected_at >= ?
        ''', (since,))
        
        stats = cursor.fetchone()
        
        conn.close()
        
        return {
            'total_tweets': stats[0],
            'low_engagement_tweets': stats[1],
            'active_handles': stats[2],
            'period_hours': hours
        }


# 主程序 - 用于测试
if __name__ == "__main__":
    print("🎯 Silicon Valley Alpha Radar - Twitter Collector")
    print("=" * 60)
    
    collector = TwitterCollector()
    
    # 注意：这里需要从环境变量或配置文件读取 API 密钥
    print("\n⚠️  注意：需要设置 Twitter API 密钥")
    print("可以通过环境变量设置：TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_BEARER_TOKEN")
