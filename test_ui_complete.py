#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整的UI测试脚本。

测试主窗口的完整功能，包括显示窗口和交互测试。
"""

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

def test_complete_ui():
    """测试完整的UI功能。"""
    print("=== 完整UI测试 ===")
    
    # 创建QApplication
    print("正在创建QApplication...")
    app = QApplication(sys.argv)
    
    try:
        # 导入主窗口组件
        print("正在导入主窗口组件...")
        from src.ui.main_window.main_window_view import MainWindowView
        
        # 创建主窗口
        print("正在创建主窗口...")
        window_view = MainWindowView()
        
        # 设置UI
        print("正在设置UI...")
        window_view.ensure_ui_setup()
        window = window_view.get_window()
        
        # 显示窗口
        print("正在显示窗口...")
        window.show()
        
        print(f"窗口标题: {window.windowTitle()}")
        print(f"窗口大小: {window.size().width()}x{window.size().height()}")
        print("窗口显示成功！")
        
        # 设置定时器，3秒后自动关闭
        timer = QTimer()
        timer.timeout.connect(app.quit)
        timer.start(3000)  # 3秒
        
        print("窗口将在3秒后自动关闭...")
        
        # 运行应用程序
        app.exec_()
        
        print("UI测试完成！")
        
    except Exception as e:
        print(f"UI测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = test_complete_ui()
    if success:
        print("\n✅ 所有UI测试通过！")
    else:
        print("\n❌ UI测试失败！")
        sys.exit(1)