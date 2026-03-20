#!/usr/bin/env python3
"""
多数据源收集器 v2 - 优化版
改进：
1. 更准确的标题提取
2. 过滤导航/页脚链接，只保留文章链接
3. 更好的内容清洗
"""

import subprocess
import re
import sqlite3
import os
import requests
from datetime import datetime
from typing import List, Dict, Optional
from urllib.parse import urlparse

# 配置
DB_PATH = "storage/data/collected_articles.db"

# 数据源配置
DATA_SOURCES = {
    "openai_blog": {
        "name": "OpenAI Blog",
        "url": "https://openai.com/blog",
        "type": "blog",
        "priority": 100,
        # 文章 URL 模式
        "article_pattern": r'https://openai\.com/index/[a-z0-9-]+/',
        # 排除的 URL 模式
        "exclude_patterns": [
            r'/index/gpt-5-\d+/$',  # 排除旧的 GPT-5.x 链接，只保留最新
        ]
    },
    "deepmind_blog": {
        "name": "DeepMind Blog",
        "url": "https://deepmind.google/discover/",
        "type": "blog",
        "priority": 100,
        "article_pattern": r'https://deepmind\.google/[a-z0-9-]+/[a-z0-9-]+/',
        "exclude_patterns": [
            r'/models/$',  # 模型列表页
            r'/about/$',   # 关于页
            r'/careers/$', # 招聘页
            r'#',          # 锚点链接
        ]
    },
    "anthropic_blog": {
        "name": "Anthropic Blog",
        "url": "https://www.anthropic.com/research",
        "type": "blog",
        "priority": 100,
        "article_pattern": r'https://www\.anthropic\.com/(research|news)/[a-z0-9-]+',
        "exclude_patterns": [
            r'#',           # 锚点链接
            r'/research$',   # 列表页
            r'/research/$',  # 列表页
        ]
    }
}

# GitHub 组织配置
GITHUB_ORGS = [
    {"org": "openai", "name": "OpenAI", "priority": 85},
    {"org": "deepmind", "name": "DeepMind", "priority": 85},
    {"org": "anthropics", "name": "Anthropic", "priority": 85}
]


def run_jina_read(url: str) -> Optional[str]:
    """调用 jina read 命令"""
    print(f"  📖 读取: {url}")
    try:
        result = subprocess.run(
            ["jina", "read", "--url", url, "--output", "markdown"],
            capture_output=True,
            text=True,
            timeout=120
        )
        if result.returncode == 0:
            return result.stdout
        else:
            print(f"  ❌ 失败: {result.stderr[:100]}")
            return None
    except subprocess.TimeoutExpired:
        print(f"  ⏰ 超时")
        return None
    except FileNotFoundError:
        print(f"  ❌ jina 命令不存在")
        return None
    except Exception as e:
        print(f"  ❌ 错误: {e}")
        return None


def fetch_github_releases(org: str, limit: int = 5) -> List[Dict]:
    """获取 GitHub 组织的最新 releases"""
    print(f"  📦 获取 {org} releases...")
    releases = []

    try:
        url = f"https://api.github.com/orgs/{org}/repos?per_page=10&sort=updated"
        headers = {"Accept": "application/vnd.github.v3+json"}

        response = requests.get(url, headers=headers, timeout=30)

        if response.status_code != 200:
            print(f"  ❌ GitHub API 失败: {response.status_code}")
            return []

        repos = response.json()

        for repo in repos[:limit]:
            repo_name = repo.get('full_name', '')
            release_url = f"https://api.github.com/repos/{repo_name}/releases/latest"

            try:
                rel_response = requests.get(release_url, headers=headers, timeout=15)
                if rel_response.status_code == 200:
                    release = rel_response.json()
                    releases.append({
                        'title': release.get('name', '') or release.get('tag_name', 'Unknown'),
                        'url': release.get('html_url', ''),
                        'description': (release.get('body') or '')[:500],
                        'source': f'github:{org}',
                        'published_at': release.get('published_at', ''),
                        'repo': repo_name
                    })
                    print(f"     ✅ {repo_name}: {release.get('tag_name', 'N/A')}")
            except:
                continue

        return releases

    except Exception as e:
        print(f"  ❌ GitHub API 错误: {e}")
        return []


def is_valid_article_url(url: str, source_key: str) -> bool:
    """检查 URL 是否是有效的文章链接"""
    source = DATA_SOURCES.get(source_key)
    if not source:
        return False

    # 检查排除模式
    for exclude_pattern in source.get("exclude_patterns", []):
        if re.search(exclude_pattern, url):
            return False

    # 检查文章模式
    article_pattern = source.get("article_pattern")
    if article_pattern:
        return bool(re.search(article_pattern, url))

    return True


def extract_blog_links(markdown: str, source_key: str) -> List[str]:
    """从博客页面提取文章链接（优化版）"""
    if not markdown:
        return []

    source = DATA_SOURCES.get(source_key)
    if not source:
        return []

    # 提取所有 URL
    all_urls = re.findall(r'https://[^\s\)\]"\'>]+', markdown)

    # 过滤出有效文章链接
    valid_links = []
    seen = set()

    for url in all_urls:
        url = url.rstrip('.,;:')  # 清理末尾标点

        # 去重
        if url in seen:
            continue
        seen.add(url)

        # 检查是否是有效文章
        if is_valid_article_url(url, source_key):
            valid_links.append(url)

    print(f"  📋 找到 {len(valid_links)} 个有效文章链接")
    return valid_links[:5]


def extract_title(markdown: str, url: str) -> str:
    """智能提取标题（优化版）"""
    if not markdown:
        # 从 URL 提取
        slug = url.rstrip('/').split('/')[-1]
        return slug.replace('-', ' ').title()

    lines = markdown.split('\n')

    # 策略1: 查找第一个 # 标题
    for line in lines[:20]:
        line = line.strip()
        if line.startswith('# '):
            title = line[2:].strip()
            # 清理常见前缀
            title = re.sub(r'^(OpenAI|DeepMind|Anthropic)\s*[-:|]\s*', '', title)
            if len(title) > 5 and len(title) < 100:
                return title

    # 策略2: 查找包含常见模式的标题行
    title_patterns = [
        r'\*\*(.+?)\*\*',  # **Title**
        r'^[A-Z][^.!?]{10,80}$',  # 首字母大写的句子
    ]

    for line in lines[:30]:
        line = line.strip()
        if not line or line.startswith('![') or line.startswith('[') or line.startswith('|'):
            continue

        for pattern in title_patterns:
            match = re.search(pattern, line)
            if match:
                title = match.group(1) if match.lastindex else match.group(0)
                title = title.strip()
                # 过滤掉导航文字
                nav_words = ['Skip to', 'Log in', 'Menu', 'Search', 'Subscribe', 'Follow']
                if not any(nw in title for nw in nav_words):
                    if 10 < len(title) < 100:
                        return title

    # 策略3: 从 URL 提取
    slug = url.rstrip('/').split('/')[-1]
    return slug.replace('-', ' ').title()


def extract_description(markdown: str) -> str:
    """提取文章描述（优化版）"""
    if not markdown:
        return ""

    # 移除图片
    content = re.sub(r'!\[.*?\]\(.*?\)', '', markdown)
    # 移除链接但保留文字
    content = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', content)
    # 移除标题标记
    content = re.sub(r'^#{1,6}\s*', '', content, flags=re.MULTILINE)
    # 移除粗体/斜体
    content = re.sub(r'\*\*?([^\*]+)\*\*?', r'\1', content)
    # 移除多余空行
    content = re.sub(r'\n{2,}', '\n', content)

    # 获取前300字符
    lines = [l.strip() for l in content.split('\n') if l.strip()]
    desc = ' '.join(lines[:5])

    return desc[:300]


def extract_article_info(markdown: str, url: str) -> Dict:
    """从文章页面提取信息（优化版）"""
    title = extract_title(markdown, url)
    description = extract_description(markdown)
    slug = url.rstrip('/').split('/')[-1]

    print(f"  📝 提取标题: {title[:50]}...")

    return {
        'title': title,
        'url': url,
        'slug': slug,
        'description': description,
        'collected_at': datetime.now().isoformat()
    }


def init_database():
    """初始化数据库"""
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
    print(f"✅ 数据库初始化: {DB_PATH}")


def save_article(article: Dict, source: str, priority: int = 50) -> bool:
    """保存文章到数据库"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute('''
            INSERT OR REPLACE INTO articles
            (title, url, slug, description, source, priority, collected_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            article['title'],
            article['url'],
            article['slug'],
            article['description'],
            source,
            priority,
            article['collected_at']
        ))
        conn.commit()
        print(f"  ✅ 已保存: {article['title'][:40]}...")
        return True
    except Exception as e:
        print(f"  ❌ 保存失败: {e}")
        return False
    finally:
        conn.close()


def collect_blog(source_key: str):
    """收集博客数据"""
    source = DATA_SOURCES.get(source_key)
    if not source:
        return 0

    print(f"\n📰 收集 {source['name']}...")

    homepage = run_jina_read(source['url'])
    if not homepage:
        return 0

    links = extract_blog_links(homepage, source_key)

    if not links:
        print(f"  ⚠️ 没有找到有效文章链接")
        return 0

    success = 0
    for url in links[:3]:
        content = run_jina_read(url)
        if content:
            article = extract_article_info(content, url)
            if article and save_article(article, source_key, source['priority']):
                success += 1

    return success


def collect_github():
    """收集 GitHub releases"""
    total = 0

    for org_config in GITHUB_ORGS:
        print(f"\n📦 收集 {org_config['name']} GitHub releases...")
        releases = fetch_github_releases(org_config['org'], limit=3)

        for release in releases:
            article = {
                'title': f"[{release['repo']}] {release['title']}",
                'url': release['url'],
                'slug': release['repo'].replace('/', '-'),
                'description': release['description'],
                'collected_at': datetime.now().isoformat()
            }
            if save_article(article, f"github:{org_config['org']}", org_config['priority']):
                total += 1

    return total


def main():
    """主函数"""
    print("=" * 60)
    print("🚀 多数据源收集器 v2 (优化版)")
    print("=" * 60)

    print("\n[1/3] 初始化数据库...")
    init_database()

    print("\n[2/3] 收集博客数据...")
    blog_count = 0
    for source_key in DATA_SOURCES.keys():
        try:
            blog_count += collect_blog(source_key)
        except Exception as e:
            print(f"  ❌ {source_key} 收集失败: {e}")

    print("\n[3/3] 收集 GitHub releases...")
    try:
        github_count = collect_github()
    except Exception as e:
        print(f"  ❌ GitHub 收集失败: {e}")
        github_count = 0

    print("\n" + "=" * 60)
    print("📊 收集完成")
    print(f"   博客文章: {blog_count}")
    print(f"   GitHub Releases: {github_count}")
    print(f"   总计: {blog_count + github_count}")
    print(f"   数据库: {DB_PATH}")
    print("=" * 60)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT source, COUNT(*) FROM articles GROUP BY source")
    rows = cursor.fetchall()
    conn.close()

    if rows:
        print("\n📈 数据分布:")
        for source, count in rows:
            print(f"   • {source}: {count} 条")


if __name__ == "__main__":
    main()
