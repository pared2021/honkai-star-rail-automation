# -*- coding: utf-8 -*-
"""重构后的任务管理器 - 核心任务管理逻辑

专注于任务的CRUD操作和基本生命周期管理，
其他职责委托给专门的管理器。
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union
import uuid
from loguru import logger

from src.core.interfaces import (
    ITaskManager,
    ICacheManager,
    ITaskScheduler,
    ITaskMonitor,
    IResourceManager,
    IDatabaseManager,
    ITaskExecutor,
    IEventBus,
    IConfigManager
)
from src.core.dependency_injection import Injectable, inject
from src.models.task_models import Task, TaskConfig, TaskPriority, TaskStatus, TaskType
from src.exceptions import TaskStateError, TaskValidationError


class RefactoredTaskManager(Injectable, ITaskManager):
    """重构后的任务管理器
    
    专注于核心任务管理逻辑：
    - 任务CRUD操作
    - 任务状态管理
    - 任务验证
    - 基本生命周期管理
    
    其他职责委托给专门的管理器：
    - 缓存管理 -> ICacheManager
    - 任务调度 -> ITaskScheduler
    - 状态监控 -> ITaskMonitor
    - 资源管理 -> IResourceManager
    - 任务执行 -> ITaskExecutor
    - 事件发布 -> IEventBus
    - 配置管理 -> IConfigManager
    """
    
    @inject
    def __init__(
        self,
        database_manager: IDatabaseManager,
        cache_manager: ICacheManager,
        task_scheduler: ITaskScheduler,
        task_monitor: ITaskMonitor,
        resource_manager: IResourceManager,
        task_executor: ITaskExecutor,
        event_bus: IEventBus,
        config_manager: IConfigManager,
        default_user_id: str = "default_user"
    ):
        """初始化重构后的任务管理器
        
        Args:
            db_manager: 数据库管理器
            cache_manager: 缓存管理器
            scheduler: 任务调度器
            monitor: 任务监控器
            resource_manager: 资源管理器
            executor: 任务执行器
            event_bus: 事件总线
            config_manager: 配置管理器
            default_user_id: 默认用户ID
        """
        super().__init__()
        self._db_manager = database_manager
        self._cache_manager = cache_manager
        self._scheduler = task_scheduler
        self._monitor = task_monitor
        self._resource_manager = resource_manager
        self._executor = task_executor
        self._event_bus = event_bus
        self._config_manager = config_manager
        self._default_user_id = default_user_id
        
        # 任务验证规则
        self._validation_rules = {
            'name': {'required': True, 'max_length': 255},
            'type': {'required': True, 'enum': [t.value for t in TaskType]},
            'priority': {'required': True, 'enum': [p.value for p in TaskPriority]},
            'config': {'required': True, 'type': dict}
        }
        
        logger.info("重构后的任务管理器初始化完成")
    
    async def create_task(
        self,
        name: str,
        task_type: TaskType,
        config: Dict[str, Any],
        priority: TaskPriority = TaskPriority.MEDIUM,
        user_id: Optional[str] = None,
        parent_id: Optional[str] = None,
        dependencies: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """创建新任务
        
        Args:
            name: 任务名称
            task_type: 任务类型
            config: 任务配置
            priority: 任务优先级
            user_id: 用户ID
            parent_id: 父任务ID
            dependencies: 依赖任务列表
            metadata: 任务元数据
            
        Returns:
            任务ID
            
        Raises:
            TaskValidationError: 任务验证失败
        """
        try:
            # 生成任务ID
            task_id = str(uuid.uuid4())
            user_id = user_id or self._default_user_id
            
            # 验证任务配置
            await self._validate_task_config(name, task_type, config, priority)
            
            # 验证父任务
            if parent_id:
                await self._validate_parent_task(parent_id, user_id)
            
            # 验证依赖任务
            if dependencies:
                await self._validate_dependencies(dependencies, user_id)
            
            # 创建任务对象
            task = Task(
                id=task_id,
                name=name,
                type=task_type,
                status=TaskStatus.PENDING,
                priority=priority,
                config=TaskConfig(**config),
                user_id=user_id,
                parent_id=parent_id,
                dependencies=dependencies or [],
                metadata=metadata or {},
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            # 保存到数据库
            await self._save_task_to_db(task)
            
            # 清理相关缓存
            await self._cache_manager.invalidate_user_cache(user_id)
            await self._cache_manager.invalidate_task_cache(task_id)
            
            # 发布任务创建事件
            await self._event_bus.publish(
                'task.created',
                {
                    'task_id': task_id,
                    'name': name,
                    'type': task_type.value,
                    'priority': priority.value,
                    'user_id': user_id
                },
                source='task_manager'
            )
            
            # 如果有依赖，添加到调度器
            if dependencies:
                for dep_id in dependencies:
                    await self._scheduler.add_task_dependency(task_id, dep_id)
            
            # 添加到监控
            await self._monitor.add_task_monitoring(task_id)
            
            logger.info(f"任务创建成功: {task_id} - {name}")
            return task_id
            
        except Exception as e:
            logger.error(f"创建任务失败: {e}")
            raise TaskValidationError(f"创建任务失败: {str(e)}")
    
    async def get_task(self, task_id: str, user_id: Optional[str] = None) -> Optional[Task]:
        """获取任务信息
        
        Args:
            task_id: 任务ID
            user_id: 用户ID
            
        Returns:
            任务对象，如果不存在则返回None
        """
        try:
            user_id = user_id or self._default_user_id
            
            # 尝试从缓存获取
            cache_key = f"task:{task_id}:{user_id}"
            cached_task = await self._cache_manager.get(cache_key)
            if cached_task:
                return Task(**cached_task)
            
            # 从数据库查询
            task_data = await self._get_task_from_db(task_id, user_id)
            if not task_data:
                return None
            
            task = Task(**task_data)
            
            # 缓存结果
            await self._cache_manager.set(
                cache_key, 
                task_data, 
                ttl=300  # 5分钟缓存
            )
            
            return task
            
        except Exception as e:
            logger.error(f"获取任务失败: {task_id} - {e}")
            return None
    
    async def update_task(
        self,
        task_id: str,
        updates: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> bool:
        """更新任务信息
        
        Args:
            task_id: 任务ID
            updates: 更新数据
            user_id: 用户ID
            
        Returns:
            是否更新成功
        """
        try:
            user_id = user_id or self._default_user_id
            
            # 获取当前任务
            current_task = await self.get_task(task_id, user_id)
            if not current_task:
                logger.warning(f"任务不存在: {task_id}")
                return False
            
            # 验证更新数据
            await self._validate_task_updates(updates, current_task)
            
            # 更新时间戳
            updates['updated_at'] = datetime.now()
            
            # 更新数据库
            success = await self._update_task_in_db(task_id, updates, user_id)
            if not success:
                return False
            
            # 清理缓存
            await self._cache_manager.invalidate_task_cache(task_id)
            await self._cache_manager.invalidate_user_cache(user_id)
            
            # 发布任务更新事件
            await self._event_bus.publish(
                'task.updated',
                {
                    'task_id': task_id,
                    'updates': updates,
                    'user_id': user_id
                },
                source='task_manager'
            )
            
            logger.info(f"任务更新成功: {task_id}")
            return True
            
        except Exception as e:
            logger.error(f"更新任务失败: {task_id} - {e}")
            return False
    
    async def delete_task(self, task_id: str, user_id: Optional[str] = None) -> bool:
        """删除任务
        
        Args:
            task_id: 任务ID
            user_id: 用户ID
            
        Returns:
            是否删除成功
        """
        try:
            user_id = user_id or self._default_user_id
            
            # 检查任务是否存在
            task = await self.get_task(task_id, user_id)
            if not task:
                logger.warning(f"任务不存在: {task_id}")
                return False
            
            # 检查任务状态
            if task.status == TaskStatus.RUNNING:
                logger.warning(f"无法删除正在运行的任务: {task_id}")
                return False
            
            # 移除依赖关系
            await self._remove_task_dependencies(task_id)
            
            # 从数据库删除
            success = await self._delete_task_from_db(task_id, user_id)
            if not success:
                return False
            
            # 清理缓存
            await self._cache_manager.invalidate_task_cache(task_id)
            await self._cache_manager.invalidate_user_cache(user_id)
            
            # 从调度器移除
            await self._scheduler.cancel_task_schedule(task_id)
            
            # 从监控移除
            await self._monitor.remove_task_monitoring(task_id)
            
            # 发布任务删除事件
            await self._event_bus.publish(
                'task.deleted',
                {
                    'task_id': task_id,
                    'user_id': user_id
                },
                source='task_manager'
            )
            
            logger.info(f"任务删除成功: {task_id}")
            return True
            
        except Exception as e:
            logger.error(f"删除任务失败: {task_id} - {e}")
            return False
    
    async def list_tasks(
        self,
        user_id: Optional[str] = None,
        status: Optional[TaskStatus] = None,
        task_type: Optional[TaskType] = None,
        priority: Optional[TaskPriority] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Task]:
        """列出任务
        
        Args:
            user_id: 用户ID
            status: 任务状态过滤
            task_type: 任务类型过滤
            priority: 优先级过滤
            limit: 限制数量
            offset: 偏移量
            
        Returns:
            任务列表
        """
        try:
            user_id = user_id or self._default_user_id
            
            # 构建缓存键
            cache_key = f"tasks:{user_id}:{status}:{task_type}:{priority}:{limit}:{offset}"
            
            # 尝试从缓存获取
            cached_tasks = await self._cache_manager.get(cache_key)
            if cached_tasks:
                return [Task(**task_data) for task_data in cached_tasks]
            
            # 从数据库查询
            tasks_data = await self._query_tasks_from_db(
                user_id, status, task_type, priority, limit, offset
            )
            
            tasks = [Task(**task_data) for task_data in tasks_data]
            
            # 缓存结果
            await self._cache_manager.set(
                cache_key,
                tasks_data,
                ttl=60  # 1分钟缓存
            )
            
            return tasks
            
        except Exception as e:
            logger.error(f"列出任务失败: {e}")
            return []
    
    async def update_task_status(
        self,
        task_id: str,
        status: TaskStatus,
        user_id: Optional[str] = None,
        result: Optional[Any] = None,
        error_message: Optional[str] = None
    ) -> bool:
        """更新任务状态
        
        Args:
            task_id: 任务ID
            status: 新状态
            user_id: 用户ID
            result: 任务结果
            error_message: 错误信息
            
        Returns:
            是否更新成功
        """
        try:
            user_id = user_id or self._default_user_id
            
            # 获取当前任务
            task = await self.get_task(task_id, user_id)
            if not task:
                logger.warning(f"任务不存在: {task_id}")
                return False
            
            # 验证状态转换
            if not self._is_valid_status_transition(task.status, status):
                logger.warning(f"无效的状态转换: {task.status} -> {status}")
                return False
            
            # 准备更新数据
            updates = {
                'status': status,
                'updated_at': datetime.now()
            }
            
            if result is not None:
                updates['result'] = result
            
            if error_message:
                updates['error_message'] = error_message
            
            if status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                updates['finished_at'] = datetime.now()
            
            # 更新数据库
            success = await self._update_task_in_db(task_id, updates, user_id)
            if not success:
                return False
            
            # 清理缓存
            await self._cache_manager.invalidate_task_cache(task_id)
            await self._cache_manager.invalidate_user_cache(user_id)
            
            # 发布状态变更事件
            await self._event_bus.publish(
                'task.status_changed',
                {
                    'task_id': task_id,
                    'old_status': task.status.value,
                    'new_status': status.value,
                    'user_id': user_id,
                    'result': result,
                    'error_message': error_message
                },
                source='task_manager'
            )
            
            logger.info(f"任务状态更新成功: {task_id} - {task.status} -> {status}")
            return True
            
        except Exception as e:
            logger.error(f"更新任务状态失败: {task_id} - {e}")
            return False
    
    async def execute_task(self, task_id: str, user_id: Optional[str] = None) -> bool:
        """执行任务
        
        Args:
            task_id: 任务ID
            user_id: 用户ID
            
        Returns:
            是否成功提交执行
        """
        try:
            user_id = user_id or self._default_user_id
            
            # 获取任务
            task = await self.get_task(task_id, user_id)
            if not task:
                logger.warning(f"任务不存在: {task_id}")
                return False
            
            # 检查任务状态
            if task.status != TaskStatus.PENDING:
                logger.warning(f"任务状态不允许执行: {task_id} - {task.status}")
                return False
            
            # 检查依赖
            if task.dependencies:
                dependencies_satisfied = await self._scheduler.check_dependencies_satisfied(task_id)
                if not dependencies_satisfied:
                    logger.info(f"任务依赖未满足，加入调度队列: {task_id}")
                    await self._scheduler.schedule_task(task_id)
                    return True
            
            # 检查资源
            resource_available = await self._resource_manager.check_resource_availability(
                task_id, task.config.resource_requirements or {}
            )
            if not resource_available:
                logger.info(f"资源不足，任务加入等待队列: {task_id}")
                await self._scheduler.schedule_task(task_id)
                return True
            
            # 提交给执行器
            execution_result = await self._executor.execute_task(
                task_id, task.config.__dict__
            )
            
            logger.info(f"任务提交执行成功: {task_id}")
            return True
            
        except Exception as e:
            logger.error(f"执行任务失败: {task_id} - {e}")
            return False
    
    async def pause_task(self, task_id: str, user_id: Optional[str] = None) -> bool:
        """暂停任务
        
        Args:
            task_id: 任务ID
            user_id: 用户ID
            
        Returns:
            是否暂停成功
        """
        try:
            # 委托给执行器
            success = await self._executor.pause_task(task_id)
            if success:
                await self.update_task_status(task_id, TaskStatus.PAUSED, user_id)
            return success
        except Exception as e:
            logger.error(f"暂停任务失败: {task_id} - {e}")
            return False
    
    async def resume_task(self, task_id: str, user_id: Optional[str] = None) -> bool:
        """恢复任务
        
        Args:
            task_id: 任务ID
            user_id: 用户ID
            
        Returns:
            是否恢复成功
        """
        try:
            # 委托给执行器
            success = await self._executor.resume_task(task_id)
            if success:
                await self.update_task_status(task_id, TaskStatus.RUNNING, user_id)
            return success
        except Exception as e:
            logger.error(f"恢复任务失败: {task_id} - {e}")
            return False
    
    async def cancel_task(self, task_id: str, user_id: Optional[str] = None) -> bool:
        """取消任务
        
        Args:
            task_id: 任务ID
            user_id: 用户ID
            
        Returns:
            是否取消成功
        """
        try:
            # 委托给执行器
            success = await self._executor.cancel_task(task_id)
            if success:
                await self.update_task_status(task_id, TaskStatus.CANCELLED, user_id)
            return success
        except Exception as e:
            logger.error(f"取消任务失败: {task_id} - {e}")
            return False
    
    async def get_task_statistics(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """获取任务统计信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            统计信息字典
        """
        try:
            user_id = user_id or self._default_user_id
            
            # 尝试从缓存获取
            cache_key = f"task_stats:{user_id}"
            cached_stats = await self._cache_manager.get(cache_key)
            if cached_stats:
                return cached_stats
            
            # 计算统计信息
            stats = await self._calculate_task_statistics(user_id)
            
            # 缓存结果
            await self._cache_manager.set(cache_key, stats, ttl=300)
            
            return stats
            
        except Exception as e:
            logger.error(f"获取任务统计失败: {e}")
            return {}
    
    async def search_tasks(
        self,
        query: str,
        user_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Task]:
        """搜索任务
        
        Args:
            query: 搜索查询
            user_id: 用户ID
            limit: 限制数量
            
        Returns:
            匹配的任务列表
        """
        try:
            user_id = user_id or self._default_user_id
            
            # 从数据库搜索
            tasks_data = await self._search_tasks_in_db(query, user_id, limit)
            
            return [Task(**task_data) for task_data in tasks_data]
            
        except Exception as e:
            logger.error(f"搜索任务失败: {e}")
            return []
    
    # 私有辅助方法
    
    async def _validate_task_config(
        self,
        name: str,
        task_type: TaskType,
        config: Dict[str, Any],
        priority: TaskPriority
    ) -> None:
        """验证任务配置"""
        # 验证名称
        if not name or len(name.strip()) == 0:
            raise TaskValidationError("任务名称不能为空")
        
        if len(name) > 255:
            raise TaskValidationError("任务名称长度不能超过255个字符")
        
        # 验证类型
        if not isinstance(task_type, TaskType):
            raise TaskValidationError("无效的任务类型")
        
        # 验证优先级
        if not isinstance(priority, TaskPriority):
            raise TaskValidationError("无效的任务优先级")
        
        # 验证配置
        if not isinstance(config, dict):
            raise TaskValidationError("任务配置必须是字典类型")
        
        # 委托给执行器验证具体配置
        is_valid = await self._executor.validate_task_config(config)
        if not is_valid:
            raise TaskValidationError("任务配置验证失败")
    
    async def _validate_parent_task(self, parent_id: str, user_id: str) -> None:
        """验证父任务"""
        parent_task = await self.get_task(parent_id, user_id)
        if not parent_task:
            raise TaskValidationError(f"父任务不存在: {parent_id}")
    
    async def _validate_dependencies(self, dependencies: List[str], user_id: str) -> None:
        """验证依赖任务"""
        for dep_id in dependencies:
            dep_task = await self.get_task(dep_id, user_id)
            if not dep_task:
                raise TaskValidationError(f"依赖任务不存在: {dep_id}")
    
    async def _validate_task_updates(self, updates: Dict[str, Any], current_task: Task) -> None:
        """验证任务更新"""
        # 检查不可更新的字段
        readonly_fields = {'id', 'created_at', 'user_id'}
        for field in readonly_fields:
            if field in updates:
                raise TaskValidationError(f"字段 {field} 不可更新")
        
        # 验证状态转换
        if 'status' in updates:
            new_status = updates['status']
            if isinstance(new_status, str):
                new_status = TaskStatus(new_status)
            
            if not self._is_valid_status_transition(current_task.status, new_status):
                raise TaskValidationError(
                    f"无效的状态转换: {current_task.status} -> {new_status}"
                )
    
    def _is_valid_status_transition(self, from_status: TaskStatus, to_status: TaskStatus) -> bool:
        """检查状态转换是否有效"""
        valid_transitions = {
            TaskStatus.PENDING: [TaskStatus.RUNNING, TaskStatus.CANCELLED],
            TaskStatus.RUNNING: [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.PAUSED, TaskStatus.CANCELLED],
            TaskStatus.PAUSED: [TaskStatus.RUNNING, TaskStatus.CANCELLED],
            TaskStatus.COMPLETED: [],
            TaskStatus.FAILED: [TaskStatus.PENDING],  # 允许重试
            TaskStatus.CANCELLED: [TaskStatus.PENDING]  # 允许重新启动
        }
        
        return to_status in valid_transitions.get(from_status, [])
    
    # 数据库操作方法
    
    async def _save_task_to_db(self, task: Task) -> None:
        """保存任务到数据库"""
        try:
            task_data = {
                'id': task.id,
                'name': task.name,
                'type': task.type.value,
                'status': task.status.value,
                'priority': task.priority.value,
                'config': task.config.__dict__,
                'user_id': task.user_id,
                'parent_id': task.parent_id,
                'dependencies': task.dependencies,
                'metadata': task.metadata,
                'created_at': task.created_at,
                'updated_at': task.updated_at,
                'started_at': task.started_at,
                'finished_at': task.finished_at,
                'result': task.result,
                'error_message': task.error_message
            }
            await self._db_manager.create_task(task_data)
        except Exception as e:
            logger.error(f"保存任务到数据库失败: {task.id} - {e}")
            raise
    
    async def _get_task_from_db(self, task_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """从数据库获取任务"""
        try:
            return await self._db_manager.get_task(task_id, user_id)
        except Exception as e:
            logger.error(f"从数据库获取任务失败: {task_id} - {e}")
            return None
    
    async def _update_task_in_db(self, task_id: str, updates: Dict[str, Any], user_id: str) -> bool:
        """更新数据库中的任务"""
        try:
            # 转换枚举值为字符串
            processed_updates = {}
            for key, value in updates.items():
                if hasattr(value, 'value'):  # 枚举类型
                    processed_updates[key] = value.value
                else:
                    processed_updates[key] = value
            
            return await self._db_manager.update_task(task_id, processed_updates, user_id)
        except Exception as e:
            logger.error(f"更新数据库任务失败: {task_id} - {e}")
            return False
    
    async def _delete_task_from_db(self, task_id: str, user_id: str) -> bool:
        """从数据库删除任务"""
        try:
            return await self._db_manager.delete_task(task_id, user_id)
        except Exception as e:
            logger.error(f"从数据库删除任务失败: {task_id} - {e}")
            return False
    
    async def _query_tasks_from_db(
        self,
        user_id: str,
        status: Optional[TaskStatus],
        task_type: Optional[TaskType],
        priority: Optional[TaskPriority],
        limit: int,
        offset: int
    ) -> List[Dict[str, Any]]:
        """从数据库查询任务列表"""
        try:
            filters = {'user_id': user_id}
            
            if status:
                filters['status'] = status.value
            if task_type:
                filters['type'] = task_type.value
            if priority:
                filters['priority'] = priority.value
            
            return await self._db_manager.query_tasks(
                filters=filters,
                limit=limit,
                offset=offset,
                order_by='created_at',
                order_desc=True
            )
        except Exception as e:
            logger.error(f"查询数据库任务失败: {e}")
            return []
    
    async def _search_tasks_in_db(self, query: str, user_id: str, limit: int) -> List[Dict[str, Any]]:
        """在数据库中搜索任务"""
        try:
            return await self._db_manager.search_tasks(
                query=query,
                user_id=user_id,
                limit=limit
            )
        except Exception as e:
            logger.error(f"搜索数据库任务失败: {e}")
            return []
    
    async def _calculate_task_statistics(self, user_id: str) -> Dict[str, Any]:
        """计算任务统计信息"""
        try:
            # 获取各状态的任务数量
            stats = {
                'total': 0,
                'pending': 0,
                'running': 0,
                'completed': 0,
                'failed': 0,
                'cancelled': 0,
                'paused': 0
            }
            
            # 按状态统计
            for status in TaskStatus:
                count = await self._db_manager.count_tasks_by_status(user_id, status.value)
                stats[status.value.lower()] = count
                stats['total'] += count
            
            # 按类型统计
            type_stats = {}
            for task_type in TaskType:
                count = await self._db_manager.count_tasks_by_type(user_id, task_type.value)
                type_stats[task_type.value.lower()] = count
            
            stats['by_type'] = type_stats
            
            # 按优先级统计
            priority_stats = {}
            for priority in TaskPriority:
                count = await self._db_manager.count_tasks_by_priority(user_id, priority.value)
                priority_stats[priority.value.lower()] = count
            
            stats['by_priority'] = priority_stats
            
            # 最近活动统计
            recent_stats = await self._db_manager.get_recent_task_activity(user_id, days=7)
            stats['recent_activity'] = recent_stats
            
            return stats
            
        except Exception as e:
            logger.error(f"计算任务统计失败: {e}")
            return {}
    
    async def _remove_task_dependencies(self, task_id: str) -> None:
        """移除任务依赖关系"""
        # 委托给调度器
        await self._scheduler.clear_task_dependencies(task_id)