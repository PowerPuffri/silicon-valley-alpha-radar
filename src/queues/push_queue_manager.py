"""
Push Queue Manager - 推送队列管理
管理不同级别的推送队列和调度
"""

import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import deque
from threading import Lock
import asyncio
from apscheduler.schedulers.background import BackgroundScheduler


class PushQueueManager:
    def __init__(self, config_path: str = "config/push_config.json", db_path: str = "storage/data/push_queue.db"):
        """
        初始化推送队列管理器

        Args:
            config_path: 推送配置文件路径
            db_path: 队列数据库路径
        """
        self.config_path = config_path
        self.config = self._load_config()
        self.db_path = db_path

        # 推送策略
        self.push_policy = self.config.get('push_policy', {})

        # 内存队列（用于快速访问）
        self.urgent_queue = deque()  # 🔴 立即推送
        self.hourly_queue = deque()  # 🟠 每小时推送
        self.normal_queue = deque()  # 🟡 每3小时推送

        # 线程锁
        self.lock = Lock()

        # 调度器
        self.scheduler = BackgroundScheduler()

        # 初始化数据库
        self._init_db()

        # 初始化调度器
        self._init_scheduler()

        # 统计信息
        self.stats = {
            'total_queued': 0,
            'breaking_sent': 0,
            'important_sent': 0,
            'normal_sent': 0,
            'last_sent_time': None
        }

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

    def _init_db(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 创建推送队列表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS push_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                level TEXT NOT NULL,
                activity_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                sent_at TEXT,
                status TEXT DEFAULT 'pending',
                attempts INTEGER DEFAULT 0,
                error_message TEXT
            )
        ''')

        # 创建统计表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS push_stats (
                date TEXT PRIMARY KEY,
                breaking_sent INTEGER DEFAULT 0,
                important_sent INTEGER DEFAULT 0,
                normal_sent INTEGER DEFAULT 0,
                total_sent INTEGER DEFAULT 0
            )
        ''')

        conn.commit()
        conn.close()

    def _init_scheduler(self):
        """初始化调度器"""
        # 每小时推送
        self.scheduler.add_job(
            self._process_hourly_queue,
            'cron',
            minute=0,
            id='hourly_push'
        )

        # 每3小时推送（09:00, 12:00, 15:00, 18:00, 21:00）
        schedule_times = self.push_policy.get('normal', {}).get('schedule', ['09:00', '12:00', '15:00', '18:00', '21:00'])
        for time_str in schedule_times:
            hour, minute = map(int, time_str.split(':'))
            self.scheduler.add_job(
                self._process_normal_queue,
                'cron',
                hour=hour,
                minute=minute,
                id=f'normal_push_{time_str}'
            )

        # 启动调度器
        self.scheduler.start()

    def add_to_queue(self, activity: Dict, level: str) -> bool:
        """
        添加活动到队列

        Args:
            activity: 活动数据
            level: 级别（breaking/important/normal/ignore）

        Returns:
            是否成功添加
        """
        if level == "ignore":
            return False

        # 检查策略是否启用
        policy = self.push_policy.get(level, {})
        if not policy.get('enabled', True):
            return False

        with self.lock:
            # 添加到内存队列
            if level == "breaking":
                self.urgent_queue.append(activity)
            elif level == "important":
                self.hourly_queue.append(activity)
            elif level == "normal":
                self.normal_queue.append(activity)

            # 添加到数据库
            self._save_to_db(activity, level)

            self.stats['total_queued'] += 1

        print(f"✅ 已添加到 {level} 队列: {activity.get('title', 'N/A')[:50]}")

        return True

    def _save_to_db(self, activity: Dict, level: str):
        """保存到数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        import json
        cursor.execute('''
            INSERT INTO push_queue (level, activity_json, created_at, status)
            VALUES (?, ?, ?, ?)
        ''', (
            level,
            json.dumps(activity, ensure_ascii=False),
            datetime.now().isoformat(),
            'pending'
        ))

        conn.commit()
        conn.close()

    def _process_urgent_queue(self, callback=None):
        """
        处理紧急队列（立即推送）

        Args:
            callback: 推送回调函数
        """
        if not self.push_policy.get('breaking', {}).get('enabled', True):
            return

        # 检查静默时段
        quiet_hours = self.push_policy.get('breaking', {}).get('quiet_hours', [])
        current_hour = datetime.now().hour

        for time_range in quiet_hours:
            start, end = map(int, time_range.split('-'))
            if start <= current_hour < end:
                print(f"🔇 静默时段，跳过紧急推送")
                return

        # 检查每日最大推送数量
        max_per_day = self.push_policy.get('breaking', {}).get('max_per_day', 10)
        today_sent = self._get_today_sent_count('breaking')

        if today_sent >= max_per_day:
            print(f"⚠️  今日重磅推送已达上限 ({max_per_day})")
            return

        with self.lock:
            while self.urgent_queue:
                if today_sent >= max_per_day:
                    break

                activity = self.urgent_queue.popleft()

                if callback:
                    try:
                        success = callback(activity, 'breaking')
                        if success:
                            self._mark_as_sent(activity['id'], 'breaking')
                            self.stats['breaking_sent'] += 1
                            today_sent += 1
                        else:
                            # 推送失败，放回队列
                            self.urgent_queue.appendleft(activity)
                    except Exception as e:
                        print(f"❌ 推送失败: {e}")

    def _process_hourly_queue(self, callback=None):
        """
        处理每小时队列

        Args:
            callback: 推送回调函数
        """
        if not self.push_policy.get('important', {}).get('enabled', True):
            return

        batch_size = self.push_policy.get('important', {}).get('batch_size', 5)

        with self.lock:
            count = 0
            while self.hourly_queue and count < batch_size:
                activity = self.hourly_queue.popleft()

                if callback:
                    try:
                        success = callback(activity, 'important')
                        if success:
                            self._mark_as_sent(activity['id'], 'important')
                            self.stats['important_sent'] += 1
                            count += 1
                        else:
                            # 推送失败，放回队列
                            self.hourly_queue.appendleft(activity)
                            break
                    except Exception as e:
                        print(f"❌ 推送失败: {e}")

    def _process_normal_queue(self, callback=None):
        """
        处理普通队列（每3小时）

        Args:
            callback: 推送回调函数
        """
        if not self.push_policy.get('normal', {}).get('enabled', True):
            return

        batch_size = self.push_policy.get('normal', {}).get('batch_size', 10)

        with self.lock:
            count = 0
            while self.normal_queue and count < batch_size:
                activity = self.normal_queue.popleft()

                if callback:
                    try:
                        success = callback(activity, 'normal')
                        if success:
                            self._mark_as_sent(activity['id'], 'normal')
                            self.stats['normal_sent'] += 1
                            count += 1
                        else:
                            # 推送失败，放回队列
                            self.normal_queue.appendleft(activity)
                            break
                    except Exception as e:
                        print(f"❌ 推送失败: {e}")

    def _mark_as_sent(self, activity_id: int, level: str):
        """标记为已发送"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE push_queue
            SET sent_at = ?, status = 'sent'
            WHERE id = ?
        ''', (datetime.now().isoformat(), activity_id))

        # 更新统计
        date_str = datetime.now().strftime('%Y-%m-%d')
        cursor.execute('''
            INSERT INTO push_stats (date, {level}_sent, total_sent)
            VALUES (?, 1, 1)
            ON CONFLICT(date) DO UPDATE SET
                {level}_sent = {level}_sent + 1,
                total_sent = total_sent + 1
        '''.format(level=level), (date_str,))

        conn.commit()
        conn.close()

        self.stats['last_sent_time'] = datetime.now().isoformat()

    def _get_today_sent_count(self, level: str) -> int:
        """获取今日已发送数量"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        date_str = datetime.now().strftime('%Y-%m-%d')

        cursor.execute(f'''
            SELECT {level}_sent FROM push_stats WHERE date = ?
        ''', (date_str,))

        result = cursor.fetchone()
        conn.close()

        return result[0] if result else 0

    def get_queue_status(self) -> Dict:
        """
        获取队列状态

        Returns:
            队列状态字典
        """
        with self.lock:
            return {
                'urgent_queue_size': len(self.urgent_queue),
                'hourly_queue_size': len(self.hourly_queue),
                'normal_queue_size': len(self.normal_queue),
                'stats': self.stats.copy()
            }

    def get_pending_items(self, level: str, limit: int = 10) -> List[Dict]:
        """
        获取待推送项目

        Args:
            level: 级别
            limit: 数量限制

        Returns:
            活动列表
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM push_queue
            WHERE level = ? AND status = 'pending'
            ORDER BY created_at ASC
            LIMIT ?
        ''', (level, limit))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def clear_old_items(self, days: int = 7):
        """
        清理旧项目

        Args:
            days: 保留天数
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        threshold = datetime.now() - timedelta(days=days)

        cursor.execute('''
            DELETE FROM push_queue
            WHERE sent_at < ? AND status = 'sent'
        ''', (threshold.isoformat(),))

        deleted = cursor.rowcount
        conn.commit()
        conn.close()

        print(f"🧹 清理了 {deleted} 条旧推送记录")

    def stop(self):
        """停止队列管理器"""
        print("🛑 停止推送队列管理器...")
        self.scheduler.shutdown(wait=False)
        print("✅ 队列管理器已停止")


# 测试代码
if __name__ == "__main__":
    print("🚀 Silicon Valley Alpha Radar - 推送队列管理器")
    print("=" * 60)

    # 创建队列管理器
    queue_manager = PushQueueManager()

    # 测试添加项目
    test_activities = [
        {
            'id': 1,
            'title': '重磅：GPT-5 发布',
            'level': 'breaking'
        },
        {
            'id': 2,
            'title': '重要：OpenAI 更新 API',
            'level': 'important'
        },
        {
            'id': 3,
            'title': '普通：GitHub 提交',
            'level': 'normal'
        }
    ]

    print("\n📥 添加测试项目...")
    for activity in test_activities:
        queue_manager.add_to_queue(activity, activity['level'])

    # 显示队列状态
    status = queue_manager.get_queue_status()
    print(f"\n📊 队列状态:")
    print(f"   🔴 紧急队列: {status['urgent_queue_size']}")
    print(f"   🟠 每小时队列: {status['hourly_queue_size']}")
    print(f"   🟡 普通队列: {status['normal_queue_size']}")
    print(f"   📋 总计排队: {status['stats']['total_queued']}")

    print("\n✅ 测试完成！")

    # 停止
    queue_manager.stop()
