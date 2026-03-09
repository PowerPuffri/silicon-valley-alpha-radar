#!/usr/bin/env python3
"""
OpenAI 博客收集器
直接运行：python collect_openai_blog.py
"""

import subprocess
import re
import sqlite3
import os
from datetime import datetime

# 配置
DB_PATH = "storage/data/collected_articles.db"
BLOG_URL = "https://openai.com/blog"


def run_jina_read(url):
    """
    调用 jina read 命令读取网页
    返回 markdown 内容
    """
    print(f"  📖 读取: {url}")

    try:
        result = subprocess.run(
            ["jina", "read", "--url", url, "--output", "markdown"],
            capture_output=True,
            text=True,
            timeout=120  # 2分钟超时
        )

        if result.returncode == 0:
            return result.stdout
        else:
            print(f"  ❌ 失败: {result.stderr}")
            return None

    except subprocess.TimeoutExpired:
        print(f"  ⏰ 超时")
        return None
    except FileNotFoundError:
        print(f"  ❌ jina 命令不存在，请先安装:")
        print(f"     curl -fsSL https://raw.githubusercontent.com/geekjourneyx/jina-cli/main/scripts/install.sh | bash")
        return None
    except Exception as e:
        print(f"  ❌ 错误: {e}")
        return None


def extract_article_links(markdown_content):
    """
    从 OpenAI 博客首页提取文章链接
    """
    if not markdown_content:
        return []

    # 匹配 https://openai.com/index/xxx/ 格式的链接
    pattern = r'https://openai\.com/index/([a-z0-9-]+)/?'
    matches = re.findall(pattern, markdown_content)

    # 去重
    unique_slugs = list(dict.fromkeys(matches))

    # 构建完整 URL
    links = [f"https://openai.com/index/{slug}/" for slug in unique_slugs]

    print(f"  📋 找到 {len(links)} 篇文章")
    return links


def extract_article_info(markdown_content, url):
    """
    从文章页面提取信息
    """
    if not markdown_content:
        return None

    # 提取标题（通常在第一行或第一个 # 标题）
    title = "未知标题"
    lines = markdown_content.split('\n')
    for line in lines[:10]:  # 只看前10行
        line = line.strip()
        if line.startswith('# '):
            title = line[2:].strip()
            break
        elif line and not line.startswith('[') and len(line) > 5:
            title = line[:100]  # 取第一个有效行作为标题
            break

    # 提取描述（取前500字符作为摘要）
    content_clean = re.sub(r'!\[.*?\]\(.*?\)', '', markdown_content)  # 去图片
    content_clean = re.sub(r'\[.*?\]\(.*?\)', '', content_clean)  # 去链接
    content_clean = re.sub(r'#+ ', '', content_clean)  # 去标题标记
    description = content_clean.strip()[:500]

    # 从 URL 提取 slug
    slug = url.rstrip('/').split('/')[-1]

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
            source TEXT DEFAULT 'openai_blog',
            collected_at DATETIME
        )
    ''')

    conn.commit()
    conn.close()
    print(f"✅ 数据库初始化: {DB_PATH}")


def save_article(article):
    """保存文章到数据库"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute('''
            INSERT OR REPLACE INTO articles (title, url, slug, description, collected_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            article['title'],
            article['url'],
            article['slug'],
            article['description'],
            article['collected_at']
        ))
        conn.commit()
        print(f"  ✅ 已保存: {article['title'][:50]}...")
        return True
    except Exception as e:
        print(f"  ❌ 保存失败: {e}")
        return False
    finally:
        conn.close()


def main():
    """主函数"""
    print("=" * 60)
    print("🚀 OpenAI 博客收集器")
    print("=" * 60)

    # 1. 初始化数据库
    print("\n[1/4] 初始化数据库...")
    init_database()

    # 2. 读取博客首页
    print(f"\n[2/4] 读取 OpenAI 博客首页...")
    homepage = run_jina_read(BLOG_URL)

    if not homepage:
        print("❌ 无法读取博客首页，退出")
        return

    # 3. 提取文章链接
    print(f"\n[3/4] 提取文章链接...")
    links = extract_article_links(homepage)

    if not links:
        print("❌ 没有找到文章链接，退出")
        return

    # 只处理前5篇（避免太慢）
    links_to_process = links[:5]
    print(f"   将处理前 {len(links_to_process)} 篇文章")

    # 4. 读取每篇文章并保存
    print(f"\n[4/4] 读取文章内容...")
    success_count = 0

    for i, url in enumerate(links_to_process, 1):
        print(f"\n[{i}/{len(links_to_process)}] {url}")

        content = run_jina_read(url)
        if content:
            article = extract_article_info(content, url)
            if article and save_article(article):
                success_count += 1

    # 总结
    print("\n" + "=" * 60)
    print("📊 收集完成")
    print(f"   成功: {success_count}/{len(links_to_process)}")
    print(f"   数据库: {DB_PATH}")
    print("=" * 60)

    # 显示收集到的文章
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT title, url FROM articles ORDER BY id DESC LIMIT 5")
    rows = cursor.fetchall()
    conn.close()

    if rows:
        print("\n📚 最新收集的文章:")
        for title, url in rows:
            print(f"   • {title[:40]}...")
            print(f"     {url}")


if __name__ == "__main__":
    main()
