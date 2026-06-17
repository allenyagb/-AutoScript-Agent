# 🤖 AutoScript Agent

**AutoScript Agent** 是一个基于大语言模型的 Ubuntu 自主任务执行助手。用户只需用自然语言描述任务，Agent 即可自主规划并调用工具完成文件操作、Shell 命令执行、系统巡检等各类操作。

> 核心特性：LangChain 智能体框架 + 阿里云通义千问 (Qwen3.7-max) + 多轮对话记忆 + 安全沙箱 + 错误自动重试

---

## 📋 目录

- [系统要求](#系统要求)
- [安装指南](#安装指南)
- [配置 API Key](#配置-api-key)
- [运行方式](#运行方式)
  - [1. 交互式命令行](#1-交互式命令行)
  - [2. 定时巡检任务](#2-定时巡检任务)
  - [3. 生成答辩 PPT](#3-生成答辩-ppt)
- [测试](#测试)
- [项目结构](#项目结构)
- [可用工具](#可用工具)
- [安全机制](#安全机制)
- [常见问题](#常见问题)

---

## 系统要求

| 项目 | 要求 |
|------|------|
| 操作系统 | Ubuntu 24.04（推荐，其他 Linux 也可运行） |
| Python | 3.10 及以上（开发使用 3.12） |
| Node.js | 仅生成 PPT 时需要（v18+，可选） |
| 网络 | 需能访问阿里云 DashScope API (`dashscope.aliyuncs.com`) |

---

## 安装指南

### 第一步：克隆仓库

```bash
git clone https://github.com/allenyagb/-AutoScript-Agent.git
cd -AutoScript-Agent
```

### 第二步：创建 Python 虚拟环境（推荐）

```bash
python3 -m venv LM_env
source LM_env/bin/activate
```

> 虚拟环境名使用 `LM_env`，已在 `.gitignore` 中忽略。

### 第三步：安装 Python 依赖

```bash
pip install -r requirements.txt
```

这会自动安装以下核心依赖：
- **langchain** (≥1.3.1) — Agent 框架
- **langchain-core** (≥1.4.0) — 消息、工具基类
- **pydantic** (≥2.0) — 数据模型

### 第四步：安装 Node.js 依赖（可选，仅生成 PPT 时需要）

```bash
# 如果系统没有 Node.js，先安装：
# sudo apt install nodejs npm

npm install
```

---

## 配置 API Key

Agent 需要阿里云 DashScope API Key 才能调用通义千问大模型。

### 方式一：环境变量（推荐）

```bash
export DASHSCOPE_API_KEY="你的API-KEY"
```

可将此行添加到 `~/.bashrc` 中持久化：
```bash
echo 'export DASHSCOPE_API_KEY="你的API-KEY"' >> ~/.bashrc
source ~/.bashrc
```

### 方式二：直接修改代码

代码中内置了默认 API Key，可直接修改以下文件中的 `api_key` 参数：
- `agent/agent.py` 第 59 行
- `agent/chat_model.py` 第 79 行
- `qwen_chat.py` 第 30 行
- `tests/` 目录下各测试文件

> ⚠️ **安全提示**：请勿将含有真实 API Key 的代码提交到公开仓库。

### 获取 API Key

1. 访问 [阿里云 DashScope](https://dashscope.aliyun.com/)
2. 注册/登录账号
3. 在控制台获取 API Key

---

## 运行方式

### 1. 交互式命令行

这是 Agent 的主要运行模式，适合执行各种临时任务。

```bash
python3 agent_cli.py
```

启动后进入交互式 REPL：

```
🧑 你: 在沙箱工作区创建一个 hello.txt，内容是"Hello World"

==================================================
✅ 任务完成 (耗时 3.2s, 重试 0 次)
==================================================
📝 Agent 回复:
已在沙箱工作区创建 hello.txt，内容为 "Hello World"。
==================================================
```

#### 特殊命令

| 命令 | 功能 |
|------|------|
| `/clear` | 清空对话历史 |
| `/history` | 查看对话摘要 |
| `/help` | 显示帮助信息 |
| `/exit` | 退出程序 |

#### 使用示例

```bash
# 文件操作
🧑 你: 列出当前目录下的所有文件

# 系统查询
🧑 你: 查看系统内存使用情况

# 多轮对话（Agent 会记住上下文）
🧑 你: 创建一个 config.json，内容为 {"port": 8080}
🧑 你: 把刚才那个文件重命名为 settings.json
🧑 你: 也删掉那个文件
```

### 2. 定时巡检任务

适合通过 crontab 或 systemd timer 定期执行系统巡检。

```bash
python3 patrol_task.py
```

执行后会检查以下项目并将结果写入 `sandbox_workspace/patrol_log.txt`：
- CPU 负载（1/5/15 分钟）
- 内存使用率
- 磁盘使用率
- 僵尸进程检测
- 负载是否超标

#### 配置 crontab 定时执行

```bash
# 每 30 分钟执行一次巡检
crontab -e
# 添加以下行：
*/30 * * * * cd /path/to/-AutoScript-Agent && /path/to/-AutoScript-Agent/LM_env/bin/python patrol_task.py >> patrol_cron.log 2>&1
```

### 3. 生成答辩 PPT

```bash
node make_ppt.js
```

执行后生成 `答辩PPT.pptx`，包含 9 张幻灯片。

---

## 测试

所有测试用例位于 `tests/` 目录下，直接运行即可。

### 运行全部测试

```bash
# 确保在项目根目录，且已激活虚拟环境
python3 tests/test_write_file.py       # 写文件测试（3 个用例）
python3 tests/test_move_file.py        # 移动/重命名文件测试（2 个用例）
python3 tests/test_execute_file.py     # Shell 执行测试（6 个用例）
python3 tests/test_shell_safety.py     # 安全机制测试（5 个用例）
python3 tests/test_organize_files.py   # 文件组织测试（1 个用例）
```

### 一键运行所有测试

```bash
for test in tests/test_*.py; do
    echo "========== 运行: $test =========="
    python3 "$test"
    echo ""
done
```

### 测试内容概览

| 测试文件 | 用例数 | 覆盖内容 |
|----------|--------|----------|
| `test_write_file.py` | 3 | 写文本文件、写 JSON、安全检查 |
| `test_move_file.py` | 2 | 移动文件、重命名文件 |
| `test_execute_file.py` | 6 | 列出文件、系统信息、Shell 执行、超时处理、错误处理、文件不存在 |
| `test_shell_safety.py` | 5 | 安全命令白名单、危险命令拦截、风险等级、错误重试、安全适配 |
| `test_organize_files.py` | 1 | Agent 自主编写并执行文件分类脚本 |

---

## 项目结构

```
-AutoScript-Agent/
├── agent/                      # 核心包
│   ├── __init__.py             # 包导出
│   ├── agent.py                # LangChain Agent 主控
│   ├── chat_model.py           # Qwen ChatModel 封装
│   ├── tools.py                # 6 个 LangChain 工具
│   ├── safety_checker.py       # 安全审查器
│   ├── script_executor.py      # 脚本执行器（沙箱+超时）
│   └── script_generator.py     # 脚本生成器
├── tests/                      # 测试套件
│   ├── test_write_file.py
│   ├── test_move_file.py
│   ├── test_execute_file.py
│   ├── test_shell_safety.py
│   └── test_organize_files.py
├── sandbox_workspace/          # 沙箱工作区（运行时文件操作）
├── agent_cli.py                # 🚀 交互式 CLI 入口
├── patrol_task.py              # 🔄 定时巡检入口
├── qwen_chat.py                # Qwen API 底层调用
├── make_ppt.js                 # PPT 生成脚本
├── requirements.txt            # Python 依赖
├── package.json                # Node.js 依赖
└── .gitignore
```

---

## 可用工具

Agent 拥有以下 6 个工具，可自主选择调用：

| 工具 | 功能 | 示例 |
|------|------|------|
| `write_file` | 创建或覆盖文件 | `write_file("config.py", content)` |
| `read_file` | 读取文件内容 | `read_file("config.py")` |
| `list_files` | 列出目录文件 | `list_files(".")` |
| `move_file` | 移动或重命名 | `move_file("a.txt", "b.txt")` |
| `delete_file` | 删除文件 | `delete_file("temp.log")` |
| `execute_shell` | 执行安全 Shell 命令 | `execute_shell("df -h")` |

---

## 安全机制

系统内置多层安全防护：

1. **安全审查器** (`safety_checker.py`)
   - 正则 + AST 语法树分析
   - 识别并拦截危险操作（`sudo`, `rm -rf /`, `chmod 777 /` 等）
   - 风险等级评估

2. **沙箱执行器** (`script_executor.py`)
   - 所有脚本/命令在沙箱工作区内执行
   - 超时自动终止（默认 60 秒）
   - 输出自动截断（防止海量输出）

3. **工作区隔离**
   - 默认工作区为 `sandbox_workspace/`
   - 文件操作被限定在工作区范围内

4. **错误重试**
   - 最多 3 次自动重试
   - 指数退避（2s → 4s → 8s）
   - 区分瞬时错误与逻辑错误

---

## 常见问题

### Q: 运行时提示 `ModuleNotFoundError: No module named 'langchain'`

A: 请确保已激活虚拟环境并安装了依赖：
```bash
source LM_env/bin/activate
pip install -r requirements.txt
```

### Q: 提示 API Key 无效或鉴权失败

A: 检查是否正确设置了 `DASHSCOPE_API_KEY` 环境变量，或确认代码中硬编码的 Key 有效。

### Q: 测试运行失败

A: 测试依赖 API 调用，请确保：
1. 网络可访问 `dashscope.aliyuncs.com`
2. API Key 有效且有余额
3. 在项目根目录运行测试脚本

### Q: 可以在其他 Linux 发行版上运行吗？

A: 可以。Agent 的核心功能是跨平台的。但部分 Shell 命令（如 `apt` 包管理）是 Ubuntu 特有的，Agent 在这些场景下的行为可能不同。

### Q: 支持其他大模型吗？

A: 当前仅支持通义千问 (Qwen)。如需切换模型，可修改 `agent/chat_model.py` 中的 API 地址和模型参数。

---

## 📄 许可证

本项目仅用于学习和研究目的。

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)
