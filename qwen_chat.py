#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Qwen 大模型多轮对话脚本
使用阿里云 DashScope API 与通义千问进行对话
Rich 流式输出 — 打字机效果 + 美观终端 UI
"""

import os
import sys
import json
import ssl
import time
from typing import List, Dict

from urllib import request, error

from rich.live import Live
from rich.panel import Panel
from rich.text import Text
from rich import box

# ── 尝试导入项目 Rich Console，失败则用默认 ──
try:
    from agent.console import console
except ImportError:
    from rich.console import Console
    console = Console()


class QwenChat:
    """通义千问多轮对话类（Rich 流式输出）"""

    def __init__(self, api_key: str = None, model: str = "qwen-max"):
        """
        初始化对话器

        Args:
            api_key: 阿里云 DashScope API Key，如果为 None 则使用默认值
            model: 使用的模型名称，默认为 qwen3.7-max
        """
        self.api_key = (
            api_key
            or os.getenv("DASHSCOPE_API_KEY")
            or "sk-ee03a518654647f09d2579009abbb4c2"
        )
        self.model = model if model != "qwen-max" else "qwen3.7-max"
        self.api_url = (
            "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
        )
        self.conversation_history: List[Dict[str, str]] = []

        # 创建 SSL 上下文
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE

    def add_user_message(self, content: str):
        """添加用户消息到对话历史"""
        self.conversation_history.append({"role": "user", "content": content})

    def add_assistant_message(self, content: str):
        """添加助手消息到对话历史"""
        self.conversation_history.append({"role": "assistant", "content": content})

    def chat(self, user_input: str, stream: bool = True) -> str:
        """
        发送消息并获取回复

        Args:
            user_input: 用户输入的消息
            stream: 是否使用流式输出，默认为 True

        Returns:
            助手的回复内容
        """
        self.add_user_message(user_input)

        try:
            payload = {
                "model": self.model,
                "input": {"messages": self.conversation_history},
                "parameters": {"result_format": "message"},
            }

            if stream:
                payload["parameters"]["incremental_output"] = True

            data = json.dumps(payload).encode("utf-8")

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            if stream:
                headers["Accept"] = "text/event-stream"

            req_obj = request.Request(
                self.api_url, data=data, headers=headers, method="POST"
            )

            response = request.urlopen(req_obj, context=self.ssl_context, timeout=60)

            if stream:
                return self._handle_stream_response(response)
            else:
                return self._handle_normal_response(response)

        except error.HTTPError as e:
            try:
                error_body = e.read().decode("utf-8")
                error_data = json.loads(error_body)
                error_msg = f"HTTP 错误 {e.code}: {error_data.get('message', '未知错误')}"
            except Exception:
                error_msg = f"HTTP 错误 {e.code}: {e.reason}"

            console.print(f"\n[error]⚠️  {error_msg}[/error]")
            return f"抱歉，发生错误: {e.code}"

        except error.URLError as e:
            error_msg = f"网络连接失败: {e.reason}"
            console.print(f"\n[error]⚠️  {error_msg}[/error]")
            return "抱歉，网络连接失败，请检查网络"

        except TimeoutError:
            console.print("\n[error]⚠️  请求超时，请检查网络连接[/error]")
            return "抱歉，请求超时，请稍后重试"

        except Exception as e:
            console.print(f"\n[error]⚠️  发生异常: {str(e)}[/error]")
            return f"抱歉，发生异常: {str(e)}"

    def _handle_stream_response(self, response) -> str:
        """
        处理 Rich 流式响应 — 打字机效果
        """
        full_content = ""
        stream_text = Text("")
        typing_speed = 0.015  # 打字机字符间隔（秒）

        try:
            with Live(
                Panel(stream_text, title="🤖 Qwen 回复中…", border_style="green"),
                console=console,
                refresh_per_second=20,
                transient=False,
            ) as live:
                for line in response:
                    line_str = line.decode("utf-8").strip()
                    if not line_str:
                        continue

                    if line_str.startswith("data:"):
                        json_str = line_str[5:].strip()

                        if json_str == "[DONE]":
                            break

                        try:
                            data = json.loads(json_str)

                            if "output" in data and "choices" in data["output"]:
                                choice = data["output"]["choices"][0]

                                content = None
                                if "delta" in choice and "content" in choice["delta"]:
                                    content = choice["delta"]["content"]
                                elif (
                                    "message" in choice
                                    and "content" in choice["message"]
                                ):
                                    content = choice["message"]["content"]

                                if content:
                                    full_content += content
                                    stream_text.append(content, style="green")
                                    live.update(
                                        Panel(
                                            stream_text,
                                            title="🤖 Qwen 回复中…",
                                            border_style="green",
                                        )
                                    )
                                    time.sleep(typing_speed)

                        except json.JSONDecodeError:
                            continue

        except Exception as e:
            console.print(f"\n[error]⚠️  流式输出异常: {e}[/error]")

        if full_content:
            self.add_assistant_message(full_content)

        return full_content

    def _handle_normal_response(self, response) -> str:
        """处理普通响应（非流式）"""
        response_data = response.read().decode("utf-8")
        result = json.loads(response_data)

        if "output" in result and "choices" in result["output"]:
            assistant_reply = result["output"]["choices"][0]["message"]["content"]
            self.add_assistant_message(assistant_reply)
            return assistant_reply
        else:
            error_msg = f"响应格式异常: {result}"
            console.print(f"\n[error]⚠️  {error_msg}[/error]")
            return "抱歉，无法解析响应结果"

    def clear_history(self):
        """清空对话历史"""
        self.conversation_history.clear()
        console.print("[success]✅ 对话历史已清空[/success]")

    def get_history_length(self) -> int:
        """获取对话历史长度（消息对数）"""
        return len(self.conversation_history) // 2

    def show_history(self):
        """显示对话历史"""
        if not self.conversation_history:
            console.print("[dim]📝 当前没有对话历史[/dim]")
            return

        console.print()
        for i, msg in enumerate(self.conversation_history, 1):
            role_icon = "👤 用户" if msg["role"] == "user" else "🤖 助手"
            style = "user" if msg["role"] == "user" else "agent"
            console.print(
                Panel(
                    Text(msg["content"]),
                    title=f"[{i}] {role_icon}",
                    border_style=style,
                    box=box.ROUNDED,
                )
            )


def print_welcome():
    """打印欢迎信息 — Rich 风格"""
    console.print()
    console.print(
        Panel(
            Text.from_markup(
                "[bold]🤖 Qwen 多轮对话系统[/bold]\n\n"
                "[dim]💡 使用提示:[/dim]\n"
                "  • 直接输入消息与 AI 对话\n"
                "  • 输入 [info]history[/info] 查看对话历史\n"
                "  • 输入 [info]clear[/info] 清空对话历史\n"
                "  • 输入 [info]quit[/info] / [info]exit[/info] 退出对话"
            ),
            title="🚀 欢迎",
            border_style="green",
            box=box.HEAVY,
            padding=(1, 2),
        )
    )


def main():
    """主函数 — Rich 流式交互"""
    print_welcome()

    try:
        chatbot = QwenChat()
        console.print(
            f"[success]✅ 已成功连接到 {chatbot.model} 模型[/success] [dim](流式输出)[/dim]\n"
        )
    except ValueError as e:
        console.print(f"[error]❌ {e}[/error]")
        sys.exit(1)

    while True:
        try:
            user_input = console.input("\n[user]👤 你:[/user] ").strip()

            if not user_input:
                continue

            if user_input.lower() in ("quit", "exit", "q"):
                console.print("\n[agent]👋 再见！感谢使用 Qwen 对话系统[/agent]")
                break

            if user_input.lower() == "history":
                chatbot.show_history()
                continue

            if user_input.lower() == "clear":
                chatbot.clear_history()
                continue

            # 流式输出
            console.print("\n[agent]🤖 Qwen:[/agent] ", end="")
            reply = chatbot.chat(user_input, stream=True)

        except KeyboardInterrupt:
            console.print("\n\n[agent]👋 检测到中断信号，再见！[/agent]")
            break
        except EOFError:
            console.print("\n\n[agent]👋 输入结束，再见！[/agent]")
            break


if __name__ == "__main__":
    main()
