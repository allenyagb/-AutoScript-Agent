#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LangChain 兼容的 Qwen ChatModel - 封装 DashScope API
支持工具调用 (Function Calling) + SSE 流式输出
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
    AIMessageChunk,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.outputs import ChatGeneration, ChatGenerationChunk, ChatResult
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
                "required": schema.get("required", []),
            },
        },
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
                    tool_calls.append(
                        {
                            "function": {
                                "name": tc["name"],
                                "arguments": json.dumps(tc["args"], ensure_ascii=False),
                            }
                        }
                    )
                entry["tool_calls"] = tool_calls
            result.append(entry)
        elif isinstance(msg, ToolMessage):
            result.append(
                {
                    "role": "tool",
                    "content": msg.content,
                    "tool_call_id": msg.tool_call_id,
                }
            )
    return result


def _build_ssl_context() -> ssl.SSLContext:
    """构建 SSL 上下文（跳过证书验证，兼容内网环境）"""
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    return ssl_context


def _build_payload(
    model_name: str,
    dashscope_messages: List[dict],
    temperature: float,
    bound_tools: Optional[List[dict]],
    stream: bool = False,
) -> dict:
    """构建 DashScope API 请求体"""
    payload: dict = {
        "model": model_name,
        "input": {"messages": dashscope_messages},
        "parameters": {
            "result_format": "message",
            "temperature": temperature,
        },
    }
    if bound_tools:
        payload["parameters"]["tools"] = bound_tools
    if stream:
        payload["parameters"]["incremental_output"] = True
    return payload


def _iter_sse_stream(response) -> Iterator[dict]:
    """逐行解析 SSE 流，yield 每个 JSON 数据块"""
    for line in response:
        line_str = line.decode("utf-8").strip()
        if not line_str:
            continue
        if line_str.startswith("data:"):
            json_str = line_str[5:].strip()
            if json_str == "[DONE]":
                return
            try:
                yield json.loads(json_str)
            except json.JSONDecodeError:
                continue


def _extract_delta(data: dict) -> Optional[str]:
    """从 SSE chunk 中提取 delta content"""
    try:
        choice = data["output"]["choices"][0]
        if "delta" in choice and "content" in choice["delta"]:
            return choice["delta"]["content"]
        # 兼容非增量流式：某些实现用 message
        if "message" in choice and "content" in choice["message"]:
            return choice["message"]["content"]
    except (KeyError, IndexError):
        pass
    return None


class ChatQwen(BaseChatModel):
    """LangChain 兼容的通义千问 ChatModel (DashScope API) — 支持流式输出"""

    api_key: str = Field(default="sk-ee03a518654647f09d2579009abbb4c2")
    model_name: str = Field(default="qwen3.7-max")
    temperature: float = Field(default=0.1)
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

    # ── 流式输出 ──────────────────────────────────────────

    def _stream(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> Iterator[ChatGenerationChunk]:
        """SSE 流式调用 DashScope API，逐 token yield ChatGenerationChunk"""
        dashscope_messages = _convert_messages_to_dashscope(messages)
        payload = _build_payload(
            self.model_name, dashscope_messages, self.temperature,
            self._bound_tools, stream=True,
        )

        ssl_context = _build_ssl_context()
        data_bytes = json.dumps(payload).encode("utf-8")
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
        }

        req = request.Request(self.api_url, data=data_bytes, headers=headers, method="POST")

        try:
            response = request.urlopen(req, context=ssl_context, timeout=60)
        except error.HTTPError as e:
            error_body = e.read().decode("utf-8") if e.fp else str(e)
            raise RuntimeError(f"DashScope API 错误 {e.code}: {error_body}")
        except Exception as e:
            raise RuntimeError(f"DashScope API 调用失败: {e}")

        content_buf = ""
        tool_calls_map: Dict[int, dict] = {}  # index -> {name, args_str, id}

        for chunk_data in _iter_sse_stream(response):
            # 提取文本 delta
            delta_content = _extract_delta(chunk_data)
            if delta_content:
                content_buf += delta_content
                chunk_msg = AIMessageChunk(content=delta_content)
                if run_manager:
                    run_manager.on_llm_new_token(delta_content)
                yield ChatGenerationChunk(message=chunk_msg)

            # 提取 tool_calls delta（DashScope 流式可能逐 part 传输）
            try:
                choice = chunk_data["output"]["choices"][0]
                # 检查 delta 中的 tool_calls
                delta = choice.get("delta", {})
                tool_call_deltas = delta.get("tool_calls", [])
                for tc_delta in tool_call_deltas:
                    idx = tc_delta.get("index", 0)
                    if idx not in tool_calls_map:
                        tool_calls_map[idx] = {"name": "", "arguments": "", "id": ""}
                    func = tc_delta.get("function", {})
                    if "name" in func:
                        tool_calls_map[idx]["name"] += func["name"]
                    if "arguments" in func:
                        tool_calls_map[idx]["arguments"] += func["arguments"]
                    if "id" in func:
                        tool_calls_map[idx]["id"] = func["id"]
            except (KeyError, IndexError):
                pass

        # 最终的 tool_calls（如果有）
        if tool_calls_map:
            lc_tool_calls = []
            for idx in sorted(tool_calls_map.keys()):
                tc = tool_calls_map[idx]
                try:
                    args = json.loads(tc["arguments"]) if tc["arguments"] else {}
                except json.JSONDecodeError:
                    args = {}
                lc_tool_calls.append({
                    "name": tc["name"],
                    "args": args,
                    "id": tc["id"] or f"call_{uuid.uuid4().hex[:8]}",
                })
            # 把 tool_calls 附加到最后一个 chunk
            final_msg = AIMessageChunk(content="", tool_calls=lc_tool_calls)
            yield ChatGenerationChunk(message=final_msg)

    # ── 非流式（内部也用 SSE 以支持回调）─────────────────

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """
        调用 DashScope API 生成回复。

        内部使用 SSE 流式请求，一边累积完整响应，
        一边通过 run_manager.on_llm_new_token() 通知回调（实现流式展示）。
        如果不需要实时回调，行为等价于普通非流式调用。
        """
        # ── 使用 SSE 流式请求（有回调时实时推送 token）──
        try:
            # 流式请求以支持 on_llm_new_token 回调
            dashscope_messages = _convert_messages_to_dashscope(messages)
            payload = _build_payload(
                self.model_name, dashscope_messages, self.temperature,
                self._bound_tools, stream=True,
            )

            ssl_context = _build_ssl_context()
            data_bytes = json.dumps(payload).encode("utf-8")
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "text/event-stream",
            }

            req = request.Request(self.api_url, data=data_bytes, headers=headers, method="POST")

            response = request.urlopen(req, context=ssl_context, timeout=60)

            # 累积完整消息
            full_content = ""
            tool_calls_map: Dict[int, dict] = {}

            for chunk_data in _iter_sse_stream(response):
                delta_content = _extract_delta(chunk_data)
                if delta_content:
                    full_content += delta_content
                    if run_manager:
                        run_manager.on_llm_new_token(delta_content)

                # 累积 tool_calls
                try:
                    choice = chunk_data["output"]["choices"][0]
                    delta = choice.get("delta", {})
                    for tc_delta in delta.get("tool_calls", []):
                        idx = tc_delta.get("index", 0)
                        if idx not in tool_calls_map:
                            tool_calls_map[idx] = {"name": "", "arguments": "", "id": ""}
                        func = tc_delta.get("function", {})
                        if "name" in func:
                            tool_calls_map[idx]["name"] += func["name"]
                        if "arguments" in func:
                            tool_calls_map[idx]["arguments"] += func["arguments"]
                        if "id" in func:
                            tool_calls_map[idx]["id"] = func["id"]
                except (KeyError, IndexError):
                    pass

            # 构建最终 AIMessage
            lc_tool_calls = []
            if tool_calls_map:
                for idx in sorted(tool_calls_map.keys()):
                    tc = tool_calls_map[idx]
                    try:
                        args = json.loads(tc["arguments"]) if tc["arguments"] else {}
                    except json.JSONDecodeError:
                        args = {}
                    lc_tool_calls.append({
                        "name": tc["name"],
                        "args": args,
                        "id": tc["id"] or f"call_{uuid.uuid4().hex[:8]}",
                    })

            ai_message = AIMessage(content=full_content)
            if lc_tool_calls:
                ai_message = AIMessage(content=full_content, tool_calls=lc_tool_calls)

            return ChatResult(generations=[ChatGeneration(message=ai_message)])

        except error.HTTPError as e:
            error_body = e.read().decode("utf-8") if e.fp else str(e)
            raise RuntimeError(f"DashScope API 错误 {e.code}: {error_body}")
        except RuntimeError:
            raise  # 重抛已包装的 RuntimeError
        except Exception as e:
            raise RuntimeError(f"DashScope API 调用失败: {e}")

    # ── 工具绑定 ──────────────────────────────────────────

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
