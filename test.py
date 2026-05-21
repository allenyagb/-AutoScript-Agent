import sys
import platform

def main():
    print("=" * 40)
    print("🎉 恭喜！Python 脚本运行成功！")
    print("=" * 40)

    # 获取系统信息
    print(f"当前操作系统: {platform.system()} {platform.release()}")
    print(f"Python 版本: {sys.version}")
    print(f"当前工作目录: /home/yg/LinuxMind")

    # 简单的计算测试
    a = 100
    b = 200
    print(f"\n简单计算测试: {a} + {b} = {a + b}")
    print("=" * 40)

if __name__ == "__main__":
    main()
    