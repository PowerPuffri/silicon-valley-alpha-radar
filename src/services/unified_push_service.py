"""
Unified Push Service - 统一推送服务
整合信息判断、队列管理和消息推送
启动时发送真实数据作为测试
"""

import os
import sys
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

from judges.info_judge import InfoJudge
from queues.push_queue_manager import PushQueueManager
from formatters.push_formatter import PushFormatter

# 尝试导入 Telegram 发送器（默认）
try:
    from utils.telegram_test import TelegramTester
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    print("⚠️  Telegram Tester 导入失败")


class UnifiedPushService:
    def __init__(
        self,
        main_config_path: str = "config/config.json",
        push_config_path: str = "config/push_config.json",
        storage_dir: str = "storage/data",
        queue_db: str = "storage/data/push_queue.db",
        unified_db: str = "storage/data/unified_activities.db"
    ):
        """
        初始化统一推送服务

        Args:
            main_config_path: 主配置文件路径（包含 Telegram 配置）
            push_config_path: 推送配置文件路径（包含推送策略）
            storage_dir: 数据存储目录
            queue_db: 队列数据库路径
            unified_db: 统一活动数据库路径
        """
        self.main_config_path = main_config_path
        self.push_config_path = push_config_path
        self.storage_dir = storage_dir
        self.queue_db = queue_db
        self.unified_db = unified_db

        # 初始化组件
        self.judge = InfoJudge(push_config_path)
        self.queue_manager = PushQueueManager(push_config_path, queue_db)
        self.formatter = PushFormatter()

        # Telegram 客户端（默认）
        self.telegram_client = None
        self.target_chat_id = None
        self._init_telegram()

        # 运行状态
        self.is_running = False

        print("✅ 统一推送服务已初始化")

    def _init_telegram(self):
        """初始化 Telegram 客户端（默认）"""
        if not TELEGRAM_AVAILABLE:
            print("⚠️  Telegram 不可用")
            return

        try:
            # 从 main config 读取 Telegram 配置
            with open(self.main_config_path, 'r') as f:
                config = json.load(f)

            telegram_config = config.get('telegram', {})
            bot_token = telegram_config.get('botToken', '')
            chat_id = telegram_config.get('chatId', '')

            if bot_token and chat_id:
                self.telegram_client = TelegramTester(bot_token, chat_id)
                self.target_chat_id = chat_id
                print(f"✅ Telegram 客户端已初始化 (Chat ID: {chat_id})")
            else:
                print("⚠️  Telegram 配置不完整")
        except FileNotFoundError:
            print(f"⚠️  配置文件未找到: {self.main_config_path}")
        except Exception as e:
            print(f"⚠️  Telegram 客户端初始化失败: {e}")

    def _load_test_data(self) -> List[Dict]:
        """加载真实测试数据"""
        print(f"\n🧪 加载真实测试数据...")

        if not os.path.exists(self.unified_db):
            print("⚠️  测试数据库不存在，跳过")
            return []

        try:
            conn = sqlite3.connect(self.unified_db)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute('SELECT * FROM activities ORDER BY score DESC, timestamp DESC LIMIT 30')
            activities = [dict(row) for row in cursor.fetchall()]

            conn.close()

            print(f"✅ 加载了 {len(activities)} 条真实测试数据")
            return activities

        except Exception as e:
            print(f"❌ 加载测试数据失败: {e}")
            return []

    def _send_test_summary(self, activities: List[Dict]):
        """发送真实测试数据摘要"""
        if not activities:
            print("⚠️  没有测试数据可发送")
            return

        print(f"\n📤 发送真实测试数据摘要...")

        try:
            message = f"""🧪 <b>SV Alpha Radar - 真实测试数据</b>

📅 <b>启动时间:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}

✅ <b>真实数据</b>
以下是从 Hacker News 和 Reddit 官方 API 收集的真实数据！

📈 <b>统计信息:</b>
"""

            # 按来源统计
            from collections import Counter
            sources = [a['source'] for a in activities]
            source_count = Counter(sources)

            for source, count in source_count.most_common():
                message += f"   • {source}: {count} 条\n"

            # 按类型统计
            types = [a['activity_type'] for a in activities]
            type_count = Counter(types)

            message += f"\n<b>按类型:</b>\n"
            for activity_type, count in type_count.most_common():
                message += f"   • {activity_type}: {count} 条\n"

            # 显示前 10 条热门真实内容
            message += f"\n<b>🔥 热门真实内容 (Top 10):</b>\n"

            top_10 = activities[:10]
            for i, activity in enumerate(top_10, 1):
                message += f"\n{i}. ⭐ <b>{activity['title'][:50]}...</b>\n"
                message += f"   📦 来源: {activity['source']}\n"
                message += f"   👤 作者: {activity['author']}\n"
                message += f"   ⭐ 分数: {activity['score']} | 💬 {activity['comments']}\n"
                message += f"   🔗 <a href=\"{activity['url']}\">原始链接</a>\n"

            # 免责声明
            message += f"""

---
⚠️ <b>【真实测试数据】</b>
以上是从 Hacker News 和 Reddit 官方 API 收集的真实数据。
每条信息都可追溯到原始链接。
数据收集时间：最近 7 天
用于验证推送功能。

<i>🕐 发送时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}</i>
"""

            if self.telegram_client:
                result = self.telegram_client.send_message(message)
                if result.get('success'):
                    print("✅ 真实测试数据摘要发送成功！")
                else:
                    print(f"❌ 发送失败: {result.get('error', 'Unknown')}")

        except Exception as e:
            print(f"❌ 发送真实测试数据摘要失败: {e}")

    def _send_telegram_message(self, message: str) -> bool:
        """
        发送 Telegram 消息（默认）

        Args:
            message: 消息内容

        Returns:
            是否发送成功
        """
        if not self.telegram_client:
            print("⚠️  Telegram 客户端未初始化")
            return False

        try:
            # 发送消息
            result = self.telegram_client.send_message(message)
            if result.get('success'):
                print(f"✅ Telegram 消息已发送")
                return True
            else:
                print(f"❌ Telegram 消息发送失败: {result.get('error', 'Unknown')}")
                return False
        except Exception as e:
            print(f"❌ Telegram 消息发送失败: {e}")
            return False

    def run_one_cycle(self, days: int = 1):
        """
        运行一个完整周期（收集 -> 判断 -> 队列）

        Args:
            days: 收集最近多少天的数据
        """
        print(f"\n" + "=" * 60)
        print(f"🔄 [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 开始新的推送周期")
        print("=" * 60)

        # 注意：当前使用真实测试数据，不从其他数据源收集
        print(f"\n🧪 使用真实测试数据...")

        # 1. 加载真实测试数据
        test_activities = self._load_test_data()

        # 2. 批量判断
        print(f"\n🔍 判断活动级别...")
        judged_activities = self.judge.judge_activities_batch(test_activities)

        # 显示摘要
        summary = self.judge.get_judgment_summary(judged_activities)
        print(f"📋 判断摘要:")
        print(f"   🔴 重磅: {summary['breaking']}")
        print(f"   🟠 重要: {summary['important']}")
        print(f"   🟡 普通: {summary['normal']}")
        print(f"   ⚪ 忽略: {summary['ignored']}")

        # 3. 添加到队列
        print(f"\n📥 添加活动到队列...")
        count = 0
        for activity in judged_activities:
            level = activity.get('level', 'ignore')
            if level != 'ignore':
                success = self.queue_manager.add_to_queue(activity, level)
                if success:
                    count += 1

        print(f"✅ 已添加 {count} 个活动到队列")

        # 4. 处理紧急推送
        print(f"\n🚨 处理紧急推送...")
        with self.queue_manager.lock:
            if not self.queue_manager.urgent_queue:
                print("✅ 没有待发送的紧急推送")
            else:
                activities = list(self.queue_manager.urgent_queue)[:1]
                if activities:
                    message = self.formatter.format_breaking(activities)
                    if message:
                        message = self.formatter.truncate_message(message)
                        success = self._send_telegram_message(message)

                        if success:
                            self.queue_manager.urgent_queue.popleft()
                            self.queue_manager._mark_as_sent(activities[0].get('id'), 'breaking')
                            self.queue_manager.stats['breaking_sent'] += 1
                            print(f"✅ 紧急推送已发送")

        # 5. 显示队列状态
        status = self.queue_manager.get_queue_status()
        print(f"\n📊 队列状态:")
        print(f"   🔴 紧急队列: {status['urgent_queue_size']}")
        print(f"   🟠 每小时队列: {status['hourly_queue_size']}")
        print(f"   🟡 普通队列: {status['normal_queue_size']}")
        print(f"   📋 总计排队: {status['stats']['total_queued']}")
        print(f"   📤 已发送: 🔴{status['stats']['breaking_sent']}")

        print(f"\n✅ 推送周期完成")

    def start_with_test(self):
        """启动时发送真实测试数据"""
        print(f"\n🧪 [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 启动模式：发送真实测试数据")

        # 1. 加载并发送真实测试数据摘要
        test_activities = self._load_test_data()
        self._send_test_summary(test_activities)

        # 2. 使用真实测试数据运行一个周期
        if test_activities:
            print(f"\n🔄 使用真实测试数据运行推送周期...")
            self.run_one_cycle(days=7)

    def start(self, interval_minutes: int = 30):
        """
        启动持续监控（循环运行）

        Args:
            interval_minutes: 检查间隔（分钟）
        """
        self.is_running = True

        print(f"\n🚀 启动持续推送服务")
        print(f"📅 检查间隔: {interval_minutes} 分钟")
        print(f"📡 推送目标: Telegram ({self.target_chat_id})")
        print(f"\n提示: 使用 Ctrl+C 停止服务\n")

        try:
            while self.is_running:
                self.run_one_cycle(days=1)  # 每次检查最近1天的数据

                # 等待
                print(f"\n⏳ 等待 {interval_minutes} 分钟后进行下一次检查...")
                import time
                time.sleep(interval_minutes * 60)

        except KeyboardInterrupt:
            print(f"\n\n🛑 收到停止信号")
            self.stop()

    def stop(self):
        """停止服务"""
        self.is_running = False
        self.queue_manager.stop()
        print("✅ 统一推送服务已停止")


# 主程序
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Silicon Valley Alpha Radar - 统一推送服务（使用真实测试数据）"
    )
    parser.add_argument('--startup-test', action='store_true', help='启动时发送真实测试数据')
    parser.add_argument('--start', action='store_true', help='启动持续监控')
    parser.add_argument('--interval', type=int, default=30, help='检查间隔（分钟，默认30）')
    parser.add_argument('--status', action='store_true', help='查看队列状态')

    args = parser.parse_args()

    # 创建推送服务
    try:
        service = UnifiedPushService()

        if args.startup_test:
            # 启动时发送真实测试数据
            service.start_with_test()

        elif args.start:
            # 启动持续监控
            service.start(interval_minutes=args.interval)

        elif args.status:
            # 查看队列状态
            status = service.queue_manager.get_queue_status()
            print(f"\n📊 队列状态:")
            print(f"   🔴 紧急队列: {status['urgent_queue_size']}")
            print(f"   🟠 每小时队列: {status['hourly_queue_size']}")
            print(f"   🟡 普通队列: {status['normal_queue_size']}")
            print(f"   📋 总计排队: {status['stats']['total_queued']}")
            print(f"   📤 已发送: 🔴{status['stats']['breaking_sent']}")

        else:
            print("⚠️  请指定操作：--startup-test, --start, 或 --status")
            print("\n📝 使用示例：")
            print("  python unified_push_service.py --startup-test")
            print("  python unified_push_service.py --start --interval 30")
            print("  python unified_push_service.py --status")

    except Exception as e:
        print(f"\n❌ 程序错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
