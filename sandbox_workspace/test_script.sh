#!/bin/bash
# 测试 Shell 脚本
echo "========================================="
echo "Shell 脚本执行测试"
echo "========================================="
echo "当前用户: $(whoami)"
echo "当前目录: $(pwd)"
echo "脚本路径: $0"
echo "参数个数: $#"
echo "所有参数: $@"
echo ""
echo "执行简单计算..."
echo "100 + 200 = $((100 + 200))"
echo ""
echo "列出当前目录文件:"
ls -la
echo ""
echo "✅ Shell 脚本执行成功!"
