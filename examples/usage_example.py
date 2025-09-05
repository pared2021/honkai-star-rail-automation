#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重构后架构使用示例

展示如何使用新的依赖注入架构和专门管理器。
"""

import logging
from typing import Any, Dict

import asyncio

from src.core.app import create_app, get_app
from src.core.events.task_events import TaskCreatedEvent, TaskStatusChangedEvent
from src.core.models.task import Task, TaskConfig, TaskPriority, TaskStatus, TaskType

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def example_task_management():
    """任务管理示例"""
    logger.info("=== 任务管理示例 ===")

    # 获取任务管理器
    task_manager = get_app().task_manager

    # 创建任务配置
    config = TaskConfig(
        max_retries=3,
        timeout=300,
        parameters={"input_file": "data.txt", "output_dir": "/tmp/output"},
    )

    # 创建任务
    task = await task_manager.create_task(
        name="数据处理任务",
        task_type=TaskType.DATA_PROCESSING,
        config=config,
        user_id="user123",
        priority=TaskPriority.HIGH,
    )

    logger.info(f"创建任务: {task.id} - {task.name}")

    # 获取任务
    retrieved_task = await task_manager.get_task(task.id, "user123")
    logger.info(f"获取任务: {retrieved_task.name} - 状态: {retrieved_task.status}")

    # 执行任务
    await task_manager.execute_task(task.id, "user123")
    logger.info(f"任务执行已启动: {task.id}")

    # 等待一段时间
    await asyncio.sleep(2)

    # 检查任务状态
    updated_task = await task_manager.get_task(task.id, "user123")
    logger.info(f"任务状态更新: {updated_task.status}")

    # 获取任务列表
    tasks = await task_manager.list_tasks(
        user_id="user123", status=TaskStatus.RUNNING, limit=10
    )
    logger.info(f"运行中的任务数量: {len(tasks)}")

    # 获取任务统计
    stats = await task_manager.get_task_statistics("user123")
    logger.info(f"任务统计: {stats}")


async def example_event_handling():
    """事件处理示例"""
    logger.info("=== 事件处理示例 ===")

    # 获取事件总线
    event_bus = get_app().event_bus

    # 定义事件处理器
    async def on_task_created(event: TaskCreatedEvent):
        logger.info(f"任务创建事件: {event.task_id} - {event.task_name}")

    async def on_task_status_changed(event: TaskStatusChangedEvent):
        logger.info(
            f"任务状态变更: {event.task_id} - {event.old_status} -> {event.new_status}"
        )

    # 订阅事件
    await event_bus.subscribe(TaskCreatedEvent, on_task_created)
    await event_bus.subscribe(TaskStatusChangedEvent, on_task_status_changed)

    # 发布事件
    await event_bus.publish(
        TaskCreatedEvent(
            task_id="task123",
            task_name="测试任务",
            user_id="user123",
            task_type=TaskType.PYTHON_SCRIPT,
        )
    )

    await event_bus.publish(
        TaskStatusChangedEvent(
            task_id="task123",
            old_status=TaskStatus.PENDING,
            new_status=TaskStatus.RUNNING,
            user_id="user123",
        )
    )

    # 等待事件处理
    await asyncio.sleep(1)

    # 获取事件统计
    stats = await event_bus.get_statistics()
    logger.info(f"事件统计: {stats}")


async def example_cache_usage():
    """缓存使用示例"""
    logger.info("=== 缓存使用示例 ===")

    # 获取缓存管理器
    cache_manager = get_app().cache_manager

    # 缓存数据
    await cache_manager.set(
        "user:123:profile",
        {"name": "张三", "email": "zhangsan@example.com", "role": "admin"},
        ttl=3600,
    )

    # 获取缓存数据
    profile = await cache_manager.get("user:123:profile")
    logger.info(f"用户资料: {profile}")

    # 缓存任务结果
    await cache_manager.cache_task_result(
        "task123",
        {
            "status": "completed",
            "result": "处理完成",
            "output_files": ["/tmp/output/result.txt"],
        },
    )

    # 获取任务结果
    result = await cache_manager.get_task_result("task123")
    logger.info(f"任务结果: {result}")

    # 获取缓存统计
    stats = await cache_manager.get_statistics()
    logger.info(f"缓存统计: {stats}")


async def example_configuration():
    """配置管理示例"""
    logger.info("=== 配置管理示例 ===")

    # 获取配置管理器
    config_manager = get_app().config_manager

    # 设置配置
    await config_manager.set_config("app.name", "星铁任务管理系统")
    await config_manager.set_config("app.version", "2.0.0")
    await config_manager.set_config("database.max_connections", 100)
    await config_manager.set_config("cache.default_ttl", 3600)

    # 获取配置
    app_name = await config_manager.get_config("app.name")
    db_connections = await config_manager.get_config("database.max_connections")

    logger.info(f"应用名称: {app_name}")
    logger.info(f"数据库最大连接数: {db_connections}")

    # 获取配置段
    app_config = await config_manager.get_config_section("app")
    logger.info(f"应用配置: {app_config}")

    # 获取所有配置键
    keys = await config_manager.get_config_keys()
    logger.info(f"配置键: {keys}")


async def example_resource_monitoring():
    """资源监控示例"""
    logger.info("=== 资源监控示例 ===")

    # 获取资源管理器
    resource_manager = get_app().resource_manager

    # 分配资源
    allocation = await resource_manager.allocate_resources(
        "task123", {"cpu": 2.0, "memory": 1024, "disk": 500}
    )

    if allocation.success:
        logger.info(f"资源分配成功: {allocation.allocated_resources}")
    else:
        logger.warning(f"资源分配失败: {allocation.reason}")

    # 获取资源使用情况
    usage = await resource_manager.get_resource_usage("task123")
    logger.info(f"资源使用情况: {usage}")

    # 获取系统资源状态
    system_resources = await resource_manager.get_system_resources()
    logger.info(f"系统资源: {system_resources}")

    # 释放资源
    await resource_manager.release_resources("task123")
    logger.info("资源已释放")


async def main():
    """主函数"""
    logger.info("开始运行重构后架构示例")

    # 创建并初始化应用程序
    app = await create_app()

    try:
        # 启动应用程序
        await app.start()

        # 运行示例
        await example_configuration()
        await example_cache_usage()
        await example_event_handling()
        await example_resource_monitoring()
        await example_task_management()

        logger.info("所有示例运行完成")

    except Exception as e:
        logger.error(f"示例运行失败: {e}")
        raise

    finally:
        # 清理应用程序
        await app.cleanup()
        logger.info("应用程序已清理")


if __name__ == "__main__":
    asyncio.run(main())
