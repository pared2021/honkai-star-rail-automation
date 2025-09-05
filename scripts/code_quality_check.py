#!/usr/bin/env python3
"""
代码质量检查脚本

集成flake8、pylint、mypy、black、isort等工具，提供统一的代码质量检查入口。
"""

import argparse
import json
from pathlib import Path
import subprocess
import sys
import time
from typing import List, Optional, Tuple


class CodeQualityChecker:
    """代码质量检查器"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.src_dir = project_root / "src"
        self.results = {}

    def run_command(self, cmd: List[str], description: str) -> Tuple[bool, str, str]:
        """运行命令并返回结果"""
        print(f"\n🔍 {description}...")
        print(f"执行命令: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300,  # 5分钟超时
            )

            success = result.returncode == 0
            status = "✅ 通过" if success else "❌ 失败"
            print(f"结果: {status}")

            if result.stdout:
                print(f"输出:\n{result.stdout}")
            if result.stderr:
                print(f"错误:\n{result.stderr}")

            return success, result.stdout, result.stderr

        except subprocess.TimeoutExpired:
            print("❌ 命令执行超时")
            return False, "", "命令执行超时"
        except Exception as e:
            print(f"❌ 命令执行失败: {e}")
            return False, "", str(e)

    def check_black(self, fix: bool = False) -> bool:
        """检查代码格式化"""
        cmd = ["python", "-m", "black"]
        if not fix:
            cmd.append("--check")
        cmd.extend(["--diff", str(self.src_dir)])

        success, stdout, stderr = self.run_command(
            cmd, "检查代码格式化 (black)" if not fix else "修复代码格式化 (black)"
        )

        self.results["black"] = {"success": success, "output": stdout, "error": stderr}

        return success

    def check_isort(self, fix: bool = False) -> bool:
        """检查导入排序"""
        cmd = ["python", "-m", "isort"]
        if not fix:
            cmd.append("--check-only")
        cmd.extend(["--diff", str(self.src_dir)])

        success, stdout, stderr = self.run_command(
            cmd, "检查导入排序 (isort)" if not fix else "修复导入排序 (isort)"
        )

        self.results["isort"] = {"success": success, "output": stdout, "error": stderr}

        return success

    def check_flake8(self) -> bool:
        """检查代码风格"""
        cmd = [
            "python", "-m", "flake8", 
            str(self.src_dir),
            "--max-line-length=88",
            "--extend-ignore=E203,W503,D400"
        ]

        success, stdout, stderr = self.run_command(cmd, "检查代码风格 (flake8)")

        self.results["flake8"] = {"success": success, "output": stdout, "error": stderr}

        return success

    def check_pylint(self) -> bool:
        """检查代码质量"""
        cmd = ["python", "-m", "pylint", str(self.src_dir)]

        success, stdout, stderr = self.run_command(cmd, "检查代码质量 (pylint)")

        # pylint的返回码不是0不一定表示失败，需要检查分数
        score = self._extract_pylint_score(stdout)
        success = score >= 8.0 if score is not None else success

        self.results["pylint"] = {
            "success": success,
            "output": stdout,
            "error": stderr,
            "score": score,
        }

        return success

    def check_mypy(self) -> bool:
        """检查类型注解"""
        cmd = ["python", "-m", "mypy", str(self.src_dir), "--ignore-missing-imports"]

        success, stdout, stderr = self.run_command(cmd, "检查类型注解 (mypy)")

        self.results["mypy"] = {"success": success, "output": stdout, "error": stderr}

        return success

    def _extract_pylint_score(self, output: str) -> Optional[float]:
        """从pylint输出中提取分数"""
        try:
            for line in output.split("\n"):
                if "Your code has been rated at" in line:
                    # 提取分数，格式如: "Your code has been rated at 8.50/10"
                    score_part = line.split("rated at")[1].split("/")[0].strip()
                    return float(score_part)
        except (IndexError, ValueError):
            pass
        return None

    def generate_report(self) -> str:
        """生成检查报告"""
        report = ["\n" + "=" * 60]
        report.append("📊 代码质量检查报告")
        report.append("=" * 60)

        total_checks = len(self.results)
        passed_checks = sum(1 for r in self.results.values() if r["success"])

        report.append(f"\n总检查项: {total_checks}")
        report.append(f"通过检查: {passed_checks}")
        report.append(f"失败检查: {total_checks - passed_checks}")
        report.append(f"通过率: {passed_checks/total_checks*100:.1f}%")

        report.append("\n📋 详细结果:")
        report.append("-" * 40)

        for tool, result in self.results.items():
            status = "✅ 通过" if result["success"] else "❌ 失败"
            report.append(f"{tool.upper():10} | {status}")

            if tool == "pylint" and "score" in result and result["score"]:
                report.append(f"{'':10} | 分数: {result['score']:.2f}/10")

        report.append("-" * 40)

        if passed_checks == total_checks:
            report.append("\n🎉 所有检查都通过了！代码质量良好。")
        else:
            report.append("\n⚠️  存在代码质量问题，请查看上述详细信息。")

        report.append("\n💡 建议:")
        if not self.results.get("black", {}).get("success", True):
            report.append("  - 运行 'python -m black src' 修复格式问题")
        if not self.results.get("isort", {}).get("success", True):
            report.append("  - 运行 'python -m isort src' 修复导入排序")
        if not self.results.get("flake8", {}).get("success", True):
            report.append("  - 查看flake8输出，修复代码风格问题")
        if not self.results.get("mypy", {}).get("success", True):
            report.append("  - 添加类型注解，修复mypy报告的问题")
        if not self.results.get("pylint", {}).get("success", True):
            report.append("  - 查看pylint输出，改进代码质量")

        return "\n".join(report)

    def save_report(self, report: str, format: str = "txt") -> Path:
        """保存报告到文件"""
        timestamp = time.strftime("%Y%m%d_%H%M%S")

        if format == "json":
            report_file = self.project_root / f"quality_report_{timestamp}.json"
            with open(report_file, "w", encoding="utf-8") as f:
                json.dump(self.results, f, indent=2, ensure_ascii=False)
        else:
            report_file = self.project_root / f"quality_report_{timestamp}.txt"
            with open(report_file, "w", encoding="utf-8") as f:
                f.write(report)

        return report_file

    def run_all_checks(self, fix: bool = False, skip_tools: List[str] = None) -> bool:
        """运行所有检查"""
        skip_tools = skip_tools or []

        print("🚀 开始代码质量检查...")
        print(f"项目根目录: {self.project_root}")
        print(f"源代码目录: {self.src_dir}")

        all_passed = True

        # 按顺序执行检查
        checks = [
            ("black", lambda: self.check_black(fix)),
            ("isort", lambda: self.check_isort(fix)),
            ("flake8", self.check_flake8),
            ("mypy", self.check_mypy),
            ("pylint", self.check_pylint),
        ]

        for tool_name, check_func in checks:
            if tool_name in skip_tools:
                print(f"\n⏭️  跳过 {tool_name} 检查")
                continue

            try:
                success = check_func()
                if not success:
                    all_passed = False
            except Exception as e:
                print(f"\n❌ {tool_name} 检查失败: {e}")
                all_passed = False

        return all_passed


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="代码质量检查工具")
    parser.add_argument(
        "--fix", action="store_true", help="自动修复可修复的问题（black, isort）"
    )
    parser.add_argument(
        "--skip",
        nargs="*",
        choices=["black", "isort", "flake8", "mypy", "pylint"],
        help="跳过指定的检查工具",
    )
    parser.add_argument(
        "--report-format", choices=["txt", "json"], default="txt", help="报告格式"
    )
    parser.add_argument("--save-report", action="store_true", help="保存报告到文件")

    args = parser.parse_args()

    # 确定项目根目录
    project_root = Path(__file__).parent.parent
    if not (project_root / "src").exists():
        print("❌ 错误: 找不到src目录")
        sys.exit(1)

    # 创建检查器并运行检查
    checker = CodeQualityChecker(project_root)

    try:
        all_passed = checker.run_all_checks(fix=args.fix, skip_tools=args.skip or [])

        # 生成报告
        report = checker.generate_report()
        print(report)

        # 保存报告
        if args.save_report:
            report_file = checker.save_report(report, args.report_format)
            print(f"\n📄 报告已保存到: {report_file}")

        # 设置退出码
        sys.exit(0 if all_passed else 1)

    except KeyboardInterrupt:
        print("\n\n⚠️  检查被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 检查过程中发生错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
