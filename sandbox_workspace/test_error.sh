#!/bin/bash
set -e
echo "开始执行..."
echo "尝试执行不存在的命令..."
this_command_does_not_exist_xyz
echo "你不应该看到这行"
