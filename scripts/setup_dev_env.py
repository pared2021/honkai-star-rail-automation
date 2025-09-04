#!/usr/bin/env python3
"""
开发环境设置脚本

该脚本帮助新开发者快速搭建完整的开发环境，包括：
- 检查Python版本
- 安装依赖包
- 配置预提交钩子
- 验证工具配置
- 运行初始化检查

使用方法:
    python scripts/setup_dev_env.py [--force] [--skip-hooks] [--skip-tests]
"""

import argparse
import os
from pathlib import Path
import subprocess
import sys
from typing import List, Tuple


class Colors:
    """终端颜色常量"""

    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    BOLD = "\033[1m"
    END = "\033[0m"


class DevEnvSetup:
    """开发环境设置类"""

    def __init__(
        self, force: bool = False, skip_hooks: bool = False, skip_tests: bool = False
    ):
        self.force = force
        self.skip_hooks = skip_hooks
        self.skip_tests = skip_tests
        self.project_root = Path(__file__).parent.parent
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def print_step(self, message: str) -> None:
        """打印步骤信息"""
        print(f"{Colors.BLUE}[步骤]{Colors.END} {message}")

    def print_success(self, message: str) -> None:
        """打印成功信息"""
        print(f"{Colors.GREEN}[成功]{Colors.END} {message}")

    def print_warning(self, message: str) -> None:
        """打印警告信息"""
        print(f"{Colors.YELLOW}[警告]{Colors.END} {message}")
        self.warnings.append(message)

    def print_error(self, message: str) -> None:
        """打印错误信息"""
        print(f"{Colors.RED}[错误]{Colors.END} {message}")
        self.errors.append(message)

    def run_command(
        self, command: List[str], check: bool = True, capture_output: bool = False
    ) -> Tuple[bool, str]:
        """运行命令"""
        try:
            if capture_output:
                result = subprocess.run(
                    command, capture_output=True, text=True, check=check
                )
                return True, result.stdout.strip()
            else:
                subprocess.run(command, check=check)
                return True, ""
        except subprocess.CalledProcessError as e:
            error_msg = f"命令执行失败: {' '.join(command)}"
            if capture_output and e.stderr:
                error_msg += f"\n错误输出: {e.stderr}"
            self.print_error(error_msg)
            return False, ""
        except FileNotFoundError:
            self.print_error(f"命令未找到: {command[0]}")
            return False, ""

    def check_python_version(self) -> bool:
        """检查Python版本"""
        self.print_step("检查Python版本")

        version = sys.version_info
        if version.major != 3 or version.minor < 9:
            self.print_error(
                f"需要Python 3.9+，当前版本: {version.major}.{version.minor}.{version.micro}"
            )
            return False

        self.print_success(
            f"Python版本检查通过: {version.major}.{version.minor}.{version.micro}"
        )
        return True

    def check_git(self) -> bool:
        """检查Git是否可用"""
        self.print_step("检查Git")

        success, _ = self.run_command(["git", "--version"], capture_output=True)
        if not success:
            self.print_error("Git未安装或不可用")
            return False

        self.print_success("Git检查通过")
        return True

    def install_dependencies(self) -> bool:
        """安装依赖包"""
        self.print_step("安装项目依赖")

        # 升级pip
        success, _ = self.run_command(
            [sys.executable, "-m", "pip", "install", "--upgrade", "pip"]
        )
        if not success:
            return False

        # 安装主要依赖
        requirements_file = self.project_root / "requirements.txt"
        if requirements_file.exists():
            success, _ = self.run_command(
                [sys.executable, "-m", "pip", "install", "-r", str(requirements_file)]
            )
            if not success:
                return False
        else:
            self.print_warning("requirements.txt文件不存在")

        # 安装开发依赖
        dev_requirements_file = self.project_root / "requirements-dev.txt"
        if dev_requirements_file.exists():
            success, _ = self.run_command(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "install",
                    "-r",
                    str(dev_requirements_file),
                ]
            )
            if not success:
                return False
        else:
            self.print_warning("requirements-dev.txt文件不存在")

        self.print_success("依赖安装完成")
        return True

    def setup_pre_commit_hooks(self) -> bool:
        """设置预提交钩子"""
        if self.skip_hooks:
            self.print_step("跳过预提交钩子设置")
            return True

        self.print_step("设置预提交钩子")

        # 检查配置文件是否存在
        config_file = self.project_root / ".pre-commit-config.yaml"
        if not config_file.exists():
            self.print_warning(".pre-commit-config.yaml文件不存在")
            return True

        # 安装预提交钩子
        success, _ = self.run_command(["pre-commit", "install"])
        if not success:
            return False

        success, _ = self.run_command(
            ["pre-commit", "install", "--hook-type", "commit-msg"]
        )
        if not success:
            return False

        self.print_success("预提交钩子设置完成")
        return True

    def verify_tools(self) -> bool:
        """验证开发工具配置"""
        self.print_step("验证开发工具配置")

        tools = [
            ("black", ["black", "--version"]),
            ("isort", ["isort", "--version"]),
            ("flake8", ["flake8", "--version"]),
            ("pylint", ["pylint", "--version"]),
            ("mypy", ["mypy", "--version"]),
            ("pytest", ["pytest", "--version"]),
        ]

        all_success = True
        for tool_name, command in tools:
            success, output = self.run_command(
                command, check=False, capture_output=True
            )
            if success:
                self.print_success(
                    f"{tool_name}: {output.split()[0] if output else '已安装'}"
                )
            else:
                self.print_warning(f"{tool_name}: 未安装或配置错误")
                all_success = False

        return all_success

    def verify_config_files(self) -> bool:
        """验证配置文件"""
        self.print_step("验证配置文件")

        config_files = [
            ".flake8",
            ".pylintrc",
            "mypy.ini",
            "pyproject.toml",
            ".pre-commit-config.yaml",
        ]

        all_exist = True
        for config_file in config_files:
            file_path = self.project_root / config_file
            if file_path.exists():
                self.print_success(f"配置文件存在: {config_file}")
            else:
                self.print_warning(f"配置文件缺失: {config_file}")
                all_exist = False

        return all_exist

    def run_initial_checks(self) -> bool:
        """运行初始检查"""
        if self.skip_tests:
            self.print_step("跳过初始检查")
            return True

        self.print_step("运行初始检查")

        # 运行代码格式化
        self.print_step("格式化代码")
        success, _ = self.run_command(
            [sys.executable, "scripts/code_quality_check.py", "--fix"]
        )
        if not success:
            self.print_warning("代码格式化失败")

        # 运行基本的代码检查
        self.print_step("运行代码检查")
        success, _ = self.run_command(
            [sys.executable, "scripts/code_quality_check.py", "--skip", "pylint"]
        )
        if not success:
            self.print_warning("代码检查发现问题")

        # 运行测试
        self.print_step("运行测试")
        success, _ = self.run_command(
            [sys.executable, "scripts/test_runner.py", "run", "--no-coverage"]
        )
        if not success:
            self.print_warning("测试运行失败")

        return True

    def create_dev_scripts(self) -> bool:
        """创建开发便捷脚本"""
        self.print_step("创建开发便捷脚本")

        # 创建快速检查脚本
        quick_check_script = self.project_root / "quick_check.py"
        quick_check_content = '''#!/usr/bin/env python3
"""快速代码检查脚本"""
import subprocess
import sys

def main():
    print("运行快速代码检查...")
    
    # 格式化代码
    subprocess.run([sys.executable, "scripts/code_quality_check.py", "--fix"])
    
    # 运行基本检查
    result = subprocess.run([sys.executable, "scripts/code_quality_check.py", "--skip", "pylint"])
    
    if result.returncode == 0:
        print("✅ 快速检查通过")
    else:
        print("❌ 快速检查失败")
        sys.exit(1)

if __name__ == "__main__":
    main()
'''

        try:
            with open(quick_check_script, "w", encoding="utf-8") as f:
                f.write(quick_check_content)
            self.print_success("创建快速检查脚本: quick_check.py")
        except Exception as e:
            self.print_warning(f"创建快速检查脚本失败: {e}")

        return True

    def print_summary(self) -> None:
        """打印设置摘要"""
        print(f"\n{Colors.BOLD}=== 开发环境设置摘要 ==={Colors.END}")

        if not self.errors:
            self.print_success("开发环境设置成功完成！")
        else:
            self.print_error("开发环境设置过程中遇到错误")
            for error in self.errors:
                print(f"  - {error}")

        if self.warnings:
            print(f"\n{Colors.YELLOW}警告:{Colors.END}")
            for warning in self.warnings:
                print(f"  - {warning}")

        print(f"\n{Colors.BOLD}下一步:{Colors.END}")
        print("1. 运行 'python quick_check.py' 进行快速检查")
        print("2. 运行 'python scripts/quality_gate.py' 进行完整质量检查")
        print("3. 查看 'Makefile' 了解更多开发命令")
        print("4. 阅读开发规范文档: .trae/documents/开发规范和治理文档.md")

    def setup(self) -> bool:
        """执行完整的开发环境设置"""
        print(f"{Colors.BOLD}=== 星铁助手开发环境设置 ==={Colors.END}")
        print(f"项目根目录: {self.project_root}")
        print()

        steps = [
            self.check_python_version,
            self.check_git,
            self.install_dependencies,
            self.setup_pre_commit_hooks,
            self.verify_tools,
            self.verify_config_files,
            self.create_dev_scripts,
            self.run_initial_checks,
        ]

        for step in steps:
            if not step():
                if not self.force:
                    self.print_error("设置过程中断，使用 --force 参数强制继续")
                    return False
                else:
                    self.print_warning("强制模式：忽略错误继续")

        self.print_summary()
        return len(self.errors) == 0


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="开发环境设置脚本")
    parser.add_argument("--force", action="store_true", help="强制继续，即使遇到错误")
    parser.add_argument("--skip-hooks", action="store_true", help="跳过预提交钩子设置")
    parser.add_argument("--skip-tests", action="store_true", help="跳过初始测试")

    args = parser.parse_args()

    setup = DevEnvSetup(
        force=args.force, skip_hooks=args.skip_hooks, skip_tests=args.skip_tests
    )

    success = setup.setup()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
