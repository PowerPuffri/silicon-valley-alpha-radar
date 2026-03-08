"""
Twint Collector - 使用 twint 开源工具收集 Twitter 数据
替代官方 API，无需 API 密钥，完全免费
"""

import json
import subprocess
import pandas as pd
from datetime import datetime, timedelta
import sqlite3
from typing import List, Dict, Optional
import os
import sys

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))
sys.path.insert(0, project_root)

from collectors.twitter_collector import TwitterCollector  # 复用数据模型


class TwintCollector:
    def __init__(self, config_path: str = "config/config.json"):
        """
        初始化 Twint 收集器
        
        Args:
            config_path: 配置文件路径
        """
        self.config = self._load_config(config_path)
        self.storage_path = "storage/data/twitter_posts_twint.db"
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
            CREATE TABLE IF NOT EXISTS twitter_posts_twint (
                id TEXT PRIMARY KEY,
                author TEXT,
                handle TEXT,
                content TEXT,
                likes INTEGER,
                retweets INTEGER,
                timestamp DATETIME,
                keywords TEXT,
                collected_at DATETIME,
                is_low_engagement INTEGER,
                source TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def check_twint_installed(self) -> bool:
        """
        检查 twint 是否已安装
        
        Returns:
            bool: 是否已安装
        """
        try:
            result = subprocess.run(
                ["twint", "--version"],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False
    
    def install_twint(self) -> bool:
        """
        安装 twint
        
        Returns:
            bool: 安装是否成功
        """
        print("📦 正在安装 twint...")
        
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "twint", "--upgrade"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("✅ twint 安装成功！")
                return True
            else:
                print(f"❌ twint 安装失败: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ 安装 twint 时出错: {e}")
            return False
    
    def collect_tweets_with_twint(self, handle: str, days: int = 7) -> List[Dict]:
        """
        使用 twint 收集指定用户的推文
        
        Args:
            handle: Twitter 用户名（不含 @）
            days: 收集最近多少天的推文
            
        Returns:
            推文列表
        """
        if not self.check_twint_installed():
            if not self.install_twint():
                raise RuntimeError("twint 安装失败，无法继续")
        
        try:
            # 使用 twint 命令行工具收集推文
            cmd = [
                "twint",
                "timeline",
                f"--username", handle,
                "--limit", "200",  # 最多获取 200 条
                "--output", "/tmp/twint_data.json"
            ]
            
            print(f"📱 正在使用 twint 收集 @{handle} 的推文（最近 {days} 天）...")
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"❌ twint 收集失败: {result.stderr}")
                return []
            
            # 读取 twint 输出的 JSON 文件
            tweets = []
            output_file = "/tmp/twint_data.json"
            
            if os.path.exists(output_file):
                try:
                    with open(output_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        # twint 输出格式：{"tweets": [...]}
                        if "tweets" in data:
                            tweets = data["tweets"]
                except Exception as e:
                    print(f"❌ 读取 twint 输出失败: {e}")
                    return []
            else:
                print("⚠️  twint 未生成输出文件")
                return []
            
            # 过滤时间窗口
            if tweets:
                cutoff_time = datetime.now() - timedelta(days=days)
                tweets = [
                    tweet for tweet in tweets
                    if datetime.strptime(tweet['date'], '%Y-%m-%d %H:%M:%S') >= cutoff_time
                ]
            
            print(f"✅ 使用 twint 收集到 {len(tweets)} 条推文")
            return tweets
            
        except Exception as e:
            print(f"❌ twint 收集推文失败: {e}")
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
            text = tweet.get('content', tweet.get('text', '')).lower()
            
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
            likes = tweet.get('likes', tweet.get('statistics', {}).get('likes', 0))
            
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
            # 解析时间戳
            timestamp_str = tweet.get('date', tweet.get('timestamp', ''))
            if timestamp_str:
                try:
                    # twint 格式：2023-10-01 12:00:00
                    timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                except:
                    timestamp = datetime.now()
            else:
                timestamp = datetime.now()
            
            # 标准化推文数据
            tweet_id = tweet.get('id', tweet.get('id_str', ''))
            if not tweet_id:
                # 如果没有 ID，生成一个（罕见情况）
                tweet_id = f"twint_{timestamp_str}_{hash(tweet.get('content', ''))}"
            
            cursor.execute('''
                INSERT OR REPLACE INTO twitter_posts_twint 
                (id, author, handle, content, likes, retweets, timestamp, 
                 keywords, collected_at, is_low_engagement, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                tweet_id,
                tweet.get('author', tweet.get('username', '')),
                tweet.get('username', ''),
                tweet.get('content', tweet.get('text', '')),
                tweet.get('likes', tweet.get('statistics', {}).get('likes', 0)),
                tweet.get('retweets', tweet.get('statistics', {}).get('retweets', 0)),
                timestamp,
                json.dumps(tweet.get('matched_keywords', [])),
                collected_at,
                tweet.get('is_low_engagement', 0),
                'twint'
            ))
        
        conn.commit()
        conn.close()
        
        print(f"✅ 已保存 {len(tweets)} 条推文到数据库")
    
    def collect_all_accounts_with_twint(self, days: int = 7):
        """
        使用 twint 收集所有监控账号的推文
        
        Args:
            days: 收集最近多少天的推文
        """
        all_tweets = []
        keywords = self.config.get('keywords', [])
        max_likes = self.config.get('trend_detection', {}).get('max_public_likes', 100)
        
        # 遍历所有公司
        for company, config in self.config['monitored_accounts'].items():
            print(f"\n📊 正在使用 twint 收集 {config['name']} 的推文...")
            
            # 收集每个 handle 的推文
            company_tweets = []
            for handle in config.get('handles', []):
                tweets = self.collect_tweets_with_twint(handle, days)
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
            FROM twitter_posts_twint
            WHERE collected_at >= ?
        ''', (since,))
        
        stats = cursor.fetchone()
        
        conn.close()
        
        return {
            'total_tweets': stats[0],
            'low_engagement_tweets': stats[1],
            'active_handles': stats[2],
            'period_hours': hours,
            'source': 'twint'
        }


# 主程序 - 用于测试
if __name__ == "__main__":
    print("🎯 Silicon Valley Alpha Radar - Twint Collector (开源方案）")
    print("=" * 60)
    print("\n💡 使用开源工具 twint 收集 Twitter 数据，无需 API 密钥")
    
    collector = TwintCollector()
    
    # 检查 twint 是否已安装
    if not collector.check_twint_installed():
        print("\n⚠️  twint 未安装，正在自动安装...")
        collector.install_twint()
    
    print("\n✅ Twint 已就绪！")
    print("\n下一步：")
    print("1. 确保已安装依赖：pip install -r requirements.txt")
    print("2. 测试数据收集：python orchestrator.py --days 7 --twitter-only")
