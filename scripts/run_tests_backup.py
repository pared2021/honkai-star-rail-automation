#!/usr/bin/env python3
"""测试运行脚本

提供便捷的测试执行命令，支持不同类型的测试运行。
"""

import argparse
import os
from pathlib import Path
import subprocess
import sys


def run_command(cmd: list[str], description: str) -> int:
    """运行命令并返回退出码"""
    print(f"\n{'='*60}")
    print(f"🚀 {description}")
    print(f"{'='*60}")
    print(f"执行命令: {' '.join(cmd)}")
    print()

    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except KeyboardInterrupt:
        print("\n❌ 测试被用户中断")
        return 1
    except Exception as e:
        print(f"\n❌ 执行命令时出错: {e}")
        return 1


def ensure_test_dirs():
    """确保测试目录存在"""
    test_dirs = [
        "tests/logs",
        "htmlcov",
        "tests/unit",
        "tests/integration",
        "tests/performance",
    ]

    for dir_path in test_dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)


def main():
    parser = argparse.ArgumentParser(description="测试运行脚本")
    parser.add_argument(
        "test_type",
        choices=[
            "all",
            "unit",
            "integration",
            "performance",
            "fast",
            "slow",
            "coverage",
            "lint",
            "format",
        ],
        help="要运行的测试类型",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="详细输出")
    parser.add_argument("-f", "--file", help="运行特定的测试文件")
    parser.add_argument("-k", "--keyword", help="运行匹配关键字的测试")
    parser.add_argument("--no-cov", action="store_true", help="禁用覆盖率报告")
    parser.add_argument(
        "--parallel", action="store_true", help="并行运行测试（需要pytest-xdist）"
    )

    args = parser.parse_args()

    # 确保测试目录存在
    ensure_test_dirs()

    # 基础pytest命令
    base_cmd = ["python", "-m", "pytest"]

    if args.verbose:
        base_cmd.extend(["-v", "-s"])

    if args.no_cov:
        base_cmd.extend(["--no-cov"])

    if args.parallel:
        base_cmd.extend(["-n", "auto"])

    if args.file:
        base_cmd.append(args.file)

    if args.keyword:
        base_cmd.extend(["-k", args.keyword])

    exit_code = 0

    if args.test_type == "all":
        # 运行所有测试
        cmd = base_cmd + ["tests/"]
        exit_code = run_command(cmd, "运行所有测试")

    elif args.test_type == "unit":
        # 运行单元测试
        cmd = base_cmd + ["-m", "unit", "tests/unit/"]
        exit_code = run_command(cmd, "运行单元测试")

    elif args.test_type == "integration":
        # 运行集成测试
        cmd = base_cmd + ["-m", "integration", "tests/integration/"]
        exit_code = run_command(cmd, "运行集成测试")

    elif args.test_type == "performance":
        # 运行性能测试
        cmd = base_cmd + ["-m", "performance", "tests/performance/", "--no-cov"]
        exit_code = run_command(cmd, "运行性能测试")

    elif args.test_type == "fast":
        # 运行快速测试（排除慢速测试）
        cmd = base_cmd + ["-m", "not slow", "tests/"]
        exit_code = run_command(cmd, "运行快速测试")

    elif args.test_type == "slow":
        # 运行慢速测试
        cmd = base_cmd + ["-m", "slow", "tests/"]
        exit_code = run_command(cmd, "运行慢速测试")

    elif args.test_type == "coverage":
        # 生成覆盖率报告
        cmd = base_cmd + ["tests/", "--cov-report=html", "--cov-report=term"]
        exit_code = run_command(cmd, "生成覆盖率报告")

        if exit_code == 0:
            print("\n📊 覆盖率报告已生成:")
            print(f"   HTML报告: {os.path.abspath('htmlcov/index.html')}")
            print(f"   XML报告:  {os.path.abspath('coverage.xml')}")

    elif args.test_type == "lint":
        # 代码检查
        commands = [
            (["python", "-m", "flake8", "src/", "tests/"], "Flake8代码检查"),
            (["python", "-m", "mypy", "src/"], "MyPy类型检查"),
            (["python", "-m", "pylint", "src/"], "Pylint代码检查"),
        ]

        for cmd, desc in commands:
            result = run_command(cmd, desc)
            if result != 0:
                exit_code = result

    elif args.test_type == "format":
        # 代码格式化
        commands = [
            (["python", "-m", "black", "src/", "tests/"], "Black代码格式化"),
            (["python", "-m", "isort", "src/", "tests/"], "isort导入排序"),
        ]

        for cmd, desc in commands:
            result = run_command(cmd, desc)
            if result != 0:
                exit_code = result

    # 输出最终结果
    print(f"\n{'='*60}")
    if exit_code == 0:
        print("✅ 所有测试执行完成")
    else:
        print(f"❌ 测试执行失败，退出码: {exit_code}")
    print(f"{'='*60}\n")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
