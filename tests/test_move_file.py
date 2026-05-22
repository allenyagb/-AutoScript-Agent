#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LangChain 全流程测试2: 移动文件
使用 LangChain Agent 自主调用工具完成任务
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent import LangChainAgent

API_KEY = "sk-ee03a518654647f09d2579009abbb4c2"


def test_move_file():
    """Agent 自主创建并移动文件"""
    print("\n" + "=" * 60)
    print("📦 测试1: Agent 自主创建并移动文件")
    print("=" * 60)

    agent = LangChainAgent(api_key=API_KEY)
    task = "在沙箱工作区执行以下操作：1. 创建一个 source.txt 文件，内容为'这是要移动的源文件内容' 2. 创建一个名为 backup 的目录 3. 将 source.txt 移动到 backup 目录下，改名为 backed_up.txt"

    result = agent.execute(task)
    agent.print_result(result)

    # 验证
    source = os.path.join(agent.workspace_dir, "source.txt")
    target = os.path.join(agent.workspace_dir, "backup", "backed_up.txt")
    checks = []
    if os.path.exists(target):
        checks.append(f"✅ 目标文件存在: {target}")
    else:
        checks.append(f"❌ 目标文件不存在")
    if not os.path.exists(source):
        checks.append(f"✅ 源文件已移除")
    else:
        checks.append(f"❌ 源文件仍存在")

    print("\n🔍 手动验证:")
    for c in checks:
        print(f"  {c}")
    return all("✅" in c for c in checks)


def test_rename_file():
    """Agent 自主重命名文件"""
    print("\n" + "=" * 60)
    print("📦 测试2: Agent 自主重命名文件")
    print("=" * 60)

    agent = LangChainAgent(api_key=API_KEY)
    task = "创建一个名为 draft.txt 的文件，内容写'这是草稿'，然后将它重命名为 final.txt"

    result = agent.execute(task)
    agent.print_result(result)

    old = os.path.join(agent.workspace_dir, "draft.txt")
    new = os.path.join(agent.workspace_dir, "final.txt")
    checks = []
    if os.path.exists(new):
        checks.append(f"✅ 新文件存在: {new}")
    else:
        checks.append(f"❌ 新文件不存在")
    if not os.path.exists(old):
        checks.append(f"✅ 旧文件已移除")
    else:
        checks.append(f"❌ 旧文件仍存在")

    print("\n🔍 手动验证:")
    for c in checks:
        print(f"  {c}")
    return all("✅" in c for c in checks)


def main():
    print("\n" + "📦" * 30)
    print("    AutoScript Agent (LangChain) - 移动文件测试")
    print("📦" * 30)

    results = []
    results.append(("Agent移动文件", test_move_file()))
    results.append(("Agent重命名文件", test_rename_file()))

    print("\n" + "=" * 60)
    print("📊 测试结果汇总")
    print("=" * 60)
    for name, passed in results:
        print(f"  {'✅ 通过' if passed else '❌ 失败'}: {name}")
    total = len(results)
    passed_count = sum(1 for _, p in results if p)
    print(f"\n总计: {passed_count}/{total} 通过")
    return 0 if passed_count == total else 1


if __name__ == "__main__":
    sys.exit(main())
