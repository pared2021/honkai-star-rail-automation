"""性能测试

测试系统在高负载和并发场景下的性能表现。
"""

import asyncio
import pytest
import tempfile
import os
import time
import statistics
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import Mock, AsyncMock, patch

from src.models.task_models import Task, TaskType, TaskStatus, TaskPriority, TaskConfig
from src.services.task_application_service import TaskApplicationService
from src.services.automation_application_service import AutomationApplicationService
from src.core.task_executor import TaskExecutor, ExecutorStatus, TaskExecutionContext
from src.services.event_bus import EventBus
from src.repositories import (
    TaskRepository, 
    ConfigRepository, 
    TaskExecutionRepository,
    ExecutionActionRepository,
    ScreenshotRepository
)


class PerformanceMetrics:
    """性能指标收集器"""
    
    def __init__(self):
        self.task_creation_times = []
        self.task_execution_times = []
        self.database_operation_times = []
        self.memory_usage = []
        self.concurrent_task_counts = []
        self.error_counts = 0
        self.total_operations = 0
    
    def record_task_creation_time(self, duration: float):
        """记录任务创建时间"""
        self.task_creation_times.append(duration)
    
    def record_task_execution_time(self, duration: float):
        """记录任务执行时间"""
        self.task_execution_times.append(duration)
    
    def record_database_operation_time(self, duration: float):
        """记录数据库操作时间"""
        self.database_operation_times.append(duration)
    
    def record_error(self):
        """记录错误"""
        self.error_counts += 1
    
    def record_operation(self):
        """记录操作"""
        self.total_operations += 1
    
    def get_statistics(self) -> dict:
        """获取性能统计"""
        return {
            'task_creation': {
                'count': len(self.task_creation_times),
                'avg': statistics.mean(self.task_creation_times) if self.task_creation_times else 0,
                'median': statistics.median(self.task_creation_times) if self.task_creation_times else 0,
                'max': max(self.task_creation_times) if self.task_creation_times else 0,
                'min': min(self.task_creation_times) if self.task_creation_times else 0
            },
            'task_execution': {
                'count': len(self.task_execution_times),
                'avg': statistics.mean(self.task_execution_times) if self.task_execution_times else 0,
                'median': statistics.median(self.task_execution_times) if self.task_execution_times else 0,
                'max': max(self.task_execution_times) if self.task_execution_times else 0,
                'min': min(self.task_execution_times) if self.task_execution_times else 0
            },
            'database_operations': {
                'count': len(self.database_operation_times),
                'avg': statistics.mean(self.database_operation_times) if self.database_operation_times else 0,
                'median': statistics.median(self.database_operation_times) if self.database_operation_times else 0,
                'max': max(self.database_operation_times) if self.database_operation_times else 0,
                'min': min(self.database_operation_times) if self.database_operation_times else 0
            },
            'errors': {
                'count': self.error_counts,
                'rate': self.error_counts / self.total_operations if self.total_operations > 0 else 0
            },
            'total_operations': self.total_operations
        }


class TestPerformance:
    """性能测试类"""
    
    @pytest.fixture
    async def setup_performance_system(self):
        """设置性能测试系统"""
        # 创建临时数据库
        db_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        db_path = db_file.name
        db_file.close()
        
        try:
            # 初始化仓储
            task_repo = TaskRepository(db_path)
            config_repo = ConfigRepository(db_path)
            execution_repo = TaskExecutionRepository(db_path)
            action_repo = ExecutionActionRepository(db_path)
            screenshot_repo = ScreenshotRepository(db_path)
            
            # 初始化事件系统
            event_bus = EventBus()
            
            # 初始化任务领域服务
            from src.services.task_service import TaskService
            task_domain_service = TaskService(
                task_repository=task_repo,
                event_bus=event_bus
            )
            
            # 初始化服务
            task_service = TaskApplicationService(
                task_service=task_domain_service,
                event_bus=event_bus
            )
            
            automation_service = AutomationApplicationService(
                screenshot_repository=screenshot_repo,
                action_repository=action_repo,
                event_bus=event_bus
            )
            
            # 初始化任务执行器
            task_executor = TaskExecutor(
                task_service=task_service,
                automation_service=automation_service,
                event_bus=event_bus,
                max_workers=4  # 增加工作线程数用于性能测试
            )
            
            # 性能指标收集器
            metrics = PerformanceMetrics()
            
            yield {
                'task_service': task_service,
                'automation_service': automation_service,
                'task_executor': task_executor,
                'event_bus': event_bus,
                'metrics': metrics,
                'repositories': {
                    'task': task_repo,
                    'config': config_repo,
                    'execution': execution_repo,
                    'action': action_repo,
                    'screenshot': screenshot_repo
                }
            }
            
        finally:
            # 清理
            if os.path.exists(db_path):
                os.unlink(db_path)
    
    @pytest.mark.asyncio
    async def test_task_creation_performance(self, setup_performance_system):
        """测试任务创建性能"""
        system = await setup_performance_system
        task_service = system['task_service']
        metrics = system['metrics']
        
        # 测试参数
        num_tasks = 100
        batch_size = 10
        
        print(f"\n开始任务创建性能测试: {num_tasks} 个任务")
        
        # 批量创建任务
        for batch_start in range(0, num_tasks, batch_size):
            batch_end = min(batch_start + batch_size, num_tasks)
            batch_tasks = []
            
            start_time = time.time()
            
            for i in range(batch_start, batch_end):
                config = TaskConfig(
                    name=f"性能测试任务_{i+1}",
                    description=f"测试任务创建性能_{i+1}",
                    task_type=TaskType.MANUAL,
                    priority=TaskPriority.MEDIUM
                )
                
                task_start = time.time()
                task = await task_service.create_task(
                    user_id="perf_test_user",
                    config=config
                )
                task_end = time.time()
                
                metrics.record_task_creation_time(task_end - task_start)
                metrics.record_operation()
                batch_tasks.append(task)
            
            batch_time = time.time() - start_time
            print(f"批次 {batch_start//batch_size + 1}: {batch_end - batch_start} 个任务, 耗时 {batch_time:.3f}s")
        
        # 获取统计信息
        stats = metrics.get_statistics()
        print(f"\n任务创建性能统计:")
        print(f"  总任务数: {stats['task_creation']['count']}")
        print(f"  平均创建时间: {stats['task_creation']['avg']:.4f}s")
        print(f"  中位数创建时间: {stats['task_creation']['median']:.4f}s")
        print(f"  最大创建时间: {stats['task_creation']['max']:.4f}s")
        print(f"  最小创建时间: {stats['task_creation']['min']:.4f}s")
        
        # 性能断言
        assert stats['task_creation']['avg'] < 0.1  # 平均创建时间应小于100ms
        assert stats['task_creation']['max'] < 0.5   # 最大创建时间应小于500ms
        assert stats['errors']['count'] == 0        # 不应有错误
    
    @pytest.mark.asyncio
    async def test_concurrent_task_execution_performance(self, setup_performance_system):
        """测试并发任务执行性能"""
        system = await setup_performance_system
        task_service = system['task_service']
        task_executor = system['task_executor']
        metrics = system['metrics']
        
        # 测试参数
        num_tasks = 50
        max_concurrent = 10
        
        print(f"\n开始并发任务执行性能测试: {num_tasks} 个任务, 最大并发 {max_concurrent}")
        
        # 启动任务执行器
        await task_executor.start()
        
        try:
            # 创建任务
            tasks = []
            for i in range(num_tasks):
                config = TaskConfig(
                    name=f"并发执行测试任务_{i+1}",
                    description=f"测试并发执行性能_{i+1}",
                    task_type=TaskType.MANUAL,
                    priority=TaskPriority.MEDIUM
                )
                
                task = await task_service.create_task(
                    user_id="perf_test_user",
                    config=config
                )
                tasks.append(task)
            
            # 记录开始时间
            start_time = time.time()
            
            # 分批提交任务
            for i in range(0, len(tasks), max_concurrent):
                batch = tasks[i:i + max_concurrent]
                
                # 提交批次任务
                submit_tasks = []
                for task in batch:
                    execution_context = TaskExecutionContext(
                        task_id=task.task_id,
                        user_id="perf_test_user"
                    )
                    submit_tasks.append(task_executor.submit_task(execution_context))
                
                await asyncio.gather(*submit_tasks)
                
                # 等待批次完成
                await asyncio.sleep(0.5)
                
                # 检查运行状态
                running_tasks = task_executor.get_running_tasks()
                print(f"批次 {i//max_concurrent + 1}: 提交 {len(batch)} 个任务, 当前运行 {len(running_tasks)} 个")
            
            # 等待所有任务完成
            max_wait_time = 30.0
            wait_start = time.time()
            
            while time.time() - wait_start < max_wait_time:
                running_tasks = task_executor.get_running_tasks()
                if len(running_tasks) == 0:
                    break
                await asyncio.sleep(0.1)
            
            total_time = time.time() - start_time
            
            print(f"\n并发执行完成, 总耗时: {total_time:.3f}s")
            print(f"平均每任务耗时: {total_time/num_tasks:.4f}s")
            print(f"任务吞吐量: {num_tasks/total_time:.2f} 任务/秒")
            
            # 验证任务状态
            completed_count = 0
            for task in tasks:
                final_task = await task_service.get_task(task.task_id)
                if final_task.status in [TaskStatus.COMPLETED, TaskStatus.RUNNING]:
                    completed_count += 1
            
            print(f"完成/运行中任务数: {completed_count}/{num_tasks}")
            
            # 性能断言
            assert total_time < 60.0  # 总时间应小于60秒
            assert num_tasks/total_time > 1.0  # 吞吐量应大于1任务/秒
            assert completed_count >= num_tasks * 0.8  # 至少80%的任务应该完成或运行
            
        finally:
            await task_executor.stop()
    
    @pytest.mark.asyncio
    async def test_database_operation_performance(self, setup_performance_system):
        """测试数据库操作性能"""
        system = await setup_performance_system
        task_repo = system['repositories']['task']
        metrics = system['metrics']
        
        # 测试参数
        num_operations = 200
        
        print(f"\n开始数据库操作性能测试: {num_operations} 次操作")
        
        # 创建测试任务
        test_tasks = []
        for i in range(num_operations):
            config = TaskConfig(
                name=f"数据库测试任务_{i+1}",
                description=f"测试数据库性能_{i+1}",
                task_type=TaskType.MANUAL,
                priority=TaskPriority.LOW
            )
            
            task = Task(
                task_id=f"db_test_{i+1:03d}",
                user_id="db_test_user",
                config=config,
                status=TaskStatus.PENDING,
                created_at=datetime.now()
            )
            test_tasks.append(task)
        
        # 测试批量插入
        insert_start = time.time()
        for task in test_tasks:
            op_start = time.time()
            await task_repo.create(task)
            op_end = time.time()
            metrics.record_database_operation_time(op_end - op_start)
            metrics.record_operation()
        insert_time = time.time() - insert_start
        
        print(f"批量插入: {num_operations} 条记录, 耗时 {insert_time:.3f}s")
        print(f"插入速率: {num_operations/insert_time:.2f} 记录/秒")
        
        # 测试批量查询
        query_start = time.time()
        for task in test_tasks[:50]:  # 查询前50个
            op_start = time.time()
            retrieved_task = await task_repo.get_by_id(task.task_id)
            op_end = time.time()
            metrics.record_database_operation_time(op_end - op_start)
            metrics.record_operation()
            assert retrieved_task is not None
        query_time = time.time() - query_start
        
        print(f"批量查询: 50 次查询, 耗时 {query_time:.3f}s")
        print(f"查询速率: {50/query_time:.2f} 查询/秒")
        
        # 测试批量更新
        update_start = time.time()
        for task in test_tasks[:30]:  # 更新前30个
            op_start = time.time()
            task.status = TaskStatus.RUNNING
            await task_repo.update(task)
            op_end = time.time()
            metrics.record_database_operation_time(op_end - op_start)
            metrics.record_operation()
        update_time = time.time() - update_start
        
        print(f"批量更新: 30 次更新, 耗时 {update_time:.3f}s")
        print(f"更新速率: {30/update_time:.2f} 更新/秒")
        
        # 获取统计信息
        stats = metrics.get_statistics()
        print(f"\n数据库操作性能统计:")
        print(f"  总操作数: {stats['database_operations']['count']}")
        print(f"  平均操作时间: {stats['database_operations']['avg']:.4f}s")
        print(f"  中位数操作时间: {stats['database_operations']['median']:.4f}s")
        print(f"  最大操作时间: {stats['database_operations']['max']:.4f}s")
        print(f"  最小操作时间: {stats['database_operations']['min']:.4f}s")
        
        # 性能断言
        assert stats['database_operations']['avg'] < 0.05  # 平均操作时间应小于50ms
        assert stats['database_operations']['max'] < 0.2   # 最大操作时间应小于200ms
        assert num_operations/insert_time > 50            # 插入速率应大于50记录/秒
        assert 50/query_time > 100                       # 查询速率应大于100查询/秒
    
    @pytest.mark.asyncio
    async def test_memory_usage_under_load(self, setup_performance_system):
        """测试负载下的内存使用"""
        system = await setup_performance_system
        task_service = system['task_service']
        
        import psutil
        import gc
        
        # 获取当前进程
        process = psutil.Process()
        
        # 记录初始内存使用
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        print(f"\n初始内存使用: {initial_memory:.2f} MB")
        
        # 创建大量任务
        num_tasks = 500
        tasks = []
        
        for i in range(num_tasks):
            config = TaskConfig(
                name=f"内存测试任务_{i+1}",
                description=f"测试内存使用_{i+1}" * 10,  # 增加描述长度
                task_type=TaskType.AUTOMATION,
                priority=TaskPriority.MEDIUM,
                automation_config={
                    'window_title': f'测试窗口_{i+1}',
                    'actions': [
                        {'type': 'detect_window', 'window_title': f'窗口_{i+1}'},
                        {'type': 'take_screenshot', 'save_path': f'screenshot_{i+1}.png'},
                        {'type': 'find_element', 'element_type': 'button', 'element_text': f'按钮_{i+1}'}
                    ] * 5  # 增加动作数量
                }
            )
            
            task = await task_service.create_task(
                user_id="memory_test_user",
                config=config
            )
            tasks.append(task)
            
            # 每100个任务检查一次内存
            if (i + 1) % 100 == 0:
                current_memory = process.memory_info().rss / 1024 / 1024
                memory_increase = current_memory - initial_memory
                print(f"创建 {i+1} 个任务后内存使用: {current_memory:.2f} MB (+{memory_increase:.2f} MB)")
        
        # 记录峰值内存
        peak_memory = process.memory_info().rss / 1024 / 1024
        peak_increase = peak_memory - initial_memory
        print(f"峰值内存使用: {peak_memory:.2f} MB (+{peak_increase:.2f} MB)")
        
        # 执行垃圾回收
        gc.collect()
        
        # 删除任务引用
        del tasks
        gc.collect()
        
        # 等待一段时间让内存释放
        await asyncio.sleep(1.0)
        
        # 检查内存释放
        final_memory = process.memory_info().rss / 1024 / 1024
        memory_released = peak_memory - final_memory
        print(f"清理后内存使用: {final_memory:.2f} MB (释放 {memory_released:.2f} MB)")
        
        # 内存使用断言
        assert peak_increase < 200  # 峰值内存增长应小于200MB
        assert memory_released > peak_increase * 0.3  # 应该释放至少30%的内存
    
    @pytest.mark.asyncio
    async def test_event_system_performance(self, setup_performance_system):
        """测试事件系统性能"""
        system = await setup_performance_system
        event_bus = system['event_bus']
        
        # 事件计数器
        event_counts = {'received': 0, 'processed': 0}
        processing_times = []
        
        def fast_handler(event):
            """快速事件处理器"""
            start_time = time.time()
            event_counts['received'] += 1
            # 模拟快速处理
            time.sleep(0.001)  # 1ms
            event_counts['processed'] += 1
            processing_times.append(time.time() - start_time)
        
        def slow_handler(event):
            """慢速事件处理器"""
            start_time = time.time()
            # 模拟慢速处理
            time.sleep(0.01)  # 10ms
            processing_times.append(time.time() - start_time)
        
        # 注册事件处理器
        event_bus.subscribe_all(fast_handler)
        event_bus.subscribe_all(slow_handler)
        
        # 发布大量事件
        num_events = 1000
        
        print(f"\n开始事件系统性能测试: {num_events} 个事件")
        
        start_time = time.time()
        
        for i in range(num_events):
            # 创建模拟事件
            from src.core.events import TaskCreatedEvent
            event = TaskCreatedEvent(
                task_id=f"event_test_{i+1}",
                user_id="event_test_user",
                task_name=f"事件测试任务_{i+1}",
                timestamp=datetime.now()
            )
            
            await event_bus.publish(event)
        
        # 等待所有事件处理完成
        await asyncio.sleep(0.5)
        
        total_time = time.time() - start_time
        
        print(f"事件发布完成, 总耗时: {total_time:.3f}s")
        print(f"事件发布速率: {num_events/total_time:.2f} 事件/秒")
        print(f"接收事件数: {event_counts['received']}")
        print(f"处理事件数: {event_counts['processed']}")
        
        if processing_times:
            avg_processing_time = statistics.mean(processing_times)
            max_processing_time = max(processing_times)
            print(f"平均处理时间: {avg_processing_time:.4f}s")
            print(f"最大处理时间: {max_processing_time:.4f}s")
        
        # 性能断言
        assert num_events/total_time > 100  # 事件发布速率应大于100事件/秒
        assert event_counts['received'] >= num_events  # 应该接收到所有事件
        assert event_counts['processed'] >= num_events  # 应该处理所有事件
    
    def test_performance_summary(self, setup_performance_system):
        """性能测试总结"""
        print("\n" + "="*60)
        print("性能测试总结")
        print("="*60)
        print("所有性能测试已完成。")
        print("请查看上述各项测试的详细性能指标。")
        print("="*60)


if __name__ == "__main__":
    # 运行性能测试
    pytest.main([__file__, "-v", "-s"])