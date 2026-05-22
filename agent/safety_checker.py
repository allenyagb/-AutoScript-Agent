#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全性检查模块 - 检测脚本中的高风险指令和恶意代码
"""

import re
import ast
from dataclasses import dataclass, field
from typing import List, Tuple


@dataclass
class SafetyReport:
    """安全检查报告"""
    is_safe: bool = True
    risks: List[str] = field(default_factory=list)
    risk_level: str = "safe"  # safe, warning, dangerous


class SafetyChecker:
    """脚本安全性检查器"""

    # Shell 脚本高风险指令黑名单
    SHELL_DANGEROUS_PATTERNS = [
        # 删除命令
        (r"\brm\s+-rf\s+/(\s|$|\*|\.\.)", "危险: 检测到 rm -rf / 删除根目录"),
        (r"\brm\s+-rf\s+~(\s|$|\*)", "危险: 检测到 rm -rf ~ 删除用户目录"),
        (r"\brm\s+-rf\s+/([a-z]+/)+", "危险: 检测到 rm -rf /path 删除系统路径"),
        (r"\brm\s+-rf\s+\$HOME", "危险: 检测到删除 HOME 目录"),
        (r"\brm\s+-rf\s+\/etc", "危险: 检测到删除 /etc 系统配置"),
        (r"\brm\s+-rf\s+\/boot", "危险: 检测到删除 /boot 启动目录"),

        # 权限提升
        (r"\bsudo\b", "警告: 脚本中包含 sudo 提权操作"),
        (r"\bsu\s+-", "警告: 脚本中包含 su 切换用户操作"),

        # 系统命令危险操作
        (r"\bchmod\s+777\s+/", "警告: 对系统路径使用 chmod 777"),
        (r"\bchmod\s+-R\s+777\s+/", "危险: 递归修改系统路径权限为 777"),
        (r"\bmount\s+/dev/", "警告: 挂载块设备操作"),
        (r"\bmkfs\.", "危险: 格式化文件系统"),
        (r"\bdd\s+if=/dev/", "危险: dd 直接操作块设备"),
        (r"\b:\(\)\s*\{\s*:\|\:&\s*\}\s*;", "危险: 检测到 fork 炸弹"),

        # 网络和下载危险指令
        (r"\bcurl.*\|.*sh\b", "危险: curl 管道执行远程脚本"),
        (r"\bwget.*-O\s*-\s*\|.*sh\b", "危险: wget 管道执行远程脚本"),
        (r"\bnc\s+-[lL].*-[eE]\s+/bin/", "危险: netcat 反向 shell"),

        # 系统服务操作
        (r"\bsystemctl\s+disable\s+", "警告: 禁用系统服务"),
        (r"\bsystemctl\s+stop\s+(ssh|firewall|ufw|iptables)", "危险: 停止安全相关服务"),
        (r"\bmodprobe\s+-r\b", "警告: 卸载内核模块"),

        # 用户和权限
        (r"\buserdel\s+-r\s+root", "危险: 删除 root 用户"),
        (r"\bpasswd\s+root", "警告: 修改 root 密码"),
        (r"\bchown\s+-R\s+.*\s+/", "警告: 递归修改系统路径所有权"),
    ]

    # 需要工作区路径限制检查的模式
    WORKSPACE_CHECK_PATTERNS = [
        r"open\s*\(['\"]/",
        r"open\s*\(['\"]~",
        r"os\.chdir\s*\(['\"]/",
        r"os\.chdir\s*\(['\"]~",
        r"subprocess\..*['\"]/",
        r"shutil\.rmtree\s*\(['\"]/",
        r"shutil\.rmtree\s*\(['\"]~",
    ]

    def __init__(self, workspace_dir: str = None):
        """
        初始化安全检查器

        Args:
            workspace_dir: 允许操作的工作区目录，默认为当前目录
        """
        import os
        self.workspace_dir = os.path.abspath(workspace_dir or os.getcwd())

    def check_shell_script(self, script_content: str) -> SafetyReport:
        """
        检查 Shell 脚本安全性

        Args:
            script_content: Shell 脚本内容

        Returns:
            SafetyReport: 安全检查报告
        """
        report = SafetyReport()

        for pattern, risk_msg in self.SHELL_DANGEROUS_PATTERNS:
            if re.search(pattern, script_content, re.IGNORECASE):
                report.risks.append(risk_msg)
                report.is_safe = False

                # 根据风险等级分类
                if risk_msg.startswith("危险:"):
                    report.risk_level = "dangerous"
                elif risk_msg.startswith("警告:") and report.risk_level != "dangerous":
                    report.risk_level = "warning"

        return report

    def check_python_script(self, script_content: str) -> SafetyReport:
        """
        检查 Python 脚本安全性 (通过 AST 静态分析)

        Args:
            script_content: Python 脚本内容

        Returns:
            SafetyReport: 安全检查报告
        """
        report = SafetyReport()

        # 1. 首先用正则检查高危模式
        for pattern in self.WORKSPACE_CHECK_PATTERNS:
            if re.search(pattern, script_content):
                report.risks.append("警告: 检测到可能访问系统路径的代码")
                report.risk_level = "warning"

        # 2. AST 静态分析
        try:
            tree = ast.parse(script_content)
            self._analyze_ast(tree, report)
        except SyntaxError as e:
            report.is_safe = False
            report.risk_level = "dangerous"
            report.risks.append(f"语法错误: {e}")

        return report

    def _analyze_ast(self, tree: ast.AST, report: SafetyReport):
        """递归分析 AST 检测危险操作"""
        for node in ast.walk(tree):
            # 检测 os.system / subprocess 调用
            if isinstance(node, ast.Call):
                self._check_dangerous_call(node, report)

            # 检测 import 危险模块
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in ("os", "subprocess", "shutil", "ctypes"):
                        # 导入这些模块本身不危险，但需要进一步检查调用
                        pass

            if isinstance(node, ast.ImportFrom):
                if node.module in ("os", "subprocess", "shutil", "ctypes"):
                    pass

    def _check_dangerous_call(self, node: ast.Call, report: SafetyReport):
        """检查函数调用中的危险操作"""
        # 检查 os.system / os.popen / subprocess.call 等
        if isinstance(node.func, ast.Attribute):
            func_name = node.func.attr

            # os.system("rm -rf /")
            if func_name in ("system", "popen", "call", "run", "Popen"):
                for arg in node.args:
                    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                        arg_str = arg.value.lower()
                        if any(dangerous in arg_str for dangerous in
                               ["rm -rf /", "mkfs.", "dd if=/dev/", "fdisk", "modprobe"]):
                            report.is_safe = False
                            report.risk_level = "dangerous"
                            report.risks.append(f"危险: 检测到危险命令: {arg.value[:50]}")

            # os.remove / shutil.rmtree 路径检查
            if func_name in ("remove", "rmtree", "unlink"):
                for arg in node.args:
                    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                        path = arg.value
                        if path.startswith("/etc") or path.startswith("/boot") or \
                           path.startswith("/bin") or path.startswith("/usr") or \
                           path == "/":
                            report.is_safe = False
                            report.risk_level = "dangerous"
                            report.risks.append(f"危险: 尝试操作系统关键路径: {path}")

        # 检查直接调用 eval / exec / compile
        if isinstance(node.func, ast.Name):
            if node.func.id in ("eval", "exec", "compile", "__import__"):
                report.risks.append("警告: 使用了 eval/exec/compile 动态执行")
                if report.risk_level != "dangerous":
                    report.risk_level = "warning"

    def check(self, script_content: str, script_type: str = "auto") -> SafetyReport:
        """
        统一安全检查入口

        Args:
            script_content: 脚本内容
            script_type: 脚本类型 ("python", "shell", "auto")

        Returns:
            SafetyReport: 安全检查报告
        """
        if script_type == "auto":
            # 自动检测脚本类型
            script_type = self._detect_script_type(script_content)

        if script_type == "python":
            return self.check_python_script(script_content)
        else:
            return self.check_shell_script(script_content)

    def _detect_script_type(self, content: str) -> str:
        """自动检测脚本类型"""
        if content.strip().startswith("#!/") and "python" in content.split("\n")[0].lower():
            return "python"
        if re.search(r"(import\s+\w+|def\s+\w+\s*\(|class\s+\w+)", content):
            return "python"
        if content.strip().startswith("#!/bin/bash") or content.strip().startswith("#!/bin/sh"):
            return "shell"
        # 默认按 shell 处理
        return "shell"
