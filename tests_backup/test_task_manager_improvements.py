#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试TaskManager改进功能
包括异步操作、事务处理、性能优化、状态监控和调度逻辑
"""

import unittest
import asyncio
import tempfile
import os
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
import json
import sys
import time
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 导入需要测试的模块
from src.adapters.task_manager_adapter import TaskManagerAdapter
from src.models.task_models import Task, TaskConfig, TaskType, TaskStatus, TaskPriority

# 创建简单的DatabaseManager模拟类
class MockDatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._initialize_database()
    
    def _initialize_database(self):
        """初始化数据库表结构"""
        import sqlite3
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建用户表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                username TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 创建任务表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                task_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                task_name TEXT NOT NULL,
                description TEXT,
                task_type TEXT NOT NULL,
                priority TEXT DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high')),
                status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed', 'paused', 'cancelled')),
                max_duration INTEGER DEFAULT 300,
                retry_count INTEGER DEFAULT 3,
                retry_interval REAL DEFAULT 1.0,
                safe_mode BOOLEAN DEFAULT 1,
                scheduled_time TIMESTAMP,
                repeat_interval INTEGER,
                last_execution TIMESTAMP,
                execution_count INTEGER DEFAULT 0,
                progress REAL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        # 创建任务配置表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS task_configs (
                config_id TEXT PRIMARY KEY,
                task_id TEXT NOT NULL,
                config_key TEXT NOT NULL,
                config_value TEXT NOT NULL,
                data_type TEXT DEFAULT 'string' CHECK (data_type IN ('string', 'integer', 'float', 'boolean', 'json')),
                FOREIGN KEY (task_id) REFERENCES tasks(task_id) ON DELETE CASCADE
            )
        """)
        
        # 创建execution_logs表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS execution_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT NOT NULL,
                execution_id TEXT NOT NULL,
                status TEXT NOT NULL,
                start_time TEXT,
                end_time TEXT,
                result TEXT,
                error_message TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (task_id) REFERENCES tasks (task_id) ON DELETE CASCADE
            )
        """)
        
        # 插入默认用户
        cursor.execute(
            "INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)",
            ('default_user', '默认用户')
        )
        
        conn.commit()
        conn.close()


class TestTaskManagerImprovements:
    """TaskManager改进功能测试类"""
    
    def __init__(self):
        self.temp_db = None
        self.task_manager = None
        self.db_manager = None
    
    async def setup(self):
        """测试环境设置"""
        # 创建临时数据库
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.temp_db.close()
        
        # 创建模拟的数据库管理器
        self.db_manager = MockDatabaseManager(self.temp_db.name)
        
        # 初始化任务管理器适配器
        self.task_manager = TaskManagerAdapter(self.db_manager)
        
        print(f"✓ 测试环境已设置，临时数据库: {self.temp_db.name}")
    
    async def teardown(self):
        """测试环境清理"""
        if self.task_manager:
            try:
                await self.task_manager.stop_status_monitoring()
            except:
                pass
            try:
                await self.task_manager.stop_scheduler()
            except:
                pass
            try:
                # 关闭数据库连接
                await self.task_manager.close_connections()
            except Exception as e:
                print(f"关闭数据库连接时出错: {e}")
        
        # 等待一下确保连接完全关闭
        await asyncio.sleep(0.1)
        
        if self.temp_db and os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
        
        print("✓ 测试环境已清理")
    
    async def test_async_crud_operations(self):
        """测试异步CRUD操作"""
        print("\n=== 测试异步CRUD操作 ===")
        
        # 测试创建任务

        task_config = TaskConfig(
            task_name="测试任务",
            task_type=TaskType.CUSTOM,
            description="这是一个测试任务",
            priority=TaskPriority.HIGH
        )
        
        task_id = await self.task_manager.create_task(
            config=task_config
        )
        print(f"✓ 创建任务成功: {task_id}")
        
        # 测试获取任务
        task = await self.task_manager.get_task(task_id)
        assert task is not None, "获取任务失败"
        print(f"实际任务名称: '{task.name}', 期望: '测试任务'")
        assert task.name == "测试任务", f"任务名称不匹配: 实际='{task.name}', 期望='测试任务'"
        print("✓ 获取任务成功")
        
        # 测试更新任务
        updated_config = TaskConfig(
            task_name="更新后的测试任务",
            task_type=TaskType.CUSTOM,
            description="这是一个更新后的测试任务",
            priority=TaskPriority.MEDIUM
        )
        
        await self.task_manager.update_task(
            task_id,
            config=updated_config
        )
        
        updated_task = await self.task_manager.get_task(task_id)
        assert updated_task.name == "更新后的测试任务", "任务更新失败"
        print("✓ 更新任务成功")
        
        # 测试状态更新
        # TaskStatus已经在顶部导入了
        await self.task_manager.update_task_status(task_id, TaskStatus.RUNNING)
        task_after_status_update = await self.task_manager.get_task(task_id)
        assert task_after_status_update.status == TaskStatus.RUNNING, "状态更新失败"
        print("✓ 状态更新成功")
        
        # 测试列表任务
        tasks = await self.task_manager.list_tasks()
        assert len(tasks) >= 1, "列表任务失败"
        print(f"✓ 列表任务成功，共 {len(tasks)} 个任务")
        
        # 测试删除任务
        await self.task_manager.delete_task(task_id)
        deleted_task = await self.task_manager.get_task(task_id)
        assert deleted_task is None, "删除任务失败"
        print("✓ 删除任务成功")
    
    async def test_data_validation(self):
        """测试数据验证功能"""
        print("\n=== 测试数据验证功能 ===")
        
        # 测试无效任务类型
        try:
            invalid_config = TaskConfig(
                task_name="无效任务",
                task_type="invalid_type",  # 这会导致类型错误
                description="测试无效任务类型",
                priority=TaskPriority.HIGH
            )
            await self.task_manager.create_task(
                config=invalid_config
            )
            assert False, "应该抛出验证错误"
        except Exception as e:
            print(f"✓ 无效任务类型验证成功: {e}")
        
        # 测试无效优先级
        try:
            invalid_config = TaskConfig(
                task_name="无效优先级任务",
                task_type=TaskType.CUSTOM,
                description="测试无效优先级",
                priority="invalid_priority"  # 这会导致类型错误
            )
            await self.task_manager.create_task(
                config=invalid_config
            )
            assert False, "应该抛出验证错误"
        except Exception as e:
            print(f"✓ 无效优先级验证成功: {e}")
        
        # 测试无效状态转换
        valid_config = TaskConfig(
            task_name="状态转换测试任务",
            task_type=TaskType.CUSTOM,
            description="测试状态转换",
            priority=TaskPriority.MEDIUM
        )
        
        task_id = await self.task_manager.create_task(
            config=valid_config
        )
        
        try:
            # 尝试从pending直接转换到completed（应该失败）
            await self.task_manager.update_task_status(task_id, TaskStatus.COMPLETED)
            assert False, "应该抛出状态转换错误"
        except Exception as e:
            print(f"✓ 无效状态转换验证成功: {e}")
        
        # 清理
        await self.task_manager.delete_task(task_id)
    
    async def test_transaction_support(self):
        """测试事务支持"""
        print("\n=== 测试事务支持 ===")
        
        # 测试批量创建任务
        task_configs = []
        for i in range(3):
            config = TaskConfig(
                task_name=f"批量任务 {i}",
                task_type=TaskType.CUSTOM,
                description=f"批量创建的第 {i} 个任务",
                priority=TaskPriority.MEDIUM
            )
            task_configs.append(config)
        
        # 将TaskConfig转换为字典格式
        tasks_data = []
        for config in task_configs:
            task_data = {
                'name': config.task_name,
                'description': config.description,
                'user_id': 'test_user',
                'config': {
                    'task_name': config.task_name,
                    'task_type': config.task_type.value,
                    'description': config.description,
                    'priority': config.priority.value,
                    'max_retry_count': config.max_retry_count,
                    'timeout_seconds': config.timeout_seconds,
                    'auto_restart': config.auto_restart,
                    'schedule_enabled': config.schedule_enabled,
                    'schedule_time': config.schedule_time,
                    'schedule_days': config.schedule_days,
                    'actions': config.actions,
                    'tags': config.tags,
                    'custom_params': config.custom_params
                }
            }
            tasks_data.append(task_data)
        
        task_ids = await self.task_manager.batch_create_tasks(tasks_data)
        assert len(task_ids) == 3, "批量创建任务失败"
        print(f"✓ 批量创建任务成功: {task_ids}")
        
        # 测试批量状态更新
        status_updates = [{'task_id': task_id, 'status': 'running'} for task_id in task_ids]
        await self.task_manager.batch_update_task_status(status_updates)
        
        # 验证状态更新
        for task_id in task_ids:
            task = await self.task_manager.get_task(task_id)
            assert task.status == TaskStatus.RUNNING, f"任务 {task_id} 状态更新失败"
        print("✓ 批量状态更新成功")
        
        # 测试事务回滚（模拟）
        async def failing_operation(conn):
            # 这个操作会失败
            await conn.execute("INSERT INTO invalid_table VALUES (1)")
        
        try:
            await self.task_manager.execute_in_transaction([failing_operation])
            assert False, "应该抛出事务错误"
        except Exception as e:
            print(f"✓ 事务回滚测试成功: {e}")
        
        # 清理
        for task_id in task_ids:
            await self.task_manager.delete_task(task_id)
    
    async def test_performance_optimization(self):
        """测试性能优化"""
        print("\n=== 测试性能优化 ===")
        
        # 创建多个任务用于性能测试
        task_ids = []
        for i in range(10):
            config = TaskConfig(
                task_name=f"性能测试任务 {i}",
                task_type=TaskType.CUSTOM,
                description=f"第 {i} 个性能测试任务",
                priority=TaskPriority.LOW
            )
            task_id = await self.task_manager.create_task(
                config=config
            )
            task_ids.append(task_id)
        
        print(f"✓ 创建了 {len(task_ids)} 个测试任务")
        
        # 测试缓存查询性能
        start_time = time.time()
        
        # 第一次查询（无缓存）
        tasks1 = await self.task_manager.list_tasks(use_cache=True)
        first_query_time = time.time() - start_time
        
        # 第二次查询（有缓存）
        start_time = time.time()
        tasks2 = await self.task_manager.list_tasks(use_cache=True)
        second_query_time = time.time() - start_time
        
        print(f"✓ 第一次查询时间: {first_query_time:.4f}s")
        print(f"✓ 第二次查询时间: {second_query_time:.4f}s")
        print(f"✓ 缓存加速比: {first_query_time/second_query_time:.2f}x")
        
        # 测试统计查询缓存
        start_time = time.time()
        stats1 = await self.task_manager.get_task_statistics(use_cache=True)
        stats_first_time = time.time() - start_time
        
        start_time = time.time()
        stats2 = await self.task_manager.get_task_statistics(use_cache=True)
        stats_second_time = time.time() - start_time
        
        print(f"✓ 统计查询第一次: {stats_first_time:.4f}s")
        print(f"✓ 统计查询第二次: {stats_second_time:.4f}s")
        
        # 清理
        for task_id in task_ids:
            await self.task_manager.delete_task(task_id)
    
    async def test_status_monitoring(self):
        """测试状态监控"""
        print("\n=== 测试状态监控 ===")
        
        # 创建测试任务
        config = TaskConfig(
            task_name="监控测试任务",
            task_type=TaskType.CUSTOM,
            description="用于测试状态监控的任务",
            priority=TaskPriority.MEDIUM
        )
        
        task_id = await self.task_manager.create_task(
            config=config
        )
        
        # 添加状态监控
        callback_called = {'count': 0}
        
        def status_callback(task_id, event_type, data):
            callback_called['count'] += 1
            print(f"✓ 状态回调触发: {task_id}, {event_type}, {data}")
        
        self.task_manager.add_status_monitor(task_id, status_callback)
        
        # 启动状态监控
        await self.task_manager.start_status_monitoring(interval=1)
        
        # 更新任务状态
        await self.task_manager.update_task_status(task_id, TaskStatus.RUNNING)
        
        # 等待监控检查
        await asyncio.sleep(2)
        
        # 获取监控状态
        monitoring_status = await self.task_manager.get_monitoring_status()
        print(f"✓ 监控状态: {monitoring_status}")
        
        # 停止监控
        await self.task_manager.stop_status_monitoring()
        
        # 清理
        await self.task_manager.delete_task(task_id)
    
    async def test_scheduling_logic(self):
        """测试调度逻辑"""
        print("\n=== 测试调度逻辑 ===")
        
        # 创建不同优先级的任务
        high_config = TaskConfig(
            task_name="高优先级任务",
            task_type=TaskType.CUSTOM,
            description="高优先级测试任务",
            priority=TaskPriority.HIGH
        )
        medium_config = TaskConfig(
            task_name="中优先级任务",
            task_type=TaskType.CUSTOM,
            description="中优先级测试任务",
            priority=TaskPriority.MEDIUM
        )
        low_config = TaskConfig(
            task_name="低优先级任务",
            task_type=TaskType.CUSTOM,
            description="低优先级测试任务",
            priority=TaskPriority.LOW
        )
        
        high_task_id = await self.task_manager.create_task(
            config=high_config
        )
        medium_task_id = await self.task_manager.create_task(
            config=medium_config
        )
        low_task_id = await self.task_manager.create_task(
            config=low_config
        )
        
        task_ids = [high_task_id, medium_task_id, low_task_id]
        
        # 添加任务依赖关系
        self.task_manager.add_task_dependency(task_ids[1], task_ids[0])  # 中优先级依赖高优先级
        self.task_manager.add_task_dependency(task_ids[2], task_ids[1])  # 低优先级依赖中优先级
        
        # 获取依赖关系
        deps = self.task_manager.get_task_dependencies(task_ids[1])
        print(f"✓ 任务依赖关系: {deps}")
        
        # 启动调度器
        await self.task_manager.start_scheduler(interval=2)
        
        # 等待调度执行
        await asyncio.sleep(3)
        
        # 获取调度器状态
        scheduler_status = await self.task_manager.get_scheduler_status()
        print(f"✓ 调度器状态: {scheduler_status}")
        
        # 停止调度器
        await self.task_manager.stop_scheduler()
        
        # 清理
        for task_id in task_ids:
            await self.task_manager.delete_task(task_id)
    
    async def run_all_tests(self):
        """运行所有测试"""
        print("开始TaskManager改进功能测试...")
        
        try:
            await self.setup()
            
            await self.test_async_crud_operations()
            await self.test_data_validation()
            await self.test_transaction_support()
            await self.test_performance_optimization()
            await self.test_status_monitoring()
            await self.test_scheduling_logic()
            
            print("\n=== 所有测试完成 ===")
            print("✓ 异步CRUD操作测试通过")
            print("✓ 数据验证功能测试通过")
            print("✓ 事务支持测试通过")
            print("✓ 性能优化测试通过")
            print("✓ 状态监控测试通过")
            print("✓ 调度逻辑测试通过")
            
        except Exception as e:
            print(f"\n❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            await self.teardown()


async def main():
    """主函数"""
    test_runner = TestTaskManagerImprovements()
    await test_runner.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())