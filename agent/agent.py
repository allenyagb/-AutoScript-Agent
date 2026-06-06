#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AutoScript Agent 主控模块 (LangChain 版本)
支持多轮对话记忆 + 错误自动重试（最多3次）+ 流式输出
"""

import os
import sys
import time
from typing import List, Optional

from langchain.agents import create_agent
from langchain_core.messages import HumanMessage, SystemMessage, BaseMessage, AIMessage
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult

from rich.live import Live
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.spinner import Spinner
from rich.layout import Layout
from rich import box

from .chat_model import ChatQwen
from .tools import write_file, read_file, list_files, move_file, delete_file, execute_shell
from .safety_checker import SafetyChecker
from .script_executor import ScriptExecutor
from .console import console, task_panel, dim, tool_style

ALL_TOOLS = [write_file, read_file, list_files, move_file, delete_file, execute_shell]

SYSTEM_PROMPT = """你是 Ubuntu 24.04 上的自主任务执行助手 AutoScript Agent。

## 你的能力
你可以使用以下工具完成文件操作和系统命令：
- write_file: 创建或覆盖文件
- read_file: 读取文件内容
- list_files: 列出工作区文件
- move_file: 移动或重命名文件
- delete_file: 删除工作区文件
- execute_shell: 执行安全的 Shell 命令

## 工作原则
1. 收到用户任务后，选择合适的工具逐步完成
2. 完成操作后，用 read_file 或 list_files 验证结果
3. 最后用中文向用户报告任务完成情况和结果
4. 如果遇到错误，说明原因并建议解决方案
5. 绝不尝试执行危险命令（sudo, rm -rf / 等）

## 对话规则
- 如果用户的指令不明确（如缺少参数、范围模糊），先提问澄清
- 记住之前的对话内容，用户可以用简称或代词指代之前的内容
- 例如：用户说"也删掉那个"，你要能根据上下文找到指代的目标

## 工作区
所有文件操作都在沙箱工作区中进行，路径相对于工作区根目录。
"""

MAX_RETRIES = 3


# ═══════════════════════════════════════════════════
#  Rich 流式回调处理器
# ═══════════════════════════════════════════════════

class StreamingCallback(BaseCallbackHandler):
    """LangChain 回调处理器 — 驱动 Rich Live 实时展示 Agent 执行过程"""

    def __init__(self):
        super().__init__()
        self._live: Optional[Live] = None
        self._output = Text("")
        self._tool_log: List[str] = []
        self._current_llm_text = ""
        self._thinking = True

    # ── LLM 回调 ──────────────────────────────────────

    def on_llm_start(
        self, serialized: dict, prompts: list, **kwargs
    ) -> None:
        """LLM 开始思考"""
        self._current_llm_text = ""
        self._thinking = True
        self._refresh()

    def on_llm_new_token(self, token: str, **kwargs) -> None:
        """收到新 token — 流式输出"""
        self._current_llm_text += token
        self._refresh()

    def on_llm_end(self, response: LLMResult, **kwargs) -> None:
        """LLM 思考结束"""
        self._thinking = False
        self._refresh()

    # ── 工具回调 ──────────────────────────────────────

    def on_tool_start(
        self, serialized: dict, input_str: str, **kwargs
    ) -> None:
        """工具开始执行"""
        name = serialized.get("name", "unknown")
        try:
            import json
            args = json.loads(input_str)
        except Exception:
            args = input_str
        self._tool_log.append(f"[tool]🔧 {name}[/tool] {dim(str(args)[:100])}")
        self._refresh()

    def on_tool_end(self, output: str, **kwargs) -> None:
        """工具执行结束"""
        out_short = output[:120].replace("\n", " ")
        self._tool_log.append(f"  [tool_out]↳ {out_short}[/tool_out]")
        self._refresh()

    def on_tool_error(self, error, **kwargs) -> None:
        """工具执行出错"""
        self._tool_log.append(f"  [error]✗ {str(error)[:120]}[/error]")
        self._refresh()

    # ── Agent 回调 ─────────────────────────────────────

    def on_agent_action(self, action, **kwargs) -> None:
        """Agent 决策执行某个工具"""
        pass  # on_tool_start 已处理

    def on_agent_finish(self, finish, **kwargs) -> None:
        """Agent 完成"""
        self._thinking = False
        self._refresh()

    # ── 渲染 ───────────────────────────────────────────

    def _build_renderable(self):
        """构建 Rich renderable"""
        from rich.console import Group

        parts = []

        # 思考中状态
        if self._thinking:
            parts.append(Spinner("dots", text=" [dim]正在思考...[/dim]"))

        # LLM 当前输出
        if self._current_llm_text:
            parts.append(Text(self._current_llm_text, style="agent"))

        # 工具调用日志
        if self._tool_log:
            if self._current_llm_text:
                parts.append(Text(""))  # 空行分隔
            for log_line in self._tool_log[-12:]:  # 最多显示 12 行
                parts.append(Text.from_markup(log_line))

        if not parts:
            parts.append(Text("⏳ 等待响应...", style="dim"))

        # 单个 renderable 直接传入，多个用 Group 组合
        content = parts[0] if len(parts) == 1 else Group(*parts)

        return Panel(
            content,
            title="🤖 Agent 执行中",
            border_style="agent",
            box=box.ROUNDED,
            padding=(0, 1),
        )

    def _refresh(self):
        """刷新 Live 显示"""
        if self._live:
            self._live.update(self._build_renderable())

    def attach(self, live: Live):
        """绑定 Rich Live 实例"""
        self._live = live
        live.update(self._build_renderable())

    def final_output(self) -> str:
        """返回 LLM 最终文本"""
        return self._current_llm_text


# ═══════════════════════════════════════════════════
#  LangChain Agent
# ═══════════════════════════════════════════════════

class LangChainAgent:
    """基于 LangChain 的自主任务执行智能体
    支持多轮对话记忆 + 错误自动重试 + Rich 流式输出
    """

    def __init__(self, api_key: str = None, workspace_dir: str = None):
        self.api_key = api_key or "sk-ee03a518654647f09d2579009abbb4c2"
        self.workspace_dir = os.path.abspath(
            workspace_dir
            or os.path.join(os.path.dirname(os.path.dirname(__file__)), "sandbox_workspace")
        )
        os.makedirs(self.workspace_dir, exist_ok=True)

        self.model = ChatQwen(api_key=self.api_key).bind_tools(ALL_TOOLS)
        self.agent = create_agent(
            model=self.model, tools=ALL_TOOLS, system_prompt=SYSTEM_PROMPT
        )

        self.safety_checker = SafetyChecker(workspace_dir=self.workspace_dir)
        self.executor = ScriptExecutor(workspace_dir=self.workspace_dir)

        # ── 多轮对话核心：持久化消息列表 ──
        self._conversation_history: List[BaseMessage] = [
            SystemMessage(content=SYSTEM_PROMPT)
        ]

    # ═══════════════════════════════════════════════════
    #  多轮对话记忆
    # ═══════════════════════════════════════════════════

    def execute(self, task: str) -> dict:
        """
        执行自然语言任务（带对话记忆 + Rich 流式展示）

        Args:
            task: 自然语言任务描述

        Returns:
            dict: {success, task, messages, elapsed, final_answer, retries}
        """
        start_time = time.time()

        console.print()  # 空行
        console.print(task_panel(task))
        console.print(
            f"[dim]💬 对话轮次: {self._count_user_turns() + 1}[/dim]"
        )

        # 追加用户消息到历史
        self._conversation_history.append(HumanMessage(content=task))

        # ── 错误重试循环 ──
        retries = 0
        last_error = ""

        while retries <= MAX_RETRIES:
            try:
                # 创建回调处理器
                callback = StreamingCallback()

                # 使用 Rich Live 包裹整个 Agent 调用
                with Live(
                    callback._build_renderable(),
                    console=console,
                    refresh_per_second=8,
                    transient=False,
                    vertical_overflow="visible",
                ) as live:
                    callback.attach(live)

                    result = self.agent.invoke(
                        {"messages": list(self._conversation_history)},
                        config={"callbacks": [callback]},
                    )

                break  # 成功，跳出重试循环

            except Exception as e:
                retries += 1
                last_error = str(e)

                if retries > MAX_RETRIES:
                    elapsed = time.time() - start_time
                    console.print(
                        Panel(
                            f"重试 {MAX_RETRIES} 次后仍失败: {last_error}",
                            title="❌ 任务失败",
                            border_style="error",
                        )
                    )
                    return {
                        "success": False,
                        "task": task,
                        "messages": list(self._conversation_history),
                        "elapsed": elapsed,
                        "final_answer": f"❌ 重试{MAX_RETRIES}次后仍失败: {last_error}",
                        "retries": retries,
                    }

                console.print(
                    f"  [warning]⚠️ 第 {retries}/{MAX_RETRIES} 次重试...[/warning] "
                    f"[dim](错误: {last_error[:100]})[/dim]"
                )
                # 将错误信息注入对话，让 LLM 自我修正
                self._conversation_history.append(
                    HumanMessage(content=f"上次执行出错: {last_error}\n请修正后重试。")
                )

        # ── 更新历史 ──
        self._conversation_history = list(result.get("messages", []))

        elapsed = time.time() - start_time
        messages = result.get("messages", [])

        return {
            "success": True,
            "task": task,
            "messages": messages,
            "elapsed": elapsed,
            "final_answer": messages[-1].content if messages else "",
            "retries": retries,
        }

    def clear_history(self):
        """清空对话历史（保留系统提示）"""
        self._conversation_history = [SystemMessage(content=SYSTEM_PROMPT)]
        console.print("[info]🧹 对话历史已清空[/info]")

    def get_history_summary(self) -> str:
        """获取对话历史摘要"""
        user_turns = self._count_user_turns()
        tool_calls = self._count_tool_calls()
        return f"💬 {user_turns} 轮对话, 🔧 {tool_calls} 次工具调用"

    def _count_user_turns(self) -> int:
        return sum(
            1 for m in self._conversation_history if isinstance(m, HumanMessage)
        )

    def _count_tool_calls(self) -> int:
        return sum(
            len(msg.tool_calls)
            for msg in self._conversation_history
            if hasattr(msg, "tool_calls") and msg.tool_calls
        )

    # ═══════════════════════════════════════════════════
    #  结果输出 （Rich 格式化）
    # ═══════════════════════════════════════════════════

    def print_result(self, result: dict):
        """以 Rich 格式打印任务执行报告"""
        messages = result.get("messages", [])
        retries = result.get("retries", 0)

        # ── 步骤表格 ──
        table = Table(
            title="📊 LangChain Agent 执行报告",
            title_style="heading bold",
            border_style="dim",
            box=box.ROUNDED,
            show_header=True,
            header_style="title bold",
            expand=True,
        )
        table.add_column("#", style="dim", width=4)
        table.add_column("角色", width=6)
        table.add_column("详情")

        for i, msg in enumerate(messages):
            role = type(msg).__name__
            if role == "SystemMessage":
                continue
            elif role == "HumanMessage":
                content = msg.content[:80]
                if len(msg.content) > 80:
                    content += "…"
                table.add_row(str(i), "👤 用户", content)
            elif role == "AIMessage":
                if msg.tool_calls:
                    for tc in msg.tool_calls:
                        args_str = str(tc.get("args", ""))[:100]
                        table.add_row(
                            str(i),
                            "🔧 工具",
                            f"[tool]{tc.get('name', '?')}[/tool]({args_str})",
                        )
                if msg.content:
                    table.add_row(
                        str(i),
                        "🤖 Agent",
                        msg.content[:300],
                    )
            elif role == "ToolMessage":
                table.add_row(
                    str(i),
                    "📤 返回",
                    f"[tool_out]{msg.content[:200]}[/tool_out]",
                )

        console.print(table)

        # ── 摘要行 ──
        summary_parts = [f"⏱ 总耗时: [time]{result['elapsed']:.2f}[/time] 秒"]
        if retries > 0:
            summary_parts.append(f"🔄 重试: [warning]{retries}[/warning] 次")
        console.print("  " + " | ".join(summary_parts))

        # ── 最终回复 ──
        if result.get("final_answer"):
            console.print()
            console.print(
                Panel(
                    Text(result["final_answer"]),
                    title="📝 最终回复",
                    border_style="agent",
                    box=box.ROUNDED,
                )
            )

        console.print()  # 尾空行


# ═══════════════════════════════════════════════════
#  兼容旧接口
# ═══════════════════════════════════════════════════

class AutoScriptAgent(LangChainAgent):
    """兼容旧接口"""

    def execute_task(self, task_description: str):
        from dataclasses import dataclass, field
        from typing import List as _List

        @dataclass
        class TaskResult:
            success: bool = False
            task_description: str = ""
            steps: _List[str] = field(default_factory=list)
            total_time: float = 0.0
            error_message: str = ""
            retries: int = 0

        result = self.execute(task_description)
        messages = result["messages"]
        tr = TaskResult(
            success=result["success"],
            task_description=task_description,
            total_time=result["elapsed"],
            retries=result.get("retries", 0),
        )
        for msg in messages:
            role = type(msg).__name__
            if role == "AIMessage":
                if msg.tool_calls:
                    for tc in msg.tool_calls:
                        tr.steps.append(f"🔧 调用: {tc['name']}({tc['args']})")
                elif msg.content:
                    tr.steps.append(f"🤖 {msg.content[:200]}")
            elif role == "ToolMessage":
                tr.steps.append(f"📤 {msg.content[:100]}")
        return tr

    def print_result(self, task_result):
        console.print()
        status = "✅ 成功" if task_result.success else "❌ 失败"
        console.print(
            Panel(
                Text("\n".join(task_result.steps) or "(无步骤)"),
                title=f"📊 任务执行报告 — {status}",
                border_style="success" if task_result.success else "error",
                box=box.ROUNDED,
            )
        )
        console.print(f"  ⏱ 总耗时: [time]{task_result.total_time:.2f}[/time] 秒")
        if task_result.retries > 0:
            console.print(f"  🔄 重试: [warning]{task_result.retries}[/warning] 次")


# ═══════════════════════════════════════════════════
#  交互式运行（多轮对话）
# ═══════════════════════════════════════════════════

def run_interactive():
    """交互式运行 Agent（支持多轮对话）—— Rich 风格"""
    console.print()
    console.print(
        Panel(
            Text.from_markup(
                "[bold]🤖 AutoScript Agent (LangChain) — 多轮对话版[/bold]\n\n"
                "[dim]💡 使用提示:[/dim]\n"
                "  • 用自然语言描述任务，Agent 会自动执行\n"
                "  • Agent 会记住之前的对话，可以用代词指代\n"
                "  • 输入 [info]history[/info] 查看对话统计\n"
                "  • 输入 [info]clear[/info] 清空对话历史\n"
                "  • 输入 [info]quit[/info] / [info]exit[/info] 退出"
            ),
            title="🚀 欢迎",
            border_style="agent",
            box=box.HEAVY,
            padding=(1, 2),
        )
    )

    agent = LangChainAgent()
    console.print(f"[success]✅ Agent 初始化成功[/success] (LangChain + qwen3.7-max)")
    console.print(f"[dim]📂 工作区: {agent.workspace_dir}[/dim]")
    console.print()

    while True:
        try:
            task = console.input("[user]💬 你:[/user] ").strip()
            if not task:
                continue
            if task.lower() in ("quit", "exit", "q"):
                console.print("\n[agent]👋 再见！[/agent]")
                break
            if task.lower() == "history":
                console.print(f"\n[dim]{agent.get_history_summary()}[/dim]")
                continue
            if task.lower() == "clear":
                agent.clear_history()
                continue

            result = agent.execute(task)
            agent.print_result(result)

        except KeyboardInterrupt:
            console.print("\n\n[agent]👋 再见！[/agent]")
            break
