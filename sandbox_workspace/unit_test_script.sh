#!/bin/bash
echo "========================================="
echo "Shell 脚本执行测试"
echo "========================================="
echo "当前用户: $(whoami)"
echo "当前目录: $(pwd)"
echo "工作区: ${AGENT_WORKSPACE:-未设置}"
echo "100 + 200 = $((100 + 200))"
echo ""
echo "工作区文件列表:"
ls -la
echo ""
echo "Shell 脚本执行成功!"
