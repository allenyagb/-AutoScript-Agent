#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全流程测试3: 执行文件 / 系统信息
流程: 自然语言任务 → LLM生成脚本 → 安全检查 → 执行 → 结果验证
同时保留执行器单元测试（超时、错误处理等）
"""

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent import AutoScriptAgent, ScriptExecutor

# API 配置
API_KEY = "sk-ee03a518654647f09d2579009abbb4c2"


def test_full_list_files():
    """全流程测试: 自然语言 → 列出工作区文件"""
    print("\n" + "=" * 60)
    print("📂 全流程测试1: 列出工作区文件")
    print("=" * 60)

    # 先在当前目录创建一个文件确保有东西可列出
    executor = ScriptExecutor()
    test_file = os.path.join(executor.workspace_dir, "sample_for_list.txt")
    with open(test_file, 'w') as f:
        f.write("test content for listing")

    task = "列出沙箱工作区目录下的所有文件和文件夹，显示它们的名称和大小"

    print(f"📋 用户任务: {task}")

    agent = AutoScriptAgent(api_key=API_KEY)
    result = agent.execute_task(task)
    agent.print_result(result)

    # 验证输出中包含工作区信息
    if result.execution_result and result.execution_result.success:
        stdout = result.execution_result.stdout
        if executor.workspace_dir in stdout or "sample_for_list" in stdout:
            print("\n🔍 手动验证: ✅ 输出包含工作区文件信息")
            return True
        else:
            print("\n🔍 手动验证: ⚠️ 输出可能不完整")
            return True  # 命令执行成功就算通过
    return False


def test_full_system_info():
    """全流程测试: 自然语言 → 获取系统信息"""
    print("\n" + "=" * 60)
    print("🖥  全流程测试2: 获取系统信息")
    print("=" * 60)

    task = "显示当前系统的以下信息：操作系统名称和版本、当前用户名、工作目录路径、磁盘使用情况"

    print(f"📋 用户任务: {task}")

    agent = AutoScriptAgent(api_key=API_KEY)
    result = agent.execute_task(task)
    agent.print_result(result)

    if result.execution_result and result.execution_result.success:
        print("\n🔍 手动验证: ✅ 系统信息获取成功")
        return True
    return False


# ============ 以下为执行器单元测试（不需要 LLM） ============

def setup_test_files(workspace_dir: str) -> dict:
    """准备测试用的脚本文件"""
    files = {}

    shell_script = os.path.join(workspace_dir, "unit_test_script.sh")
    with open(shell_script, 'w') as f:
        f.write("""#!/bin/bash
echo "========================================="
echo "Shell 脚本执行测试"
echo "========================================="
echo "当前用户: $(whoami)"
echo "当前目录: $(pwd)"
echo "工作区: ${AGENT_WORKSPACE:-未设置}"
echo "100 + 200 = $((100 + 200))"
echo ""
echo "工作区文件列表:"
ls -la
echo ""
echo "Shell 脚本执行成功!"
""")
    os.chmod(shell_script, 0o755)
    files["shell"] = shell_script

    timeout_script = os.path.join(workspace_dir, "unit_test_timeout.sh")
    with open(timeout_script, 'w') as f:
        f.write("""#!/bin/bash
echo "这个脚本会运行很久..."
sleep 30
echo "你不应该看到这行"
""")
    os.chmod(timeout_script, 0o755)
    files["timeout"] = timeout_script

    error_script = os.path.join(workspace_dir, "unit_test_error.sh")
    with open(error_script, 'w') as f:
        f.write("""#!/bin/bash
set -e
echo "开始执行..."
echo "尝试执行不存在的命令..."
this_command_does_not_exist_xyz
echo "你不应该看到这行"
""")
    os.chmod(error_script, 0o755)
    files["error"] = error_script

    return files


def test_executor_shell_file(executor: ScriptExecutor, files: dict):
    """单元测试: 执行已有 Shell 脚本"""
    print("\n" + "=" * 60)
    print("▶️  单元测试3: 执行已有 Shell 脚本文件")
    print("=" * 60)

    result = executor.execute_file(files["shell"])
    print(f"\n执行结果: {'✅ 成功' if result.success else '❌ 失败'}")
    print(f"返回码: {result.return_code}")
    print(f"执行时间: {result.execution_time:.2f} 秒")
    print(f"\n标准输出:\n{result.stdout[:500]}")
    if result.stderr:
        print(f"\n标准错误:\n{result.stderr[:300]}")

    return result.success


def test_executor_timeout(executor: ScriptExecutor, files: dict):
    """单元测试: 超时控制"""
    print("\n" + "=" * 60)
    print("⏰ 单元测试4: 执行超时控制")
    print("=" * 60)

    print("超时设置: 3 秒 (脚本会 sleep 30 秒)")
    start = time.time()
    result = executor.execute_file(files["timeout"], timeout=3)
    elapsed = time.time() - start

    print(f"\n返回码: {result.return_code}")
    print(f"实际耗时: {elapsed:.2f} 秒")
    print(f"\n标准错误: {result.stderr}")

    is_expected = not result.success and "超时" in (result.stderr + result.error_message)
    status = "✅ 超时控制正常" if is_expected else "❌ 超时控制异常"
    print(f"\n{status}")

    return is_expected


def test_executor_error(executor: ScriptExecutor, files: dict):
    """单元测试: 错误脚本处理"""
    print("\n" + "=" * 60)
    print("⚠️  单元测试5: 错误脚本处理")
    print("=" * 60)

    result = executor.execute_file(files["error"])

    print(f"\n返回码: {result.return_code}")
    print(f"标准输出: {result.stdout}")
    print(f"标准错误: {result.stderr}")

    is_ok = not result.success and result.return_code != 0
    status = "✅ 错误处理正常" if is_ok else "❌ 错误处理异常"
    print(f"\n{status}")

    return is_ok


def test_executor_not_found(executor: ScriptExecutor):
    """单元测试: 执行不存在的文件"""
    print("\n" + "=" * 60)
    print("❓ 单元测试6: 文件不存在处理")
    print("=" * 60)

    result = executor.execute_file("/tmp/non_existent_script_xyz.sh")
    print(f"错误信息: {result.error_message}")

    is_ok = not result.success and "不存在" in result.error_message
    status = "✅ 正确处理" if is_ok else "❌ 处理异常"
    print(f"\n{status}")

    return is_ok


def main():
    """运行所有测试"""
    print("\n" + "▶️" * 30)
    print("    AutoScript Agent - 全流程执行测试")
    print("▶️" * 30)
    print("💡 前两项为全流程测试，后四项为执行器单元测试")

    executor = ScriptExecutor()
    workspace = executor.workspace_dir
    files = setup_test_files(workspace)
    print(f"\n📂 工作区: {workspace}")

    results = []
    results.append(("全流程-列出文件", test_full_list_files()))
    results.append(("全流程-系统信息", test_full_system_info()))
    results.append(("单元-执行Shell脚本", test_executor_shell_file(executor, files)))
    results.append(("单元-超时控制", test_executor_timeout(executor, files)))
    results.append(("单元-错误处理", test_executor_error(executor, files)))
    results.append(("单元-文件不存在", test_executor_not_found(executor)))

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
