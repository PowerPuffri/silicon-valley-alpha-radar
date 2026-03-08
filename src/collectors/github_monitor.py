"""
GitHub Monitor - 监控大佬们的仓库活动
追踪 commits, issues, pull requests 和代码结构变化
"""

import github
from github import GithubException
import os
from datetime import datetime, timedelta
import sqlite3
from typing import List, Dict, Optional
import json


class GitHubMonitor:
    def __init__(self, config_path: str = "config/config.json", token: str = None):
        """
        初始化 GitHub 监控器

        Args:
            config_path: 配置文件路径
            token: GitHub Personal Access Token（可选，优先级低于环境变量）
        """
        self.config_path = config_path
        self.github_client = None
        self.storage_path = "storage/data/github_activity.db"
        self._init_storage()

        # 自动认证
        self._auto_authenticate(token)

    def _auto_authenticate(self, provided_token: str = None):
        """
        自动认证：尝试多种方式获取 token
        """
        token = None

        # 优先级 1: 环境变量
        if 'GITHUB_TOKEN' in os.environ:
            token = os.environ['GITHUB_TOKEN']
            print("✅ 从环境变量读取 GITHUB_TOKEN")

        # 优先级 2: 提供的 token
        elif provided_token:
            token = provided_token
            print("✅ 使用提供的 token")

        # 优先级 3: .env 文件（在项目根目录）
        else:
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            env_file = os.path.join(project_root, '.env')
            
            if os.path.exists(env_file):
                try:
                    from dotenv import load_dotenv
                    load_dotenv(env_file)
                    
                    if 'GITHUB_TOKEN' in os.environ:
                        token = os.environ['GITHUB_TOKEN']
                        print("✅ 从 .env 文件读取 GITHUB_TOKEN")
                except ImportError:
                    pass

        # 如果还是没有 token，提示用户
        if not token:
            print("\n" + "=" * 80)
            print("❌ 未找到 GitHub Token！")
            print("=" * 80)
            print("\n请设置 GitHub Token：")
            print("\n方法 1: 设置环境变量")
            print("  export GITHUB_TOKEN='your_token_here'")
            print("\n方法 2: 创建 .env 文件")
            print("  在项目根目录创建 .env 文件，内容：")
            print("  GITHUB_TOKEN=your_token_here")
            print("\n方法 3: 申请 token")
            print("  访问: https://github.com/settings/tokens")
            print("  生成 Personal Access Token (classic)")
            print("  勾选 'repo' 权限")
            print("=" * 80)
            return False

        # 尝试认证
        return self.authenticate(token)

    def _load_config(self, config_path: str) -> Dict:
        """加载配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"配置文件未找到: {config_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"配置文件格式错误: {e}")

    def _init_storage(self):
        """初始化 SQLite 存储"""
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)

        conn = sqlite3.connect(self.storage_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS github_activity (
                id TEXT PRIMARY KEY,
                repo_name TEXT,
                repo_owner TEXT,
                author TEXT,
                activity_type TEXT,
                description TEXT,
                url TEXT,
                stars INTEGER,
                timestamp DATETIME,
                collected_at DATETIME
            )
        ''')

        conn.commit()
        conn.close()

    def authenticate(self, token: str):
        """
        认证 GitHub API

        Args:
            token: GitHub Personal Access Token
        """
        try:
            g = github.Github(token)
            # 测试连接
            user = g.get_user()
            print(f"✅ GitHub API 认证成功！用户: {user.name}")
            self.github_client = g
            return True
        except GithubException as e:
            print(f"❌ GitHub API 认证失败: {e}")
            return False

    def get_repo_activity(self, repo_name: str, days: int = 7) -> List[Dict]:
        """
        获取指定仓库的活动

        Args:
            repo_name: 仓库名（格式：owner/repo）
            days: 最近多少天的活动

        Returns:
            活动列表
        """
        if not self.github_client:
            print("❌ 未认证 GitHub API，请先调用 authenticate()")
            return []

        try:
            repo = self.github_client.get_repo(repo_name)

            activities = []
            since = datetime.now() - timedelta(days=days)

            # 获取最近的 commits
            commits = repo.get_commits(since=since)
            commit_count = 0
            for commit in list(commits)[:50]:  # 最多获取 50 个
                try:
                    activities.append({
                        'id': f"commit_{commit.sha}",
                        'repo_name': repo_name,
                        'repo_owner': repo.owner.login,
                        'author': commit.author.login if commit.author else 'unknown',
                        'activity_type': 'commit',
                        'description': commit.commit.message.split('\n')[0][:200],  # 前 200 字
                        'url': commit.html_url,
                        'stars': repo.stargazers_count,
                        'timestamp': commit.author.date,
                        'collected_at': datetime.now()
                    })
                    commit_count += 1
                except Exception as e:
                    print(f"⚠️  处理 commit 失败: {e}")
                    continue

            # 获取最近的 issues
            issues = repo.get_issues(state='open', since=since)
            issue_count = 0
            for issue in list(issues)[:30]:  # 最多获取 30 个
                try:
                    activities.append({
                        'id': f"issue_{issue.id}",
                        'repo_name': repo_name,
                        'repo_owner': repo.owner.login,
                        'author': issue.user.login,
                        'activity_type': 'issue',
                        'description': issue.title,
                        'url': issue.html_url,
                        'stars': repo.stargazers_count,
                        'timestamp': issue.created_at,
                        'collected_at': datetime.now()
                    })
                    issue_count += 1
                except Exception as e:
                    print(f"⚠️  处理 issue 失败: {e}")
                    continue

            # 获取最近的 pull requests
            pulls = repo.get_pull_requests(state='open', since=since)
            pr_count = 0
            for pr in list(pulls)[:30]:  # 最多获取 30 个
                try:
                    activities.append({
                        'id': f"pr_{pr.id}",
                        'repo_name': repo_name,
                        'repo_owner': repo.owner.login,
                        'author': pr.user.login,
                        'activity_type': 'pull_request',
                        'description': pr.title,
                        'url': pr.html_url,
                        'stars': repo.stargazers_count,
                        'timestamp': pr.created_at,
                        'collected_at': datetime.now()
                    })
                    pr_count += 1
                except Exception as e:
                    print(f"⚠️  处理 PR 失败: {e}")
                    continue

            print(f"✅ {repo_name}: {commit_count} commits, {issue_count} issues, {pr_count} PRs")

            return activities

        except GithubException as e:
            print(f"❌ 获取仓库 {repo_name} 活动失败: {e}")
            return []

    def save_activities(self, activities: List[Dict]):
        """
        保存活动到 SQLite 数据库

        Args:
            activities: 活动列表
        """
        conn = sqlite3.connect(self.storage_path)
        cursor = conn.cursor()

        for activity in activities:
            cursor.execute('''
                INSERT OR REPLACE INTO github_activity
                (id, repo_name, repo_owner, author, activity_type,
                 description, url, stars, timestamp, collected_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                activity['id'],
                activity['repo_name'],
                activity['repo_owner'],
                activity['author'],
                activity['activity_type'],
                activity['description'],
                activity['url'],
                activity['stars'],
                activity['timestamp'],
                activity['collected_at']
            ))

        conn.commit()
        conn.close()

        print(f"✅ 已保存 {len(activities)} 条 GitHub 活动到数据库")

    def monitor_all_repos(self, days: int = 7) -> List[Dict]:
        """
        监控所有配置的仓库

        Args:
            days: 收集最近多少天的活动

        Returns:
            所有活动列表
        """
        config = self._load_config(self.config_path)

        # 遍历所有公司
        all_activities = []

        for company, company_config in config.get('monitored_accounts', {}).items():
            print(f"\n📊 正在监控 {company_config.get('name', company)} 的仓库...")

            # 监控每个仓库
            company_activities = []
            for repo_name in company_config.get('github_repos', []):
                activities = self.get_repo_activity(repo_name, days)
                company_activities.extend(activities)

            all_activities.extend(company_activities)

        # 保存所有活动
        if all_activities:
            self.save_activities(all_activities)

        return all_activities

    def get_repo_stats(self, repo_name: str) -> Dict:
        """
        获取仓库的统计信息

        Args:
            repo_name: 仓库名

        Returns:
            统计信息字典
        """
        if not self.github_client:
            raise RuntimeError("未认证 GitHub API，请先调用 authenticate()")

        try:
            repo = self.github_client.get_repo(repo_name)

            stats = {
                'repo_name': repo_name,
                'stars': repo.stargazers_count,
                'forks': repo.forks_count,
                'open_issues': repo.open_issues_count,
                'language': repo.language,
                'description': repo.description,
                'updated_at': repo.updated_at,
                'created_at': repo.created_at
            }

            return stats

        except GithubException as e:
            print(f"❌ 获取仓库 {repo_name} 统计失败: {e}")
            return None

    def get_recent_stats(self, hours: int = 24) -> Dict:
        """
        获取最近统计信息

        Args:
            hours: 最近多少小时的统计

        Returns:
            统计信息字典
        """
        conn = sqlite3.connect(self.storage_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        since = datetime.now() - timedelta(hours=hours)

        cursor.execute('''
            SELECT COUNT(*) as total_activities,
                   COUNT(DISTINCT repo_name) as active_repos,
                   COUNT(*) FILTER (WHERE timestamp >= ?) as recent_activities
            FROM github_activity
            WHERE timestamp >= ?
        ''', (since,))

        row = cursor.fetchone()
        conn.close()

        return {
            'total_activities': row[0] or 0,
            'active_repos': row[1] or 0,
            'recent_activities': row[2] or 0,
            'period_hours': hours
        }


# 主程序 - 用于测试
if __name__ == "__main__":
    print("🎯 Silicon Valley Alpha Radar - GitHub Monitor")
    print("=" * 60)

    # 测试模式
    monitor = GitHubMonitor()

    print("\n✅ 认证成功，可以开始监控")
