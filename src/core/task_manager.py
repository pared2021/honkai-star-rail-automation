# -*- coding: utf-8 -*-
"""
任务管理器 - 负责任务的创建、查询、更新和删除操作
"""

import json
import uuid
import asyncio
import aiosqlite
from typing import Optional, Dict, Any, List, Union
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
from contextlib import asynccontextmanager
import weakref
import time

from loguru import logger
from ..database.db_manager import DatabaseManager
from ..models.task_model import Task, TaskStatus, TaskType, TaskPriority
from .task_executor import TaskExecutor
from .task_actions import ActionFactory
from .enums import ActionType


@dataclass
class TaskConfig:
    """任务配置数据结构"""
    # 基本信息
    task_name: str
    task_type: TaskType
    description: str = ""
    priority: TaskPriority = TaskPriority.MEDIUM
    
    # 执行配置
    max_retry_count: int = 3
    timeout_seconds: int = 300
    auto_restart: bool = False
    
    # 调度配置
    schedule_enabled: bool = False
    schedule_time: Optional[str] = None  # "HH:MM" 格式
    schedule_days: List[str] = None  # ["monday", "tuesday", ...]
    
    # 操作序列
    actions: List[Dict[str, Any]] = None
    
    # 其他配置
    tags: List[str] = None
    custom_params: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.actions is None:
            self.actions = []
        if self.tags is None:
            self.tags = []
        if self.custom_params is None:
            self.custom_params = {}
        if self.schedule_days is None:
            self.schedule_days = []
        
        # 验证参数
        if not self.task_name or not self.task_name.strip():
            raise ValueError("任务名称不能为空")
        if self.max_retry_count < 0:
            raise ValueError("重试次数不能为负数")
        if self.timeout_seconds < 0:
            raise ValueError("超时时间不能为负数")


# Task类已从models.task_model导入


class TaskValidationError(Exception):
    """任务验证错误"""
    pass

class TaskStateError(Exception):
    """任务状态错误"""
    pass

class TaskManager:
    """异步任务管理器 - 负责任务的创建、管理和执行"""
    
    def __init__(self, db_manager: DatabaseManager, default_user_id: str = "default_user"):
        """初始化任务管理器
        
        Args:
            db_manager: 数据库管理器
            default_user_id: 默认用户ID
        """
        self.db_manager = db_manager
        self.default_user_id = default_user_id
        self.task_executor = TaskExecutor(db_manager)
        self._connection_pool = {}
        self._pool_size = 10
        self._connection_timeout = 30
        self._query_cache = {}
        self._cache_size = 100
        self._cache_ttl = 300  # 5分钟缓存过期
        
        # 状态监控相关
        self._status_monitors = {}  # 任务状态监控器
        self._status_callbacks = {}  # 状态变更回调
        self._monitoring_active = False
        self._monitor_interval = 5  # 监控间隔（秒）
        self._monitor_task = None
        
        # 调度相关
        self._scheduler_active = False
        self._scheduler_task = None
        self._scheduler_interval = 10  # 调度间隔（秒）
        self._task_dependencies = {}  # 任务依赖关系
        self._priority_weights = {
            'low': 1,
            'medium': 2,
            'high': 3,
            'urgent': 4
        }
        
        logger.info("任务管理器初始化完成")
        
    @asynccontextmanager
    async def get_async_connection(self):
        """获取异步数据库连接（带连接池管理）"""
        conn = await self._get_pooled_connection()
        try:
            yield conn
        finally:
            await self._return_connection(conn)
    
    async def _get_pooled_connection(self):
        """从连接池获取连接"""
        current_time = time.time()
        
        # 清理过期连接
        expired_keys = []
        for key, (conn, timestamp) in self._connection_pool.items():
            if current_time - timestamp > self._connection_timeout:
                expired_keys.append(key)
        
        for key in expired_keys:
            conn, _ = self._connection_pool.pop(key)
            try:
                await conn.close()
            except:
                pass
        
        # 如果池中有可用连接，直接返回
        if self._connection_pool:
            key = next(iter(self._connection_pool))
            conn, _ = self._connection_pool.pop(key)
            return conn
        
        # 创建新连接
        conn = await aiosqlite.connect(self.db_manager.db_path)
        conn.row_factory = aiosqlite.Row
        
        # 启用WAL模式以减少锁定问题
        await conn.execute("PRAGMA journal_mode=WAL")
        await conn.execute("PRAGMA synchronous=NORMAL")
        await conn.execute("PRAGMA cache_size=10000")
        await conn.execute("PRAGMA temp_store=memory")
        
        return conn
    
    async def _return_connection(self, conn):
        """将连接返回到连接池"""
        if len(self._connection_pool) < self._pool_size:
            connection_id = id(conn)
            self._connection_pool[connection_id] = (conn, time.time())
        else:
            await conn.close()
    
    def _get_cache_key(self, query: str, params: tuple = None) -> str:
        """生成查询缓存键"""
        params_str = str(params) if params else ""
        return f"{hash(query + params_str)}"
    
    async def _cached_query(self, query: str, params: tuple = None, cache_key: str = None) -> List[Dict]:
        """执行带缓存的查询"""
        if cache_key is None:
            cache_key = self._get_cache_key(query, params)
        
        current_time = time.time()
        
        # 检查缓存
        if cache_key in self._query_cache:
            cached_data, timestamp = self._query_cache[cache_key]
            if current_time - timestamp < self._cache_ttl:
                logger.debug(f"查询缓存命中: {cache_key}")
                return cached_data
            else:
                # 缓存过期，删除
                del self._query_cache[cache_key]
        
        # 执行查询
        async with self.get_async_connection() as conn:
            cursor = await conn.execute(query, params or ())
            rows = await cursor.fetchall()
            result = [dict(row) for row in rows]
        
        # 缓存结果（如果缓存未满）
        if len(self._query_cache) < self._cache_size:
            self._query_cache[cache_key] = (result, current_time)
            logger.debug(f"查询结果已缓存: {cache_key}")
        
        return result
    
    def _clear_cache(self, pattern: str = None):
        """清理查询缓存"""
        if pattern:
            # 清理匹配模式的缓存
            keys_to_remove = [key for key in self._query_cache.keys() if pattern in str(key)]
            for key in keys_to_remove:
                del self._query_cache[key]
            logger.debug(f"清理缓存，模式: {pattern}，清理数量: {len(keys_to_remove)}")
        else:
            # 清理所有缓存
            cache_count = len(self._query_cache)
            self._query_cache.clear()
            logger.debug(f"清理所有缓存，清理数量: {cache_count}")
    
    async def close_connections(self):
        """关闭所有连接池中的连接"""
        for conn, _ in self._connection_pool.values():
            try:
                await conn.close()
            except:
                pass
        self._connection_pool.clear()
        logger.info("所有数据库连接已关闭")
    
    async def start_status_monitoring(self, interval: int = 5):
        """启动任务状态监控"""
        if self._monitoring_active:
            logger.warning("状态监控已经在运行中")
            return
        
        self._monitor_interval = interval
        self._monitoring_active = True
        self._monitor_task = asyncio.create_task(self._monitor_task_status())
        logger.info(f"任务状态监控已启动，监控间隔: {interval}秒")
    
    async def stop_status_monitoring(self):
        """停止任务状态监控"""
        if not self._monitoring_active:
            logger.warning("状态监控未在运行")
            return
        
        self._monitoring_active = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("任务状态监控已停止")
    
    async def _monitor_task_status(self):
        """监控任务状态变更"""
        while self._monitoring_active:
            try:
                # 获取所有正在运行的任务
                running_tasks = await self.list_tasks(status='running', use_cache=False)
                
                for task in running_tasks:
                    task_id = task['task_id']
                    
                    # 检查任务是否有监控器
                    if task_id in self._status_monitors:
                        await self._check_task_health(task_id)
                
                # 清理已完成任务的监控器
                await self._cleanup_completed_monitors()
                
                await asyncio.sleep(self._monitor_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"状态监控出错: {e}")
                await asyncio.sleep(self._monitor_interval)
    
    async def _check_task_health(self, task_id: str):
        """检查任务健康状态"""
        try:
            task = await self.get_task(task_id)
            if not task:
                return
            
            monitor_info = self._status_monitors.get(task_id, {})
            last_check = monitor_info.get('last_check', 0)
            current_time = time.time()
            
            # 更新监控信息
            self._status_monitors[task_id] = {
                'last_check': current_time,
                'status': task['status'],
                'check_count': monitor_info.get('check_count', 0) + 1
            }
            
            # 检查任务是否超时
            if task['status'] == 'running':
                last_execution = task.get('last_execution')
                if last_execution:
                    # 解析时间戳
                    if isinstance(last_execution, str):
                        from datetime import datetime
                        last_execution = datetime.fromisoformat(last_execution).timestamp()
                    elif isinstance(last_execution, datetime):
                        last_execution = last_execution.timestamp()
                    
                    # 检查是否超时（默认30分钟）
                    timeout_threshold = 30 * 60  # 30分钟
                    if current_time - last_execution > timeout_threshold:
                        logger.warning(f"任务 {task_id} 可能已超时")
                        await self._trigger_status_callback(task_id, 'timeout', {
                            'message': '任务执行超时',
                            'last_execution': last_execution,
                            'current_time': current_time
                        })
            
        except Exception as e:
            logger.error(f"检查任务 {task_id} 健康状态失败: {e}")
    
    async def _cleanup_completed_monitors(self):
        """清理已完成任务的监控器"""
        completed_statuses = ['completed', 'failed', 'cancelled']
        tasks_to_remove = []
        
        for task_id in self._status_monitors:
            try:
                task = await self.get_task(task_id)
                if not task or task['status'] in completed_statuses:
                    tasks_to_remove.append(task_id)
            except Exception:
                tasks_to_remove.append(task_id)
        
        for task_id in tasks_to_remove:
            self._status_monitors.pop(task_id, None)
            self._status_callbacks.pop(task_id, None)
            logger.debug(f"清理任务 {task_id} 的监控器")
    
    def add_status_monitor(self, task_id: str, callback: callable = None):
        """添加任务状态监控"""
        self._status_monitors[task_id] = {
            'last_check': time.time(),
            'status': None,
            'check_count': 0
        }
        
        if callback:
            self._status_callbacks[task_id] = callback
        
        logger.info(f"已添加任务 {task_id} 的状态监控")
    
    def remove_status_monitor(self, task_id: str):
        """移除任务状态监控"""
        self._status_monitors.pop(task_id, None)
        self._status_callbacks.pop(task_id, None)
        logger.info(f"已移除任务 {task_id} 的状态监控")
    
    async def _trigger_status_callback(self, task_id: str, event_type: str, data: Dict):
        """触发状态变更回调"""
        callback = self._status_callbacks.get(task_id)
        if callback:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(task_id, event_type, data)
                else:
                    callback(task_id, event_type, data)
                logger.debug(f"任务 {task_id} 状态回调已触发: {event_type}")
            except Exception as e:
                logger.error(f"执行任务 {task_id} 状态回调失败: {e}")
    
    async def get_monitoring_status(self) -> Dict[str, Any]:
        """获取监控状态信息"""
        return {
            'monitoring_active': self._monitoring_active,
            'monitor_interval': self._monitor_interval,
            'monitored_tasks': len(self._status_monitors),
            'monitors': dict(self._status_monitors)
         }
    
    async def start_scheduler(self, interval: int = 10):
        """启动任务调度器"""
        if self._scheduler_active:
            logger.warning("任务调度器已经在运行中")
            return
        
        self._scheduler_interval = interval
        self._scheduler_active = True
        self._scheduler_task = asyncio.create_task(self._schedule_tasks())
        logger.info(f"任务调度器已启动，调度间隔: {interval}秒")
    
    async def stop_scheduler(self):
        """停止任务调度器"""
        if not self._scheduler_active:
            logger.warning("任务调度器未在运行")
            return
        
        self._scheduler_active = False
        if self._scheduler_task:
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass
        logger.info("任务调度器已停止")
    
    async def _schedule_tasks(self):
        """任务调度主循环"""
        while self._scheduler_active:
            try:
                # 获取待调度的任务
                pending_tasks = await self.list_tasks(status='pending', use_cache=False)
                
                if pending_tasks:
                    # 按优先级和依赖关系排序
                    scheduled_tasks = await self._prioritize_tasks(pending_tasks)
                    
                    # 执行可调度的任务
                    for task in scheduled_tasks:
                        if await self._can_execute_task(task):
                            await self._schedule_task_execution(task)
                
                await asyncio.sleep(self._scheduler_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"任务调度出错: {e}")
                await asyncio.sleep(self._scheduler_interval)
    
    async def _prioritize_tasks(self, tasks: List[Dict]) -> List[Dict]:
        """按优先级和依赖关系对任务进行排序"""
        # 计算任务优先级分数
        task_scores = []
        for task in tasks:
            score = await self._calculate_task_priority(task)
            task_scores.append((task, score))
        
        # 按分数降序排序
        task_scores.sort(key=lambda x: x[1], reverse=True)
        
        # 应用依赖关系约束
        prioritized_tasks = []
        processed_tasks = set()
        
        for task, score in task_scores:
            task_id = task['task_id']
            if await self._dependencies_satisfied(task_id, processed_tasks):
                prioritized_tasks.append(task)
                processed_tasks.add(task_id)
        
        return prioritized_tasks
    
    async def _calculate_task_priority(self, task: Dict) -> float:
        """计算任务优先级分数"""
        base_score = self._priority_weights.get(task.get('priority', 'medium'), 2)
        
        # 考虑任务创建时间（越早创建优先级越高）
        created_at = task.get('created_at')
        if created_at:
            if isinstance(created_at, str):
                from datetime import datetime
                created_timestamp = datetime.fromisoformat(created_at).timestamp()
            else:
                created_timestamp = created_at.timestamp() if hasattr(created_at, 'timestamp') else created_at
            
            # 时间权重：每小时增加0.1分
            time_weight = (time.time() - created_timestamp) / 3600 * 0.1
            base_score += time_weight
        
        # 考虑任务类型权重
        task_type = task.get('task_type', 'default')
        type_weights = {
            'system': 1.5,
            'user': 1.0,
            'background': 0.8,
            'maintenance': 0.6
        }
        type_weight = type_weights.get(task_type, 1.0)
        base_score *= type_weight
        
        # 考虑重试次数（重试次数越多优先级越低）
        retry_count = task.get('retry_count', 0)
        retry_penalty = retry_count * 0.2
        base_score -= retry_penalty
        
        return max(base_score, 0.1)  # 确保最小优先级
    
    async def _dependencies_satisfied(self, task_id: str, processed_tasks: set) -> bool:
        """检查任务依赖是否满足"""
        dependencies = self._task_dependencies.get(task_id, [])
        
        for dep_id in dependencies:
            # 检查依赖任务是否已完成
            try:
                dep_task = await self.get_task(dep_id)
                if not dep_task or dep_task['status'] not in ['completed']:
                    return False
            except Exception:
                return False
        
        return True
    
    async def _can_execute_task(self, task: Dict) -> bool:
        """检查任务是否可以执行"""
        # 检查调度配置
        config = task.get('config', {})
        if isinstance(config, str):
            try:
                import json
                config = json.loads(config)
            except:
                config = {}
        
        schedule_config = config.get('schedule', {})
        
        # 检查调度时间
        if not await self._check_schedule_time(schedule_config):
            return False
        
        # 检查资源限制
        if not await self._check_resource_limits():
            return False
        
        return True
    
    async def _check_schedule_time(self, schedule_config: Dict) -> bool:
        """检查调度时间是否满足"""
        if not schedule_config:
            return True
        
        schedule_type = schedule_config.get('type')
        
        if schedule_type == 'cron':
            # 简单的cron检查（这里可以集成更完整的cron库）
            cron_expr = schedule_config.get('expression', '')
            # 暂时返回True，实际应该解析cron表达式
            return True
        
        elif schedule_type == 'interval':
            interval = schedule_config.get('interval', 0)
            last_execution = schedule_config.get('last_execution', 0)
            current_time = time.time()
            
            return (current_time - last_execution) >= interval
        
        elif schedule_type == 'once':
            scheduled_time = schedule_config.get('scheduled_time', 0)
            return time.time() >= scheduled_time
        
        return True
    
    async def _check_resource_limits(self) -> bool:
        """检查资源限制"""
        # 检查当前运行的任务数量
        running_tasks = await self.list_tasks(status='running', use_cache=False)
        max_concurrent = 10  # 最大并发任务数
        
        return len(running_tasks) < max_concurrent
    
    async def _schedule_task_execution(self, task: Dict):
        """调度任务执行"""
        task_id = task['task_id']
        
        try:
            # 更新任务状态为运行中
            await self.update_task_status(task_id, TaskStatus.RUNNING)
            
            # 添加状态监控
            self.add_status_monitor(task_id)
            
            # 这里应该调用实际的任务执行器
            # await self.execute_task(task_id)
            
            logger.info(f"任务 {task_id} 已调度执行")
            
        except Exception as e:
            logger.error(f"调度任务 {task_id} 执行失败: {e}")
            await self.update_task_status(task_id, TaskStatus.FAILED)
    
    def add_task_dependency(self, task_id: str, dependency_id: str):
        """添加任务依赖关系"""
        if task_id not in self._task_dependencies:
            self._task_dependencies[task_id] = []
        
        if dependency_id not in self._task_dependencies[task_id]:
            self._task_dependencies[task_id].append(dependency_id)
            logger.info(f"已添加任务依赖: {task_id} -> {dependency_id}")
    
    def remove_task_dependency(self, task_id: str, dependency_id: str):
        """移除任务依赖关系"""
        if task_id in self._task_dependencies:
            if dependency_id in self._task_dependencies[task_id]:
                self._task_dependencies[task_id].remove(dependency_id)
                logger.info(f"已移除任务依赖: {task_id} -> {dependency_id}")
    
    def get_task_dependencies(self, task_id: str) -> List[str]:
        """获取任务依赖列表"""
        return self._task_dependencies.get(task_id, [])
    
    async def get_scheduler_status(self) -> Dict[str, Any]:
        """获取调度器状态信息"""
        pending_tasks = await self.list_tasks(status='pending', use_cache=False)
        running_tasks = await self.list_tasks(status='running', use_cache=False)
        
        return {
            'scheduler_active': self._scheduler_active,
            'scheduler_interval': self._scheduler_interval,
            'pending_tasks_count': len(pending_tasks),
            'running_tasks_count': len(running_tasks),
            'task_dependencies': dict(self._task_dependencies)
        }
                
    def _validate_task_config(self, config: TaskConfig) -> None:
        """验证任务配置
        
        Args:
            config: 任务配置
            
        Raises:
            TaskValidationError: 配置验证失败
        """
        if not config.task_name or not config.task_name.strip():
            raise TaskValidationError("任务名称不能为空")
        
        if len(config.task_name) > 255:
            raise TaskValidationError("任务名称长度不能超过255个字符")
        
        if config.description and len(config.description) > 1000:
            raise TaskValidationError("任务描述长度不能超过1000个字符")
        
        if config.timeout_seconds and config.timeout_seconds <= 0:
            raise TaskValidationError("超时时间必须大于0")
        
        if config.max_retry_count and config.max_retry_count < 0:
            raise TaskValidationError("最大重试次数不能为负数")
        
        # 验证任务类型和优先级
        if not isinstance(config.task_type, TaskType):
            raise TaskValidationError("无效的任务类型")
        
        if not isinstance(config.priority, TaskPriority):
            raise TaskValidationError("无效的任务优先级")
        
        # 验证参数格式
        if config.custom_params and not isinstance(config.custom_params, dict):
            raise TaskValidationError("任务参数必须是字典格式")
        
        # 验证调度配置
        if config.schedule_enabled and config.schedule_time:
            self._validate_schedule_config(config)
    
    def _validate_schedule_config(self, config: TaskConfig) -> None:
        """验证调度配置
        
        Args:
            config: 任务配置
            
        Raises:
            TaskValidationError: 调度配置验证失败
        """
        if config.schedule_time:
            import re
            time_pattern = r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$'
            if not re.match(time_pattern, config.schedule_time):
                raise TaskValidationError("调度时间格式无效，应为HH:MM格式")
        
        if config.schedule_days:
            valid_days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
            for day in config.schedule_days:
                if day.lower() not in valid_days:
                    raise TaskValidationError(f"无效的星期: {day}")
            
    def _validate_status_transition(self, current_status: str, new_status: str) -> None:
        """验证状态转换是否合法
        
        Args:
            current_status: 当前状态
            new_status: 新状态
            
        Raises:
            TaskStateError: 状态转换不合法
        """
        # 定义合法的状态转换矩阵
        valid_transitions = {
            'pending': ['running', 'cancelled'],
            'running': ['completed', 'failed', 'paused', 'cancelled'],
            'paused': ['running', 'cancelled'],
            'completed': [],  # 完成状态不能转换到其他状态
            'failed': ['pending', 'running'],  # 失败可以重新开始或重试
            'cancelled': ['pending']  # 取消可以重新开始
        }
        
        # 验证状态值的有效性
        all_valid_statuses = set(valid_transitions.keys())
        for transitions in valid_transitions.values():
            all_valid_statuses.update(transitions)
        
        if current_status not in all_valid_statuses:
            raise TaskStateError(f"未知的当前状态: {current_status}")
        
        if new_status not in all_valid_statuses:
            raise TaskStateError(f"未知的目标状态: {new_status}")
        
        # 检查是否为相同状态（允许但记录警告）
        if current_status == new_status:
            logger.warning(f"状态转换为相同状态: {current_status}")
            return
        
        # 检查转换是否合法
        if new_status not in valid_transitions.get(current_status, []):
            raise TaskStateError(
                f"不能从状态 '{current_status}' 转换到 '{new_status}'。"
                f"允许的转换: {valid_transitions.get(current_status, [])}"
            )
        
        logger.debug(f"状态转换验证通过: {current_status} -> {new_status}")
    
    def _handle_database_error(self, error: Exception, operation: str, task_id: str = None):
        """统一处理数据库错误"""
        error_msg = str(error).lower()
        
        if "unique constraint" in error_msg or "duplicate" in error_msg:
            logger.error(f"{operation}失败 - 数据重复: {error}")
            raise TaskValidationError(f"任务ID或名称已存在")
        elif "foreign key" in error_msg:
            logger.error(f"{operation}失败 - 外键约束: {error}")
            raise TaskValidationError(f"关联数据不存在")
        elif "database is locked" in error_msg:
            logger.error(f"{operation}失败 - 数据库锁定: {error}")
            raise RuntimeError(f"数据库繁忙，请稍后重试")
        else:
            logger.error(f"{operation}失败: {error}")
            raise RuntimeError(f"{operation}操作失败")
    
    async def batch_create_tasks(self, tasks_data: List[Dict]) -> List[str]:
        """批量创建任务"""
        task_ids = []
        async with self.get_async_connection() as conn:
            try:
                await conn.execute("BEGIN TRANSACTION")
                
                for task_data in tasks_data:
                    # 验证任务配置
                    config_data = task_data.get('config', {})
                    # 转换枚举类型
                    if 'task_type' in config_data and isinstance(config_data['task_type'], str):
                        config_data['task_type'] = TaskType(config_data['task_type'])
                    if 'priority' in config_data and isinstance(config_data['priority'], str):
                        config_data['priority'] = TaskPriority(config_data['priority'])
                    
                    config = TaskConfig(**config_data)
                    self._validate_task_config(config)
                    
                    task_id = str(uuid.uuid4())
                    task_ids.append(task_id)
                    
                    # 插入任务基本信息
                    await conn.execute(
                        "INSERT INTO tasks (task_id, user_id, task_name, description, task_type, priority, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (task_id, task_data['user_id'], task_data['name'], task_data.get('description', ''),
                         config.task_type.value, config.priority.value, 'pending', datetime.now(), datetime.now())
                    )
                    
                    # 插入任务配置
                    config_dict = config.__dict__.copy()
                    # 转换枚举为字符串值以便JSON序列化
                    if 'task_type' in config_dict:
                        config_dict['task_type'] = config_dict['task_type'].value
                    if 'priority' in config_dict:
                        config_dict['priority'] = config_dict['priority'].value
                    
                    await conn.execute(
                        "INSERT INTO task_configs (config_id, task_id, config_key, config_value) VALUES (?, ?, ?, ?)",
                        (str(uuid.uuid4()), task_id, "full_config", json.dumps(config_dict, ensure_ascii=False))
                    )
                
                await conn.commit()
                logger.info(f"批量创建任务成功，共创建 {len(task_ids)} 个任务")
                return task_ids
                
            except Exception as e:
                await conn.rollback()
                self._handle_database_error(e, "批量创建任务")
                raise
    
    async def batch_update_task_status(self, task_status_updates: List[Dict[str, str]]) -> bool:
        """批量更新任务状态"""
        async with self.get_async_connection() as conn:
            try:
                await conn.execute("BEGIN TRANSACTION")
                
                for update in task_status_updates:
                    task_id = update['task_id']
                    new_status = update['status']
                    
                    # 获取当前状态
                    cursor = await conn.execute(
                        "SELECT status FROM tasks WHERE task_id = ?", (task_id,)
                    )
                    result = await cursor.fetchone()
                    if not result:
                        raise TaskValidationError(f"任务 {task_id} 不存在")
                    
                    current_status = result[0]
                    self._validate_status_transition(current_status, new_status)
                    
                    # 更新状态
                    update_time = datetime.now()
                    last_execution = update_time if new_status in ['running', 'completed', 'failed'] else None
                    
                    await conn.execute(
                        "UPDATE tasks SET status = ?, updated_at = ?, last_execution = ? WHERE task_id = ?",
                        (new_status, update_time, last_execution, task_id)
                    )
                
                await conn.commit()
                logger.info(f"批量更新任务状态成功，共更新 {len(task_status_updates)} 个任务")
                return True
                
            except Exception as e:
                await conn.rollback()
                self._handle_database_error(e, "批量更新任务状态")
                raise
    
    async def execute_in_transaction(self, operations: List[callable]) -> List:
        """在事务中执行多个操作"""
        results = []
        async with self.get_async_connection() as conn:
            try:
                await conn.execute("BEGIN TRANSACTION")
                
                for operation in operations:
                    if asyncio.iscoroutinefunction(operation):
                        result = await operation(conn)
                    else:
                        result = operation(conn)
                    results.append(result)
                
                await conn.commit()
                logger.info(f"事务执行成功，共执行 {len(operations)} 个操作")
                return results
                
            except Exception as e:
                await conn.rollback()
                self._handle_database_error(e, "事务执行")
                raise
    
    async def create_task(self, config: TaskConfig, user_id: Optional[str] = None) -> str:
        """异步创建新任务
        
        Args:
            config: 任务配置
            user_id: 用户ID，如果为None则使用默认用户
            
        Returns:
            str: 任务ID
            
        Raises:
            TaskValidationError: 配置验证失败
        """
        # 验证任务配置
        self._validate_task_config(config)
        
        if user_id is None:
            user_id = self.default_user_id
        
        # 生成任务ID
        task_id = str(uuid.uuid4())
        
        # 创建任务对象
        task = Task(
            task_id=task_id,
            user_id=user_id,
            config=config,
            status=TaskStatus.PENDING,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # 使用事务保存到数据库
        async with self.get_async_connection() as conn:
            try:
                await conn.execute("BEGIN TRANSACTION")
                
                # 插入任务基本信息
                await conn.execute(
                    "INSERT INTO tasks (task_id, user_id, task_name, task_type, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (task_id, user_id, config.task_name, config.task_type.value, TaskStatus.PENDING.value, 
                     task.created_at.isoformat(), task.updated_at.isoformat())
                )
                
                # 插入任务配置
                config_data = asdict(config)
                config_data['task_type'] = config.task_type.value
                config_data['priority'] = config.priority.value
                
                await conn.execute(
                    "INSERT INTO task_configs (config_id, task_id, config_key, config_value) VALUES (?, ?, ?, ?)",
                    (str(uuid.uuid4()), task_id, "full_config", json.dumps(config_data, ensure_ascii=False))
                )
                
                await conn.commit()
                logger.info(f"创建任务成功: {config.task_name} (ID: {task_id})")
                return task_id
                
            except Exception as e:
                await conn.rollback()
                self._handle_database_error(e, "创建任务", task_id)
                raise
    
    async def get_task(self, task_id: str) -> Optional[Task]:
        """异步获取任务详情
        
        Args:
            task_id: 任务ID
            
        Returns:
            Optional[Task]: 任务对象，如果不存在则返回None
        """
        async with self.get_async_connection() as conn:
            try:
                # 获取任务基本信息
                cursor = await conn.execute(
                    "SELECT * FROM tasks WHERE task_id = ?",
                    (task_id,)
                )
                
                task_row = await cursor.fetchone()
                if not task_row:
                    return None
                
                # 获取任务配置
                cursor = await conn.execute(
                    "SELECT config_value FROM task_configs WHERE task_id = ? AND config_key = 'full_config'",
                    (task_id,)
                )
                
                config_row = await cursor.fetchone()
                if not config_row:
                    logger.warning(f"任务 {task_id} 缺少配置信息")
                    return None
                
                config_data = json.loads(config_row[0])
                config_data['task_type'] = TaskType(config_data['task_type'])
                config_data['priority'] = TaskPriority(config_data['priority'])
                config = TaskConfig(**config_data)
                
                task = Task(
                    task_id=task_row['task_id'],
                    user_id=task_row['user_id'],
                    name=config.task_name,  # 从配置中获取任务名称
                    description=getattr(config, 'description', ''),  # 从配置中获取描述
                    task_type=config.task_type,
                    priority=config.priority,
                    status=TaskStatus(task_row['status']),
                    config=config,
                    created_at=datetime.fromisoformat(task_row['created_at']),
                    updated_at=datetime.fromisoformat(task_row['updated_at'])
                )
                
                return task
                
            except Exception as e:
                logger.error(f"获取任务失败: {e}")
                return None
    
    async def update_task(self, task_id: str, config: Optional[TaskConfig] = None, 
                         status: Optional[TaskStatus] = None) -> bool:
        """异步更新任务信息
        
        Args:
            task_id: 任务ID
            config: 新的任务配置（可选）
            status: 新的任务状态（可选）
            
        Returns:
            bool: 更新是否成功
            
        Raises:
            TaskValidationError: 配置验证失败
            TaskStateError: 状态转换不合法
        """
        # 验证配置
        if config is not None:
            self._validate_task_config(config)
        
        async with self.get_async_connection() as conn:
            try:
                await conn.execute("BEGIN TRANSACTION")
                
                # 检查任务是否存在并获取当前状态
                cursor = await conn.execute("SELECT status FROM tasks WHERE task_id = ?", (task_id,))
                task_row = await cursor.fetchone()
                
                if not task_row:
                    logger.warning(f"任务不存在: {task_id}")
                    return False
                
                current_status = task_row[0]
                
                # 验证状态转换
                if status is not None:
                    self._validate_status_transition(current_status, status.value)
                    
                    await conn.execute(
                        "UPDATE tasks SET status = ?, updated_at = ? WHERE task_id = ?",
                        (status.value, datetime.now().isoformat(), task_id)
                    )
                
                # 更新任务配置
                if config is not None:
                    config_data = asdict(config)
                    config_data['task_type'] = config.task_type.value
                    config_data['priority'] = config.priority.value
                    
                    await conn.execute(
                        "UPDATE task_configs SET config_value = ? WHERE task_id = ? AND config_key = 'full_config'",
                        (json.dumps(config_data, ensure_ascii=False), task_id)
                    )
                
                await conn.commit()
                logger.info(f"更新任务成功: {task_id}")
                return True
                
            except Exception as e:
                await conn.rollback()
                self._handle_database_error(e, "更新任务", task_id)
                raise
    
    async def delete_task(self, task_id: str) -> bool:
        """异步删除任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 删除是否成功
        """
        max_retries = 3
        retry_delay = 0.1
        
        for attempt in range(max_retries):
            try:
                async with self.get_async_connection() as conn:
                    await conn.execute("BEGIN IMMEDIATE TRANSACTION")
                    
                    # 检查任务是否存在
                    cursor = await conn.execute("SELECT 1 FROM tasks WHERE task_id = ?", (task_id,))
                    if not await cursor.fetchone():
                        logger.warning(f"任务 {task_id} 不存在")
                        return False
                    
                    # 删除相关数据（按依赖关系顺序）
                    await conn.execute("DELETE FROM execution_logs WHERE task_id = ?", (task_id,))
                    await conn.execute("DELETE FROM task_configs WHERE task_id = ?", (task_id,))
                    await conn.execute("DELETE FROM tasks WHERE task_id = ?", (task_id,))
                    
                    await conn.commit()
                    logger.info(f"删除任务成功: {task_id}")
                    return True
                    
            except Exception as e:
                if "database is locked" in str(e) and attempt < max_retries - 1:
                    logger.warning(f"数据库锁定，重试 {attempt + 1}/{max_retries}: {e}")
                    await asyncio.sleep(retry_delay * (2 ** attempt))  # 指数退避
                    continue
                else:
                    self._handle_database_error(e, "删除任务", task_id)
                    raise
        
        return False
    
    async def update_task_status(self, task_id: str, status: TaskStatus) -> bool:
        """异步更新任务状态
        
        Args:
            task_id: 任务ID
            status: 新状态
            
        Returns:
            bool: 更新是否成功
            
        Raises:
            TaskStateError: 状态转换不合法
        """
        async with self.get_async_connection() as conn:
            try:
                await conn.execute("BEGIN TRANSACTION")
                
                # 检查任务是否存在并获取当前状态
                cursor = await conn.execute("SELECT status FROM tasks WHERE task_id = ?", (task_id,))
                task_row = await cursor.fetchone()
                
                if not task_row:
                    logger.warning(f"任务 {task_id} 不存在")
                    return False
                
                current_status = task_row[0]
                
                # 验证状态转换
                self._validate_status_transition(current_status, status.value)
                
                # 更新状态和时间戳
                update_fields = ["status = ?", "updated_at = ?"]
                update_values = [status.value, datetime.now().isoformat()]
                
                # 根据状态更新相应的时间戳
                if status == TaskStatus.RUNNING:
                    # 如果是开始运行，记录最后执行时间
                    update_fields.append("last_execution = ?")
                    update_values.append(datetime.now().isoformat())
                elif status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                    # 如果是结束状态，也记录最后执行时间
                    update_fields.append("last_execution = ?")
                    update_values.append(datetime.now().isoformat())
                
                update_values.append(task_id)
                
                await conn.execute(
                    f"UPDATE tasks SET {', '.join(update_fields)} WHERE task_id = ?",
                    update_values
                )
                
                await conn.commit()
                logger.info(f"更新任务状态成功: {task_id} -> {status.value}")
                return True
                
            except Exception as e:
                await conn.rollback()
                self._handle_database_error(e, "更新任务状态", task_id)
                raise
    
    async def list_tasks(self, user_id: Optional[str] = None, status: Optional[TaskStatus] = None,
                           limit: int = 100, offset: int = 0, use_cache: bool = True) -> List[Dict[str, Any]]:
        """异步获取任务列表（支持缓存）
        
        Args:
            user_id: 用户ID（可选）
            status: 任务状态（可选）
            limit: 返回数量限制
            offset: 偏移量
            use_cache: 是否使用缓存
            
        Returns:
            List[Dict]: 任务列表
        """
        # 构建查询条件
        where_conditions = []
        params = []
        
        if user_id:
            where_conditions.append("user_id = ?")
            params.append(user_id)
        
        if status:
            where_conditions.append("status = ?")
            # 处理字符串和枚举类型
            if isinstance(status, str):
                params.append(status)
            else:
                params.append(status.value)
        
        where_clause = ""
        if where_conditions:
            where_clause = "WHERE " + " AND ".join(where_conditions)
        
        # 执行查询（使用索引优化）
        query = f"""
            SELECT task_id, task_name, task_type, status, priority, 
                   created_at, updated_at, last_execution, user_id
            FROM tasks 
            {where_clause}
            ORDER BY created_at DESC 
            LIMIT ? OFFSET ?
        """
        
        params.extend([limit, offset])
        
        if use_cache:
            # 使用缓存查询
            rows_data = await self._cached_query(query, tuple(params))
            tasks = []
            for row_dict in rows_data:
                task_dict = {
                    'task_id': row_dict['task_id'],
                    'task_name': row_dict['task_name'],
                    'task_type': row_dict['task_type'],
                    'status': row_dict['status'],
                    'priority': row_dict['priority'],
                    'created_at': row_dict['created_at'],
                    'updated_at': row_dict['updated_at'],
                    'last_execution': row_dict['last_execution'],
                    'user_id': row_dict['user_id']
                }
                tasks.append(task_dict)
        else:
            # 直接查询
            async with self.get_async_connection() as conn:
                cursor = await conn.execute(query, params)
                rows = await cursor.fetchall()
                
                tasks = []
                for row in rows:
                    task_dict = {
                        'task_id': row[0],
                        'task_name': row[1],
                        'task_type': row[2],
                        'status': row[3],
                        'priority': row[4],
                        'created_at': row[5],
                        'updated_at': row[6],
                        'last_execution': row[7],
                        'user_id': row[8]
                    }
                    tasks.append(task_dict)
        
        return tasks
    
    async def get_task_statistics(self, user_id: Optional[str] = None, use_cache: bool = True) -> Dict[str, Any]:
        """异步获取任务统计信息（支持缓存）
        
        Args:
            user_id: 用户ID（可选）
            use_cache: 是否使用缓存
            
        Returns:
            Dict[str, Any]: 统计信息
        """
        # 构建查询条件
        where_clause = ""
        params = []
        
        if user_id:
            where_clause = "WHERE user_id = ?"
            params = [user_id]
        
        # 使用单个查询获取所有统计信息（性能优化）
        query = f"""
            SELECT 
                COUNT(*) as total_tasks,
                SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending_count,
                SUM(CASE WHEN status = 'running' THEN 1 ELSE 0 END) as running_count,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_count,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_count,
                SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) as cancelled_count,
                SUM(CASE WHEN priority = 'low' THEN 1 ELSE 0 END) as low_priority_count,
                SUM(CASE WHEN priority = 'medium' THEN 1 ELSE 0 END) as medium_priority_count,
                SUM(CASE WHEN priority = 'high' THEN 1 ELSE 0 END) as high_priority_count
            FROM tasks 
            {where_clause}
        """
        
        if use_cache:
            # 使用缓存查询
            rows_data = await self._cached_query(query, tuple(params))
            stats_row = rows_data[0] if rows_data else {}
        else:
            # 直接查询
            async with self.get_async_connection() as conn:
                cursor = await conn.execute(query, params)
                row = await cursor.fetchone()
                # 将Row对象转换为字典以便统一处理
                if row:
                    stats_row = {
                        'total_count': row[0],
                        'pending_count': row[1],
                        'running_count': row[2],
                        'completed_count': row[3],
                        'failed_count': row[4],
                        'cancelled_count': row[5],
                        'low_priority_count': row[6],
                        'medium_priority_count': row[7],
                        'high_priority_count': row[8]
                    }
                else:
                    stats_row = {}
        
        # 获取类型统计
        type_query = f"""
            SELECT task_type, COUNT(*) as count
            FROM tasks 
            {where_clause}
            GROUP BY task_type
        """
        
        if use_cache:
            type_rows_data = await self._cached_query(type_query, tuple(params))
            type_stats = {row['task_type']: row['count'] for row in type_rows_data}
        else:
            async with self.get_async_connection() as conn:
                cursor = await conn.execute(type_query, params)
                type_rows = await cursor.fetchall()
                type_stats = {row[0]: row[1] for row in type_rows}
        
        return {
            'total_tasks': stats_row.get('total_count', 0) if stats_row else 0,
            'status_distribution': {
                'pending': stats_row.get('pending_count', 0) if stats_row else 0,
                'running': stats_row.get('running_count', 0) if stats_row else 0,
                'completed': stats_row.get('completed_count', 0) if stats_row else 0,
                'failed': stats_row.get('failed_count', 0) if stats_row else 0,
                'cancelled': stats_row.get('cancelled_count', 0) if stats_row else 0
            },
            'priority_distribution': {
                'low': stats_row.get('low_priority_count', 0) if stats_row else 0,
                'medium': stats_row.get('medium_priority_count', 0) if stats_row else 0,
                'high': stats_row.get('high_priority_count', 0) if stats_row else 0
            },
            'type_distribution': type_stats
        }
    
    def add_task_action(self, task_id: str, action_type: str, action_data: Dict[str, Any]) -> str:
        """为任务添加动作
        
        Args:
            task_id: 任务ID
            action_type: 动作类型
            action_data: 动作数据
            
        Returns:
            str: 动作ID
        """
        action_id = str(uuid.uuid4())
        
        # 准备动作数据
        coordinates = action_data.get('coordinates', '{}')
        if isinstance(coordinates, dict):
            coordinates = json.dumps(coordinates)
        
        parameters = action_data.get('parameters', {})
        if isinstance(parameters, dict):
            parameters = json.dumps(parameters)
        
        # 创建动作记录
        self.db_manager.create_task_action(
            task_id=task_id,
            action_type=action_type,
            action_order=action_data.get('sequence_order', 0),
            target_element=action_data.get('target_element', ''),
            coordinates=coordinates,
            key_code=action_data.get('key_code', ''),
            wait_duration=action_data.get('wait_duration', 0.0),
            screenshot_path=action_data.get('screenshot_path', ''),
            custom_script=action_data.get('custom_script', ''),
            parameters=parameters
        )
        
        logger.info(f"为任务 {task_id} 添加动作: {action_type} (ID: {action_id})")
        return action_id
    
    def get_task_actions(self, task_id: str) -> List[Dict[str, Any]]:
        """获取任务的所有动作
        
        Args:
            task_id: 任务ID
            
        Returns:
            List[Dict[str, Any]]: 动作列表
        """
        return self.db_manager.get_task_actions(task_id)
    
    def update_task_action(self, action_id: str, action_data: Dict[str, Any]) -> bool:
        """更新任务动作
        
        Args:
            action_id: 动作ID
            action_data: 新的动作数据
            
        Returns:
            bool: 是否更新成功
        """
        # 准备更新数据
        update_data = {}
        
        if 'action_type' in action_data:
            update_data['action_type'] = action_data['action_type']
        
        if 'sequence_order' in action_data:
            update_data['action_order'] = action_data['sequence_order']
        
        if 'coordinates' in action_data:
            coordinates = action_data['coordinates']
            if isinstance(coordinates, dict):
                coordinates = json.dumps(coordinates)
            update_data['coordinates'] = coordinates
        
        if 'key_code' in action_data:
            update_data['key_code'] = action_data['key_code']
        
        if 'wait_duration' in action_data:
            update_data['wait_duration'] = action_data['wait_duration']
        
        if 'screenshot_path' in action_data:
            update_data['screenshot_path'] = action_data['screenshot_path']
        
        if 'custom_script' in action_data:
            update_data['custom_script'] = action_data['custom_script']
        
        if 'parameters' in action_data:
            parameters = action_data['parameters']
            if isinstance(parameters, dict):
                parameters = json.dumps(parameters)
            update_data['parameters'] = parameters
        
        if 'description' in action_data:
            update_data['description'] = action_data['description']
        
        if not update_data:
            return False
        
        success = self.db_manager.update_task_action(action_id, **update_data)
        
        if success:
            logger.info(f"更新动作成功: {action_id}")
        else:
            logger.warning(f"更新动作失败: {action_id}")
        
        return success
    
    def delete_task_action(self, action_id: str) -> bool:
        """删除任务动作
        
        Args:
            action_id: 动作ID
            
        Returns:
            bool: 是否删除成功
        """
        success = self.db_manager.delete_task_action(action_id)
        
        if success:
            logger.info(f"删除动作成功: {action_id}")
        else:
            logger.warning(f"删除动作失败: {action_id}")
        
        return success
    
    async def execute_task(self, task_id: str, user_id: Optional[str] = None) -> str:
        """异步执行任务
        
        Args:
            task_id: 任务ID
            user_id: 用户ID（可选）
            
        Returns:
            str: 执行ID
        """
        if user_id is None:
            user_id = self.default_user_id
        
        # 获取任务
        task = await self.get_task(task_id)
        if not task:
            raise ValueError(f"任务不存在: {task_id}")
        
        # 检查任务状态
        if task.status == TaskStatus.RUNNING:
            raise RuntimeError(f"任务正在执行中: {task_id}")
        
        # 执行任务
        execution_id = await self.task_executor.execute_task(task, user_id)
        
        logger.info(f"开始执行任务: {task_id} (执行ID: {execution_id})")
        return execution_id
    
    def pause_task_execution(self):
        """暂停当前任务执行"""
        self.task_executor.pause_execution()
    
    def resume_task_execution(self):
        """恢复当前任务执行"""
        self.task_executor.resume_execution()
    
    def stop_task_execution(self):
        """停止当前任务执行"""
        self.task_executor.stop_execution()
    
    def get_execution_status(self) -> Optional[Dict[str, Any]]:
        """获取当前执行状态
        
        Returns:
            Optional[Dict[str, Any]]: 执行状态信息
        """
        return self.task_executor.get_execution_status()
    
    def get_task_executions(self, task_id: str) -> List[Dict[str, Any]]:
        """获取任务的执行历史
        
        Args:
            task_id: 任务ID
            
        Returns:
            List[Dict[str, Any]]: 执行历史列表
        """
        return self.db_manager.get_task_executions(task_id)