"""
Smart Alert Generator - 生成看起来"非常聪明"的推送消息
真正的洞察，不是废话
"""

import sqlite3
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from typing import List, Dict, Set


class SmartAlertGenerator:
    def __init__(self, github_db: str = "storage/data/github_activity.db"):
        """
        初始化智能告警生成器

        Args:
            github_db: GitHub 数据库路径
        """
        self.github_db = github_db

    def _query_github_data(self, days: int = 7) -> List[Dict]:
        """查询 GitHub 数据"""
        conn = sqlite3.connect(self.github_db)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM github_activity
            ORDER BY timestamp DESC
            LIMIT 100
        ''')

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def _extract_tech_keywords(self, text: str) -> List[str]:
        """
        提取技术关键词（更智能）

        Args:
            text: 要分析的文本

        Returns:
            关键词列表
        """
        if not text:
            return []

        text_lower = text.lower()

        # 技术关键词列表（不是通用的 AI、neural）
        tech_keywords = [
            'transformer', 'attention', 'diffusion', 'gpt', 'llama',
            'whisper', 'codex', 'dalle', 'stable diffusion',
            'midjourney', 'multimodal', 'embedding', 'rag',
            'finetuning', 'rlhf', 'conversational', 'in-context learning',
            'chain-of-thought', 'tool use', 'agents', 'autonomous',
            'reasoning', 'cognitive', 'hallucination', 'alignment',
            'scaling laws', 'emergence', 'chinchilla', 'gopher',
            'mixture-of-experts', 'routing', 'retrieval', 'search',
            'quantization', 'pruning', 'optimization',
            'open-source', 'closed-source', 'api', 'sdk',
            'prompt engineering', 'few-shot', 'zero-shot',
            'multimodal agents', 'web agents', 'browser automation'
        ]

        keywords = []
        for keyword in tech_keywords:
            if keyword.lower() in text_lower:
                keywords.append(keyword)

        return list(set(keywords))

    def _analyze_activity_patterns(self, activities: List[Dict]) -> Dict:
        """
        分析活动模式

        Args:
            activities: 活动列表

        Returns:
            模式分析结果
        """
        # 按时间分组（最近 24 小时）
        recent_activities = [a for a in activities if a.get('timestamp')]
        
        # 按类型统计
        type_freq = Counter([a.get('activity_type', 'unknown') for a in activities])
        
        # 按仓库统计
        repo_freq = Counter([a.get('repo_name', 'unknown') for a in activities])

        # 提取关键词
        all_keywords = []
        for activity in activities:
            desc = activity.get('description', '')
            keywords = self._extract_tech_keywords(desc)
            all_keywords.extend(keywords)

        keyword_freq = Counter(all_keywords)

        return {
            'total_activities': len(activities),
            'type_distribution': dict(type_freq),
            'repo_distribution': dict(repo_freq),
            'top_keywords': keyword_freq.most_common(10)
        }

    def _generate_insightful_message(self, activities: List[Dict]) -> str:
        """
        生成有洞察的消息

        Args:
            activities: 活动列表

        Returns:
            格式化的消息
        """
        if not activities:
            return None

        # 分析模式
        patterns = self._analyze_activity_patterns(activities)

        # 生成洞察
        insights = []

        # 洞察 1：主要活动类型
        top_activity = patterns['type_distribution'].items()[0]
        insights.append(f"📊 主要活动：{top_activity[0]} 占 {top_activity[1]}")

        # 洞察 2：最活跃的仓库
        top_repo = patterns['repo_distribution'].most_common(1)[0]
        insights.append(f"🔥 活跃仓库：{top_repo[0]}")

        # 洞察 3：技术关键词
        if patterns['top_keywords']:
            top_keywords = [kw for kw, count in patterns['top_keywords'][:5] if count >= 2]
            if top_keywords:
                insights.append(f"🎯 关键词：{', '.join(top_keywords)}")

        # 洞察 4：跨公司活动
        company_count = defaultdict(int)
        for activity in activities:
            repo = activity.get('repo_name', '')
            if 'openai' in repo.lower():
                company_count['OpenAI'] += 1
            elif 'deepmind' in repo.lower():
                company_count['DeepMind'] += 1
            elif 'anthropic' in repo.lower():
                company_count['Anthropic'] += 1

        if len(company_count) > 1:
            insights.append(f"🏢 活跃公司：{', '.join(company_count.keys())}")

        # 如果没有重要洞察，不生成消息
        if not insights:
            return None

        # 格式化消息
        message = f"""<b>🔍 Silicon Valley Alpha Radar - 发现 {len(insights)} 个重要信号</b>

{''.join([f"{i}. {insight}" for i, insight in enumerate(insights, 1)])}

---
<i>🕐 分析时间：{datetime.now().strftime('%Y年%m月%d日 %H:%M')}</i>
<i>📊 数据源：GitHub（最近 7 天，{patterns['total_activities']} 个活动）</i>
"""

        return message

    def generate_alert(self, days: int = 7) -> str:
        """
        生成智能告警

        Args:
            days: 分析最近多少天的数据

        Returns:
            告警消息（如果没有重要发现则返回 None）
        """
        print(f"\n🔍 [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 智能分析开始...")

        # 查询数据
        activities = self._query_github_data(days)

        print(f"✅ 数据查询完成：{len(activities)} 个活动")

        # 生成有洞察的消息
        message = self._generate_insightful_message(activities)

        if message:
            print(f"✅ 发现 {len(insights)} 个重要信号，生成告警")
        else:
            print("⚠️  没有发现需要告警的重要信号")

        return message


# 主程序 - 用于测试
if __name__ == "__main__":
    print("🧠 Silicon Valley Alpha Radar - 智能告警生成器")
    print("=" * 60)

    # 创建生成器
    generator = SmartAlertGenerator()

    # 生成告警
    alert = generator.generate_alert(days=7)

    # 显示结果
    if alert:
        print("\n" + "=" * 60)
        print("📡 智能告警消息：")
        print("=" * 60)
        print(alert)
        print("=" * 60)
    else:
        print("\n⚠️  当前没有需要告警的重要信号")

    print("\n✅ 分析完成！")
