#!/usr/bin/env python3
"""
测试运行器和覆盖率检查脚本

提供统一的测试执行和覆盖率检查功能，支持多种测试模式和报告格式。
"""

import argparse
import json
from pathlib import Path
import subprocess
import sys
from typing import Any, Dict, List, Optional
import xml.etree.ElementTree as ET


class TestRunner:
    """测试运行器"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.src_dir = project_root / "src"
        self.tests_dir = project_root / "tests"
        self.reports_dir = project_root / "reports"

        # 确保报告目录存在
        self.reports_dir.mkdir(exist_ok=True)

        # 测试配置
        self.pytest_config = {
            "testpaths": ["tests", "src"],
            "python_files": ["test_*.py", "*_test.py"],
            "python_classes": ["Test*"],
            "python_functions": ["test_*"],
            "addopts": [
                "-v",
                "--tb=short",
                "--strict-markers",
                "--disable-warnings",
                "--color=yes",
            ],
        }

        # 覆盖率配置
        self.coverage_config = {
            "source": ["src"],
            "omit": [
                "*/tests/*",
                "*/test_*",
                "*/__pycache__/*",
                "*/venv/*",
                "*/env/*",
                "*/.tox/*",
            ],
            "branch": True,
            "show_missing": True,
            "skip_covered": False,
            "precision": 2,
        }

    def check_dependencies(self) -> bool:
        """检查测试依赖是否安装"""
        required_packages = ["pytest", "coverage", "pytest-cov"]
        missing_packages = []

        for package in required_packages:
            try:
                subprocess.run(
                    [sys.executable, "-c", f'import {package.replace("-", "_")}'],
                    check=True,
                    capture_output=True,
                )
            except subprocess.CalledProcessError:
                missing_packages.append(package)

        if missing_packages:
            print(f"❌ 缺少测试依赖: {', '.join(missing_packages)}")
            print(f"请运行: pip install {' '.join(missing_packages)}")
            return False

        print("✅ 测试依赖检查通过")
        return True

    def discover_tests(self) -> List[Path]:
        """发现测试文件"""
        test_files = []

        # 在tests目录中查找
        if self.tests_dir.exists():
            test_files.extend(self.tests_dir.rglob("test_*.py"))
            test_files.extend(self.tests_dir.rglob("*_test.py"))

        # 在src目录中查找
        if self.src_dir.exists():
            test_files.extend(self.src_dir.rglob("test_*.py"))
            test_files.extend(self.src_dir.rglob("*_test.py"))

        return sorted(test_files)

    def run_tests(
        self,
        test_path: Optional[str] = None,
        coverage: bool = True,
        verbose: bool = True,
        fail_fast: bool = False,
        markers: Optional[str] = None,
        output_format: str = "terminal",
    ) -> bool:
        """运行测试"""
        print("🧪 开始运行测试...")

        # 构建pytest命令
        cmd = [sys.executable, "-m", "pytest"]

        # 添加测试路径
        if test_path:
            cmd.append(test_path)
        else:
            # 使用默认测试路径
            if self.tests_dir.exists():
                cmd.append(str(self.tests_dir))
            if self.src_dir.exists():
                cmd.append(str(self.src_dir))

        # 添加选项
        if verbose:
            cmd.append("-v")

        if fail_fast:
            cmd.append("-x")

        if markers:
            cmd.extend(["-m", markers])

        # 添加覆盖率选项
        if coverage:
            cmd.extend(
                [
                    "--cov=src",
                    "--cov-branch",
                    "--cov-report=term-missing",
                    f"--cov-report=html:{self.reports_dir}/coverage_html",
                    f"--cov-report=xml:{self.reports_dir}/coverage.xml",
                    f"--cov-report=json:{self.reports_dir}/coverage.json",
                ]
            )

        # 添加输出格式
        if output_format == "junit":
            cmd.append(f"--junit-xml={self.reports_dir}/junit.xml")
        elif output_format == "json":
            cmd.append(f"--json-report={self.reports_dir}/test_report.json")

        # 设置工作目录
        cwd = self.project_root

        print(f"执行命令: {' '.join(cmd)}")
        print(f"工作目录: {cwd}")

        try:
            result = subprocess.run(cmd, cwd=cwd, capture_output=False, text=True)

            success = result.returncode == 0

            if success:
                print("\n✅ 测试执行成功")
            else:
                print("\n❌ 测试执行失败")

            return success

        except Exception as e:
            print(f"❌ 测试执行出错: {e}")
            return False

    def run_coverage_only(self, test_path: Optional[str] = None) -> bool:
        """只运行覆盖率检查"""
        print("📊 运行覆盖率检查...")

        # 先运行测试收集覆盖率数据
        cmd_test = [sys.executable, "-m", "coverage", "run", "-m", "pytest"]

        if test_path:
            cmd_test.append(test_path)
        else:
            if self.tests_dir.exists():
                cmd_test.append(str(self.tests_dir))

        try:
            # 运行测试收集覆盖率
            result = subprocess.run(
                cmd_test, cwd=self.project_root, capture_output=True, text=True
            )

            if result.returncode != 0:
                print(f"❌ 覆盖率数据收集失败: {result.stderr}")
                return False

            # 生成覆盖率报告
            self._generate_coverage_reports()

            return True

        except Exception as e:
            print(f"❌ 覆盖率检查出错: {e}")
            return False

    def _generate_coverage_reports(self) -> None:
        """生成覆盖率报告"""
        reports = [
            ("report", "终端报告"),
            ("html", f"HTML报告 -> {self.reports_dir}/htmlcov"),
            ("xml", f"XML报告 -> {self.reports_dir}/coverage.xml"),
            ("json", f"JSON报告 -> {self.reports_dir}/coverage.json"),
        ]

        for report_type, description in reports:
            try:
                cmd = [sys.executable, "-m", "coverage", report_type]

                if report_type == "html":
                    cmd.extend(["-d", str(self.reports_dir / "htmlcov")])
                elif report_type == "xml":
                    cmd.extend(["-o", str(self.reports_dir / "coverage.xml")])
                elif report_type == "json":
                    cmd.extend(["-o", str(self.reports_dir / "coverage.json")])

                result = subprocess.run(
                    cmd,
                    cwd=self.project_root,
                    capture_output=(report_type != "report"),
                    text=True,
                )

                if result.returncode == 0:
                    print(f"✅ {description}")
                else:
                    print(f"⚠️  {description} 生成失败")

            except Exception as e:
                print(f"⚠️  生成 {description} 时出错: {e}")

    def get_coverage_summary(self) -> Optional[Dict[str, Any]]:
        """获取覆盖率摘要"""
        coverage_json_path = self.reports_dir / "coverage.json"

        if not coverage_json_path.exists():
            return None

        try:
            with open(coverage_json_path, "r", encoding="utf-8") as f:
                coverage_data = json.load(f)

            summary = coverage_data.get("totals", {})

            return {
                "covered_lines": summary.get("covered_lines", 0),
                "num_statements": summary.get("num_statements", 0),
                "percent_covered": summary.get("percent_covered", 0),
                "missing_lines": summary.get("missing_lines", 0),
                "excluded_lines": summary.get("excluded_lines", 0),
                "num_branches": summary.get("num_branches", 0),
                "num_partial_branches": summary.get("num_partial_branches", 0),
                "covered_branches": summary.get("covered_branches", 0),
                "percent_covered_display": summary.get("percent_covered_display", "0%"),
            }

        except Exception as e:
            print(f"⚠️  读取覆盖率摘要失败: {e}")
            return None

    def check_coverage_threshold(self, threshold: float = 80.0) -> bool:
        """检查覆盖率是否达到阈值"""
        summary = self.get_coverage_summary()

        if not summary:
            print("⚠️  无法获取覆盖率数据")
            return False

        coverage_percent = summary["percent_covered"]

        if coverage_percent >= threshold:
            print(f"✅ 覆盖率 {coverage_percent:.1f}% 达到阈值 {threshold}%")
            return True
        else:
            print(f"❌ 覆盖率 {coverage_percent:.1f}% 未达到阈值 {threshold}%")
            return False

    def create_test_template(self, module_path: str) -> Path:
        """为指定模块创建测试模板"""
        module_path_obj = Path(module_path)

        if not module_path_obj.exists():
            raise FileNotFoundError(f"模块文件不存在: {module_path}")

        # 确定测试文件路径
        if module_path_obj.is_relative_to(self.src_dir):
            relative_path = module_path_obj.relative_to(self.src_dir)
        else:
            relative_path = module_path_obj.relative_to(self.project_root)

        test_file_name = f"test_{relative_path.stem}.py"
        test_file_path = self.tests_dir / relative_path.parent / test_file_name

        # 确保测试目录存在
        test_file_path.parent.mkdir(parents=True, exist_ok=True)

        # 生成测试模板
        module_name = relative_path.stem
        import_path = (
            str(relative_path.with_suffix("")).replace("/", ".").replace("\\", ".")
        )

        template = f'''#!/usr/bin/env python3
"""
{module_name} 模块的测试用例

测试文件: {relative_path}
生成时间: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# 添加src目录到Python路径
src_dir = Path(__file__).parent.parent / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

# 导入被测试的模块
try:
    from {import_path} import *
except ImportError as e:
    pytest.skip(f"无法导入模块 {import_path}: {{e}}", allow_module_level=True)


class Test{module_name.title()}:
    """测试 {module_name} 模块"""
    
    def setup_method(self):
        """每个测试方法执行前的设置"""
        pass
    
    def teardown_method(self):
        """每个测试方法执行后的清理"""
        pass
    
    def test_module_import(self):
        """测试模块是否可以正常导入"""
        # 这个测试确保模块可以被正确导入
        assert True  # 如果能到这里说明导入成功
    
    # TODO: 添加具体的测试方法
    # 示例:
    # def test_function_name(self):
    #     """测试 function_name 函数"""
    #     # 准备测试数据
    #     input_data = "test_input"
    #     expected_output = "expected_result"
    #     
    #     # 执行测试
    #     result = function_name(input_data)
    #     
    #     # 验证结果
    #     assert result == expected_output
    
    @pytest.mark.parametrize("input_value,expected", [
        # TODO: 添加参数化测试数据
        # ("input1", "expected1"),
        # ("input2", "expected2"),
    ])
    def test_parametrized_example(self, input_value, expected):
        """参数化测试示例"""
        # TODO: 实现参数化测试逻辑
        pass
    
    def test_error_handling(self):
        """测试错误处理"""
        # TODO: 测试异常情况
        # with pytest.raises(ExpectedException):
        #     function_that_should_raise_exception()
        pass
    
    @patch('module.dependency')
    def test_with_mock(self, mock_dependency):
        """使用Mock的测试示例"""
        # TODO: 配置mock对象
        # mock_dependency.return_value = "mocked_result"
        # 
        # # 执行测试
        # result = function_using_dependency()
        # 
        # # 验证mock被调用
        # mock_dependency.assert_called_once()
        # assert result == "expected_result"
        pass


if __name__ == "__main__":
    # 运行当前文件的测试
    pytest.main(["-v", __file__])
'''

        # 写入测试文件
        with open(test_file_path, "w", encoding="utf-8") as f:
            f.write(template)

        print(f"✅ 测试模板已创建: {test_file_path}")
        return test_file_path

    def generate_test_summary(self) -> str:
        """生成测试摘要报告"""
        test_files = self.discover_tests()
        coverage_summary = self.get_coverage_summary()

        report = ["\n" + "=" * 50]
        report.append("🧪 测试摘要报告")
        report.append("=" * 50)

        # 测试文件统计
        report.append(f"\n📊 测试文件统计:")
        report.append(f"  发现测试文件: {len(test_files)}")

        if test_files:
            report.append(f"\n📋 测试文件列表:")
            for test_file in test_files[:10]:  # 只显示前10个
                relative_path = test_file.relative_to(self.project_root)
                report.append(f"  📄 {relative_path}")

            if len(test_files) > 10:
                report.append(f"  ... 还有 {len(test_files) - 10} 个测试文件")

        # 覆盖率统计
        if coverage_summary:
            report.append(f"\n📊 覆盖率统计:")
            report.append(f"  总覆盖率: {coverage_summary['percent_covered_display']}")
            report.append(
                f"  覆盖行数: {coverage_summary['covered_lines']}/{coverage_summary['num_statements']}"
            )
            report.append(
                f"  分支覆盖: {coverage_summary['covered_branches']}/{coverage_summary['num_branches']}"
            )
            report.append(f"  缺失行数: {coverage_summary['missing_lines']}")
        else:
            report.append(f"\n⚠️  暂无覆盖率数据")

        # 报告文件
        report.append(f"\n📄 报告文件:")
        report_files = [
            ("coverage.xml", "XML覆盖率报告"),
            ("coverage.json", "JSON覆盖率报告"),
            ("htmlcov/index.html", "HTML覆盖率报告"),
            ("junit.xml", "JUnit测试报告"),
        ]

        for filename, description in report_files:
            file_path = self.reports_dir / filename
            if file_path.exists():
                report.append(f"  ✅ {description}: {file_path}")
            else:
                report.append(f"  ❌ {description}: 未生成")

        return "\n".join(report)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="测试运行器")
    parser.add_argument(
        "command",
        choices=["run", "coverage", "template", "summary", "check"],
        help="要执行的命令",
    )
    parser.add_argument("--path", help="测试路径或模块路径")
    parser.add_argument("--no-coverage", action="store_true", help="不收集覆盖率数据")
    parser.add_argument("--fail-fast", action="store_true", help="遇到第一个失败就停止")
    parser.add_argument("--markers", help="运行特定标记的测试")
    parser.add_argument(
        "--format",
        choices=["terminal", "junit", "json"],
        default="terminal",
        help="输出格式",
    )
    parser.add_argument("--threshold", type=float, default=80.0, help="覆盖率阈值")

    args = parser.parse_args()

    # 确定项目根目录
    project_root = Path(__file__).parent.parent

    # 创建测试运行器
    runner = TestRunner(project_root)

    # 检查依赖
    if not runner.check_dependencies():
        sys.exit(1)

    try:
        if args.command == "run":
            # 运行测试
            success = runner.run_tests(
                test_path=args.path,
                coverage=not args.no_coverage,
                verbose=True,
                fail_fast=args.fail_fast,
                markers=args.markers,
                output_format=args.format,
            )
            sys.exit(0 if success else 1)

        elif args.command == "coverage":
            # 只运行覆盖率检查
            success = runner.run_coverage_only(args.path)
            if success:
                runner.check_coverage_threshold(args.threshold)
            sys.exit(0 if success else 1)

        elif args.command == "template":
            # 创建测试模板
            if not args.path:
                print("❌ 请指定模块路径")
                sys.exit(1)

            runner.create_test_template(args.path)
            sys.exit(0)

        elif args.command == "summary":
            # 生成测试摘要
            summary = runner.generate_test_summary()
            print(summary)
            sys.exit(0)

        elif args.command == "check":
            # 检查覆盖率阈值
            success = runner.check_coverage_threshold(args.threshold)
            sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试执行出错: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
