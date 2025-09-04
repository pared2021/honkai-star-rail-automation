#!/usr/bin/env python3
"""
重复代码和功能检测脚本

检测项目中的重复代码、重复类定义、重复函数实现等，
并与功能注册表进行对比，确保没有重复开发。
"""

import argparse
import ast
from collections import defaultdict
import difflib
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any, Dict, List, Optional, Set, Tuple


class CodeElement:
    """代码元素基类"""

    def __init__(self, name: str, file_path: Path, line_number: int, content: str):
        self.name = name
        self.file_path = file_path
        self.line_number = line_number
        self.content = content
        self.hash = self._calculate_hash()

    def _calculate_hash(self) -> str:
        """计算内容哈希"""
        # 标准化内容（去除空白、注释等）
        normalized = re.sub(r"\s+", " ", self.content.strip())
        normalized = re.sub(r"#.*$", "", normalized, flags=re.MULTILINE)
        return hashlib.md5(normalized.encode()).hexdigest()

    def similarity(self, other: "CodeElement") -> float:
        """计算与另一个代码元素的相似度"""
        if self.hash == other.hash:
            return 1.0

        # 使用difflib计算相似度
        matcher = difflib.SequenceMatcher(None, self.content, other.content)
        return matcher.ratio()

    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.name}) at {self.file_path}:{self.line_number}"


class ClassElement(CodeElement):
    """类元素"""

    def __init__(
        self,
        name: str,
        file_path: Path,
        line_number: int,
        content: str,
        methods: List[str],
    ):
        super().__init__(name, file_path, line_number, content)
        self.methods = methods


class FunctionElement(CodeElement):
    """函数元素"""

    def __init__(
        self, name: str, file_path: Path, line_number: int, content: str, signature: str
    ):
        super().__init__(name, file_path, line_number, content)
        self.signature = signature


class DuplicateDetector:
    """重复检测器"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.src_dir = project_root / "src"
        self.function_registry_path = (
            project_root / ".trae" / "documents" / "功能注册表.md"
        )

        # 存储检测到的代码元素
        self.classes: List[ClassElement] = []
        self.functions: List[FunctionElement] = []

        # 重复检测结果
        self.duplicate_classes: List[Tuple[ClassElement, ClassElement, float]] = []
        self.duplicate_functions: List[
            Tuple[FunctionElement, FunctionElement, float]
        ] = []
        self.duplicate_code_blocks: List[Tuple[str, List[Tuple[Path, int]]]] = []

        # 功能注册表内容
        self.registered_functions: Set[str] = set()

    def load_function_registry(self) -> None:
        """加载功能注册表"""
        if not self.function_registry_path.exists():
            print(f"⚠️  功能注册表不存在: {self.function_registry_path}")
            return

        try:
            with open(self.function_registry_path, "r", encoding="utf-8") as f:
                content = f.read()

            # 提取已注册的功能名称
            # 匹配模式: ### 1. 功能名称 (ClassName)
            pattern = r"###\s+\d+\.\s+(.+?)\s+\((.+?)\)"
            matches = re.findall(pattern, content)

            for func_desc, class_name in matches:
                self.registered_functions.add(class_name.strip())

            print(f"📋 已加载 {len(self.registered_functions)} 个注册功能")

        except Exception as e:
            print(f"❌ 加载功能注册表失败: {e}")

    def parse_python_file(self, file_path: Path) -> None:
        """解析Python文件"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    self._extract_class(node, file_path, content)
                elif isinstance(node, ast.FunctionDef):
                    self._extract_function(node, file_path, content)

        except Exception as e:
            print(f"⚠️  解析文件失败 {file_path}: {e}")

    def _extract_class(self, node: ast.ClassDef, file_path: Path, content: str) -> None:
        """提取类定义"""
        lines = content.split("\n")
        start_line = node.lineno - 1
        end_line = node.end_lineno if hasattr(node, "end_lineno") else start_line + 10

        class_content = "\n".join(lines[start_line:end_line])

        # 提取方法名
        methods = []
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                methods.append(item.name)

        class_element = ClassElement(
            name=node.name,
            file_path=file_path,
            line_number=node.lineno,
            content=class_content,
            methods=methods,
        )

        self.classes.append(class_element)

    def _extract_function(
        self, node: ast.FunctionDef, file_path: Path, content: str
    ) -> None:
        """提取函数定义"""
        lines = content.split("\n")
        start_line = node.lineno - 1
        end_line = node.end_lineno if hasattr(node, "end_lineno") else start_line + 5

        func_content = "\n".join(lines[start_line:end_line])

        # 构建函数签名
        args = [arg.arg for arg in node.args.args]
        signature = f"{node.name}({', '.join(args)})"

        func_element = FunctionElement(
            name=node.name,
            file_path=file_path,
            line_number=node.lineno,
            content=func_content,
            signature=signature,
        )

        self.functions.append(func_element)

    def scan_source_files(self) -> None:
        """扫描源代码文件"""
        print(f"🔍 扫描源代码目录: {self.src_dir}")

        python_files = list(self.src_dir.rglob("*.py"))
        print(f"找到 {len(python_files)} 个Python文件")

        for file_path in python_files:
            # 跳过测试文件和__pycache__
            if "test_" in file_path.name or "__pycache__" in str(file_path):
                continue

            print(f"解析: {file_path.relative_to(self.project_root)}")
            self.parse_python_file(file_path)

        print(f"\n📊 扫描结果:")
        print(f"  类定义: {len(self.classes)}")
        print(f"  函数定义: {len(self.functions)}")

    def detect_duplicate_classes(self, similarity_threshold: float = 0.8) -> None:
        """检测重复的类定义"""
        print(f"\n🔍 检测重复类定义 (相似度阈值: {similarity_threshold})...")

        for i, class1 in enumerate(self.classes):
            for j, class2 in enumerate(self.classes[i + 1 :], i + 1):
                # 跳过同一文件中的类
                if class1.file_path == class2.file_path:
                    continue

                similarity = class1.similarity(class2)

                if similarity >= similarity_threshold:
                    self.duplicate_classes.append((class1, class2, similarity))

        print(f"发现 {len(self.duplicate_classes)} 对重复类")

    def detect_duplicate_functions(self, similarity_threshold: float = 0.8) -> None:
        """检测重复的函数定义"""
        print(f"\n🔍 检测重复函数定义 (相似度阈值: {similarity_threshold})...")

        for i, func1 in enumerate(self.functions):
            for j, func2 in enumerate(self.functions[i + 1 :], i + 1):
                # 跳过同一文件中的函数
                if func1.file_path == func2.file_path:
                    continue

                # 跳过不同名的函数（除非相似度很高）
                if func1.name != func2.name and similarity_threshold > 0.9:
                    continue

                similarity = func1.similarity(func2)

                if similarity >= similarity_threshold:
                    self.duplicate_functions.append((func1, func2, similarity))

        print(f"发现 {len(self.duplicate_functions)} 对重复函数")

    def detect_code_clones(self, min_lines: int = 5) -> None:
        """检测代码克隆（相同的代码块）"""
        print(f"\n🔍 检测代码克隆 (最小行数: {min_lines})...")

        # 收集所有代码块
        code_blocks = defaultdict(list)

        for file_path in self.src_dir.rglob("*.py"):
            if "test_" in file_path.name or "__pycache__" in str(file_path):
                continue

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()

                # 提取代码块
                for i in range(len(lines) - min_lines + 1):
                    block = "".join(lines[i : i + min_lines])
                    # 标准化代码块
                    normalized = re.sub(r"\s+", " ", block.strip())
                    normalized = re.sub(r"#.*$", "", normalized, flags=re.MULTILINE)

                    if len(normalized) > 20:  # 忽略太短的块
                        block_hash = hashlib.md5(normalized.encode()).hexdigest()
                        code_blocks[block_hash].append((file_path, i + 1))

            except Exception as e:
                print(f"⚠️  读取文件失败 {file_path}: {e}")

        # 找出重复的代码块
        for block_hash, locations in code_blocks.items():
            if len(locations) > 1:
                self.duplicate_code_blocks.append((block_hash, locations))

        print(f"发现 {len(self.duplicate_code_blocks)} 个重复代码块")

    def check_against_registry(self) -> List[str]:
        """检查是否有未注册的核心功能"""
        print(f"\n🔍 检查功能注册表合规性...")

        unregistered_classes = []

        # 核心功能关键词
        core_keywords = [
            "detector",
            "manager",
            "adapter",
            "service",
            "controller",
            "handler",
            "processor",
            "executor",
            "scheduler",
            "monitor",
        ]

        for class_elem in self.classes:
            class_name = class_elem.name.lower()

            # 检查是否是核心功能类
            is_core = any(keyword in class_name for keyword in core_keywords)

            if is_core and class_elem.name not in self.registered_functions:
                unregistered_classes.append(class_elem.name)

        if unregistered_classes:
            print(f"⚠️  发现 {len(unregistered_classes)} 个未注册的核心功能类")
        else:
            print("✅ 所有核心功能类都已注册")

        return unregistered_classes

    def generate_report(self) -> str:
        """生成检测报告"""
        report = ["\n" + "=" * 60]
        report.append("🔍 重复代码检测报告")
        report.append("=" * 60)

        # 总体统计
        report.append(f"\n📊 扫描统计:")
        report.append(f"  扫描文件数: {len(list(self.src_dir.rglob('*.py')))}")
        report.append(f"  类定义数: {len(self.classes)}")
        report.append(f"  函数定义数: {len(self.functions)}")

        # 重复检测结果
        report.append(f"\n🚨 重复检测结果:")
        report.append(f"  重复类: {len(self.duplicate_classes)}")
        report.append(f"  重复函数: {len(self.duplicate_functions)}")
        report.append(f"  代码克隆: {len(self.duplicate_code_blocks)}")

        # 详细的重复类信息
        if self.duplicate_classes:
            report.append(f"\n📋 重复类详情:")
            report.append("-" * 40)
            for class1, class2, similarity in self.duplicate_classes:
                report.append(f"\n🔸 {class1.name} (相似度: {similarity:.2f})")
                report.append(
                    f"   📁 {class1.file_path.relative_to(self.project_root)}:{class1.line_number}"
                )
                report.append(
                    f"   📁 {class2.file_path.relative_to(self.project_root)}:{class2.line_number}"
                )

                # 显示方法对比
                common_methods = set(class1.methods) & set(class2.methods)
                if common_methods:
                    report.append(f"   🔗 共同方法: {', '.join(common_methods)}")

        # 详细的重复函数信息
        if self.duplicate_functions:
            report.append(f"\n📋 重复函数详情:")
            report.append("-" * 40)
            for func1, func2, similarity in self.duplicate_functions:
                report.append(f"\n🔸 {func1.name} (相似度: {similarity:.2f})")
                report.append(
                    f"   📁 {func1.file_path.relative_to(self.project_root)}:{func1.line_number}"
                )
                report.append(
                    f"   📁 {func2.file_path.relative_to(self.project_root)}:{func2.line_number}"
                )

        # 代码克隆信息
        if self.duplicate_code_blocks:
            report.append(f"\n📋 代码克隆详情:")
            report.append("-" * 40)
            for i, (block_hash, locations) in enumerate(
                self.duplicate_code_blocks[:5]
            ):  # 只显示前5个
                report.append(f"\n🔸 代码块 #{i+1} (出现 {len(locations)} 次)")
                for file_path, line_num in locations:
                    report.append(
                        f"   📁 {file_path.relative_to(self.project_root)}:{line_num}"
                    )

            if len(self.duplicate_code_blocks) > 5:
                report.append(
                    f"   ... 还有 {len(self.duplicate_code_blocks) - 5} 个代码克隆"
                )

        # 功能注册表检查
        unregistered = self.check_against_registry()
        if unregistered:
            report.append(f"\n⚠️  未注册的核心功能:")
            for class_name in unregistered:
                report.append(f"   - {class_name}")

        # 建议
        report.append(f"\n💡 建议:")
        if self.duplicate_classes:
            report.append("  - 合并重复的类定义，保留最完整的实现")
        if self.duplicate_functions:
            report.append("  - 提取重复的函数到公共模块")
        if self.duplicate_code_blocks:
            report.append("  - 重构重复的代码块，提取为公共函数")
        if unregistered:
            report.append("  - 将核心功能类添加到功能注册表")

        if not any(
            [
                self.duplicate_classes,
                self.duplicate_functions,
                self.duplicate_code_blocks,
            ]
        ):
            report.append("  🎉 没有发现重复代码，代码结构良好！")

        return "\n".join(report)

    def save_detailed_report(self, output_path: Path) -> None:
        """保存详细的JSON报告"""
        report_data = {
            "scan_summary": {
                "total_files": len(list(self.src_dir.rglob("*.py"))),
                "total_classes": len(self.classes),
                "total_functions": len(self.functions),
            },
            "duplicate_classes": [
                {
                    "class1": {
                        "name": c1.name,
                        "file": str(c1.file_path.relative_to(self.project_root)),
                        "line": c1.line_number,
                        "methods": c1.methods,
                    },
                    "class2": {
                        "name": c2.name,
                        "file": str(c2.file_path.relative_to(self.project_root)),
                        "line": c2.line_number,
                        "methods": c2.methods,
                    },
                    "similarity": similarity,
                }
                for c1, c2, similarity in self.duplicate_classes
            ],
            "duplicate_functions": [
                {
                    "function1": {
                        "name": f1.name,
                        "file": str(f1.file_path.relative_to(self.project_root)),
                        "line": f1.line_number,
                        "signature": f1.signature,
                    },
                    "function2": {
                        "name": f2.name,
                        "file": str(f2.file_path.relative_to(self.project_root)),
                        "line": f2.line_number,
                        "signature": f2.signature,
                    },
                    "similarity": similarity,
                }
                for f1, f2, similarity in self.duplicate_functions
            ],
            "code_clones": [
                {
                    "hash": block_hash,
                    "locations": [
                        {
                            "file": str(file_path.relative_to(self.project_root)),
                            "line": line_num,
                        }
                        for file_path, line_num in locations
                    ],
                }
                for block_hash, locations in self.duplicate_code_blocks
            ],
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)

    def run_detection(
        self, similarity_threshold: float = 0.8, min_clone_lines: int = 5
    ) -> bool:
        """运行完整的重复检测"""
        print("🚀 开始重复代码检测...")

        # 加载功能注册表
        self.load_function_registry()

        # 扫描源代码
        self.scan_source_files()

        # 执行各种检测
        self.detect_duplicate_classes(similarity_threshold)
        self.detect_duplicate_functions(similarity_threshold)
        self.detect_code_clones(min_clone_lines)

        # 检查功能注册表
        unregistered = self.check_against_registry()

        # 判断是否有问题
        has_issues = bool(
            self.duplicate_classes
            or self.duplicate_functions
            or self.duplicate_code_blocks
            or unregistered
        )

        return not has_issues


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="重复代码检测工具")
    parser.add_argument(
        "--similarity", type=float, default=0.8, help="相似度阈值 (0.0-1.0)"
    )
    parser.add_argument("--min-lines", type=int, default=5, help="代码克隆的最小行数")
    parser.add_argument("--output", type=Path, help="详细报告输出文件路径")

    args = parser.parse_args()

    # 确定项目根目录
    project_root = Path(__file__).parent.parent
    if not (project_root / "src").exists():
        print("❌ 错误: 找不到src目录")
        sys.exit(1)

    # 创建检测器并运行检测
    detector = DuplicateDetector(project_root)

    try:
        no_issues = detector.run_detection(
            similarity_threshold=args.similarity, min_clone_lines=args.min_lines
        )

        # 生成并显示报告
        report = detector.generate_report()
        print(report)

        # 保存详细报告
        if args.output:
            detector.save_detailed_report(args.output)
            print(f"\n📄 详细报告已保存到: {args.output}")

        # 设置退出码
        sys.exit(0 if no_issues else 1)

    except KeyboardInterrupt:
        print("\n\n⚠️  检测被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 检测过程中发生错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
