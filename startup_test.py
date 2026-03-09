#!/usr/bin/env python3
"""
启动测试脚本 - 简单版
测试 Silicon Valley Alpha Radar 的核心功能
"""

import os
import sys
import sqlite3
from datetime import datetime

# 项目路径
PROJECT_ROOT = '/Users/zhipu_glm/.openclaw/workspace/silicon-valley-alpha-radar'
DB_PATH = os.path.join(PROJECT_ROOT, 'storage/data/collected_articles.db')

print("=" * 60)
print("🚀 Silicon Valley Alpha Radar - 启动测试")
print("=" * 60)
print(f"📅 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# 测试 1: 检查数据库
print("[测试 1] 检查数据库...")
if os.path.exists(DB_PATH):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 统计
    cursor.execute("SELECT COUNT(*) FROM articles")
    count = cursor.fetchone()[0]
    print(f"   ✅ 数据库存在，共 {count} 条记录")

    # 按来源统计
    cursor.execute("SELECT source, COUNT(*) FROM articles GROUP BY source")
    rows = cursor.fetchall()
    print("   📊 数据分布:")
    for source, cnt in rows:
        print(f"      • {source}: {cnt} 条")

    conn.close()
else:
    print(f"   ❌ 数据库不存在: {DB_PATH}")

print()

# 测试 2: 检查关键文件
print("[测试 2] 检查关键文件...")
key_files = [
    'collect_all_sources.py',
    'collect_twitter.py',
    'scheduler.py',
    'config/config.json'
]

for f in key_files:
    path = os.path.join(PROJECT_ROOT, f)
    if os.path.exists(path):
        print(f"   ✅ {f}")
    else:
        print(f"   ❌ {f} 不存在")

print()

# 测试 3: 检查依赖
print("[测试 3] 检查 Python 依赖...")
try:
    import requests
    print("   ✅ requests")
except ImportError:
    print("   ❌ requests 未安装")

try:
    import schedule
    print("   ✅ schedule")
except ImportError:
    print("   ❌ schedule 未安装")

print()

# 总结
print("=" * 60)
print("✅ 启动测试完成")
print("=" * 60)
print()
print("📋 快速命令:")
print("   python scheduler.py          # 单次运行")
print("   python scheduler.py --daemon # 后台运行")
