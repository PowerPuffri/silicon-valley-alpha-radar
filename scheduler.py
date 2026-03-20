#!/usr/bin/env python3
"""
自动化调度器 - 定时收集 + 推送
使用方法：
  python scheduler.py          # 单次运行
  python scheduler.py --daemon  # 后台持续运行
"""

import argparse
import time
import schedule
import threading
from datetime import datetime
from collect_all_sources import (
    init_database,
    collect_blog,
    collect_github,
    DATA_SOURCES,
    GITHUB_ORGS
)

DB_PATH = "storage/data/collected_articles.db"
import sqlite3
import requests
import json
import os

# Telegram 配置
CONFIG_PATH = "config/config.json"


def load_config():
    """加载配置"""
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}


def deduplicate_articles():
    """去重 - 删除重复文章"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 按标题去重，保留最新的
    cursor.execute('''
        DELETE FROM articles
        WHERE id NOT IN (
            SELECT MAX(id) FROM articles GROUP BY url
        )
    ''')

    deleted = cursor.rowcount
    conn.commit()
    conn.close()

    if deleted > 0:
        print(f"  🧹 去重: 删除 {deleted} 条重复数据")


def clean_old_articles(days: int = 30):
    """清理旧文章"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        DELETE FROM articles
        WHERE datetime(collected_at) < datetime('now', ?)
    ''', (f'-{days} days',))

    deleted = cursor.rowcount
    conn.commit()
    conn.close()

    if deleted > 0:
        print(f"  🗑️ 清理: 删除 {deleted} 条超过 {days} 天的数据")


def get_new_articles(since_hours: int = 24) -> list:
    """获取新文章（指定时间内）"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT title, url, source, priority
        FROM articles
        WHERE datetime(collected_at) > datetime('now', ?)
        ORDER BY priority DESC, collected_at DESC
    ''', (f'-{since_hours} hours',))

    articles = cursor.fetchall()
    conn.close()

    return articles


def send_telegram_report(articles: list) -> bool:
    """发送 Telegram 报告"""
    if not articles:
        print("  ⚠️ 没有新文章，跳过推送")
        return False

    config = load_config()
    bot_token = config.get('telegram', {}).get('botToken', '')
    chat_id = config.get('telegram', {}).get('chatId', '')

    if not bot_token or not chat_id:
        print("  ❌ Telegram 配置缺失")
        return False

    # 构建消息
    lines = [f'🚨 <b>SV Alpha Radar</b> | {datetime.now().strftime("%Y-%m-%d %H:%M")}']
    lines.append('')
    lines.append('━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
    lines.append('⚡ <b>NEW UPDATES</b>')
    lines.append('━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
    lines.append('')

    source_icons = {
        'openai_blog': '🟢',
        'anthropic_blog': '🟣',
        'deepmind_blog': '🔵',
        'github:openai': '📦',
        'github:deepmind': '📦',
        'github:anthropics': '📦'
    }

    for title, url, source, _ in articles[:10]:
        icon = source_icons.get(source, '📄')
        title_clean = title.split('|')[0].strip()[:50]
        lines.append(f'{icon} <a href="{url}">{title_clean}</a>')

    lines.append('')
    lines.append('━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
    lines.append(f'<i>🕐 {datetime.now().strftime("%H:%M")} | OpenAI + Anthropic + DeepMind</i>')

    message = '\n'.join(lines)

    # 发送
    url_api = f'https://api.telegram.org/bot{bot_token}/sendMessage'
    payload = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'HTML',
        'disable_web_page_preview': True
    }

    try:
        response = requests.post(url_api, json=payload, timeout=30)
        if response.status_code == 200:
            print(f"  ✅ 推送成功: {len(articles)} 条文章")
            return True
        else:
            print(f"  ❌ 推送失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"  ❌ 推送错误: {e}")
        return False


def run_collection_job():
    """执行收集任务"""
    print("\n" + "=" * 60)
    print(f"🔄 [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 开始收集...")
    print("=" * 60)

    # 初始化
    init_database()

    # 1. 收集博客
    blog_count = 0
    for source_key in DATA_SOURCES.keys():
        try:
            blog_count += collect_blog(source_key)
        except Exception as e:
            print(f"  ❌ {source_key} 失败: {e}")

    # 2. 收集 Twitter
    twitter_count = 0
    try:
        from collect_twitter import collect_twitter
        twitter_count = collect_twitter()
    except Exception as e:
        print(f"  ❌ Twitter 失败: {e}")

    # 3. 收集 GitHub
    github_count = 0
    try:
        for org_config in GITHUB_ORGS:
            from collect_all_sources import fetch_github_releases, save_article
            releases = fetch_github_releases(org_config['org'], limit=2)
            for release in releases:
                article = {
                    'title': f"[{release['repo']}] {release['title']}",
                    'url': release['url'],
                    'slug': release['repo'].replace('/', '-'),
                    'description': release['description'],
                    'collected_at': datetime.now().isoformat()
                }
                if save_article(article, f"github:{org_config['org']}", org_config['priority']):
                    github_count += 1
    except Exception as e:
        print(f"  ❌ GitHub 失败: {e}")

    # 去重和清理
    deduplicate_articles()

    # 获取新文章并推送
    new_articles = get_new_articles(since_hours=24)
    send_telegram_report(new_articles)

    print(f"\n📊 本次收集: 博客 {blog_count}, Twitter {twitter_count}, GitHub {github_count}")

    return blog_count + twitter_count + github_count


def run_daemon():
    """后台持续运行"""
    print("=" * 60)
    print("🤖 SV Alpha Radar 调度器启动")
    print("=" * 60)
    print(f"📅 调度计划:")
    print(f"   • 每天 00:00, 06:00, 12:00, 18:00 收集一次")
    print(f"   • 每天 09:00 推送日报")
    print("=" * 60)

    # 定时任务
    schedule.every().day.at("00:00").do(run_collection_job)
    schedule.every().day.at("06:00").do(run_collection_job)
    schedule.every().day.at("12:00").do(run_collection_job)
    schedule.every().day.at("18:00").do(run_collection_job)
    schedule.every().day.at("09:00").do(run_collection_job)

    print("\n📋 当前任务队列及下次执行时间:")
    for job in schedule.get_jobs():
        print(f"   • 任务: {job} | 下次执行: {job.next_run}")

    # 首次运行
    run_collection_job()

    print("\n🔄 调度器运行中... (Ctrl+C 停止)")

    while True:
        schedule.run_pending()
        time.sleep(60)


def main():
    parser = argparse.ArgumentParser(description='SV Alpha Radar 调度器')
    parser.add_argument('--daemon', '-d', action='store_true', help='后台持续运行')
    parser.add_argument('--collect', '-c', action='store_true', help='仅收集，不推送')
    args = parser.parse_args()

    if args.daemon:
        run_daemon()
    elif args.collect:
        init_database()
        for source_key in DATA_SOURCES.keys():
            collect_blog(source_key)
        deduplicate_articles()
    else:
        run_collection_job()


if __name__ == "__main__":
    main()
