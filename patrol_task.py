#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
定时巡检任务入口 — 供 cron/systemd timer 调用
用法: python3 patrol_task.py

Rich 美化的流式输出版本
"""

import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent import LangChainAgent
from agent.console import console, dim

from rich.panel import Panel
from rich.text import Text
from rich import box


PATROL_TASK = """
执行一次系统巡检，检查以下项目并将结果写入 patrol_log.txt（追加模式，带上时间戳）：
1. CPU 负载（1/5/15分钟）
2. 内存使用率
3. 磁盘使用率（根分区）
4. 检查是否有僵尸进程
5. 最近 5 分钟的系统负载均值是否超过 CPU 核心数的 80%

最后在 patrol_log.txt 末尾写一行总结：正常/异常。
"""


def main():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    console.print()
    console.print(
        Panel(
            Text(f"⏰ 巡检开始: {now}\n\n{dim(PATROL_TASK.strip())}"),
            title="🔍 系统巡检",
            border_style="info",
            box=box.ROUNDED,
        )
    )

    agent = LangChainAgent()
    result = agent.execute(PATROL_TASK)

    if result["success"]:
        console.print(
            Panel(
                Text(result["final_answer"]),
                title=f"✅ 巡检完成 ({result['elapsed']:.1f}s)",
                border_style="success",
                box=box.ROUNDED,
            )
        )
    else:
        console.print(
            Panel(
                Text(result["final_answer"][:200]),
                title="❌ 巡检失败",
                border_style="error",
                box=box.ROUNDED,
            )
        )

    # 追加分隔线
    log_path = os.path.join(agent.workspace_dir, "patrol_log.txt")
    with open(log_path, "a") as f:
        f.write(f"\n{'─' * 60}\n")

    console.print(f"[dim]📄 日志: {log_path}[/dim]")


if __name__ == "__main__":
    main()
