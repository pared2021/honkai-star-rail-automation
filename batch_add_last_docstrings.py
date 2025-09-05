#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批量添加最后剩余文档字符串的脚本。"""

import os
from pathlib import Path

# 定义需要添加文档字符串的文件和对应的描述
files_to_process = {
    'src/application/error_handling_service.py': '错误处理服务模块。\n\n提供应用程序级别的错误处理服务。',
    'src/config/error_recovery_strategies.py': '错误恢复策略配置模块。\n\n定义错误恢复的策略配置。',
    'src/core/action_executor.py': '动作执行器模块。\n\n提供动作的执行功能。',
    'src/core/app.py': '核心应用程序模块。\n\n提供应用程序的核心功能。',
    'src/core/config_manager.py': '核心配置管理器模块。\n\n提供核心系统的配置管理功能。',
    'src/core/container.py': '依赖注入容器模块。\n\n提供依赖注入容器功能。',
    'src/core/container_config.py': '容器配置模块。\n\n提供依赖注入容器的配置。',
    'src/core/dependency_injection.py': '依赖注入模块。\n\n提供依赖注入的实现。',
    'src/core/enums.py': '枚举定义模块。\n\n定义核心系统使用的枚举类型。',
    'src/core/error_handling.py': '错误处理模块。\n\n提供错误处理和异常管理功能。',
    'src/core/error_recovery_coordinator.py': '错误恢复协调器模块。\n\n提供错误恢复的协调功能。',
    'src/core/event_bus.py': '事件总线模块。\n\n提供事件的发布和订阅功能。',
    'src/core/events.py': '事件定义模块。\n\n定义系统使用的事件类型。',
    'src/core/exception_recovery.py': '异常恢复模块。\n\n提供异常恢复功能。',
    'src/core/game_operations.py': '游戏操作模块。\n\n提供游戏相关的操作功能。',
    'src/core/intelligent_scheduler.py': '智能调度器模块。\n\n提供智能任务调度功能。',
    'src/core/interfaces/cache_manager_interface.py': '缓存管理器接口模块。\n\n定义缓存管理器的接口。',
    'src/core/interfaces/executor_interface.py': '执行器接口模块。\n\n定义执行器的接口。',
    'src/core/interfaces/i_action_config_service.py': '动作配置服务接口模块。\n\n定义动作配置服务的接口。'
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
    print('开始批量添加最后剩余文档字符串...')
    
    for file_path, description in files_to_process.items():
        add_docstring_to_file(file_path, description)
    
    print('\n批量添加最后剩余文档字符串完成！')

if __name__ == '__main__':
    main()