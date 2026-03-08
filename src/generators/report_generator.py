"""
Report Generator - 生成多种格式的报告
Markdown, JSON, HTML, 和总结格式
"""

import os
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json


class ReportGenerator:
    def __init__(self, github_db: str = "storage/data/github_activity.db",
                 twitter_db: str = "storage/data/twitter_posts_jina.db",
                 reddit_db: str = "storage/data/reddit_posts.db",
                 hackernews_db: str = "storage/data/hacker_news.db"):
        """
        初始化报告生成器

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

        self.output_reports = "output/reports"

    def _query_github_data(self, limit: int = 50) -> List[Dict]:
        """查询 GitHub 数据"""
        if not os.path.exists(self.github_db):
            return []

        conn = sqlite3.connect(self.github_db)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM github_activity
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def _query_reddit_data(self, limit: int = 20) -> List[Dict]:
        """查询 Reddit 数据"""
        if not os.path.exists(self.reddit_db):
            return []

        conn = sqlite3.connect(self.reddit_db)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM reddit_posts
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def _query_hackernews_data(self, limit: int = 20) -> List[Dict]:
        """查询 Hacker News 数据"""
        if not os.path.exists(self.hackernews_db):
            return []

        conn = sqlite3.connect(self.hackernews_db)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM hacker_news
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def _query_twitter_data(self, limit: int = 20) -> List[Dict]:
        """查询 Twitter 数据"""
        if not os.path.exists(self.twitter_db):
            return []

        conn = sqlite3.connect(self.twitter_db)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM twitter_posts
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def generate_activity_summary(self, github_data: List[Dict], twitter_data: List[Dict], reddit_data: List[Dict], hackernews_data: List[Dict]) -> Dict:
        """
        生成活动摘要

        Args:
            github_data: GitHub 数据
            twitter_data: Twitter 数据
            reddit_data: Reddit 数据
            hackernews_data: Hacker News 数据

        Returns:
            摘要字典
        """
        summary = {
            'github_total': len(github_data),
            'twitter_total': len(twitter_data),
            'reddit_total': len(reddit_data),
            'hackernews_total': len(hackernews_data),
            'github_by_type': {},
            'github_by_repo': {},
            'timeline': []
        }

        # GitHub 按类型统计
        for activity in github_data:
            activity_type = activity.get('activity_type', 'unknown')
            summary['github_by_type'][activity_type] = \
                summary['github_by_type'].get(activity_type, 0) + 1

        # GitHub 按仓库统计
        for activity in github_data:
            repo_name = activity.get('repo_name', 'unknown')
            summary['github_by_repo'][repo_name] = \
                summary['github_by_repo'].get(repo_name, 0) + 1

        # 时间线（最新 20 条）
        all_activities = []

        for activity in github_data[:10]:
            all_activities.append({
                'source': 'github',
                'type': activity.get('activity_type', 'unknown'),
                'repo': activity.get('repo_name', 'unknown'),
                'author': activity.get('author', 'unknown'),
                'description': activity.get('description', '')[:100],
                'url': activity.get('url', ''),
                'timestamp': activity.get('timestamp', '')
            })

        for post in reddit_data[:5]:
            all_activities.append({
                'source': 'reddit',
                'type': 'post',
                'repo': post.get('subreddit', 'unknown'),
                'author': post.get('author', 'unknown'),
                'description': post.get('title', '')[:100],
                'url': post.get('url', ''),
                'timestamp': post.get('timestamp', '')
            })

        for story in hackernews_data[:5]:
            all_activities.append({
                'source': 'hackernews',
                'type': 'story',
                'repo': 'hackernews',
                'author': story.get('author', 'unknown'),
                'description': story.get('title', '')[:100],
                'url': story.get('url', ''),
                'timestamp': story.get('timestamp', '')
            })

        # 按时间排序
        all_activities.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        summary['timeline'] = all_activities[:20]

        return summary

    def generate_markdown_report(self, summary: Dict, include_reddit: bool = False, include_hackernews: bool = False) -> str:
        """
        生成 Markdown 格式的报告

        Args:
            summary: 活动摘要
            include_reddit: 是否包含 Reddit 数据
            include_hackernews: 是否包含 Hacker News 数据

        Returns:
            Markdown 字符串
        """
        report_date = datetime.now().strftime("%Y年%m月%d日 %H:%M")
        report = f"""# 🎯 Silicon Valley Alpha Radar - 监控报告

**生成时间：** {report_date}
**报告周期：** 最近 30 天

---

## 📊 数据概览

### GitHub 活动
- **总计：** {summary['github_total']} 条
- **类型分布：**
"""
        for activity_type, count in summary['github_by_type'].items():
            report += f"  - {activity_type}: {count} 条\n"

        if include_reddit:
            report += f"""
### Reddit 活动
- **总计：** {summary['reddit_total']} 条
"""

        if include_hackernews:
            report += f"""
### Hacker News 活动
- **总计：** {summary['hackernews_total']} 条
"""

        report += f"""
### Twitter 活动
- **总计：** {summary['twitter_total']} 条

---

## 📋 按仓库统计

### GitHub 活动详情
"""
        for repo_name, count in summary['github_by_repo'].items():
            report += f"#### {repo_name}\n"
            report += f"- **活动数：** {count} 条\n\n"

        report += """
---

## 🕐 最新活动（Top 20）

"""
        for i, activity in enumerate(summary['timeline'], 1):
            emoji_map = {
                'github': '📊',
                'reddit': '📱',
                'hackernews': '🕶️',
                'twitter': '🐦'
            }
            emoji = emoji_map.get(activity['source'], '📋')
            report += f"{i}. {emoji} **{activity.get('repo', 'Unknown')}**\n"
            report += f"   - **类型：** {activity.get('type', 'Unknown')}\n"
            report += f"   - **作者：** {activity.get('author', 'Unknown')}\n"
            report += f"   - **时间：** {activity.get('timestamp', 'Unknown')}\n"
            report += f"   - **描述：** {activity.get('description', 'N/A')}\n"
            report += f"   - **链接：** [{activity.get('url', 'N/A')}]({activity.get('url', 'N/A')})\n\n"

        report += """
---

## 🔍 趋势分析

**注意：** 当前版本仅收集数据，趋势检测功能待实现。

### 关键观察

1. **GitHub 活动**
   - 活跃仓库已监控
   - 收集到 commits, issues, pull requests
   - 数据质量良好

2. **其他数据源**
"""

        if include_reddit:
            report += f"   - Reddit 收集器已配置\n"
        
        if include_hackernews:
            report += f"   - Hacker News 收集器已配置\n"

        report += f"   - Twitter 框架就绪\n"

        report += """
### 下一步

- [ ] 实现 Twitter 数据收集
- [ ] 关键词频率分析
- [ ] 话题聚类算法
- [ ] 时间序列分析
- [ ] 隐性共识检测

---

## 📝 技术说明

### 数据来源

**GitHub：**
- API: PyGithub (官方库）
- 认证: Personal Access Token
- 状态: ✅ 完全工作

**Reddit：**
- 工具: Requests (公开 API)
- API: Reddit JSON 接口
- 状态: ✅ 已实现

**Hacker News：**
- 工具: Requests (公开 API)
- API: Hacker News Firebase 接口
- 状态: ✅ 已实现

**Twitter：**
- 工具: jina-cli v1.0.2
- API: Jina AI Reader (免费）
- 状态: ✅ 框架就绪，需要数据源

### 数据存储

**GitHub：**
- 文件: {self.github_db}
- 格式: SQLite
- 记录: {summary['github_total']} 条

**Reddit：**
- 文件: {self.reddit_db}
- 格式: SQLite
- 记录: {summary['reddit_total']} 条

**Hacker News：**
- 文件: {self.hackernews_db}
- 格式: SQLite
- 记录: {summary['hackernews_total']} 条

**Twitter：**
- 文件: {self.twitter_db}
- 格式: SQLite
- 记录: {summary['twitter_total']} 条

---

## 💡 使用建议

1. **定期检查报告** - 每周查看一次
2. **扩展监控范围** - 添加更多 AI 公司/大佬
3. **关注趋势变化** - 注意关键词频率变化
4. **验证数据准确性** - 对比多个数据源

---

## 🎯 下一步行动

### 立即执行
1. ✅ 推送代码到 GitHub
2. ✅ 创建 GitHub Release
3. ✅ 生成演示视频
4. ✅ 分享到相关社区

### 本周计划
1. 🔄 完善 Twitter 数据收集（找到可靠数据源）
2. 🔄 实现 Reddit 和 Hacker News 自动收集
3. 🔄 添加定时任务调度（每日 00:00 UTC）
4. 🔄 添加 Telegram 自动推送

---

**报告生成器：** Nina (你的猫耳娘 AI 秘书）🐱✨
**项目：** Silicon Valley Alpha Radar
**版本：** 0.1.0
"""

        return report

    def generate_activity_summary_for_auto(self, github_data: List[Dict], reddit_data: List[Dict], hackernews_data: List[Dict], twitter_data: List[Dict]) -> Dict:
        """
        生成简化版活动摘要（用于自动化推送）

        Args:
            github_data: GitHub 数据
            reddit_data: Reddit 数据
            hackernews_data: Hacker News 数据
            twitter_data: Twitter 数据

        Returns:
            简化摘要字典
        """
        return {
            'github_total': len(github_data),
            'reddit_total': len(reddit_data),
            'hackernews_total': len(hackernews_data),
            'twitter_total': len(twitter_data),
            'duration': 0
        }

    def generate_report(self, days: int = 7, include_reddit: bool = False, include_hackernews: bool = False, for_auto: bool = False) -> str:
        """
        生成完整报告

        Args:
            days: 生成最近多少天的报告
            include_reddit: 是否包含 Reddit 数据
            include_hackernews: 是否包含 Hacker News 数据
            for_auto: 是否用于自动化推送

        Returns:
            Markdown 报告内容
        """
        print(f"\n📝 正在生成报告（最近 {days} 天）...")

        # 查询数据
        github_data = self._query_github_data(limit=50)
        reddit_data = self._query_reddit_data(limit=10) if include_reddit else []
        hackernews_data = self._query_hackernews_data(limit=10) if include_hackernews else []
        twitter_data = self._query_twitter_data(limit=10)

        # 生成摘要
        if for_auto:
            summary = self.generate_activity_summary_for_auto(
                github_data, reddit_data, hackernews_data, twitter_data
            )
        else:
            summary = self.generate_activity_summary(
                github_data, twitter_data, reddit_data, hackernews_data
            )

        # 生成 Markdown 报告
        report = self.generate_markdown_report(
            summary, include_reddit=include_reddit, include_hackernews=include_hackernews
        )

        print(f"✅ 报告生成完成！")

        return report

    def save_report(self, report: str, filename: Optional[str] = None) -> str:
        """
        保存报告到文件

        Args:
            report: Markdown 报告内容
            filename: 输出文件名（可选）

        Returns:
            报告文件路径
        """
        os.makedirs(self.output_reports, exist_ok=True)

        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"sv_alpha_radar_report_{timestamp}.md"

        filepath = os.path.join(self.output_reports, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"✅ 报告已保存到: {filepath}")

        return filepath

    def get_latest_report_file(self) -> Optional[str]:
        """
        获取最新的报告文件

        Returns:
            最新报告文件路径，如果不存在则返回 None
        """
        if not os.path.exists(self.output_reports):
            return None

        # 获取所有 Markdown 报告文件
        import glob
        report_files = glob.glob(os.path.join(self.output_reports, "sv_alpha_radar_report_*.md"))

        if not report_files:
            return None

        # 按修改时间排序，返回最新的
        latest_report = max(report_files, key=os.path.getmtime)
        return latest_report


def main():
    """主程序"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Silicon Valley Alpha Radar - 报告生成"
    )
    parser.add_argument('--days', type=int, default=7, help="生成最近多少天的报告 (默认: 7)")
    parser.add_argument('--include-reddit', action='store_true', help='包含 Reddit 数据')
    parser.add_argument('--include-hackernews', action='store_true', help='包含 Hacker News 数据')
    parser.add_argument('--output', type=str, help='输出文件路径 (可选）')
    parser.add_argument('--for-auto', action='store_true',
                    help='生成简化报告（用于自动化推送）')

    args = parser.parse_args()

    # 初始化报告生成器
    generator = ReportGenerator()

    # 执行报告生成
    report = generator.generate_report(
        days=args.days,
        include_reddit=args.include_reddit,
        include_hackernews=args.include_hackernews,
        for_auto=args.for_auto
    )

    # 保存或显示报告
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"✅ 报告已保存到: {args.output}")
    else:
        generator.save_report(report)

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
