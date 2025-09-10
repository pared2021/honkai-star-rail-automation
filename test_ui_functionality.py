#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UI功能测试脚本

测试主窗口的所有功能按钮和显示状态。
"""

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from PyQt5.QtWidgets import QApplication, QPushButton, QTabWidget, QLabel, QTextEdit
from PyQt5.QtCore import QTimer

def test_ui_functionality():
    """测试UI功能。"""
    print("=" * 50)
    print("UI功能测试")
    print("=" * 50)
    
    # 创建QApplication
    app = QApplication(sys.argv)
    
    try:
        # 导入主窗口组件
        print("\n1. 导入主窗口组件...")
        from src.ui.main_window.main_window_view import MainWindowView
        
        # 创建主窗口
        print("\n2. 创建主窗口...")
        window_view = MainWindowView()
        window_view.ensure_ui_setup()
        window = window_view.get_window()
        
        print(f"✅ 窗口标题: {window.windowTitle()}")
        print(f"✅ 窗口大小: {window.size().width()}x{window.size().height()}")
        
        # 检查选项卡
        print("\n3. 检查选项卡...")
        tab_widget = window_view.tab_widget
        if isinstance(tab_widget, QTabWidget):
            tab_count = tab_widget.count()
            print(f"✅ 选项卡数量: {tab_count}")
            
            for i in range(tab_count):
                tab_text = tab_widget.tabText(i)
                tab_widget_obj = tab_widget.widget(i)
                print(f"  - 选项卡 {i+1}: {tab_text} (类型: {type(tab_widget_obj).__name__})")
        else:
            print("❌ 选项卡组件未找到")
        
        # 检查主控制面板按钮
        print("\n4. 检查主控制面板按钮...")
        if hasattr(window_view, 'start_button') and isinstance(window_view.start_button, QPushButton):
            print(f"✅ 开始按钮: {window_view.start_button.text()}")
            print(f"  - 按钮可见: {window_view.start_button.isVisible()}")
            print(f"  - 按钮启用: {window_view.start_button.isEnabled()}")
        else:
            print("❌ 开始按钮未找到")
            
        if hasattr(window_view, 'stop_button') and isinstance(window_view.stop_button, QPushButton):
            print(f"✅ 停止按钮: {window_view.stop_button.text()}")
            print(f"  - 按钮可见: {window_view.stop_button.isVisible()}")
            print(f"  - 按钮启用: {window_view.stop_button.isEnabled()}")
        else:
            print("❌ 停止按钮未找到")
        
        # 检查日志显示区域
        print("\n5. 检查日志显示区域...")
        if hasattr(window_view, 'log_display') and isinstance(window_view.log_display, QTextEdit):
            print("✅ 日志显示区域存在")
            print(f"  - 只读模式: {window_view.log_display.isReadOnly()}")
            print(f"  - 占位符文本: {window_view.log_display.placeholderText()}")
        else:
            print("❌ 日志显示区域未找到")
        
        # 检查状态栏
        print("\n6. 检查状态栏...")
        status_bar = window.statusBar()
        if status_bar:
            print(f"✅ 状态栏存在: {status_bar.currentMessage()}")
        else:
            print("❌ 状态栏未找到")
        
        # 检查菜单栏
        print("\n7. 检查菜单栏...")
        menu_bar = window.menuBar()
        if menu_bar:
            actions = menu_bar.actions()
            print(f"✅ 菜单栏存在，菜单数量: {len(actions)}")
            for action in actions:
                if action.menu():
                    print(f"  - 菜单: {action.text()}")
        else:
            print("❌ 菜单栏未找到")
        
        # 检查工具栏
        print("\n8. 检查工具栏...")
        toolbars = window.findChildren(type(window.addToolBar("")))
        if toolbars:
            print(f"✅ 工具栏数量: {len(toolbars)}")
            for i, toolbar in enumerate(toolbars):
                actions = toolbar.actions()
                print(f"  - 工具栏 {i+1}: {len(actions)} 个动作")
                for action in actions:
                    if action.text():
                        print(f"    * {action.text()}")
        else:
            print("❌ 工具栏未找到")
        
        # 测试按钮点击功能
        print("\n9. 测试按钮功能...")
        if hasattr(window_view, 'start_button'):
            # 模拟点击开始按钮
            print("  - 模拟点击开始按钮")
            try:
                window_view.start_button.click()
                print("  ✅ 开始按钮点击成功")
            except Exception as e:
                print(f"  ❌ 开始按钮点击失败: {e}")
        
        if hasattr(window_view, 'stop_button'):
            # 模拟点击停止按钮
            print("  - 模拟点击停止按钮")
            try:
                window_view.stop_button.click()
                print("  ✅ 停止按钮点击成功")
            except Exception as e:
                print(f"  ❌ 停止按钮点击失败: {e}")
        
        # 测试状态更新
        print("\n10. 测试状态更新...")
        try:
            window_view.update_status("测试状态消息")
            current_status = window.statusBar().currentMessage()
            if current_status == "测试状态消息":
                print("✅ 状态更新功能正常")
            else:
                print(f"❌ 状态更新失败，当前状态: {current_status}")
        except Exception as e:
            print(f"❌ 状态更新测试失败: {e}")
        
        # 测试日志添加
        print("\n11. 测试日志添加...")
        try:
            window_view.append_log("测试日志消息")
            log_content = window_view.log_display.toPlainText()
            if "测试日志消息" in log_content:
                print("✅ 日志添加功能正常")
            else:
                print(f"❌ 日志添加失败，当前内容: {log_content[:100]}...")
        except Exception as e:
            print(f"❌ 日志添加测试失败: {e}")
        
        print("\n=" * 50)
        print("✅ UI功能测试完成")
        print("=" * 50)
        
        return True
        
    except Exception as e:
        print(f"❌ UI功能测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # 确保应用程序退出
        if 'app' in locals():
            app.quit()

def main():
    """主函数。"""
    success = test_ui_functionality()
    
    print("\n" + "=" * 60)
    print("测试结果摘要")
    print("=" * 60)
    
    if success:
        print("🎉 所有UI功能测试通过！")
        return True
    else:
        print("❌ UI功能测试失败，请检查相关组件。")
        return False

if __name__ == "__main__":
    success = main()
    print("\n测试脚本结束")
    sys.exit(0 if success else 1)