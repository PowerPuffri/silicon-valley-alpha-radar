"""
GitHub Release 收集器 - 收集顶级AI公司的 GitHub Release
"""

import requests
from datetime import datetime, timedelta
from typing import List, Dict
import sys
import os

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'config'))

from data_sources_config import DATA_SOURCES_CONFIG


class GitHubReleaseCollector:
    def __init__(self):
        """初始化 GitHub Release 收集器"""
        self.organizations = DATA_SOURCES_CONFIG["github"]["organizations"]
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
            'Accept': 'application/vnd.github.v3+json'
        })

    def fetch_releases(self, org: str, days: int = 7) -> List[Dict]:
        """
        获取组织或仓库的 Release

        Args:
            org: 组织名称或仓库 owner
            days: 收集最近多少天

        Returns:
            Release 列表
        """
        print(f"   📡 获取 {org} 的 Releases...")

        releases = []

        try:
            # GitHub API - 获取 releases
            api_url = f"https://api.github.com/repos/{org}/releases"
            response = self.session.get(api_url, timeout=10)
            response.raise_for_status()

            data = response.json()

            for release in data[:50]:  # 限制前 50 个
                # 检查时间
                published_at = release.get('published_at')
                if not published_at:
                    continue

                published_time = datetime.fromisoformat(published_at.replace('Z', '+00:00'))

                # 只保留 7 天内的
                if published_time >= datetime.now() - timedelta(days=days):
                    # 转换为统一格式
                    item = {
                        'id': f"gh_release_{org}_{release.get('id')}",
                        'source_type': 'github_release',
                        'source': f"GitHub/{org}",
                        'activity_type': 'release',
                        'title': release.get('name', 'N/A'),
                        'description': release.get('body', '')[:500] if release.get('body') else '',
                        'author': release.get('author', {}).get('login', 'N/A'),
                        'url': release.get('html_url', ''),
                        'score': 0,  # Release 没有原生分数
                        'comments': 0,  # Release 可能没有 comments 字段
                        'timestamp': published_time.isoformat(),
                        'org': org,
                        'tag_name': release.get('tag_name', ''),
                        'prerelease': release.get('prerelease', False),
                        'draft': release.get('draft', False),
                        'assets_count': len(release.get('assets', [])),
                        'priority': self._get_org_priority(org)
                    }

                    releases.append(item)

            print(f"      ✅ 收集了 {len(releases)} 个 Releases")

        except Exception as e:
            print(f"      ❌ 获取 {org} Releases 失败: {e}")

        return releases

    def _get_org_priority(self, org: str) -> str:
        """获取组织优先级"""
        org_config = None

        for blog in DATA_SOURCES_CONFIG["official_blogs"]:
            if blog['company'].lower() in org.lower():
                org_config = blog
                break

        if org_config:
            return org_config.get('priority', 'P3')

        return 'P3'

    def collect_all_releases(self, days: int = 7) -> List[Dict]:
        """
        收集所有配置的组织的 Releases

        Args:
            days: 收集最近多少天

        Returns:
            所有 Release 列表
        """
        print("\n🔗 [3/4] 收集 GitHub Releases...")

        all_releases = []

        # 按优先级分组
        priority_groups = {
            'P0': [],
            'P1': [],
            'P2': [],
            'P3': []
        }

        for org in self.organizations:
            priority = self._get_org_priority(org)
            priority_groups[priority].append(org)

        # 按优先级收集
        for priority in ['P0', 'P1', 'P2']:
            orgs = priority_groups[priority]
            if not orgs:
                continue

            print(f"\n   优先级 {priority}: {len(orgs)} 个组织")

            for org in orgs:
                releases = self.fetch_releases(org, days)
                all_releases.extend(releases)

        print(f"\n   ✅ GitHub Releases 收集完成: {len(all_releases)} 个")

        return all_releases


if __name__ == "__main__":
    # 测试 GitHub Release 收集器
    print("🧪 Silicon Valley Alpha Radar - GitHub Release 收集器测试")

    collector = GitHubReleaseCollector()
    releases = collector.collect_all_releases(days=7)

    print(f"\n📊 总计: {len(releases)} 个 Releases")

    # 按组织统计
    from collections import Counter
    orgs = [r['org'] for r in releases]
    org_count = Counter(orgs)

    print(f"\n📊 按组织统计:")
    for org, count in org_count.most_common():
        print(f"   {org}: {count} 个")

    # 按优先级统计
    priorities = [r['priority'] for r in releases]
    priority_count = Counter(priorities)

    print(f"\n📊 按优先级统计:")
    for priority, count in priority_count.most_common():
        print(f"   {priority}: {count} 个")

    # 显示前 10 个
    print(f"\n🔥 最新 10 个 Releases:")
    for i, release in enumerate(releases[:10], 1):
        print(f"\n   [{i}] {release['title']}")
        print(f"      📦 {release['org']}")
        print(f"      👤 {release['author']}")
        print(f"      🏷️ Tag: {release['tag_name']}")
        print(f"      🔗 {release['url']}")
        print(f"      🕐 {release['timestamp']}")

    print("\n✅ 测试完成")
