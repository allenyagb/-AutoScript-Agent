#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
脚本生成模块 - 利用 Qwen 大模型将自然语言任务转换为可执行脚本
Rich 流式输出版本
"""

import re
import sys
import os
from dataclasses import dataclass
from typing import Optional

from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax
from rich.panel import Panel

# 添加项目根目录到 Python 路径，以便导入 qwen_chat
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from qwen_chat import QwenChat

# 导入项目控制台
try:
    from .console import console, dim, code_block
except ImportError:
    from agent.console import console, dim, code_block


@dataclass
class GeneratedScript:
    """生成的脚本"""
    content: str          # 脚本内容
    script_type: str      # 脚本类型: python, shell
    language: str         # 脚本语言
    description: str      # 脚本功能描述
    raw_response: str     # 原始模型响应


class ScriptGenerator:
    """脚本生成器 - 使用 Qwen 模型生成可执行脚本（Rich 流式输出）"""

    # 脚本生成的系统提示词
    SYSTEM_PROMPT = """你是 Ubuntu 24.04 上的脚本生成专家。将用户任务转为可执行脚本。

规则：
1. 文件操作/系统命令 → Shell(bash)；文本处理/复杂逻辑 → Python
2. 只用标准库，不依赖第三方包
3. 文件路径使用 $AGENT_WORKSPACE 环境变量
4. 禁止 sudo、rm -rf / 等危险操作
5. 包含错误处理和注释

输出格式（严格）：
```脚本类型
脚本代码
```
脚本类型: python 或 shell"""

    def __init__(self, api_key: str = None):
        """
        初始化脚本生成器

        Args:
            api_key: DashScope API Key，为 None 时使用默认值
        """
        self.api_key = api_key

    def generate(self, task_description: str) -> GeneratedScript:
        """
        根据任务描述生成脚本

        Args:
            task_description: 自然语言任务描述

        Returns:
            GeneratedScript: 生成的脚本对象
        """
        # 构建完整提示词（系统提示 + 任务）
        prompt = f"{self.SYSTEM_PROMPT}\n\n## 任务\n{task_description}"

        # 每次生成创建新的对话实例，避免历史积累
        chat = QwenChat(api_key=self.api_key)

        console.print()
        console.print(f"  [dim]⏳ 正在调用 {chat.model} 模型生成脚本...[/dim]")

        # 使用流式输出获取响应
        raw_response = chat.chat(prompt, stream=True)

        console.print(f"  [success]✅ 模型响应已收到[/success] [dim]({len(raw_response)} 字符)[/dim]")

        # 解析模型响应，提取脚本
        script_content, script_type, description = self._parse_response(raw_response)

        # 后处理：清理脚本
        script_content = self._clean_script(script_content, script_type)

        # 代码高亮展示
        lang = "python" if script_type == "python" else "bash"
        console.print(
            Panel(
                code_block(script_content, language=lang),
                title=f"📄 生成 {script_type.upper()} 脚本 ({len(script_content)} 字符)",
                border_style="success",
            )
        )

        return GeneratedScript(
            content=script_content,
            script_type=script_type,
            language="Python" if script_type == "python" else "Bash",
            description=description,
            raw_response=raw_response,
        )

    def _parse_response(self, response: str) -> tuple:
        """
        解析模型响应，提取脚本内容和类型

        Returns:
            (script_content, script_type, description)
        """
        script_content = ""
        script_type = "shell"
        description = ""

        # 尝试匹配 ```script_type ... ``` 格式
        pattern = r"```(\w+)\s*\n(.*?)```"
        matches = re.findall(pattern, response, re.DOTALL)

        if matches:
            for match_type, match_content in matches:
                if match_type.lower() in ("python", "py"):
                    script_type = "python"
                    script_content = match_content.strip()
                    break
                elif match_type.lower() in ("bash", "shell", "sh"):
                    script_type = "shell"
                    script_content = match_content.strip()
                    break
                else:
                    script_content = match_content.strip()
                    break

        if not script_content:
            # 没有代码块标记，尝试提取
            if re.search(
                r"(import\s+\w+|def\s+\w+\s*\(|#!/usr/bin/env\s+python)", response
            ):
                script_type = "python"

            script_content = response.strip()
            script_content = re.sub(r"^```\w*\s*", "", script_content)
            script_content = re.sub(r"\s*```$", "", script_content)

            # 移除解释性文本行
            lines = script_content.split("\n")
            filtered_lines = []
            for line in lines:
                if line.startswith("```"):
                    continue
                filtered_lines.append(line)
            script_content = "\n".join(filtered_lines).strip()

        return script_content, script_type, description

    def _clean_script(self, content: str, script_type: str) -> str:
        """清理和规范化脚本内容"""
        content = content.strip()

        if script_type == "python":
            if not content.startswith("#!/"):
                content = "#!/usr/bin/env python3\n# -*- coding: utf-8 -*-\n\n" + content
        elif script_type == "shell":
            if not content.startswith("#!/"):
                content = "#!/bin/bash\nset -euo pipefail\n\n" + content

        return content
