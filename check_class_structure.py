#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查 TaskManager 类结构
"""

import sys
from pathlib import Path
import ast

# 添加src目录到路径
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

def check_class_methods():
    """检查 TaskManager 类的方法结构"""
    task_manager_file = Path("src/core/task_manager.py")
    
    if not task_manager_file.exists():
        print(f"文件不存在: {task_manager_file}")
        return
    
    try:
        with open(task_manager_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 解析 AST
        tree = ast.parse(content)
        
        # 查找 TaskManager 类
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == 'TaskManager':
                print(f"找到 TaskManager 类，行号: {node.lineno}")
                print("类中的方法:")
                
                methods = []
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        methods.append((item.name, item.lineno))
                
                for method_name, line_no in sorted(methods, key=lambda x: x[1]):
                    print(f"  - {method_name} (行号: {line_no})")
                
                # 检查是否有 get_task_sync 方法
                has_get_task_sync = any(name == 'get_task_sync' for name, _ in methods)
                print(f"\nget_task_sync 方法存在: {has_get_task_sync}")
                
                return
        
        print("未找到 TaskManager 类")
        
    except SyntaxError as e:
        print(f"语法错误: {e}")
        print(f"行号: {e.lineno}, 列号: {e.offset}")
    except Exception as e:
        print(f"解析失败: {e}")

if __name__ == "__main__":
    check_class_methods()