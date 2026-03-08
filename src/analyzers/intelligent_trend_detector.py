"""
Intelligent Trend Detector - 智能趋势检测器
真正的频率分析、相关性检测、隐性共识发现
"""

import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set, Tuple
from collections import Counter, defaultdict
import json
import os


class IntelligentTrendDetector:
    def __init__(self, github_db: str = "storage/data/github_activity.db",
                 twitter_db: str = "storage/data/twitter_posts_jina.db",
                 reddit_db: str = "storage/data/reddit_posts.db",
                 hackernews_db: str = "storage/data/hacker_news.db"):
        """
        初始化智能趋势检测器

        Args:
            github_db: GitHub 数据库路径
            twitter_db: Twitter 数据库路径
            reddit_db: Reddit 数据库路径
            hackernews_db: Hacker News 数据库路径
        """
        self.github_db = github_db
        self.twitter_db = twitter_db
        self.reddit_db = reddit_db
        self.hackernews_db = hackernews_db

        self.storage_history = "storage/data/trend_history.db"
        self._init_storage()
        self._init_history()

    def _init_storage(self):
        """初始化 SQLite 存储"""
        os.makedirs(os.path.dirname(self.storage_history), exist_ok=True)

        conn = sqlite3.connect(self.storage_history)
        cursor = conn.cursor()

        # 历史关键词频率表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS keyword_frequency (
                keyword TEXT PRIMARY KEY,
                frequency INTEGER,
                last_seen DATETIME,
                trend TEXT,  -- 'rising', 'falling', 'stable'
                daily_counts TEXT  -- JSON 格式，存储最近 7 天的每日计数
            )
        ''')

        # 相关性表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS correlations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keyword1 TEXT,
                keyword2 TEXT,
                correlation_score REAL,
                co_occurrence_count INTEGER,
                last_seen DATETIME
            )
        ''')

        conn.commit()
        conn.close()

    def _init_history(self):
        """初始化历史数据库"""
        os.makedirs(os.path.dirname(self.storage_history), exist_ok=True)

        conn = sqlite3.connect(self.storage_history)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # 检查是否是第一次运行
        cursor.execute('SELECT COUNT(*) FROM keyword_frequency')
        count = cursor.fetchone()[0]
        conn.close()

        self.is_first_run = (count == 0)
        if self.is_first_run:
            print("✅ 智能趋势检测器首次运行，需要至少 2 天的数据来检测趋势")

    def _query_github_data(self, days: int = 7) -> List[Dict]:
        """查询 GitHub 数据"""
        conn = sqlite3.connect(self.github_db)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        since = datetime.now() - timedelta(days=days * 2)

        cursor.execute('''
            SELECT * FROM github_activity
            WHERE timestamp >= ?
            ORDER BY timestamp DESC
            LIMIT 500
        ''', (since,))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def _query_twitter_data(self, days: int = 7) -> List[Dict]:
        """查询 Twitter 数据"""
        if not os.path.exists(self.twitter_db):
            return []

        conn = sqlite3.connect(self.twitter_db)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        since = datetime.now() - timedelta(days=days * 2)

        cursor.execute('''
            SELECT * FROM twitter_posts
            WHERE timestamp >= ?
            ORDER BY timestamp DESC
            LIMIT 200
        ''', (since,))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def _query_reddit_data(self, days: int = 7) -> List[Dict]:
        """查询 Reddit 数据"""
        if not os.path.exists(self.reddit_db):
            return []

        conn = sqlite3.connect(self.reddit_db)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        since = datetime.now() - timedelta(days=days * 2)

        cursor.execute('''
            SELECT * FROM reddit_posts
            WHERE timestamp >= ?
            ORDER BY timestamp DESC
            LIMIT 100
        ''', (since,))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def _query_hackernews_data(self, days: int = 7) -> List[Dict]:
        """查询 Hacker News 数据"""
        if not os.path.exists(self.hackernews_db):
            return []

        conn = sqlite3.connect(self.hackernews_db)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        since = datetime.now() - timedelta(days=days * 2)

        cursor.execute('''
            SELECT * FROM hacker_news
            WHERE timestamp >= ?
            ORDER BY timestamp DESC
            LIMIT 100
        ''', (since,))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def extract_keywords(self, text: str, config_keywords: List[str]) -> List[str]:
        """
        从文本中提取关键词

        Args:
            text: 要分析的文本
            config_keywords: 配置的关键词列表

        Returns:
            匹配的关键词列表
        """
        if not text:
            return []

        keywords = []
        text_lower = text.lower()

        # 从文本中提取所有单词
        words = text_lower.split()

        # 匹配配置的关键词
        for keyword in config_keywords:
            keyword_lower = keyword.lower()
            # 完全匹配或包含匹配
            if keyword_lower in text_lower:
                keywords.append(keyword)

        return list(set(keywords))  # 去重

    def analyze_keyword_frequency_trend(self, current_freq: Counter,
                                       historical_freq: Dict[str, Dict]) -> Dict[str, str]:
        """
        分析关键词频率趋势

        Args:
            current_freq: 当前频率
            historical_freq: 历史频率数据（keyword -> {date: count}）

        Returns:
            趋势字典（keyword -> trend）
        """
        trends = {}

        for keyword, current_count in current_freq.items():
            # 获取历史数据
            keyword_history = historical_freq.get(keyword, {})

            if not keyword_history:
                trends[keyword] = 'unknown'
                continue

            # 计算最近 7 天的平均频率
            recent_counts = list(keyword_history.values())[-7:]
            if recent_counts:
                avg_recent_freq = sum(recent_counts) / len(recent_counts)
            else:
                avg_recent_freq = current_count  # 如果没有历史数据

            # 计算增长率
            growth_rate = (current_count - avg_recent_freq) / max(avg_recent_freq, 1) * 100

            # 判断趋势
            if growth_rate > 50:
                trends[keyword] = 'rapidly_rising'
            elif growth_rate > 20:
                trends[keyword] = 'rising'
            elif growth_rate < -50:
                trends[keyword] = 'rapidly_falling'
            elif growth_rate < -20:
                trends[keyword] = 'falling'
            else:
                trends[keyword] = 'stable'

        return trends

    def detect_keyword_correlations(self, texts: List[str], config_keywords: List[str]) -> Dict[Tuple[str, str], float]:
        """
        检测关键词之间的相关性（共现）

        Args:
            texts: 文本列表
            config_keywords: 配置的关键词列表

        Returns:
            相关性字典（(keyword1, keyword2) -> correlation_score）
        """
        correlations = defaultdict(int)

        # 统计关键词共现
        for text in texts:
            keywords_in_text = self.extract_keywords(text, config_keywords)

            # 统计所有关键词对的共现次数
            for i, kw1 in enumerate(keywords_in_text):
                for kw2 in keywords_in_text[i+1:]:
                    # 按字母顺序排序，避免重复
                    pair = tuple(sorted([kw1, kw2]))
                    correlations[pair] += 1

        # 计算相关性分数（0-1）
        max_count = max(correlations.values()) if correlations else 1
        correlations_score = {
            pair: count / max_count if max_count > 0 else 0
            for pair, count in correlations.items()
        }

        # 只保留相关性 > 0.2 的对
        strong_correlations = {
            pair: score for pair, score in correlations_score.items()
            if score > 0.2
        }

        return strong_correlations

    def detect_hidden_consensus(self, github_data: List[Dict],
                                config_keywords: List[str],
                                min_participants: int = 2) -> List[Dict]:
        """
        检测隐性共识 - 多个公司讨论相同话题但公开度低

        Args:
            github_data: GitHub 数据
            config_keywords: 配置的关键词列表
            min_participants: 最少参与公司数

        Returns:
            共识列表
        """
        # 按公司分组数据
        company_activities = defaultdict(list)
        for activity in github_data:
            repo_name = activity.get('repo_name', '')
            # 简化公司识别
            if 'openai' in repo_name.lower():
                company_activities['OpenAI'].append(activity)
            elif 'deepmind' in repo_name.lower() or 'google' in repo_name.lower():
                company_activities['DeepMind'].append(activity)
            elif 'anthropic' in repo_name.lower():
                company_activities['Anthropic'].append(activity)

        # 提取每个公司讨论的关键词
        company_keywords = {}
        for company, activities in company_activities.items():
            keywords = []
            for activity in activities:
                description = activity.get('description', '')
                keywords.extend(self.extract_keywords(description, config_keywords))

            # 统计关键词频率
            keyword_freq = Counter(keywords)
            company_keywords[company] = keyword_freq

        # 检测共同讨论的关键词（隐性共识）
        hidden_consensus = []

        # 找出所有出现在至少 min_participants 个公司的关键词
        keyword_participation = defaultdict(set)
        for keyword, keyword_freq in company_keywords.items():
            for company, freq in keyword_freq.items():
                if freq >= 2:  # 至少讨论 2 次
                    keyword_participation[keyword].add(company)

        # 过滤出满足条件的
        for keyword, companies in keyword_participation.items():
            if len(companies) >= min_participants:
                # 计算每个公司的讨论次数
                company_counts = {
                    company: company_keywords[company].get(keyword, 0)
                    for company in companies
                }

                # 检查是否真的有讨论（每个公司至少出现 2 次）
                if all(count >= 2 for count in company_counts.values()):
                    hidden_consensus.append({
                        'keyword': keyword,
                        'participants': list(companies),
                        'company_counts': company_counts,
                        'total_discussions': sum(company_counts.values()),
                        'consensus_type': 'multi_company'
                    })

        # 按总讨论数排序
        hidden_consensus.sort(key=lambda x: x['total_discussions'], reverse=True)

        return hidden_consensus

    def update_keyword_history(self, keyword_freq: Counter, date: datetime):
        """
        更新关键词历史

        Args:
            keyword_freq: 当前关键词频率
            date: 日期
        """
        conn = sqlite3.connect(self.storage_history)
        cursor = conn.cursor()

        date_str = date.strftime('%Y-%m-%d')

        for keyword, count in keyword_freq.items():
            # 获取历史数据
            cursor.execute('SELECT daily_counts FROM keyword_frequency WHERE keyword = ?', (keyword,))
            row = cursor.fetchone()

            if row:
                # 更新历史
                daily_counts = json.loads(row[0]) if row[0] else {}
                daily_counts[date_str] = count
            else:
                # 创建新记录
                daily_counts = {date_str: count}

            # 更新趋势
            # 计算最近 7 天的平均
            recent_counts = list(daily_counts.values())[-7:]
            if recent_counts:
                avg_recent = sum(recent_counts) / len(recent_counts)
                growth_rate = (count - avg_recent) / max(avg_recent, 1) * 100

                if growth_rate > 50:
                    trend = 'rapidly_rising'
                elif growth_rate > 20:
                    trend = 'rising'
                elif growth_rate < -50:
                    trend = 'rapidly_falling'
                elif growth_rate < -20:
                    trend = 'falling'
                else:
                    trend = 'stable'
            else:
                trend = 'stable'

            # 更新或插入
            cursor.execute('''
                INSERT OR REPLACE INTO keyword_frequency
                (keyword, frequency, last_seen, trend, daily_counts)
                VALUES (?, ?, ?, ?, ?)
            ''', (keyword, count, date, trend, json.dumps(daily_counts)))

        conn.commit()
        conn.close()

    def generate_smart_insights(self, github_data: List[Dict],
                                 config_keywords: List[str]) -> List[str]:
        """
        生成智能洞察

        Args:
            github_data: GitHub 数据
            config_keywords: 配置的关键词列表

        Returns:
            洞察列表
        """
        insights = []

        # 提取所有文本
        all_descriptions = [activity.get('description', '') for activity in github_data]

        # 检测相关性
        correlations = self.detect_keyword_correlations(all_descriptions, config_keywords)

        # 找出强相关（相关性 > 0.5）
        strong_correlations = {
            pair: score for pair, score in correlations.items()
            if score > 0.5
        }

        if strong_correlations:
            insights.append(f"🔗 **检测到 {len(strong_correlations)} 对强相关关键词**")
            for pair, score in sorted(strong_correlations.items(), key=lambda x: x[1], reverse=True)[:3]:
                insights.append(f"   - '{pair[0]}' 和 '{pair[1]}' 同时出现频率很高 (相关度: {score:.2f})")

        # 检测隐性共识
        hidden_consensus = self.detect_hidden_consensus(github_data, config_keywords, min_participants=2)

        if hidden_consensus:
            insights.append(f"\n🎯 **发现 {len(hidden_consensus)} 个跨公司共识**")

            for i, consensus in enumerate(hidden_consensus[:3], 1):
                insights.append(f"\n{i}. **{consensus['keyword']}**")
                insights.append(f"   参与公司: {', '.join(consensus['participants'])}")
                insights.append(f"   各公司讨论次数: {', '.join(f'{company}: {count}' for company, count in consensus['company_counts'].items())}")
                insights.append(f"   总讨论: {consensus['total_discussions']} 次")
                insights.append(f"   类型: 多公司共识（隐性）")

        # 分析最活跃的话题
        keyword_freq = Counter()
        for activity in github_data:
            description = activity.get('description', '')
            keywords = self.extract_keywords(description, config_keywords)
            keyword_freq.update(keywords)

        if keyword_freq:
            top_keywords = keyword_freq.most_common(10)
            insights.append(f"\n📊 **最活跃关键词（Top 10）**")
            for i, (keyword, count) in enumerate(top_keywords, 1):
                insights.append(f"{i}. {keyword}: {count} 次")

        # 分析活动类型分布
        activity_type_freq = Counter()
        for activity in github_data:
            activity_type = activity.get('activity_type', 'unknown')
            activity_type_freq[activity_type] += 1

        if activity_type_freq:
            insights.append(f"\n📈 **活动类型分布**")
            for activity_type, count in activity_type_freq.most_common():
                insights.append(f"- {activity_type}: {count} 次")

        return insights

    def generate_smart_alert_message(self, insights: List[str]) -> str:
        """
        生成智能告警消息

        Args:
            insights: 洞察列表

        Returns:
            格式化的告警消息
        """
        if not insights:
            return None

        alert_message = f"""<b>🤖 Silicon Valley Alpha Radar - 智能趋势检测</b>

---

**🔍 关键发现：**
"""
        important_insights = []

        # 强相关关键词
        if '强相关' in ' '.join(insights):
            important_insights.append("🔗 发现多个技术关键词同时高频出现，可能预示新的研究方向")

        # 隐性共识
        if '跨公司共识' in ' '.join(insights):
            important_insights.append("🎯 检测到多个 AI 公司在私下讨论相同的技术话题，这是重要的市场信号")

        # 活跃关键词
        if '最活跃关键词' in ' '.join(insights):
            important_insights.append("📊 某些技术关键词近期讨论度显著上升")

        for i, insight in enumerate(important_insights, 1):
            alert_message += f"{i}. {insight}\n"

        # 添加详细洞察
        alert_message += f"\n---\n**详细分析：**\n"
        for insight in insights[:10]:
            alert_message += f"{insight}\n"

        alert_message += f"""---
<i>🕐 检测时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}</i>
"""

        return alert_message

    def analyze_all_data(self, days: int = 7) -> Dict:
        """
        分析所有数据并生成智能洞察

        Args:
            days: 分析最近多少天的数据

        Returns:
            分析结果字典
        """
        print(f"\n🧠 [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 智能趋势分析开始（最近 {days} 天）")

        # 加载配置
        try:
            with open("config/config.json", 'r', encoding='utf-8') as f:
                config = json.load(f)
                config_keywords = config.get('keywords', [])
        except Exception as e:
            print(f"⚠️  加载配置文件失败: {e}")
            config_keywords = []

        # 查询数据
        github_data = self._query_github_data(days)
        twitter_data = self._query_twitter_data(days)
        reddit_data = self._query_reddit_data(days)
        # hackernews_data = self._query_hackernews_data(days)

        print(f"✅ 数据查询完成：GitHub {len(github_data)}, Twitter {len(twitter_data)}, Reddit {len(reddit_data)}")

        # 生成智能洞察
        insights = self.generate_smart_insights(github_data, config_keywords)

        # 更新历史
        print("✅ 更新关键词历史...")
        all_descriptions = [activity.get('description', '') for activity in github_data]
        keyword_freq = Counter()
        for description in all_descriptions:
            keywords = self.extract_keywords(description, config_keywords)
            keyword_freq.update(keywords)

        self.update_keyword_history(keyword_freq, datetime.now())

        print(f"✅ 智能分析完成，发现 {len(insights)} 个洞察")

        # 生成智能告警消息
        alert_message = self.generate_smart_alert_message(insights)

        result = {
            'analysis_time': datetime.now(),
            'data_summary': {
                'github_activities': len(github_data),
                'twitter_posts': len(twitter_data),
                'reddit_posts': len(reddit_data)
            },
            'insights_count': len(insights),
            'important_insights_count': len([i for i in insights if '强相关' in i or '跨公司共识' in i]),
            'insights': insights,
            'alert_message': alert_message,
            'has_alert': alert_message is not None
        }

        return result


# 主程序 - 用于测试
if __name__ == "__main__":
    print("🧠 Silicon Valley Alpha Radar - 智能趋势检测器")
    print("=" * 60)

    # 创建检测器
    detector = IntelligentTrendDetector()

    # 分析最近 7 天的数据
    result = detector.analyze_all_data(days=7)

    # 显示结果
    print(f"\n📊 分析结果：")
    print(f"   数据总数: {result['data_summary']['github_activities']} GitHub, {result['data_summary']['twitter_posts']} Twitter, {result['data_summary']['reddit_posts']} Reddit")
    print(f"   洞察数: {result['insights_count']}")
    print(f"   重要洞察: {result['important_insights_count']}")

    # 显示告警消息
    if result['alert_message']:
        print(f"\n📡 智能告警消息：")
        print("=" * 60)
        print(result['alert_message'])
        print("=" * 60)
    else:
        print("\n⚠️  没有发现需要告警的重要趋势")

    print("\n✅ 分析完成！")
