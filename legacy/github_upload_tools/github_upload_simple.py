#!/usr/bin/env python3
"""
GitHub 上传脚本（简化版 - 输出到文件）
"""

import os
import subprocess

# 项目根目录
project_root = '/Users/zhipu_glm/.openclaw/workspace/silicon-valley-alpha-radar'
os.chdir(project_root)

# 输出文件
output_file = '/tmp/github_upload_log.txt'


def log(message):
    """记录日志到文件和控制台"""
    print(message)
    with open(output_file, 'a') as f:
        f.write(message + '\n')


def main():
    """主程序"""
    log("\n" + "=" * 80)
    log("🚀 Silicon Valley Alpha Radar - GitHub 上传")
    log("=" * 80)
    log(f"\n📍 项目目录: {project_root}")
    log(f"\n🔗 GitHub 仓库: https://github.com/zhipu-glm/silicon-valley-alpha-radar")

    # 步骤 1: 初始化 Git
    log("\n[步骤 1/5] 初始化 Git 仓库...")
    result = subprocess.run(['git', 'init'], capture_output=True, text=True)
    log(f"✅ {result.stdout if result.stdout else '已初始化'}")

    # 步骤 2: 添加文件
    log("\n[步骤 2/5] 添加所有文件到 Git...")
    result = subprocess.run(['git', 'add', '.'], capture_output=True, text=True)
    log(f"✅ {result.stdout if result.stdout else '文件已添加'}")

    # 步骤 3: 创建提交
    log("\n[步骤 3/5] 创建初始提交...")
    result = subprocess.run(
        ['git', 'commit', '-m', 'Initial commit: Silicon Valley Alpha Radar'],
        capture_output=True,
        text=True
    )
    if 'nothing to commit' in result.stdout:
        log("✅ 没有新的变化")
    else:
        log(f"✅ {result.stdout if result.stdout else '提交已创建'}")

    # 步骤 4: 添加 remote
    log("\n[步骤 4/5] 添加 GitHub remote...")
    github_url = "https://github.com/zhipu-glm/silicon-valley-alpha-radar.git"
    result = subprocess.run(
        ['git', 'remote', 'add', 'origin', github_url],
        capture_output=True,
        text=True
    )
    log(f"✅ {result.stdout if result.stdout else 'Remote 已添加'}")

    # 步骤 5: 推送
    log("\n[步骤 5/5] 推送到 GitHub...")
    result = subprocess.run(
        ['git', 'push', '-u', 'origin', 'main'],
        capture_output=True,
        text=True,
        timeout=60
    )
    log(f"✅ {result.stdout if result.stdout else '推送完成'}")

    # 检查状态
    log("\n" + "=" * 80)
    log("📊 Git 状态")
    log("=" * 80)

    # 状态
    subprocess.run(['git', 'status'], stdout=open(output_file, 'a'))

    # 远程
    log("\n🔗 Remote:")
    subprocess.run(['git', 'remote', '-v'], stdout=open(output_file, 'a'))

    # 分支
    log("\n🌿 Branch:")
    subprocess.run(['git', 'branch'], stdout=open(output_file, 'a'))

    # 最后提交
    log("\n💾 Latest commit:")
    subprocess.run(['git', 'log', '--oneline', '-1'], stdout=open(output_file, 'a'))

    log("\n" + "=" * 80)
    log("✅ GitHub 上传脚本执行完成！")
    log("=" * 80)
    log(f"\n📁 日志文件: {output_file}")
    log(f"\n💡 查看日志:")
    log(f"   cat {output_file}")


if __name__ == "__main__":
    main()
