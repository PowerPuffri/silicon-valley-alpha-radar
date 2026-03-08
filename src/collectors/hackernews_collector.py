"""
HackerNews Collector - 监控 Hacker News 的 AI 相关文章
追踪黑客社区的 AI 技术讨论和突破
"""

import os
import requests
from datetime import datetime, timedelta
import sqlite3
from typing import List, Dict, Optional
import json
import re


class HackerNewsCollector:
    def __init__(self, config_path: str = "config/config.json"):
        """
        初始化 Hacker News 收集器

        Args:
            config_path: 配置文件路径
        """
        self.config = self._load_config(config_path)
        self.storage_path = "storage/data/hacker_news.db"
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
            CREATE TABLE IF NOT EXISTS hacker_news (
                id TEXT PRIMARY KEY,
                title TEXT,
                url TEXT,
                source TEXT,
                author TEXT,
                points INTEGER,
                comments_count INTEGER,
                time_ago TEXT,
                timestamp DATETIME,
                tags TEXT,
                keywords_found TEXT,
                collected_at DATETIME
            )
        ''')

        conn.commit()
        conn.close()

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

    def fetch_hacker_news_stories(self, limit: int = 30) -> List[Dict]:
        """
        获取 Hacker News 的热门故事

        Args:
            limit: 获取的条数

        Returns:
            故事列表
        """
        print(f"\n🕶️ 正在获取 Hacker News 热门故事（最新 {limit} 条）...")

        # Hacker News API (无需 API key）
        url = "https://hacker-news.firebaseio.com/v0/item"

        try:
            response = requests.get(url, timeout=60)
            response.raise_for_status()

            data = response.json()

            stories = []

            for item in data.get('items', []):
                # 提取故事信息
                title = item.get('title', '')
                url = item.get('url', '')
                points = item.get('points', 0)
                comments_count = item.get('comments_count', 0)
                time_ago = item.get('time_ago', '')
                author = item.get('by', '')
                
                # 提取标签（keywords）
                tags = item.get('tags', '')
                keywords = self._extract_keywords(title + ' ' + tags)
                
                # 检测是否 AI 相关
                ai_related = self._is_ai_related(title, tags, keywords)

                stories.append({
                    'id': f"hn_{item.get('id', '')}",
                    'source': 'hackernews',
                    'company': 'hackernews',
                    'title': title,
                    'url': url,
                    'points': points,
                    'comments_count': comments_count,
                    'time_ago': time_ago,
                    'author': author,
                    'tags': tags,
                    'keywords_found': ','.join(keywords),
                    'ai_related': ai_related,
                    'timestamp': datetime.now(),
                    'collected_at': datetime.now()
                })

            print(f"✅ 成功获取 {len(stories)} 条 Hacker News 故事")
            return stories

        except Exception as e:
            print(f"❌ 获取 Hacker News 失败: {e}")
            return []

    def _is_ai_related(self, title: str, tags: str, keywords: List[str]) -> bool:
        """
        检测是否 AI 相关

        Args:
            title: 故事标题
            tags: 故事标签
            keywords: 提取的关键词

        Returns:
            是否 AI 相关
        """
        text_to_check = (title + ' ' + tags + ' ' + ' '.join(keywords)).lower()
        
        # AI 相关关键词
        ai_keywords = ['ai', 'neural', 'machine learning', 'deep learning', 
                      'llm', 'language model', 'gpt', 'transformer',
                      'neural network', 'attention', 'reinforcement learning',
                      'artificial intelligence', 'openai', 'anthropic', 'claude',
                      'robotics', 'computer vision', 'nlp', 'natural language processing',
                      'agi', 'generative ai', 'autonomous agents', 'agent-based',
                      'multi-modal', 'diffusion', 'foundation models', 'training',
                      'inference', 'model', 'chatgpt', 'gemma', 'llama']

        # 检查是否包含 AI 关键词
        for keyword in ai_keywords:
            if keyword in text_to_check:
                return True

        return False

    def collect_all_stories(self, days: int = 7) -> List[Dict]:
        """
        收集所有故事

        Args:
            days: 收集最近多少天的数据

        Returns:
            故事列表
        """
        print(f"\n🕶️ 正在收集 Hacker News 故事（最近 {days} 天）...")

        # 获取热门故事
        stories = self.fetch_hacker_news_stories(limit=50)

        # 按时间过滤
        since = datetime.now() - timedelta(days=days)
        filtered_stories = [s for s in stories if self._is_within_days(s, s.get('timestamp'), days)]

        # 保存到数据库
        if filtered_stories:
            self._save_stories(filtered_stories)

        return filtered_stories

    def _is_within_days(self, story_timestamp: str, days: int) -> bool:
        """
        检查故事是否在指定天数内

        Args:
            story_timestamp: 故事时间戳
            days: 天数

        Returns:
            是否在范围内
        """
        try:
            # Hacker News 返回的是 ISO 格式时间戳
            story_dt = datetime.fromisoformat(story_timestamp.replace('Z', '+00:00'))
            since_dt = datetime.now() - timedelta(days=days)
            return story_dt >= since_dt
        except:
            return False

    def _save_stories(self, stories: List[Dict]):
        """
        保存故事到 SQLite 数据库

        Args:
            stories: 故事列表
        """
        conn = sqlite3.connect(self.storage_path)
        cursor = conn.cursor()

        for story in stories:
            cursor.execute('''
                INSERT OR REPLACE INTO hacker_news
                (id, title, url, source, author, points, comments_count,
                 time_ago, timestamp, tags, keywords_found, collected_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                story['id'],
                story['title'],
                story['url'],
                story['source'],
                story['author'],
                story['points'],
                story['comments_count'],
                story['time_ago'],
                story['timestamp'],
                story['tags'],
                story['keywords_found'],
                story['collected_at']
            ))

        conn.commit()
        conn.close()

        print(f"✅ 已保存 {len(stories)} 条 Hacker News 故事到数据库")

    def get_ai_related_stories(self, days: int = 7) -> List[Dict]:
        """
        获取 AI 相关的故事

        Args:
            days: 最近多少天的数据

        Returns:
            AI 相关故事列表
        """
        print(f"\n🤖 正在查找 AI 相关的 Hacker News 故事（最近 {days} 天）...")

        conn = sqlite3.connect(self.storage_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        since = datetime.now() - timedelta(days=days)

        cursor.execute('''
            SELECT * FROM hacker_news
            WHERE timestamp >= ? AND ai_related = 1
            ORDER BY timestamp DESC
            LIMIT 50
        ''', (since,))

        rows = cursor.fetchall()
        conn.close()

        ai_stories = [dict(row) for row in rows]

        print(f"✅ 找到 {len(ai_stories)} 条 AI 相关故事")
        return ai_stories

    def get_recent_stats(self, hours: int = 24) -> Dict:
        """
        获取最近统计信息

        Args:
            hours: 最近多少小时的统计

        Returns:
            统计信息字典
        """
        conn = sqlite3.connect(self.storage_path)
        cursor = conn.cursor()

        since = datetime.now() - timedelta(hours=hours)

        cursor.execute('''
            SELECT
                COUNT(*) as total_stories,
                COUNT(*) FILTER (WHERE ai_related = 1) as ai_related_count,
                COUNT(*) FILTER (WHERE timestamp >= ?) as recent_stories
            FROM hacker_news
            WHERE timestamp >= ?
        ''', (since,))

        row = cursor.fetchone()
        conn.close()

        return {
            'total_stories': row[0] or 0,
            'ai_related_count': row[1] or 0,
            'recent_stories': row[2] or 0,
            'period_hours': hours
        }


if __name__ == "__main__":
    print("🕶️ Hacker News Collector - 测试模式")
    
    collector = HackerNewsCollector()
    
    # 测试获取热门故事
    stories = collector.fetch_hacker_news_stories(limit=10)
    
    # 显示前 3 条故事
    print("\n📋 热门故事预览：")
    for i, story in enumerate(stories[:3], 1):
        print(f"\n{i}. {story['title']}")
        print(f"   📍 URL: {story['url']}")
        print(f"   ⭐ Points: {story['points']}")
        print(f"   💬 Comments: {story['comments_count']}")
        print(f"   🏷️ Tags: {story['tags']}")
        print(f"   🤖 AI Related: {'是' if story['ai_related'] else '否'}")
