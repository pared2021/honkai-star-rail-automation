# -*- coding: utf-8 -*-
"""
任务执行器 - 负责执行任务和管理动作序列
"""

import json
import time
import uuid
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from loguru import logger
from PyQt6.QtCore import QObject, pyqtSignal, QThread, QTimer

from .task_actions import ActionFactory, BaseAction, ActionResult, ActionStatus
from models.task_models import Task, TaskStatus
from database.db_manager import DatabaseManager


class ExecutionStatus(Enum):
    """执行状态枚举"""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ExecutionContext:
    """执行上下文"""
    task_id: str
    execution_id: str
    user_id: str
    start_time: float
    current_action_index: int = 0
    total_actions: int = 0
    completed_actions: int = 0
    failed_actions: int = 0
    status: ExecutionStatus = ExecutionStatus.IDLE
    error_message: Optional[str] = None
    
    @property
    def progress_percentage(self) -> float:
        """执行进度百分比"""
        if self.total_actions == 0:
            return 0.0
        return (self.completed_actions / self.total_actions) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'task_id': self.task_id,
            'execution_id': self.execution_id,
            'user_id': self.user_id,
            'start_time': self.start_time,
            'current_action_index': self.current_action_index,
            'total_actions': self.total_actions,
            'completed_actions': self.completed_actions,
            'failed_actions': self.failed_actions,
            'progress_percentage': self.progress_percentage,
            'status': self.status.value,
            'error_message': self.error_message
        }


class TaskExecutor(QObject):
    """任务执行器"""
    
    # 信号定义
    execution_started = pyqtSignal(str, str)  # task_id, execution_id
    execution_progress = pyqtSignal(str, str, float)  # task_id, execution_id, progress
    execution_completed = pyqtSignal(str, str, bool)  # task_id, execution_id, success
    execution_paused = pyqtSignal(str, str)  # task_id, execution_id
    execution_resumed = pyqtSignal(str, str)  # task_id, execution_id
    execution_stopped = pyqtSignal(str, str)  # task_id, execution_id
    action_executed = pyqtSignal(str, str, dict)  # task_id, execution_id, action_result
    execution_error = pyqtSignal(str, str, str)  # task_id, execution_id, error_message
    
    def __init__(self, db_manager: DatabaseManager):
        super().__init__()
        self.db_manager = db_manager
        self.current_execution: Optional[ExecutionContext] = None
        self.current_actions: List[BaseAction] = []
        self.is_paused = False
        self.should_stop = False
        
        # 执行定时器
        self.execution_timer = QTimer()
        self.execution_timer.timeout.connect(self._execute_next_action)
        self.execution_timer.setSingleShot(True)
    
    def execute_task(self, task: Task, user_id: str) -> str:
        """执行任务
        
        Args:
            task: 要执行的任务
            user_id: 用户ID
            
        Returns:
            str: 执行ID
        """
        if self.current_execution and self.current_execution.status == ExecutionStatus.RUNNING:
            raise RuntimeError("已有任务正在执行中")
        
        # 创建执行上下文
        execution_id = str(uuid.uuid4())
        self.current_execution = ExecutionContext(
            task_id=task.task_id,
            execution_id=execution_id,
            user_id=user_id,
            start_time=time.time(),
            status=ExecutionStatus.RUNNING
        )
        
        try:
            # 获取任务动作
            self._load_task_actions(task.task_id)
            
            # 创建执行记录
            self.db_manager.create_task_execution(
                task_id=task.task_id,
                execution_id=execution_id,
                user_id=user_id,
                status='running',
                start_time=self.current_execution.start_time
            )
            
            # 更新任务状态
            self.db_manager.update_task_status(task.task_id, TaskStatus.RUNNING.value)
            
            # 发送开始信号
            self.execution_started.emit(task.task_id, execution_id)
            
            # 开始执行
            self._start_execution()
            
            logger.info(f"任务执行开始: {task.task_id} (执行ID: {execution_id})")
            
        except Exception as e:
            error_msg = f"任务执行启动失败: {str(e)}"
            logger.error(error_msg)
            self._handle_execution_error(error_msg)
            raise
        
        return execution_id
    
    def pause_execution(self):
        """暂停执行"""
        if not self.current_execution or self.current_execution.status != ExecutionStatus.RUNNING:
            return
        
        self.is_paused = True
        self.current_execution.status = ExecutionStatus.PAUSED
        self.execution_timer.stop()
        
        # 更新数据库
        self.db_manager.update_task_execution(
            self.current_execution.execution_id,
            status='paused'
        )
        
        self.execution_paused.emit(
            self.current_execution.task_id,
            self.current_execution.execution_id
        )
        
        logger.info(f"任务执行已暂停: {self.current_execution.task_id}")
    
    def resume_execution(self):
        """恢复执行"""
        if not self.current_execution or self.current_execution.status != ExecutionStatus.PAUSED:
            return
        
        self.is_paused = False
        self.current_execution.status = ExecutionStatus.RUNNING
        
        # 更新数据库
        self.db_manager.update_task_execution(
            self.current_execution.execution_id,
            status='running'
        )
        
        self.execution_resumed.emit(
            self.current_execution.task_id,
            self.current_execution.execution_id
        )
        
        # 继续执行
        self._continue_execution()
        
        logger.info(f"任务执行已恢复: {self.current_execution.task_id}")
    
    def stop_execution(self):
        """停止执行"""
        if not self.current_execution:
            return
        
        self.should_stop = True
        self.execution_timer.stop()
        
        if self.current_execution.status in [ExecutionStatus.RUNNING, ExecutionStatus.PAUSED]:
            self.current_execution.status = ExecutionStatus.STOPPED
            
            # 更新数据库
            self.db_manager.update_task_execution(
                self.current_execution.execution_id,
                status='stopped',
                end_time=time.time()
            )
            
            self.db_manager.update_task_status(
                self.current_execution.task_id, 
                TaskStatus.STOPPED.value
            )
            
            self.execution_stopped.emit(
                self.current_execution.task_id,
                self.current_execution.execution_id
            )
            
            logger.info(f"任务执行已停止: {self.current_execution.task_id}")
        
        self._cleanup_execution()
    
    def get_execution_status(self) -> Optional[Dict[str, Any]]:
        """获取当前执行状态"""
        if not self.current_execution:
            return None
        return self.current_execution.to_dict()
    
    def _load_task_actions(self, task_id: str):
        """加载任务动作"""
        actions_data = self.db_manager.get_task_actions(task_id)
        self.current_actions = []
        
        for action_data in actions_data:
            try:
                action = ActionFactory.create_action(action_data)
                self.current_actions.append(action)
            except Exception as e:
                logger.error(f"创建动作失败: {str(e)}, 动作数据: {action_data}")
        
        self.current_execution.total_actions = len(self.current_actions)
        logger.info(f"加载了 {len(self.current_actions)} 个动作")
    
    def _start_execution(self):
        """开始执行"""
        if not self.current_actions:
            self._complete_execution(True, "没有动作需要执行")
            return
        
        self.current_execution.current_action_index = 0
        self.is_paused = False
        self.should_stop = False
        
        # 开始执行第一个动作
        self._continue_execution()
    
    def _continue_execution(self):
        """继续执行"""
        if self.should_stop:
            return
        
        if self.is_paused:
            return
        
        if self.current_execution.current_action_index >= len(self.current_actions):
            self._complete_execution(True)
            return
        
        # 延迟执行下一个动作（避免阻塞UI）
        self.execution_timer.start(100)  # 100ms延迟
    
    def _execute_next_action(self):
        """执行下一个动作"""
        if self.should_stop or self.is_paused:
            return
        
        if self.current_execution.current_action_index >= len(self.current_actions):
            self._complete_execution(True)
            return
        
        # 获取当前动作
        action = self.current_actions[self.current_execution.current_action_index]
        
        try:
            logger.info(f"执行动作 {self.current_execution.current_action_index + 1}/{len(self.current_actions)}: {action.action_type.value}")
            
            # 执行动作
            result = action.execute()
            
            # 记录执行结果
            self._record_action_result(action, result)
            
            # 更新进度
            if result.status == ActionStatus.COMPLETED:
                self.current_execution.completed_actions += 1
            else:
                self.current_execution.failed_actions += 1
            
            # 发送进度信号
            self.execution_progress.emit(
                self.current_execution.task_id,
                self.current_execution.execution_id,
                self.current_execution.progress_percentage
            )
            
            # 发送动作执行信号
            self.action_executed.emit(
                self.current_execution.task_id,
                self.current_execution.execution_id,
                result.to_dict()
            )
            
            # 移动到下一个动作
            self.current_execution.current_action_index += 1
            
            # 继续执行
            self._continue_execution()
            
        except Exception as e:
            error_msg = f"动作执行失败: {str(e)}"
            logger.error(error_msg)
            self._handle_execution_error(error_msg)
    
    def _record_action_result(self, action: BaseAction, result: ActionResult):
        """记录动作执行结果"""
        try:
            # 这里可以扩展为记录到数据库
            log_data = {
                'execution_id': self.current_execution.execution_id,
                'action_id': action.action_id,
                'action_type': action.action_type.value,
                'status': result.status.value,
                'duration': result.duration,
                'error_message': result.error_message,
                'output_data': result.output_data
            }
            
            # 添加执行日志
            self.db_manager.add_execution_log(
                task_id=self.current_execution.task_id,
                execution_id=self.current_execution.execution_id,
                level='INFO' if result.status == ActionStatus.COMPLETED else 'ERROR',
                message=f"动作 {action.action_type.value} 执行{result.status.value}",
                details=json.dumps(log_data, ensure_ascii=False)
            )
            
        except Exception as e:
            logger.error(f"记录动作结果失败: {str(e)}")
    
    def _complete_execution(self, success: bool, message: str = None):
        """完成执行"""
        if not self.current_execution:
            return
        
        end_time = time.time()
        
        if success:
            self.current_execution.status = ExecutionStatus.COMPLETED
            task_status = TaskStatus.COMPLETED.value
        else:
            self.current_execution.status = ExecutionStatus.FAILED
            task_status = TaskStatus.FAILED.value
            if message:
                self.current_execution.error_message = message
        
        # 更新数据库
        self.db_manager.update_task_execution(
            self.current_execution.execution_id,
            status=self.current_execution.status.value.lower(),
            end_time=end_time,
            result_data=json.dumps(self.current_execution.to_dict(), ensure_ascii=False)
        )
        
        self.db_manager.update_task_status(
            self.current_execution.task_id,
            task_status
        )
        
        # 发送完成信号
        self.execution_completed.emit(
            self.current_execution.task_id,
            self.current_execution.execution_id,
            success
        )
        
        logger.info(f"任务执行完成: {self.current_execution.task_id} - {'成功' if success else '失败'}")
        
        self._cleanup_execution()
    
    def _handle_execution_error(self, error_message: str):
        """处理执行错误"""
        if not self.current_execution:
            return
        
        self.current_execution.error_message = error_message
        
        # 发送错误信号
        self.execution_error.emit(
            self.current_execution.task_id,
            self.current_execution.execution_id,
            error_message
        )
        
        # 完成执行（失败）
        self._complete_execution(False, error_message)
    
    def _cleanup_execution(self):
        """清理执行状态"""
        self.execution_timer.stop()
        self.current_execution = None
        self.current_actions = []
        self.is_paused = False
        self.should_stop = False


class TaskExecutorThread(QThread):
    """任务执行器线程"""
    
    def __init__(self, executor: TaskExecutor):
        super().__init__()
        self.executor = executor
    
    def run(self):
        """线程运行"""
        # 在线程中运行执行器
        self.exec()