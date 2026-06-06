#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AutoScript Agent 交互式命令行
用法: python3 agent_cli.py

Rich 流式输出版本 — 美观、实时、现代化终端体验
"""

import sys
import os

# 确保项目根目录在 sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent import LangChainAgent
from agent.console import console, dim, user_style

from rich.panel import Panel
from rich.text import Text
from rich import box


BANNER = Panel(
    Text.from_markup(
        "[bold]🤖 AutoScript Agent 交互终端[/bold]\n\n"
        "[dim]自然语言驱动 · 自主执行 · 多轮对话[/dim]\n\n"
        "[dim]特殊命令:[/dim]\n"
        "  [info]/clear[/info]   清空对话历史\n"
        "  [info]/history[/info] 查看对话摘要\n"
        "  [info]/exit[/info]    退出\n\n"
        "[dim]可用工具:[/dim] [tool]write_file[/tool] | [tool]read_file[/tool] | "
        "[tool]list_files[/tool] | [tool]move_file[/tool] | "
        "[tool]delete_file[/tool] | [tool]execute_shell[/tool]"
    ),
    title="🏠 主菜单",
    border_style="agent",
    box=box.HEAVY,
    padding=(1, 2),
)


def main():
    console.print(BANNER)

    agent = LangChainAgent()
    console.print(f"[success]✅ Agent 已就绪[/success] [dim](LangChain + qwen3.7-max)[/dim]")
    console.print(f"[dim]📂 工作区: {agent.workspace_dir}[/dim]")

    while True:
        try:
            user_input = console.input("\n[user]🧑 你:[/user] ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[agent]👋 再见！[/agent]")
            break

        if not user_input:
            continue

        # 特殊命令
        if user_input == "/exit":
            console.print("[agent]👋 再见！[/agent]")
            break
        elif user_input == "/clear":
            agent.clear_history()
            continue
        elif user_input == "/history":
            console.print(f"[dim]{agent.get_history_summary()}[/dim]")
            continue
        elif user_input == "/help":
            console.print(BANNER)
            continue

        # 执行任务
        result = agent.execute(user_input)

        # 显示结果摘要
        console.print()
        if result["success"]:
            console.print(
                Panel(
                    Text(result["final_answer"]),
                    title=f"✅ 任务完成 (耗时 {result['elapsed']:.1f}s, 重试 {result['retries']} 次)",
                    border_style="success",
                    box=box.ROUNDED,
                )
            )
        else:
            console.print(
                Panel(
                    Text(result["final_answer"]),
                    title=f"❌ 任务失败 (重试 {result['retries']} 次)",
                    border_style="error",
                    box=box.ROUNDED,
                )
            )


if __name__ == "__main__":
    main()
