#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批量添加核心模块文档字符串的脚本。"""

import os
from pathlib import Path

# 定义需要添加文档字符串的文件和对应的描述
files_to_process = {
    'src/core/interfaces/__init__.py': '核心接口包。\n\n定义核心模块的接口。',
    'src/core/interfaces/automation_interface.py': '自动化接口模块。\n\n定义自动化功能的接口。',
    'src/core/interfaces/cache_interface.py': '缓存接口模块。\n\n定义缓存服务的接口。',
    'src/core/interfaces/config_interface.py': '配置接口模块。\n\n定义配置管理的接口。',
    'src/core/interfaces/database_interface.py': '数据库接口模块。\n\n定义数据库操作的接口。',
    'src/core/interfaces/event_interface.py': '事件接口模块。\n\n定义事件处理的接口。',
    'src/core/interfaces/game_detector_interface.py': '游戏检测器接口模块。\n\n定义游戏检测功能的接口。',
    'src/core/interfaces/logger_interface.py': '日志接口模块。\n\n定义日志服务的接口。',
    'src/core/interfaces/monitor_interface.py': '监控接口模块。\n\n定义监控服务的接口。',
    'src/core/interfaces/resource_manager_interface.py': '资源管理器接口模块。\n\n定义资源管理的接口。',
    'src/core/interfaces/scheduler_interface.py': '调度器接口模块。\n\n定义任务调度的接口。',
    'src/core/interfaces/task_manager_interface.py': '任务管理器接口模块。\n\n定义任务管理的接口。',
    'src/core/logger.py': '核心日志模块。\n\n提供核心系统的日志功能。',
    'src/core/managers/__init__.py': '管理器包。\n\n定义各种管理器模块。',
    'src/core/managers/task_cache_manager.py': '任务缓存管理器模块。\n\n提供任务缓存的管理功能。',
    'src/core/managers/task_executor.py': '任务执行器模块。\n\n提供任务的执行功能。',
    'src/core/managers/task_monitor.py': '任务监控器模块。\n\n提供任务监控功能。',
    'src/core/managers/task_resource_manager.py': '任务资源管理器模块。\n\n提供任务资源的管理功能。',
    'src/core/managers/task_scheduler.py': '任务调度器模块。\n\n提供任务调度功能。',
    'src/core/performance_monitor.py': '性能监控器模块。\n\n提供系统性能监控功能。',
    'src/core/refactored_task_manager.py': '重构任务管理器模块。\n\n提供重构后的任务管理功能。',
    'src/core/service_locator.py': '服务定位器模块。\n\n提供服务的定位和管理功能。',
    'src/core/services/__init__.py': '核心服务包。\n\n定义核心服务模块。',
    'src/core/services/action_config_service.py': '动作配置服务模块。\n\n提供动作配置的服务功能。',
    'src/core/task_actions.py': '任务动作模块。\n\n定义任务的各种动作。',
    'src/core/task_cache_manager.py': '任务缓存管理器模块。\n\n提供任务缓存管理功能。',
    'src/core/task_database_manager.py': '任务数据库管理器模块。\n\n提供任务数据库管理功能。',
    'src/core/task_executor.py': '任务执行器模块。\n\n提供任务执行功能。',
    'src/core/task_resource_manager.py': '任务资源管理器模块。\n\n提供任务资源管理功能。',
    'src/core/task_retry_manager.py': '任务重试管理器模块。\n\n提供任务重试管理功能。',
    'src/core/task_scheduler.py': '任务调度器模块。\n\n提供任务调度功能。',
    'src/core/task_status_monitor.py': '任务状态监控器模块。\n\n提供任务状态监控功能。',
    'src/core/task_validator.py': '任务验证器模块。\n\n提供任务验证功能。',
    'src/core/types/__init__.py': '核心类型包。\n\n定义核心模块的数据类型。',
    'src/core/types/resource_types.py': '资源类型模块。\n\n定义资源相关的数据类型。',
    'src/database/db_manager.py': '数据库管理器模块。\n\n提供数据库的管理和操作功能。'
}

def add_docstring_to_file(file_path: str, description: str):
    """为文件添加文档字符串。"""
    full_path = Path(file_path)
    
    # 确保目录存在
    full_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 创建文档字符串内容
    docstring_content = f'"""{ description}\n"""\n'
    
    # 如果文件不存在或为空，创建文件并添加文档字符串
    if not full_path.exists() or full_path.stat().st_size == 0:
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(docstring_content)
        print(f'已为 {file_path} 添加文档字符串')
    else:
        print(f'文件 {file_path} 已存在且非空，跳过')

def main():
    """主函数。"""
    print('开始批量添加核心模块文档字符串...')
    
    for file_path, description in files_to_process.items():
        add_docstring_to_file(file_path, description)
    
    print('\n批量添加核心模块文档字符串完成！')

if __name__ == '__main__':
    main()