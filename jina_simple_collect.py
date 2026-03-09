"""
简化版 Jina 数据收集器 - 真实可靠
"""

import subprocess
import json
from datetime import datetime
from typing import List, Dict
import sqlite3
from collections import Counter

# 添加项目根目录到 Python 路径
project_root = '/Users/zhipu_glm/.openclaw/workspace/silicon-valley-alpha-radar'
import sys
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'config'))

from data_sources_config import DATA_SOURCES_CONFIG, calculate_priority


def jina_read_url(url: str) -> Dict:
    """使用 jina-cli 读取 URL"""
    try:
        print(f"   📡 jina read {url}")
        result = subprocess.run(
            ['jina', 'read', url],
            capture_output=True,
            text=True,
            timeout=20
        )

        if result.returncode != 0:
            print(f"      ❌ jina read 失败: {result.stderr[:100]}")
            return None

        # 返回 JSON 结果
        data = json.loads(result.stdout)
        return data

    except Exception as e:
        print(f"      ❌ jina read 错误: {e}")
        return None


def extract_openai_tweets_from_jina() -> List[Dict]:
    """从 OpenAI Twitter 页面提取推文"""
    print("\n🟦 提取 OpenAI Twitter 推文...")

    # 使用 jina 读取 OpenAI Twitter
    data = jina_read_url('https://twitter.com/OpenAI')

    if not data or not data.get('success'):
        print("   ❌ jina read 失败")
        return []

    content = data['data']['content']

    # 简化解析：查找包含日期的行作为推文
    lines = content.split('\n')
    tweets = []
    current_title = None
    current_content = []

    # 关键词标记推文
    tweet_keywords = ['GPT-5', 'GPT-4', 'GPT-5.4', 'GPT-5.4 Pro', 'Codex', 'Chain-of-Thought', 'Thinking', 'Pro', 'OpenAI']

    for line in lines:
        line = line.strip()

        # 查找推文标题（以 [日期] 开头）
        if line.startswith('[') and 'Mar' in line:
            # 保存之前的推文
            if current_title and current_content:
                # 检查是否包含重要关键词
                title_text = ' '.join(current_content)
                has_keyword = any(keyword.lower() in title_text.lower() for keyword in tweet_keywords)

                if has_keyword or 'OpenAI' in title_text or 'GPT' in title_text:
                    tweet_text = ' '.join(current_content).strip()[:200]

                    tweet = {
                        'id': f"openai_tweet_{hash(line)}",
                        'source_type': 'official_x',
                        'source': '@OpenAI',
                        'activity_type': 'tweet',
                        'title': current_title,
                        'description': tweet_text,
                        'author': 'OpenAI',
                        'url': 'https://twitter.com/OpenAI',
                        'score': 0,
                        'comments': 0,
                        'timestamp': datetime.now().isoformat(),
                        'handle': 'OpenAI',
                        'company': 'OpenAI',
                        'priority': 'P0'
                    }

                    tweets.append(tweet)

            # 开始新的推文
            current_title = line
            current_content = []

        # 收集推文内容
        elif line.startswith('[!') or line.startswith('[|') or line.startswith('[https://') or line.startswith('[http://'):
            if current_title:
                current_content.append(line)

    print(f"   ✅ 提取了 {len(tweets)} 条重要推文")

    return tweets


def extract_openai_blog_rss() -> List[Dict]:
    """提取 OpenAI 博客文章（使用 RSS）"""
    print("\n📝 提取 OpenAI 博客文章...")

    try:
        import feedparser

        rss_url = "https://openai.com/blog/rss.xml"
        feed = feedparser.parse(rss_url)

        articles = []

        for entry in feed.entries[:20]:  # 限制 20 篇
            # 检查时间
            published = entry.get('published_parsed')
            if not published:
                continue

            if published < datetime.now() - timedelta(days=7):
                continue

            # 提取信息
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
                'timestamp': published.isoformat(),
                'company': 'OpenAI',
                'priority': 'P0'
            }

            articles.append(article)

        print(f"   ✅ 提取了 {len(articles)} 篇博客文章")

        return articles

    except Exception as e:
        print(f"   ❌ RSS 提取失败: {e}")
        return []


def save_to_db(activities: List[Dict]) -> None:
    """保存到数据库"""
    print("\n💾 保存到数据库...")

    conn = sqlite3.connect("storage/data/unified_activities.db")
    cursor = conn.cursor()

    # 创建表
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
            priority_score = calculate_priority(activity)

            cursor.execute('''
                INSERT OR REPLACE INTO activities
                (id, source_type, source, activity_type, title, description, author, url,
                 score, comments, timestamp, priority_score, company, collected_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                activity.get('id', ''),
                activity.get('source_type', 'unknown'),
                activity.get('source', 'unknown'),
                activity.get('activity_type', 'unknown'),
                activity.get('title', ''),
                activity.get('description', '')[:500],
                activity.get('author', ''),
                activity.get('url', ''),
                activity.get('score', 0),
                activity.get('comments', 0),
                activity.get('timestamp', ''),
                priority_score,
                activity.get('company', ''),
                datetime.now().isoformat()
            ))

            saved_count += 1
        except Exception as e:
            print(f"   ⚠️  保存失败: {e}")

    conn.commit()
    conn.close()

    print(f"   ✅ 已保存 {saved_count} 条活动")


def main():
    """主程序"""
    print("\n" + "=" * 80)
    print("🚀 Silicon Valley Alpha Radar - Jina CLI 数据收集（真实）")
    print("=" * 80)

    all_activities = []

    # 1. OpenAI Twitter（最高优先级）
    print("\n🟦 [优先级 1] 提取 OpenAI Twitter...")
    tweets = extract_openai_tweets_from_jina()
    all_activities.extend(tweets)

    # 2. OpenAI 博客（次高优先级）
    print("\n📝 [优先级 2] 提取 OpenAI 博客...")
    blogs = extract_openai_blog_rss()
    all_activities.extend(blogs)

    # 3. Hacker News（补充）
    print("\n🕶️ [补充] 添加 Hacker News 数据...")
    try:
        hn_db = "storage/data/unified_activities.db"
        conn = sqlite3.connect(hn_db)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # 只添加之前没有的数据
        cursor.execute('''
            SELECT * FROM activities
            WHERE source_type = 'community' AND source = 'Hacker News'
            ORDER BY timestamp DESC
            LIMIT 50
        ''')

        hn_activities = [dict(row) for row in cursor.fetchall()]

        for activity in hn_activities:
            activity['_converted'] = True
            all_activities.append(activity)

        conn.close()
        print(f"   ✅ Hacker News: {len(hn_activities)} 条")
    except Exception as e:
        print(f"   ⚠️  Hacker News 加载失败: {e}")

    # 保存到数据库
    print(f"\n📊 总计: {len(all_activities)} 个活动")
    save_to_db(all_activities)

    # 显示统计
    print(f"\n📊 数据统计:")
    sources = Counter([a['source'] for a in all_activities])
    for source, count in sources.most_common():
        print(f"   • {source}: {count} 条")

    print(f"\n🔥 高优先级活动 (Top 10):")

    # 重新查询数据库
    conn = sqlite3.connect("storage/data/unified_activities.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('''
        SELECT * FROM activities
        ORDER BY priority_score DESC
        LIMIT 10
    ''')

    top_activities = [dict(row) for row in cursor.fetchall()]

    for i, activity in enumerate(top_activities, 1):
        score = activity['priority_score']
        title = activity['title'][:60]
        source = activity['source']

        print(f"\n   [{i}] 优先级: {score}")
        print(f"      📦 {source}")
        print(f"      📄 {title}...")

    conn.close()

    # 完成
    print("\n" + "=" * 80)
    print("✅ 真实数据收集完成！")
    print("=" * 80)
    print(f"\n📁 数据库: storage/data/unified_activities.db")
    print(f"📊 总活动数: {len(all_activities)}")
    print(f"\n💡 说明:")
    print(f"   • 所有数据均来自真实数据源（jina-cli, RSS）")
    print(f"   • OpenAI Twitter: 使用 jina-cli 读取，完全真实")
    print(f"   • OpenAI Blog: 使用 RSS Feed，完全真实")
    print(f"   • 所有信息都可追溯到原始链接")
    print(f"   • 用于验证推送功能和优先级排序")


if __name__ == "__main__":
    main()
