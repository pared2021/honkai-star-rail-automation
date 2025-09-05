#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试模块导入问题
"""

from pathlib import Path
import sys

# 添加src目录到路径
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

print("开始测试导入...")

try:
    print("1. 测试导入 DatabaseManager...")
    from database.db_manager import DatabaseManager

    print("   DatabaseManager 导入成功")

    print("2. 创建 DatabaseManager 实例...")
    db = DatabaseManager()
    print("   DatabaseManager 实例创建成功")

    print("3. 初始化数据库...")
    db.initialize_database()
    print("   数据库初始化成功")

    print("4. 检查 get_task_config 方法...")
    has_method = hasattr(db, "get_task_config")
    print(f"   get_task_config 方法存在: {has_method}")

    if has_method:
        print("5. 测试调用 get_task_config 方法...")
        try:
            result = db.get_task_config("test_task_id")
            print(f"   get_task_config 调用成功，返回: {result}")
        except Exception as e:
            print(f"   get_task_config 调用失败: {e}")

    print("6. 列出 DatabaseManager 的所有方法...")
    methods = [m for m in dir(db) if not m.startswith("_") and callable(getattr(db, m))]
    print(f"   方法列表: {methods}")

except Exception as e:
    print(f"导入失败: {e}")
    import traceback

    traceback.print_exc()

print("测试完成")
