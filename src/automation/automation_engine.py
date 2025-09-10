"""自动化执行引擎模块.

提供智能任务调度、执行监控和错误恢复功能。
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union
from concurrent.futures import ThreadPoolExecutor, Future
import threading

from src.core.game_detector import GameDetector, SceneType
from src.core.game_operator import GameOperator, OperationResult
from src.core.task_manager import TaskManager, TaskStatus, TaskType, TaskPriority
from src.core.error_handler import ErrorHandler
from src.exceptions import AutomationError, GameDetectionError
from src.config.config_manager import ConfigManager


class ExecutionStrategy(Enum):
    """执行策略枚举."""
    IMMEDIATE = "immediate"  # 立即执行
    SCHEDULED = "scheduled"  # 定时执行
    CONDITIONAL = "conditional"  # 条件执行
    ADAPTIVE = "adaptive"  # 自适应执行


class WaitStrategy(Enum):
    """等待策略枚举."""
    FIXED_DELAY = "fixed_delay"  # 固定延迟
    EXPONENTIAL_BACKOFF = "exponential_backoff"  # 指数退避
    ADAPTIVE_WAIT = "adaptive_wait"  # 自适应等待
    SCENE_BASED = "scene_based"  # 基于场景的等待


@dataclass
class ExecutionContext:
    """执行上下文."""
    task_id: str
    execution_id: str
    start_time: datetime
    current_scene: Optional[SceneType] = None
    retry_count: int = 0
    last_error: Optional[Exception] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def elapsed_time(self) -> float:
        """获取已执行时间（秒）."""
        return (datetime.now() - self.start_time).total_seconds()


@dataclass
class ExecutionConfig:
    """执行配置."""
    strategy: ExecutionStrategy = ExecutionStrategy.IMMEDIATE
    wait_strategy: WaitStrategy = WaitStrategy.ADAPTIVE_WAIT
    max_retries: int = 3
    timeout: float = 300.0  # 5分钟超时
    retry_delay: float = 2.0
    scene_requirements: List[SceneType] = field(default_factory=list)
    pre_conditions: List[Callable] = field(default_factory=list)
    post_conditions: List[Callable] = field(default_factory=list)
    enable_smart_wait: bool = True
    enable_error_recovery: bool = True


class ITaskExecutor(ABC):
    """任务执行器接口."""
    
    @abstractmethod
    async def execute(self, context: ExecutionContext) -> OperationResult:
        """执行任务.
        
        Args:
            context: 执行上下文
            
        Returns:
            执行结果
        """
        pass
    
    @abstractmethod
    def can_execute(self, context: ExecutionContext) -> bool:
        """检查是否可以执行.
        
        Args:
            context: 执行上下文
            
        Returns:
            是否可以执行
        """
        pass


class SmartWaitManager:
    """智能等待管理器."""
    
    def __init__(self, game_detector: GameDetector):
        """初始化智能等待管理器.
        
        Args:
            game_detector: 游戏检测器
        """
        self.game_detector = game_detector
        self.logger = logging.getLogger(__name__)
        self._scene_wait_times: Dict[SceneType, float] = {
            SceneType.LOADING: 5.0,
            SceneType.MAIN_MENU: 2.0,
            SceneType.GAME_PLAY: 1.0,
            SceneType.SETTINGS: 1.5,
        }
    
    async def wait_for_scene(self, target_scene: SceneType, timeout: float = 30.0) -> bool:
        """等待特定场景出现.
        
        Args:
            target_scene: 目标场景
            timeout: 超时时间
            
        Returns:
            是否成功等待到目标场景
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                current_scene = self.game_detector.detect_current_scene()
                if current_scene == target_scene:
                    return True
                
                # 根据当前场景调整等待时间
                wait_time = self._scene_wait_times.get(current_scene, 2.0)
                await asyncio.sleep(wait_time)
                
            except Exception as e:
                self.logger.warning(f"场景检测失败: {e}")
                await asyncio.sleep(1.0)
        
        return False
    
    async def smart_wait(self, strategy: WaitStrategy, base_delay: float = 1.0, 
                        retry_count: int = 0) -> None:
        """智能等待.
        
        Args:
            strategy: 等待策略
            base_delay: 基础延迟
            retry_count: 重试次数
        """
        if strategy == WaitStrategy.FIXED_DELAY:
            await asyncio.sleep(base_delay)
        elif strategy == WaitStrategy.EXPONENTIAL_BACKOFF:
            delay = base_delay * (2 ** retry_count)
            await asyncio.sleep(min(delay, 30.0))  # 最大30秒
        elif strategy == WaitStrategy.ADAPTIVE_WAIT:
            # 根据当前场景自适应等待
            try:
                current_scene = self.game_detector.detect_current_scene()
                scene_delay = self._scene_wait_times.get(current_scene, base_delay)
                await asyncio.sleep(scene_delay)
            except Exception:
                await asyncio.sleep(base_delay)
        elif strategy == WaitStrategy.SCENE_BASED:
            # 等待场景稳定
            await self._wait_for_scene_stability()
    
    async def _wait_for_scene_stability(self, stability_time: float = 2.0) -> None:
        """等待场景稳定.
        
        Args:
            stability_time: 稳定时间要求
        """
        last_scene = None
        stable_start = None
        
        while True:
            try:
                current_scene = self.game_detector.detect_current_scene()
                
                if current_scene == last_scene:
                    if stable_start is None:
                        stable_start = time.time()
                    elif time.time() - stable_start >= stability_time:
                        break
                else:
                    stable_start = None
                    last_scene = current_scene
                
                await asyncio.sleep(0.5)
                
            except Exception as e:
                self.logger.warning(f"场景稳定性检测失败: {e}")
                await asyncio.sleep(1.0)


class ErrorRecoveryManager:
    """错误恢复管理器."""
    
    def __init__(self, game_operator: GameOperator, game_detector: GameDetector):
        """初始化错误恢复管理器.
        
        Args:
            game_operator: 游戏操作器
            game_detector: 游戏检测器
        """
        self.game_operator = game_operator
        self.game_detector = game_detector
        self.logger = logging.getLogger(__name__)
        
        # 恢复策略映射
        self._recovery_strategies: Dict[type, Callable] = {
            GameDetectionError: self._recover_from_detection_error,
            TimeoutError: self._recover_from_timeout,
            Exception: self._generic_recovery
        }
    
    async def recover_from_error(self, error: Exception, context: ExecutionContext) -> bool:
        """从错误中恢复.
        
        Args:
            error: 发生的错误
            context: 执行上下文
            
        Returns:
            是否成功恢复
        """
        self.logger.info(f"尝试从错误恢复: {type(error).__name__}: {error}")
        
        # 查找合适的恢复策略
        for error_type, strategy in self._recovery_strategies.items():
            if isinstance(error, error_type):
                try:
                    return await strategy(error, context)
                except Exception as e:
                    self.logger.error(f"恢复策略执行失败: {e}")
                    break
        
        return False
    
    async def _recover_from_detection_error(self, error: GameDetectionError, 
                                          context: ExecutionContext) -> bool:
        """从游戏检测错误恢复."""
        self.logger.info("尝试重新检测游戏状态")
        
        # 等待一段时间后重新检测
        await asyncio.sleep(2.0)
        
        try:
            if self.game_detector.is_game_running():
                return True
        except Exception as e:
            self.logger.error(f"游戏状态检测失败: {e}")
        
        return False
    
    async def _recover_from_timeout(self, error: TimeoutError, 
                                  context: ExecutionContext) -> bool:
        """从超时错误恢复."""
        self.logger.info("尝试从超时错误恢复")
        
        # 检查游戏是否仍在运行
        try:
            if not self.game_detector.is_game_running():
                self.logger.error("游戏已停止运行")
                return False
            
            # 尝试返回主菜单
            await self._return_to_main_menu()
            return True
            
        except Exception as e:
            self.logger.error(f"超时恢复失败: {e}")
            return False
    
    async def _generic_recovery(self, error: Exception, 
                              context: ExecutionContext) -> bool:
        """通用错误恢复."""
        self.logger.info("执行通用错误恢复")
        
        try:
            # 截图保存错误现场
            screenshot = self.game_detector.take_screenshot()
            if screenshot is not None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                screenshot_path = f"error_screenshot_{timestamp}.png"
                # 这里可以保存截图
            
            # 等待一段时间
            await asyncio.sleep(3.0)
            
            # 检查游戏状态
            if self.game_detector.is_game_running():
                return True
                
        except Exception as e:
            self.logger.error(f"通用恢复失败: {e}")
        
        return False
    
    async def _return_to_main_menu(self) -> None:
        """尝试返回主菜单."""
        # 这里可以实现返回主菜单的逻辑
        # 例如按ESC键或点击特定按钮
        pass


class AutomationEngine:
    """自动化执行引擎."""
    
    def __init__(self, 
                 game_detector: Optional[GameDetector] = None,
                 game_operator: Optional[GameOperator] = None,
                 task_manager: Optional[TaskManager] = None,
                 config_manager: Optional[ConfigManager] = None):
        """初始化自动化执行引擎.
        
        Args:
            game_detector: 游戏检测器
            game_operator: 游戏操作器
            task_manager: 任务管理器
            config_manager: 配置管理器
        """
        self.logger = logging.getLogger(__name__)
        
        # 初始化核心组件
        self.game_detector = game_detector or GameDetector()
        self.game_operator = game_operator or GameOperator()
        self.task_manager = task_manager or TaskManager()
        self.config_manager = config_manager or ConfigManager()
        
        # 初始化错误处理器
        self.error_handler = ErrorHandler()
        
        # 初始化管理器
        self.wait_manager = SmartWaitManager(self.game_detector)
        self.recovery_manager = ErrorRecoveryManager(self.game_operator, self.game_detector)
        
        # 执行器注册表
        self._executors: Dict[str, ITaskExecutor] = {}
        
        # 执行状态
        self._running = False
        self._executor_pool = ThreadPoolExecutor(max_workers=3)
        self._active_executions: Dict[str, ExecutionContext] = {}
        
        self.logger.info("自动化执行引擎初始化完成")
    
    def register_executor(self, task_type: str, executor: ITaskExecutor) -> None:
        """注册任务执行器.
        
        Args:
            task_type: 任务类型
            executor: 执行器实例
        """
        self._executors[task_type] = executor
        self.logger.info(f"注册任务执行器: {task_type}")
    
    async def execute_task(self, task_id: str, config: Optional[ExecutionConfig] = None) -> OperationResult:
        """执行任务.
        
        Args:
            task_id: 任务ID
            config: 执行配置
            
        Returns:
            执行结果
        """
        config = config or ExecutionConfig()
        execution_id = f"{task_id}_{int(time.time())}"
        
        context = ExecutionContext(
            task_id=task_id,
            execution_id=execution_id,
            start_time=datetime.now()
        )
        
        self._active_executions[execution_id] = context
        
        try:
            return await self._execute_with_retry(context, config)
        finally:
            self._active_executions.pop(execution_id, None)
    
    async def _execute_with_retry(self, context: ExecutionContext, 
                                config: ExecutionConfig) -> OperationResult:
        """带重试的执行."""
        last_error = None
        
        for attempt in range(config.max_retries + 1):
            context.retry_count = attempt
            
            try:
                # 检查前置条件
                if not await self._check_pre_conditions(config, context):
                    raise AutomationError("前置条件检查失败")
                
                # 执行任务
                result = await self._execute_single_attempt(context, config)
                
                # 检查后置条件
                if await self._check_post_conditions(config, context):
                    return result
                else:
                    raise AutomationError("后置条件检查失败")
                    
            except Exception as e:
                last_error = e
                context.last_error = e
                
                # 使用错误处理器处理错误
                error_info = await self.error_handler.handle_error(
                    error=e,
                    task_id=context.task_id,
                    task_type="automation",
                    context={
                        "execution_id": context.execution_id,
                        "attempt": attempt + 1,
                        "max_retries": config.max_retries,
                        "elapsed_time": context.elapsed_time
                    }
                )
                
                self.logger.warning(f"执行尝试 {attempt + 1} 失败: {e}, 错误ID: {error_info.error_id}")
                
                # 尝试错误恢复
                if config.enable_error_recovery and attempt < config.max_retries:
                    # 首先尝试ErrorHandler的恢复
                    recovery_success = await self.error_handler.try_recovery(error_info)
                    
                    # 如果ErrorHandler恢复失败，尝试专用的恢复管理器
                    if not recovery_success:
                        recovery_success = await self.recovery_manager.recover_from_error(e, context)
                    
                    if recovery_success:
                        self.logger.info("错误恢复成功，继续重试")
                        await self.wait_manager.smart_wait(
                            config.wait_strategy, config.retry_delay, attempt
                        )
                        continue
                
                if attempt < config.max_retries:
                    await self.wait_manager.smart_wait(
                        config.wait_strategy, config.retry_delay, attempt
                    )
        
        # 所有重试都失败了
        return OperationResult(
            success=False,
            execution_time=context.elapsed_time,
            error_message=f"执行失败，已重试 {config.max_retries} 次: {last_error}"
        )
    
    async def _execute_single_attempt(self, context: ExecutionContext, 
                                     config: ExecutionConfig) -> OperationResult:
        """单次执行尝试."""
        # 获取任务执行器
        task_info = self.task_manager.get_task(context.task_id)
        if not task_info:
            raise AutomationError(f"任务不存在: {context.task_id}")
        
        task_type = task_info.task_type.value if hasattr(task_info.task_type, 'value') else str(task_info.task_type)
        executor = self._executors.get(task_type)
        if not executor:
            raise AutomationError(f"未找到任务执行器: {task_type}")
        
        # 检查是否可以执行
        if not executor.can_execute(context):
            raise AutomationError("执行器检查失败")
        
        # 等待场景就绪
        if config.scene_requirements:
            for scene in config.scene_requirements:
                if not await self.wait_manager.wait_for_scene(scene, config.timeout):
                    raise AutomationError(f"等待场景超时: {scene}")
        
        # 执行任务
        return await executor.execute(context)
    
    async def _check_pre_conditions(self, config: ExecutionConfig, 
                                  context: ExecutionContext) -> bool:
        """检查前置条件."""
        for condition in config.pre_conditions:
            try:
                if not await self._run_condition(condition, context):
                    return False
            except Exception as e:
                self.logger.error(f"前置条件检查失败: {e}")
                return False
        return True
    
    async def _check_post_conditions(self, config: ExecutionConfig, 
                                   context: ExecutionContext) -> bool:
        """检查后置条件."""
        for condition in config.post_conditions:
            try:
                if not await self._run_condition(condition, context):
                    return False
            except Exception as e:
                self.logger.error(f"后置条件检查失败: {e}")
                return False
        return True
    
    async def _run_condition(self, condition: Callable, context: ExecutionContext) -> bool:
        """运行条件检查."""
        if asyncio.iscoroutinefunction(condition):
            return await condition(context)
        else:
            return condition(context)
    
    def start(self) -> None:
        """启动引擎."""
        self._running = True
        self.logger.info("自动化执行引擎已启动")
    
    def stop(self) -> None:
        """停止引擎."""
        self._running = False
        self._executor_pool.shutdown(wait=True)
        self.logger.info("自动化执行引擎已停止")
    
    def get_active_executions(self) -> Dict[str, ExecutionContext]:
        """获取活动执行上下文."""
        return self._active_executions.copy()
    
    def is_running(self) -> bool:
        """检查引擎是否运行中."""
        return self._running