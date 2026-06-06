#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AutoScript Agent 交互式命令行
用法: python3 agent_cli.py
"""

import sys
import os

# 确保项目根目录在 sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent import LangChainAgent


BANNER = """
╔══════════════════════════════════════════════╗
║        🤖 AutoScript Agent 交互终端          ║
║      自然语言驱动 · 自主执行 · 多轮对话       ║
╚══════════════════════════════════════════════╝

  输入任务描述，Agent 会自主规划并执行。
  
  特殊命令:
    /clear   清空对话历史
    /history 查看对话摘要
    /exit    退出

  可用工具: write_file | read_file | list_files | move_file | delete_file | execute_shell
"""


def main():
    print(BANNER)

    agent = LangChainAgent()

    while True:
        try:
            user_input = input("\n🧑 你: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n👋 再见！")
            break

        if not user_input:
            continue

        # 特殊命令
        if user_input == "/exit":
            print("👋 再见！")
            break
        elif user_input == "/clear":
            agent.clear_history()
            continue
        elif user_input == "/history":
            print(agent.get_history_summary())
            continue
        elif user_input == "/help":
            print(BANNER)
            continue

        # 执行任务
        result = agent.execute(user_input)

        # ── 提取脚本/命令执行的实际输出 ──
        script_outputs = agent._extract_script_outputs(result.get("messages", []))

        # 显示结果
        print(f"\n{'='*50}")
        if result["success"]:
            print(f"✅ 任务完成 (耗时 {result['elapsed']:.1f}s, 重试 {result['retries']} 次)")
        else:
            print(f"❌ 任务失败 (重试 {result['retries']} 次)")
        print(f"{'='*50}")

        # ── 展示脚本 / 命令的实际终端输出 ──
        if script_outputs:
            print(f"\n{'─' * 50}")
            print("📟 终端输出 (脚本/命令执行结果)")
            print(f"{'─' * 50}")
            for out in script_outputs:
                prefix = "❌" if out["is_error"] else "✅"
                print(f"\n{prefix} [{out['label']}]:")
                for line in out["content"].split("\n"):
                    print(f"  {line}")
            print(f"{'─' * 50}")

        print(f"\n📝 Agent 回复:\n{result['final_answer']}")
        print(f"{'='*50}")


if __name__ == "__main__":
    main()
