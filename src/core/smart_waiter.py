"""智能等待机制模块。

提供智能等待功能，包括动态等待时间调整、多种等待条件、超时处理等。
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Callable, List, Union
from dataclasses import dataclass
from enum import Enum

from ..config.logger import get_logger
from .types import WaitCondition
from .game_operator import GameOperator


class WaitStrategy(Enum):
    """等待策略枚举。"""
    FIXED = "fixed"  # 固定间隔
    EXPONENTIAL = "exponential"  # 指数退避
    LINEAR = "linear"  # 线性增长
    ADAPTIVE = "adaptive"  # 自适应


class WaitResult(Enum):
    """等待结果枚举。"""
    SUCCESS = "success"  # 成功
    TIMEOUT = "timeout"  # 超时
    ERROR = "error"  # 错误
    CANCELLED = "cancelled"  # 取消


@dataclass
class WaitConfig:
    """等待配置。"""
    initial_delay: float = 0.5  # 初始延迟（秒）
    max_delay: float = 5.0  # 最大延迟（秒）
    timeout: float = 30.0  # 超时时间（秒）
    strategy: WaitStrategy = WaitStrategy.EXPONENTIAL  # 等待策略
    backoff_factor: float = 1.5  # 退避因子
    jitter: bool = True  # 是否添加随机抖动
    max_attempts: int = 0  # 最大尝试次数（0表示无限制）


@dataclass
class WaitContext:
    """等待上下文。"""
    condition_name: str
    start_time: datetime
    attempt_count: int = 0
    last_check_time: Optional[datetime] = None
    last_delay: float = 0.0
    total_wait_time: float = 0.0
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class SmartWaiter:
    """智能等待器。
    
    提供多种等待策略和条件检查功能。
    """
    
    def __init__(self, default_config: Optional[WaitConfig] = None):
        """初始化智能等待器。
        
        Args:
            default_config: 默认等待配置
        """
        self.logger = get_logger(__name__)
        self.default_config = default_config or WaitConfig()
        
        # 等待历史记录
        self.wait_history: List[WaitContext] = []
        
        # 性能统计
        self.stats = {
            'total_waits': 0,
            'successful_waits': 0,
            'timeout_waits': 0,
            'error_waits': 0,
            'average_wait_time': 0.0,
            'condition_success_rates': {}
        }
        
        self.logger.info("智能等待器初始化完成")
    
    async def wait_for_condition(
        self,
        condition_func: Callable[[], Union[bool, Any]],
        condition_name: str = "custom_condition",
        config: Optional[WaitConfig] = None,
        context_data: Optional[Dict[str, Any]] = None
    ) -> tuple[WaitResult, Any]:
        """等待条件满足。
        
        Args:
            condition_func: 条件检查函数
            condition_name: 条件名称
            config: 等待配置
            context_data: 上下文数据
            
        Returns:
            (等待结果, 条件函数返回值)
        """
        config = config or self.default_config
        context = WaitContext(
            condition_name=condition_name,
            start_time=datetime.now(),
            metadata=context_data or {}
        )
        
        self.logger.debug(f"开始等待条件: {condition_name}")
        
        try:
            result, value = await self._execute_wait(condition_func, config, context)
            
            # 记录等待历史
            self.wait_history.append(context)
            
            # 更新统计
            self._update_statistics(context, result)
            
            self.logger.debug(f"等待完成: {condition_name} - {result.value}")
            return result, value
            
        except Exception as e:
            self.logger.error(f"等待异常: {condition_name} - {e}")
            context.metadata['error'] = str(e)
            self.wait_history.append(context)
            self._update_statistics(context, WaitResult.ERROR)
            return WaitResult.ERROR, None
    
    async def _execute_wait(
        self,
        condition_func: Callable,
        config: WaitConfig,
        context: WaitContext
    ) -> tuple[WaitResult, Any]:
        """执行等待逻辑。"""
        start_time = time.time()
        current_delay = config.initial_delay
        
        while True:
            # 检查超时
            elapsed_time = time.time() - start_time
            if elapsed_time >= config.timeout:
                context.total_wait_time = elapsed_time
                return WaitResult.TIMEOUT, None
            
            # 检查最大尝试次数
            if config.max_attempts > 0 and context.attempt_count >= config.max_attempts:
                context.total_wait_time = elapsed_time
                return WaitResult.TIMEOUT, None
            
            # 执行条件检查
            context.attempt_count += 1
            context.last_check_time = datetime.now()
            
            try:
                # 支持同步和异步条件函数
                if asyncio.iscoroutinefunction(condition_func):
                    result = await condition_func()
                else:
                    result = condition_func()
                
                # 如果条件满足
                if result:
                    context.total_wait_time = elapsed_time
                    return WaitResult.SUCCESS, result
                
            except Exception as e:
                self.logger.warning(f"条件检查异常: {e}")
                # 继续等待，不因为单次检查失败而终止
            
            # 计算下次等待时间
            next_delay = self._calculate_next_delay(current_delay, config, context)
            
            # 确保不超过剩余时间
            remaining_time = config.timeout - elapsed_time
            actual_delay = min(next_delay, remaining_time)
            
            if actual_delay <= 0:
                context.total_wait_time = elapsed_time
                return WaitResult.TIMEOUT, None
            
            # 等待
            context.last_delay = actual_delay
            await asyncio.sleep(actual_delay)
            current_delay = next_delay
    
    def _calculate_next_delay(self, current_delay: float, config: WaitConfig, context: WaitContext) -> float:
        """计算下次等待延迟。"""
        if config.strategy == WaitStrategy.FIXED:
            next_delay = config.initial_delay
        
        elif config.strategy == WaitStrategy.EXPONENTIAL:
            next_delay = current_delay * config.backoff_factor
        
        elif config.strategy == WaitStrategy.LINEAR:
            next_delay = config.initial_delay + (context.attempt_count * 0.1)
        
        elif config.strategy == WaitStrategy.ADAPTIVE:
            # 自适应策略：根据历史成功率调整
            success_rate = self._get_condition_success_rate(context.condition_name)
            if success_rate > 0.8:
                next_delay = current_delay * 0.8  # 成功率高，减少等待
            elif success_rate < 0.3:
                next_delay = current_delay * 1.5  # 成功率低，增加等待
            else:
                next_delay = current_delay
        
        else:
            next_delay = current_delay
        
        # 限制在最大延迟范围内
        next_delay = min(next_delay, config.max_delay)
        
        # 添加随机抖动
        if config.jitter:
            import random
            jitter_factor = 0.1  # 10%的抖动
            jitter = random.uniform(-jitter_factor, jitter_factor)
            next_delay = next_delay * (1 + jitter)
        
        return max(0.1, next_delay)  # 最小延迟0.1秒
    
    def _get_condition_success_rate(self, condition_name: str) -> float:
        """获取条件成功率。"""
        return self.stats['condition_success_rates'].get(condition_name, 0.5)
    
    def _update_statistics(self, context: WaitContext, result: WaitResult):
        """更新统计信息。"""
        self.stats['total_waits'] += 1
        
        if result == WaitResult.SUCCESS:
            self.stats['successful_waits'] += 1
        elif result == WaitResult.TIMEOUT:
            self.stats['timeout_waits'] += 1
        elif result == WaitResult.ERROR:
            self.stats['error_waits'] += 1
        
        # 更新平均等待时间
        total_time = sum(ctx.total_wait_time for ctx in self.wait_history)
        self.stats['average_wait_time'] = total_time / len(self.wait_history)
        
        # 更新条件成功率
        condition_name = context.condition_name
        if condition_name not in self.stats['condition_success_rates']:
            self.stats['condition_success_rates'][condition_name] = {'success': 0, 'total': 0}
        
        condition_stats = self.stats['condition_success_rates'][condition_name]
        condition_stats['total'] += 1
        if result == WaitResult.SUCCESS:
            condition_stats['success'] += 1
        
        # 计算成功率
        success_rate = condition_stats['success'] / condition_stats['total']
        self.stats['condition_success_rates'][condition_name] = success_rate
    
    async def wait_for_ui_element(
        self,
        element_name: str,
        game_detector,
        appear: bool = True,
        config: Optional[WaitConfig] = None
    ) -> tuple[WaitResult, Any]:
        """等待UI元素出现或消失。
        
        Args:
            element_name: 元素名称
            game_detector: 游戏检测器
            appear: True等待出现，False等待消失
            config: 等待配置
            
        Returns:
            (等待结果, UI元素或None)
        """
        condition_name = f"ui_element_{'appear' if appear else 'disappear'}_{element_name}"
        
        async def check_condition():
            elements = game_detector.detect_ui_elements([element_name])
            if appear:
                return elements[0] if elements else None
            else:
                return not bool(elements)
        
        return await self.wait_for_condition(
            check_condition,
            condition_name,
            config,
            {'element_name': element_name, 'appear': appear}
        )
    
    async def wait_for_scene_change(
        self,
        target_scene: Optional[str],
        game_detector,
        config: Optional[WaitConfig] = None
    ) -> tuple[WaitResult, Any]:
        """等待场景切换。
        
        Args:
            target_scene: 目标场景名称，None表示任意场景变化
            game_detector: 游戏检测器
            config: 等待配置
            
        Returns:
            (等待结果, 当前场景)
        """
        initial_scene = game_detector.detect_scene()
        condition_name = f"scene_change_to_{target_scene or 'any'}"
        
        def check_condition():
            current_scene = game_detector.detect_scene()
            if target_scene:
                return current_scene and current_scene.value == target_scene
            else:
                return current_scene != initial_scene
        
        return await self.wait_for_condition(
            check_condition,
            condition_name,
            config,
            {'target_scene': target_scene, 'initial_scene': initial_scene}
        )
    
    async def wait_for_multiple_conditions(
        self,
        conditions: List[tuple[Callable, str]],
        require_all: bool = False,
        config: Optional[WaitConfig] = None
    ) -> tuple[WaitResult, Dict[str, Any]]:
        """等待多个条件。
        
        Args:
            conditions: 条件列表，每个元素为(条件函数, 条件名称)
            require_all: True表示需要所有条件都满足，False表示任一条件满足即可
            config: 等待配置
            
        Returns:
            (等待结果, 条件结果字典)
        """
        condition_name = f"multiple_conditions_{'all' if require_all else 'any'}"
        
        async def check_conditions():
            results = {}
            satisfied_count = 0
            
            for condition_func, name in conditions:
                try:
                    if asyncio.iscoroutinefunction(condition_func):
                        result = await condition_func()
                    else:
                        result = condition_func()
                    
                    results[name] = result
                    if result:
                        satisfied_count += 1
                        
                        # 如果只需要任一条件满足，立即返回
                        if not require_all:
                            return results
                            
                except Exception as e:
                    self.logger.warning(f"条件检查异常 {name}: {e}")
                    results[name] = False
            
            # 检查是否满足要求
            if require_all:
                return results if satisfied_count == len(conditions) else None
            else:
                return results if satisfied_count > 0 else None
        
        return await self.wait_for_condition(
            check_conditions,
            condition_name,
            config,
            {'require_all': require_all, 'condition_count': len(conditions)}
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取等待统计信息。"""
        return self.stats.copy()
    
    def get_wait_history(self, limit: int = 100) -> List[WaitContext]:
        """获取等待历史。"""
        return self.wait_history[-limit:]
    
    def clear_history(self):
        """清空等待历史。"""
        self.wait_history.clear()
        self.stats = {
            'total_waits': 0,
            'successful_waits': 0,
            'timeout_waits': 0,
            'error_waits': 0,
            'average_wait_time': 0.0,
            'condition_success_rates': {}
        }
        
        self.logger.info("等待历史已清空")


class ElementWaitCondition:
    """元素等待条件类。"""
    
    def __init__(self, element_name: str, timeout: float = 30.0, check_interval: float = 0.5):
        self.element_name = element_name
        self.timeout = timeout
        self.check_interval = check_interval
    
    async def check(self, game_operator: GameOperator) -> bool:
        """检查元素是否存在。"""
        try:
            element = game_operator.find_element(self.element_name)
            return element is not None
        except Exception:
            return False


class SceneWaitCondition:
    """场景等待条件类。"""
    
    def __init__(self, expected_scene: str, timeout: float = 30.0, check_interval: float = 0.5):
        self.expected_scene = expected_scene
        self.timeout = timeout
        self.check_interval = check_interval
    
    async def check(self, game_operator: GameOperator) -> bool:
        """检查当前场景是否匹配。"""
        try:
            current_scene = game_operator.get_current_scene()
            return current_scene == self.expected_scene
        except Exception:
            return False


class CustomWaitCondition:
    """自定义等待条件类。"""
    
    def __init__(self, check_function: Callable, timeout: float = 30.0, 
                 check_interval: float = 0.5, description: str = "Custom condition"):
        self.check_function = check_function
        self.timeout = timeout
        self.check_interval = check_interval
        self.description = description
    
    async def check(self, game_operator: GameOperator) -> bool:
        """执行自定义检查函数。"""
        try:
            if asyncio.iscoroutinefunction(self.check_function):
                return await self.check_function(game_operator)
            else:
                return self.check_function(game_operator)
        except Exception:
            return False


class TimeoutWaitStrategy:
    """超时等待策略类。"""
    
    async def wait(self, condition, game_operator: GameOperator):
        """执行等待逻辑。"""
        start_time = time.time()
        
        while True:
            elapsed_time = time.time() - start_time
            
            # 检查超时
            if elapsed_time >= condition.timeout:
                return WaitResultData(
                    success=False,
                    elapsed_time=elapsed_time,
                    message="Wait timeout"
                )
            
            # 检查条件
            if await condition.check(game_operator):
                return WaitResultData(
                    success=True,
                    elapsed_time=elapsed_time,
                    message="Wait completed successfully"
                )
            
            # 等待检查间隔
            await asyncio.sleep(condition.check_interval)


class ExponentialBackoffStrategy:
    """指数退避等待策略类。"""
    
    def __init__(self, initial_delay: float = 0.1, max_delay: float = 1.0, backoff_factor: float = 2.0):
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
    
    async def wait(self, condition, game_operator: GameOperator):
        """执行指数退避等待逻辑。"""
        start_time = time.time()
        current_delay = self.initial_delay
        
        while True:
            elapsed_time = time.time() - start_time
            
            # 检查超时
            if elapsed_time >= condition.timeout:
                return WaitResultData(
                    success=False,
                    elapsed_time=elapsed_time,
                    message="Wait timeout"
                )
            
            # 检查条件
            if await condition.check(game_operator):
                return WaitResultData(
                    success=True,
                    elapsed_time=elapsed_time,
                    message="Wait completed successfully"
                )
            
            # 等待当前延迟时间
            await asyncio.sleep(current_delay)
            
            # 计算下次延迟时间
            current_delay = min(current_delay * self.backoff_factor, self.max_delay)


class AdaptiveWaitStrategy:
    """自适应等待策略类。"""
    
    async def wait(self, condition, game_operator: GameOperator):
        """执行自适应等待逻辑。"""
        start_time = time.time()
        
        while True:
            elapsed_time = time.time() - start_time
            
            # 检查超时
            if elapsed_time >= condition.timeout:
                return WaitResultData(
                    success=False,
                    elapsed_time=elapsed_time,
                    message="Wait timeout"
                )
            
            # 检查条件
            if await condition.check(game_operator):
                return WaitResultData(
                    success=True,
                    elapsed_time=elapsed_time,
                    message="Wait completed successfully"
                )
            
            # 自适应延迟调整
            adaptive_delay = min(0.5 + elapsed_time * 0.1, 2.0)
            await asyncio.sleep(adaptive_delay)


@dataclass
class WaitResultData:
    """等待结果数据类。"""
    success: bool
    elapsed_time: float
    message: str