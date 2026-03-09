"""
Info Judge - 信息判断层
判断搜集到的信息属于哪个量级，并按照对应的级别进行推送
"""

import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import Counter, defaultdict


class InfoJudge:
    def __init__(self, config_path: str = "config/push_config.json"):
        """
        初始化信息判断器

        Args:
            config_path: 推送配置文件路径
        """
        self.config_path = config_path
        self.config = self._load_config()

        # 配置参数
        self.weights = self.config.get('scoring_weights', {})
        self.thresholds = self.config.get('thresholds', {})
        self.keywords = self.config.get('keywords', {})
        self.monitored_repos = self.config.get('monitored_repos', [])
        self.notable_authors = self.config.get('notable_authors', [])
        self.engagement_thresholds = self.config.get('engagement_thresholds', {})
        self.duplicate_config = self.config.get('duplicate_detection', {})

        # 数据库连接
        self.github_db = "storage/data/github_activity.db"

        # 缓存：用于跨公司共识检测
        self._keyword_cache = {}
        self._company_activity_cache = defaultdict(list)

    def _load_config(self) -> Dict:
        """加载配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"⚠️  配置文件未找到: {self.config_path}")
            return {}
        except json.JSONDecodeError as e:
            print(f"⚠️  配置文件格式错误: {e}")
            return {}

    def _is_monitored_repo(self, repo_name: str) -> bool:
        """
        判断是否在监控范围内的仓库

        Args:
            repo_name: 仓库名称

        Returns:
            是否在监控范围内
        """
        if not repo_name:
            return False

        repo_name_lower = repo_name.lower()

        for pattern in self.monitored_repos:
            if '*' in pattern:
                # 通配符匹配
                prefix = pattern.replace('*', '').lower()
                if repo_name_lower.startswith(prefix):
                    return True
            else:
                # 精确匹配
                if repo_name_lower == pattern.lower():
                    return True

        return False

    def _is_notable_author(self, author: str) -> bool:
        """
        判断是否为知名作者

        Args:
            author: 作者名称

        Returns:
            是否为知名作者
        """
        if not author:
            return False

        author_lower = author.lower()

        for notable in self.notable_authors:
            if notable.lower() in author_lower:
                return True

        return False

    def _contains_keywords(self, text: str, keyword_type: str) -> List[str]:
        """
        检查文本中是否包含特定类型的关键词

        Args:
            text: 要检查的文本
            keyword_type: 关键词类型（breaking/important/tech）

        Returns:
            匹配到的关键词列表
        """
        if not text:
            return []

        text_lower = text.lower()
        keywords_list = self.keywords.get(keyword_type, [])

        matched_keywords = []
        for keyword in keywords_list:
            if keyword.lower() in text_lower:
                matched_keywords.append(keyword)

        return matched_keywords

    def _calculate_engagement_score(self, activity: Dict) -> int:
        """
        计算热度分数

        Args:
            activity: 活动数据

        Returns:
            热度分数（0-2）
        """
        score = 0

        # 检查点赞数（如果有）
        if activity.get('likes', 0) > self.engagement_thresholds.get('high_engagement', 100):
            score += 2
        elif activity.get('likes', 0) > self.engagement_thresholds.get('low_engagement', 10):
            score += 1

        # 检查评论数（如果有）
        if activity.get('comments', 0) > self.engagement_thresholds.get('high_engagement', 100):
            score += 2
        elif activity.get('comments', 0) > self.engagement_thresholds.get('low_engagement', 10):
            score += 1

        return score

    def _detect_cross_company_consensus(self, activities: List[Dict], keyword: str, time_window_hours: int = 72) -> int:
        """
        检测跨公司共识（多个公司在短时间内讨论同一技术方向）

        Args:
            activities: 活动列表
            keyword: 关键词
            time_window_hours: 时间窗口（小时）

        Returns:
            讨论该关键词的公司数量
        """
        if not activities or not keyword:
            return 0

        time_threshold = datetime.now() - timedelta(hours=time_window_hours)

        # 统计讨论该关键词的公司
        companies = set()

        for activity in activities:
            timestamp_str = activity.get('timestamp', '')
            if not timestamp_str:
                continue

            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                if timestamp < time_threshold:
                    continue
            except:
                continue

            # 检查是否包含关键词
            description = activity.get('description', '').lower()
            if keyword.lower() not in description:
                continue

            # 识别公司
            repo_name = activity.get('repo_name', '').lower()
            if 'openai' in repo_name:
                companies.add('OpenAI')
            elif 'deepmind' in repo_name:
                companies.add('DeepMind')
            elif 'anthropic' in repo_name:
                companies.add('Anthropic')
            elif 'google' in repo_name:
                companies.add('Google')
            elif 'facebook' in repo_name or 'meta' in repo_name:
                companies.add('Meta')

        return len(companies)

    def _is_duplicate(self, activity: Dict, recent_activities: List[Dict]) -> bool:
        """
        检查是否为重复信息

        Args:
            activity: 当前活动
            recent_activities: 最近的活动列表

        Returns:
            是否为重复信息
        """
        similarity_threshold = self.duplicate_config.get('similarity_threshold', 0.8)
        time_window_hours = self.duplicate_config.get('time_window_hours', 24)

        current_desc = activity.get('description', '').lower()
        current_title = activity.get('title', '').lower()

        time_threshold = datetime.now() - timedelta(hours=time_window_hours)

        for recent_activity in recent_activities:
            # 检查时间
            timestamp_str = recent_activity.get('timestamp', '')
            if not timestamp_str:
                continue

            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                if timestamp < time_threshold:
                    continue
            except:
                continue

            # 计算相似度
            recent_desc = recent_activity.get('description', '').lower()
            recent_title = recent_activity.get('title', '').lower()

            # 简单的相似度计算（基于 Jaccard 相似度）
            def jaccard_similarity(s1, s2):
                if not s1 or not s2:
                    return 0
                set1 = set(s1.split())
                set2 = set(s2.split())
                intersection = len(set1 & set2)
                union = len(set1 | set2)
                return intersection / union if union > 0 else 0

            title_similarity = jaccard_similarity(current_title, recent_title)
            desc_similarity = jaccard_similarity(current_desc, recent_desc)

            if title_similarity > similarity_threshold or desc_similarity > similarity_threshold:
                return True

        return False

    def judge_activity(self, activity: Dict, recent_activities: List[Dict] = None) -> Tuple[str, int, Dict]:
        """
        判断单个活动的级别

        Args:
            activity: 活动数据
            recent_activities: 最近的活动列表（用于去重和共识检测）

        Returns:
            (级别, 分数, 详细信息)
            级别: "breaking", "important", "normal", "ignore"
            分数: 计算的总分数
            详细信息: 包含判断依据的字典
        """
        if recent_activities is None:
            recent_activities = []

        score = 0
        details = {
            'activity_type': activity.get('activity_type', 'unknown'),
            'repo_name': activity.get('repo_name', ''),
            'author': activity.get('author', ''),
            'matched_keywords': [],
            'reasons': []
        }

        # 1. 活动类型检查
        activity_type = activity.get('activity_type', '').lower()
        if activity_type in ['release', 'security_advisory']:
            score += self.weights.get('release_type', 4)
            details['reasons'].append(f"活动类型: {activity_type} (+{self.weights.get('release_type', 4)})")

        # 2. 作者检查
        if self._is_notable_author(activity.get('author', '')):
            score += self.weights.get('notable_author', 3)
            details['reasons'].append(f"知名作者: {activity.get('author', '')} (+{self.weights.get('notable_author', 3)})")

        # 3. 关键词检查
        breaking_keywords = self._contains_keywords(
            activity.get('description', '') + ' ' + activity.get('title', ''),
            'breaking'
        )
        if breaking_keywords:
            score += self.weights.get('breaking_keyword', 3)
            details['reasons'].append(f"重磅关键词: {', '.join(breaking_keywords)} (+{self.weights.get('breaking_keyword', 3)})")
            details['matched_keywords'].extend(breaking_keywords)

        # 4. 跨公司共识检测
        tech_keywords = self._contains_keywords(
            activity.get('description', '') + ' ' + activity.get('title', ''),
            'tech'
        )
        if tech_keywords:
            details['matched_keywords'].extend(tech_keywords)

            for keyword in tech_keywords[:3]:  # 只检查前3个关键词
                companies_count = self._detect_cross_company_consensus(
                    recent_activities,
                    keyword,
                    time_window_hours=72
                )
                if companies_count >= 3:
                    score += self.weights.get('cross_company_consensus', 4)
                    details['reasons'].append(f"跨公司共识: {keyword} ({companies_count}家公司) (+{self.weights.get('cross_company_consensus', 4)})")
                    break

        # 5. 热度检查
        engagement_score = self._calculate_engagement_score(activity)
        if engagement_score > 0:
            score += engagement_score
            details['reasons'].append(f"高热度 (score: {engagement_score}) (+{engagement_score})")

        # 6. 仓库检查
        if self._is_monitored_repo(activity.get('repo_name', '')):
            score += self.weights.get('monitored_repo', 2)
            details['reasons'].append(f"监控仓库: {activity.get('repo_name', '')} (+{self.weights.get('monitored_repo', 2)})")

        # 7. 其他活动类型
        if activity_type == 'pull_request' and activity.get('state') == 'merged':
            score += self.weights.get('pr_merged', 2)
            details['reasons'].append(f"已合并PR (+{self.weights.get('pr_merged', 2)})")
        elif activity_type in ['issue', 'comment']:
            score += self.weights.get('issue_discussion', 1)
            details['reasons'].append(f"讨论活动 (+{self.weights.get('issue_discussion', 1)})")

        # 判断级别
        thresholds = self.thresholds
        if score >= thresholds.get('breaking', 5):
            level = "breaking"
        elif score >= thresholds.get('important', 2):
            level = "important"
        elif score >= thresholds.get('normal', 1):
            level = "normal"
        else:
            level = "ignore"

        # 去重检查
        if level != "ignore":
            if self._is_duplicate(activity, recent_activities):
                level = "ignore"
                details['reasons'].append("重复信息（已忽略）")

        details['level'] = level
        details['score'] = score

        return level, score, details

    def judge_activities_batch(self, activities: List[Dict]) -> List[Dict]:
        """
        批量判断活动级别

        Args:
            activities: 活动列表

        Returns:
            带有级别信息的活动列表
        """
        results = []
        judged_activities = []

        for activity in activities:
            # 只与已判断的活动比较，避免与自身比较
            level, score, details = self.judge_activity(activity, judged_activities)

            result = activity.copy()
            result['level'] = level
            result['score'] = score
            result['judgment_details'] = details

            results.append(result)

            # 添加到已判断活动列表（用于去重）
            if level != "ignore":
                judged_activities.append(result)

        return results

    def get_judgment_summary(self, judged_activities: List[Dict]) -> Dict:
        """
        获取判断摘要

        Args:
            judged_activities: 已判断的活动列表

        Returns:
            判断摘要
        """
        level_counts = Counter([a.get('level', 'ignore') for a in judged_activities])

        summary = {
            'total': len(judged_activities),
            'breaking': level_counts.get('breaking', 0),
            'important': level_counts.get('important', 0),
            'normal': level_counts.get('normal', 0),
            'ignored': level_counts.get('ignore', 0),
            'timestamp': datetime.now().isoformat()
        }

        return summary


# 测试代码
if __name__ == "__main__":
    print("🧠 Silicon Valley Alpha Radar - 信息判断层")
    print("=" * 60)

    # 创建判断器
    judge = InfoJudge()

    # 测试数据
    test_activities = [
        {
            'activity_type': 'release',
            'repo_name': 'openai/gpt-5',
            'author': 'sama',
            'title': 'GPT-5 Technical Preview',
            'description': 'Breaking: We are excited to announce GPT-5, a revolutionary AGI breakthrough',
            'timestamp': datetime.now().isoformat(),
            'likes': 500,
            'comments': 200
        },
        {
            'activity_type': 'pull_request',
            'repo_name': 'deepmind/alpha',
            'author': 'demishassabis',
            'title': 'Optimize transformer architecture',
            'description': 'Improvement: Add better attention mechanism',
            'state': 'merged',
            'timestamp': datetime.now().isoformat(),
            'likes': 50,
            'comments': 20
        },
        {
            'activity_type': 'issue',
            'repo_name': 'unknown/repo',
            'author': 'randomuser',
            'title': 'Bug fix',
            'description': 'Fix small bug',
            'timestamp': datetime.now().isoformat(),
            'likes': 2,
            'comments': 1
        }
    ]

    # 批量判断
    judged = judge.judge_activities_batch(test_activities)

    # 显示结果
    print("\n📊 判断结果:")
    for i, activity in enumerate(judged, 1):
        print(f"\n[{i}] {activity.get('title', 'N/A')}")
        print(f"   级别: {activity.get('level', 'N/A').upper()}")
        print(f"   分数: {activity.get('score', 0)}")
        print(f"   原因: {activity.get('judgment_details', {}).get('reasons', [])}")

    # 显示摘要
    summary = judge.get_judgment_summary(judged)
    print(f"\n📋 摘要:")
    print(f"   总计: {summary['total']}")
    print(f"   🔴 重磅: {summary['breaking']}")
    print(f"   🟠 重要: {summary['important']}")
    print(f"   🟡 普通: {summary['normal']}")
    print(f"   ⚪ 忽略: {summary['ignored']}")

    print("\n✅ 测试完成！")
