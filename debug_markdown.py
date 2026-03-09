"""
调试脚本：保存 OpenAI 博客 markdown 并分析结构
"""

import os
import sys
import subprocess
import json
import re

# 添加项目根目录到 Python 路径
project_root = '/Users/zhipu_glm/.openclaw/workspace/silicon-valley-alpha-radar'
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'config'))

from data_sources_config import calculate_priority


def jina_read_save(url: str, output_file: str = "storage/data/debug_markdown.md"):
    """
    使用 jina 读取 URL 并保存到文件

    Args:
        url: 要读取的 URL
        output_file: 输出文件路径
    """
    try:
        print(f"📡 jina read: {url}")

        # 调用 jina
        result = subprocess.run(
            ['jina', url],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            print(f"❌ jina read 失败: {result.stderr}")
            return None

        # 保存到文件
        content = result.stdout

        os.makedirs(os.path.dirname(output_file), exist_ok=True)

        with open(output_file, 'w') as f:
            f.write(content)

        print(f"✅ 已保存 markdown 到 {output_file}")
        print(f"   文件大小: {len(content)} 字符")

        return content

    except Exception as e:
        print(f"❌ jina read 失败: {e}")
        return None


def analyze_markdown_structure(markdown_content: str):
    """
    分析 markdown 结构，查找链接模式

    Args:
        markdown_content: markdown 内容
    """
    print(f"\n🔍 分析 markdown 结构...")
    print(f"   内容长度: {len(markdown_content)} 字符")

    # 查找所有链接
    all_links = re.findall(r'https?://[^\s\)]+', markdown_content)
    print(f"   所有链接数量: {len(all_links)}")

    # 查找包含 "index/" 的链接
    index_links = [link for link in all_links if '/index/' in link]
    print(f"   包含 '/index/' 的链接数量: {len(index_links)}")

    if index_links:
        print(f"   示例 index 链接:")
        for link in index_links[:10]:
            print(f"      {link}")

    # 查找 markdown 链接格式：[text](url)
    md_links = re.findall(r'\[[^\]]+\]\([^)]+\)', markdown_content)
    print(f"   Markdown 链接数量: {len(md_links)}")

    if md_links:
        print(f"   示例 Markdown 链接:")
        for link in md_links[:10]:
            print(f"      {link}")

    # 查找列表项格式：* [text](url)
    list_links = re.findall(r'\*\s*\[([^\]]+)\]\([^)]+\)', markdown_content)
    print(f"   列表项链接数量: {len(list_links)}")

    if list_links:
        print(f"   示例列表项链接:")
        for link in list_links[:10]:
            print(f"      {link}")

    return {
        'total_links': len(all_links),
        'index_links': index_links,
        'md_links': md_links,
        'list_links': list_links
    }


def main():
    """主程序"""
    print("\n" + "=" * 80)
    print("🧪 Silicon Valley Alpha Radar - 调试 markdown 结构")
    print("=" * 80)

    # 1. 读取 OpenAI 博客
    print("\n📡 步骤 1/3: 读取 OpenAI 博客...")
    markdown_content = jina_read_save("https://openai.com/blog")

    if not markdown_content:
        print("❌ 读取失败")
        return

    # 2. 分析结构
    print("\n🔍 步骤 2/3: 分析 markdown 结构...")
    structure = analyze_markdown_structure(markdown_content)

    # 3. 输出建议
    print("\n💡 步骤 3/3: 建议的提取方案...")

    if structure['list_links']:
        print("   发现列表项格式：* [text](url)")
        print("   建议的正则：r'\\*\\s*\\[([^\\]]+)\\]\\([^)]+\\)'")
        print("   或者：r'\\*\\s*\\[([^\\]]+)\\]\\(https://[^\\)]+\\)'")
    elif structure['md_links']:
        print("   发现 markdown 链接格式：[text](url)")
        print("   建议的正则：r'\\[([^\\]]+)\\]\\([^)]+\\)'")
    elif structure['index_links']:
        print("   发现 index 链接")
        print("   建议的正则：r'https?://[^\\s\\)]+/index/'")
    else:
        print("   ⚠️  没有发现明显的链接模式")

    # 4. 显示摘要
    print("\n📋 结构摘要:")
    print(f"   总链接数: {structure['total_links']}")
    print(f"   Index 链接: {len(structure['index_links'])}")
    print(f"   Markdown 链接: {len(structure['md_links'])}")
    print(f"   列表项链接: {len(structure['list_links'])}")

    print("\n" + "=" * 80)
    print("✅ 调试完成")
    print("=" * 80)
    print(f"\n📁 已保存: storage/data/debug_markdown.md")
    print(f"\n💡 下一步:")
    print(f"   1. 手动查看 markdown 文件结构")
    print(f"   2. 根据实际格式修改提取逻辑")
    print(f"   3. 重新运行收集脚本")


if __name__ == "__main__":
    main()
