#!/usr/bin/env python3
"""
Twitter 收集器 v2 - 收集官方账号和关键人物推文
运行: python collect_twitter.py
"""

import subprocess
import re
import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional

DB_PATH = "/Users/zhipu_glm/.openclaw/workspace/silicon-valley-alpha-radar/storage/data/collected_articles.db"

# Twitter 账号配置
TWITTER_ACCOUNTS = {
    "official": {
        "priority": 90,
        "accounts": [
            {"handle": "OpenAI", "name": "OpenAI"},
            {"handle": "AnthropicAI", "name": "Anthropic"},
            {"handle": "DeepMindAI", "name": "DeepMind"},
        ]
    },
    "key_people": {
        "priority": 80,
        "accounts": [
            {"handle": "sama", "name": "Sam Altman"},
            {"handle": "gdb", "name": "Greg Brockman"},
            {"handle": "demishassabis", "name": "Demis Hassabis"},
            {"handle": "karpathy", "name": "Andrej Karpathy"},
        ]
    }
}


def run_jina_read(url: str) -> Optional[str]:
    """调用 jina read"""
    try:
        result = subprocess.run(
            ["jina", "read", "--url", url, "--output", "markdown"],
            capture_output=True,
            text=True,
            timeout=120
        )
        if result.returncode == 0:
            return result.stdout
        return None
    except:
        return None


def extract_tweets(markdown: str, handle: str) -> List[Dict]:
    """
    从 Twitter 页面提取推文

    格式分析：
    [Mar 5](https://x.com/OpenAI/status/2029620619743219811)
    GPT-5.4 Thinking and GPT-5.4 Pro are rolling out...
    """
    if not markdown:
        return []

    tweets = []
    lines = markdown.split('\n')

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # 匹配日期链接: [Mar 5](https://x.com/.../status/xxx)
        date_match = re.search(r'\[([A-Z][a-z]{2}\s+\d+)\]\(https://x\.com/[^/]+/status/(\d+)\)', line)

        if date_match:
            date_str = date_match.group(1)
            status_id = date_match.group(2)
            tweet_url = f"https://x.com/{handle}/status/{status_id}"

            # 收集后续行的文本
            tweet_text = ""
            j = i + 1
            while j < len(lines) and j < i + 10:
                next_line = lines[j].strip()

                # 跳过空行
                if not next_line:
                    j += 1
                    continue

                # 跳过图片
                if next_line.startswith('![') or 'profile_images' in next_line or 'twimg' in next_line:
                    j += 1
                    continue

                # 跳过数字（点赞数等）
                if re.match(r'^\d+\.?\d*[KM]?$', next_line):
                    j += 1
                    continue

                # 跳过链接
                if next_line.startswith('[') and '](' in next_line:
                    # 检查是否是另一个日期链接（新推文开始）
                    new_date = re.search(r'\[([A-Z][a-z]{2}\s+\d+)\]\(https://x\.com/[^/]+/status/\d+\)', next_line)
                    if new_date:
                        break
                    j += 1
                    continue

                # 跳过"Show more"
                if 'Show more' in next_line:
                    j += 1
                    continue

                # 跳过@mentions
                if next_line.startswith('@') and len(next_line.split()) <= 2:
                    j += 1
                    continue

                # 跳过"From xxx"
                if next_line.startswith('From ') or next_line.startswith('Pinned'):
                    j += 1
                    continue

                # 收集文本
                if len(next_line) > 10:
                    tweet_text += next_line + " "

                j += 1

            # 清理文本
            tweet_text = tweet_text.strip()

            # 过滤太短的推文
            if len(tweet_text) > 15:
                tweets.append({
                    'text': tweet_text[:400],
                    'date': date_str,
                    'url': tweet_url,
                    'handle': handle
                })

        i += 1

    return tweets


def save_tweet(tweet: Dict, account: Dict, priority: int) -> bool:
    """保存推文到数据库"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # 用 URL 的一部分作为 slug
        slug = tweet['url'].split('/')[-1][:20]

        cursor.execute('''
            INSERT OR REPLACE INTO articles
            (title, url, slug, description, source, priority, collected_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            tweet['text'][:80],  # title
            tweet['url'],
            slug,
            tweet['text'],
            f"twitter:{tweet['handle']}",
            priority,
            datetime.now().isoformat()
        ))
        conn.commit()
        return True
    except Exception as e:
        print(f"     ❌ 保存失败: {e}")
        return False
    finally:
        conn.close()


def collect_twitter():
    """收集 Twitter 数据"""
    print("\n" + "=" * 60)
    print("🐦 Twitter 数据收集")
    print("=" * 60)

    total = 0

    for category, config in TWITTER_ACCOUNTS.items():
        print(f"\n📂 {category.upper()} (优先级: {config['priority']})")

        for account in config['accounts']:
            handle = account['handle']
            name = account['name']
            url = f"https://x.com/{handle}"

            print(f"  📖 @{handle} ({name})...", end='')

            markdown = run_jina_read(url)

            if markdown:
                tweets = extract_tweets(markdown, handle)

                if tweets:
                    print(f" 找到 {len(tweets)} 条推文")
                    for tweet in tweets[:3]:  # 每个账号最多3条
                        if save_tweet(tweet, account, config['priority']):
                            print(f"     ✅ {tweet['text'][:50]}...")
                            total += 1
                else:
                    print(" ⚠️ 没有提取到推文")
            else:
                print(" ❌ 读取失败")

    print(f"\n📊 Twitter 收集完成: {total} 条")
    return total


def main():
    """主函数"""
    # 初始化数据库
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            url TEXT UNIQUE,
            slug TEXT,
            description TEXT,
            source TEXT,
            priority INTEGER DEFAULT 50,
            published_at TEXT,
            collected_at DATETIME
        )
    ''')
    conn.commit()
    conn.close()

    collect_twitter()

    # 显示统计
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT source, COUNT(*) FROM articles WHERE source LIKE 'twitter:%' GROUP BY source")
    rows = cursor.fetchall()
    conn.close()

    if rows:
        print("\n📈 Twitter 数据分布:")
        for source, count in rows:
            print(f"   • {source}: {count} 条")


if __name__ == "__main__":
    main()
