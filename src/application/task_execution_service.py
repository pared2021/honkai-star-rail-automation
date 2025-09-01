# -*- coding: utf-8 -*-
"""
任务执行引擎服务 - 应用层服务
负责协调任务执行、状态管理和错误处理
"""

import asyncio
import json
import time
import uuid
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime

from loguru import logger
from PyQt6.QtCore import QObject, pyqtSignal

from core.task_executor import TaskExecutor, ExecutionStatus, ExecutionContext
from core.task_actions import ActionFactory, BaseAction, ActionResult
from automation.automation_controller import AutomationController
from automation.game_detector import GameDetector
from models.task_models import Task, TaskStatus
from database.db_manager import DatabaseManager
from events.event_bus import EventBus
from events.task_events import (
    TaskExecutionStartedEvent, TaskExecutionCompletedEvent,
    TaskExecutionPausedEvent, TaskExecutionResumedEvent,
    TaskExecutionStoppedEvent, TaskExecutionErrorEvent
)
from .base_async_service import BaseAsyncService


@dataclass
class ExecutionRequest:
    """执行请求"""
    task_id: str
    user_id: str
    execution_config: Optional[Dict[str, Any]] = None
    priority: str = "medium"
    retry_count: int = 0
    max_retries: int = 3


@dataclass
class ExecutionResponse:
    """执行响应"""
    execution_id: str
    task_id: str
    status: str
    message: str
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    progress: float = 0.0
    error_details: Optional[Dict[str, Any]] = None


class TaskExecutionError(Exception):
    """任务执行异常"""
    def __init__(self, message: str, error_code: str = None, details: Dict[str, Any] = None):
        super().__init__(message)
        self.error_code = error_code
        self.details = details or {}


class TaskExecutionService(BaseAsyncService):
    """任务执行引擎服务"""
    
    # 信号定义
    execution_started = pyqtSignal(str, str)  # task_id, execution_id
    execution_progress = pyqtSignal(str, str, float)  # task_id, execution_id, progress
    execution_completed = pyqtSignal(str, str, bool)  # task_id, execution_id, success
    execution_paused = pyqtSignal(str, str)  # task_id, execution_id
    execution_resumed = pyqtSignal(str, str)  # task_id, execution_id
    execution_stopped = pyqtSignal(str, str)  # task_id, execution_id
    execution_error = pyqtSignal(str, str, str)  # task_id, execution_id, error_message
    
    def __init__(self, db_manager: DatabaseManager, event_bus: EventBus):
        super().__init__()
        self.db_manager = db_manager
        self.event_bus = event_bus
        
        # 核心组件
        self.task_executor = TaskExecutor(db_manager)
        self.automation_controller = AutomationController()
        self.game_detector = GameDetector()
        
        # 执行状态管理
        self.active_executions: Dict[str, ExecutionContext] = {}
        self.execution_queue: List[ExecutionRequest] = []
        self.is_processing = False
        
        # 配置
        self.max_concurrent_executions = 1  # 当前只支持单任务执行
        self.execution_timeout = 3600  # 1小时超时
        
        # 连接信号
        self._connect_signals()
        
        # 注册事件处理器
        self._register_event_handlers()
    
    def _connect_signals(self):
        """连接信号"""
        # 连接TaskExecutor信号
        self.task_executor.execution_started.connect(self._on_execution_started)
        self.task_executor.execution_progress.connect(self._on_execution_progress)
        self.task_executor.execution_completed.connect(self._on_execution_completed)
        self.task_executor.execution_paused.connect(self._on_execution_paused)
        self.task_executor.execution_resumed.connect(self._on_execution_resumed)
        self.task_executor.execution_stopped.connect(self._on_execution_stopped)
        self.task_executor.execution_error.connect(self._on_execution_error)
    
    def _register_event_handlers(self):
        """注册事件处理器"""
        pass  # 可以根据需要添加事件处理器
    
    async def start_task_execution(self, request: ExecutionRequest) -> ExecutionResponse:
        """开始任务执行
        
        Args:
            request: 执行请求
            
        Returns:
            ExecutionResponse: 执行响应
        """
        try:
            # 验证请求
            await self._validate_execution_request(request)
            
            # 检查是否已有任务在执行
            if len(self.active_executions) >= self.max_concurrent_executions:
                # 添加到队列
                self.execution_queue.append(request)
                return ExecutionResponse(
                    execution_id="",
                    task_id=request.task_id,
                    status="queued",
                    message="任务已添加到执行队列"
                )
            
            # 获取任务信息
            task = await self._get_task(request.task_id)
            if not task:
                raise TaskExecutionError(f"任务不存在: {request.task_id}")
            
            # 检查游戏状态（如果需要）
            if await self._requires_game_detection(task):
                game_status = await self._check_game_status()
                if not game_status['is_running']:
                    raise TaskExecutionError("游戏未运行，无法执行任务")
            
            # 开始执行
            execution_id = self.task_executor.execute_task(task, request.user_id)
            
            # 记录执行上下文
            execution_context = self.task_executor.get_execution_status()
            if execution_context:
                self.active_executions[execution_id] = ExecutionContext(**execution_context)
            
            # 发布事件
            event = TaskExecutionStartedEvent(
                task_id=request.task_id,
                execution_id=execution_id,
                user_id=request.user_id,
                timestamp=datetime.now()
            )
            await self.event_bus.publish(event)
            
            return ExecutionResponse(
                execution_id=execution_id,
                task_id=request.task_id,
                status="running",
                message="任务执行已开始",
                start_time=time.time()
            )
            
        except Exception as e:
            logger.error(f"启动任务执行失败: {str(e)}")
            raise TaskExecutionError(f"启动任务执行失败: {str(e)}")
    
    async def pause_task_execution(self, execution_id: str) -> ExecutionResponse:
        """暂停任务执行
        
        Args:
            execution_id: 执行ID
            
        Returns:
            ExecutionResponse: 执行响应
        """
        try:
            if execution_id not in self.active_executions:
                raise TaskExecutionError(f"执行不存在: {execution_id}")
            
            self.task_executor.pause_execution()
            
            execution_context = self.active_executions[execution_id]
            
            return ExecutionResponse(
                execution_id=execution_id,
                task_id=execution_context.task_id,
                status="paused",
                message="任务执行已暂停"
            )
            
        except Exception as e:
            logger.error(f"暂停任务执行失败: {str(e)}")
            raise TaskExecutionError(f"暂停任务执行失败: {str(e)}")
    
    async def resume_task_execution(self, execution_id: str) -> ExecutionResponse:
        """恢复任务执行
        
        Args:
            execution_id: 执行ID
            
        Returns:
            ExecutionResponse: 执行响应
        """
        try:
            if execution_id not in self.active_executions:
                raise TaskExecutionError(f"执行不存在: {execution_id}")
            
            self.task_executor.resume_execution()
            
            execution_context = self.active_executions[execution_id]
            
            return ExecutionResponse(
                execution_id=execution_id,
                task_id=execution_context.task_id,
                status="running",
                message="任务执行已恢复"
            )
            
        except Exception as e:
            logger.error(f"恢复任务执行失败: {str(e)}")
            raise TaskExecutionError(f"恢复任务执行失败: {str(e)}")
    
    async def stop_task_execution(self, execution_id: str) -> ExecutionResponse:
        """停止任务执行
        
        Args:
            execution_id: 执行ID
            
        Returns:
            ExecutionResponse: 执行响应
        """
        try:
            if execution_id not in self.active_executions:
                raise TaskExecutionError(f"执行不存在: {execution_id}")
            
            self.task_executor.stop_execution()
            
            execution_context = self.active_executions[execution_id]
            
            return ExecutionResponse(
                execution_id=execution_id,
                task_id=execution_context.task_id,
                status="stopped",
                message="任务执行已停止"
            )
            
        except Exception as e:
            logger.error(f"停止任务执行失败: {str(e)}")
            raise TaskExecutionError(f"停止任务执行失败: {str(e)}")
    
    async def get_execution_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """获取执行状态
        
        Args:
            execution_id: 执行ID
            
        Returns:
            Optional[Dict[str, Any]]: 执行状态信息
        """
        if execution_id in self.active_executions:
            return self.active_executions[execution_id].to_dict()
        
        # 从数据库查询历史执行记录
        return await self._get_execution_from_db(execution_id)
    
    async def get_active_executions(self) -> List[Dict[str, Any]]:
        """获取活动执行列表
        
        Returns:
            List[Dict[str, Any]]: 活动执行列表
        """
        return [context.to_dict() for context in self.active_executions.values()]
    
    async def get_execution_queue(self) -> List[Dict[str, Any]]:
        """获取执行队列
        
        Returns:
            List[Dict[str, Any]]: 执行队列
        """
        return [
            {
                'task_id': req.task_id,
                'user_id': req.user_id,
                'priority': req.priority,
                'retry_count': req.retry_count
            }
            for req in self.execution_queue
        ]
    
    # 信号处理器
    def _on_execution_started(self, task_id: str, execution_id: str):
        """执行开始信号处理"""
        logger.info(f"任务执行开始: {task_id} (执行ID: {execution_id})")
        self.execution_started.emit(task_id, execution_id)
    
    def _on_execution_progress(self, task_id: str, execution_id: str, progress: float):
        """执行进度信号处理"""
        logger.debug(f"任务执行进度: {task_id} - {progress:.1f}%")
        self.execution_progress.emit(task_id, execution_id, progress)
    
    def _on_execution_completed(self, task_id: str, execution_id: str, success: bool):
        """执行完成信号处理"""
        logger.info(f"任务执行完成: {task_id} - {'成功' if success else '失败'}")
        
        # 清理执行上下文
        if execution_id in self.active_executions:
            del self.active_executions[execution_id]
        
        # 处理队列中的下一个任务
        asyncio.create_task(self._process_next_in_queue())
        
        self.execution_completed.emit(task_id, execution_id, success)
    
    def _on_execution_paused(self, task_id: str, execution_id: str):
        """执行暂停信号处理"""
        logger.info(f"任务执行暂停: {task_id}")
        self.execution_paused.emit(task_id, execution_id)
    
    def _on_execution_resumed(self, task_id: str, execution_id: str):
        """执行恢复信号处理"""
        logger.info(f"任务执行恢复: {task_id}")
        self.execution_resumed.emit(task_id, execution_id)
    
    def _on_execution_stopped(self, task_id: str, execution_id: str):
        """执行停止信号处理"""
        logger.info(f"任务执行停止: {task_id}")
        
        # 清理执行上下文
        if execution_id in self.active_executions:
            del self.active_executions[execution_id]
        
        # 处理队列中的下一个任务
        asyncio.create_task(self._process_next_in_queue())
        
        self.execution_stopped.emit(task_id, execution_id)
    
    def _on_execution_error(self, task_id: str, execution_id: str, error_message: str):
        """执行错误信号处理"""
        logger.error(f"任务执行错误: {task_id} - {error_message}")
        
        # 清理执行上下文
        if execution_id in self.active_executions:
            del self.active_executions[execution_id]
        
        # 处理队列中的下一个任务
        asyncio.create_task(self._process_next_in_queue())
        
        self.execution_error.emit(task_id, execution_id, error_message)
    
    # 辅助方法
    async def _validate_execution_request(self, request: ExecutionRequest):
        """验证执行请求"""
        if not request.task_id:
            raise TaskExecutionError("任务ID不能为空")
        
        if not request.user_id:
            raise TaskExecutionError("用户ID不能为空")
        
        # 检查任务是否存在
        task = await self._get_task(request.task_id)
        if not task:
            raise TaskExecutionError(f"任务不存在: {request.task_id}")
        
        # 检查任务状态
        if task.status not in [TaskStatus.PENDING.value, TaskStatus.CREATED.value]:
            raise TaskExecutionError(f"任务状态不允许执行: {task.status}")
    
    async def _get_task(self, task_id: str) -> Optional[Task]:
        """获取任务信息"""
        try:
            task_data = self.db_manager.get_task(task_id)
            if task_data:
                return Task(**task_data)
            return None
        except Exception as e:
            logger.error(f"获取任务失败: {str(e)}")
            return None
    
    async def _requires_game_detection(self, task: Task) -> bool:
        """检查任务是否需要游戏检测"""
        # 根据任务类型判断是否需要游戏检测
        game_required_types = [
            'daily_mission', 'weekly_mission', 'material_farming',
            'exploration', 'combat_training'
        ]
        return task.task_type in game_required_types
    
    async def _check_game_status(self) -> Dict[str, Any]:
        """检查游戏状态"""
        try:
            is_running = self.game_detector.is_game_running()
            game_window = None
            
            if is_running:
                game_window = self.game_detector.find_game_window()
            
            return {
                'is_running': is_running,
                'game_window': game_window.to_dict() if game_window else None
            }
        except Exception as e:
            logger.error(f"检查游戏状态失败: {str(e)}")
            return {'is_running': False, 'game_window': None}
    
    async def _get_execution_from_db(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """从数据库获取执行记录"""
        try:
            execution_data = self.db_manager.get_task_execution(execution_id)
            return execution_data
        except Exception as e:
            logger.error(f"获取执行记录失败: {str(e)}")
            return None
    
    async def _process_next_in_queue(self):
        """处理队列中的下一个任务"""
        if self.execution_queue and len(self.active_executions) < self.max_concurrent_executions:
            next_request = self.execution_queue.pop(0)
            try:
                await self.start_task_execution(next_request)
            except Exception as e:
                logger.error(f"处理队列任务失败: {str(e)}")
    
    # BaseAsyncService 抽象方法实现
    async def start_service(self):
        """启动服务"""
        logger.info("任务执行引擎服务启动")
        self.is_running = True
    
    async def stop_service(self):
        """停止服务"""
        logger.info("任务执行引擎服务停止")
        
        # 停止所有活动执行
        for execution_id in list(self.active_executions.keys()):
            try:
                await self.stop_task_execution(execution_id)
            except Exception as e:
                logger.error(f"停止执行失败: {str(e)}")
        
        # 清理队列
        self.execution_queue.clear()
        
        self.is_running = False
    
    async def get_service_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        return {
            'service_name': 'TaskExecutionService',
            'is_running': self.is_running,
            'active_executions_count': len(self.active_executions),
            'queue_length': len(self.execution_queue),
            'max_concurrent_executions': self.max_concurrent_executions,
            'execution_timeout': self.execution_timeout
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            # 检查核心组件
            components_status = {
                'task_executor': self.task_executor is not None,
                'automation_controller': self.automation_controller is not None,
                'game_detector': self.game_detector is not None,
                'database': await self._check_database_health(),
                'event_bus': self.event_bus is not None
            }
            
            all_healthy = all(components_status.values())
            
            return {
                'healthy': all_healthy,
                'components': components_status,
                'active_executions': len(self.active_executions),
                'queue_length': len(self.execution_queue),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"健康检查失败: {str(e)}")
            return {
                'healthy': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def _check_database_health(self) -> bool:
        """检查数据库健康状态"""
        try:
            # 简单的数据库连接测试
            self.db_manager.get_connection()
            return True
        except Exception:
            return False