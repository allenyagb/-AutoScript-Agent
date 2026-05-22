#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试 Python 脚本"""
import os
import sys
import platform

print("=" * 50)
print("Python 脚本执行测试")
print("=" * 50)
print(f"Python 版本: {sys.version}")
print(f"操作系统: {platform.system()} {platform.release()}")
print(f"当前目录: {os.getcwd()}")
print(f"脚本路径: {__file__}")
print(f"工作区: {os.environ.get('AGENT_WORKSPACE', '未设置')}")
print()

# 执行一些操作
workspace = os.environ.get("AGENT_WORKSPACE", ".")
test_file = os.path.join(workspace, "exec_test_result.txt")

# 写一个文件
with open(test_file, 'w') as f:
    f.write("由 Python 脚本创建的文件\n")
    f.write(f"创建时间: {__import__('datetime').datetime.now()}\n")

print(f"已创建文件: {test_file}")

# 读取文件列表
print("\n当前目录文件列表:")
for item in sorted(os.listdir(workspace)):
    full_path = os.path.join(workspace, item)
    if os.path.isfile(full_path):
        size = os.path.getsize(full_path)
        print(f"  📄 {item} ({size} bytes)")
    elif os.path.isdir(full_path):
        print(f"  📁 {item}/")

print("\n✅ Python 脚本执行成功!")
