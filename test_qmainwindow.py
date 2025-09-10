#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试QMainWindow创建时机
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_qmainwindow_creation():
    """测试QMainWindow创建时机."""
    print("=== 测试QMainWindow创建时机 ===")
    
    try:
        print("1. 导入PyQt5...")
        from PyQt5.QtWidgets import QMainWindow, QApplication
        
        print("2. 尝试创建QMainWindow（无QApplication）...")
        window = QMainWindow()
        print("QMainWindow创建成功！")
        
    except Exception as e:
        print(f"QMainWindow创建失败: {e}")
        
    try:
        print("3. 创建QApplication...")
        app = QApplication([])
        
        print("4. 创建QMainWindow（有QApplication）...")
        window = QMainWindow()
        print("QMainWindow创建成功！")
        
        app.quit()
        
    except Exception as e:
        print(f"QMainWindow创建失败: {e}")

if __name__ == "__main__":
    test_qmainwindow_creation()