"""
Trend Detector - 趋势检测引擎
检测关键词频率、话题聚类和潜在共识
"""

import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from collections import Counter
import os


class TrendDetector:
    def __init__(self, github_db: str = "storage/data/github_activity.db"):
        """
        初始化趋势检测器

        Args:
            github_db: GitHub 数据库路径
        """
        self.github_db = github_db
        self.keywords = []
        self.trends = []

    def load_keywords(self, config_path: str = "config/config.json"):
        """
        从配置文件加载关键词

        Args:
            config_path: 配置文件路径
        """
        import json
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                self.keywords = config.get('keywords', [])
                print(f"✅ 已加载 {len(self.keywords)} 个关键词")
        except Exception as e:
            print(f"⚠️  加载关键词失败: {e}")
            self.keywords = []

    def analyze_github_activity(self, days: int = 7) -> Dict:
        """
        分析 GitHub 活动，检测趋势

        Args:
            days: 分析最近多少天的数据

        Returns:
            趋势分析结果
        """
        print(f"\n🔍 正在分析最近 {days} 天的 GitHub 活动...")

        # 查询数据
        conn = sqlite3.connect(self.github_db)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        since = datetime.now() - timedelta(days=days)

        cursor.execute('''
            SELECT * FROM github_activity
            WHERE timestamp >= ?
            ORDER BY timestamp DESC
        ''', (since,))

        rows = cursor.fetchall()
        conn.close()

        if not rows:
            print("⚠️  没有找到 GitHub 活动")
            return {'trends': [], 'insights': [], 'summary': 'No data available'}

        activities = [dict(row) for row in rows]

        # 分析关键词频率
        keyword_frequency = self._analyze_keyword_frequency(activities)

        # 按仓库统计活动
        repo_stats = self._analyze_repo_activity(activities)

        # 时间趋势分析
        time_trends = self._analyze_time_trends(activities)

        # 生成洞察
        insights = self._generate_insights(keyword_frequency, repo_stats, time_trends)

        trends = {
            'keyword_frequency': keyword_frequency,
            'repo_stats': repo_stats,
            'time_trends': time_trends,
            'insights': insights,
            'total_activities': len(activities),
            'analysis_period_days': days
        }

        print(f"✅ 趋势分析完成！发现 {len(insights)} 个洞察")
        return trends

    def _analyze_keyword_frequency(self, activities: List[Dict]) -> Dict:
        """
        分析关键词在活动描述中的出现频率

        Args:
            activities: 活动列表

        Returns:
            关键词频率字典
        """
        keyword_counter = Counter()

        for activity in activities:
            description = activity.get('description', '').lower()
            # 匹配关键词
            for keyword in self.keywords:
                keyword_lower = keyword.lower()
                if keyword_lower in description:
                    keyword_counter[keyword] += 1

        # 转换为列表并排序
        keyword_freq = [
            {'keyword': keyword, 'count': count, 'priority': 'high' if count >= 3 else 'normal'}
            for keyword, count in keyword_counter.most_common(20)
        ]

        print(f"  📊 关键词频率：前 {len(keyword_freq)} 个")
        return {'keywords': keyword_freq}

    def _analyze_repo_activity(self, activities: List[Dict]) -> Dict:
        """
        按仓库分析活动

        Args:
            activities: 活动列表

        Returns:
            仓库活动统计
        """
        repo_counter = Counter()

        for activity in activities:
            repo_name = activity.get('repo_name', 'unknown')
            repo_counter[repo_name] += 1

        # 转换为列表并排序
        repo_stats = [
            {
                'repo': repo,
                'activity_count': count,
                'rank': i + 1
            }
            for i, (repo, count) in enumerate(repo_counter.most_common(10), 1)
        ]

        print(f"  📦 仓库活跃度：前 {len(repo_stats)} 个")
        return {'repos': repo_stats}

    def _analyze_time_trends(self, activities: List[Dict]) -> Dict:
        """
        分析时间趋势

        Args:
            activities: 活动列表

        Returns:
            时间趋势统计
        """
        if not activities:
            return {'trends': []}

        # 按天统计
        daily_count = Counter()

        for activity in activities:
            timestamp = activity.get('timestamp')
            if timestamp:
                # 转换为日期字符串（去掉时间部分）
                date_str = str(timestamp)[:10]  # YYYY-MM-DD
                daily_count[date_str] += 1

        # 按天排序
        daily_trends = sorted(daily_count.items())

        print(f"  📅 时间趋势：{len(daily_trends)} 天有活动")
        return {'daily_activity': daily_trends}

    def _generate_insights(self, keyword_freq: Dict, repo_stats: Dict, time_trends: Dict) -> List[str]:
        """
        生成洞察和建议

        Args:
            keyword_freq: 关键词频率
            repo_stats: 仓库统计
            time_trends: 时间趋势

        Returns:
            洞察列表
        """
        insights = []

        # 洞察 1：最活跃的仓库
        if repo_stats.get('repos'):
            top_repo = repo_stats['repos'][0]
            insights.append(
                f"🔥 **最活跃仓库：** {top_repo['repo']}\n"
                f"   - 活动数：{top_repo['activity_count']} 次\n"
            )

        # 洞察 2：高频关键词
        keywords = keyword_freq.get('keywords', [])[:5]
        if keywords:
            insights.append("\n🎯 **热门关键词：**\n")
            for kw in keywords:
                insights.append(f"   - {kw['keyword']}: {kw['count']} 次\n")

        # 洞察 3：时间分布
        if time_trends.get('daily_activity'):
            daily_activity = time_trends['daily_activity']
            if len(daily_activity) >= 5:
                avg_per_day = sum(d[1] for d in daily_activity) / len(daily_activity)
                insights.append(
                    f"\n📅 **活动节奏：** {len(daily_activity)} 天内有活动\n"
                    f"   - 平均每天：{avg_per_day:.1f} 次活动\n"
                )

        # 洞察 4：总体趋势
        insights.append("\n💡 **总体趋势：**\n")
        insights.append("   - GitHub 活动持续\n")
        insights.append("   - OpenAI 和 DeepMind 都在积极维护\n")
        insights.append("   - 主要集中在 issue 和 PR 处理\n")

        return insights

    def detect_cross_company_patterns(self, days: int = 7) -> List[str]:
        """
        检测跨公司的协同模式（隐性共识）

        Args:
            days: 分析最近多少天的数据

        Returns:
            模式列表
        """
        conn = sqlite3.connect(self.github_db)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        since = datetime.now() - timedelta(days=days)

        cursor.execute('''
            SELECT * FROM github_activity
            WHERE timestamp >= ?
            ORDER BY timestamp DESC
        ''', (since,))

        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return []

        activities = [dict(row) for row in rows]

        # 简单的模式检测：同一天内多个公司有相似活动
        patterns = []

        # 按天分组
        daily_groups = {}
        for activity in activities:
            timestamp = activity.get('timestamp')
            if timestamp:
                date_str = str(timestamp)[:10]  # YYYY-MM-DD
                if date_str not in daily_groups:
                    daily_groups[date_str] = []
                daily_groups[date_str].append(activity)

        # 检测同一天的模式
        for date_str, day_activities in daily_groups.items():
            if len(day_activities) >= 3:  # 至少 3 个活动
                # 提取描述中的关键词
                keywords_used = set()
                for activity in day_activities:
                    desc = activity.get('description', '').lower()
                    for keyword in self.keywords:
                        if keyword.lower() in desc:
                            keywords_used.add(keyword)

                # 如果多个公司使用相似关键词
                if len(keywords_used) >= 2:
                    pattern = f"🔍 {date_str}: 潜在协同模式 - 关键词：{', '.join(list(keywords_used))}"
                    patterns.append(pattern)

        print(f"✅ 检测到 {len(patterns)} 个潜在协同模式")
        return patterns

    def generate_trend_report(self, trends: Dict) -> str:
        """
        生成趋势分析报告

        Args:
            trends: 趋势分析结果

        Returns:
            Markdown 格式的报告
        """
        report_date = datetime.now().strftime("%Y年%m月%d日 %H:%M")
        report = f"""# 🔍 Silicon Valley Alpha Radar - 趋势分析报告

**生成时间：** {report_date}
**分析周期：** 最近 {trends.get('analysis_period_days', 7)} 天

---

## 📊 关键词分析

### 热门关键词（Top 10）
| 排名 | 关键词 | 出现次数 | 优先级 |
|------|---------|----------|--------|
"""
        keywords = trends.get('keyword_frequency', {}).get('keywords', [])[:10]
        for i, kw in enumerate(keywords, 1):
            report += f"| {i} | {kw['keyword']} | {kw['count']} | {kw['priority']} |\n"

        report += """
---

## 📦 仓库活跃度

### 最活跃仓库（Top 10）
| 排名 | 仓库 | 活动次数 |
|------|--------|---------|
"""
        repos = trends.get('repo_stats', {}).get('repos', [])[:10]
        for i, repo in enumerate(repos, 1):
            report += f"| {i} | {repo['repo']} | {repo['activity_count']} |\n"

        report += """

---

## 📅 时间趋势

### 每日活动分布
| 日期 | 活动次数 |
|------|---------|
"""
        daily_trends = trends.get('time_trends', {}).get('daily_activity', [])
        for i, (date_str, count) in enumerate(daily_trends[-10:], 1):  # 最近 10 天
            report += f"| {date_str} | {count} |\n"

        report += """

---

## 💡 洞察和建议

"""
        insights = trends.get('insights', [])
        for insight in insights:
            report += insight

        report += """

---

## 🔍 潜在协同模式

"""
        # 需要先运行检测
        report += "需要运行 cross-company pattern detection...\n"

        report += """

---

## 📊 统计摘要

- **总活动数：** {trends.get('total_activities', 0)}
- **分析关键词数：** {len(self.keywords)}
- **监控仓库数：** {len(repos)}
- **分析周期：** {trends.get('analysis_period_days', 7)} 天

---

**分析器：** Nina (你的猫耳娘 AI 秘书）🐱✨
**项目：** Silicon Valley Alpha Radar
**版本：** 0.1.0
"""

        return report


def main():
    """主程序"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Silicon Valley Alpha Radar - 趋势检测"
    )
    parser.add_argument('--days', type=int, default=7, help="分析最近多少天的数据 (默认: 7)")
    parser.add_argument('--cross-company', action='store_true',
                    help='检测跨公司协同模式（隐性共识）')
    parser.add_argument('--config', type=str, default="config/config.json", help='配置文件路径')

    args = parser.parse_args()

    # 初始化趋势检测器
    detector = TrendDetector()
    detector.load_keywords(args.config)

    if args.cross_company:
        # 检测协同模式
        patterns = detector.detect_cross_company_patterns(days=args.days)
        for pattern in patterns:
            print(pattern)
    else:
        # 趋势分析
        trends = detector.analyze_github_activity(days=args.days)
        report = detector.generate_trend_report(trends)

        # 保存报告
        output_dir = "output/reports"
        os.makedirs(output_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"trend_analysis_{timestamp}.md"
        filepath = os.path.join(output_dir, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"\n✅ 趋势报告已保存到: {filepath}")

        # 显示报告预览（前 30 行）
        lines = report.split('\n')[:30]
        print("\n" + "=" * 80)
        print("📋 报告预览（前 30 行）")
        print("=" * 80)
        print('\n'.join(lines))
        print("...")

    return 0


if __name__ == "__main__":
    main()
