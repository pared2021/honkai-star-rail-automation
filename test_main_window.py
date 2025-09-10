#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的主窗口测试脚本
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_import_only():
    """仅测试导入功能"""
    try:
        print("正在导入主窗口组件...")
        from src.ui.main_window.main_window_view import MainWindowView
        print("主窗口组件导入成功！")
        return 0
        
    except Exception as e:
        print(f"主窗口组件导入失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

def test_with_qapp():
    """测试创建主窗口（使用QApplication）."""
    from PyQt5.QtWidgets import QApplication
    
    print("正在导入主窗口组件...")
    from src.ui.main_window.main_window_mvp import MainWindowView
    
    print("正在创建QApplication...")
    app = QApplication([])
    
    print("正在创建主窗口...")
    window_view = MainWindowView()
    
    print("正在设置UI...")
    window_view.ensure_ui_setup()
    window = window_view.get_window()
    print("主窗口创建成功！")
    print(f"窗口标题: {window.windowTitle()}")
    
    # 不显示窗口，只测试创建
    app.quit()

if __name__ == "__main__":
    print("=== 测试1: 仅导入组件 ===")
    result1 = test_import_only()
    
    if result1 == 0:
        print("\n=== 测试2: 创建主窗口 ===")
        result2 = test_with_qapp()
        sys.exit(result2)
    else:
        sys.exit(result1)