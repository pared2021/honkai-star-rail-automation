"""智能等待机制模块.

提供基于UI状态的智能等待和重试功能。
"""

import asyncio
import time
from typing import Callable, Optional, Any, Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

from ..core.game_detector import GameDetector, SceneType
from ..core.game_operator import GameOperator
from ..core.template_matcher import TemplateMatcher, MatchResult
from ..exceptions.automation_exceptions import WaitTimeoutError, GameDetectionError


class WaitConditionType(Enum):
    """等待条件类型枚举."""
    ELEMENT_APPEAR = "element_appear"  # 元素出现
    ELEMENT_DISAPPEAR = "element_disappear"  # 元素消失
    SCENE_CHANGE = "scene_change"  # 场景变化
    CUSTOM_CONDITION = "custom_condition"  # 自定义条件
    MULTIPLE_ELEMENTS = "multiple_elements"  # 多个元素
    ELEMENT_STABLE = "element_stable"  # 元素稳定


@dataclass
class WaitCondition:
    """等待条件数据类."""
    condition_type: WaitConditionType
    target: Optional[str] = None  # 目标元素或场景
    timeout: float = 30.0  # 超时时间（秒）
    check_interval: float = 0.5  # 检查间隔（秒）
    threshold: float = 0.8  # 匹配阈值
    stable_duration: float = 1.0  # 稳定持续时间
    custom_checker: Optional[Callable[[], bool]] = None  # 自定义检查函数
    metadata: Optional[Dict[str, Any]] = None  # 额外元数据


@dataclass
class WaitResult:
    """等待结果数据类."""
    success: bool
    elapsed_time: float
    condition_met: bool = False
    final_state: Optional[Any] = None
    error_message: Optional[str] = None
    match_results: Optional[List[MatchResult]] = None


class SmartWaiter:
    """智能等待器.
    
    提供基于UI状态的智能等待功能，支持多种等待条件和重试策略。
    """
    
    def __init__(self, 
                 game_detector: GameDetector,
                 game_operator: GameOperator,
                 template_matcher: TemplateMatcher):
        """初始化智能等待器.
        
        Args:
            game_detector: 游戏检测器
            game_operator: 游戏操作器
            template_matcher: 模板匹配器
        """
        self.game_detector = game_detector
        self.game_operator = game_operator
        self.template_matcher = template_matcher
        self.logger = logging.getLogger(__name__)
        
        # 等待历史记录
        self._wait_history: List[Dict[str, Any]] = []
        
        # 默认配置
        self.default_timeout = 30.0
        self.default_check_interval = 0.5
        self.default_threshold = 0.8
    
    async def wait_for_condition(self, condition: WaitCondition) -> WaitResult:
        """等待指定条件满足.
        
        Args:
            condition: 等待条件
            
        Returns:
            WaitResult: 等待结果
        """
        start_time = time.time()
        self.logger.info(f"开始等待条件: {condition.condition_type.value}")
        
        try:
            # 根据条件类型选择等待策略
            if condition.condition_type == WaitConditionType.ELEMENT_APPEAR:
                result = await self._wait_for_element_appear(condition)
            elif condition.condition_type == WaitConditionType.ELEMENT_DISAPPEAR:
                result = await self._wait_for_element_disappear(condition)
            elif condition.condition_type == WaitConditionType.SCENE_CHANGE:
                result = await self._wait_for_scene_change(condition)
            elif condition.condition_type == WaitConditionType.CUSTOM_CONDITION:
                result = await self._wait_for_custom_condition(condition)
            elif condition.condition_type == WaitConditionType.MULTIPLE_ELEMENTS:
                result = await self._wait_for_multiple_elements(condition)
            elif condition.condition_type == WaitConditionType.ELEMENT_STABLE:
                result = await self._wait_for_element_stable(condition)
            else:
                raise ValueError(f"不支持的等待条件类型: {condition.condition_type}")
            
            elapsed_time = time.time() - start_time
            result.elapsed_time = elapsed_time
            
            # 记录等待历史
            self._record_wait_history(condition, result)
            
            if result.success:
                self.logger.info(f"等待条件满足，耗时: {elapsed_time:.2f}秒")
            else:
                self.logger.warning(f"等待条件未满足，耗时: {elapsed_time:.2f}秒")
            
            return result
            
        except Exception as e:
            elapsed_time = time.time() - start_time
            error_result = WaitResult(
                success=False,
                elapsed_time=elapsed_time,
                error_message=str(e)
            )
            self._record_wait_history(condition, error_result)
            self.logger.error(f"等待过程中发生错误: {e}")
            return error_result
    
    async def _wait_for_element_appear(self, condition: WaitCondition) -> WaitResult:
        """等待元素出现."""
        if not condition.target:
            return WaitResult(
                success=False,
                elapsed_time=0,
                error_message="未指定目标元素"
            )
        
        start_time = time.time()
        
        while time.time() - start_time < condition.timeout:
            try:
                # 获取当前截图
                screenshot_result = self.game_operator.take_screenshot()
                if not screenshot_result.success or screenshot_result.screenshot is None:
                    await asyncio.sleep(condition.check_interval)
                    continue
                
                # 匹配模板
                match_result = self.template_matcher.match_template(
                    screenshot_result.screenshot,
                    condition.target,
                    threshold=condition.threshold
                )
                
                if match_result.found:
                    return WaitResult(
                        success=True,
                        elapsed_time=time.time() - start_time,
                        condition_met=True,
                        final_state=match_result.position,
                        match_results=[match_result]
                    )
                
                await asyncio.sleep(condition.check_interval)
                
            except Exception as e:
                self.logger.warning(f"检查元素出现时发生错误: {e}")
                await asyncio.sleep(condition.check_interval)
        
        return WaitResult(
            success=False,
            elapsed_time=time.time() - start_time,
            error_message=f"等待元素 {condition.target} 出现超时"
        )
    
    async def _wait_for_element_disappear(self, condition: WaitCondition) -> WaitResult:
        """等待元素消失."""
        if not condition.target:
            return WaitResult(
                success=False,
                elapsed_time=0,
                error_message="未指定目标元素"
            )
        
        start_time = time.time()
        
        while time.time() - start_time < condition.timeout:
            try:
                # 获取当前截图
                screenshot_result = self.game_operator.take_screenshot()
                if not screenshot_result.success or screenshot_result.screenshot is None:
                    await asyncio.sleep(condition.check_interval)
                    continue
                
                # 匹配模板
                match_result = self.template_matcher.match_template(
                    screenshot_result.screenshot,
                    condition.target,
                    threshold=condition.threshold
                )
                
                if not match_result.found:
                    return WaitResult(
                        success=True,
                        elapsed_time=time.time() - start_time,
                        condition_met=True,
                        final_state=None,
                        match_results=[match_result]
                    )
                
                await asyncio.sleep(condition.check_interval)
                
            except Exception as e:
                self.logger.warning(f"检查元素消失时发生错误: {e}")
                await asyncio.sleep(condition.check_interval)
        
        return WaitResult(
            success=False,
            elapsed_time=time.time() - start_time,
            error_message=f"等待元素 {condition.target} 消失超时"
        )
    
    async def _wait_for_scene_change(self, condition: WaitCondition) -> WaitResult:
        """等待场景变化."""
        if not condition.target:
            return WaitResult(
                success=False,
                elapsed_time=0,
                error_message="未指定目标场景"
            )
        
        try:
            target_scene = SceneType(condition.target)
        except ValueError:
            return WaitResult(
                success=False,
                elapsed_time=0,
                error_message=f"无效的场景类型: {condition.target}"
            )
        
        start_time = time.time()
        
        while time.time() - start_time < condition.timeout:
            try:
                # 检测当前场景
                current_scene = self.game_detector.detect_current_scene()
                
                if current_scene == target_scene:
                    return WaitResult(
                        success=True,
                        elapsed_time=time.time() - start_time,
                        condition_met=True,
                        final_state=current_scene
                    )
                
                await asyncio.sleep(condition.check_interval)
                
            except Exception as e:
                self.logger.warning(f"检查场景变化时发生错误: {e}")
                await asyncio.sleep(condition.check_interval)
        
        return WaitResult(
            success=False,
            elapsed_time=time.time() - start_time,
            error_message=f"等待场景变化到 {target_scene} 超时"
        )
    
    async def _wait_for_custom_condition(self, condition: WaitCondition) -> WaitResult:
        """等待自定义条件."""
        if not condition.custom_checker:
            return WaitResult(
                success=False,
                elapsed_time=0,
                error_message="未提供自定义检查函数"
            )
        
        start_time = time.time()
        
        while time.time() - start_time < condition.timeout:
            try:
                # 执行自定义检查
                if condition.custom_checker():
                    return WaitResult(
                        success=True,
                        elapsed_time=time.time() - start_time,
                        condition_met=True
                    )
                
                await asyncio.sleep(condition.check_interval)
                
            except Exception as e:
                self.logger.warning(f"执行自定义检查时发生错误: {e}")
                await asyncio.sleep(condition.check_interval)
        
        return WaitResult(
            success=False,
            elapsed_time=time.time() - start_time,
            error_message="等待自定义条件超时"
        )
    
    async def _wait_for_multiple_elements(self, condition: WaitCondition) -> WaitResult:
        """等待多个元素."""
        if not condition.metadata or 'elements' not in condition.metadata:
            return WaitResult(
                success=False,
                elapsed_time=0,
                error_message="未指定要等待的元素列表"
            )
        
        elements = condition.metadata['elements']
        require_all = condition.metadata.get('require_all', True)
        
        start_time = time.time()
        
        while time.time() - start_time < condition.timeout:
            try:
                # 获取当前截图
                screenshot_result = self.game_operator.take_screenshot()
                if not screenshot_result.success or screenshot_result.screenshot is None:
                    await asyncio.sleep(condition.check_interval)
                    continue
                
                # 匹配所有元素
                match_results = self.template_matcher.match_multiple_templates(
                    screenshot_result.screenshot,
                    elements,
                    threshold=condition.threshold
                )
                
                found_elements = [r for r in match_results if r.found]
                
                if require_all:
                    # 需要所有元素都找到
                    if len(found_elements) == len(elements):
                        return WaitResult(
                            success=True,
                            elapsed_time=time.time() - start_time,
                            condition_met=True,
                            match_results=match_results
                        )
                else:
                    # 只需要找到任意一个元素
                    if found_elements:
                        return WaitResult(
                            success=True,
                            elapsed_time=time.time() - start_time,
                            condition_met=True,
                            match_results=match_results
                        )
                
                await asyncio.sleep(condition.check_interval)
                
            except Exception as e:
                self.logger.warning(f"检查多个元素时发生错误: {e}")
                await asyncio.sleep(condition.check_interval)
        
        return WaitResult(
            success=False,
            elapsed_time=time.time() - start_time,
            error_message="等待多个元素超时"
        )
    
    async def _wait_for_element_stable(self, condition: WaitCondition) -> WaitResult:
        """等待元素稳定."""
        if not condition.target:
            return WaitResult(
                success=False,
                elapsed_time=0,
                error_message="未指定目标元素"
            )
        
        start_time = time.time()
        stable_start_time = None
        last_position = None
        
        while time.time() - start_time < condition.timeout:
            try:
                # 获取当前截图
                screenshot_result = self.game_operator.take_screenshot()
                if not screenshot_result.success or screenshot_result.screenshot is None:
                    stable_start_time = None
                    await asyncio.sleep(condition.check_interval)
                    continue
                
                # 匹配模板
                match_result = self.template_matcher.match_template(
                    screenshot_result.screenshot,
                    condition.target,
                    threshold=condition.threshold
                )
                
                if match_result.found:
                    current_position = match_result.position
                    
                    # 检查位置是否稳定
                    if last_position is None:
                        last_position = current_position
                        stable_start_time = time.time()
                    elif abs(current_position[0] - last_position[0]) <= 5 and \
                         abs(current_position[1] - last_position[1]) <= 5:
                        # 位置稳定
                        if stable_start_time and \
                           time.time() - stable_start_time >= condition.stable_duration:
                            return WaitResult(
                                success=True,
                                elapsed_time=time.time() - start_time,
                                condition_met=True,
                                final_state=current_position,
                                match_results=[match_result]
                            )
                    else:
                        # 位置变化，重新开始计时
                        last_position = current_position
                        stable_start_time = time.time()
                else:
                    # 元素未找到，重置状态
                    stable_start_time = None
                    last_position = None
                
                await asyncio.sleep(condition.check_interval)
                
            except Exception as e:
                self.logger.warning(f"检查元素稳定性时发生错误: {e}")
                stable_start_time = None
                await asyncio.sleep(condition.check_interval)
        
        return WaitResult(
            success=False,
            elapsed_time=time.time() - start_time,
            error_message=f"等待元素 {condition.target} 稳定超时"
        )
    
    def _record_wait_history(self, condition: WaitCondition, result: WaitResult):
        """记录等待历史."""
        history_entry = {
            'timestamp': time.time(),
            'condition_type': condition.condition_type.value,
            'target': condition.target,
            'timeout': condition.timeout,
            'success': result.success,
            'elapsed_time': result.elapsed_time,
            'condition_met': result.condition_met,
            'error_message': result.error_message
        }
        
        self._wait_history.append(history_entry)
        
        # 保持历史记录数量在合理范围内
        if len(self._wait_history) > 100:
            self._wait_history = self._wait_history[-50:]
    
    async def wait_for_any(self, conditions: List[WaitCondition]) -> Tuple[int, WaitResult]:
        """等待任意一个条件满足.
        
        Args:
            conditions: 条件列表
            
        Returns:
            Tuple[int, WaitResult]: (满足条件的索引, 等待结果)
        """
        tasks = []
        
        for i, condition in enumerate(conditions):
            task = asyncio.create_task(self.wait_for_condition(condition))
            tasks.append((i, task))
        
        try:
            # 等待任意一个任务完成
            done, pending = await asyncio.wait(
                [task for _, task in tasks],
                return_when=asyncio.FIRST_COMPLETED
            )
            
            # 取消其他任务
            for task in pending:
                task.cancel()
            
            # 获取完成的任务结果
            completed_task = done.pop()
            result = await completed_task
            
            # 找到对应的索引
            for i, task in tasks:
                if task == completed_task:
                    return i, result
            
            return -1, result
            
        except Exception as e:
            # 取消所有任务
            for _, task in tasks:
                if not task.done():
                    task.cancel()
            
            return -1, WaitResult(
                success=False,
                elapsed_time=0,
                error_message=f"等待过程中发生错误: {e}"
            )
    
    def get_wait_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取等待历史记录.
        
        Args:
            limit: 返回记录数量限制
            
        Returns:
            List[Dict[str, Any]]: 历史记录列表
        """
        return self._wait_history[-limit:] if self._wait_history else []
    
    def clear_wait_history(self):
        """清空等待历史记录."""
        self._wait_history.clear()
        self.logger.debug("等待历史记录已清空")
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取等待统计信息.
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        if not self._wait_history:
            return {
                'total_waits': 0,
                'success_rate': 0.0,
                'average_wait_time': 0.0,
                'condition_types': {}
            }
        
        total_waits = len(self._wait_history)
        successful_waits = sum(1 for h in self._wait_history if h['success'])
        success_rate = successful_waits / total_waits
        
        total_time = sum(h['elapsed_time'] for h in self._wait_history)
        average_wait_time = total_time / total_waits
        
        # 按条件类型统计
        condition_types = {}
        for history in self._wait_history:
            condition_type = history['condition_type']
            if condition_type not in condition_types:
                condition_types[condition_type] = {
                    'count': 0,
                    'success_count': 0,
                    'total_time': 0.0
                }
            
            condition_types[condition_type]['count'] += 1
            if history['success']:
                condition_types[condition_type]['success_count'] += 1
            condition_types[condition_type]['total_time'] += history['elapsed_time']
        
        # 计算每种条件类型的成功率和平均时间
        for stats in condition_types.values():
            stats['success_rate'] = stats['success_count'] / stats['count']
            stats['average_time'] = stats['total_time'] / stats['count']
        
        return {
            'total_waits': total_waits,
            'success_rate': success_rate,
            'average_wait_time': average_wait_time,
            'condition_types': condition_types
        }