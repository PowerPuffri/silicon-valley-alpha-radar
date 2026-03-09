#!/usr/bin/env python3
"""
Final Unified Test - 最终统一测试
完全独立，不依赖其他模块
重构版本：提供有判断力的信号筛选、隐性关联分析、可行动建议
"""

import sqlite3
import json
import requests
import time
import os
from datetime import datetime, timedelta
from collections import Counter, defaultdict


def main():
    """主测试程序"""
    print("\n" + "=" * 80)
    print("🚀 Silicon Valley Alpha Radar - 最终统一测试")
    print("=" * 80)
    print(f"\n📅 测试时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 1. GitHub 数据收集
    print(f"\n[1/4] 📊 收集 GitHub 数据（最近 7 天）...")
    try:
        github_data = test_github_collection()
        print(f"   ✅ 收集到 {len(github_data)} 条活动")
    except Exception as e:
        print(f"   ❌ GitHub 数据收集失败：{e}")
        github_data = []

    # 2. 模式分析
    print(f"\n[2/4] 🔍 分析活动模式...")
    try:
        patterns = analyze_patterns(github_data)
        print(f"   ✅ 分析完成")
    except Exception as e:
        print(f"   ❌ 模式分析失败：{e}")
        patterns = {'type_distribution': {}, 'repo_distribution': {}, 'top_keywords': {}}

    # 3. 智能洞察
    print(f"\n[3/4] 🧠 生成智能洞察...")
    try:
        insights = generate_insights(github_data, patterns)
        print(f"   ✅ 发现 {len(insights)} 个重要洞察")
    except Exception as e:
        print(f"   ❌ 洞察生成失败：{e}")
        insights = []

    # 4. Telegram 推送
    print(f"\n[4/4] 📡 推送到 Telegram...")
    push_success = test_telegram_push(github_data, patterns, insights)

    # 总结
    print("\n" + "=" * 80)
    print("📊 测试总结")
    print("=" * 80)
    print(f"\n✅ GitHub 数据收集：{len(github_data)} 条")
    print(f"✅ 智能洞察：{len(insights)} 个")
    print(f"{'✅ Telegram 推送：成功' if push_success else '⚠️  Telegram 推送：失败'}")
    print("\n" + "=" * 80)
    print("🎉 最终测试完成！")
    print("=" * 80)

    return 0


def test_github_collection():
    """测试 GitHub 数据收集"""
    db_path = "storage/data/github_activity.db"

    if not os.path.exists(db_path):
        print("   ⚠️  GitHub 数据库不存在，使用模拟数据")
        # 返回模拟数据
        return [
            {'id': 'mock1', 'repo_name': 'openai/whisper', 'activity_type': 'issue',
             'author': 'user1', 'description': 'Test issue 1', 'url': 'https://github.com/openai/whisper/issues/1',
             'stars': 100, 'timestamp': datetime.now(), 'collected_at': datetime.now()},
            {'id': 'mock2', 'repo_name': 'deepmind/deepmind-research', 'activity_type': 'pull_request',
             'author': 'user2', 'description': 'Test PR 2', 'url': 'https://github.com/deepmind/deepmind-research/pull/2',
             'stars': 200, 'timestamp': datetime.now(), 'collected_at': datetime.now()}
        ]

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('''
        SELECT * FROM github_activity
        ORDER BY timestamp DESC
        LIMIT 50
    ''')

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def analyze_patterns(activities):
    """分析活动模式"""
    type_freq = Counter([a.get('activity_type', 'unknown') for a in activities])
    repo_freq = Counter([a.get('repo_name', 'unknown') for a in activities])

    # 提取关键词
    tech_keywords = [
        'transformer', 'attention', 'diffusion', 'gpt', 'llama',
        'whisper', 'stable diffusion', 'multimodal', 'embedding'
    ]

    keyword_freq = Counter()
    for activity in activities:
        desc = activity.get('description', '').lower()
        for keyword in tech_keywords:
            if keyword in desc:
                keyword_freq[keyword] += 1

    return {
        'total_activities': len(activities),
        'type_distribution': dict(type_freq),
        'repo_distribution': dict(repo_freq),
        'top_keywords': dict(keyword_freq.most_common(10))
    }


def generate_insights(activities, patterns):
    """生成智能洞察"""
    insights = []

    # 洞察 1：主要活动类型
    if patterns['type_distribution']:
        top_activity = list(patterns['type_distribution'].items())[0]
        insights.append(f"📊 主要活动：{top_activity[0]} 占 {top_activity[1]}")

    # 洞察 2：最活跃的仓库
    if patterns['repo_distribution']:
        top_repo = max(patterns['repo_distribution'].items(), key=lambda x: x[1])
        insights.append(f"🔥 最活跃仓库：{top_repo[0]}")

    # 洞察 3：技术关键词
    if patterns['top_keywords']:
        top_keywords = [f"{kw} ({count})" for kw, count in list(patterns['top_keywords'].items())[:3]]
        insights.append(f"🎯 热门技术：{', '.join(top_keywords)}")

    # 洞察 4：跨公司活动
    company_count = Counter()
    for activity in activities:
        repo = activity.get('repo_name', '')
        if 'openai' in repo.lower():
            company_count['OpenAI'] += 1
        elif 'deepmind' in repo.lower():
            company_count['DeepMind'] += 1

    if len(company_count) > 1:
        insights.append(f"🏢 活跃公司：{', '.join(company_count.keys())}")

    # 洞察 5：时间分布
    if activities:
        insights.append(f"⏰  最近 7 天活动：{len(activities)} 条")

    return insights


# ============================================
# 信号分级与富报告生成
# ============================================

# 知名作者列表（高权重）
NOTABLE_AUTHORS = {
    'sama', 'ilyasut', 'gdb',  # OpenAI
    'demishassabis', 'mustafasuleyman',  # DeepMind
    'karpathy', 'lecun', 'jeffdean',  # 其他AI领袖
    'doriangpt', 'stanfordnlp'
}

# 高优先级关键词
BREAKING_KEYWORDS = {'release', 'launch', 'announce', 'breaking', 'new', 'update', 'published'}

# 技术关键词列表
TECH_KEYWORDS = [
    'transformer', 'attention', 'diffusion', 'gpt', 'llama',
    'whisper', 'stable diffusion', 'multimodal', 'embedding',
    'agents', 'reinforcement learning', 'scaling', 'neural',
    'agi', 'reasoning', 'architecture', 'spiking'
]


def find_breaking_signals(activities):
    """
    找出高优先级信号
    条件：release类型 OR 重要关键词 OR 知名作者
    """
    breaking = []

    for activity in activities:
        score = 0
        reasons = []

        # 1. 检查活动类型
        activity_type = activity.get('activity_type', '').lower()
        if activity_type == 'release':
            score += 3
            reasons.append('release')

        # 2. 检查关键词
        desc = activity.get('description', '').lower()
        for keyword in BREAKING_KEYWORDS:
            if keyword in desc:
                score += 2
                reasons.append(f'关键词:{keyword}')
                break

        # 3. 检查知名作者
        author = activity.get('author', '').lower()
        if author in NOTABLE_AUTHORS:
            score += 3
            reasons.append(f'知名作者:{author}')

        if score >= 2:
            breaking.append({
                'activity': activity,
                'score': score,
                'reasons': reasons
            })

    # 按分数排序
    breaking.sort(key=lambda x: x['score'], reverse=True)
    return breaking[:5]  # 最多返回5条


def find_watching_signals(activities, patterns):
    """
    找出值得关注的信号
    条件：频率突增 + 多公司讨论
    """
    watching = []

    # 1. 关键词频率分析
    keyword_freq = patterns.get('top_keywords', {})
    for keyword, count in keyword_freq.items():
        if count >= 5:
            watching.append({
                'type': 'keyword_surge',
                'keyword': keyword,
                'count': count,
                'message': f'"{keyword}" 关键词出现 {count} 次'
            })

    # 2. 按公司统计活跃度
    company_count = Counter()
    company_activities = defaultdict(list)

    for activity in activities:
        repo = activity.get('repo_name', '').lower()
        if 'openai' in repo:
            company_count['OpenAI'] += 1
            company_activities['OpenAI'].append(activity)
        elif 'deepmind' in repo or 'google' in repo:
            company_count['DeepMind'] += 1
            company_activities['DeepMind'].append(activity)
        elif 'anthropic' in repo:
            company_count['Anthropic'] += 1
            company_activities['Anthropic'].append(activity)

    # 3. 检测高活跃公司
    for company, count in company_count.items():
        if count >= 5:
            watching.append({
                'type': 'company_active',
                'company': company,
                'count': count,
                'message': f'{company} 本周活跃度 {count} 条'
            })

    return watching[:5]  # 最多返回5条


def detect_correlations(activities):
    """
    检测隐性关联 - 复用类似 detect_hidden_consensus 的逻辑
    找出跨公司讨论的共同话题
    """
    correlations = []

    # 按公司分组关键词
    company_keywords = defaultdict(Counter)

    for activity in activities:
        repo = activity.get('repo_name', '').lower()
        desc = activity.get('description', '').lower()

        # 识别公司
        company = None
        if 'openai' in repo:
            company = 'OpenAI'
        elif 'deepmind' in repo or 'google' in repo:
            company = 'DeepMind'
        elif 'anthropic' in repo:
            company = 'Anthropic'

        if not company:
            continue

        # 提取关键词
        for keyword in TECH_KEYWORDS:
            if keyword in desc:
                company_keywords[company][keyword] += 1

    # 找出跨公司共同讨论的关键词
    keyword_companies = defaultdict(list)
    for company, keywords in company_keywords.items():
        for keyword, count in keywords.items():
            if count >= 2:  # 至少讨论2次
                keyword_companies[keyword].append((company, count))

    # 筛选出多公司共识
    for keyword, company_list in keyword_companies.items():
        if len(company_list) >= 2:
            companies = [c[0] for c in company_list]
            total_count = sum(c[1] for c in company_list)
            correlations.append({
                'keyword': keyword,
                'companies': companies,
                'total_count': total_count,
                'message': f"{' + '.join(companies)} 都在讨论 {keyword}",
                'insight': '可能是下一个热点方向'
            })

    # 按总讨论数排序
    correlations.sort(key=lambda x: x['total_count'], reverse=True)
    return correlations[:3]  # 最多返回3条


def format_bar_chart(count, max_count, bar_length=10):
    """生成简单的文本条形图"""
    filled = int(count / max_count * bar_length) if max_count > 0 else 0
    return '█' * filled + '░' * (bar_length - filled)


def generate_rich_report(activities, patterns, insights):
    """
    生成富文本报告
    格式：BREAKING | WATCHING | 隐性关联 | 概览 | 建议
    """
    report_date = datetime.now().strftime('%Y-%m-%d')

    # 1. 高优先级信号
    breaking = find_breaking_signals(activities)

    # 2. 值得关注信号
    watching = find_watching_signals(activities, patterns)

    # 3. 隐性关联
    correlations = detect_correlations(activities)

    # 构建报告
    lines = []

    # 头部
    lines.append(f"🚨 <b>SV Alpha Radar</b> | {report_date}")
    lines.append("")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("⚡ <b>BREAKING | 高优先级信号</b>")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("")

    if breaking:
        for item in breaking:
            activity = item['activity']
            desc = activity.get('description', 'N/A')[:50]
            author = activity.get('author', 'unknown')
            url = activity.get('url', '')

            # 提取仓库名
            repo = activity.get('repo_name', '')
            repo_short = repo.split('/')[-1] if '/' in repo else repo

            lines.append(f"• <b>{repo_short}</b>: {desc}...")
            if url:
                lines.append(f"  👤 {author} | <a href=\"{url}\">🔗 链接</a>")
            else:
                lines.append(f"  👤 {author}")
            lines.append("")
    else:
        lines.append("暂无高优先级信号")
        lines.append("")

    # 值得关注
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("👀 <b>WATCHING | 值得关注</b>")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("")

    if watching:
        for item in watching:
            lines.append(f"• {item['message']}")
        lines.append("")
    else:
        lines.append("暂无特别关注信号")
        lines.append("")

    # 隐性关联
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("🔗 <b>隐性关联</b>")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("")

    if correlations:
        for item in correlations:
            lines.append(f"• {item['message']}")
            lines.append(f"  → {item['insight']}")
            lines.append("")
    else:
        lines.append("暂未检测到跨公司共识")
        lines.append("")

    # 概览
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("📊 <b>本周概览</b>")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("")

    # 统计各公司活动
    company_count = Counter()
    for activity in activities:
        repo = activity.get('repo_name', '').lower()
        if 'openai' in repo:
            company_count['OpenAI'] += 1
        elif 'deepmind' in repo or 'google' in repo:
            company_count['DeepMind'] += 1
        elif 'anthropic' in repo:
            company_count['Anthropic'] += 1

    if company_count:
        max_count = max(company_count.values())
        for company, count in sorted(company_count.items(), key=lambda x: x[1], reverse=True):
            bar = format_bar_chart(count, max_count)
            lines.append(f"{company}: {bar} {count}")

    lines.append("")

    # 建议
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("💡 <b>建议</b>")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("")

    recommendation = generate_recommendation(breaking, watching, correlations)
    lines.append(recommendation)
    lines.append("")

    # 收集链接
    links = []
    for item in breaking[:3]:
        url = item['activity'].get('url', '')
        if url:
            repo = item['activity'].get('repo_name', '详情')
            links.append(f'<a href="{url}">{repo.split("/")[-1]}</a>')

    if links:
        lines.append(f"📎 详情: {' | '.join(links)}")

    return '\n'.join(lines)


def generate_recommendation(breaking, watching, correlations):
    """
    生成可行动建议
    """
    recommendations = []

    # 基于高优先级信号
    if breaking:
        top_breaking = breaking[0]
        repo = top_breaking['activity'].get('repo_name', '')
        repo_name = repo.split('/')[-1] if '/' in repo else repo
        recommendations.append(f"重点关注 {repo_name} 的最新动态")

    # 基于隐性关联
    if correlations:
        top_correlation = correlations[0]
        keyword = top_correlation['keyword']
        companies = ' + '.join(top_correlation['companies'][:2])
        recommendations.append(f"建议深入调研 {companies} 在 {keyword} 方向的布局")

    # 基于值得关注信号
    keyword_watching = [w for w in watching if w['type'] == 'keyword_surge']
    if keyword_watching:
        top_keyword = keyword_watching[0]['keyword']
        recommendations.append(f'追踪 "{top_keyword}" 相关的技术进展')

    if not recommendations:
        recommendations.append("持续监控硅谷AI实验室动态，暂无紧急关注事项")

    return recommendations[0] if recommendations else "继续监控中"


def test_telegram_push(github_data, patterns, insights):
    """测试 Telegram 推送 - 使用富报告格式"""
    try:
        with open("config/config.json", 'r', encoding='utf-8') as f:
            config = json.load(f)
            bot_token = config.get('telegram', {}).get('botToken', '')
            chat_id = config.get('telegram', {}).get('chatId', '7974510481')
    except:
        bot_token = ''
        chat_id = "7974510481"

    if not bot_token:
        print("   ⚠️  未找到 Telegram Bot Token")
        return False

    # 生成富报告
    report = generate_rich_report(github_data, patterns, insights)

    # 添加时间戳
    report += f"\n\n<i>🕐 {datetime.now().strftime('%Y-%m-%d %H:%M')} | 数据源: GitHub(7d)</i>"

    # 发送
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    payload = {
        'chat_id': chat_id,
        'text': report,
        'parse_mode': 'HTML',
        'disable_web_page_preview': True
    }

    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()

        result = response.json()

        if result.get('ok'):
            print(f"   ✅ 消息发送成功！")
            return True
        else:
            print(f"   ❌ 消息发送失败: {result.get('description', 'Unknown')}")
            return False

    except Exception as e:
        print(f"   ❌ 网络错误: {e}")
        return False


if __name__ == "__main__":
    import os
    import sys

    sys.exit(main())
