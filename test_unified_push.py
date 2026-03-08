#!/usr/bin/env python3
"""
统一测试 - 完整的自动化推送（修复 datetime 冲突版本）
"""

import os
import sys
import json
import time
from typing import List, Dict
from collections import Counter
import sqlite3
import requests

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# 延迟导入这些可能冲突的模块
github_monitor = None
telegram_tester = None

# 等运行时再导入


class UnifiedPushTest:
    def __init__(self, chat_id: str = "7974510481"):
        """
        初始化统一推送测试器
        """
        self.chat_id = chat_id
        self.storage_path = "storage/data/github_activity.db"
        self.telegram_token = None
        self.keywords = []

        # 加载配置
        self._load_config()

    def _load_config(self):
        """加载配置"""
        try:
            with open("config/config.json", 'r', encoding='utf-8') as f:
                config = json.load(f)
            self.telegram_token = config.get('telegram', {}).get('botToken', '')
            self.keywords = config.get('keywords', [])
            print(f"✅ 配置加载完成，token 长度: {len(self.telegram_token)}")
        except Exception as e:
            print(f"⚠️  配置加载失败: {e}")
            self.telegram_token = ''
            self.keywords = []

    def _query_github_data(self, limit: int = 100) -> List[Dict]:
        """查询 GitHub 数据"""
        if not os.path.exists(self.storage_path):
            return []

        conn = sqlite3.connect(self.storage_path)
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

    def _extract_tech_keywords(self, text: str) -> List[str]:
        """提取技术关键词"""
        if not text:
            return []

        text_lower = text.lower()
        tech_keywords = [
            'transformer', 'attention', 'diffusion', 'gpt', 'llama',
            'whisper', 'stable diffusion', 'multimodal', 'embedding'
        ]

        keywords = []
        for keyword in tech_keywords:
            if keyword.lower() in text_lower:
                keywords.append(keyword)

        return list(set(keywords))

    def _analyze_activity_patterns(self, activities: List[Dict]) -> Dict:
        """分析活动模式"""
        type_freq = Counter([a.get('activity_type', 'unknown') for a in activities])
        repo_freq = Counter([a.get('repo_name', 'unknown') for a in activities])

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
            'top_keywords': dict(keyword_freq.most_common(10))
        }

    def _generate_smart_insights(self, activities: List[Dict]) -> List[str]:
        """生成智能洞察"""
        if not activities:
            return []

        patterns = self._analyze_activity_patterns(activities)
        insights = []

        # 主要活动类型
        top_activity = list(patterns['type_distribution'].items())[0]
        insights.append(f"📊 主要活动：{top_activity[0]} 占 {top_activity[1]}")

        # 最活跃的仓库
        top_repo = list(patterns['repo_distribution'].most_common(1))[0]
        insights.append(f"🔥 最活跃仓库：{top_repo[0]}")

        # 技术关键词
        if patterns['top_keywords']:
            top_keywords = list(patterns['top_keywords'].items())[:5]
            if top_keywords:
                insights.append(f"🎯 热门技术关键词：{', '.join([kw[0] for kw in top_keywords])}")

        return insights

    def _send_telegram_message(self, message: str) -> Dict:
        """发送 Telegram 消息"""
        if not self.telegram_token:
            return {'success': False, 'error': 'No token'}

        url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"

        payload = {
            'chat_id': self.chat_id,
            'text': message,
            'parse_mode': 'HTML'
        }

        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()

            result = response.json()

            if result.get('ok'):
                print("✅ Telegram 消息发送成功")
                return {'success': True}
            else:
                print(f"❌ Telegram 消息发送失败: {result.get('description', 'Unknown')}")
                return {'success': False, 'error': result.get('description')}

        except Exception as e:
            print(f"❌ 网络错误: {e}")
            return {'success': False, 'error': str(e)}

    def run_unified_test(self, days: int = 7):
        """运行统一测试"""
        print(f"\n📅 [{time.strftime('%Y-%m-%d %H:%M:%S')}] 统一测试开始（最近 {days} 天）")

        # 1. GitHub 数据收集
        print(f"\n[1/4] 📊 收集 GitHub 数据...")
        try:
            # 延迟导入
            global github_monitor
            from collectors.github_monitor import GitHubMonitor
            github_monitor_obj = GitHubMonitor()
            github_activities = github_monitor_obj.monitor_all_repos(days=days)
            print(f"   ✅ GitHub 数据收集完成，{len(github_activities)} 条活动")
        except Exception as e:
            print(f"   ❌ GitHub 数据收集失败：{e}")
            return 1

        # 2. 智能洞察生成
        print(f"\n[2/4] 🔍 生成智能洞察...")
        try:
            insights = self._generate_smart_insights(github_activities)
            if insights:
                print(f"   ✅ 发现 {len(insights)} 个重要洞察")
            else:
                print(f"   ⚠️  智能洞察生成完成，但没有发现重要趋势")
        except Exception as e:
            print(f"   ❌ 智能洞察生成失败：{e}")
            return 1

        # 3. 生成报告
        print(f"\n[3/4] 📝 生成报告...")
        try:
            report = f"""<b>🔍 Silicon Valley Alpha Radar - 发现 {len(insights)} 个重要信号</b>

---

<b>📊 数据概览</b>
• GitHub 活动: {len(github_activities)} 条

<b>🧠 关键发现</b>
{chr(10).join([f"{i}. {insight}" for i, insight in enumerate(insights, 1)])}

---
<i>🕐 检测时间: {time.strftime('%Y-%m-%d %H:%M')}</i>
<i>📊 数据源: GitHub（最近 {days} 天）</i>
<i>💡 智能分析: 频率检测 + 相关性分析 + 模式识别</i>
"""
            print(f"   ✅ 报告生成完成，{len(report)} 字符")
        except Exception as e:
            print(f"   ❌ 报告生成失败：{e}")
            return 1

        # 4. Telegram 推送
        print(f"\n[4/4] 📡 推送到 Telegram...")
        try:
            result = self._send_telegram_message(report)
            if result.get('success'):
                print(f"   ✅ Telegram 推送成功！")
            else:
                print(f"   ❌ Telegram 推送失败：{result.get('error', 'Unknown')}")

        except Exception as e:
            print(f"   ❌ Telegram 推送失败：{e}")

        # 总结
        print(f"\n" + "=" * 80)
        print("📊 测试总结")
        print("=" * 80)
        print(f"\n✅ GitHub 数据收集：{len(github_activities)} 条")
        print(f"✅ 智能洞察生成：{len(insights)} 个")
        print(f"✅ 报告生成：{len(report)} 字符")
        print(f"{'✅ Telegram 推送：' + f'{len(report)} 字符' if result.get('success') else '❌ Telegram 推送：' + f'{result.get('error', 'Unknown')}'}")
        print(f"\n" + "=" * 80)
        print("🎉 统一测试完成！")
        print("=" * 80)

        return 0


def main():
    """主程序"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Silicon Valley Alpha Radar - 统一推送测试"
    )
    parser.add_argument('--days', type=int, default=7, help="分析最近多少天的数据")
    parser.add_argument('--chat-id', type=str, default="7974510481", help="Telegram Chat ID")

    args = parser.parse_args()

    # 运行测试
    tester = UnifiedPushTest(chat_id=args.chat_id)
    return tester.run_unified_test(days=args.days)


if __name__ == "__main__":
    sys.exit(main())
