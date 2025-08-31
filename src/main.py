#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
崩坏：星穹铁道自动化工具
主程序入口
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from loguru import logger

# 导入主窗口
from src.gui.main_window import MainWindow


def setup_logging():
    """设置日志配置"""
    # 创建logs目录
    logs_dir = project_root / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    # 配置loguru
    logger.remove()  # 移除默认处理器
    
    # 添加控制台输出
    logger.add(
        sys.stderr,
        level="INFO",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )
    
    # 添加文件输出
    logger.add(
        logs_dir / "app_{time:YYYY-MM-DD}.log",
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="1 day",
        retention="7 days",
        compression="zip",
        encoding="utf-8"
    )
    
    # 添加错误日志文件
    logger.add(
        logs_dir / "error_{time:YYYY-MM-DD}.log",
        level="ERROR",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="1 day",
        retention="30 days",
        compression="zip",
        encoding="utf-8"
    )


def setup_application():
    """设置应用程序"""
    # 设置应用程序属性
    QApplication.setApplicationName("崩坏：星穹铁道自动化工具")
    QApplication.setApplicationVersion("1.0.0")
    QApplication.setOrganizationName("StarRail Automation")
    QApplication.setOrganizationDomain("starrail-automation.local")
    
    # 启用高DPI支持 (PyQt6中这些属性已经默认启用，不需要手动设置)
    # QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    # QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)


def main():
    """主函数"""
    try:
        # 设置日志
        setup_logging()
        logger.info("启动崩坏：星穹铁道自动化工具")
        
        # 设置应用程序
        setup_application()
        
        # 创建应用程序实例
        app = QApplication(sys.argv)
        
        # 设置应用程序图标（如果存在）
        icon_path = project_root / "resources" / "icon.ico"
        if icon_path.exists():
            app.setWindowIcon(QIcon(str(icon_path)))
        
        # 创建主窗口
        main_window = MainWindow()
        main_window.show()
        
        logger.info("应用程序界面已启动")
        
        # 运行应用程序
        exit_code = app.exec()
        
        logger.info(f"应用程序退出，退出代码: {exit_code}")
        return exit_code
        
    except Exception as e:
        logger.exception(f"应用程序启动失败: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())