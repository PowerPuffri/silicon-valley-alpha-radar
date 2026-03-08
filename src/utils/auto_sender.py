"""
Auto Sender - 自动化调度和推送系统
定时执行数据收集、分析和推送到 Telegram
"""

import os
import sys
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import sqlite3
from apscheduler.schedulers.background import BackgroundScheduler
import requests

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src_root = os.path.join(project_root, 'src')
sys.path.insert(0, project_root)
sys.path.insert(0, src_root)

from collectors.github_monitor import GitHubMonitor
from generators.report_generator import ReportGenerator
from utils.telegram_test import TelegramTester


class AutoSender:
    def __init__(self, config_path: str = "config/config.json", 
                 target_chat_id: str = "7974510481"):
        """
        初始化自动化发送器

        Args:
            config_path: 配置文件路径
            target_chat_id: 接收报告的 Telegram Chat ID
        """
        self.config = self._load_config(config_path)
        self.target_chat_id = target_chat_id
        
        # 初始化组件
        self.github_monitor = GitHubMonitor(config_path)
        self.report_generator = ReportGenerator()
        self.telegram_sender = TelegramTester(self.config['telegram']['botToken'], target_chat_id)
        
        # 初始化调度器
        self.scheduler = BackgroundScheduler()
        
        # 存储目录
        self.storage_reports = "output/reports"
        self.storage_data = "storage/data"

    def _load_config(self, config_path: str) -> Dict:
        """加载配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"配置文件未找到: {config_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"配置文件格式错误: {e}")

    def send_trend_alert(self, title: str, content: str, urgency: str = "normal") -> Dict:
        """
        发送趋势告警到 Telegram

        Args:
            title: 告警标题
            content: 告警内容
            urgency: 紧急级别
        """
        # 格式化消息
        urgency_emoji = "🔴" if urgency == "high" else "🟠" if urgency == "medium" else "🟢"
        
        message = f"""
{urgency_emoji} <b>{title}</b>

{content}

---
<i>📅 发送时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}</i>
"""
        
        return self.telegram_sender.send_message(message)

    def send_daily_report(self, report: str, summary: Dict) -> Dict:
        """
        发送每日报告到 Telegram

        Args:
            report: 报告内容（Markdown 格式）
            summary: 数据摘要

        Returns:
            发送结果
        """
        # 格式化每日报告消息
        message = f"""
<b>📊 Silicon Valley Alpha Radar - 每日报告</b>

📅 <b>报告时间:</b> {datetime.now().strftime('%Y年%m月%d日 %H:%M')}

📈 <b>数据概览:</b>
• GitHub 活动: {summary.get('github_total', 0)} 条
• Reddit 帖子: {summary.get('reddit_total', 0)} 条
• Hacker News: {summary.get('hackernews_total', 0)} 条

⏱️ <b>数据耗时:</b> {summary.get('duration', 0):.1f} 秒

---

{report}

---
<i>💡 信息不对称是终极力量</i>
"""
        
        return self.telegram_sender.send_message(message)

    def send_weekly_summary(self, week_data: Dict) -> Dict:
        """
        发送周总结到 Telegram

        Args:
            week_data: 一周的数据汇总

        Returns:
            发送结果
        """
        message = f"""
<b>📊 Silicon Valley Alpha Radar - 周总结</b>

📅 <b>时间范围:</b> {week_data.get('start_date')} - {week_data.get('end_date')}

📈 <b>本周数据:</b>
• 总活动数: {week_data.get('total_activities', 0)} 条
• 新趋势数: {week_data.get('new_trends', 0)} 个
• AI 相关文章: {week_data.get('ai_related_stories', 0)} 篇

🔥 <b>最活跃话题:</b>
{week_data.get('top_topics', '')}

---

<i>💡 保持信息优势！</i>
"""
        
        return self.telegram_sender.send_message(message)

    def scheduled_daily_collection(self):
        """
        定时任务：每日数据收集
        """
        print(f"\n📅 [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 定时任务：每日数据收集")
        
        # 收集数据
        try:
            # GitHub 收集（7 天）
            github_activities = self.github_monitor.monitor_all_repos(days=7)
            
            # 生成报告
            print(f"✅ GitHub 数据收集完成，生成报告...")
            summary = self.report_generator.generate_activity_summary(
                {'github_posts': [a for a in github_activities]},
                {'twitter_posts': []},  # Twitter 暂无数据
                {'reddit_posts': []}  # Reddit 暂无数据
            )
            
            report = self.report_generator.generate_markdown_report(summary)
            
            # 发送到 Telegram
            print(f"📡 发送每日报告到 Telegram...")
            result = self.send_daily_report(report, {
                'github_total': len(github_activities),
                'reddit_total': 0,
                'hackernews_total': 0,
                'duration': 0
            })
            
            if result.get('success'):
                print(f"✅ 每日报告发送成功！")
            else:
                print(f"❌ 每日报告发送失败：{result.get('error', 'Unknown')}")
            
        except Exception as e:
            print(f"❌ 定时任务执行失败: {e}")
            import traceback
            traceback.print_exc()
            
            # 发送错误告警
            self.send_trend_alert(
                "⚠️ 每日报告执行失败",
                f"错误: {str(e)}",
                urgency="high"
            )

    def scheduled_trend_analysis(self):
        """
        定时任务：趋势分析和推送
        """
        print(f"\n🔍 [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 定时任务：趋势分析")
        
        # 等待实现
        print(f"✅ 趋势分析任务触发（功能待实现）")

    def start_scheduler(self, daily_time: str = "00:00"):
        """
        启动调度器

        Args:
            daily_time: 每日运行时间（格式：HH:MM，默认 00:00 UTC）
        """
        print(f"\n🕶️ [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 启动自动化调度器...")
        print(f"📅 每日运行时间: {daily_time} (UTC)")
        
        # 添加每日数据收集任务
        hour, minute = map(int, daily_time.split(':'))
        
        self.scheduler.add_job(
            self.scheduled_daily_collection,
            'cron',
            hour=hour,
            minute=minute,
            timezone='UTC',
            id='daily_data_collection'
        )
        
        # 添加趋势分析任务（每小时检查一次）
        self.scheduler.add_job(
            self.scheduled_trend_analysis,
            'interval',
            hours=1,
            id='trend_analysis_hourly'
        )
        
        # 启动调度器
        self.scheduler.start()
        
        print(f"✅ 调度器已启动！")
        print(f"\n📋 已配置的定时任务：")
        print(f"   1. 每日数据收集 - {daily_time} UTC")
        print(f"   2. 趋势分析 - 每小时")
        print(f"\n📡 自动推送到: Chat ID {self.target_chat_id}")

    def stop_scheduler(self):
        """
        停止调度器
        """
        print(f"\n🛑 [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 停止调度器...")
        
        self.scheduler.shutdown(wait=False)
        print(f"✅ 调度器已停止")

    def get_status(self) -> Dict:
        """
        获取调度器状态

        Returns:
            状态字典
        """
        jobs = self.scheduler.get_jobs()
        
        return {
            'status': 'running' if self.scheduler.running else 'stopped',
            'jobs_count': len(jobs),
            'jobs': [
                {
                    'id': job.id,
                    'name': job.name,
                    'next_run_time': job.next_run_time.strftime('%Y-%m-%d %H:%M:%S') if job.next_run_time else None
                }
                for job in jobs
            ]
        }

    def add_one_time_task(self, task_type: str, delay_minutes: int = 0):
        """
        添加一次性延时任务

        Args:
            task_type: 任务类型
            delay_minutes: 延迟分钟数
        """
        print(f"\n➕ [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 添加一次性任务: {task_type}，延迟 {delay_minutes} 分钟")

        if task_type == "daily_collection":
            self.scheduler.add_job(
                self.scheduled_daily_collection,
                'date',
                run_date=datetime.now() + timedelta(minutes=delay_minutes),
                id='one_time_daily_collection'
            )
        elif task_type == "test_trend_alert":
            self.scheduler.add_job(
                lambda: self.send_trend_alert("测试趋势告警", "这是一个测试消息，5分钟后将发送实际报告。", urgency="medium"),
                'date',
                run_date=datetime.now() + timedelta(minutes=5),
                id='test_trend_alert'
            )


def main():
    """主程序"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Silicon Valley Alpha Radar - 自动化调度器"
    )
    parser.add_argument('--start', action='store_true', help='启动调度器')
    parser.add_argument('--stop', action='store_true', help='停止调度器')
    parser.add_argument('--status', action='store_true', help='查看调度器状态')
    parser.add_argument('--daily-time', type=str, default="00:00", 
                    help='每日数据收集时间（格式：HH:MM，默认 00:00 UTC）')
    parser.add_argument('--chat-id', type=str, default="7974510481",
                    help='接收报告的 Telegram Chat ID')
    parser.add_argument('--test-alert', action='store_true', help='发送测试趋势告警')

    args = parser.parse_args()

    # 初始化自动发送器
    try:
        sender = AutoSender(target_chat_id=args.chat_id)

        if args.status:
            # 查看状态
            status = sender.get_status()
            print(f"\n📋 调度器状态:")
            print(f"   运行状态: {status['status']}")
            print(f"   定时任务数: {status['jobs_count']}")
            print(f"\n已配置的任务:")
            for job in status['jobs']:
                print(f"   - {job['name']}: 下次运行 {job['next_run_time']}")

        elif args.start:
            # 启动调度器
            sender.start_scheduler(daily_time=args.daily_time)

        elif args.stop:
            # 停止调度器
            sender.stop_scheduler()

        elif args.test_alert:
            # 发送测试告警
            sender.send_trend_alert(
                "🔔 自动化系统测试",
                "这是 Silicon Valley Alpha Radar 的自动推送测试。\n\n系统运行正常，自动化任务已配置。\n\n预期功能：\n• 每日数据收集\n• 自动趋势分析\n• Telegram 报告推送",
                urgency="medium"
            )

        else:
            print("⚠️  请指定操作：--start, --stop, --status, 或 --test-alert")
            print("\n📝 使用示例：")
            print("  python auto_sender.py --start")
            print("  python auto_sender.py --daily-time 08:00")
            print("  python auto_sender.py --test-alert")

    except Exception as e:
        print(f"\n❌ 程序错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
