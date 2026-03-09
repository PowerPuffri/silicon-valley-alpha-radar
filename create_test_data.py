"""
创建高质量的测试数据
基于真实场景但明确标注为测试数据
"""

import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict


def create_high_quality_test_data() -> List[Dict]:
    """创建高质量的测试数据"""
    test_activities = []

    # Hacker News 测试数据（模拟真实讨论）
    test_activities.append({
        'id': 'hn_test_001',
        'source': 'Hacker News',
        'activity_type': 'story',
        'title': '[TEST] New Transformer Architecture Achieves SOTA Performance',
        'description': 'Researchers propose a novel transformer variant with improved efficiency and accuracy.',
        'author': 'test_researcher',
        'url': 'https://news.ycombinator.com/item?id=12345',
        'score': 250,
        'comments': 85,
        'timestamp': (datetime.now() - timedelta(hours=2)).isoformat(),
    })

    test_activities.append({
        'id': 'hn_test_002',
        'source': 'Hacker News',
        'activity_type': 'story',
        'title': '[TEST] Open Source LLM Surpasses GPT-4 in Benchmarks',
        'description': 'A new open-source large language model shows competitive performance on standard benchmarks.',
        'author': 'test_ml_engineer',
        'url': 'https://news.ycombinator.com/item?id=12346',
        'score': 420,
        'comments': 156,
        'timestamp': (datetime.now() - timedelta(hours=5)).isoformat(),
    })

    test_activities.append({
        'id': 'hn_test_003',
        'source': 'Hacker News',
        'activity_type': 'story',
        'title': '[TEST] AI Research Breakthrough: Efficient Training Methods',
        'description': 'New techniques reduce training costs by 80% while maintaining model quality.',
        'author': 'test_ai_scientist',
        'url': 'https://news.ycombinator.com/item?id=12347',
        'score': 180,
        'comments': 42,
        'timestamp': (datetime.now() - timedelta(hours=12)).isoformat(),
    })

    # Reddit 测试数据（模拟真实讨论）
    test_activities.append({
        'id': 'reddit_test_001',
        'source': 'r/MachineLearning',
        'activity_type': 'post',
        'title': '[TEST] Paper: Attention Mechanisms in Large Language Models',
        'description': 'Comprehensive analysis of attention patterns in GPT-scale models.',
        'author': 'test_researcher_1',
        'url': 'https://reddit.com/r/MachineLearning/comments/test123/',
        'score': 450,
        'comments': 67,
        'timestamp': (datetime.now() - timedelta(hours=3)).isoformat(),
    })

    test_activities.append({
        'id': 'reddit_test_002',
        'source': 'r/MachineLearning',
        'activity_type': 'post',
        'title': '[TEST] Discussion: The Future of AGI Research',
        'description': 'What are the most promising directions for achieving AGI?',
        'author': 'test_ai_enthusiast',
        'url': 'https://reddit.com/r/MachineLearning/comments/test124/',
        'score': 320,
        'comments': 89,
        'timestamp': (datetime.now() - timedelta(hours=8)).isoformat(),
    })

    test_activities.append({
        'id': 'reddit_test_003',
        'source': 'r/deeplearning',
        'activity_type': 'post',
        'title': '[TEST] Implementation of Mixture-of-Experts for Training',
        'description': 'Tutorial and code for implementing MoE in PyTorch.',
        'author': 'test_ml_engineer_2',
        'url': 'https://reddit.com/r/deeplearning/comments/test125/',
        'score': 280,
        'comments': 34,
        'timestamp': (datetime.now() - timedelta(hours=18)).isoformat(),
    })

    # 更多测试数据
    test_activities.append({
        'id': 'hn_test_004',
        'source': 'Hacker News',
        'activity_type': 'story',
        'title': '[TEST] Multimodal AI System Demonstrates Cross-Modal Reasoning',
        'description': 'New model achieves SOTA on vision-language tasks.',
        'author': 'test_vision_researcher',
        'url': 'https://news.ycombinator.com/item?id=12348',
        'score': 390,
        'comments': 112,
        'timestamp': (datetime.now() - timedelta(hours=6)).isoformat(),
    })

    test_activities.append({
        'id': 'reddit_test_004',
        'source': 'r/artificial',
        'activity_type': 'post',
        'title': '[TEST] Analysis: Transformer Scaling Laws and Their Implications',
        'description': 'Discussion of scaling laws in large language models.',
        'author': 'test_ml_theorist',
        'url': 'https://reddit.com/r/artificial/comments/test126/',
        'score': 195,
        'comments': 28,
        'timestamp': (datetime.now() - timedelta(hours=24)).isoformat(),
    })

    test_activities.append({
        'id': 'hn_test_005',
        'source': 'Hacker News',
        'activity_type': 'story',
        'title': '[TEST] OpenAI Releases New Research on Model Alignment',
        'description': 'Research paper proposes novel techniques for aligning AI systems with human values.',
        'author': 'test_safety_researcher',
        'url': 'https://news.ycombinator.com/item?id=12349',
        'score': 520,
        'comments': 203,
        'timestamp': (datetime.now() - timedelta(hours=1)).isoformat(),
    })

    test_activities.append({
        'id': 'reddit_test_005',
        'source': 'r/ArtificialIntelligence',
        'activity_type': 'post',
        'title': '[TEST] Benchmark: Comparing Performance of Leading LLMs',
        'description': 'Comprehensive benchmark of GPT-4, Claude, and open-source alternatives.',
        'author': 'test_benchmark_author',
        'url': 'https://reddit.com/r/ArtificialIntelligence/comments/test127/',
        'score': 380,
        'comments': 95,
        'timestamp': (datetime.now() - timedelta(hours=4)).isoformat(),
    })

    return test_activities


def save_to_unified_db(activities: List[Dict], db_path: str = "storage/data/unified_activities.db"):
    """保存到统一数据库"""
    print(f"\n💾 保存测试数据到统一数据库...")

    # 初始化数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS activities (
            id TEXT PRIMARY KEY,
            source TEXT NOT NULL,
            activity_type TEXT,
            title TEXT,
            description TEXT,
            author TEXT,
            url TEXT,
            score INTEGER DEFAULT 0,
            comments INTEGER DEFAULT 0,
            timestamp TEXT,
            collected_at TEXT
        )
    ''')

    conn.commit()

    # 清空旧数据
    cursor.execute('DELETE FROM activities')
    conn.commit()

    # 插入数据
    saved_count = 0
    for activity in activities:
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO activities
                (id, source, activity_type, title, description, author, url, score, comments,
                 timestamp, collected_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                activity.get('id'),
                activity.get('source'),
                activity.get('activity_type'),
                activity.get('title'),
                activity.get('description'),
                activity.get('author'),
                activity.get('url'),
                activity.get('score'),
                activity.get('comments'),
                activity.get('timestamp'),
                datetime.now().isoformat()
            ))

            saved_count += 1
        except Exception as e:
            print(f"⚠️  保存活动失败：{e}")

    conn.commit()
    conn.close()

    print(f"✅ 已保存 {saved_count} 条高质量测试数据")


def display_test_summary(db_path: str = "storage/data/unified_activities.db"):
    """显示测试数据摘要"""
    print(f"\n📊 测试数据摘要...")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 获取所有数据，按分数排序
    cursor.execute('SELECT * FROM activities ORDER BY score DESC')
    activities = [dict(row) for row in cursor.fetchall()]

    print(f"\n📋 数据统计：")
    print(f"   总活动数：{len(activities)}")

    # 按来源统计
    cursor.execute('''
        SELECT source, COUNT(*) as count, AVG(score) as avg_score
        FROM activities
        GROUP BY source
        ORDER BY count DESC
    ''')

    source_stats = cursor.fetchall()
    print(f"\n📊 按来源统计：")
    for row in source_stats:
        print(f"   {row[0]}: {row[1]} 条 (平均分: {row[2]:.1f})")

    # 显示前 10 条热门
    print(f"\n🔥 热门内容 (Top 10):")
    for i, activity in enumerate(activities[:10], 1):
        print(f"\n   [{i}] ⭐ {activity['score']} | 💬 {activity['comments']}")
        print(f"       {activity['source']}")
        print(f"       {activity['title'][:60]}...")

    conn.close()

    return activities


def main():
    """主程序"""
    print("\n" + "=" * 80)
    print("🧪 Silicon Valley Alpha Radar - 创建高质量测试数据")
    print("=" * 80)

    print("\n⚠️  重要：")
    print("   以下数据是基于真实场景创建的测试数据")
    print("   所有内容均为虚构，不代表真实事件")
    print("   用于验证推送功能和信息判断层\n")

    # 创建测试数据
    print("🎯 [步骤 1/3] 创建高质量测试数据...")
    test_activities = create_high_quality_test_data()
    print(f"✅ 创建了 {len(test_activities)} 条高质量测试数据")

    # 保存到数据库
    print("\n💾 [步骤 2/3] 保存到统一数据库...")
    save_to_unified_db(test_activities)

    # 显示摘要
    print("\n📊 [步骤 3/3] 显示测试数据摘要...")
    sorted_activities = display_test_summary()

    # 完成
    print("\n" + "=" * 80)
    print("✅ 高质量测试数据创建完成！")
    print("=" * 80)
    print(f"\n📁 数据库: storage/data/unified_activities.db")
    print(f"📊 总活动数: {len(sorted_activities)}")
    print(f"\n💡 提示:")
    print("   • 所有数据都明确标注 [TEST]")
    print("   • 数据基于真实场景但完全虚构")
    print("   • 用于验证推送功能，不是真实信息")


if __name__ == "__main__":
    main()
