#!/usr/bin/env python3
"""
Silicon Valley Alpha Radar - 完整系统测试
发动测试：收集→判断→存储→推送完整流程
"""

import os
import sys
import json
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict

# 添加项目根目录到 Python 路径
project_root = '/Users/zhipu_glm/.openclaw/workspace/silicon-valley-alpha-radar'
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))
sys.path.insert(0, os.path.join(project_root, 'src', 'collectors'))
sys.path.insert(0, os.path.join(project_root, 'src', 'services'))
sys.path.insert(0, os.path.join(project_root, 'src', 'formatters'))
sys.path.insert(0, os.path.join(project_root, 'src', 'judges'))
sys.path.insert(0, os.path.join(project_root, 'src', 'queues'))
sys.path.insert(0, os.path.join(project_root, 'src', 'utils'))
sys.path.insert(0, os.path.join(project_root, 'config'))

from judges.info_judge import InfoJudge
from queues.push_queue_manager import PushQueueManager
from formatters.push_formatter import PushFormatter
from utils.telegram_test import TelegramTester


class SystemTest:
    """完整系统测试"""

    def __init__(self):
        """初始化测试系统"""
        self.judge = InfoJudge("config/push_config.json")
        self.queue_manager = PushQueueManager("config/push_config.json", "storage/data/push_queue.db")
        self.formatter = PushFormatter()
        self.telegram_client = None
        self._init_telegram()

        print("✅ 测试系统初始化完成")

    def _init_telegram(self):
        """初始化 Telegram 客户端"""
        try:
            with open("config/config.json", 'r') as f:
                config = json.load(f)

            telegram_config = config.get('twitter', {}).get('telegram', config.get('telegram', {}))
            bot_token = telegram_config.get('botToken', '')
            chat_id = telegram_config.get('chatId', '')

            if bot_token and chat_id:
                self.telegram_client = TelegramTester(bot_token, chat_id)
                print(f"✅ Telegram 已初始化")
            else:
                print(f"⚠️  Telegram 配置不完整")
        except Exception as e:
            print(f"⚠️  Telegram 初始化失败: {e}")

    def test_1_data_collection(self) -> Dict:
        """
        测试 1：数据收集
        """
        print("\n" + "=" * 80)
        print("📡 测试 1/6: 数据收集")
        print("=" * 80)

        test_results = {
            'total': 0,
            'collected': 0,
            'sources': {}
        }

        # 1.1 检查数据库
        print("\n   📊 [1.1] 检查数据库状态...")
        databases = {
            'OpenAI 博客': 'storage/data/collected_articles.db',
            'Hacker News': 'storage/data/hacker_news.db',
            'Reddit': 'storage/data/reddit_posts.db',
            'Push Queue': 'storage/data/push_queue.db',
            'Trend History': 'storage/data/trend_history.db'
        }

        for name, db_path in databases.items():
            if os.path.exists(db_path):
                try:
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()

                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = [row[0] for row in cursor.fetchall()]

                    for table in tables:
                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        count = cursor.fetchone()[0]
                        print(f"      ✅ {name}: {table}: {count} 条")

                    conn.close()
                except Exception as e:
                    print(f"      ⚠️  {name}: 读取失败 ({e})")
            else:
                print(f"      ⚠️  {name}: 不存在")

        # 1.2 加载 OpenAI 博客数据
        print("\n   📥 [1.2] 加载 OpenAI 博客数据...")
        try:
            conn = sqlite3.connect("storage/data/collected_articles.db")
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute('SELECT * FROM articles ORDER BY id DESC LIMIT 10')
            openai_articles = [dict(row) for row in cursor.fetchall()]

            conn.close()

            print(f"      ✅ 加载了 {len(openai_articles)} 篇 OpenAI 博客")
            test_results['sources']['OpenAI Blog'] = len(openai_articles)
            test_results['collected'] += len(openai_articles)

            for i, article in enumerate(openai_articles[:5], 1):
                print(f"         {i}. {article.get('title', '')[:50]}...")

        except Exception as e:
            print(f"      ❌ 加载失败: {e}")

        test_results['total'] = test_results['collected']

        print(f"\n   ✅ 测试 1 完成: 收集了 {test_results['collected']} 条数据")

        return test_results

    def test_2_priority_calculation(self, activities: List[Dict]) -> List[Dict]:
        """
        测试 2：优先级计算
        """
        print("\n" + "=" * 80)
        print("🔍 测试 2/6: 优先级计算")
        print("=" * 80)

        if not activities:
            print("   ⚠️  没有可用的活动")
            return []

        # 计算优先级
        print(f"\n   📊 [2.1] 计算优先级: {len(activities)} 个活动...")

        prioritized_activities = []

        for i, activity in enumerate(activities):
            try:
                # 添加必要的字段
                if 'source_type' not in activity:
                    if 'source' in activity and 'blog' in activity.get('source', '').lower():
                        activity['source_type'] = 'official_blog'
                    elif 'twitter' in activity.get('source', '').lower():
                        activity['source_type'] = 'official_x'
                    else:
                        activity['source_type'] = 'community'

                activity['priority_score'] = self.judge.judge_activity(activity)

                prioritized_activities.append(activity)

            except Exception as e:
                print(f"      ⚠️  计算活动 {i} 失败: {e}")

        # 排序
        prioritized = sorted(prioritized_activities, key=lambda x: x['priority_score'], 0), reverse=True)

        print(f"   ✅ 优先级计算完成")

        # 统计
        print(f"\n   📊 [2.2] 优先级统计:")
        high = len([a for a in prioritized if a['priority_score'] >= 90])
        medium = len([a for a in prioritized if 50 <= a['priority_score'] < 90])
        low = len([a for a in prioritized if a['priority_score'] < 50])

        print(f"      🔴 高 (>=90): {high}")
        print(f"      🟠 中 (50-89): {medium}")
        print(f"      🟡 低 (<50): {low}")

        # 显示 Top 10
        print(f"\n   🔥 [2.3] 高优先级活动 (Top 10):")
        for i, activity in enumerate(prioritized[:10], 1):
            score = activity['priority_score']
            title = activity.get('title', activity.get('slug', ''))[:50]
            source = activity.get('source', 'OpenAI Blog')

            print(f"      [{i}] 优先级: {score}")
            print(f"         📦 {source}")
            print(f"         📄 {title}...")

        print(f"\n   ✅ 测试 2 完成: 计算了 {len(prioritized)} 个活动的优先级")

        return prioritized

    def test_3_queue_management(self, activities: List[Dict]) -> Dict:
        """
        测试 3：队列管理
        """
        print("\n" + "=" * 80)
        print("📥 测试 3/6: 队列管理")
        print("=" * 80)

        if not activities:
            print("   ⚠️  没有可用的活动")
            return {}

        # 清空队列
        print(f"\n   🧹 [3.1] 清空推送队列...")
        with self.queue_manager.lock:
            while self.queue_manager.urgent_queue:
                self.queue_manager.urgent_queue.popleft()
            while self.queue_manager.hourly_queue:
                self.queue_manager.hourly_queue.popleft()
            while self.queue_manager.normal_queue:
                self.queue_manager.normal_queue.popleft()

        print(f"   ✅ 队列已清空")

        # 添加到队列
        print(f"\n   📥 [3.2] 添加活动到队列...")
        added = 0

        for activity in activities:
            try:
                level = activity.get('priority_level', 'unknown')

                if level == 'breaking':
                    success = self.queue_manager.add_to_queue(activity, 'urgent')
                elif level == 'important':
                    success = self.queue_manager.add_to_queue(activity, 'hourly')
                elif level == 'normal':
                    success = self.queue_manager.add_to_queue(activity, 'normal')

                if success:
                    added += 1

            except Exception as e:
                print(f"      ⚠️  添加活动失败: {e}")

        print(f"   ✅ 成功添加 {added} 个活动到队列")

        # 查看队列状态
        print(f"\n   📊 [3.3] 队列状态:")
        with self.queue_manager.lock:
            urgent = len(self.queue_manager.urgent_queue)
            hourly = len(self.queue_manager.hourly_queue)
            normal = len(self.queue_manager.normal_queue)

        print(f"      🔴 紧急队列: {urgent}")
        print(f"      🟠 每小时队列: {hourly}")
        print(f"      🟡 普通队列: {normal}")

        queue_stats = {
            'added': added,
            'urgent': urgent,
            'hourly': hourly,
            'normal': normal
        }

        print(f"   ✅ 测试 3 完成: 队列管理测试完成")

        return queue_stats

    def test_4_message_formatting(self, activities: List[Dict]) -> Dict:
        """
        测试 4：消息格式化
        """
        print("\n" + "=" * 80)
        print("📝 测试 4/6: 消息格式化")
        print("=" * 80)

        if not activities:
            print("   ⚠️  没有可用的活动")
            return {}

        formatted_messages = {}

        # 格式化 BREAKING 消息
        print(f"\n   📝 [4.1] 格式化 BREAKING 消息...")
        try:
            breaking_activities = activities[:1]  # 只测试 1 篇
            if breaking_activities:
                message = self.formatter.format_breaking(breaking_activities)
                message = self.formatter.truncate_message(message)

                formatted_messages['breaking'] = {
                    'length': len(message),
                    'activities': len(breaking_activities)
                }

                print(f"      ✅ BREAKING 消息格式化成功")
                print(f"      长度: {len(message)} 字符")
                print(f"      活动数: {len(breaking_activities)}")
        except Exception as e:
            print(f"      ❌ BREAKING 格式化失败: {e}")

        # 格式化汇总消息
        print(f"\n   📝 [4.2] 格式化汇总消息...")
        try:
            all_activities = activities[:5]  # 测试 5 篇
            message = self.formatter.format_normal_batch(all_activities)
            message = self.formatter.truncate_message(message)

            formatted_messages['summary'] = {
                'length': len(message),
                'activities': len(all_activities)
            }

            print(f"      ✅ 汇总消息格式化成功")
            print(f"      长度: {len(message)} 字符")
            print(f"      活动数: {len(all_activities)}")
        except Exception as e:
            print(f"      ❌ 汇总格式化失败: {e}")

        print(f"   ✅ 测试 4 完成: 消息格式化测试完成")

        return formatted_messages

    def test_5_telegram_push(self, activities: List[Dict]) -> bool:
        """
        测试 5：Telegram 推送
        """
        print("\n" + "=" * 80)
        print("📤 测试 5/6: Telegram 推送")
        print("=" * 80)

        if not self.telegram_client:
            print("   ⚠️  Telegram 客户端未初始化")
            return False

        if not activities:
            print("   ⚠️  没有可用的活动")
            return False

        # 发送测试消息
        print(f"\n   📡 [5.1] 发送测试消息...")

        # 使用纯文本格式
        test_message = f"""🧪 SV Alpha Radar - 系统发动测试

📅 时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}

✅ 测试内容:

[测试文章 1]
标题: {activities[0].get('title', 'Test')[:50]}
链接: {activities[0].get('url', 'https://openai.com/blog')}
来源: {activities[0].get('source', 'OpenAI Blog')}

---

🧪 这是系统发动测试消息
用于验证完整的数据收集→判断→存储→推送流程。

🕐 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}
"""

        try:
            result = self.telegram_client.send_message(test_message)

            if result.get('success'):
                print(f"   ✅ Telegram 推送成功！")
                print(f"      返回: {result.get('message', 'Success')}")
                return True
            else:
                print(f"   ❌ Telegram 推送失败: {result.get('error', 'Unknown')}")
                return False

        except Exception as e:
            print(f"   ❌ 推送失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    def test_6_integration(self, activities: List[Dict]) -> Dict:
        """
        测试 6：完整集成流程
        """
        print("\n" + "=" * 80)
        print("🔄 测试 6/6: 完整集成流程")
        print("=" * 80)

        integration_results = {
            'steps': {},
            'total_time': 0,
            'success': False
        }

        start_time = datetime.now()

        # 6.1 收集
        print(f"\n   📡 [6.1] 收集数据...")
        collection_results = self.test_1_data_collection()
        integration_results['steps']['collection'] = collection_results['collected']
        step1_time = datetime.now() - start_time

        # 6.2 判断
        print(f"\n   🔍 [6.2] 判断优先级...")
        prioritized = self.test_2_priority_calculation(activities if 'OpenAI Blog' in collection_results['sources'] else [])
        integration_results['steps']['prioritization'] = len(prioritized)
        step2_time = datetime.now() - step1_time - start_time

        # 6.3 队列
        print(f"\n   📥 [6.3] 队列管理...")
        queue_stats = self.test_3_queue_management(prioritized if prioritized else [])
        integration_results['steps']['queue'] = queue_stats['added']
        step3_time = datetime.now() - step2_time - start_time

        # 6.4 格式化
        print(f"\n   📝 [6.4] 消息格式化...")
        formatted = self.test_4_message_formatting(prioritized if prioritized else [])
        integration_results['steps']['formatting'] = formatted.get('breaking', {}).get('activities', 0)
        step4_time = datetime.now() - step3_time - start_time

        # 6.5 推送
        print(f"\n   📤 [6.5] Telegram 推送...")
        push_success = self.test_5_telegram_push(prioritized if prioritized else [])
        integration_results['steps']['push'] = push_success
        step5_time = datetime.now() - step4_time - start_time

        integration_results['total_time'] = (datetime.now() - start_time).total_seconds()

        if (collection_results['collected'] > 0 and
            len(prioritized) > 0 and
            queue_stats['added'] > 0 and
            push_success):
            integration_results['success'] = True

        print(f"\n   ✅ 测试 6 完成: 集成测试完成")
        print(f"      总耗时: {integration_results['total_time']} 秒")
        print(f"      成功: {'✅' if integration_results['success'] else '❌'}")

        return integration_results

    def main(self):
        """主测试程序"""
        print("\n" + "=" * 80)
        print("🚀 Silicon Valley Alpha Radar - 系统发动测试")
        print("=" * 80)
        print("\n🎯 测试目标:")
        print("   1. 数据收集")
        print("   2. 优先级计算")
        print("   3. 队列管理")
        print("   4. 消息格式化")
        print("   5. Telegram 推送")
        print("   6. 完整集成流程")

        # 加载测试数据
        print("\n📥 [0] 加载测试数据...")
        activities = []

        try:
            conn = sqlite3.connect("storage/data/collected_articles.db")
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute('SELECT * FROM articles ORDER BY id DESC')
            activities = [dict(row) for row in cursor.fetchall()]

            conn.close()

            print(f"✅ 加载了 {len(activities)} 个活动")
        except Exception as e:
            print(f"❌ 加载数据失败: {e}")

        if not activities:
            print("\n❌ 没有测试数据，无法继续")
            return

        # 执行完整测试
        integration_results = self.test_6_integration(activities)

        # 最终报告
        print("\n" + "=" * 80)
        print("📊 Silicon Valley Alpha Radar - 系统发动测试完成")
        print("=" * 80)

        print(f"\n✅ 测试总结:")
        print(f"   📡 数据收集: {integration_results['steps'].get('collection', 0)} 条")
        print(f"   🔍 优先级计算: {integration_results['steps'].get('prioritization', 0)} 条")
        print(f"   📥 队列管理: {integration_results['steps'].get('queue', 0)} 条")
        print(f"   📝 消息格式化: {integration_results['steps'].get('formatting', 0)} 条")
        print(f"   📤 Telegram 推送: {'✅ 成功' if integration_results['steps'].get('push', False) else '❌ 失败'}")
        print(f"   🔄 完整流程: {'✅ 成功' if integration_results['success'] else '❌ 失败'}")
        print(f"   ⏱️  总耗时: {integration_results['total_time']} 秒")

        print(f"\n📋 最终状态:")
        print(f"   系统状态: {'✅ 运行正常' if integration_results['success'] else '⚠️  部分失败'}")
        print(f"   数据收集: {'✅ 正常' if integration_results['steps'].get('collection', 0) > 0 else '❌ 无数据'}")
        print(f"   推送功能: {'✅ 正常' if integration_results['steps'].get('push', False) else '❌ 异常'}")

        print("\n" + "=" * 80)
        print("🎉 系统发动测试完成！")
        print("=" * 80)
        print(f"\n📱 请检查 Telegram 是否收到测试消息")
        print(f"🚀 系统准备好进入正常运行状态！")


if __name__ == "__main__":
    tester = SystemTest()
    tester.main()
