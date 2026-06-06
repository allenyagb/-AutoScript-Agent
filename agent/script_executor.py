#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
脚本执行模块 - 安全执行脚本并捕获输出
"""

import os
import sys
import tempfile
import subprocess
import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ExecutionResult:
    """脚本执行结果"""
    success: bool
    stdout: str
    stderr: str
    return_code: int
    script_path: str
    script_type: str
    execution_time: float
    error_message: str = ""


class ScriptExecutor:
    """脚本执行器 - 在受控环境中执行脚本"""

    # 默认执行超时时间（秒）
    DEFAULT_TIMEOUT = 30

    # 最大输出字节数
    MAX_OUTPUT_SIZE = 10 * 1024 * 1024  # 10MB

    def __init__(self, workspace_dir: str = None, use_sandbox: bool = False):
        """
        初始化脚本执行器

        Args:
            workspace_dir: 工作区目录，脚本在此目录下执行
            use_sandbox: 是否使用沙箱执行（MVP阶段先实现简单子进程执行）
        """
        self.workspace_dir = os.path.abspath(
            workspace_dir or os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "sandbox_workspace"
            )
        )
        self.use_sandbox = use_sandbox

        # 确保工作区目录存在
        os.makedirs(self.workspace_dir, exist_ok=True)

    def execute(self, script_content: str, script_type: str = "auto",
                timeout: int = None, env: dict = None) -> ExecutionResult:
        """
        执行脚本

        Args:
            script_content: 脚本内容
            script_type: 脚本类型 ("python", "shell", "auto")
            timeout: 超时时间（秒），默认 30 秒
            env: 额外的环境变量

        Returns:
            ExecutionResult: 执行结果
        """
        timeout = timeout or self.DEFAULT_TIMEOUT
        script_type = self._resolve_script_type(script_content, script_type)

        # 生成临时脚本文件
        script_path = self._create_temp_script(script_content, script_type)

        start_time = time.time()

        try:
            result = self._run_script(script_path, script_type, timeout, env)
        finally:
            # 清理临时文件
            self._cleanup_script(script_path)

        result.execution_time = time.time() - start_time
        result.script_type = script_type

        return result

    def execute_file(self, file_path: str, timeout: int = None) -> ExecutionResult:
        """
        执行已有的脚本文件

        Args:
            file_path: 脚本文件路径
            timeout: 超时时间

        Returns:
            ExecutionResult: 执行结果
        """
        timeout = timeout or self.DEFAULT_TIMEOUT

        if not os.path.isfile(file_path):
            return ExecutionResult(
                success=False,
                stdout="",
                stderr="",
                return_code=-1,
                script_path=file_path,
                script_type="unknown",
                execution_time=0,
                error_message=f"文件不存在: {file_path}"
            )

        script_type = self._detect_file_type(file_path)

        # 确保可执行权限
        if script_type == "shell":
            os.chmod(file_path, os.stat(file_path).st_mode | 0o111)

        start_time = time.time()

        try:
            result = self._run_script(file_path, script_type, timeout)
        except Exception as e:
            result = ExecutionResult(
                success=False,
                stdout="",
                stderr=str(e),
                return_code=-1,
                script_path=file_path,
                script_type=script_type,
                execution_time=time.time() - start_time,
                error_message=str(e)
            )

        result.execution_time = time.time() - start_time
        result.script_type = script_type

        return result

    def _run_script(self, script_path: str, script_type: str,
                    timeout: int, env: dict = None) -> ExecutionResult:
        """实际运行脚本"""
        try:
            # 构建执行命令
            if script_type == "python":
                cmd = [sys.executable or "python3", script_path]
            elif script_type == "shell":
                cmd = ["/bin/bash", script_path]
            else:
                return ExecutionResult(
                    success=False,
                    stdout="",
                    stderr="",
                    return_code=-1,
                    script_path=script_path,
                    script_type=script_type,
                    execution_time=0,
                    error_message=f"不支持的脚本类型: {script_type}"
                )

            # 准备环境变量
            process_env = os.environ.copy()
            if env:
                process_env.update(env)
            # 设置工作区环境变量
            process_env["AGENT_WORKSPACE"] = self.workspace_dir

            # 执行脚本
            process = subprocess.run(
                cmd,
                cwd=self.workspace_dir,
                env=process_env,
                capture_output=True,
                timeout=timeout,
                text=True,
            )

            # 限制输出大小
            stdout = self._truncate_output(process.stdout)
            stderr = self._truncate_output(process.stderr)

            return ExecutionResult(
                success=(process.returncode == 0),
                stdout=stdout,
                stderr=stderr,
                return_code=process.returncode,
                script_path=script_path,
                script_type=script_type,
                execution_time=0,
                error_message="" if process.returncode == 0 else stderr
            )

        except subprocess.TimeoutExpired:
            return ExecutionResult(
                success=False,
                stdout="",
                stderr=f"脚本执行超时 ({timeout} 秒)",
                return_code=-1,
                script_path=script_path,
                script_type=script_type,
                execution_time=0,
                error_message=f"执行超时: 超过 {timeout} 秒"
            )
        except FileNotFoundError as e:
            return ExecutionResult(
                success=False,
                stdout="",
                stderr=str(e),
                return_code=-1,
                script_path=script_path,
                script_type=script_type,
                execution_time=0,
                error_message=f"解释器未找到: {e}"
            )

    def _create_temp_script(self, content: str, script_type: str) -> str:
        """创建临时脚本文件"""
        suffix = ".py" if script_type == "python" else ".sh"
        fd, path = tempfile.mkstemp(suffix=suffix, dir=self.workspace_dir)
        with os.fdopen(fd, 'w') as f:
            f.write(content)

        # 设置可执行权限
        os.chmod(path, 0o755)
        return path

    def _cleanup_script(self, script_path: str):
        """清理临时脚本文件"""
        try:
            if os.path.exists(script_path):
                os.remove(script_path)
        except OSError:
            pass  # 忽略清理失败

    def _resolve_script_type(self, content: str, script_type: str) -> str:
        """解析脚本类型"""
        if script_type != "auto":
            return script_type

        # 自动检测
        if content.strip().startswith("#!/usr/bin/env python") or \
           content.strip().startswith("#!/usr/bin/python"):
            return "python"
        if content.strip().startswith("#!/bin/bash") or \
           content.strip().startswith("#!/bin/sh"):
            return "shell"
        # 检查 Python 特征
        import re
        if re.search(r"(import\s+\w+|def\s+\w+\s*\(|class\s+\w+|print\s*\()", content):
            return "python"
        return "shell"

    def _detect_file_type(self, file_path: str) -> str:
        """检测文件类型"""
        with open(file_path, 'r') as f:
            first_line = f.readline().strip()

        if "python" in first_line.lower():
            return "python"
        if "bash" in first_line.lower() or "sh" in first_line.lower():
            return "shell"

        # 根据扩展名判断
        if file_path.endswith(".py"):
            return "python"
        if file_path.endswith(".sh"):
            return "shell"

        # 默认 shell
        return "shell"

    def _truncate_output(self, output: str) -> str:
        """截断过大的输出"""
        if len(output) > self.MAX_OUTPUT_SIZE:
            truncated = output[:self.MAX_OUTPUT_SIZE]
            return truncated + f"\n\n... (输出已截断，原始大小 {len(output)} 字节)"
        return output

    def get_workspace_info(self) -> dict:
        """获取工作区信息"""
        files = []
        try:
            for entry in os.listdir(self.workspace_dir):
                full_path = os.path.join(self.workspace_dir, entry)
                if os.path.isfile(full_path):
                    size = os.path.getsize(full_path)
                    files.append({
                        "name": entry,
                        "size": size,
                        "path": full_path
                    })
        except OSError:
            pass

        return {
            "workspace_dir": self.workspace_dir,
            "exists": os.path.isdir(self.workspace_dir),
            "files": files,
            "file_count": len(files)
        }
