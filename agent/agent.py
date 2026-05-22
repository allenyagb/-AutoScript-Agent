#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AutoScript Agent 主控模块 - 编排任务解析、生成、执行全流程
"""

import os
import sys
import time
from dataclasses import dataclass, field
from typing import List, Optional

from .script_generator import ScriptGenerator, GeneratedScript
from .script_executor import ScriptExecutor, ExecutionResult
from .safety_checker import SafetyChecker, SafetyReport


@dataclass
class TaskResult:
    """任务执行结果"""
    success: bool = False
    task_description: str = ""
    generated_script: Optional[GeneratedScript] = None
    safety_report: Optional[SafetyReport] = None
    execution_result: Optional[ExecutionResult] = None
    retry_count: int = 0
    max_retries: int = 3
    error_message: str = ""
    total_time: float = 0.0
    steps: List[str] = field(default_factory=list)


class AutoScriptAgent:
    """自主任务执行智能体

    核心流程：
    1. 解析用户自然语言任务
    2. 调用大模型生成脚本
    3. 安全性检查
    4. 执行脚本并返回结果
    5. 失败时自动重试（最多3次）
    """

    # 最大重试次数
    MAX_RETRIES = 3

    def __init__(self, api_key: str = None, workspace_dir: str = None,
                 use_sandbox: bool = False):
        """
        初始化智能体

        Args:
            api_key: DashScope API Key
            workspace_dir: 工作区目录
            use_sandbox: 是否使用沙箱
        """
        self.workspace_dir = os.path.abspath(
            workspace_dir or os.path.join(os.path.dirname(os.path.dirname(__file__)), "sandbox_workspace")
        )

        self.generator = ScriptGenerator(api_key=api_key)
        self.executor = ScriptExecutor(workspace_dir=self.workspace_dir, use_sandbox=use_sandbox)
        self.safety_checker = SafetyChecker(workspace_dir=self.workspace_dir)

    def execute_task(self, task_description: str) -> TaskResult:
        """
        执行自然语言描述的任务

        Args:
            task_description: 自然语言任务描述，如 "在 /tmp 下创建一个名为 hello.txt 的文件"

        Returns:
            TaskResult: 任务执行结果
        """
        start_time = time.time()
        result = TaskResult(task_description=task_description)
        result.steps.append(f"📋 收到任务: {task_description}")

        retry_count = 0
        last_error = ""

        while retry_count <= self.MAX_RETRIES:
            if retry_count > 0:
                result.steps.append(f"🔄 第 {retry_count} 次重试...")
                # 在重试时，把上次的错误信息加入任务描述
                enhanced_task = f"{task_description}\n\n【上次执行失败的错误信息】\n{last_error}\n请修正脚本。"
            else:
                enhanced_task = task_description

            # 步骤1: 生成脚本
            result.steps.append("🤖 正在调用大模型生成脚本...")
            try:
                generated_script = self.generator.generate(enhanced_task)
                result.generated_script = generated_script
                result.steps.append(
                    f"✅ 脚本生成成功 (类型: {generated_script.script_type}, "
                    f"长度: {len(generated_script.content)} 字符)"
                )
            except Exception as e:
                result.steps.append(f"❌ 脚本生成失败: {e}")
                result.error_message = f"脚本生成失败: {e}"
                break

            # 步骤2: 安全性检查
            result.steps.append("🔍 正在进行安全性检查...")
            safety_report = self.safety_checker.check(
                generated_script.content,
                generated_script.script_type
            )
            result.safety_report = safety_report

            if safety_report.risk_level == "dangerous":
                result.steps.append(f"⛔ 脚本包含高危操作，拒绝执行: {safety_report.risks}")
                result.error_message = f"安全检查不通过 (危险): {', '.join(safety_report.risks)}"
                last_error = f"安全风险: {', '.join(safety_report.risks)}。请生成不包含这些危险操作的脚本。"
                retry_count += 1
                continue

            if safety_report.risk_level == "warning":
                result.steps.append(f"⚠️ 安全检查发现警告: {safety_report.risks}")
                # 警告级别仍然允许执行，但记录下来

            result.steps.append("✅ 安全检查通过")

            # 步骤3: 执行脚本
            result.steps.append("🚀 正在执行脚本...")
            execution_result = self.executor.execute(
                generated_script.content,
                generated_script.script_type
            )
            result.execution_result = execution_result
            result.retry_count = retry_count

            elapsed = time.time() - start_time
            result.steps.append(f"⏱ 执行耗时: {elapsed:.2f} 秒")

            if execution_result.success:
                result.success = True
                result.steps.append("🎉 任务执行成功！")
                break
            else:
                result.steps.append(f"❌ 执行失败 (返回码: {execution_result.return_code})")
                last_error = execution_result.stderr or execution_result.error_message

                # 如果是致命错误（如语法错误），不再重试
                if "SyntaxError" in last_error:
                    result.steps.append("检测到语法错误，不再重试")
                    result.error_message = f"脚本语法错误: {last_error}"
                    break

                retry_count += 1
                if retry_count > self.MAX_RETRIES:
                    result.steps.append(f"已达最大重试次数 ({self.MAX_RETRIES})，任务失败")
                    result.error_message = f"重试 {self.MAX_RETRIES} 次后仍失败: {last_error}"

        result.total_time = time.time() - start_time
        return result

    def print_result(self, result: TaskResult):
        """格式化打印任务结果"""
        print("\n" + "=" * 60)
        print("📊 任务执行报告")
        print("=" * 60)

        # 执行步骤
        print("\n📋 执行流程:")
        for step in result.steps:
            print(f"  {step}")

        # 脚本内容
        if result.generated_script:
            print("\n" + "-" * 60)
            print(f"📝 生成的脚本 ({result.generated_script.script_type}):")
            print("-" * 60)
            print(result.generated_script.content)

        # 执行结果
        if result.execution_result:
            print("\n" + "-" * 60)
            print("📤 执行输出 (stdout):")
            print("-" * 60)
            print(result.execution_result.stdout or "(无输出)")

            if result.execution_result.stderr and not result.execution_result.success:
                print("\n" + "-" * 60)
                print("⚠️ 错误输出 (stderr):")
                print("-" * 60)
                print(result.execution_result.stderr)

            print(f"\n返回码: {result.execution_result.return_code}")
            print(f"执行耗时: {result.execution_result.execution_time:.2f} 秒")

        # 安全报告
        if result.safety_report and result.safety_report.risks:
            print(f"\n🛡 安全报告 (等级: {result.safety_report.risk_level}):")
            for risk in result.safety_report.risks:
                print(f"  - {risk}")

        # 总结
        print("\n" + "=" * 60)
        if result.success:
            print(f"✅ 任务执行成功！总耗时: {result.total_time:.2f} 秒")
        else:
            print(f"❌ 任务执行失败 (重试 {result.retry_count} 次)")
            if result.error_message:
                print(f"   原因: {result.error_message}")
        print("=" * 60)


def run_interactive(api_key: str = None, workspace_dir: str = None):
    """交互式运行 Agent"""
    print("\n" + "=" * 60)
    print("🤖 AutoScript Agent - 自主任务执行智能体")
    print("=" * 60)
    print("💡 使用提示:")
    print("  - 用自然语言描述你要执行的任务")
    print("  - 例如: '在沙箱中创建一个 hello.txt 文件'")
    print("  - 例如: '在当前目录列出所有文件'")
    print("  - 输入 'quit' 或 'exit' 退出")
    print("=" * 60)

    agent = AutoScriptAgent(api_key=api_key, workspace_dir=workspace_dir)
    print(f"✅ Agent 初始化成功")
    print(f"📂 工作区: {agent.workspace_dir}\n")

    while True:
        try:
            task = input("\n💬 请输入任务: ").strip()

            if not task:
                continue

            if task.lower() in ("quit", "exit", "q"):
                print("\n👋 再见！")
                break

            if task.lower() == "workspace":
                info = agent.executor.get_workspace_info()
                print(f"\n📂 工作区: {info['workspace_dir']}")
                print(f"📄 文件数: {info['file_count']}")
                for f in info["files"]:
                    size_kb = f["size"] / 1024
                    print(f"  - {f['name']} ({size_kb:.1f} KB)")
                continue

            # 执行任务
            result = agent.execute_task(task)
            agent.print_result(result)

        except KeyboardInterrupt:
            print("\n\n👋 检测到中断信号，再见！")
            break
        except EOFError:
            print("\n\n👋 输入结束，再见！")
            break
