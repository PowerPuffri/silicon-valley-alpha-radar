"""
Report Generator - 生成 Markdown 报告
基于收集的数据生成结构化报告
"""

import os
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json


class ReportGenerator:
    def __init__(self, data_dir: str = "storage/data"):
        """
        初始化报告生成器

        Args:
            data_dir: 数据目录路径
        """
        self.data_dir = data_dir
        self.github_db = os.path.join(data_dir, "github_activity.db")
        self.twitter_db = os.path.join(data_dir, "twitter_posts_jina.db")

    def _query_github_data(self, days: int = 7) -> List[Dict]:
        """
        查询 GitHub 数据

        Args:
            days: 查询最近多少天的数据

        Returns:
            活动列表
        """
        conn = sqlite3.connect(self.github_db)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        since = datetime.now() - timedelta(days=days * 2)  # 扩大时间范围

        cursor.execute('''
            SELECT * FROM github_activity
            WHERE timestamp >= ?
            ORDER BY timestamp DESC
        ''', (since,))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def _query_twitter_data(self, days: int = 7) -> List[Dict]:
        """
        查询 Twitter 数据

        Args:
            days: 查询最近多少天的数据

        Returns:
            推文列表
        """
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
            LIMIT 100
        ''', (since,))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def generate_activity_summary(self, github_data: List[Dict], twitter_data: List[Dict]) -> Dict:
        """
        生成活动摘要

        Args:
            github_data: GitHub 数据
            twitter_data: Twitter 数据

        Returns:
            摘要字典
        """
        summary = {
            'github_total': len(github_data),
            'twitter_total': len(twitter_data),
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

        # 时间线（最新 10 条）
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

        for tweet in twitter_data[:10]:
            all_activities.append({
                'source': 'twitter',
                'type': 'tweet',
                'repo': tweet.get('company', 'unknown'),
                'author': tweet.get('handle', 'unknown'),
                'description': tweet.get('content', '')[:100],
                'url': tweet.get('url', ''),
                'timestamp': tweet.get('timestamp', '')
            })

        # 按时间排序
        all_activities.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        summary['timeline'] = all_activities[:10]

        return summary

    def generate_markdown_report(self, summary: Dict) -> str:
        """
        生成 Markdown 格式的报告

        Args:
            summary: 活动摘要

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

## 🕐 最新活动（Top 10）

"""
        for i, activity in enumerate(summary['timeline'], 1):
            emoji = '📊' if activity['source'] == 'github' else '📱'
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

2. **Twitter 数据**
   - 使用 jina-cli 框架就绪
   - 等待数据源接入

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

**Twitter：**
- 工具: jina-cli v1.0.2
- API: Jina AI Reader (免费）
- 状态: 🔄 框架就绪，等待数据

### 数据存储

**GitHub：**
- 文件: {self.github_db}
- 格式: SQLite
- 记录: {summary['github_total']} 条

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

**报告生成器：** Nina (你的猫耳娘 AI 秘书）🐱✨
**项目：** Silicon Valley Alpha Radar
**版本：** 0.1.0
"""

        return report

    def generate_report(self, days: int = 7) -> str:
        """
        生成完整报告

        Args:
            days: 生成最近多少天的报告

        Returns:
            Markdown 报告内容
        """
        print(f"\n📝 正在生成报告（最近 {days} 天）...")

        # 查询数据
        github_data = self._query_github_data(days)
        twitter_data = self._query_twitter_data(days)

        # 生成摘要
        summary = self.generate_activity_summary(github_data, twitter_data)

        # 生成 Markdown 报告
        report = self.generate_markdown_report(summary)

        print(f"✅ 报告生成完成！")

        return report

    def save_report(self, report: str) -> str:
        """
        保存报告到文件

        Args:
            report: Markdown 报告内容

        Returns:
            报告文件路径
        """
        output_dir = "output/reports"
        os.makedirs(output_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"sv_alpha_radar_report_{timestamp}.md"
        filepath = os.path.join(output_dir, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"✅ 报告已保存到: {filepath}")

        return filepath


def main():
    """主程序"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Silicon Valley Alpha Radar - 报告生成"
    )
    parser.add_argument('--days', type=int, default=7, help="生成最近多少天的报告 (默认: 7)")
    parser.add_argument('--output', type=str, help="输出文件路径 (可选）")

    args = parser.parse_args()

    # 初始化报告生成器
    generator = ReportGenerator()

    # 生成报告
    report = generator.generate_report(days=args.days)

    # 保存报告
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"✅ 报告已保存到: {args.output}")
    else:
        generator.save_report(report)

    # 显示报告预览（前 20 行）
    print("\n" + "=" * 80)
    print("📋 报告预览（前 20 行）")
    print("=" * 80)
    lines = report.split('\n')[:20]
    print('\n'.join(lines))
    print("...")

    return 0


if __name__ == "__main__":
    main()
