#!/usr/bin/env python3
"""修复Python文件中的文档字符串格式问题。

这个脚本会自动为缺少句号的文档字符串添加句号。
"""

import os
from pathlib import Path
import re


def fix_docstring_in_file(file_path: Path) -> bool:
    """修复单个文件中的文档字符串。

    Args:
        file_path: 文件路径

    Returns:
        是否进行了修复
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        original_content = content

        # 匹配模块级文档字符串（文件开头的三引号字符串）
        # 处理单行文档字符串
        content = re.sub(
            r'^(\s*"""[^"\n]+)(?<!\.)"""', r'\1."""', content, flags=re.MULTILINE
        )

        # 处理多行文档字符串的第一行
        content = re.sub(
            r'^(\s*"""[^"\n]+)(?<!\.)\n', r"\1.\n", content, flags=re.MULTILINE
        )

        # 匹配函数/类/方法的文档字符串
        # 处理单行文档字符串
        content = re.sub(r'(\s+"""[^"\n]+)(?<!\.)"""', r'\1."""', content)

        # 处理多行文档字符串的第一行
        content = re.sub(r'(\s+"""[^"\n]+)(?<!\.)\n', r"\1.\n", content)

        # 处理单引号文档字符串
        content = re.sub(r"(\s*'''[^'\n]+)(?<!\.)'''", r"\1.'''", content)

        content = re.sub(r"(\s*'''[^'\n]+)(?<!\.)\n", r"\1.\n", content)

        if content != original_content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return True

        return False

    except Exception as e:
        print(f"处理文件 {file_path} 时出错: {e}")
        return False


def main():
    """主函数。"""
    src_dir = Path("src")
    if not src_dir.exists():
        print("src目录不存在")
        return

    fixed_count = 0
    total_files = 0

    # 遍历所有Python文件
    for py_file in src_dir.rglob("*.py"):
        total_files += 1
        if fix_docstring_in_file(py_file):
            fixed_count += 1
            print(f"修复了文件: {py_file}")

    print(f"\n总共检查了 {total_files} 个文件")
    print(f"修复了 {fixed_count} 个文件")


if __name__ == "__main__":
    main()
