"""
Jina CLI 数据收集器 - 真正能工作的数据收集
使用 subprocess 调用 jina-cli 工具
"""

import os
import sys
import subprocess
import json
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict
from collections import Counter

# 添加项目根目录到 Python 路径
project_root = '/Users/zhipu_glm/.openclaw/workspace/silicon-valley-alpha-radar'
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'config'))

from data_sources_config import DATA_SOURCES_CONFIG, calculate_priority


def jina_read_url(url: str, timeout: int = 30) -> Dict:
    """
    使用 jina-cli 读取 URL

    Args:
        url: 要读取的 URL
        timeout: 超时时间（秒）

    Returns:
        解析后的数据
    """
    try:
        print(f"   📡 jina read {url}")

        # 调用 jina-cli
        result = subprocess.run(
            ['jina', 'read', url],
            capture_output=True,
            text=True,
            timeout=timeout
        )

        if result.returncode != 0:
            print(f"      ❌ jina read 失败: {result.stderr[:200]}")
            return None

        # 解析 JSON 输出
        content = result.stdout

        # jina-cli 返回的是 markdown，不是 JSON
        # 需要解析 markdown 内容
        return {
            'url': url,
            'content': content,
            'success': True
        }

    except subprocess.TimeoutExpired:
        print(f"      ❌ 超时: {timeout} 秒")
        return None
    except Exception as e:
        print(f"      ❌ jina read 错误: {e}")
        return None


def collect_twitter_with_jina(handles: List[str], days: int = 7) -> List[Dict]:
    """
    使用 jina-cli 收集 Twitter 数据

    Args:
        handles: Twitter 账号列表（@sama, @OpenAI 等）
        days: 收集最近多少天

    Returns:
        推文列表
    """
    print("\n🟦 使用 jina-cli 收集 Twitter 数据...")
    print(f"   账号数量: {len(handles)}")

    tweets = []

    for handle in handles:
        url = f"https://twitter.com/{handle}"

        print(f"\n   📡 收集 @{handle}...")
        data = jina_read_url(url, timeout=15)

        if data and data.get('success'):
            # 解析推文内容
            content = data['content']

            # 简单解析：推文通常以换行符分隔
            lines = content.split('\n')
            first_line = lines[0] if lines else ''

            # 尝试提取推文文本（通常是第一行）
            tweet_text = first_line[:200]

            if tweet_text.startswith('@'):
                # 可能是回复，尝试第二行
                if len(lines) > 1:
                    tweet_text = lines[1][:200]

            tweet = {
                'id': f"twitter_{handle}_{hash(url)}",
                'source_type': 'official_x' if handle in ['OpenAI', 'DeepMind', 'AnthropicAI'] else 'notable_person',
                'source': f"@{handle}",
                'activity_type': 'tweet',
                'title': tweet_text,
                'description': content[:500],
                'author': handle,
                'url': url,
                'score': 0,
                'comments': 0,
                'timestamp': datetime.now().isoformat(),
                'handle': handle,
                'company': _get_twitter_company(handle),
                'priority': _get_twitter_priority(handle)
            }

            tweets.append(tweet)
            print(f"      ✅ 推文长度: {len(tweet_text)} 字符")

    print(f"\n   ✅ Twitter: {len(tweets)} 条推文")

    return tweets


def collect_blog_with_jina(blog_config: Dict, days: int = 7) -> List[Dict]:
    """
    使用 jina-cli 收集博客数据

    Args:
        blog_config: 博客配置（包含 url, company, priority）
        days: 收集最近多少天

    Returns:
        文章列表
    """
    company = blog_config['company']
    blog_url = blog_config['blog_url']
    priority = blog_config['priority']

    print(f"\n   🏢 收集 {company} 博客...")

    articles = []

    # 读取博客主页
    data = jina_read_url(blog_url, timeout=20)

    if data and data.get('success'):
        content = data['content']

        # 解析博客文章（简单版本：查找链接）
        lines = content.split('\n')

        for line in lines:
            line = line.strip()

            # 查找链接
            if line.startswith('https://') or line.startswith('http://'):
                url = line.split()[0] if ' ' in line else line

                # 只保留最近的
                published_date = _extract_date_from_url(url)
                if published_date and published_date < datetime.now() - timedelta(days=days):
                    continue

                # 尝试提取标题（通常在链接前面）
                title = line.split()[-1] if ' ' in line else url

                article = {
                    'id': f"blog_{company}_{hash(url)}",
                    'source_type': 'official_blog',
                    'source': f"{company} Blog",
                    'activity_type': 'blog_post',
                    'title': title[:100],
                    'description': '',
                    'author': company,
                    'url': url,
                    'score': 0,
                    'comments': 0,
                    'timestamp': published_date.isoformat() if published_date else datetime.now().isoformat(),
                    'company': company,
                    'priority': priority
                }

                articles.append(article)
                print(f"      ✅ 文章: {title[:50]}...")

    print(f"   ✅ {company}: {len(articles)} 篇文章")

    return articles


def _extract_date_from_url(url: str) -> datetime:
    """
    从 URL 中提取日期（简化版本）

    Args:
        url: URL

    Returns:
        日期对象
    """
    # 简化处理：假设所有内容都是最近的
    # 实际应该从 URL 中解析日期或从页面内容中提取
    return datetime.now()


def _get_twitter_company(handle: str) -> str:
    """获取 Twitter 账号对应的公司"""
    mapping = {
        'OpenAI': 'OpenAI',
        'DeepMind': 'DeepMind',
        'GoogleDeepMind': 'DeepMind',
        'AnthropicAI': 'Anthropic',
        'GoogleAI': 'Google AI',
        'MetaAI': 'Meta AI',
        'sama': 'OpenAI',
        'gdb': 'OpenAI',
        'ilyasut': 'OpenAI',
        'demishassabis': 'DeepMind',
        'shabor': 'DeepMind'
    }

    return mapping.get(handle, 'Unknown')


def _get_twitter_priority(handle: str) -> str:
    """获取 Twitter 账号的优先级"""
    p0_handles = ['OpenAI', 'DeepMind', 'AnthropicAI', 'sama', 'gdb', 'ilyasut', 'demishassabis']
    p1_handles = ['GoogleAI', 'MetaAI', 'karpathy', 'ylecun', 'jeffdean']

    if handle in p0_handles:
        return 'P0'
    elif handle in p1_handles:
        return 'P1'
    else:
        return 'P2'


def save_to_unified_db(activities: List[Dict], db_path: str = "storage/data/unified_activities.db"):
    """保存到统一数据库"""
    print(f"\n💾 保存到统一数据库...")
    print(f"   数据库: {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS activities (
            id TEXT PRIMARY KEY,
            source_type TEXT,
            source TEXT,
            activity_type TEXT,
            title TEXT,
            description TEXT,
            author TEXT,
            url TEXT,
            score INTEGER DEFAULT 0,
            comments INTEGER DEFAULT 0,
            timestamp TEXT,
            priority_score INTEGER,
            company TEXT,
            handle TEXT,
            priority TEXT,
            collected_at TEXT
        )
    ''')

    conn.commit()

    # 清空旧数据
    cursor.execute('DELETE FROM activities')
    conn.commit()

    # 插入数据
    saved_count = 0
    for activity in activities:
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO activities
                (id, source_type, source, activity_type, title, description, author, url,
                 score, comments, timestamp, priority_score, company, handle, priority, collected_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                activity.get('id', str(hash(str(activity)))),
                activity.get('source_type', 'unknown'),
                activity.get('source', 'unknown'),
                activity.get('activity_type', 'unknown'),
                activity.get('title', ''),
                activity.get('description', '')[:500],
                activity.get('author', 'unknown'),
                activity.get('url', ''),
                activity.get('score', 0),
                activity.get('comments', 0),
                activity.get('timestamp', datetime.now().isoformat()),
                activity.get('priority_score', 0),
                activity.get('company', ''),
                activity.get('handle', ''),
                activity.get('priority', 'P3'),
                datetime.now().isoformat()
            ))

            saved_count += 1
        except Exception as e:
            print(f"   ⚠️  保存活动失败: {e}")

    conn.commit()
    conn.close()

    print(f"   ✅ 已保存 {saved_count} 条活动到数据库")


def main():
    """主程序"""
    print("\n" + "=" * 80)
    print("🚀 Silicon Valley Alpha Radar - 使用 jina-cli 收集真实数据")
    print("=" * 80)

    all_activities = []

    # 1. Twitter (优先级 1)
    print("\n🟦 [优先级 1] 使用 jina-cli 收集 Twitter 数据...")
    print("   官方账号 + 关键人物")

    p0_twitter = ['OpenAI', 'sama', 'gdb', 'ilyasut', 'DeepMind', 'demishassabis', 'AnthropicAI']
    p1_twitter = ['GoogleAI', 'MetaAI', 'karpathy', 'ylecun', 'jeffdean']

    all_twitter_handles = p0_twitter + p1_twitter
    tweets = collect_twitter_with_jina(all_twitter_handles, days=7)
    all_activities.extend(tweets)

    # 2. 官方博客（优先级 2）- 只做 OpenAI（有 RSS）
    print("\n📝 [优先级 2] 使用 jina-cli 收集官方博客...")
    print("   只做 OpenAI（jina read RSS 不支持，先测试）")

    openai_config = {
        'company': 'OpenAI',
        'blog_url': 'https://openai.com/blog',
        'priority': 'P0'
    }

    # OpenAI 暂时用 RSS 而不是 jina read
    try:
        import feedparser
        rss_url = "https://openai.com/blog/rss.xml"
        feed = feedparser.parse(rss_url)

        for entry in feed.entries[:10]:  # 限制 10 篇
            article = {
                'id': f"openai_blog_{hash(entry.get('id', entry.get('link')))}",
                'source_type': 'official_blog',
                'source': "OpenAI Blog",
                'activity_type': 'blog_post',
                'title': entry.get('title', ''),
                'description': entry.get('summary', entry.get('description', ''))[:300],
                'author': entry.get('author', 'OpenAI'),
                'url': entry.get('link', 'https://openai.com/blog'),
                'score': 0,
                'comments': 0,
                'timestamp': entry.get('published_parsed', datetime.now()).isoformat(),
                'company': 'OpenAI',
                'priority': 'P0'
            }

            all_activities.append(article)

        print(f"   ✅ OpenAI RSS: {len(feed.entries[:10])} 篇")

    except Exception as e:
        print(f"   ⚠️  OpenAI RSS 收集失败: {e}")

    # 3. Hacker News (已有数据）
    print("\n🕶️ [优先级 3] 添加 Hacker News 数据...")
    try:
        hn_db = "storage/data/hacker_news.db"
        if os.path.exists(hn_db):
            conn = sqlite3.connect(hn_db)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute('SELECT * FROM hackernews ORDER BY time DESC LIMIT 50')
            hn_events = [dict(row) for row in cursor.fetchall()]

            for event in hn_events:
                unified_event = {
                    'id': f"hn_{event['id']}",
                    'source_type': 'community',
                    'source': 'Hacker News',
                    'activity_type': 'story',
                    'title': event.get('title', ''),
                    'description': event.get('text', '')[:200],
                    'author': event.get('by', 'unknown'),
                    'url': event.get('url', f"https://news.ycombinator.com/item?id={event['id']}"),
                    'score': event.get('score', 0),
                    'comments': event.get('descendants', 0),
                    'timestamp': event.get('time', datetime.now().isoformat()),
                    'company': 'Hacker News',
                    'handle': None,
                    'priority': 'P3'
                }

                all_activities.append(unified_event)

            conn.close()
            print(f"   ✅ Hacker News: {len(hn_events)} 条")
    except Exception as e:
        print(f"   ⚠️  Hacker News 加载失败: {e}")

    print(f"\n📊 总计收集: {len(all_activities)} 个活动")

    # 计算优先级
    print(f"\n📊 计算优先级...")
    for activity in all_activities:
        try:
            activity['priority_score'] = calculate_priority(activity)
        except Exception as e:
            activity['priority_score'] = 0

    # 排序
    print(f"📊 按优先级排序...")
    prioritized = sorted(all_activities, key=lambda x: x.get('priority_score', 0), reverse=True)

    # 保存到数据库
    save_to_unified_db(prioritized)

    # 显示统计
    print(f"\n📊 数据统计:")
    print(f"   总活动数: {len(prioritized)}")

    # 按类型统计
    source_types = [a['source_type'] for a in prioritized]
    type_count = Counter(source_types)

    print(f"\n📊 按来源类型:")
    for source_type, count in type_count.most_common():
        print(f"   • {source_type}: {count} 条")

    # 按优先级统计
    priorities = [a['priority_score'] for a in prioritized]
    high_priority = len([p for p in priorities if p >= 90])
    medium_priority = len([p for p in priorities if 50 <= p < 90])
    low_priority = len([p for p in priorities if p < 50])

    print(f"\n📊 按优先级:")
    print(f"   🔴 高 (>=90): {high_priority}")
    print(f"   🟠 中 (50-89): {medium_priority}")
    print(f"   🟡 低 (<50): {low_priority}")

    # 显示前 20 个
    print(f"\n🔥 高优先级活动 (Top 20):")
    for i, activity in enumerate(prioritized[:20], 1):
        score = activity.get('priority_score', 0)
        title = activity.get('title', '')[:60]
        source = activity.get('source', '')
        company = activity.get('company', '')

        print(f"\n   [{i}] 优先级: {score}")
        print(f"      📦 {source}")
        print(f"      🏢 {company}")
        print(f"      📄 {title}...")

    # 完成
    print("\n" + "=" * 80)
    print("✅ jina-cli 数据收集完成！")
    print("=" * 80)
    print(f"\n📁 数据库: storage/data/unified_activities.db")
    print(f"📊 总活动数: {len(prioritized)}")
    print(f"🔴 高优先级: {high_priority}")


if __name__ == "__main__":
    main()
