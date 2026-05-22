#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LangChain Tools - 文件操作和命令执行工具
封装 ScriptExecutor 和 SafetyChecker 为 LangChain 可调用工具
"""

import os
import sys
from typing import Optional

from langchain_core.tools import tool
from pydantic import BaseModel, Field

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agent.script_executor import ScriptExecutor
from agent.safety_checker import SafetyChecker

# 全局执行器和检查器实例
_executor = ScriptExecutor()
_checker = SafetyChecker()


# ===================== Pydantic 输入模型 =====================

class WriteFileInput(BaseModel):
    """写文件输入"""
    filepath: str = Field(description="文件路径（相对于工作区），例如 'hello.txt' 或 'subdir/data.txt'")
    content: str = Field(description="要写入文件的内容")


class ReadFileInput(BaseModel):
    """读文件输入"""
    filepath: str = Field(description="要读取的文件路径（相对于工作区）")


class MoveFileInput(BaseModel):
    """移动文件输入"""
    source: str = Field(description="源文件路径（相对于工作区）")
    destination: str = Field(description="目标文件路径（相对于工作区）")


class ExecuteShellInput(BaseModel):
    """执行 Shell 命令输入"""
    command: str = Field(description="要执行的 Shell 命令（会在沙箱工作区中执行）")


class DeleteFileInput(BaseModel):
    """删除文件输入"""
    filepath: str = Field(description="要删除的文件路径（相对于工作区）")


# ===================== Tools =====================

@tool(args_schema=WriteFileInput)
def write_file(filepath: str, content: str) -> str:
    """
    在沙箱工作区中创建一个文件并写入内容。
    使用此工具来创建新文件或覆盖已有文件。
    文件路径相对于工作区目录。
    """
    full_path = os.path.join(_executor.workspace_dir, filepath)
    os.makedirs(os.path.dirname(full_path) or _executor.workspace_dir, exist_ok=True)

    try:
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        size = os.path.getsize(full_path)
        return f"✅ 文件写入成功: {filepath} ({size} 字节)"
    except Exception as e:
        return f"❌ 文件写入失败: {e}"


@tool(args_schema=ReadFileInput)
def read_file(filepath: str) -> str:
    """
    读取沙箱工作区中的文件内容。
    使用此工具查看已创建文件的内容。
    """
    full_path = os.path.join(_executor.workspace_dir, filepath)
    if not os.path.exists(full_path):
        return f"❌ 文件不存在: {filepath}"

    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        size = os.path.getsize(full_path)
        return f"📄 {filepath} ({size} 字节):\n{content}"
    except Exception as e:
        return f"❌ 读取失败: {e}"


@tool
def list_files() -> str:
    """
    列出沙箱工作区中的所有文件和目录。
    使用此工具查看当前有哪些文件。
    """
    try:
        items = []
        workspace = _executor.workspace_dir
        for entry in sorted(os.listdir(workspace)):
            full_path = os.path.join(workspace, entry)
            if os.path.isfile(full_path):
                size = os.path.getsize(full_path)
                items.append(f"  📄 {entry} ({size} 字节)")
            elif os.path.isdir(full_path):
                items.append(f"  📁 {entry}/")

        if not items:
            return "📂 工作区为空"

        return f"📂 工作区文件列表 ({workspace}):\n" + "\n".join(items)
    except Exception as e:
        return f"❌ 列出文件失败: {e}"


@tool(args_schema=MoveFileInput)
def move_file(source: str, destination: str) -> str:
    """
    移动或重命名沙箱工作区中的文件。
    使用此工具将文件从一个位置移动/重命名到另一个位置。
    """
    src_path = os.path.join(_executor.workspace_dir, source)
    dst_path = os.path.join(_executor.workspace_dir, destination)

    if not os.path.exists(src_path):
        return f"❌ 源文件不存在: {source}"

    try:
        os.makedirs(os.path.dirname(dst_path) or _executor.workspace_dir, exist_ok=True)
        os.rename(src_path, dst_path)
        return f"✅ 文件移动成功: {source} → {destination}"
    except Exception as e:
        return f"❌ 移动失败: {e}"


@tool(args_schema=DeleteFileInput)
def delete_file(filepath: str) -> str:
    """
    删除沙箱工作区中的文件。
    使用此工具删除不需要的文件。只能删除工作区内的文件。
    """
    full_path = os.path.join(_executor.workspace_dir, filepath)

    # 安全检查：禁止删除系统关键路径
    resolved = os.path.realpath(full_path)
    workspace_real = os.path.realpath(_executor.workspace_dir)
    if not resolved.startswith(workspace_real):
        return f"⛔ 安全拒绝: 不能删除工作区外的文件 {filepath}"

    if not os.path.exists(full_path):
        return f"❌ 文件不存在: {filepath}"

    if os.path.isdir(full_path):
        return f"❌ 不能直接删除目录: {filepath}（如需删除非空目录请用 execute_shell 执行 rm -r）"

    try:
        os.remove(full_path)
        return f"✅ 文件已删除: {filepath}"
    except Exception as e:
        return f"❌ 删除失败: {e}"


@tool(args_schema=ExecuteShellInput)
def execute_shell(command: str) -> str:
    """
    在沙箱工作区中执行 Shell 命令。
    使用此工具来运行系统命令（如 ls, cat, echo, date 等）。
    命令会在隔离的工作区目录中执行。
    注意：禁止使用 sudo, rm -rf / 等危险命令。
    """
    # 安全检查
    report = _checker.check_shell_script(command)
    if report.risk_level == "dangerous":
        return f"⛔ 命令被安全策略拒绝: {'; '.join(report.risks)}"

    # 包装为脚本执行
    script = f"#!/bin/bash\nset -e\n{command}"
    result = _executor.execute(script, script_type="shell", timeout=15)

    if result.success:
        return f"✅ 命令执行成功:\n{result.stdout}" if result.stdout else "✅ 命令执行成功（无输出）"
    else:
        return f"❌ 命令执行失败 (返回码 {result.return_code}):\n{result.stderr or result.stdout}"
