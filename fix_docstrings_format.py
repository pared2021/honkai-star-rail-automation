#!/usr/bin/env python3
"""批量修复docstring格式脚本.

将所有Python文件中的中文句号改为英文句号以符合flake8 D400规则.
"""

import os
import re


def fix_docstring_format(file_path):
    """修复单个文件的docstring格式.
    
    Args:
        file_path: 文件路径
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 替换docstring中的中文句号为英文句号
        # 匹配 """开头的docstring第一行
        pattern = r'("""[^"\n]+)。'
        replacement = r'\1.'
        
        new_content = re.sub(pattern, replacement, content)
        
        if new_content != content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"已修复: {file_path}")
    except Exception as e:
        print(f"修复失败 {file_path}: {e}")


def main():
    """主函数."""
    src_dir = 'src'
    
    for root, dirs, files in os.walk(src_dir):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                fix_docstring_format(file_path)
    
    print("批量修复完成！")


if __name__ == '__main__':
    main()