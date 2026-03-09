import subprocess
import json

# 测试 jina 命令
result = subprocess.run(
    ['jina', 'https://openai.com/blog'],
    capture_output=True,
    text=True,
    timeout=20
)

print(f"返回码: {result.returncode}")
print(f"标准输出: {result.stdout[:200] if result.stdout else '空'}")
print(f"标准错误: {result.stderr[:200] if result.stderr else '空'}")
