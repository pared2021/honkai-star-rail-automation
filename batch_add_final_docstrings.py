#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批量添加最后剩余文档字符串的脚本。"""

import os
from pathlib import Path

# 定义需要添加文档字符串的文件和对应的描述
files_to_process = {
    "src/database/migrate.py": "数据库迁移模块。\n\n提供数据库迁移的执行和管理功能。",
    "src/infrastructure/architecture_validator.py": "架构验证器模块。\n\n提供系统架构的验证和检查功能。",
    "src/interfaces/infrastructure/__init__.py": "基础设施接口包。\n\n定义基础设施相关的接口。",
    "src/interfaces/infrastructure/architecture_validation_interface.py": "架构验证接口模块。\n\n定义架构验证的接口。",
    "src/interfaces/infrastructure/architecture_validation_types.py": "架构验证类型模块。\n\n定义架构验证相关的数据类型。",
    "src/interfaces/infrastructure/cache_interface.py": "缓存接口模块。\n\n定义缓存服务的接口。",
    "src/interfaces/infrastructure/configuration_interface.py": "配置接口模块。\n\n定义配置管理的接口。",
    "src/interfaces/infrastructure/configuration_types.py": "配置类型模块。\n\n定义配置相关的数据类型。",
    "src/interfaces/infrastructure/dependency_injection_interface.py": "依赖注入接口模块。\n\n定义依赖注入的接口。",
    "src/interfaces/infrastructure/dependency_injection_types.py": "依赖注入类型模块。\n\n定义依赖注入相关的数据类型。",
    "src/interfaces/infrastructure/event_bus_interface.py": "事件总线接口模块。\n\n定义事件总线的接口。",
    "src/interfaces/infrastructure/filesystem_interface.py": "文件系统接口模块。\n\n定义文件系统操作的接口。",
    "src/interfaces/infrastructure/filesystem_types.py": "文件系统类型模块。\n\n定义文件系统相关的数据类型。",
    "src/interfaces/infrastructure/logger_interface.py": "日志接口模块。\n\n定义日志服务的接口。",
    "src/interfaces/infrastructure/messaging_interface.py": "消息接口模块。\n\n定义消息传递的接口。",
    "src/interfaces/infrastructure/messaging_types.py": "消息类型模块。\n\n定义消息相关的数据类型。",
    "src/interfaces/infrastructure/network_interface.py": "网络接口模块。\n\n定义网络服务的接口。",
    "src/interfaces/infrastructure/network_types.py": "网络类型模块。\n\n定义网络相关的数据类型。",
    "src/interfaces/infrastructure/security_interface.py": "安全接口模块。\n\n定义安全服务的接口。",
    "src/interfaces/repositories/__init__.py": "仓储接口包。\n\n定义数据仓储相关的接口。",
    "src/interfaces/services/__init__.py": "服务接口包。\n\n定义业务服务相关的接口。",
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
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(docstring_content)
        print(f"已为 {file_path} 添加文档字符串")
    else:
        print(f"文件 {file_path} 已存在且非空，跳过")


def main():
    """主函数。"""
    print("开始批量添加最后剩余文档字符串...")

    for file_path, description in files_to_process.items():
        add_docstring_to_file(file_path, description)

    print("\n批量添加最后剩余文档字符串完成！")


if __name__ == "__main__":
    main()
