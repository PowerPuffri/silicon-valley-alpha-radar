"""
测试数据源配置和优先级计算
"""

import sys
import os

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'config'))

from data_sources_config import DATA_SOURCES_CONFIG, calculate_priority
from datetime import datetime, timedelta


def test_configuration():
    """测试配置加载"""
    print("\n" + "=" * 80)
    print("🧪 Silicon Valley Alpha Radar - 配置测试")
    print("=" * 80)

    # 显示官方博客配置
    print("\n📝 [1] 官方博客配置:")
    blogs = DATA_SOURCES_CONFIG["official_blogs"]
    for i, blog in enumerate(blogs, 1):
        print(f"\n   [{i}] {blog['company']} ({blog['priority']})")
        print(f"      Blog: {blog['blog_url']}")
        print(f"      RSS: {blog['rss_url'] if blog['rss_url'] else '无'}")
        print(f"      GitHub: {blog['github_org']}")

    # 显示 Twitter 账号配置
    print("\n🟦 [2] Twitter 账号配置:")
    official = DATA_SOURCES_CONFIG["x_accounts"]["official"]
    for priority in ['P0', 'P1']:
        accounts = official.get(priority, [])
        if accounts:
            print(f"\n   优先级 {priority}:")
            for account in accounts:
                print(f"      @{account['handle']} ({account['company']})")

    # 显示优先级权重
    print("\n📊 [3] 优先级权重配置:")
    weights = DATA_SOURCES_CONFIG["priority_weights"]
    for source, weight in weights.items():
        print(f"   {source}: {weight}")

    # 测试优先级计算
    print("\n🧪 [4] 优先级计算测试:")

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
            'title': '@sama 推文',
            'timestamp': (datetime.now() - timedelta(hours=1)).isoformat(),
            'score': 200,
            'comments': 50,
            'cross_verified': False
        },
        {
            'source_type': 'github_release',
            'title': 'DeepMind AlphaFold 更新',
            'timestamp': (datetime.now() - timedelta(hours=2)).isoformat(),
            'score': 100,
            'comments': 30,
            'cross_verified': False
        },
        {
            'source_type': 'notable_person',
            'title': 'Karpathy 新论文',
            'timestamp': (datetime.now() - timedelta(hours=6)).isoformat(),
            'score': 80,
            'comments': 20,
            'cross_verified': False
        },
        {
            'source_type': 'community',
            'title': 'Hacker News 讨论',
            'timestamp': (datetime.now() - timedelta(hours=24)).isoformat(),
            'score': 50,
            'comments': 10,
            'cross_verified': False
        }
    ]

    for i, item in enumerate(test_items, 1):
        score = calculate_priority(item)
        print(f"\n   [{i}] 优先级: {score}")
        print(f"      来源: {item['source_type']}")
        print(f"      标题: {item['title'][:50]}...")
        print(f"      时间: {item['timestamp']}")
        print(f"      交叉验证: {item.get('cross_verified', False)}")

    # 显示排序结果
    print("\n📊 [5] 排序结果:")
    sorted_items = sorted(test_items, key=lambda x: calculate_priority(x), reverse=True)

    for i, item in enumerate(sorted_items, 1):
        score = calculate_priority(item)
        print(f"\n   [{i}] 优先级: {score}")
        print(f"      {item['source_type']} - {item['title'][:50]}...")

    # 显示交叉验证配置
    print("\n✅ [6] 交叉验证配置:")
    cv = DATA_SOURCES_CONFIG["cross_validation"]
    print(f"   需要验证源数量: {cv['required_sources']}")
    print(f"   有效验证组合:")
    for i, combo in enumerate(cv['valid_combinations'], 1):
        print(f"   {i}. {', '.join(combo)}")

    print("\n" + "=" * 80)
    print("✅ 配置测试完成")
    print("=" * 80)

    # 显示总结
    print("\n📋 配置总结:")
    print(f"   • 官方博客: {len(blogs)} 个")
    print(f"   • Twitter 账号: {len(official['P0']) + len(official['P1']) + len(DATA_SOURCES_CONFIG['x_accounts']['notable_persons']['P0']) + len(DATA_SOURCES_CONFIG['x_accounts']['notable_persons']['P1']) + len(DATA_SOURCES_CONFIG['x_accounts']['notable_persons']['P2'])} 个")
    print(f"   • GitHub 组织: {len(DATA_SOURCES_CONFIG['github']['organizations'])} 个")
    print(f"   • 优先级算法: 来源权重 + 时间新鲜度 + 交叉验证")


if __name__ == "__main__":
    test_configuration()
