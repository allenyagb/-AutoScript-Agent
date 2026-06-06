#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
共享的 Rich 控制台工具 — 统一 AutoScript Agent 所有终端输出风格

提供:
  - console: 带自定义主题的 Rich Console 实例
  - 常用辅助函数: 面板、表格、语法高亮、状态提示
"""

import sys
from typing import Optional

from rich.console import Console
from rich.theme import Theme
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.syntax import Syntax
from rich.box import Box, ROUNDED, HEAVY
from rich.columns import Columns

# ── 自定义主题 ─────────────────────────────────────────────
AGENT_THEME = Theme(
    {
        # 角色
        "agent": "#10b981 bold",  # 翡翠绿 — Agent 消息
        "user": "#3b82f6 bold",  # 蓝色 — 用户消息
        "system": "#8b5cf6",  # 紫色 — 系统消息
        # 工具
        "tool": "#f59e0b",  # 琥珀色 — 工具调用
        "tool_out": "#6b7280 italic",  # 灰色 — 工具输出
        # 状态
        "success": "#10b981 bold",
        "error": "#ef4444 bold",
        "warning": "#f59e0b",
        "info": "#60a5fa",
        # 元数据
        "dim": "#6b7280 dim",
        "time": "#9ca3af italic",
        "highlight": "#fbbf24",
        # 标题
        "title": "#818cf8 bold",
        "heading": "#c084fc bold",
    }
)

# 全局 Console 实例
console = Console(
    theme=AGENT_THEME,
    highlight=True,  # 自动语法高亮
    markup=True,  # 支持 Rich markup
    force_terminal=True,  # 始终输出 ANSI
    color_system="truecolor",
)


# ── 辅助函数 ────────────────────────────────────────────────

def success_panel(message: str, title: str = "✅ 成功") -> Panel:
    """成功消息面板"""
    return Panel(
        Text(message, style="success"),
        title=title,
        border_style="success",
        box=ROUNDED,
    )


def error_panel(message: str, title: str = "❌ 错误") -> Panel:
    """错误消息面板"""
    return Panel(
        Text(message, style="error"),
        title=title,
        border_style="error",
        box=ROUNDED,
    )


def info_panel(message: str, title: str = "ℹ️ 信息") -> Panel:
    """信息面板"""
    return Panel(
        Text(message, style="info"),
        title=title,
        border_style="info",
        box=ROUNDED,
    )


def task_panel(message: str) -> Panel:
    """任务面板"""
    return Panel(
        Text(message, style="bold"),
        title="📋 任务",
        border_style="magenta",
        box=HEAVY,
        padding=(1, 2),
    )


def code_block(code: str, language: str = "python", title: Optional[str] = None) -> Syntax:
    """语法高亮代码块"""
    return Syntax(
        code,
        language if language in ("python", "bash", "shell", "json", "yaml") else "text",
        theme="monokai",
        line_numbers=True,
        word_wrap=True,
        background_color="default",
    )


def make_table(title: str, headers: list, rows: list, **kwargs) -> Table:
    """创建风格统一的表格"""
    table = Table(
        title=title,
        title_style="title",
        border_style="dim",
        box=ROUNDED,
        show_header=True,
        header_style="heading",
        **kwargs,
    )
    for h in headers:
        table.add_column(h)
    for row in rows:
        table.add_row(*[str(c) for c in row])
    return table


def dim(text: str) -> str:
    """返回 dim 样式的 markup"""
    return f"[dim]{text}[/dim]"


def agent_style(text: str) -> str:
    return f"[agent]{text}[/agent]"


def tool_style(text: str) -> str:
    return f"[tool]{text}[/tool]"


def user_style(text: str) -> str:
    return f"[user]{text}[/user]"
