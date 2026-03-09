#!/usr/bin/env python3
import sys
import os

print("✅ 测试脚本正在运行...", file=sys.stderr)
print(f"Python 版本: {sys.version}", file=sys.stderr)
print(f"当前目录: {os.getcwd()}", file=sys.stderr)

print("✅ 测试完成！", file=sys.stdout)
