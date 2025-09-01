#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
崩坏星穹铁道自动化助手 - MVP模式主程序入口

使用MVP架构模式重构的主程序入口
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

from src.core.config_manager import ConfigManager
from src.core.logger import setup_logger
from src.database.db_manager import DatabaseManager
from src.application.task_application_service import TaskApplicationService
from src.application.automation_application_service import AutomationApplicationService
from src.ui.sync_adapter import SyncAdapter
from src.ui.main_window import MainWindowModel, MainWindowView, MainWindowPresenter


def setup_application():
    """初始化应用程序配置"""
    # 设置应用程序属性
    QApplication.setApplicationName("崩坏星穹铁道自动化助手")
    QApplication.setApplicationVersion("2.0.0")
    QApplication.setOrganizationName("HSR Automation")
    QApplication.setOrganizationDomain("hsr-automation.local")


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


def initialize_services(config_manager: ConfigManager, db_manager: DatabaseManager):
    """初始化应用服务层"""
    from src.services.event_bus import EventBus
    from src.automation.game_detector import GameDetector
    from src.automation.automation_controller import AutomationController
    from src.services.task_service import TaskService
    from src.repositories.sqlite_task_repository import SQLiteTaskRepository
    
    # 初始化事件总线
    event_bus = EventBus()
    
    # 初始化任务数据访问层
    task_repository = SQLiteTaskRepository(db_manager.db_path)
    
    # 初始化任务领域服务
    task_domain_service = TaskService(task_repository, event_bus)
    
    # 初始化任务应用服务
    task_service = TaskApplicationService(task_domain_service, event_bus)
    
    # 初始化游戏检测器和自动化控制器
    game_detector = GameDetector(config_manager)
    automation_controller = AutomationController(config_manager, db_manager, game_detector)
    
    # 初始化自动化服务
    automation_service = AutomationApplicationService(
        game_detector=game_detector,
        automation_controller=automation_controller,
        event_bus=event_bus
    )
    
    return task_service, automation_service


def create_mvp_components(task_service: TaskApplicationService, 
                         automation_service: AutomationApplicationService,
                         config_manager: ConfigManager):
    """创建MVP组件"""
    # 创建同步适配器
    sync_adapter = SyncAdapter()
    
    # 创建Model
    model = MainWindowModel(
        task_service=task_service,
        automation_service=automation_service,
        config_manager=config_manager
    )
    
    # 创建View
    view = MainWindowView()
    
    # 创建Presenter
    presenter = MainWindowPresenter(
        model=model,
        view=view,
        sync_adapter=sync_adapter,
        task_service=task_service,
        automation_controller=automation_service.automation_controller,
        monitoring_service=None,  # 暂时设为None
        performance_monitor=None  # 暂时设为None
    )
    
    return model, view, presenter, sync_adapter


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
        logger.info("MVP模式应用程序启动")
        
        # 初始化配置管理器
        config_manager = ConfigManager()
        
        # 初始化数据库
        db_manager = DatabaseManager()
        db_manager.initialize_database()
        
        # 初始化服务层
        task_service, automation_service = initialize_services(config_manager, db_manager)
        
        # 创建MVP组件
        model, view, presenter, sync_adapter = create_mvp_components(
            task_service, automation_service, config_manager
        )
        
        # 设置应用图标
        icon_path = project_root / "assets" / "icon.ico"
        if icon_path.exists():
            app.setWindowIcon(QIcon(str(icon_path)))
        
        # 显示主窗口
        view.show()
        
        logger.info("MVP模式主窗口已显示")
        
        # 运行应用程序
        exit_code = app.exec()
        
        # 清理资源
        presenter.cleanup()
        sync_adapter.close()
        
        logger.info(f"应用程序退出，退出码: {exit_code}")
        return exit_code
        
    except Exception as e:
        print(f"应用程序启动失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())