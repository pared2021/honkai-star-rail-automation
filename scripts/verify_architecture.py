#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""架构一致性验证脚本

检查项目架构是否符合设计规范，包括：
1. 目录结构一致性
2. 依赖关系合规性
3. 命名规范一致性
4. MVP模式实现完整性
"""

import ast
import os
from pathlib import Path
import re
import sys
from typing import Dict, List, Set, Tuple

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class ArchitectureValidator:
    """架构验证器"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.src_path = project_root / "src"
        self.issues: List[str] = []
        self.warnings: List[str] = []

        # 架构规范定义
        self.expected_structure = {
            "src/core": ["interfaces", "models", "enums.py", "config_manager.py"],
            "src/application": [
                "task_service.py",
                "automation_service.py",
                "error_handling_service.py",
            ],
            "src/services": ["event_bus.py", "base_async_service.py"],
            "src/repositories": [],
            "src/ui": ["main_window", "task_list", "task_creation", "mvp"],
            "src/adapters": [],
            "src/config": [],
            "src/database": [],
        }

        # 依赖规则 - 更新为符合实际项目架构的规则
        self.dependency_rules = {
            "ui": [
                "core",
                "application",
                "adapters",
                "services",
                "models",
                "config",
            ],  # UI层
            "application": [
                "core",
                "services",
                "repositories",
                "models",
                "config",
                "exceptions",
                "database",
            ],  # 应用层
            "services": [
                "core",
                "repositories",
                "models",
                "config",
                "exceptions",
                "database",
            ],  # 服务层
            "repositories": [
                "core",
                "models",
                "config",
                "database",
                "exceptions",
            ],  # 仓储层
            "core": [
                "models",
                "config",
                "exceptions",
                "database",
                "services",
            ],  # 核心层 - 允许依赖基础设施
            "adapters": [
                "core",
                "application",
                "services",
                "models",
                "config",
            ],  # 适配器层
            "automation": [
                "core",
                "services",
                "models",
                "config",
                "exceptions",
            ],  # 自动化层
            "monitoring": [
                "core",
                "services",
                "database",
                "automation",
                "models",
                "config",
            ],  # 监控层
            "middleware": ["core", "services", "exceptions"],  # 中间件层
            "database": ["core", "config", "models"],  # 数据库层
            "models": ["core"],  # 模型层
            "config": ["core"],  # 配置层
            "exceptions": ["core"],  # 异常层
        }

    def validate(self) -> Tuple[bool, List[str], List[str]]:
        """执行完整的架构验证

        Returns:
            (是否通过验证, 错误列表, 警告列表)
        """
        print("开始架构一致性验证...")

        # 1. 验证目录结构
        self._validate_directory_structure()

        # 2. 验证依赖关系
        self._validate_dependencies()

        # 3. 验证命名规范
        self._validate_naming_conventions()

        # 4. 验证MVP模式
        self._validate_mvp_pattern()

        # 5. 验证服务注册
        self._validate_service_registration()

        # 计算一致性分数
        total_checks = len(self.issues) + len(self.warnings)
        if total_checks == 0:
            consistency_score = 100.0
        else:
            # 错误权重更高
            error_weight = len(self.issues) * 2
            warning_weight = len(self.warnings) * 1
            total_weight = error_weight + warning_weight
            consistency_score = max(0, 100 - (total_weight * 5))  # 每个问题扣5分

        print(f"\n架构一致性分数: {consistency_score:.1f}%")

        return len(self.issues) == 0, self.issues, self.warnings

    def _validate_directory_structure(self):
        """验证目录结构"""
        print("验证目录结构...")

        # 检查必需的目录
        for expected_dir in self.expected_structure.keys():
            dir_path = self.project_root / expected_dir
            if not dir_path.exists():
                self.issues.append(f"缺少必需目录: {expected_dir}")

        # 检查是否还有旧的gui目录
        gui_path = self.src_path / "gui"
        if gui_path.exists():
            self.issues.append("发现废弃的gui目录，应该已迁移到ui目录")

        # 检查是否有重复的main.py文件
        main_files = list(self.project_root.glob("**/main.py"))
        if len(main_files) > 1:
            self.warnings.append(f"发现多个main.py文件: {[str(f) for f in main_files]}")

    def _validate_dependencies(self):
        """验证依赖关系"""
        print("验证依赖关系...")

        # 扫描所有Python文件的导入
        for py_file in self.src_path.rglob("*.py"):
            if py_file.name == "__init__.py":
                continue

            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    content = f.read()

                # 解析导入语句
                imports = self._extract_imports(content)

                # 检查依赖规则
                file_layer = self._get_file_layer(py_file)
                if file_layer:
                    self._check_layer_dependencies(py_file, file_layer, imports)

            except Exception as e:
                self.warnings.append(f"无法解析文件 {py_file}: {e}")

    def _extract_imports(self, content: str) -> List[str]:
        """提取导入语句"""
        imports = []

        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module)
        except:
            # 如果AST解析失败，使用正则表达式
            import_patterns = [r"from\s+([\w\.]+)\s+import", r"import\s+([\w\.]+)"]

            for pattern in import_patterns:
                matches = re.findall(pattern, content)
                imports.extend(matches)

        return imports

    def _get_file_layer(self, file_path: Path) -> str:
        """获取文件所属的架构层"""
        relative_path = file_path.relative_to(self.src_path)
        parts = relative_path.parts

        if len(parts) > 0:
            return parts[0]
        return ""

    def _check_layer_dependencies(
        self, file_path: Path, layer: str, imports: List[str]
    ):
        """检查层级依赖规则"""
        allowed_layers = self.dependency_rules.get(layer, [])

        for import_module in imports:
            if import_module.startswith("src."):
                # 提取导入的层
                import_parts = import_module.split(".")
                if len(import_parts) >= 2:
                    imported_layer = import_parts[1]

                    # 检查是否违反依赖规则
                    if imported_layer != layer and imported_layer not in allowed_layers:
                        # 检查是否是允许的特殊情况
                        if not self._is_allowed_exception(
                            layer, imported_layer, import_module
                        ):
                            self.issues.append(
                                f"违反依赖规则: {layer}层的{file_path.name}不应依赖{imported_layer}层({import_module})"
                            )

    def _is_allowed_exception(
        self, from_layer: str, to_layer: str, import_module: str
    ) -> bool:
        """检查是否是允许的依赖异常"""
        # 允许的特殊情况
        exceptions = {
            # 服务定位器模式允许的导入
            ("core", "application"): ["src.core.service_locator"],
            ("core", "services"): ["src.core.service_locator"],
        }

        allowed_imports = exceptions.get((from_layer, to_layer), [])
        return any(import_module.startswith(allowed) for allowed in allowed_imports)

    def _validate_naming_conventions(self):
        """验证命名规范"""
        print("验证命名规范...")

        # 检查文件命名
        for py_file in self.src_path.rglob("*.py"):
            filename = py_file.stem

            # 检查是否使用下划线命名
            if not re.match(r"^[a-z][a-z0-9_]*$", filename) and filename != "__init__":
                self.warnings.append(f"文件名不符合下划线命名规范: {py_file.name}")

        # 检查目录命名
        for directory in self.src_path.rglob("*"):
            if directory.is_dir() and directory.name != "__pycache__":
                dirname = directory.name
                if not re.match(r"^[a-z][a-z0-9_]*$", dirname):
                    self.warnings.append(f"目录名不符合下划线命名规范: {dirname}")

    def _validate_mvp_pattern(self):
        """验证MVP模式实现"""
        print("验证MVP模式...")

        ui_path = self.src_path / "ui"
        if not ui_path.exists():
            return

        # 检查MVP组件
        mvp_components = []
        for item in ui_path.iterdir():
            if item.is_dir() and item.name not in ["__pycache__", "common", "mvp"]:
                mvp_components.append(item)

        for component_dir in mvp_components:
            component_name = component_dir.name

            # 检查是否有MVP三个文件
            expected_files = [
                f"{component_name}_model.py",
                f"{component_name}_view.py",
                f"{component_name}_presenter.py",
                f"{component_name}_mvp.py",
            ]

            missing_files = []
            for expected_file in expected_files:
                if not (component_dir / expected_file).exists():
                    missing_files.append(expected_file)

            if missing_files:
                self.warnings.append(
                    f"MVP组件{component_name}缺少文件: {missing_files}"
                )

    def _validate_service_registration(self):
        """验证服务注册"""
        print("验证服务注册...")

        # 检查依赖注入配置
        di_file = self.src_path / "core" / "dependency_injection.py"
        if not di_file.exists():
            self.issues.append("缺少依赖注入配置文件")
            return

        # 检查服务定位器
        sl_file = self.src_path / "core" / "service_locator.py"
        if not sl_file.exists():
            self.issues.append("缺少服务定位器文件")

    def print_report(self):
        """打印验证报告"""
        print("\n" + "=" * 60)
        print("架构一致性验证报告")
        print("=" * 60)

        if self.issues:
            print(f"\n❌ 发现 {len(self.issues)} 个错误:")
            for i, issue in enumerate(self.issues, 1):
                print(f"  {i}. {issue}")

        if self.warnings:
            print(f"\n⚠️  发现 {len(self.warnings)} 个警告:")
            for i, warning in enumerate(self.warnings, 1):
                print(f"  {i}. {warning}")

        if not self.issues and not self.warnings:
            print("\n✅ 架构验证通过，未发现问题！")

        print("\n" + "=" * 60)


def main():
    """主函数"""
    validator = ArchitectureValidator(project_root)

    try:
        is_valid, issues, warnings = validator.validate()
        validator.print_report()

        # 计算一致性分数
        total_problems = len(issues) + len(warnings)
        if total_problems == 0:
            consistency_score = 100.0
        else:
            # 错误权重更高
            error_weight = len(issues) * 2
            warning_weight = len(warnings) * 1
            total_weight = error_weight + warning_weight
            consistency_score = max(0, 100 - (total_weight * 5))

        print(f"\n最终架构一致性分数: {consistency_score:.1f}%")

        # 检查是否达到95%的目标
        if consistency_score >= 95.0:
            print("🎉 架构一致性达到95%以上的目标！")
            return 0
        else:
            print(f"❌ 架构一致性未达到95%的目标，当前: {consistency_score:.1f}%")
            return 1

    except Exception as e:
        print(f"验证过程中发生错误: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
