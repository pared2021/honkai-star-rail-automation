# -*- coding: utf-8 -*-
"""
任务调度器 - 负责任务的调度和优先级管理
"""

import asyncio
import time
from typing import Any, Dict, List, Set

from ..entities.task import TaskPriority, TaskStatus
from ..utils.logger import get_logger

logger = get_logger(__name__)


class TaskScheduler:
    """任务调度器 - 专门负责任务的调度和优先级管理"""

    def __init__(self, config_manager=None, max_concurrent_tasks: int = None):
        """初始化任务调度器

        Args:
            config_manager: 配置管理器
            max_concurrent_tasks: 最大并发任务数
        """
        self.config_manager = config_manager
        self._scheduler_active = False
        self._scheduler_interval = self._get_config_value('task_scheduler.scheduler_interval', 10)  # 调度间隔（秒）
        self._scheduler_task = None
        self._max_concurrent_tasks = max_concurrent_tasks or self._get_config_value('task_scheduler.max_concurrent_tasks', 10)
        
        # 任务依赖关系
        self._task_dependencies: Dict[str, List[str]] = {}
        
        # 优先级权重
        default_weights = {
            "low": 1,
            "medium": 2,
            "high": 3,
            "urgent": 4,
        }
        self._priority_weights = self._get_config_value('task_scheduler.priority_weights', default_weights)
        
        # 调度统计
        self._scheduled_count = 0
        self._failed_schedule_count = 0
    
    def _get_config_value(self, key: str, default_value):
        """获取配置值"""
        if self.config_manager:
            return self.config_manager.get(key, default_value)
        return default_value

    async def start_scheduler(self, interval: int = 10):
        """启动任务调度器

        Args:
            interval: 调度间隔（秒）
        """
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
                pending_tasks = await self._get_pending_tasks()

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

    async def _get_pending_tasks(self) -> List[Dict[str, Any]]:
        """获取待调度的任务
        
        注意：这个方法需要在TaskManager中实现具体的数据库查询逻辑
        """
        # 这里应该调用TaskDatabaseManager来获取待调度的任务
        # 暂时返回空列表，实际实现时需要注入数据库管理器
        return []

    async def _prioritize_tasks(self, tasks: List[Dict]) -> List[Dict]:
        """按优先级和依赖关系对任务进行排序

        Args:
            tasks: 任务列表

        Returns:
            List[Dict]: 排序后的任务列表
        """
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
            task_id = task["task_id"]
            if await self._dependencies_satisfied(task_id, processed_tasks):
                prioritized_tasks.append(task)
                processed_tasks.add(task_id)

        return prioritized_tasks

    async def _calculate_task_priority(self, task: Dict) -> float:
        """计算任务优先级分数

        Args:
            task: 任务信息

        Returns:
            float: 优先级分数
        """
        base_score = self._priority_weights.get(task.get("priority", "medium"), 2)

        # 考虑任务创建时间（越早创建优先级越高）
        created_at = task.get("created_at")
        if created_at:
            if isinstance(created_at, str):
                from datetime import datetime
                created_timestamp = datetime.fromisoformat(created_at).timestamp()
            else:
                created_timestamp = (
                    created_at.timestamp()
                    if hasattr(created_at, "timestamp")
                    else created_at
                )

            # 时间权重：每小时增加0.1分
            time_weight = (time.time() - created_timestamp) / 3600 * 0.1
            base_score += time_weight

        # 考虑任务类型权重
        task_type = task.get("task_type", "default")
        type_weights = {
            "system": 1.5,
            "user": 1.0,
            "background": 0.8,
            "maintenance": 0.6,
        }
        type_weight = type_weights.get(task_type, 1.0)
        base_score *= type_weight

        # 考虑重试次数（重试次数越多优先级越低）
        retry_count = task.get("retry_count", 0)
        retry_penalty = retry_count * 0.2
        base_score -= retry_penalty

        return max(base_score, 0.1)  # 确保最小优先级

    async def _dependencies_satisfied(self, task_id: str, processed_tasks: set) -> bool:
        """检查任务依赖是否满足

        Args:
            task_id: 任务ID
            processed_tasks: 已处理的任务集合

        Returns:
            bool: 依赖是否满足
        """
        dependencies = self._task_dependencies.get(task_id, [])

        for dep_id in dependencies:
            # 检查依赖任务是否已完成
            try:
                # 这里应该调用数据库管理器来检查依赖任务状态
                # dep_task = await self._db_manager.get_task(dep_id)
                # if not dep_task or dep_task["status"] not in ["completed"]:
                #     return False
                pass
            except Exception:
                return False

        return True

    async def _can_execute_task(self, task: Dict) -> bool:
        """检查任务是否可以执行

        Args:
            task: 任务信息

        Returns:
            bool: 是否可以执行
        """
        # 检查调度配置
        config = task.get("config", {})
        if isinstance(config, str):
            try:
                import json
                config = json.loads(config)
            except:
                config = {}

        schedule_config = config.get("schedule", {})

        # 检查调度时间
        if not await self._check_schedule_time(schedule_config):
            return False

        # 检查资源限制
        if not await self._check_resource_limits():
            return False

        return True

    async def _check_schedule_time(self, schedule_config: Dict) -> bool:
        """检查调度时间是否满足

        Args:
            schedule_config: 调度配置

        Returns:
            bool: 时间是否满足
        """
        if not schedule_config:
            return True

        schedule_type = schedule_config.get("type")

        if schedule_type == "cron":
            # 简单的cron检查（这里可以集成更完整的cron库）
            cron_expr = schedule_config.get("expression", "")
            # 暂时返回True，实际应该解析cron表达式
            return True

        elif schedule_type == "interval":
            interval = schedule_config.get("interval", 0)
            last_execution = schedule_config.get("last_execution", 0)
            current_time = time.time()

            return (current_time - last_execution) >= interval

        elif schedule_type == "once":
            scheduled_time = schedule_config.get("scheduled_time", 0)
            return time.time() >= scheduled_time

        return True

    async def _check_resource_limits(self) -> bool:
        """检查资源限制

        Returns:
            bool: 资源是否满足
        """
        # 检查当前运行的任务数量
        # running_tasks = await self._db_manager.list_tasks(status="running", use_cache=False)
        # return len(running_tasks) < self._max_concurrent_tasks
        
        # 暂时返回True，实际实现时需要注入数据库管理器
        return True

    async def _schedule_task_execution(self, task: Dict):
        """调度任务执行

        Args:
            task: 任务信息
        """
        task_id = task["task_id"]

        try:
            # 这里应该调用任务执行器来执行任务
            # await self._task_executor.execute_task(task_id)
            
            self._scheduled_count += 1
            logger.info(f"任务 {task_id} 已调度执行")

        except Exception as e:
            self._failed_schedule_count += 1
            logger.error(f"调度任务 {task_id} 执行失败: {e}")

    def add_task_dependency(self, task_id: str, dependency_id: str):
        """添加任务依赖关系

        Args:
            task_id: 任务ID
            dependency_id: 依赖任务ID
        """
        if task_id not in self._task_dependencies:
            self._task_dependencies[task_id] = []

        if dependency_id not in self._task_dependencies[task_id]:
            self._task_dependencies[task_id].append(dependency_id)
            logger.info(f"已添加任务依赖: {task_id} -> {dependency_id}")

    def remove_task_dependency(self, task_id: str, dependency_id: str):
        """移除任务依赖关系

        Args:
            task_id: 任务ID
            dependency_id: 依赖任务ID
        """
        if task_id in self._task_dependencies:
            if dependency_id in self._task_dependencies[task_id]:
                self._task_dependencies[task_id].remove(dependency_id)
                logger.info(f"已移除任务依赖: {task_id} -> {dependency_id}")

    def get_task_dependencies(self, task_id: str) -> List[str]:
        """获取任务依赖列表

        Args:
            task_id: 任务ID

        Returns:
            List[str]: 依赖任务ID列表
        """
        return self._task_dependencies.get(task_id, [])

    def clear_task_dependencies(self, task_id: str):
        """清除任务的所有依赖关系

        Args:
            task_id: 任务ID
        """
        if task_id in self._task_dependencies:
            del self._task_dependencies[task_id]
            logger.info(f"已清除任务 {task_id} 的所有依赖关系")

    def set_priority_weights(self, weights: Dict[str, float]):
        """设置优先级权重

        Args:
            weights: 优先级权重字典
        """
        self._priority_weights.update(weights)
        logger.info(f"优先级权重已更新: {weights}")

    def set_max_concurrent_tasks(self, max_tasks: int):
        """设置最大并发任务数

        Args:
            max_tasks: 最大并发任务数
        """
        self._max_concurrent_tasks = max_tasks
        logger.info(f"最大并发任务数已更新为: {max_tasks}")

    async def get_scheduler_status(self) -> Dict[str, Any]:
        """获取调度器状态信息

        Returns:
            Dict[str, Any]: 调度器状态
        """
        return {
            "scheduler_active": self._scheduler_active,
            "scheduler_interval": self._scheduler_interval,
            "max_concurrent_tasks": self._max_concurrent_tasks,
            "task_dependencies_count": len(self._task_dependencies),
            "scheduled_count": self._scheduled_count,
            "failed_schedule_count": self._failed_schedule_count,
            "priority_weights": dict(self._priority_weights),
        }

    def reset_stats(self):
        """重置调度统计信息"""
        self._scheduled_count = 0
        self._failed_schedule_count = 0
        logger.info("调度器统计信息已重置")

    def is_active(self) -> bool:
        """检查调度器是否活跃

        Returns:
            bool: 调度器是否活跃
        """
        return self._scheduler_active

    def get_dependency_graph(self) -> Dict[str, List[str]]:
        """获取完整的依赖关系图

        Returns:
            Dict[str, List[str]]: 依赖关系图
        """
        return dict(self._task_dependencies)

    def validate_dependency_cycle(self, task_id: str, dependency_id: str) -> bool:
        """验证添加依赖是否会造成循环依赖

        Args:
            task_id: 任务ID
            dependency_id: 依赖任务ID

        Returns:
            bool: 是否会造成循环依赖
        """
        # 使用深度优先搜索检测循环
        visited = set()
        rec_stack = set()

        def has_cycle(node: str) -> bool:
            if node in rec_stack:
                return True
            if node in visited:
                return False

            visited.add(node)
            rec_stack.add(node)

            # 检查所有依赖
            for dep in self._task_dependencies.get(node, []):
                if has_cycle(dep):
                    return True

            rec_stack.remove(node)
            return False

        # 临时添加依赖关系进行检测
        temp_dependencies = dict(self._task_dependencies)
        if task_id not in temp_dependencies:
            temp_dependencies[task_id] = []
        temp_dependencies[task_id].append(dependency_id)

        # 保存原始依赖关系
        original_dependencies = self._task_dependencies
        self._task_dependencies = temp_dependencies

        # 检测循环
        has_cycle_result = has_cycle(dependency_id)

        # 恢复原始依赖关系
        self._task_dependencies = original_dependencies

        return has_cycle_result