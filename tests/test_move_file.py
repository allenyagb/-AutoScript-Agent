#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全流程测试2: 移动文件
流程: 自然语言任务 → LLM生成脚本 → 安全检查 → 执行 → 结果验证
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent import AutoScriptAgent

# API 配置
API_KEY = "sk-ee03a518654647f09d2579009abbb4c2"


def test_full_move_file():
    """全流程测试: 自然语言 → 创建并移动文件"""
    print("\n" + "=" * 60)
    print("📦 全流程测试1: 创建并移动文件")
    print("=" * 60)

    task = "在沙箱工作区执行以下操作：" \
           "1. 创建一个 source.txt 文件，内容为'这是要移动的源文件内容'" \
           "2. 创建一个名为 backup 的目录" \
           "3. 将 source.txt 移动到 backup 目录下，改名为 backed_up.txt" \
           "4. 验证移动操作：确认 backup/backed_up.txt 存在且内容正确，同时 source.txt 已不存在"

    print(f"📋 用户任务: {task}")

    agent = AutoScriptAgent(api_key=API_KEY)
    result = agent.execute_task(task)
    agent.print_result(result)

    # 手动验证
    source_file = os.path.join(agent.workspace_dir, "source.txt")
    target_file = os.path.join(agent.workspace_dir, "backup", "backed_up.txt")

    checks = []
    if os.path.exists(target_file):
        with open(target_file, 'r') as f:
            content = f.read()
        if "这是要移动的源文件内容" in content:
            checks.append(f"✅ 目标文件存在且内容正确: {target_file}")
        else:
            checks.append(f"⚠️ 目标文件存在但内容不匹配")
    else:
        checks.append(f"❌ 目标文件不存在: {target_file}")

    if not os.path.exists(source_file):
        checks.append(f"✅ 源文件已不存在 (确认是移动而非复制)")
    else:
        checks.append(f"❌ 源文件仍然存在: {source_file}")

    print("\n🔍 手动验证:")
    for c in checks:
        print(f"  {c}")

    return all("✅" in c for c in checks)


def test_full_rename_file():
    """全流程测试: 自然语言 → 创建并重命名文件"""
    print("\n" + "=" * 60)
    print("📦 全流程测试2: 创建并重命名文件")
    print("=" * 60)

    task = "在沙箱工作区执行以下操作：" \
           "1. 创建一个名为 draft_notes.txt 的文件，内容写'这些是草稿笔记'" \
           "2. 将该文件重命名为 final_notes.txt" \
           "3. 验证重命名操作：确认 final_notes.txt 存在，draft_notes.txt 不存在"

    print(f"📋 用户任务: {task}")

    agent = AutoScriptAgent(api_key=API_KEY)
    result = agent.execute_task(task)
    agent.print_result(result)

    # 手动验证
    old_file = os.path.join(agent.workspace_dir, "draft_notes.txt")
    new_file = os.path.join(agent.workspace_dir, "final_notes.txt")

    checks = []
    if os.path.exists(new_file):
        checks.append(f"✅ 新文件名存在: {new_file}")
    else:
        checks.append(f"❌ 新文件名不存在: {new_file}")

    if not os.path.exists(old_file):
        checks.append(f"✅ 旧文件名已不存在")
    else:
        checks.append(f"❌ 旧文件名仍然存在: {old_file}")

    print("\n🔍 手动验证:")
    for c in checks:
        print(f"  {c}")

    return all("✅" in c for c in checks)


def main():
    """运行所有移动文件测试"""
    print("\n" + "📦" * 30)
    print("    AutoScript Agent - 全流程移动文件测试")
    print("📦" * 30)
    print("💡 测试流程: 自然语言任务 → LLM生成脚本 → 安全检查 → 执行 → 验证")

    results = []
    results.append(("全流程-创建并移动文件", test_full_move_file()))
    results.append(("全流程-创建并重命名文件", test_full_rename_file()))

    # 汇总
    print("\n" + "=" * 60)
    print("📊 测试结果汇总")
    print("=" * 60)
    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"  {status}: {name}")

    total = len(results)
    passed_count = sum(1 for _, p in results if p)
    print(f"\n总计: {passed_count}/{total} 通过")
    print("=" * 60)

    return 0 if passed_count == total else 1


if __name__ == "__main__":
    sys.exit(main())
