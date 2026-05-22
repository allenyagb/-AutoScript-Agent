#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AutoScript Agent 主控模块 (LangChain 版本)
使用 LangChain Agent + 工具调用完成自主任务执行
"""

import os
import sys
import time
from typing import Optional

from langchain.agents import create_agent
from langchain_core.messages import HumanMessage

from .chat_model import ChatQwen
from .tools import write_file, read_file, list_files, move_file, delete_file, execute_shell
from .safety_checker import SafetyChecker
from .script_executor import ScriptExecutor

# 注册所有工具
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

## 工作区
所有文件操作都在沙箱工作区中进行，路径相对于工作区根目录。
"""


class LangChainAgent:
    """基于 LangChain 的自主任务执行智能体"""

    def __init__(self, api_key: str = None, workspace_dir: str = None):
        """
        初始化 Agent

        Args:
            api_key: DashScope API Key
            workspace_dir: 工作区目录
        """
        self.api_key = api_key or "sk-ee03a518654647f09d2579009abbb4c2"
        self.workspace_dir = os.path.abspath(
            workspace_dir or os.path.join(os.path.dirname(os.path.dirname(__file__)), "sandbox_workspace")
        )
        os.makedirs(self.workspace_dir, exist_ok=True)

        # 创建 LangChain ChatModel 并绑定工具
        self.model = ChatQwen(api_key=self.api_key).bind_tools(ALL_TOOLS)

        # 创建 Agent
        self.agent = create_agent(
            model=self.model,
            tools=ALL_TOOLS,
            system_prompt=SYSTEM_PROMPT,
        )

        # 保留安全检查器和执行器供直接使用
        self.safety_checker = SafetyChecker(workspace_dir=self.workspace_dir)
        self.executor = ScriptExecutor(workspace_dir=self.workspace_dir)

    def execute(self, task: str) -> dict:
        """
        执行自然语言任务

        Args:
            task: 自然语言任务描述

        Returns:
            dict: 包含执行步骤和结果的字典
        """
        start_time = time.time()

        print(f"\n📋 任务: {task}")
        print("🤖 Agent 正在使用 LangChain 工具调用...")

        result = self.agent.invoke({"messages": [HumanMessage(content=task)]})

        elapsed = time.time() - start_time

        # 提取消息历史
        messages = result.get("messages", [])

        return {
            "success": True,
            "task": task,
            "messages": messages,
            "elapsed": elapsed,
            "final_answer": messages[-1].content if messages else "",
        }

    def print_result(self, result: dict):
        """打印任务执行结果"""
        print("\n" + "=" * 60)
        print("📊 LangChain Agent 执行报告")
        print("=" * 60)

        messages = result.get("messages", [])

        print("\n📋 执行步骤:")
        for i, msg in enumerate(messages):
            role = type(msg).__name__
            if role == "HumanMessage":
                print(f"  [{i}] 👤 用户: {msg.content[:100]}...")
            elif role == "AIMessage":
                if msg.tool_calls:
                    for tc in msg.tool_calls:
                        print(f"  [{i}] 🔧 调用工具: {tc['name']}({tc['args']})")
                elif msg.content:
                    print(f"  [{i}] 🤖 Agent: {msg.content[:200]}")
            elif role == "ToolMessage":
                print(f"  [{i}] 📤 工具返回: {msg.content[:150]}")

        print(f"\n⏱ 总耗时: {result['elapsed']:.2f} 秒")

        if result.get("final_answer"):
            print(f"\n📝 最终回复:\n{result['final_answer']}")

        print("=" * 60)


# 兼容旧接口
class AutoScriptAgent(LangChainAgent):
    """兼容旧接口的包装器"""
    def execute_task(self, task_description: str):
        """兼容旧的 execute_task 接口"""
        # 返回类似旧 TaskResult 的对象
        from dataclasses import dataclass, field
        from typing import List

        @dataclass
        class TaskResult:
            success: bool = False
            task_description: str = ""
            steps: List[str] = field(default_factory=list)
            total_time: float = 0.0
            error_message: str = ""

        result = self.execute(task_description)
        messages = result["messages"]

        tr = TaskResult(
            success=result["success"],
            task_description=task_description,
            total_time=result["elapsed"],
        )

        for msg in messages:
            role = type(msg).__name__
            if role == "AIMessage":
                if msg.tool_calls:
                    for tc in msg.tool_calls:
                        tr.steps.append(f"🔧 调用工具: {tc['name']}({tc['args']})")
                elif msg.content:
                    tr.steps.append(f"🤖 {msg.content[:200]}")
            elif role == "ToolMessage":
                tr.steps.append(f"📤 工具返回: {msg.content[:100]}")

        return tr

    def print_result(self, task_result):
        """兼容旧的 print_result 接口"""
        print("\n" + "=" * 60)
        print("📊 任务执行报告")
        print("=" * 60)
        print("\n📋 执行流程:")
        for step in task_result.steps:
            print(f"  {step}")
        print(f"\n⏱ 总耗时: {task_result.total_time:.2f} 秒")
        status = "✅ 成功" if task_result.success else "❌ 失败"
        print(f"{status}")
        print("=" * 60)


def run_interactive():
    """交互式运行 Agent"""
    print("\n" + "=" * 60)
    print("🤖 AutoScript Agent (LangChain) - 自主任务执行智能体")
    print("=" * 60)
    print("💡 使用提示:")
    print("  - 用自然语言描述你要执行的任务")
    print("  - 例如: '创建一个 hello.txt 文件，内容是Hello World'")
    print("  - 例如: '列出当前目录的所有文件'")
    print("  - 例如: '把 hello.txt 重命名为 world.txt'")
    print("  - 输入 'quit' 或 'exit' 退出")
    print("=" * 60)

    agent = LangChainAgent()
    print(f"✅ Agent 初始化成功 (LangChain + qwen3.7-max)")
    print(f"📂 工作区: {agent.workspace_dir}\n")

    while True:
        try:
            task = input("\n💬 请输入任务: ").strip()
            if not task:
                continue
            if task.lower() in ("quit", "exit", "q"):
                print("\n👋 再见！")
                break

            result = agent.execute(task)
            agent.print_result(result)

        except KeyboardInterrupt:
            print("\n\n👋 再见！")
            break
