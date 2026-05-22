#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LangChain 全流程测试3: 执行文件 / 系统命令
使用 LangChain Agent 自主调用工具完成任务
"""

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent import LangChainAgent, ScriptExecutor

API_KEY = "sk-ee03a518654647f09d2579009abbb4c2"


def test_agent_list_files():
    """Agent 自主列出文件"""
    print("\n" + "=" * 60)
    print("📂 测试1: Agent 自主列出工作区文件")
    print("=" * 60)

    # 先创建一些文件
    test_file = "/tmp/agent_test_prep.txt"
    try:
        os.remove(test_file)
    except Exception:
        pass

    agent = LangChainAgent(api_key=API_KEY)
    task = "先创建一个 test_agent.txt 文件，内容写'LangChain Agent Test'，然后列出当前工作区的所有文件"

    result = agent.execute(task)
    agent.print_result(result)

    return result["success"]


def test_agent_system_info():
    """Agent 自主获取系统信息"""
    print("\n" + "=" * 60)
    print("🖥  测试2: Agent 自主获取系统信息")
    print("=" * 60)

    agent = LangChainAgent(api_key=API_KEY)
    task = "显示当前系统的用户名、工作目录和日期时间"

    result = agent.execute(task)
    agent.print_result(result)

    return result["success"]


# ==================== 单元测试 ====================

def setup_test_files(workspace_dir: str) -> dict:
    files = {}
    for name, content in [
        ("unit_shell.sh", "#!/bin/bash\necho 'Shell test OK'\necho 'User: '$(whoami)"),
        ("unit_timeout.sh", "#!/bin/bash\necho 'sleeping...'\nsleep 30\necho 'done'"),
        ("unit_error.sh", "#!/bin/bash\nset -e\necho 'start'\nbad_command_xyz\necho 'not reached'"),
    ]:
        path = os.path.join(workspace_dir, name)
        with open(path, 'w') as f:
            f.write(content)
        os.chmod(path, 0o755)
        files[name.split(".")[0]] = path
    return files


def test_executor_shell(executor, files):
    print("\n" + "=" * 60)
    print("▶️  单元测试3: 执行已有 Shell 脚本")
    print("=" * 60)
    result = executor.execute_file(files["unit_shell"])
    print(f"返回码: {result.return_code}, 输出: {result.stdout[:100]}...")
    return result.success


def test_executor_timeout(executor, files):
    print("\n" + "=" * 60)
    print("⏰ 单元测试4: 超时控制")
    print("=" * 60)
    start = time.time()
    result = executor.execute_file(files["unit_timeout"], timeout=3)
    elapsed = time.time() - start
    ok = not result.success and "超时" in (result.stderr + result.error_message)
    print(f"耗时: {elapsed:.1f}s, 超时捕获: {'✅' if ok else '❌'}")
    return ok


def test_executor_error(executor, files):
    print("\n" + "=" * 60)
    print("⚠️  单元测试5: 错误处理")
    print("=" * 60)
    result = executor.execute_file(files["unit_error"])
    ok = not result.success and result.return_code != 0
    print(f"返回码: {result.return_code}, 正确处理: {'✅' if ok else '❌'}")
    return ok


def test_not_found(executor):
    print("\n" + "=" * 60)
    print("❓ 单元测试6: 文件不存在")
    print("=" * 60)
    result = executor.execute_file("/tmp/nonexistent_xyz.sh")
    ok = not result.success and "不存在" in result.error_message
    print(f"错误: {result.error_message}, 处理: {'✅' if ok else '❌'}")
    return ok


def main():
    print("\n" + "▶️" * 30)
    print("    AutoScript Agent (LangChain) - 执行测试")
    print("▶️" * 30)

    executor = ScriptExecutor()
    files = setup_test_files(executor.workspace_dir)

    results = []
    results.append(("Agent列出文件", test_agent_list_files()))
    results.append(("Agent系统信息", test_agent_system_info()))
    results.append(("单元-执行Shell", test_executor_shell(executor, files)))
    results.append(("单元-超时控制", test_executor_timeout(executor, files)))
    results.append(("单元-错误处理", test_executor_error(executor, files)))
    results.append(("单元-文件不存在", test_not_found(executor)))

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
