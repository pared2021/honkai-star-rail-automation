#!/usr/bin/env python3
"""
开发前检查脚本

在开始开发新功能前，自动执行功能注册表检查，防止重复开发。
包括功能重复检测、架构合规性检查、开发环境验证等。
"""

import argparse
from dataclasses import dataclass
from enum import Enum
import json
from pathlib import Path
import re
import subprocess
import sys
import time
from typing import Any, Dict, List, Optional, Tuple


class CheckStatus(Enum):
    """检查状态枚举"""

    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass
class CheckResult:
    """检查结果"""

    name: str
    status: CheckStatus
    message: str
    details: Optional[str] = None
    suggestions: Optional[List[str]] = None


@dataclass
class FeatureInfo:
    """功能信息"""

    name: str
    description: str
    category: str
    status: str
    files: List[str]
    dependencies: List[str]
    author: str
    created_date: str
    last_modified: str


class PreDevChecker:
    """开发前检查器"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.src_dir = project_root / "src"
        self.docs_dir = project_root / ".trae" / "documents"
        self.scripts_dir = project_root / "scripts"

        # 功能注册表路径
        self.feature_registry_path = self.docs_dir / "功能注册表.md"
        self.dev_standards_path = self.docs_dir / "开发规范和治理文档.md"

        # 检查结果
        self.results: List[CheckResult] = []

        # 功能注册表数据
        self.registered_features: List[FeatureInfo] = []

        # 开发规范
        self.dev_standards: Dict[str, Any] = {}

    def load_feature_registry(self) -> bool:
        """加载功能注册表"""
        if not self.feature_registry_path.exists():
            print(f"⚠️  功能注册表不存在: {self.feature_registry_path}")
            return False

        try:
            with open(self.feature_registry_path, "r", encoding="utf-8") as f:
                content = f.read()

            # 解析Markdown格式的功能注册表
            self.registered_features = self._parse_feature_registry(content)
            print(f"✅ 已加载功能注册表: {len(self.registered_features)} 个功能")
            return True

        except Exception as e:
            print(f"❌ 加载功能注册表失败: {e}")
            return False

    def _parse_feature_registry(self, content: str) -> List[FeatureInfo]:
        """解析功能注册表内容"""
        features = []

        # 查找功能表格
        table_pattern = r"\|\s*功能名称\s*\|.*?\n((?:\|.*?\n)*?)"
        table_match = re.search(table_pattern, content, re.MULTILINE | re.DOTALL)

        if not table_match:
            return features

        table_content = table_match.group(1)
        lines = table_content.strip().split("\n")

        for line in lines:
            if line.strip().startswith("|") and "---" not in line:
                parts = [part.strip() for part in line.split("|")[1:-1]]

                if len(parts) >= 8:
                    try:
                        feature = FeatureInfo(
                            name=parts[0],
                            description=parts[1],
                            category=parts[2],
                            status=parts[3],
                            files=parts[4].split(",") if parts[4] else [],
                            dependencies=parts[5].split(",") if parts[5] else [],
                            author=parts[6],
                            created_date=parts[7],
                            last_modified=parts[8] if len(parts) > 8 else parts[7],
                        )
                        features.append(feature)
                    except Exception as e:
                        print(f"⚠️  解析功能行失败: {line} - {e}")

        return features

    def load_dev_standards(self) -> bool:
        """加载开发规范"""
        if not self.dev_standards_path.exists():
            print(f"⚠️  开发规范文档不存在: {self.dev_standards_path}")
            return False

        try:
            with open(self.dev_standards_path, "r", encoding="utf-8") as f:
                content = f.read()

            # 简单解析开发规范（实际项目中可能需要更复杂的解析）
            self.dev_standards = {"content": content, "loaded": True}

            print("✅ 已加载开发规范文档")
            return True

        except Exception as e:
            print(f"❌ 加载开发规范失败: {e}")
            return False

    def check_feature_duplication(
        self, feature_name: str, feature_description: str = ""
    ) -> CheckResult:
        """检查功能重复"""
        print(f"🔍 检查功能重复: {feature_name}")

        # 精确匹配
        exact_matches = [
            f
            for f in self.registered_features
            if f.name.lower() == feature_name.lower()
        ]

        # 模糊匹配
        fuzzy_matches = []
        feature_keywords = set(feature_name.lower().split())

        for feature in self.registered_features:
            existing_keywords = set(feature.name.lower().split())
            existing_desc_keywords = (
                set(feature.description.lower().split())
                if feature.description
                else set()
            )

            # 计算关键词重叠度
            name_overlap = len(feature_keywords & existing_keywords) / len(
                feature_keywords | existing_keywords
            )
            desc_overlap = 0

            if feature_description:
                desc_keywords = set(feature_description.lower().split())
                desc_overlap = (
                    len(desc_keywords & existing_desc_keywords)
                    / len(desc_keywords | existing_desc_keywords)
                    if desc_keywords
                    else 0
                )

            # 如果重叠度超过阈值，认为可能重复
            if name_overlap > 0.6 or desc_overlap > 0.5:
                fuzzy_matches.append((feature, max(name_overlap, desc_overlap)))

        # 生成检查结果
        if exact_matches:
            return CheckResult(
                name="功能重复检查",
                status=CheckStatus.FAILED,
                message=f"发现完全重复的功能: {feature_name}",
                details=f"已存在功能: {', '.join([f.name for f in exact_matches])}",
                suggestions=[
                    "请检查是否真的需要开发新功能",
                    "考虑扩展或修改现有功能",
                    "如果确实需要，请使用不同的功能名称",
                ],
            )

        elif fuzzy_matches:
            fuzzy_matches.sort(key=lambda x: x[1], reverse=True)
            top_matches = fuzzy_matches[:3]

            return CheckResult(
                name="功能重复检查",
                status=CheckStatus.WARNING,
                message=f"发现可能重复的功能: {feature_name}",
                details="\n".join(
                    [
                        f"- {match[0].name} (相似度: {match[1]:.1%}): {match[0].description}"
                        for match in top_matches
                    ]
                ),
                suggestions=[
                    "请仔细检查这些相似功能",
                    "确认新功能的独特性",
                    "考虑是否可以复用现有代码",
                ],
            )

        else:
            return CheckResult(
                name="功能重复检查",
                status=CheckStatus.PASSED,
                message=f"未发现重复功能: {feature_name}",
            )

    def check_naming_convention(
        self, feature_name: str, file_paths: List[str] = None
    ) -> CheckResult:
        """检查命名规范"""
        print("📏 检查命名规范")

        issues = []
        suggestions = []

        # 检查功能名称规范
        if not feature_name:
            issues.append("功能名称不能为空")
        elif len(feature_name) < 3:
            issues.append("功能名称过短（少于3个字符）")
        elif len(feature_name) > 50:
            issues.append("功能名称过长（超过50个字符）")

        # 检查是否包含特殊字符
        if re.search(r"[^\w\s\-_\u4e00-\u9fff]", feature_name):
            issues.append("功能名称包含不允许的特殊字符")
            suggestions.append("只允许使用字母、数字、中文、连字符和下划线")

        # 检查文件路径规范
        if file_paths:
            for file_path in file_paths:
                if not file_path.startswith("src/"):
                    issues.append(f"文件路径不符合规范: {file_path}")
                    suggestions.append("所有源代码文件应放在src/目录下")

                # 检查文件名规范
                file_name = Path(file_path).name
                if not re.match(r"^[a-z][a-z0-9_]*\.py$", file_name):
                    issues.append(f"文件名不符合规范: {file_name}")
                    suggestions.append("文件名应使用小写字母和下划线，以.py结尾")

        # 生成结果
        if issues:
            return CheckResult(
                name="命名规范检查",
                status=CheckStatus.FAILED,
                message="命名规范检查失败",
                details="\n".join([f"- {issue}" for issue in issues]),
                suggestions=suggestions,
            )
        else:
            return CheckResult(
                name="命名规范检查",
                status=CheckStatus.PASSED,
                message="命名规范检查通过",
            )

    def check_architecture_compliance(
        self, feature_category: str, file_paths: List[str] = None
    ) -> CheckResult:
        """检查架构合规性"""
        print("🏗️  检查架构合规性")

        issues = []
        suggestions = []

        # 定义架构层级规范
        architecture_rules = {
            "UI层": {
                "allowed_dirs": ["src/ui", "src/views", "src/components"],
                "forbidden_imports": ["src.infrastructure", "src.data"],
            },
            "应用服务层": {
                "allowed_dirs": ["src/services", "src/application"],
                "forbidden_imports": ["src.ui", "src.infrastructure.database"],
            },
            "领域服务层": {
                "allowed_dirs": ["src/domain", "src/core"],
                "forbidden_imports": ["src.ui", "src.infrastructure"],
            },
            "基础设施层": {
                "allowed_dirs": ["src/infrastructure", "src/data"],
                "forbidden_imports": ["src.ui", "src.services"],
            },
        }

        # 检查文件路径是否符合架构层级
        if feature_category in architecture_rules and file_paths:
            rules = architecture_rules[feature_category]

            for file_path in file_paths:
                # 检查文件是否在允许的目录中
                allowed = any(
                    file_path.startswith(allowed_dir)
                    for allowed_dir in rules["allowed_dirs"]
                )

                if not allowed:
                    issues.append(
                        f"文件 {file_path} 不在 {feature_category} 允许的目录中"
                    )
                    suggestions.append(
                        f"请将文件移动到: {', '.join(rules['allowed_dirs'])}"
                    )

        # 检查是否遵循分层架构原则
        if not feature_category or feature_category not in architecture_rules:
            issues.append(f"未指定或无效的功能分类: {feature_category}")
            suggestions.append(
                f"请选择有效的分类: {', '.join(architecture_rules.keys())}"
            )

        # 生成结果
        if issues:
            return CheckResult(
                name="架构合规性检查",
                status=CheckStatus.FAILED,
                message="架构合规性检查失败",
                details="\n".join([f"- {issue}" for issue in issues]),
                suggestions=suggestions,
            )
        else:
            return CheckResult(
                name="架构合规性检查",
                status=CheckStatus.PASSED,
                message="架构合规性检查通过",
            )

    def check_development_environment(self) -> CheckResult:
        """检查开发环境"""
        print("🔧 检查开发环境")

        issues = []
        warnings = []

        # 检查Python版本
        python_version = sys.version_info
        if python_version < (3, 8):
            issues.append(
                f"Python版本过低: {python_version.major}.{python_version.minor}"
            )
        elif python_version < (3, 9):
            warnings.append(
                f"建议升级Python版本: {python_version.major}.{python_version.minor}"
            )

        # 检查必要的工具
        required_tools = [
            ("black", "代码格式化工具"),
            ("isort", "导入排序工具"),
            ("flake8", "代码风格检查"),
            ("pylint", "代码质量检查"),
            ("mypy", "类型检查"),
            ("pytest", "测试框架"),
        ]

        missing_tools = []
        for tool, description in required_tools:
            try:
                subprocess.run(
                    [sys.executable, "-c", f"import {tool.replace('-', '_')}"],
                    check=True,
                    capture_output=True,
                )
            except subprocess.CalledProcessError:
                missing_tools.append((tool, description))

        if missing_tools:
            issues.extend(
                [f"缺少工具: {tool} ({desc})" for tool, desc in missing_tools]
            )

        # 检查配置文件
        config_files = [".flake8", ".pylintrc", "mypy.ini", "pyproject.toml"]

        missing_configs = []
        for config_file in config_files:
            if not (self.project_root / config_file).exists():
                missing_configs.append(config_file)

        if missing_configs:
            warnings.extend([f"缺少配置文件: {config}" for config in missing_configs])

        # 生成结果
        if issues:
            status = CheckStatus.FAILED
            message = "开发环境检查失败"
        elif warnings:
            status = CheckStatus.WARNING
            message = "开发环境检查通过，但有警告"
        else:
            status = CheckStatus.PASSED
            message = "开发环境检查通过"

        details = ""
        if issues:
            details += "错误:\n" + "\n".join([f"- {issue}" for issue in issues])
        if warnings:
            if details:
                details += "\n\n"
            details += "警告:\n" + "\n".join([f"- {warning}" for warning in warnings])

        suggestions = []
        if missing_tools:
            suggestions.append(
                f"安装缺少的工具: pip install {' '.join([tool for tool, _ in missing_tools])}"
            )
        if missing_configs:
            suggestions.append("运行质量检查脚本生成配置文件")

        return CheckResult(
            name="开发环境检查",
            status=status,
            message=message,
            details=details if details else None,
            suggestions=suggestions if suggestions else None,
        )

    def check_git_status(self) -> CheckResult:
        """检查Git状态"""
        print("📝 检查Git状态")

        try:
            # 检查是否有未提交的更改
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True,
            )

            if result.stdout.strip():
                return CheckResult(
                    name="Git状态检查",
                    status=CheckStatus.WARNING,
                    message="存在未提交的更改",
                    details=result.stdout,
                    suggestions=[
                        "建议在开始新功能开发前提交当前更改",
                        "或者创建新的分支进行开发",
                    ],
                )
            else:
                return CheckResult(
                    name="Git状态检查",
                    status=CheckStatus.PASSED,
                    message="Git工作区干净",
                )

        except subprocess.CalledProcessError:
            return CheckResult(
                name="Git状态检查",
                status=CheckStatus.SKIPPED,
                message="不是Git仓库或Git不可用",
            )
        except Exception as e:
            return CheckResult(
                name="Git状态检查",
                status=CheckStatus.ERROR,
                message=f"Git状态检查出错: {e}",
            )

    def run_pre_dev_check(
        self,
        feature_name: str,
        feature_description: str = "",
        feature_category: str = "",
        file_paths: List[str] = None,
    ) -> bool:
        """运行开发前检查"""
        print("🚀 开始开发前检查...")
        print("=" * 60)
        print(f"功能名称: {feature_name}")
        if feature_description:
            print(f"功能描述: {feature_description}")
        if feature_category:
            print(f"功能分类: {feature_category}")
        if file_paths:
            print(f"涉及文件: {', '.join(file_paths)}")
        print("=" * 60)

        # 加载必要数据
        if not self.load_feature_registry():
            print("⚠️  无法加载功能注册表，跳过重复检查")

        if not self.load_dev_standards():
            print("⚠️  无法加载开发规范，跳过部分检查")

        # 执行各项检查
        checks = [
            ("开发环境检查", lambda: self.check_development_environment()),
            ("Git状态检查", lambda: self.check_git_status()),
            (
                "功能重复检查",
                lambda: self.check_feature_duplication(
                    feature_name, feature_description
                ),
            ),
            (
                "命名规范检查",
                lambda: self.check_naming_convention(feature_name, file_paths),
            ),
            (
                "架构合规性检查",
                lambda: self.check_architecture_compliance(
                    feature_category, file_paths
                ),
            ),
        ]

        # 执行检查
        for check_name, check_func in checks:
            try:
                result = check_func()
                self.results.append(result)

                # 显示结果
                status_icon = {
                    CheckStatus.PASSED: "✅",
                    CheckStatus.FAILED: "❌",
                    CheckStatus.WARNING: "⚠️",
                    CheckStatus.SKIPPED: "⏭️",
                    CheckStatus.ERROR: "💥",
                }[result.status]

                print(f"{status_icon} {result.name}: {result.message}")

                # 显示详细信息
                if result.details and result.status in [
                    CheckStatus.FAILED,
                    CheckStatus.WARNING,
                    CheckStatus.ERROR,
                ]:
                    for line in result.details.split("\n"):
                        if line.strip():
                            print(f"   {line}")

                # 显示建议
                if result.suggestions:
                    print("   建议:")
                    for suggestion in result.suggestions:
                        print(f"   - {suggestion}")

            except Exception as e:
                error_result = CheckResult(
                    name=check_name,
                    status=CheckStatus.ERROR,
                    message=f"检查执行出错: {e}",
                )
                self.results.append(error_result)
                print(f"💥 {check_name}: {error_result.message}")

        # 判断整体结果
        failed_checks = [r for r in self.results if r.status == CheckStatus.FAILED]
        error_checks = [r for r in self.results if r.status == CheckStatus.ERROR]
        warning_checks = [r for r in self.results if r.status == CheckStatus.WARNING]

        print("\n" + "=" * 60)
        print("📊 开发前检查结果:")

        if failed_checks:
            print(f"❌ 失败: {', '.join([r.name for r in failed_checks])}")

        if error_checks:
            print(f"💥 错误: {', '.join([r.name for r in error_checks])}")

        if warning_checks:
            print(f"⚠️  警告: {', '.join([r.name for r in warning_checks])}")

        success = len(failed_checks) == 0 and len(error_checks) == 0

        if success:
            if warning_checks:
                print("\n🎯 开发前检查基本通过，但请注意警告信息")
            else:
                print("\n🎉 开发前检查全部通过，可以开始开发！")
        else:
            print("\n🚫 开发前检查未通过，请解决问题后再开始开发")

        return success

    def register_new_feature(
        self,
        feature_name: str,
        feature_description: str,
        feature_category: str,
        file_paths: List[str],
        dependencies: List[str] = None,
        author: str = "",
    ) -> bool:
        """注册新功能到功能注册表"""
        print(f"📝 注册新功能: {feature_name}")

        if not self.feature_registry_path.exists():
            print(f"❌ 功能注册表不存在: {self.feature_registry_path}")
            return False

        try:
            # 读取现有内容
            with open(self.feature_registry_path, "r", encoding="utf-8") as f:
                content = f.read()

            # 准备新功能行
            current_date = time.strftime("%Y-%m-%d")
            dependencies_str = ",".join(dependencies) if dependencies else ""
            files_str = ",".join(file_paths)

            new_row = f"| {feature_name} | {feature_description} | {feature_category} | 开发中 | {files_str} | {dependencies_str} | {author} | {current_date} | {current_date} |"

            # 查找表格位置并插入新行
            table_end_pattern = r"(\|.*?\|\s*\n)(?=\n|$)"
            matches = list(re.finditer(table_end_pattern, content, re.MULTILINE))

            if matches:
                # 在最后一个表格行后插入
                last_match = matches[-1]
                insert_pos = last_match.end()
                new_content = (
                    content[:insert_pos] + new_row + "\n" + content[insert_pos:]
                )
            else:
                # 如果找不到表格，在文件末尾添加
                new_content = content + "\n" + new_row + "\n"

            # 写回文件
            with open(self.feature_registry_path, "w", encoding="utf-8") as f:
                f.write(new_content)

            print(f"✅ 功能已注册到功能注册表")
            return True

        except Exception as e:
            print(f"❌ 注册功能失败: {e}")
            return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="开发前检查")
    parser.add_argument("feature_name", help="功能名称")
    parser.add_argument("--description", help="功能描述")
    parser.add_argument(
        "--category",
        choices=["UI层", "应用服务层", "领域服务层", "基础设施层"],
        help="功能分类",
    )
    parser.add_argument("--files", nargs="*", help="涉及的文件路径")
    parser.add_argument("--dependencies", nargs="*", help="依赖的功能")
    parser.add_argument("--author", help="开发者")
    parser.add_argument(
        "--register", action="store_true", help="检查通过后自动注册功能"
    )

    args = parser.parse_args()

    # 确定项目根目录
    project_root = Path(__file__).parent.parent

    # 创建检查器
    checker = PreDevChecker(project_root)

    try:
        # 运行检查
        success = checker.run_pre_dev_check(
            feature_name=args.feature_name,
            feature_description=args.description or "",
            feature_category=args.category or "",
            file_paths=args.files or [],
        )

        # 如果检查通过且需要注册
        if success and args.register:
            checker.register_new_feature(
                feature_name=args.feature_name,
                feature_description=args.description or "",
                feature_category=args.category or "",
                file_paths=args.files or [],
                dependencies=args.dependencies or [],
                author=args.author or "",
            )

        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n\n⚠️  开发前检查被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 开发前检查出错: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
