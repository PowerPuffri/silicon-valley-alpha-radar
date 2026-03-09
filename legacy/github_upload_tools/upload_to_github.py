#!/usr/bin/env python3
"""
GitHub 上传脚本
初始化 Git 仓库并推送到 GitHub
"""

import os
import sys
import subprocess

# 项目根目录
project_root = '/Users/zhipu_glm/.openclaw/workspace/silicon-valley-alpha-radar'
os.chdir(project_root)


def step_1_init_git():
    """步骤 1: 初始化 Git 仓库"""
    print("\n" + "=" * 80)
    print("📡 步骤 1/5: 初始化 Git 仓库")
    print("=" * 80)

    try:
        # 初始化 Git
        result = subprocess.run(['git', 'init'], capture_output=True, text=True)

        if 'Initialized' in result.stdout or 'Reinitialized' in result.stdout:
            print("   ✅ Git 仓库初始化成功")
            return True
        else:
            print("   ✅ Git 仓库已存在")
            return True

    except Exception as e:
        print(f"   ❌ 初始化失败: {e}")
        return False


def step_2_add_files():
    """步骤 2: 添加所有文件到 Git"""
    print("\n" + "=" * 80)
    print("📁 步骤 2/5: 添加所有文件到 Git")
    print("=" * 80)

    try:
        # 添加所有文件
        result = subprocess.run(['git', 'add', '.'], capture_output=True, text=True)

        if result.returncode == 0:
            print("   ✅ 文件添加成功")
            return True
        else:
            print(f"   ❌ 添加失败: {result.stderr}")
            return False

    except Exception as e:
        print(f"   ❌ 添加失败: {e}")
        return False


def step_3_create_commit():
    """步骤 3: 创建初始提交"""
    print("\n" + "=" * 80)
    print("💾 步骤 3/5: 创建初始提交")
    print("=" * 80)

    try:
        # 创建提交
        result = subprocess.run(
            ['git', 'commit', '-m', 'Initial commit: Silicon Valley Alpha Radar'],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print("   ✅ 提交创建成功")
            return True
        else:
            # 可能没有变化
            if 'nothing to commit' in result.stdout.lower():
                print("   ✅ 没有新的变化")
                return True
            else:
                print(f"   ❌ 提交失败: {result.stderr}")
                return False

    except Exception as e:
        print(f"   ❌ 提交失败: {e}")
        return False


def step_4_add_remote(github_url: str):
    """步骤 4: 添加 GitHub remote"""
    print("\n" + "=" * 80)
    print("🔗 步骤 4/5: 添加 GitHub remote")
    print("=" * 80)
    print(f"   GitHub URL: {github_url}")

    try:
        # 添加 remote
        result = subprocess.run(
            ['git', 'remote', 'add', 'origin', github_url],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print("   ✅ Remote 添加成功")
            return True
        else:
            print(f"   ❌ 添加 remote 失败: {result.stderr}")
            return False

    except Exception as e:
        print(f"   ❌ 添加 remote 失败: {e}")
        return False


def step_5_push_to_github(branch: str = "main"):
    """步骤 5: 推送到 GitHub"""
    print("\n" + "=" * 80)
    print("🚀 步骤 5/5: 推送到 GitHub")
    print("=" * 80)
    print(f"   分支: {branch}")

    try:
        # 检查远程
        result = subprocess.run(['git', 'remote', '-v'], capture_output=True, text=True)

        if 'origin' not in result.stdout:
            print("   ❌ 没有 remote，请先添加")
            return False

        # 推送
        result = subprocess.run(
            ['git', 'push', '-u', 'origin', branch],
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode == 0:
            print("   ✅ 推送成功！")
            return True
        else:
            print(f"   ❌ 推送失败: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        print("   ❌ 推送超时")
        return False
    except Exception as e:
        print(f"   ❌ 推送失败: {e}")
        return False


def show_status():
    """显示 Git 状态"""
    print("\n" + "=" * 80)
    print("📊 Git 状态")
    print("=" * 80)

    try:
        # 查看状态
        subprocess.run(['git', 'status'])
        print()

        # 查看分支
        subprocess.run(['git', 'branch'])
        print()

        # 查看远程
        subprocess.run(['git', 'remote', '-v'])

    except Exception as e:
        print(f"   ❌ 无法查看状态: {e}")


def main():
    """主程序"""
    print("\n" + "=" * 80)
    print("🚀 Silicon Valley Alpha Radar - GitHub 上传")
    print("=" * 80)
    print("\n📍 当前目录:")
    print(f"   {project_root}")

    # 步骤 1: 初始化 Git
    if not step_1_init_git():
        print("\n❌ Git 初始化失败，停止")
        return

    # 步骤 2: 添加文件
    if not step_2_add_files():
        print("\n❌ 添加文件失败，停止")
        return

    # 步骤 3: 创建提交
    if not step_3_create_commit():
        print("\n❌ 创建提交失败，停止")
        return

    # 步骤 4: 添加 remote
    print("\n" + "=" * 80)
    print("🔗 添加 GitHub remote")
    print("=" * 80)
    print("\n请提供 GitHub 仓库 URL:")
    print("   格式: https://github.com/yourusername/silicon-valley-alpha-radar")
    print("\n示例:")
    print("   https://github.com/zhipu-glm/silicon-valley-alpha-radar")

    github_url = input("\nGitHub 仓库 URL: ").strip()

    if not github_url:
        print("   ⚠️  未提供 GitHub URL，跳过 remote 和推送步骤")
        print("\n💡 提示:")
        print("   1. 创建 GitHub 仓库: https://github.com/new")
        print("   2. 然后运行: git remote add origin <GitHub 仓库 URL>")
        print("   3. 推送: git push -u origin main")
    else:
        if not step_4_add_remote(github_url):
            print("\n❌ 添加 remote 失败，停止")
            return

        # 步骤 5: 推送
        if step_5_push_to_github("main"):
            print("\n" + "=" * 80)
            print("✅ GitHub 上传完成！")
            print("=" * 80)
            print(f"\n🔗 GitHub 仓库: {github_url}")
            print(f"📊 分支: main")

            # 显示状态
            show_status()

            print(f"\n💡 下一步:")
            print(f"   1. 访问 GitHub 仓库: {github_url}")
            print(f"   2. 查看 README.md 了解项目")
            print(f"   3. 根据需要进行配置和数据收集")
            return

    # 显示最终状态
    print("\n" + "=" * 80)
    print("📋 Git 状态")
    print("=" * 80)
    show_status()

    print("\n" + "=" * 80)
    print("✅ Git 初始化完成")
    print("=" * 80)
    print("\n💡 下一步:")
    print("   1. 添加 GitHub remote:")
    print("      git remote add origin <GitHub 仓库 URL>")
    print("   2. 推送到 GitHub:")
    print("      git push -u origin main")


if __name__ == "__main__":
    main()
