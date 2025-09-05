#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试运行器 - 执行所有单元测试
"""

from io import StringIO
import os
import sys
import unittest

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from test_automation_controller import TestAutomationController
from test_database import TestDatabaseManager

# 导入所有测试模块
from test_task_manager import TestTaskManager
from test_task_monitor import TestTaskMonitor


class ColoredTextTestResult(unittest.TextTestResult):
    """带颜色输出的测试结果类"""

    def __init__(self, stream, descriptions, verbosity):
        super().__init__(stream, descriptions, verbosity)
        self.success_count = 0

    def addSuccess(self, test):
        super().addSuccess(test)
        self.success_count += 1
        if self.verbosity > 1:
            self.stream.write("\033[92m✓\033[0m ")
            self.stream.write(self.getDescription(test))
            self.stream.writeln(" ... \033[92mOK\033[0m")

    def addError(self, test, err):
        super().addError(test, err)
        if self.verbosity > 1:
            self.stream.write("\033[91m✗\033[0m ")
            self.stream.write(self.getDescription(test))
            self.stream.writeln(" ... \033[91mERROR\033[0m")

    def addFailure(self, test, err):
        super().addFailure(test, err)
        if self.verbosity > 1:
            self.stream.write("\033[91m✗\033[0m ")
            self.stream.write(self.getDescription(test))
            self.stream.writeln(" ... \033[91mFAIL\033[0m")

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        if self.verbosity > 1:
            self.stream.write("\033[93m-\033[0m ")
            self.stream.write(self.getDescription(test))
            self.stream.writeln(f" ... \033[93mSKIPPED\033[0m ({reason})")


class ColoredTextTestRunner(unittest.TextTestRunner):
    """带颜色输出的测试运行器"""

    def __init__(
        self,
        stream=None,
        descriptions=True,
        verbosity=1,
        failfast=False,
        buffer=False,
        resultclass=None,
        warnings=None,
        *,
        tb_locals=False,
    ):
        if resultclass is None:
            resultclass = ColoredTextTestResult
        super().__init__(
            stream,
            descriptions,
            verbosity,
            failfast,
            buffer,
            resultclass,
            warnings,
            tb_locals=tb_locals,
        )


def create_test_suite():
    """创建测试套件"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # 添加所有测试类
    test_classes = [
        TestTaskManager,
        TestDatabaseManager,
        TestAutomationController,
        TestTaskMonitor,
    ]

    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)

    return suite


def run_specific_test(test_name):
    """运行特定的测试"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # 根据测试名称加载特定测试
    if test_name == "task_manager":
        suite.addTests(loader.loadTestsFromTestCase(TestTaskManager))
    elif test_name == "database":
        suite.addTests(loader.loadTestsFromTestCase(TestDatabaseManager))
    elif test_name == "automation":
        suite.addTests(loader.loadTestsFromTestCase(TestAutomationController))
    elif test_name == "monitor":
        suite.addTests(loader.loadTestsFromTestCase(TestTaskMonitor))
    else:
        print(f"\033[91m错误: 未知的测试名称 '{test_name}'\033[0m")
        print("可用的测试名称: task_manager, database, automation, monitor")
        return False

    runner = ColoredTextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


def print_test_summary(result):
    """打印测试摘要"""
    print("\n" + "=" * 70)
    print("\033[1m测试摘要\033[0m")
    print("=" * 70)

    total_tests = result.testsRun
    success_count = getattr(result, "success_count", 0)
    error_count = len(result.errors)
    failure_count = len(result.failures)
    skip_count = len(result.skipped) if hasattr(result, "skipped") else 0

    print(f"总测试数: {total_tests}")
    print(f"\033[92m成功: {success_count}\033[0m")

    if failure_count > 0:
        print(f"\033[91m失败: {failure_count}\033[0m")

    if error_count > 0:
        print(f"\033[91m错误: {error_count}\033[0m")

    if skip_count > 0:
        print(f"\033[93m跳过: {skip_count}\033[0m")

    success_rate = (success_count / total_tests * 100) if total_tests > 0 else 0
    print(f"成功率: {success_rate:.1f}%")

    if result.wasSuccessful():
        print("\n\033[92m✓ 所有测试通过!\033[0m")
    else:
        print("\n\033[91m✗ 部分测试失败!\033[0m")

    print("=" * 70)


def print_detailed_errors(result):
    """打印详细的错误信息"""
    if result.errors:
        print("\n\033[91m错误详情:\033[0m")
        print("-" * 50)
        for test, error in result.errors:
            print(f"\033[91m{test}:\033[0m")
            print(error)
            print("-" * 50)

    if result.failures:
        print("\n\033[91m失败详情:\033[0m")
        print("-" * 50)
        for test, failure in result.failures:
            print(f"\033[91m{test}:\033[0m")
            print(failure)
            print("-" * 50)


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="运行单元测试")
    parser.add_argument(
        "--test",
        "-t",
        help="运行特定的测试 (task_manager, database, automation, monitor)",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")
    parser.add_argument(
        "--failfast", "-f", action="store_true", help="遇到第一个失败就停止"
    )
    parser.add_argument("--quiet", "-q", action="store_true", help="静默模式")

    args = parser.parse_args()

    print("\033[1m星铁自动化工具 - 单元测试\033[0m")
    print("=" * 70)

    # 设置详细程度
    verbosity = 1
    if args.verbose:
        verbosity = 2
    elif args.quiet:
        verbosity = 0

    # 运行特定测试或所有测试
    if args.test:
        success = run_specific_test(args.test)
        return 0 if success else 1
    else:
        # 运行所有测试
        suite = create_test_suite()
        runner = ColoredTextTestRunner(verbosity=verbosity, failfast=args.failfast)

        print(f"运行 {suite.countTestCases()} 个测试...\n")

        result = runner.run(suite)

        # 打印摘要
        if not args.quiet:
            print_test_summary(result)

            # 如果有错误或失败，打印详细信息
            if not result.wasSuccessful() and args.verbose:
                print_detailed_errors(result)

        return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
