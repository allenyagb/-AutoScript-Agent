#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AutoScript Agent 主控模块 (LangChain 版本)
支持多轮对话记忆 + 错误自动重试（最多3次）
"""

import os
import sys
import time
from typing import List, Optional

from langchain.agents import create_agent
from langchain_core.messages import HumanMessage, SystemMessage, BaseMessage

from .chat_model import ChatQwen
from .tools import write_file, read_file, list_files, move_file, delete_file, execute_shell
from .safety_checker import SafetyChecker
from .script_executor import ScriptExecutor

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


class LangChainAgent:
    """基于 LangChain 的自主任务执行智能体
    支持多轮对话记忆 + 错误自动重试
    """

    def __init__(self, api_key: str = None, workspace_dir: str = None):
        self.api_key = api_key or "sk-ee03a518654647f09d2579009abbb4c2"
        self.workspace_dir = os.path.abspath(
            workspace_dir or os.path.join(os.path.dirname(os.path.dirname(__file__)), "sandbox_workspace")
        )
        os.makedirs(self.workspace_dir, exist_ok=True)

        self.model = ChatQwen(api_key=self.api_key).bind_tools(ALL_TOOLS)
        self.agent = create_agent(model=self.model, tools=ALL_TOOLS, system_prompt=SYSTEM_PROMPT)

        self.safety_checker = SafetyChecker(workspace_dir=self.workspace_dir)
        self.executor = ScriptExecutor(workspace_dir=self.workspace_dir)

        # ── 多轮对话核心：持久化消息列表 ──
        self._conversation_history: List[BaseMessage] = [SystemMessage(content=SYSTEM_PROMPT)]

    # ═══════════════════════════════════════════════════
    #  多轮对话记忆
    # ═══════════════════════════════════════════════════

    def execute(self, task: str) -> dict:
        """
        执行自然语言任务（带对话记忆）

        Args:
            task: 自然语言任务描述

        Returns:
            dict: {success, task, messages, elapsed, final_answer, retries}
        """
        start_time = time.time()

        print(f"\n📋 任务: {task}")
        print(f"💬 对话轮次: {self._count_user_turns() + 1}")
        print("🤖 Agent 正在使用 LangChain 工具调用...")

        # 追加用户消息到历史
        self._conversation_history.append(HumanMessage(content=task))

        # ── 错误重试循环 ──
        retries = 0
        last_error = ""
        backoff_base = 2  # 退避基数（秒）

        while retries <= MAX_RETRIES:
            try:
                result = self.agent.invoke({"messages": list(self._conversation_history)})
                break  # 成功，跳出重试循环

            except Exception as e:
                retries += 1
                last_error = str(e)

                if retries > MAX_RETRIES:
                    elapsed = time.time() - start_time
                    return {
                        "success": False, "task": task,
                        "messages": list(self._conversation_history),
                        "elapsed": elapsed, "final_answer": f"❌ 重试{MAX_RETRIES}次后仍失败: {last_error}",
                        "retries": retries,
                    }

                # 区分超时/网络错误 vs 逻辑错误
                is_transient = any(kw in last_error.lower() for kw in
                                   ("timeout", "timed out", "connection", "network",
                                    "unreachable", "dns", "reset", "refused"))

                if is_transient:
                    # 基础设施错误：退避等待后重试，不污染对话历史
                    wait = min(backoff_base ** retries, 30)
                    print(f"  ⚠️ 第 {retries}/{MAX_RETRIES} 次重试 (退避 {wait}s)... "
                          f"(错误: {last_error[:80]})")
                    time.sleep(wait)
                else:
                    # 逻辑/代码错误：注入对话历史让 LLM 自我修正
                    print(f"  ⚠️ 第 {retries}/{MAX_RETRIES} 次重试... (错误: {last_error[:100]})")
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
        print("🧹 对话历史已清空")

    def get_history_summary(self) -> str:
        """获取对话历史摘要"""
        user_turns = self._count_user_turns()
        tool_calls = self._count_tool_calls()
        return f"💬 {user_turns} 轮对话, 🔧 {tool_calls} 次工具调用"

    def _count_user_turns(self) -> int:
        return sum(1 for m in self._conversation_history if isinstance(m, HumanMessage))

    def _count_tool_calls(self) -> int:
        return sum(
            len(msg.tool_calls)
            for msg in self._conversation_history
            if hasattr(msg, "tool_calls") and msg.tool_calls
        )

    # ═══════════════════════════════════════════════════
    #  结果输出
    # ═══════════════════════════════════════════════════

    def _extract_script_outputs(self, messages: list) -> list[dict]:
        """
        从消息历史中提取脚本/命令执行的输出结果

        Returns:
            [{label, content, is_error}, ...]
        """
        from langchain_core.messages import ToolMessage

        outputs = []
        for msg in messages:
            if not isinstance(msg, ToolMessage):
                continue
            content = (msg.content or "").strip()
            if not content:
                continue

            is_error = False
            label = "工具返回"

            # 根据内容前缀识别工具类型
            if "命令执行成功:" in content or "命令执行失败" in content or "命令被安全策略拒绝" in content:
                label = "命令输出"
                is_error = "失败" in content or "拒绝" in content
            elif content.startswith("✅ 文件写入成功"):
                label = "文件写入"
            elif content.startswith("📄"):
                label = "文件内容"
            elif content.startswith("📂"):
                label = "文件列表"
            elif content.startswith("✅ 文件移动"):
                label = "文件移动"
            elif content.startswith("✅ 文件已删除"):
                label = "文件删除"
            elif content.startswith("❌") or content.startswith("⛔"):
                is_error = True

            outputs.append({
                "label": label,
                "content": content,
                "is_error": is_error,
            })
        return outputs

    def print_result(self, result: dict):
        """打印任务执行结果"""
        print("\n" + "=" * 60)
        print("📊 LangChain Agent 执行报告")
        print("=" * 60)

        messages = result.get("messages", [])
        retries = result.get("retries", 0)

        print("\n📋 执行步骤:")
        for i, msg in enumerate(messages):
            role = type(msg).__name__
            if role == "SystemMessage":
                continue  # 不打印系统提示
            elif role == "HumanMessage":
                content = msg.content[:80]
                if len(msg.content) > 80:
                    content += "..."
                print(f"  [{i}] 👤 用户: {content}")
            elif role == "AIMessage":
                if msg.tool_calls:
                    for tc in msg.tool_calls:
                        print(f"  [{i}] 🔧 调用工具: {tc['name']}({tc['args']})")
                if msg.content:
                    print(f"  [{i}] 🤖 Agent: {msg.content[:200]}")
            elif role == "ToolMessage":
                content = msg.content
                # 对 shell 执行结果展示完整输出
                if "命令执行" in content:
                    print(f"  [{i}] 📤 脚本输出:")
                    print("  " + "-" * 40)
                    for line in content.split("\n"):
                        print(f"  │ {line}")
                    print("  " + "-" * 40)
                else:
                    print(f"  [{i}] 📤 工具返回: {content[:150]}")

        print(f"\n⏱ 总耗时: {result['elapsed']:.2f} 秒")
        if retries > 0:
            print(f"🔄 重试次数: {retries}")

        # ── 展示脚本 / 命令的实际输出 ──
        script_outputs = self._extract_script_outputs(messages)
        if script_outputs:
            print(f"\n{'─' * 60}")
            print("📟 终端输出 (脚本/命令执行结果)")
            print(f"{'─' * 60}")
            for out in script_outputs:
                prefix = "❌ [错误]" if out["is_error"] else "✅ [成功]"
                print(f"\n{prefix}:")
                for line in out["content"].split("\n"):
                    print(f"  {line}")
            print(f"{'─' * 60}")

        if result.get("final_answer"):
            print(f"\n📝 最终回复:\n{result['final_answer']}")

        print("=" * 60)


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
        print("\n" + "=" * 60)
        print("📊 任务执行报告")
        print("=" * 60)
        print(f"\n📋 执行流程:")
        for step in task_result.steps:
            print(f"  {step}")
        print(f"\n⏱ 总耗时: {task_result.total_time:.2f} 秒")
        if task_result.retries > 0:
            print(f"🔄 重试: {task_result.retries} 次")
        print(f"{'✅ 成功' if task_result.success else '❌ 失败'}")
        print("=" * 60)


# ═══════════════════════════════════════════════════
#  交互式运行（多轮对话）
# ═══════════════════════════════════════════════════

def run_interactive():
    """交互式运行 Agent（支持多轮对话）"""
    print("\n" + "=" * 60)
    print("🤖 AutoScript Agent (LangChain) - 多轮对话版")
    print("=" * 60)
    print("💡 使用提示:")
    print("  - 用自然语言描述任务，Agent 会自动执行")
    print("  - Agent 会记住之前的对话，可以用代词指代")
    print("  - 输入 'history' 查看对话统计")
    print("  - 输入 'clear' 清空对话历史")
    print("  - 输入 'quit' 或 'exit' 退出")
    print("=" * 60)

    agent = LangChainAgent()
    print(f"✅ Agent 初始化成功 (LangChain + qwen3.7-max)")
    print(f"📂 工作区: {agent.workspace_dir}\n")

    while True:
        try:
            task = input("\n💬 你: ").strip()
            if not task:
                continue
            if task.lower() in ("quit", "exit", "q"):
                print("\n👋 再见！")
                break
            if task.lower() == "history":
                print(f"\n{agent.get_history_summary()}")
                continue
            if task.lower() == "clear":
                agent.clear_history()
                continue

            result = agent.execute(task)
            agent.print_result(result)

        except KeyboardInterrupt:
            print("\n\n👋 再见！")
            break
