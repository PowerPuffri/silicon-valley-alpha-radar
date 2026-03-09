"""
数据源配置 - 按照设计规范
"""

DATA_SOURCES_CONFIG = {
    "official_blogs": [
        # P0 - 核心公司
        {
            "priority": "P0",
            "company": "OpenAI",
            "blog_url": "https://openai.com/blog",
            "rss_url": "https://openai.com/blog/rss.xml",
            "github_org": "openai"
        },
        {
            "priority": "P0",
            "company": "DeepMind",
            "blog_url": "https://deepmind.google",
            "rss_url": None,  # 无 RSS
            "github_org": "deepmind"
        },
        {
            "priority": "P0",
            "company": "Anthropic",
            "blog_url": "https://www.anthropic.com/research",
            "rss_url": None,
            "github_org": "anthropics"
        },
        # P1 - 重要公司
        {
            "priority": "P1",
            "company": "Google AI",
            "blog_url": "https://ai.google",
            "rss_url": None,
            "github_org": "google-research"
        },
        {
            "priority": "P1",
            "company": "Meta AI",
            "blog_url": "https://ai.meta.com",
            "rss_url": None,
            "github_org": "facebookresearch"
        },
        # P2 - 值得关注
        {
            "priority": "P2",
            "company": "Mistral",
            "blog_url": "https://mistral.ai/news",
            "rss_url": None,
            "github_org": "mistralai"
        },
        {
            "priority": "P2",
            "company": "xAI",
            "blog_url": "https://x.ai",
            "rss_url": None,
            "github_org": None
        },
        {
            "priority": "P2",
            "company": "Cohere",
            "blog_url": "https://cohere.com/blog",
            "rss_url": None,
            "github_org": "cohere-ai"
        }
    ],

    "x_accounts": {
        "official": {
            "P0": [
                {"handle": "OpenAI", "company": "OpenAI"},
                {"handle": "DeepMind", "company": "DeepMind"},
                {"handle": "AnthropicAI", "company": "Anthropic"}
            ],
            "P1": [
                {"handle": "GoogleAI", "company": "Google AI"},
                {"handle": "MetaAI", "company": "Meta AI"}
            ]
        },
        "notable_persons": {
            "P0": [
                # OpenAI
                {"handle": "sama", "name": "Sam Altman", "company": "OpenAI"},
                {"handle": "gdb", "name": "Greg Brockman", "company": "OpenAI"},
                {"handle": "ilyasut", "name": "Ilya Sutskever", "company": "OpenAI (前)"},
                # DeepMind
                {"handle": "demishassabis", "name": "Demis Hassabis", "company": "DeepMind"},
                {"handle": "shabor", "name": "Shane Legg", "company": "DeepMind"},
                # Anthropic
                {"handle": "dario_amodei", "name": "Dario Amodei", "company": "Anthropic"}
            ],
            "P1": [
                # 独立/其他
                {"handle": "karpathy", "name": "Andrej Karpathy", "company": "独立"},
                {"handle": "ylecun", "name": "Yann LeCun", "company": "Meta"},
                {"handle": "jeffdean", "name": "Jeff Dean", "company": "Google"}
            ],
            "P2": [
                # 研究员
                {"handle": "simonw", "name": "Simon Willison", "company": "研究员"},
                {"handle": "goodfellow", "name": "Ian Goodfellow", "company": "研究员"},
                {"handle": "ch402", "name": "Chris Olah", "company": "研究员"}
            ]
        }
    },

    "github": {
        "organizations": {
            "P0": ["openai", "deepmind", "anthropics"],
            "P1": ["google-research", "facebookresearch"],
            "P2": ["mistralai", "Stability-AI", "cohere-ai"]
        },
        "event_types": ["release", "pull_request", "discussion"]
    },

    "priority_weights": {
        "official_blog": 100,
        "official_x": 90,
        "github_release": 85,
        "notable_person": 70,
        "github_pr": 50,
        "community": 20
    },

    "cross_validation": {
        "required_sources": 2,
        "valid_combinations": [
            ["official_x", "official_blog"],
            ["official_x", "github_release"],
            ["official_blog", "github_release"],
            ["notable_person", "official_x"],
            ["official_x", "notable_person"]  # 同一公司
        ]
    }
}


def calculate_priority(item, priority_weights=None):
    """
    计算信息优先级

    Args:
        item: 信息项
        priority_weights: 优先级权重配置

    Returns:
        优先级分数
    """
    if priority_weights is None:
        priority_weights = DATA_SOURCES_CONFIG["priority_weights"]

    score = 0

    # 来源权重（最重要）
    source_type = item.get('source_type', 'unknown')
    source_weights = {
        'official_blog': 100,
        'official_x': 90,
        'github_release': 85,
        'notable_person': 70,
        'github_pr': 50,
        'community': 20,
    }
    score += source_weights.get(source_type, 0)

    # 时间新鲜度
    from datetime import datetime, timedelta
    timestamp_str = item.get('timestamp', '')
    if timestamp_str:
        try:
            if isinstance(timestamp_str, str):
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            else:
                timestamp = timestamp_str

            hours_old = (datetime.now() - timestamp).total_seconds() / 3600

            if hours_old < 1:
                score += 30
            elif hours_old < 6:
                score += 20
            elif hours_old < 24:
                score += 10
            elif hours_old < 72:
                score += 5
        except:
            pass

    # 交叉验证加分
    if item.get('cross_verified'):
        score += 25

    # 热度加分
    engagement_score = 0
    if item.get('score'):
        engagement_score += item['score'] // 10
    if item.get('comments'):
        engagement_score += item['comments'] // 5

    # 限制热度加分上限
    score += min(engagement_score, 15)

    return score


if __name__ == "__main__":
    # 测试优先级计算
    test_items = [
        {
            'source_type': 'official_blog',
            'title': 'OpenAI 发布 GPT-5',
            'timestamp': datetime.now().isoformat(),
            'score': 500,
            'comments': 200,
            'cross_verified': True
        },
        {
            'source_type': 'official_x',
            'title': '@sama 发布新研究',
            'timestamp': (datetime.now() - timedelta(hours=2)).isoformat(),
            'score': 200,
            'comments': 50,
            'cross_verified': False
        },
        {
            'source_type': 'community',
            'title': 'Hacker News 讨论',
            'timestamp': (datetime.now() - timedelta(hours=24)).isoformat(),
            'score': 100,
            'comments': 30,
            'cross_verified': False
        }
    ]

    print("🧪 优先级计算测试\n")
    for i, item in enumerate(test_items, 1):
        score = calculate_priority(item)
        print(f"[{i}] {item['source_type']}: {score} 分")
        print(f"    {item['title'][:60]}...")
        print(f"    时间: {item['timestamp']}")
        print(f"    交叉验证: {item.get('cross_verified', False)}")
        print()
