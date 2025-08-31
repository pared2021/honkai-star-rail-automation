#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
崩坏星穹铁道自动化助手 - 主程序入口

这是一个实际可用的桌面自动化工具，专为《崩坏：星穹铁道》游戏设计。
提供完整的自动化功能，包括日常任务、材料刷取、状态监控等。
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QDir
from PyQt6.QtGui import QIcon

from src.gui.main_window import MainWindow
from src.core.config_manager import ConfigManager
from src.core.logger import setup_logger
from src.database.db_manager import DatabaseManager


def setup_application():
    """初始化应用程序配置"""
    # 设置应用程序属性
    QApplication.setApplicationName("崩坏星穹铁道自动化助手")
    QApplication.setApplicationVersion("1.0.0")
    QApplication.setOrganizationName("HSR Automation")
    QApplication.setOrganizationDomain("hsr-automation.local")
    
    # 启用高DPI支持（PyQt6中已默认启用，这些属性已被移除）
    # QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    # QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)


def create_directories():
    """创建必要的目录结构"""
    directories = [
        "data",
        "logs",
        "config",
        "assets/images",
        "assets/templates",
        "temp"
    ]
    
    for directory in directories:
        dir_path = project_root / directory
        dir_path.mkdir(parents=True, exist_ok=True)


def main():
    """主函数"""
    try:
        # 设置应用程序
        setup_application()
        
        # 创建QApplication实例
        app = QApplication(sys.argv)
        
        # 创建必要目录
        create_directories()
        
        # 初始化日志系统
        logger = setup_logger()
        logger.info("应用程序启动")
        
        # 初始化配置管理器
        config_manager = ConfigManager()
        
        # 初始化数据库
        db_manager = DatabaseManager()
        db_manager.initialize_database()
        
        # 创建主窗口，传递数据库管理器
        main_window = MainWindow(config_manager=config_manager, db_manager=db_manager)
        main_window.show()
        
        logger.info("主窗口已显示")
        
        # 运行应用程序
        exit_code = app.exec()
        
        logger.info(f"应用程序退出，退出码: {exit_code}")
        return exit_code
        
    except Exception as e:
        print(f"应用程序启动失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())