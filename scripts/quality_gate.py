#!/usr/bin/env python3
"""
质量门禁脚本

集成所有代码质量检查工具，提供统一的质量检查入口。
包括代码风格、类型检查、重复检测、测试覆盖率等全方位检查。
"""

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum


class CheckStatus(Enum):
    """检查状态枚举"""
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass
class CheckResult:
    """检查结果"""
    name: str
    status: CheckStatus
    message: str
    details: Optional[str] = None
    duration: float = 0.0
    score: Optional[float] = None


class QualityGate:
    """质量门禁"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.src_dir = project_root / "src"
        self.scripts_dir = project_root / "scripts"
        self.reports_dir = project_root / "reports"
        
        # 确保报告目录存在
        self.reports_dir.mkdir(exist_ok=True)
        
        # 检查结果
        self.results: List[CheckResult] = []
        
        # 质量阈值配置
        self.thresholds = {
            "coverage_threshold": 80.0,
            "pylint_threshold": 8.0,
            "complexity_threshold": 10,
            "duplicate_threshold": 0.8
        }
        
        # 工具配置
        self.tools = {
            "black": {
                "enabled": True,
                "command": [sys.executable, "-m", "black"],
                "check_args": ["--check", "--diff"],
                "fix_args": []
            },
            "isort": {
                "enabled": True,
                "command": [sys.executable, "-m", "isort"],
                "check_args": ["--check-only", "--diff"],
                "fix_args": []
            },
            "flake8": {
                "enabled": True,
                "command": [sys.executable, "-m", "flake8"],
                "check_args": [],
                "fix_args": None  # flake8不支持自动修复
            },
            "pylint": {
                "enabled": True,
                "command": [sys.executable, "-m", "pylint"],
                "check_args": ["--output-format=json"],
                "fix_args": None  # pylint不支持自动修复
            },
            "mypy": {
                "enabled": True,
                "command": [sys.executable, "-m", "mypy"],
                "check_args": ["--json-report", str(self.reports_dir / "mypy.json")],
                "fix_args": None  # mypy不支持自动修复
            }
        }
    
    def load_config(self, config_path: Optional[Path] = None) -> None:
        """加载配置文件"""
        if config_path is None:
            config_path = self.project_root / "quality_gate.json"
        
        if not config_path.exists():
            self._create_default_config(config_path)
            return
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 更新阈值
            if "thresholds" in config:
                self.thresholds.update(config["thresholds"])
            
            # 更新工具配置
            if "tools" in config:
                for tool_name, tool_config in config["tools"].items():
                    if tool_name in self.tools:
                        self.tools[tool_name].update(tool_config)
            
            print(f"✅ 已加载配置: {config_path}")
            
        except Exception as e:
            print(f"⚠️  加载配置失败: {e}，使用默认配置")
    
    def _create_default_config(self, config_path: Path) -> None:
        """创建默认配置文件"""
        default_config = {
            "thresholds": self.thresholds,
            "tools": self.tools,
            "exclude_paths": [
                "*/tests/*",
                "*/test_*",
                "*/__pycache__/*",
                "*/venv/*",
                "*/env/*",
                "*/.tox/*"
            ]
        }
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=2, ensure_ascii=False)
        
        print(f"📄 已创建默认配置: {config_path}")
    
    def check_dependencies(self) -> bool:
        """检查工具依赖"""
        print("🔍 检查工具依赖...")
        
        required_tools = [
            ("black", "代码格式化"),
            ("isort", "导入排序"),
            ("flake8", "代码风格检查"),
            ("pylint", "代码质量检查"),
            ("mypy", "类型检查"),
            ("pytest", "测试框架"),
            ("coverage", "覆盖率检查")
        ]
        
        missing_tools = []
        
        for tool, description in required_tools:
            try:
                subprocess.run(
                    [sys.executable, "-c", f"import {tool.replace('-', '_')}"],
                    check=True,
                    capture_output=True
                )
                print(f"  ✅ {tool} ({description})")
            except subprocess.CalledProcessError:
                missing_tools.append((tool, description))
                print(f"  ❌ {tool} ({description})")
        
        if missing_tools:
            print(f"\n❌ 缺少工具依赖:")
            for tool, description in missing_tools:
                print(f"  - {tool}: {description}")
            print(f"\n请运行: pip install {' '.join([tool for tool, _ in missing_tools])}")
            return False
        
        print("✅ 所有工具依赖检查通过")
        return True
    
    def run_code_formatting_check(self, fix: bool = False) -> CheckResult:
        """运行代码格式化检查"""
        print("\n🎨 检查代码格式化...")
        start_time = time.time()
        
        # Black检查
        black_result = self._run_tool_check("black", fix)
        
        # isort检查
        isort_result = self._run_tool_check("isort", fix)
        
        duration = time.time() - start_time
        
        # 综合结果
        if black_result.status == CheckStatus.PASSED and isort_result.status == CheckStatus.PASSED:
            status = CheckStatus.PASSED
            message = "代码格式化检查通过"
        else:
            status = CheckStatus.FAILED
            message = "代码格式化检查失败"
        
        details = f"Black: {black_result.message}\nisort: {isort_result.message}"
        
        return CheckResult(
            name="代码格式化",
            status=status,
            message=message,
            details=details,
            duration=duration
        )
    
    def run_style_check(self) -> CheckResult:
        """运行代码风格检查"""
        print("\n📏 检查代码风格...")
        start_time = time.time()
        
        result = self._run_tool_check("flake8")
        result.duration = time.time() - start_time
        result.name = "代码风格"
        
        return result
    
    def run_quality_check(self) -> CheckResult:
        """运行代码质量检查"""
        print("\n🔍 检查代码质量...")
        start_time = time.time()
        
        try:
            cmd = self.tools["pylint"]["command"] + self.tools["pylint"]["check_args"] + [str(self.src_dir)]
            
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            
            duration = time.time() - start_time
            
            # 解析pylint输出
            if result.stdout:
                try:
                    pylint_data = json.loads(result.stdout)
                    # 计算平均评分
                    if pylint_data:
                        total_score = sum(item.get('score', 0) for item in pylint_data if 'score' in item)
                        avg_score = total_score / len(pylint_data) if pylint_data else 0
                    else:
                        avg_score = 10.0  # 没有问题时给满分
                except json.JSONDecodeError:
                    avg_score = 5.0  # 解析失败时给中等分数
            else:
                avg_score = 10.0  # 没有输出通常意味着没有问题
            
            # 判断是否通过阈值
            threshold = self.thresholds["pylint_threshold"]
            
            if avg_score >= threshold:
                status = CheckStatus.PASSED
                message = f"代码质量检查通过 (评分: {avg_score:.1f}/{threshold})"
            else:
                status = CheckStatus.FAILED
                message = f"代码质量检查失败 (评分: {avg_score:.1f}/{threshold})"
            
            return CheckResult(
                name="代码质量",
                status=status,
                message=message,
                details=result.stdout if result.stdout else result.stderr,
                duration=duration,
                score=avg_score
            )
            
        except Exception as e:
            return CheckResult(
                name="代码质量",
                status=CheckStatus.ERROR,
                message=f"代码质量检查出错: {e}",
                duration=time.time() - start_time
            )
    
    def run_type_check(self) -> CheckResult:
        """运行类型检查"""
        print("\n🔍 检查类型注解...")
        start_time = time.time()
        
        try:
            cmd = self.tools["mypy"]["command"] + self.tools["mypy"]["check_args"] + [str(self.src_dir)]
            
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            
            duration = time.time() - start_time
            
            # mypy返回码为0表示没有错误
            if result.returncode == 0:
                status = CheckStatus.PASSED
                message = "类型检查通过"
            else:
                status = CheckStatus.FAILED
                message = "类型检查失败"
            
            return CheckResult(
                name="类型检查",
                status=status,
                message=message,
                details=result.stdout if result.stdout else result.stderr,
                duration=duration
            )
            
        except Exception as e:
            return CheckResult(
                name="类型检查",
                status=CheckStatus.ERROR,
                message=f"类型检查出错: {e}",
                duration=time.time() - start_time
            )
    
    def run_duplicate_check(self) -> CheckResult:
        """运行重复代码检查"""
        print("\n🔍 检查重复代码...")
        start_time = time.time()
        
        try:
            duplicate_script = self.scripts_dir / "duplicate_detector.py"
            
            if not duplicate_script.exists():
                return CheckResult(
                    name="重复检测",
                    status=CheckStatus.SKIPPED,
                    message="重复检测脚本不存在",
                    duration=time.time() - start_time
                )
            
            cmd = [sys.executable, str(duplicate_script), "--output", str(self.reports_dir / "duplicates.json")]
            
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            
            duration = time.time() - start_time
            
            # 检查返回码
            if result.returncode == 0:
                status = CheckStatus.PASSED
                message = "重复代码检查通过"
            else:
                status = CheckStatus.FAILED
                message = "发现重复代码"
            
            return CheckResult(
                name="重复检测",
                status=status,
                message=message,
                details=result.stdout,
                duration=duration
            )
            
        except Exception as e:
            return CheckResult(
                name="重复检测",
                status=CheckStatus.ERROR,
                message=f"重复检测出错: {e}",
                duration=time.time() - start_time
            )
    
    def run_test_coverage_check(self) -> CheckResult:
        """运行测试覆盖率检查"""
        print("\n🧪 检查测试覆盖率...")
        start_time = time.time()
        
        try:
            test_script = self.scripts_dir / "test_runner.py"
            
            if not test_script.exists():
                return CheckResult(
                    name="测试覆盖率",
                    status=CheckStatus.SKIPPED,
                    message="测试运行器不存在",
                    duration=time.time() - start_time
                )
            
            # 运行测试和覆盖率检查
            cmd = [
                sys.executable, str(test_script), "run",
                "--format", "junit"
            ]
            
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            
            duration = time.time() - start_time
            
            # 检查覆盖率阈值
            coverage_cmd = [
                sys.executable, str(test_script), "check",
                "--threshold", str(self.thresholds["coverage_threshold"])
            ]
            
            coverage_result = subprocess.run(
                coverage_cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            
            # 综合判断结果
            if result.returncode == 0 and coverage_result.returncode == 0:
                status = CheckStatus.PASSED
                message = f"测试覆盖率检查通过 (阈值: {self.thresholds['coverage_threshold']}%)"
            elif result.returncode != 0:
                status = CheckStatus.FAILED
                message = "测试执行失败"
            else:
                status = CheckStatus.FAILED
                message = f"测试覆盖率未达到阈值 {self.thresholds['coverage_threshold']}%"
            
            details = f"测试输出:\n{result.stdout}\n\n覆盖率检查:\n{coverage_result.stdout}"
            
            return CheckResult(
                name="测试覆盖率",
                status=status,
                message=message,
                details=details,
                duration=duration
            )
            
        except Exception as e:
            return CheckResult(
                name="测试覆盖率",
                status=CheckStatus.ERROR,
                message=f"测试覆盖率检查出错: {e}",
                duration=time.time() - start_time
            )
    
    def _run_tool_check(self, tool_name: str, fix: bool = False) -> CheckResult:
        """运行单个工具检查"""
        tool_config = self.tools[tool_name]
        
        if not tool_config["enabled"]:
            return CheckResult(
                name=tool_name,
                status=CheckStatus.SKIPPED,
                message=f"{tool_name} 已禁用"
            )
        
        try:
            cmd = tool_config["command"].copy()
            
            if fix and tool_config["fix_args"] is not None:
                cmd.extend(tool_config["fix_args"])
            else:
                cmd.extend(tool_config["check_args"])
            
            cmd.append(str(self.src_dir))
            
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                status = CheckStatus.PASSED
                message = f"{tool_name} 检查通过"
            else:
                status = CheckStatus.FAILED
                message = f"{tool_name} 检查失败"
            
            return CheckResult(
                name=tool_name,
                status=status,
                message=message,
                details=result.stdout if result.stdout else result.stderr
            )
            
        except Exception as e:
            return CheckResult(
                name=tool_name,
                status=CheckStatus.ERROR,
                message=f"{tool_name} 检查出错: {e}"
            )
    
    def run_all_checks(self, fix: bool = False, skip_tests: bool = False) -> bool:
        """运行所有质量检查"""
        print("🚀 开始质量门禁检查...")
        print("="*60)
        
        # 检查依赖
        if not self.check_dependencies():
            return False
        
        # 执行各项检查
        checks = [
            ("代码格式化", lambda: self.run_code_formatting_check(fix)),
            ("代码风格", self.run_style_check),
            ("代码质量", self.run_quality_check),
            ("类型检查", self.run_type_check),
            ("重复检测", self.run_duplicate_check),
        ]
        
        if not skip_tests:
            checks.append(("测试覆盖率", self.run_test_coverage_check))
        
        # 执行检查
        for check_name, check_func in checks:
            try:
                result = check_func()
                self.results.append(result)
                
                # 显示结果
                status_icon = {
                    CheckStatus.PASSED: "✅",
                    CheckStatus.FAILED: "❌",
                    CheckStatus.SKIPPED: "⏭️",
                    CheckStatus.ERROR: "💥"
                }[result.status]
                
                print(f"{status_icon} {result.name}: {result.message} ({result.duration:.1f}s)")
                
                if result.details and result.status in [CheckStatus.FAILED, CheckStatus.ERROR]:
                    # 只显示前几行详细信息
                    details_lines = result.details.split('\n')[:5]
                    for line in details_lines:
                        if line.strip():
                            print(f"   {line}")
                    if len(result.details.split('\n')) > 5:
                        print("   ...")
                
            except Exception as e:
                error_result = CheckResult(
                    name=check_name,
                    status=CheckStatus.ERROR,
                    message=f"检查执行出错: {e}"
                )
                self.results.append(error_result)
                print(f"💥 {check_name}: {error_result.message}")
        
        # 生成报告
        self._generate_report()
        
        # 判断整体结果
        failed_checks = [r for r in self.results if r.status == CheckStatus.FAILED]
        error_checks = [r for r in self.results if r.status == CheckStatus.ERROR]
        
        total_checks = len([r for r in self.results if r.status != CheckStatus.SKIPPED])
        passed_checks = len([r for r in self.results if r.status == CheckStatus.PASSED])
        
        print("\n" + "="*60)
        print(f"📊 质量门禁结果: {passed_checks}/{total_checks} 通过")
        
        if failed_checks:
            print(f"❌ 失败检查: {', '.join([r.name for r in failed_checks])}")
        
        if error_checks:
            print(f"💥 错误检查: {', '.join([r.name for r in error_checks])}")
        
        success = len(failed_checks) == 0 and len(error_checks) == 0
        
        if success:
            print("🎉 质量门禁检查全部通过！")
        else:
            print("🚫 质量门禁检查未通过")
        
        return success
    
    def _generate_report(self) -> None:
        """生成检查报告"""
        report_data = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "project_root": str(self.project_root),
            "thresholds": self.thresholds,
            "results": [
                {
                    "name": r.name,
                    "status": r.status.value,
                    "message": r.message,
                    "details": r.details,
                    "duration": r.duration,
                    "score": r.score
                }
                for r in self.results
            ],
            "summary": {
                "total_checks": len(self.results),
                "passed": len([r for r in self.results if r.status == CheckStatus.PASSED]),
                "failed": len([r for r in self.results if r.status == CheckStatus.FAILED]),
                "skipped": len([r for r in self.results if r.status == CheckStatus.SKIPPED]),
                "errors": len([r for r in self.results if r.status == CheckStatus.ERROR]),
                "total_duration": sum(r.duration for r in self.results)
            }
        }
        
        # 保存JSON报告
        report_path = self.reports_dir / "quality_gate.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 质量报告已保存: {report_path}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="质量门禁检查")
    parser.add_argument(
        "--fix",
        action="store_true",
        help="自动修复可修复的问题"
    )
    parser.add_argument(
        "--skip-tests",
        action="store_true",
        help="跳过测试覆盖率检查"
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="配置文件路径"
    )
    
    args = parser.parse_args()
    
    # 确定项目根目录
    project_root = Path(__file__).parent.parent
    
    # 创建质量门禁
    gate = QualityGate(project_root)
    
    # 加载配置
    gate.load_config(args.config)
    
    try:
        # 运行检查
        success = gate.run_all_checks(
            fix=args.fix,
            skip_tests=args.skip_tests
        )
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  质量检查被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 质量检查出错: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()