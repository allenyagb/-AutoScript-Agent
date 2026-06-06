#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LangChain 兼容的 Qwen ChatModel - 封装 DashScope API
支持工具调用 (Function Calling)
"""

import json
import ssl
import uuid
from typing import Any, Dict, Iterator, List, Optional, Sequence

from urllib import request, error

from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.tools import BaseTool
from pydantic import Field


def _convert_tool_to_dashscope_format(tool: BaseTool) -> dict:
    """将 LangChain Tool 转换为 DashScope tools 格式"""
    schema = tool.args_schema.model_json_schema() if tool.args_schema else {}
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description,
            "parameters": {
                "type": "object",
                "properties": schema.get("properties", {}),
                "required": schema.get("required", [])
            }
        }
    }


def _convert_messages_to_dashscope(messages: List[BaseMessage]) -> List[dict]:
    """将 LangChain 消息转为 DashScope 格式"""
    result = []
    for msg in messages:
        if isinstance(msg, SystemMessage):
            result.append({"role": "system", "content": msg.content})
        elif isinstance(msg, HumanMessage):
            result.append({"role": "user", "content": msg.content})
        elif isinstance(msg, AIMessage):
            entry: dict = {"role": "assistant", "content": msg.content or ""}
            if msg.tool_calls:
                tool_calls = []
                for tc in msg.tool_calls:
                    tool_calls.append({
                        "function": {
                            "name": tc["name"],
                            "arguments": json.dumps(tc["args"], ensure_ascii=False)
                        }
                    })
                entry["tool_calls"] = tool_calls
            result.append(entry)
        elif isinstance(msg, ToolMessage):
            result.append({
                "role": "tool",
                "content": msg.content,
                "tool_call_id": msg.tool_call_id
            })
    return result


class ChatQwen(BaseChatModel):
    """LangChain 兼容的通义千问 ChatModel (DashScope API)"""

    api_key: str = Field(default="sk-ee03a518654647f09d2579009abbb4c2")
    model_name: str = Field(default="qwen3.7-max")
    temperature: float = Field(default=0.1)
    request_timeout: int = Field(default=120, description="API 请求超时（秒），复杂工具调用任务可能需要较长时间")
    api_url: str = Field(
        default="https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
    )

    _bound_tools: Optional[List[dict]] = None

    class Config:
        arbitrary_types_allowed = True

    @property
    def _llm_type(self) -> str:
        return "qwen-dashscope"

    @property
    def _identifying_params(self) -> Dict[str, Any]:
        return {"model_name": self.model_name}

    def bind_tools(
        self,
        tools: Sequence[Any],
        **kwargs: Any,
    ) -> "ChatQwen":
        """绑定工具到模型"""
        formatted = []
        for t in tools:
            if isinstance(t, BaseTool):
                formatted.append(_convert_tool_to_dashscope_format(t))
            elif isinstance(t, dict):
                formatted.append(t)
        new_model = self.model_copy()
        new_model._bound_tools = formatted if formatted else None
        return new_model

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """调用 DashScope API 生成回复"""
        dashscope_messages = _convert_messages_to_dashscope(messages)

        payload: dict = {
            "model": self.model_name,
            "input": {"messages": dashscope_messages},
            "parameters": {
                "result_format": "message",
                "temperature": self.temperature,
            }
        }

        # 添加工具定义
        if self._bound_tools:
            payload["parameters"]["tools"] = self._bound_tools

        # SSL 上下文
        ssl_context = ssl.create_default_context()

        data = json.dumps(payload).encode("utf-8")
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        req = request.Request(self.api_url, data=data, headers=headers, method="POST")

        try:
            response = request.urlopen(req, context=ssl_context, timeout=self.request_timeout)
            response_data = json.loads(response.read().decode("utf-8"))
        except error.HTTPError as e:
            error_body = e.read().decode("utf-8") if e.fp else str(e)
            raise RuntimeError(f"DashScope API 错误 {e.code}: {error_body}")
        except Exception as e:
            raise RuntimeError(f"DashScope API 调用失败: {e}")

        # 解析响应
        try:
            choice = response_data["output"]["choices"][0]
            msg = choice["message"]
            content = msg.get("content", "") or ""
            finish_reason = choice.get("finish_reason", "stop")

            ai_message = AIMessage(content=content)

            # 处理工具调用
            tool_calls_raw = msg.get("tool_calls", [])
            if tool_calls_raw:
                lc_tool_calls = []
                for tc in tool_calls_raw:
                    func = tc.get("function", {})
                    try:
                        args = json.loads(func.get("arguments", "{}"))
                    except json.JSONDecodeError:
                        args = {}
                    lc_tool_calls.append({
                        "name": func.get("name", ""),
                        "args": args,
                        "id": func.get("id", f"call_{uuid.uuid4().hex[:8]}"),
                    })
                ai_message = AIMessage(
                    content=content,
                    tool_calls=lc_tool_calls,
                )

            generation = ChatGeneration(message=ai_message)
            return ChatResult(generations=[generation])

        except (KeyError, IndexError) as e:
            raise RuntimeError(f"DashScope 响应解析失败: {e}\n原始响应: {response_data}")
