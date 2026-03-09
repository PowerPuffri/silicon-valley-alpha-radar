"""
Push Formatter - 推送消息格式化器
根据不同级别生成不同格式的推送消息
"""

import json
from datetime import datetime
from typing import Dict, List


class PushFormatter:
    def __init__(self):
        """初始化推送格式化器"""

    def format_breaking(self, activities: List[Dict]) -> str:
        """
        格式化重磅级推送（立即推送）

        Args:
            activities: 活动列表（通常只有1个）

        Returns:
            格式化的消息
        """
        if not activities:
            return None

        activity = activities[0]

        # 基本信息
        title = activity.get('title', 'N/A')
        repo_name = activity.get('repo_name', 'N/A')
        author = activity.get('author', 'N/A')
        activity_type = activity.get('activity_type', 'unknown')
        url = activity.get('url', '')

        # 获取判断详情
        details = activity.get('judgment_details', {})
        reasons = details.get('reasons', [])
        matched_keywords = details.get('matched_keywords', [])

        # 构建消息
        message = f"""🚨 <b>BREAKING</b>

<b>{title}</b>

👤 <b>作者:</b> {author}
🏷️ <b>类型:</b> {activity_type}
📦 <b>仓库:</b> {repo_name}
"""

        # 添加关键词
        if matched_keywords:
            message += f"🎯 <b>关键词:</b> {', '.join(matched_keywords[:5])}\n"

        # 添加链接
        if url:
            message += f"\n🔗 <a href=\"{url}\">查看详情</a>\n"

        # 添加判断原因
        if reasons:
            message += f"\n💡 <b>判断依据:</b>\n"
            for i, reason in enumerate(reasons[:3], 1):
                message += f"   {i}. {reason}\n"

        # 添加时间戳
        message += f"\n<i>🕐 检测时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>"

        return message

    def format_important_batch(self, activities: List[Dict]) -> str:
        """
        格式化重要信息批量推送（每小时）

        Args:
            activities: 活动列表

        Returns:
            格式化的消息
        """
        if not activities:
            return None

        # 顶部标题
        message = f"""📊 <b>SV Alpha Radar | 过去1小时</b>

"""

        # 添加每个活动
        for i, activity in enumerate(activities, 1):
            title = activity.get('title', 'N/A')
            repo_name = activity.get('repo_name', 'N/A')
            author = activity.get('author', 'N/A')
            activity_type = activity.get('activity_type', 'unknown')
            url = activity.get('url', '')

            # 获取判断详情
            details = activity.get('judgment_details', {})
            reasons = details.get('reasons', [])
            score = details.get('score', 0)

            # 构建单个活动
            message += f"▸ <b>{title}</b>\n"
            message += f"   🏷️ {activity_type} | 👤 {author} | 📦 {repo_name}\n"

            # 添加主要判断原因
            if reasons:
                message += f"   💡 {reasons[0]}\n"

            # 添加链接
            if url:
                message += f"   🔗 <a href=\"{url}\">链接</a>\n"

            # 分隔符
            if i < len(activities):
                message += "\n"

        # 添加统计信息
        message += f"\n<i>📊 总计: {len(activities)} 条重要信息</i>"
        message += f"\n<i>🕐 更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}</i>"

        return message

    def format_normal_batch(self, activities: List[Dict]) -> str:
        """
        格式化普通信息批量推送（每3小时）

        Args:
            activities: 活动列表

        Returns:
            格式化的消息
        """
        if not activities:
            return None

        # 按仓库分组
        repo_groups = {}
        for activity in activities:
            repo = activity.get('repo_name', 'unknown')
            if repo not in repo_groups:
                repo_groups[repo] = []
            repo_groups[repo].append(activity)

        # 顶部标题
        message = f"""📊 <b>SV Alpha Radar | 过去3小时</b>

"""

        # 按仓库分组显示
        for repo, repo_activities in repo_groups.items():
            message += f"<b>📦 {repo}</b>\n"

            for activity in repo_activities:
                title = activity.get('title', 'N/A')
                author = activity.get('author', 'N/A')
                activity_type = activity.get('activity_type', 'unknown')
                url = activity.get('url', '')

                # 构建单个活动
                message += f"  • <b>{title}</b>\n"
                message += f"    ({activity_type} by {author})\n"

                # 添加链接
                if url:
                    message += f"    <a href=\"{url}\">链接</a>\n"

            message += "\n"

        # 添加统计信息
        message += f"<i>📊 总计: {len(activities)} 条信息</i>"
        message += f"\n<i>🕐 更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}</i>"

        return message

    def format_summary_report(self, summary: Dict) -> str:
        """
        格式化摘要报告

        Args:
            summary: 摘要数据

        Returns:
            格式化的消息
        """
        total = summary.get('total', 0)
        breaking = summary.get('breaking', 0)
        important = summary.get('important', 0)
        normal = summary.get('normal', 0)
        ignored = summary.get('ignored', 0)

        message = f"""📊 <b>SV Alpha Radar - 推送摘要</b>

📅 <b>时间:</b> {datetime.now().strftime('%Y年%m月%d日 %H:%M')}

📈 <b>统计信息:</b>
   🔴 重磅: {breaking}
   🟠 重要: {important}
   🟡 普通: {normal}
   ⚪ 忽略: {ignored}
   📊 总计: {total}

<i>💡 信息不对称是终极力量。保持优势！</i>
"""

        return message

    def format_error_alert(self, error: str, context: str = "") -> str:
        """
        格式化错误告警

        Args:
            error: 错误信息
            context: 上下文信息

        Returns:
            格式化的消息
        """
        message = f"""⚠️ <b>系统告警</b>

❌ <b>错误:</b> {error}

{context}

<i>🕐 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>
"""

        return message

    def truncate_message(self, message: str, max_length: int = 4096) -> str:
        """
        截断消息到最大长度（Telegram 限制）

        Args:
            message: 原始消息
            max_length: 最大长度

        Returns:
            截断后的消息
        """
        if len(message) <= max_length:
            return message

        return message[:max_length - 50] + "\n\n... (消息过长，已截断)"


# 测试代码
if __name__ == "__main__":
    print("📝 Silicon Valley Alpha Radar - 推送格式化器")
    print("=" * 60)

    formatter = PushFormatter()

    # 测试重磅消息
    test_breaking = [{
        'title': '重磅：GPT-5 技术预览发布',
        'repo_name': 'openai/gpt-5',
        'author': 'sama',
        'activity_type': 'release',
        'url': 'https://github.com/openai/gpt-5/releases',
        'judgment_details': {
            'reasons': ['活动类型: release (+4)', '知名作者: sama (+3)', '重磅关键词: breaking (+3)'],
            'matched_keywords': ['breaking', 'gpt'],
            'score': 10
        }
    }]

    print("\n🔴 重磅消息格式:")
    print("-" * 60)
    breaking_msg = formatter.format_breaking(test_breaking)
    print(breaking_msg)
    print("-" * 60)

    # 测试批量重要消息
    test_important = [
        {
            'title': '优化 Transformer 架构',
            'repo_name': 'deepmind/alpha',
            'author': 'demishassabis',
            'activity_type': 'pull_request',
            'url': 'https://github.com/deepmind/alpha/pull/123',
            'judgment_details': {
                'reasons': ['监控仓库: deepmind/alpha (+2)', '已合并PR (+2)'],
                'score': 4
            }
        },
        {
            'title': '新增 Embedding 方案',
            'repo_name': 'openai/whisper',
            'author': 'ilyasut',
            'activity_type': 'discussion',
            'url': 'https://github.com/openai/whisper/discussions/456',
            'judgment_details': {
                'reasons': ['知名作者: ilyasut (+3)', '监控仓库: openai/whisper (+2)'],
                'score': 5
            }
        }
    ]

    print("\n🟠 批量重要消息格式:")
    print("-" * 60)
    important_msg = formatter.format_important_batch(test_important)
    print(important_msg)
    print("-" * 60)

    # 测试批量普通消息
    test_normal = [
        {
            'title': '修复 bug',
            'repo_name': 'openai/gpt-4',
            'author': 'randomuser',
            'activity_type': 'issue',
            'url': 'https://github.com/openai/gpt-4/issues/789'
        },
        {
            'title': '文档更新',
            'repo_name': 'anthropic/claude',
            'author': 'contributor',
            'activity_type': 'comment',
            'url': 'https://github.com/anthropic/claude/issues/101'
        }
    ]

    print("\n🟡 批量普通消息格式:")
    print("-" * 60)
    normal_msg = formatter.format_normal_batch(test_normal)
    print(normal_msg)
    print("-" * 60)

    print("\n✅ 测试完成！")
