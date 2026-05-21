#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Qwen 大模型多轮对话脚本
使用阿里云 DashScope API 与通义千问进行对话
支持流式输出
"""

import os
import sys
import json
import ssl
from typing import List, Dict
from urllib import request, error
import time


class QwenChat:
    """通义千问多轮对话类"""
    
    def __init__(self, api_key: str = None, model: str = "qwen-max"):
        """
        初始化对话器
        
        Args:
            api_key: 阿里云 DashScope API Key，如果为 None 则使用默认值
            model: 使用的模型名称，默认为 qwen3.7-max
        """
        # 设置 API Key
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY") or "sk-ee03a518654647f09d2579009abbb4c2"
        
        self.model = model if model != "qwen-max" else "qwen3.7-max"
        self.api_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
        self.conversation_history: List[Dict[str, str]] = []
        
        # 创建 SSL 上下文
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE
    
    def add_user_message(self, content: str):
        """添加用户消息到对话历史"""
        self.conversation_history.append({
            "role": "user",
            "content": content
        })
    
    def add_assistant_message(self, content: str):
        """添加助手消息到对话历史"""
        self.conversation_history.append({
            "role": "assistant",
            "content": content
        })
    
    def chat(self, user_input: str, stream: bool = True) -> str:
        """
        发送消息并获取回复
        
        Args:
            user_input: 用户输入的消息
            stream: 是否使用流式输出，默认为 True
            
        Returns:
            助手的回复内容
        """
        # 添加用户消息到历史
        self.add_user_message(user_input)
        
        try:
            # 构建请求数据
            payload = {
                "model": self.model,
                "input": {
                    "messages": self.conversation_history
                },
                "parameters": {
                    "result_format": "message"
                }
            }
            
            # 如果启用流式输出，添加增量参数
            if stream:
                payload["parameters"]["incremental_output"] = True
            
            # 将数据转换为 JSON 字节
            data = json.dumps(payload).encode('utf-8')
            
            # 创建请求对象
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # 流式输出需要添加 Accept 头
            if stream:
                headers["Accept"] = "text/event-stream"
            
            req = request.Request(
                self.api_url,
                data=data,
                headers=headers,
                method='POST'
            )
            
            # 发送请求
            response = request.urlopen(req, context=self.ssl_context, timeout=60)
            
            if stream:
                # 流式输出处理
                return self._handle_stream_response(response)
            else:
                # 非流式输出处理
                return self._handle_normal_response(response)
                
        except error.HTTPError as e:
            # 处理 HTTP 错误
            try:
                error_body = e.read().decode('utf-8')
                error_data = json.loads(error_body)
                error_msg = f"HTTP 错误 {e.code}: {error_data.get('message', '未知错误')}"
            except:
                error_msg = f"HTTP 错误 {e.code}: {e.reason}"
            
            print(f"\n⚠️  {error_msg}")
            return f"抱歉，发生错误: {e.code}"
            
        except error.URLError as e:
            # 处理 URL 错误（通常是网络问题）
            error_msg = f"网络连接失败: {e.reason}"
            print(f"\n⚠️  {error_msg}")
            return "抱歉，网络连接失败，请检查网络"
            
        except TimeoutError:
            error_msg = "请求超时，请检查网络连接"
            print(f"\n⚠️  {error_msg}")
            return "抱歉，请求超时，请稍后重试"
            
        except Exception as e:
            error_msg = f"发生异常: {str(e)}"
            print(f"\n⚠️  {error_msg}")
            return f"抱歉，发生异常: {str(e)}"
    
    def _handle_stream_response(self, response) -> str:
        """
        处理流式响应
        
        Args:
            response: HTTP 响应对象
            
        Returns:
            完整的回复内容
        """
        full_content = ""
        
        try:
            # 逐行读取响应
            for line in response:
                line_str = line.decode('utf-8').strip()
                
                if not line_str:
                    continue
                
                # 处理 SSE 格式的数据
                if line_str.startswith('data:'):
                    json_str = line_str[5:].strip()  # 去掉 "data:" 前缀
                    
                    if json_str == '[DONE]':
                        # 流结束
                        print()  # 换行
                        self.add_assistant_message(full_content)
                        return full_content
                    
                    try:
                        data = json.loads(json_str)
                        
                        # DashScope 流式响应格式
                        if "output" in data and "choices" in data["output"]:
                            choice = data["output"]["choices"][0]
                            
                            # 检查是否有 delta 或 message
                            content = None
                            if "delta" in choice and "content" in choice["delta"]:
                                content = choice["delta"]["content"]
                            elif "message" in choice and "content" in choice["message"]:
                                content = choice["message"]["content"]
                            
                            if content:
                                full_content += content
                                # 逐字打印，实现打字机效果
                                print(content, end='', flush=True)
                                time.sleep(0.02)  # 控制输出速度
                    
                    except json.JSONDecodeError:
                        continue
                        
        except Exception as e:
            print(f"\n⚠️  流式输出异常: {e}")
        
        # 保存结果
        if full_content:
            print()  # 换行
            self.add_assistant_message(full_content)
        
        return full_content
    
    def _handle_normal_response(self, response) -> str:
        """
        处理普通响应（非流式）
        
        Args:
            response: HTTP 响应对象
            
        Returns:
            完整的回复内容
        """
        response_data = response.read().decode('utf-8')
        result = json.loads(response_data)
        
        # 解析返回结果
        if "output" in result and "choices" in result["output"]:
            assistant_reply = result["output"]["choices"][0]["message"]["content"]
            # 添加助手回复到历史
            self.add_assistant_message(assistant_reply)
            return assistant_reply
        else:
            error_msg = f"响应格式异常: {result}"
            print(f"\n⚠️  {error_msg}")
            return "抱歉，无法解析响应结果"
    
    def clear_history(self):
        """清空对话历史"""
        self.conversation_history.clear()
        print("✅ 对话历史已清空")
    
    def get_history_length(self) -> int:
        """获取对话历史长度（消息对数）"""
        return len(self.conversation_history) // 2
    
    def show_history(self):
        """显示对话历史"""
        if not self.conversation_history:
            print("📝 当前没有对话历史")
            return
        
        print("\n" + "=" * 60)
        print("📜 对话历史:")
        print("=" * 60)
        for i, msg in enumerate(self.conversation_history, 1):
            role = "👤 用户" if msg["role"] == "user" else "🤖 助手"
            print(f"\n[{i}] {role}:")
            print(f"    {msg['content']}")
        print("=" * 60)


def print_welcome():
    """打印欢迎信息"""
    print("\n" + "=" * 60)
    print("🤖 Qwen 多轮对话系统")
    print("=" * 60)
    print("💡 使用提示:")
    print("  - 直接输入消息与 AI 对话")
    print("  - 输入 'history' 查看对话历史")
    print("  - 输入 'clear' 清空对话历史")
    print("  - 输入 'quit' 或 'exit' 退出对话")
    print("=" * 60)


def main():
    """主函数"""
    print_welcome()
    
    # 初始化对话器
    try:
        chatbot = QwenChat()
        print(f"✅ 已成功连接到 {chatbot.model} 模型（流式输出）\n")
    except ValueError as e:
        print(f"❌ {e}")
        sys.exit(1)
    
    # 开始多轮对话
    while True:
        try:
            # 获取用户输入
            user_input = input("\n👤 你: ").strip()
            
            # 处理特殊命令
            if not user_input:
                continue
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\n👋 再见！感谢使用 Qwen 对话系统")
                break
            
            if user_input.lower() == 'history':
                chatbot.show_history()
                continue
            
            if user_input.lower() == 'clear':
                chatbot.clear_history()
                continue
            
            # 发送消息并获取回复（流式输出）
            print("\n🤖 Qwen: ", end="", flush=True)
            reply = chatbot.chat(user_input, stream=True)
            
        except KeyboardInterrupt:
            print("\n\n👋 检测到中断信号，再见！")
            break
        except EOFError:
            print("\n\n👋 输入结束，再见！")
            break


if __name__ == "__main__":
    main()
