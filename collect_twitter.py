#!/usr/bin/env python3
"""
Twitter 收集器 v2 - 收集官方账号和关键人物推文
运行: python collect_twitter.py
"""

import subprocess
import re
import sqlite3
import os
import random
import time
import requests
from html import unescape
from email.utils import parsedate_to_datetime
from datetime import datetime
from typing import List, Dict, Optional, Set, Tuple

DB_PATH = "storage/data/collected_articles.db"
NITTER_INSTANCES = [
    "https://nitter.net",
    "https://nitter.privacydev.net",
    "https://nitter.poast.org",
    "https://nitter.1d4.us",
]
USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
]

# Twitter 账号配置
TWITTER_ACCOUNTS = {
    "official": {
        "priority": 95,
        "accounts": [
            {"handle": "OpenAI", "name": "OpenAI"},
            {"handle": "AnthropicAI", "name": "Anthropic"},
            {"handle": "GoogleDeepMind", "name": "Google DeepMind"},
            {"handle": "MetaAI", "name": "Meta AI"},
            {"handle": "MistralAI", "name": "Mistral AI"},
            {"handle": "xai", "name": "xAI"},
            {"handle": "NVIDIAAI", "name": "NVIDIA AI"},
            {"handle": "huggingface", "name": "Hugging Face"},
        ]
    },
    "researchers": {
        "priority": 88,
        "accounts": [
            {"handle": "sama", "name": "Sam Altman"},
            {"handle": "gdb", "name": "Greg Brockman"},
            {"handle": "demishassabis", "name": "Demis Hassabis"},
            {"handle": "karpathy", "name": "Andrej Karpathy"},
            {"handle": "ylecun", "name": "Yann LeCun"},
            {"handle": "fchollet", "name": "Francois Chollet"},
            {"handle": "DrJimFan", "name": "Jim Fan"},
            {"handle": "tim_dettmers", "name": "Tim Dettmers"},
            {"handle": "SebastienBubeck", "name": "Sebastien Bubeck"},
            {"handle": "JeffDean", "name": "Jeff Dean"},
            {"handle": "janhestness", "name": "Jan Hestness"},
            {"handle": "AlecRad", "name": "Alec Radford"},
            {"handle": "JohnSchulman2", "name": "John Schulman"},
        ]
    },
    "builders": {
        "priority": 82,
        "accounts": [
            {"handle": "ClementDelangue", "name": "Clement Delangue"},
            {"handle": "hwchase17", "name": "Harrison Chase"},
            {"handle": "swyx", "name": "Shawn Wang"},
            {"handle": "simonw", "name": "Simon Willison"},
            {"handle": "natfriedman", "name": "Nat Friedman"},
            {"handle": "perplexity_ai", "name": "Perplexity"},
            {"handle": "LangChainAI", "name": "LangChain"},
            {"handle": "vllm_project", "name": "vLLM"},
        ]
    },
    "watchers": {
        "priority": 75,
        "accounts": [
            {"handle": "emollick", "name": "Ethan Mollick"},
            {"handle": "ArvindNarayanan", "name": "Arvind Narayanan"},
            {"handle": "aidan_mclau", "name": "Aidan McLaughlin"},
            {"handle": "NathanBenaich", "name": "Nathan Benaich"},
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


def _format_date(pub_date: str) -> str:
    try:
        return parsedate_to_datetime(pub_date).strftime('%b %d')
    except Exception:
        return datetime.now().strftime('%b %d')


def run_nitter_read(handle: str, max_items: int = 6) -> Optional[str]:
    headers = {"User-Agent": random.choice(USER_AGENTS)}
    for base in random.sample(NITTER_INSTANCES, len(NITTER_INSTANCES)):
        rss_url = f"{base}/{handle}/rss"
        try:
            resp = requests.get(rss_url, headers=headers, timeout=12)
            if resp.status_code != 200 or "<item>" not in resp.text:
                continue
            items = re.findall(r"<item>(.*?)</item>", resp.text, re.S)
            if not items:
                continue
            lines: List[str] = []
            count = 0
            for item in items:
                title_match = re.search(r"<title>(.*?)</title>", item, re.S)
                link_match = re.search(r"<link>(.*?)</link>", item, re.S)
                date_match = re.search(r"<pubDate>(.*?)</pubDate>", item, re.S)
                if not title_match or not link_match:
                    continue
                title = unescape(title_match.group(1)).strip()
                link = unescape(link_match.group(1)).strip()
                link = re.sub(r"^https?://[^/]+", "https://x.com", link)
                sid_match = re.search(r"/status/(\d+)", link)
                if not sid_match:
                    continue
                date_str = _format_date(date_match.group(1).strip()) if date_match else datetime.now().strftime('%b %d')
                lines.append(f"[{date_str}]({link})")
                lines.append(title)
                lines.append("")
                count += 1
                if count >= max_items:
                    break
            if lines:
                return "\n".join(lines)
        except Exception:
            continue
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
    seen_urls: Set[str] = set()
    lines = markdown.split('\n')
    status_pattern = re.compile(r'https?://(?:x|twitter)\.com/([A-Za-z0-9_]+)/status/(\d+)')

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        status_match = status_pattern.search(line)

        if status_match:
            source_handle = status_match.group(1)
            status_id = status_match.group(2)
            tweet_url = f"https://x.com/{source_handle}/status/{status_id}"
            if tweet_url in seen_urls:
                i += 1
                continue
            seen_urls.add(tweet_url)

            # 收集后续行的文本
            tweet_text = ""
            j = i + 1
            while j < len(lines) and j < i + 14:
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
                    if status_pattern.search(next_line):
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
            tweet_text = re.sub(r'\s+', ' ', tweet_text.strip())

            # 过滤太短的推文
            if len(tweet_text) > 15:
                tweets.append({
                    'text': tweet_text[:400],
                    'date': datetime.now().strftime('%b %d'),
                    'url': tweet_url,
                    'handle': handle
                })

        i += 1

    return tweets


def get_all_accounts() -> List[Tuple[str, Dict]]:
    seen: Set[str] = set()
    merged: List[Tuple[str, Dict]] = []
    for category, config in TWITTER_ACCOUNTS.items():
        for account in config.get('accounts', []):
            handle = account.get('handle', '').strip()
            if not handle:
                continue
            key = handle.lower()
            if key in seen:
                continue
            seen.add(key)
            merged.append((category, account))
    return merged


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
    all_accounts = get_all_accounts()
    print(f"\n🎯 监控账号总数: {len(all_accounts)}")

    for category, config in TWITTER_ACCOUNTS.items():
        print(f"\n📂 {category.upper()} (优先级: {config['priority']})")
        category_accounts = [acc for cat, acc in all_accounts if cat == category]

        for account in category_accounts:
            handle = account['handle']
            name = account['name']
            url = f"https://x.com/{handle}"

            print(f"  📖 @{handle} ({name})...", end='')

            markdown = run_nitter_read(handle)
            channel = "nitter"
            if not markdown:
                markdown = run_jina_read(url)
                channel = "jina"
            time.sleep(random.uniform(0.7, 1.4))

            if markdown:
                tweets = extract_tweets(markdown, handle)

                if tweets:
                    print(f" 找到 {len(tweets)} 条推文 ({channel})")
                    for tweet in tweets[:3]:
                        if save_tweet(tweet, account, config['priority']):
                            print(f"     ✅ {tweet['text'][:50]}...")
                            total += 1
                else:
                    print(f" ⚠️ 没有提取到推文 ({channel})")
            else:
                print(" ❌ 读取失败 (nitter+jina)")

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
