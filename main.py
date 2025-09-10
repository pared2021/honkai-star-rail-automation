#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
崩坏星穹铁道自动化助手主程序。

这是应用程序的主入口点。
"""

import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def main():
    """主函数。"""
    # 创建QApplication
    app = QApplication(sys.argv)
    
    # 设置应用程序属性
    app.setApplicationName("崩坏星穹铁道自动化助手")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("XingTie Automation")
    
    # 设置高DPI支持
    app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    try:
        # 导入并创建主窗口
        from src.ui.main_window.main_window_view import MainWindowView
        
        # 创建主窗口视图
        window_view = MainWindowView()
        
        # 确保UI设置完成
        window_view.ensure_ui_setup()
        
        # 获取主窗口并显示
        window = window_view.get_window()
        window.show()
        
        print("崩坏星穹铁道自动化助手已启动")
        print(f"窗口标题: {window.windowTitle()}")
        print(f"窗口大小: {window.size().width()}x{window.size().height()}")
        
        # 运行应用程序
        return app.exec_()
        
    except Exception as e:
        print(f"启动失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
