#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试: Agent 自主编写脚本，将 test_organize 下的文件按类型分类
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent import LangChainAgent

API_KEY = "sk-ee03a518654647f09d2579009abbb4c2"

ORGANIZE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "sandbox_workspace", "test_organize"
)


def test_agent_organize_files():
    """Agent 自主编写脚本 + 执行，将文件按扩展名分类到子目录"""
    print("\n" + "=" * 60)
    print("📁 测试: Agent 自主编写分类脚本并执行")
    print("=" * 60)

    # 先展示当前文件状态
    print("\n📂 分类前的文件:")

    files = sorted(os.listdir(ORGANIZE_DIR))
    for f in files:
        print(f"  {f}")
    print(f"  共 {len(files)} 个文件")

    agent = LangChainAgent(api_key=API_KEY)

    task = (
        "在 sandbox_workspace/test_organize 目录下，有很多不同类型的文件混在一起。"
        "请帮我完成以下操作："
        "1. 先列出 test_organize 目录下的所有文件"
        "2. 编写一个 Shell 脚本 organize.sh，根据文件扩展名自动创建对应文件夹（如 txt/、pdf/、jpg/、py/、sh/、json/、csv/、md/、mp3/、pptx/），"
        "并将文件移动到对应的子目录中。脚本要放在 test_organize 目录内。"
        "3. 执行 organize.sh 脚本"
        "4. 验证分类结果，列出每个子目录的内容，确认所有文件都正确归类"
    )

    result = agent.execute(task)
    agent.print_result(result)

    # 手动验证
    print("\n🔍 手动验证分类结果:")
    all_ok = True
    subdirs = []
    remaining_files = []

    for item in sorted(os.listdir(ORGANIZE_DIR)):
        full = os.path.join(ORGANIZE_DIR, item)
        if os.path.isdir(full):
            subdirs.append(item)
            sub_files = os.listdir(full)
            print(f"  📁 {item}/ → {len(sub_files)} 个文件: {sub_files}")
        else:
            remaining_files.append(item)

    if remaining_files:
        print(f"  ⚠️ 根目录剩余文件: {remaining_files}")
        # organize.sh 本身留在根目录是可以接受的
        leftovers = [f for f in remaining_files if f != "organize.sh"]
        if leftovers:
            all_ok = False
            print(f"  ❌ 有未分类文件: {leftovers}")

    print(f"\n  共创建 {len(subdirs)} 个子目录")
    result_ok = result.get("success", False)
    print(f"  Agent 执行成功: {'✅' if result_ok else '❌'}")
    print(f"  分类结果正确: {'✅' if all_ok else '❌'}")

    return result_ok and all_ok


def main():
    print("\n" + "📁" * 30)
    print("  Agent 文件自动分类测试")
    print("📁" * 30)

    passed = test_agent_organize_files()

    print("\n" + "=" * 60)
    print(f"  {'✅ 通过' if passed else '❌ 失败'}: Agent 文件自动分类")
    print("=" * 60)
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
