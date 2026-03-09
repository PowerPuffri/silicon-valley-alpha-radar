#!/usr/bin/env python3
"""
直接测试 jina read 命令
"""

import subprocess
import sys

# 测试不同的命令格式
commands = [
    'jina read --url https://openai.com/blog',
    'jina read --url "https://openai.com/blog"',
    'jina "https://openai.com/blog"',
]

for i, cmd in enumerate(commands, 1):
    print(f"\n测试命令 {i}: {cmd}")

    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=20
        )

        print(f"  返回码: {result.returncode}")
        print(f"  标准输出长度: {len(result.stdout)}")
        print(f"  标准错误长度: {len(result.stderr)}")

        if result.returncode == 0:
            print(f"  标准输出前 200 字符:")
            print(result.stdout[:200])
        else:
            print(f"  标准错误:")
            print(result.stderr[:200])

    except Exception as e:
        print(f"  错误: {e}")
