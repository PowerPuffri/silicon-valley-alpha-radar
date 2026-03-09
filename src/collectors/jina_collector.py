#!/usr/bin/env python3
"""
Jina Collector - 使用 jina-cli 收集真实数据
"""

import subprocess
import json
import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional


class JinaCollector:
    """使用 jina-cli 收集网页数据"""

    def __init__(self, db_path: str = "storage/data/github_activity.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """初始化数据库"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS collected_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_type TEXT,
                source_url TEXT,
                title TEXT,
                content TEXT,
                collected_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()

    def read_url(self, url: str) -> Optional[Dict]:
        """
        使用 jina-cli 读取 URL

        Args:
            url: 要读取的 URL

        Returns:
            解析后的数据字典，失败返回 None
        """
        try:
            # 调用 jina read 命令
            result = subprocess.run(
                ['jina', 'read', '--url', url, '--output', 'json'],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode != 0:
                print(f"❌ jina read 失败: {result.stderr}")
                return None

            # 解析 JSON 输出
            data = json.loads(result.stdout)

            if data.get('success'):
                return data.get('data', {})
            else:
                print(f"❌ jina 返回失败: {data}")
                return None

        except subprocess.TimeoutExpired:
            print(f"⏰ jina read 超时: {url}")
            return None
        except json.JSONDecodeError as e:
            print(f"❌ JSON 解析失败: {e}")
            return None
        except FileNotFoundError:
            print("❌ jina 命令不存在，请先安装 jina-cli")
            return None

    def collect_blog(self, company: str, url: str) -> bool:
        """
        收集官方博客

        Args:
            company: 公司名（如 OpenAI）
            url: 博客 URL

        Returns:
            是否成功
        """
        print(f"📰 收集 {company} 博客: {url}")

        data = self.read_url(url)
        if not data:
            return False

        # 存入数据库
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO collected_data (source_type, source_url, title, content)
            VALUES (?, ?, ?, ?)
        ''', (
            f'blog:{company}',
            url,
            data.get('title', ''),
            data.get('content', '')[:5000]  # 限制内容长度
        ))

        conn.commit()
        conn.close()

        print(f"✅ 已保存: {data.get('title', '无标题')}")
        return True

    def collect_x_profile(self, username: str) -> bool:
        """
        收集 X/Twitter 用户主页

        Args:
            username: 用户名（不带@）

        Returns:
            是否成功
        """
        url = f"https://x.com/{username}"
        print(f"🐦 收集 X 用户: @{username}")

        data = self.read_url(url)
        if not data:
            return False

        # 存入数据库
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO collected_data (source_type, source_url, title, content)
            VALUES (?, ?, ?, ?)
        ''', (
            'x_profile',
            url,
            f"@{username}",
            data.get('content', '')[:5000]
        ))

        conn.commit()
        conn.close()

        print(f"✅ 已保存 @{username} 的数据")
        return True

    def collect_all(self) -> Dict[str, int]:
        """
        收集所有配置的数据源

        Returns:
            统计结果
        """
        stats = {'success': 0, 'failed': 0}

        # 官方博客
        blogs = [
            ('OpenAI', 'https://openai.com/blog'),
            ('DeepMind', 'https://deepmind.google'),
            ('Anthropic', 'https://anthropic.com/research'),
        ]

        for company, url in blogs:
            if self.collect_blog(company, url):
                stats['success'] += 1
            else:
                stats['failed'] += 1

        # X 账号
        x_accounts = ['OpenAI', 'DeepMindAI', 'AnthropicAI']

        for username in x_accounts:
            if self.collect_x_profile(username):
                stats['success'] += 1
            else:
                stats['failed'] += 1

        return stats


def main():
    """测试收集器"""
    print("=" * 50)
    print("🚀 Jina 数据收集器测试")
    print("=" * 50)

    collector = JinaCollector()

    # 先测试单个 URL
    print("\n📰 测试读取 OpenAI 博客...")
    data = collector.read_url("https://openai.com/blog")

    if data:
        print(f"✅ 成功!")
        print(f"   标题: {data.get('title', 'N/A')}")
        print(f"   内容长度: {len(data.get('content', ''))} 字符")
    else:
        print("❌ 失败，请检查 jina-cli 是否安装")
        print("   安装命令: curl -fsSL https://raw.githubusercontent.com/geekjourneyx/jina-cli/main/scripts/install.sh | bash")

    print("\n" + "=" * 50)

    # 收集所有
    print("\n📊 开始收集所有数据源...")
    stats = collector.collect_all()

    print(f"\n📈 收集完成:")
    print(f"   ✅ 成功: {stats['success']}")
    print(f"   ❌ 失败: {stats['failed']}")


if __name__ == "__main__":
    main()
