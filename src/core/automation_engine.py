#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动化引擎核心模块。

这是整个自动化系统的核心协调器，负责：
1. 统一管理所有核心组件
2. 协调任务执行流程
3. 处理系统级事件
4. 提供统一的API接口
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from .events import EventBus
from .logger import get_logger
from .task_manager import TaskManager
from .game_operator import GameOperator
from .error_handler import ErrorHandler
from .smart_waiter import SmartWaiter
from .daily_mission_runner import DailyMissionRunner
from .resource_farming_runner import ResourceFarmingRunner
from .enhanced_task_executor import EnhancedTaskExecutor


class EngineState(Enum):
    """引擎状态枚举。"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    PAUSING = "pausing"
    PAUSED = "paused"
    STOPPING = "stopping"
    ERROR = "error"


class AutomationMode(Enum):
    """自动化模式枚举。"""
    MANUAL = "manual"  # 手动模式
    SEMI_AUTO = "semi_auto"  # 半自动模式
    FULL_AUTO = "full_auto"  # 全自动模式
    SCHEDULED = "scheduled"  # 定时模式


@dataclass
class EngineConfig:
    """引擎配置。"""
    # 基础配置
    game_window_title: str = "崩坏：星穹铁道"
    screenshot_interval: float = 0.5
    max_retry_attempts: int = 3
    
    # 任务配置
    max_concurrent_tasks: int = 3
    task_timeout: int = 300  # 5分钟
    
    # 错误处理配置
    error_recovery_enabled: bool = True
    auto_restart_on_critical_error: bool = True
    
    # 智能等待配置
    smart_wait_enabled: bool = True
    adaptive_delay_enabled: bool = True
    
    # 日志配置
    log_level: str = "INFO"
    log_file_path: Optional[str] = None
    
    # 自动化模式
    automation_mode: AutomationMode = AutomationMode.SEMI_AUTO
    
    # 调度配置
    daily_mission_time: str = "04:00"  # 每日任务执行时间
    resource_farming_enabled: bool = True
    

@dataclass
class EngineStatus:
    """引擎状态信息。"""
    state: EngineState = EngineState.STOPPED
    start_time: Optional[datetime] = None
    uptime: timedelta = field(default_factory=lambda: timedelta())
    
    # 任务统计
    total_tasks_executed: int = 0
    successful_tasks: int = 0
    failed_tasks: int = 0
    
    # 错误统计
    total_errors: int = 0
    recovered_errors: int = 0
    
    # 性能统计
    average_task_duration: float = 0.0
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    
    # 当前活动
    current_task: Optional[str] = None
    active_runners: List[str] = field(default_factory=list)
    

class AutomationEngine:
    """自动化引擎核心类。"""
    
    def __init__(self, config: Optional[EngineConfig] = None):
        """初始化自动化引擎。
        
        Args:
            config: 引擎配置
        """
        self.config = config or EngineConfig()
        self.logger = get_logger(__name__)
        
        # 状态管理
        self.status = EngineStatus()
        self._shutdown_event = asyncio.Event()
        self._pause_event = asyncio.Event()
        
        # 核心组件
        self.event_bus = EventBus()
        self.game_operator = None
        self.error_handler = None
        self.smart_waiter = None
        self.task_manager = None
        self.enhanced_executor = None
        
        # 任务执行器
        self.daily_mission_runner = None
        self.resource_farming_runner = None
        
        # 调度器
        self._scheduler_task = None
        self._monitor_task = None
        
        # 事件处理器
        self._event_handlers = {}
        
        # 性能监控
        self._performance_data = []
        self._last_performance_check = time.time()
        
        self.logger.info("自动化引擎初始化完成")
    
    async def initialize(self) -> bool:
        """初始化所有组件。
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            self.logger.info("开始初始化引擎组件...")
            self.status.state = EngineState.STARTING
            
            # 初始化游戏操作器
            self.game_operator = GameOperator(
                window_title=self.config.game_window_title,
                screenshot_interval=self.config.screenshot_interval
            )
            
            if not await self.game_operator.initialize():
                self.logger.error("游戏操作器初始化失败")
                return False
            
            # 初始化智能等待器
            self.smart_waiter = SmartWaiter(
                game_operator=self.game_operator,
                event_bus=self.event_bus
            )
            
            # 初始化错误处理器
            self.error_handler = ErrorHandler(
                event_bus=self.event_bus,
                game_operator=self.game_operator
            )
            
            # 初始化任务管理器
            self.task_manager = TaskManager(
                event_bus=self.event_bus,
                game_operator=self.game_operator,
                smart_waiter=self.smart_waiter,
                error_handler=self.error_handler,
                max_concurrent_tasks=self.config.max_concurrent_tasks
            )
            
            # 初始化增强任务执行器
            self.enhanced_executor = EnhancedTaskExecutor(
                game_operator=self.game_operator,
                event_bus=self.event_bus
            )
            
            # 初始化任务执行器
            await self._initialize_task_runners()
            
            # 注册事件处理器
            self._register_event_handlers()
            
            # 启动组件
            await self._start_components()
            
            self.status.state = EngineState.RUNNING
            self.status.start_time = datetime.now()
            
            self.logger.info("引擎组件初始化完成")
            return True
            
        except Exception as e:
            self.logger.error(f"引擎初始化失败: {e}")
            self.status.state = EngineState.ERROR
            return False
    
    async def _initialize_task_runners(self):
        """初始化任务执行器。"""
        # 日常任务执行器
        self.daily_mission_runner = DailyMissionRunner(
            game_operator=self.game_operator,
            event_bus=self.event_bus
        )
        
        # 资源刷取执行器
        self.resource_farming_runner = ResourceFarmingRunner(
            game_operator=self.game_operator,
            event_bus=self.event_bus
        )
        
        # 注册到任务管理器
        self.task_manager.register_task_runner('daily_mission', self.daily_mission_runner)
        self.task_manager.register_task_runner('resource_farming', self.resource_farming_runner)
        
        # 注册到增强执行器
        self.enhanced_executor.register_runner('daily_mission', self.daily_mission_runner)
        self.enhanced_executor.register_runner('resource_farming', self.resource_farming_runner)
    
    def _register_event_handlers(self):
        """注册事件处理器。"""
        # 任务事件
        self.event_bus.subscribe('task_started', self._on_task_started)
        self.event_bus.subscribe('task_completed', self._on_task_completed)
        self.event_bus.subscribe('task_failed', self._on_task_failed)
        
        # 错误事件
        self.event_bus.subscribe('error_occurred', self._on_error_occurred)
        self.event_bus.subscribe('error_recovered', self._on_error_recovered)
        
        # 系统事件
        self.event_bus.subscribe('system_overload', self._on_system_overload)
        self.event_bus.subscribe('game_disconnected', self._on_game_disconnected)
    
    async def _start_components(self):
        """启动所有组件。"""
        # 启动任务管理器
        await self.task_manager.start()
        
        # 启动增强执行器
        await self.enhanced_executor.start()
        
        # 启动调度器
        if self.config.automation_mode in [AutomationMode.FULL_AUTO, AutomationMode.SCHEDULED]:
            self._scheduler_task = asyncio.create_task(self._scheduler_loop())
        
        # 启动监控器
        self._monitor_task = asyncio.create_task(self._monitor_loop())
    
    async def start(self) -> bool:
        """启动自动化引擎。
        
        Returns:
            bool: 启动是否成功
        """
        if self.status.state != EngineState.STOPPED:
            self.logger.warning(f"引擎当前状态为 {self.status.state.value}，无法启动")
            return False
        
        success = await self.initialize()
        if success:
            self.logger.info("自动化引擎启动成功")
            await self.event_bus.emit('engine_started', {'status': self.status})
        else:
            self.logger.error("自动化引擎启动失败")
            await self.event_bus.emit('engine_start_failed', {'status': self.status})
        
        return success
    
    async def stop(self):
        """停止自动化引擎。"""
        if self.status.state == EngineState.STOPPED:
            self.logger.warning("引擎已经停止")
            return
        
        self.logger.info("正在停止自动化引擎...")
        self.status.state = EngineState.STOPPING
        
        # 设置停止事件
        self._shutdown_event.set()
        
        # 停止调度器和监控器
        if self._scheduler_task:
            self._scheduler_task.cancel()
        if self._monitor_task:
            self._monitor_task.cancel()
        
        # 停止所有组件
        await self._stop_components()
        
        self.status.state = EngineState.STOPPED
        self.status.start_time = None
        
        self.logger.info("自动化引擎已停止")
        await self.event_bus.emit('engine_stopped', {'status': self.status})
    
    async def _stop_components(self):
        """停止所有组件。"""
        try:
            # 停止任务管理器
            if self.task_manager:
                await self.task_manager.stop()
            
            # 停止增强执行器
            if self.enhanced_executor:
                await self.enhanced_executor.stop()
            
            # 停止错误处理器
            if self.error_handler:
                self.error_handler.shutdown()
            
            # 停止游戏操作器
            if self.game_operator:
                await self.game_operator.cleanup()
            
        except Exception as e:
            self.logger.error(f"停止组件时发生错误: {e}")
    
    async def pause(self):
        """暂停自动化引擎。"""
        if self.status.state != EngineState.RUNNING:
            self.logger.warning(f"引擎当前状态为 {self.status.state.value}，无法暂停")
            return
        
        self.logger.info("正在暂停自动化引擎...")
        self.status.state = EngineState.PAUSING
        
        # 暂停任务管理器
        if self.task_manager:
            await self.task_manager.pause()
        
        # 设置暂停事件
        self._pause_event.set()
        
        self.status.state = EngineState.PAUSED
        self.logger.info("自动化引擎已暂停")
        await self.event_bus.emit('engine_paused', {'status': self.status})
    
    async def resume(self):
        """恢复自动化引擎。"""
        if self.status.state != EngineState.PAUSED:
            self.logger.warning(f"引擎当前状态为 {self.status.state.value}，无法恢复")
            return
        
        self.logger.info("正在恢复自动化引擎...")
        
        # 清除暂停事件
        self._pause_event.clear()
        
        # 恢复任务管理器
        if self.task_manager:
            await self.task_manager.resume()
        
        self.status.state = EngineState.RUNNING
        self.logger.info("自动化引擎已恢复")
        await self.event_bus.emit('engine_resumed', {'status': self.status})
    
    async def execute_task(self, task_type: str, task_config: Dict[str, Any]) -> bool:
        """执行单个任务。
        
        Args:
            task_type: 任务类型
            task_config: 任务配置
            
        Returns:
            bool: 任务是否成功执行
        """
        if self.status.state not in [EngineState.RUNNING, EngineState.PAUSED]:
            self.logger.error(f"引擎状态 {self.status.state.value} 不允许执行任务")
            return False
        
        try:
            # 使用任务管理器执行
            task_id = await self.task_manager.submit_task(
                task_type=task_type,
                task_config=task_config,
                priority='medium'
            )
            
            if task_id:
                self.logger.info(f"任务已提交: {task_id}")
                return True
            else:
                self.logger.error("任务提交失败")
                return False
                
        except Exception as e:
            self.logger.error(f"执行任务时发生错误: {e}")
            await self.error_handler.handle_error(e, {
                'task_type': task_type,
                'task_config': task_config
            })
            return False
    
    async def _scheduler_loop(self):
        """调度器循环。"""
        self.logger.info("调度器已启动")
        
        while not self._shutdown_event.is_set():
            try:
                await self._check_scheduled_tasks()
                await asyncio.sleep(60)  # 每分钟检查一次
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"调度器循环错误: {e}")
                await asyncio.sleep(60)
        
        self.logger.info("调度器已停止")
    
    async def _check_scheduled_tasks(self):
        """检查定时任务。"""
        current_time = datetime.now()
        
        # 检查日常任务时间
        if self._should_run_daily_missions(current_time):
            await self.execute_task('daily_mission', {
                'mission_types': ['daily_training', 'simulated_universe']
            })
        
        # 检查资源刷取
        if self.config.resource_farming_enabled and self._should_run_resource_farming(current_time):
            await self.execute_task('resource_farming', {
                'resource_type': 'experience_materials',
                'target_amount': 100
            })
    
    def _should_run_daily_missions(self, current_time: datetime) -> bool:
        """检查是否应该运行日常任务。"""
        # 简单的时间检查逻辑
        target_time = datetime.strptime(self.config.daily_mission_time, "%H:%M").time()
        current_time_only = current_time.time()
        
        # 检查是否在目标时间的5分钟内
        time_diff = abs((current_time_only.hour * 60 + current_time_only.minute) - 
                       (target_time.hour * 60 + target_time.minute))
        
        return time_diff <= 5
    
    def _should_run_resource_farming(self, current_time: datetime) -> bool:
        """检查是否应该运行资源刷取。"""
        # 简单逻辑：每2小时运行一次
        return current_time.minute < 5 and current_time.hour % 2 == 0
    
    async def _monitor_loop(self):
        """监控循环。"""
        self.logger.info("监控器已启动")
        
        while not self._shutdown_event.is_set():
            try:
                await self._update_status()
                await self._check_system_health()
                await asyncio.sleep(30)  # 每30秒检查一次
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"监控循环错误: {e}")
                await asyncio.sleep(30)
        
        self.logger.info("监控器已停止")
    
    async def _update_status(self):
        """更新状态信息。"""
        if self.status.start_time:
            self.status.uptime = datetime.now() - self.status.start_time
        
        # 更新任务统计
        if self.task_manager:
            stats = self.task_manager.get_statistics()
            self.status.total_tasks_executed = stats.get('total_tasks', 0)
            self.status.successful_tasks = stats.get('completed_tasks', 0)
            self.status.failed_tasks = stats.get('failed_tasks', 0)
        
        # 更新错误统计
        if self.error_handler:
            error_stats = self.error_handler.get_error_statistics()
            self.status.total_errors = error_stats.get('total_errors', 0)
            self.status.recovered_errors = error_stats.get('resolved_errors', 0)
    
    async def _check_system_health(self):
        """检查系统健康状态。"""
        # 检查游戏连接
        if self.game_operator and not await self.game_operator.is_game_running():
            await self.event_bus.emit('game_disconnected', {})
        
        # 检查错误率
        if self.status.total_tasks_executed > 0:
            error_rate = self.status.failed_tasks / self.status.total_tasks_executed
            if error_rate > 0.5:  # 错误率超过50%
                await self.event_bus.emit('high_error_rate', {
                    'error_rate': error_rate,
                    'total_tasks': self.status.total_tasks_executed,
                    'failed_tasks': self.status.failed_tasks
                })
    
    # 事件处理器
    async def _on_task_started(self, event_data: Dict[str, Any]):
        """任务开始事件处理。"""
        task_info = event_data.get('task_info', {})
        self.status.current_task = task_info.get('task_type')
        self.logger.debug(f"任务开始: {self.status.current_task}")
    
    async def _on_task_completed(self, event_data: Dict[str, Any]):
        """任务完成事件处理。"""
        self.status.current_task = None
        self.logger.debug("任务完成")
    
    async def _on_task_failed(self, event_data: Dict[str, Any]):
        """任务失败事件处理。"""
        self.status.current_task = None
        error_info = event_data.get('error_info')
        self.logger.warning(f"任务失败: {error_info}")
    
    async def _on_error_occurred(self, event_data: Dict[str, Any]):
        """错误发生事件处理。"""
        error_info = event_data.get('error_info')
        if error_info and error_info.severity.value == 'critical':
            if self.config.auto_restart_on_critical_error:
                self.logger.warning("检测到严重错误，准备重启引擎")
                asyncio.create_task(self._restart_engine())
    
    async def _on_error_recovered(self, event_data: Dict[str, Any]):
        """错误恢复事件处理。"""
        self.logger.info("错误已恢复")
    
    async def _on_system_overload(self, event_data: Dict[str, Any]):
        """系统过载事件处理。"""
        self.logger.warning("系统过载，暂停新任务")
        if self.task_manager:
            await self.task_manager.pause()
    
    async def _on_game_disconnected(self, event_data: Dict[str, Any]):
        """游戏断开连接事件处理。"""
        self.logger.error("游戏连接断开")
        # 尝试重新连接
        if self.game_operator:
            await self.game_operator.reconnect()
    
    async def _restart_engine(self):
        """重启引擎。"""
        self.logger.info("正在重启自动化引擎...")
        await self.stop()
        await asyncio.sleep(5)  # 等待5秒
        await self.start()
    
    def get_status(self) -> EngineStatus:
        """获取引擎状态。"""
        return self.status
    
    def get_config(self) -> EngineConfig:
        """获取引擎配置。"""
        return self.config
    
    async def update_config(self, new_config: EngineConfig):
        """更新引擎配置。"""
        old_config = self.config
        self.config = new_config
        
        self.logger.info("引擎配置已更新")
        await self.event_bus.emit('config_updated', {
            'old_config': old_config,
            'new_config': new_config
        })
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计。"""
        return {
            'uptime': self.status.uptime.total_seconds(),
            'total_tasks': self.status.total_tasks_executed,
            'success_rate': (self.status.successful_tasks / max(self.status.total_tasks_executed, 1)) * 100,
            'error_rate': (self.status.failed_tasks / max(self.status.total_tasks_executed, 1)) * 100,
            'recovery_rate': (self.status.recovered_errors / max(self.status.total_errors, 1)) * 100,
            'current_state': self.status.state.value,
            'active_runners': self.status.active_runners
        }