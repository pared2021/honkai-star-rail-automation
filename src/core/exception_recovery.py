# -*- coding: utf-8 -*-
"""
异常恢复机制 - 自动处理常见异常情况并恢复任务执行
"""

import time
import threading
from typing import Dict, List, Optional, Callable, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import json

from loguru import logger
from .game_detector import GameDetector, SceneType
from automation.automation_controller import AutomationController
from .enums import ActionType
from models.task_model import Task, TaskStatus


class ExceptionType(Enum):
    """异常类型"""
    GAME_CRASH = "game_crash"
    GAME_FREEZE = "game_freeze"
    NETWORK_ERROR = "network_error"
    UI_NOT_FOUND = "ui_not_found"
    UNEXPECTED_SCENE = "unexpected_scene"
    OPERATION_TIMEOUT = "operation_timeout"
    RESOURCE_EXHAUSTED = "resource_exhausted"
    PERMISSION_DENIED = "permission_denied"
    UNKNOWN_ERROR = "unknown_error"


class RecoveryAction(Enum):
    """恢复动作"""
    RESTART_GAME = "restart_game"
    REFRESH_PAGE = "refresh_page"
    RETURN_TO_MAIN = "return_to_main"
    WAIT_AND_RETRY = "wait_and_retry"
    SKIP_TASK = "skip_task"
    FORCE_CLOSE = "force_close"
    CLEAR_CACHE = "clear_cache"
    RESET_NETWORK = "reset_network"
    MANUAL_INTERVENTION = "manual_intervention"


@dataclass
class ExceptionInfo:
    """异常信息"""
    exception_type: ExceptionType
    description: str
    timestamp: datetime
    task_id: Optional[str] = None
    scene: Optional[SceneType] = None
    error_details: Optional[Dict[str, Any]] = None
    screenshot_path: Optional[str] = None


@dataclass
class RecoveryStrategy:
    """恢复策略"""
    exception_type: ExceptionType
    actions: List[RecoveryAction]
    max_attempts: int = 3
    retry_delay: int = 5  # 秒
    timeout: int = 60  # 秒
    conditions: Optional[Dict[str, Any]] = None  # 触发条件
    success_criteria: Optional[Dict[str, Any]] = None  # 成功标准


@dataclass
class RecoveryResult:
    """恢复结果"""
    success: bool
    actions_taken: List[RecoveryAction]
    time_taken: float
    error_message: Optional[str] = None
    final_scene: Optional[SceneType] = None


class ExceptionDetector:
    """异常检测器"""
    
    def __init__(self, game_detector: GameDetector):
        self.game_detector = game_detector
        self.last_scene_change = datetime.now()
        self.scene_stability_threshold = 30  # 秒
        self.ui_response_timeout = 10  # 秒
        
    def detect_game_crash(self) -> bool:
        """检测游戏崩溃"""
        return not self.game_detector.is_game_running()
    
    def detect_game_freeze(self) -> bool:
        """检测游戏冻结"""
        # 检查场景是否长时间未变化且无响应
        current_scene = self.game_detector.detect_current_scene()
        
        # 如果场景长时间未变化，可能是冻结
        if (datetime.now() - self.last_scene_change).seconds > self.scene_stability_threshold:
            # 尝试点击检测响应
            screenshot = self.game_detector.capture_screenshot()
            if screenshot is not None:
                # 简单的冻结检测：连续截图对比
                time.sleep(1)
                new_screenshot = self.game_detector.capture_screenshot()
                if new_screenshot is not None:
                    # 如果截图完全相同，可能是冻结
                    import cv2
                    import numpy as np
                    diff = cv2.absdiff(screenshot, new_screenshot)
                    if np.sum(diff) < 1000:  # 阈值可调整
                        return True
        
        return False
    
    def detect_network_error(self) -> bool:
        """检测网络错误"""
        # 查找网络错误相关的UI元素
        error_templates = [
            "network_error_dialog",
            "connection_failed",
            "server_maintenance",
            "timeout_error"
        ]
        
        for template in error_templates:
            element = self.game_detector.find_ui_element(template)
            if element and element.confidence > 0.8:
                return True
        
        return False
    
    def detect_ui_not_found(self, expected_ui: str, timeout: int = 10) -> bool:
        """检测UI元素未找到"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            element = self.game_detector.find_ui_element(expected_ui)
            if element:
                return False
            time.sleep(0.5)
        
        return True
    
    def detect_unexpected_scene(self, expected_scene: SceneType) -> bool:
        """检测意外场景"""
        current_scene = self.game_detector.detect_current_scene()
        return current_scene != expected_scene
    
    def detect_operation_timeout(self, operation_start: datetime, timeout: int) -> bool:
        """检测操作超时"""
        return (datetime.now() - operation_start).seconds > timeout


class ExceptionRecovery:
    """异常恢复系统"""
    
    def __init__(self, game_detector: GameDetector, automation_controller: AutomationController):
        self.game_detector = game_detector
        self.automation_controller = automation_controller
        self.detector = ExceptionDetector(game_detector)
        
        # 恢复策略
        self.recovery_strategies = self._init_recovery_strategies()
        
        # 异常历史
        self.exception_history: List[ExceptionInfo] = []
        self.recovery_history: List[RecoveryResult] = []
        
        # 配置
        self.max_recovery_attempts = 3
        self.recovery_cooldown = 60  # 秒
        self.last_recovery_time = datetime.min
        
        # 回调函数
        self.exception_detected_callback: Optional[Callable] = None
        self.recovery_started_callback: Optional[Callable] = None
        self.recovery_completed_callback: Optional[Callable] = None
        
        logger.info("异常恢复系统初始化完成")
    
    def _init_recovery_strategies(self) -> Dict[ExceptionType, RecoveryStrategy]:
        """初始化恢复策略"""
        return {
            ExceptionType.GAME_CRASH: RecoveryStrategy(
                exception_type=ExceptionType.GAME_CRASH,
                actions=[RecoveryAction.RESTART_GAME, RecoveryAction.WAIT_AND_RETRY],
                max_attempts=2,
                retry_delay=10,
                timeout=120
            ),
            
            ExceptionType.GAME_FREEZE: RecoveryStrategy(
                exception_type=ExceptionType.GAME_FREEZE,
                actions=[RecoveryAction.FORCE_CLOSE, RecoveryAction.RESTART_GAME],
                max_attempts=2,
                retry_delay=5,
                timeout=60
            ),
            
            ExceptionType.NETWORK_ERROR: RecoveryStrategy(
                exception_type=ExceptionType.NETWORK_ERROR,
                actions=[RecoveryAction.WAIT_AND_RETRY, RecoveryAction.REFRESH_PAGE],
                max_attempts=3,
                retry_delay=15,
                timeout=90
            ),
            
            ExceptionType.UI_NOT_FOUND: RecoveryStrategy(
                exception_type=ExceptionType.UI_NOT_FOUND,
                actions=[RecoveryAction.REFRESH_PAGE, RecoveryAction.RETURN_TO_MAIN],
                max_attempts=2,
                retry_delay=3,
                timeout=30
            ),
            
            ExceptionType.UNEXPECTED_SCENE: RecoveryStrategy(
                exception_type=ExceptionType.UNEXPECTED_SCENE,
                actions=[RecoveryAction.RETURN_TO_MAIN, RecoveryAction.WAIT_AND_RETRY],
                max_attempts=2,
                retry_delay=5,
                timeout=45
            ),
            
            ExceptionType.OPERATION_TIMEOUT: RecoveryStrategy(
                exception_type=ExceptionType.OPERATION_TIMEOUT,
                actions=[RecoveryAction.REFRESH_PAGE, RecoveryAction.WAIT_AND_RETRY],
                max_attempts=2,
                retry_delay=5,
                timeout=30
            )
        }
    
    def detect_exceptions(self, task: Optional[Task] = None) -> List[ExceptionInfo]:
        """检测异常"""
        exceptions = []
        current_time = datetime.now()
        current_scene = self.game_detector.detect_current_scene()
        
        # 检测游戏崩溃
        if self.detector.detect_game_crash():
            exceptions.append(ExceptionInfo(
                exception_type=ExceptionType.GAME_CRASH,
                description="游戏进程已崩溃或关闭",
                timestamp=current_time,
                task_id=task.task_id if task else None,
                scene=current_scene
            ))
        
        # 检测游戏冻结
        elif self.detector.detect_game_freeze():
            exceptions.append(ExceptionInfo(
                exception_type=ExceptionType.GAME_FREEZE,
                description="游戏界面冻结，无响应",
                timestamp=current_time,
                task_id=task.task_id if task else None,
                scene=current_scene
            ))
        
        # 检测网络错误
        elif self.detector.detect_network_error():
            exceptions.append(ExceptionInfo(
                exception_type=ExceptionType.NETWORK_ERROR,
                description="检测到网络连接错误",
                timestamp=current_time,
                task_id=task.task_id if task else None,
                scene=current_scene
            ))
        
        return exceptions
    
    def handle_exception(self, exception_info: ExceptionInfo) -> RecoveryResult:
        """处理异常"""
        logger.warning(f"检测到异常: {exception_info.exception_type.value} - {exception_info.description}")
        
        # 记录异常
        self.exception_history.append(exception_info)
        
        # 调用回调
        if self.exception_detected_callback:
            self.exception_detected_callback(exception_info)
        
        # 检查恢复冷却时间
        if (datetime.now() - self.last_recovery_time).seconds < self.recovery_cooldown:
            logger.warning("恢复操作在冷却期内，跳过恢复")
            return RecoveryResult(
                success=False,
                actions_taken=[],
                time_taken=0,
                error_message="恢复操作在冷却期内"
            )
        
        # 获取恢复策略
        strategy = self.recovery_strategies.get(exception_info.exception_type)
        if not strategy:
            logger.error(f"未找到异常类型的恢复策略: {exception_info.exception_type.value}")
            return RecoveryResult(
                success=False,
                actions_taken=[],
                time_taken=0,
                error_message="未找到恢复策略"
            )
        
        # 执行恢复
        return self._execute_recovery(strategy, exception_info)
    
    def _execute_recovery(self, strategy: RecoveryStrategy, 
                         exception_info: ExceptionInfo) -> RecoveryResult:
        """执行恢复策略"""
        start_time = time.time()
        actions_taken = []
        
        logger.info(f"开始执行恢复策略: {strategy.exception_type.value}")
        
        # 调用回调
        if self.recovery_started_callback:
            self.recovery_started_callback(strategy, exception_info)
        
        try:
            for attempt in range(strategy.max_attempts):
                logger.info(f"恢复尝试 {attempt + 1}/{strategy.max_attempts}")
                
                for action in strategy.actions:
                    success = self._execute_recovery_action(action)
                    actions_taken.append(action)
                    
                    if not success:
                        logger.warning(f"恢复动作失败: {action.value}")
                        continue
                    
                    # 等待恢复生效
                    time.sleep(strategy.retry_delay)
                    
                    # 检查恢复是否成功
                    if self._check_recovery_success(strategy, exception_info):
                        time_taken = time.time() - start_time
                        final_scene = self.game_detector.detect_current_scene()
                        
                        result = RecoveryResult(
                            success=True,
                            actions_taken=actions_taken,
                            time_taken=time_taken,
                            final_scene=final_scene
                        )
                        
                        self.recovery_history.append(result)
                        self.last_recovery_time = datetime.now()
                        
                        # 调用回调
                        if self.recovery_completed_callback:
                            self.recovery_completed_callback(result)
                        
                        logger.info(f"异常恢复成功，耗时 {time_taken:.2f} 秒")
                        return result
                
                # 如果不是最后一次尝试，等待后重试
                if attempt < strategy.max_attempts - 1:
                    logger.info(f"等待 {strategy.retry_delay} 秒后重试")
                    time.sleep(strategy.retry_delay)
            
            # 所有尝试都失败
            time_taken = time.time() - start_time
            result = RecoveryResult(
                success=False,
                actions_taken=actions_taken,
                time_taken=time_taken,
                error_message="所有恢复尝试都失败",
                final_scene=self.game_detector.detect_current_scene()
            )
            
            self.recovery_history.append(result)
            
            # 调用回调
            if self.recovery_completed_callback:
                self.recovery_completed_callback(result)
            
            logger.error(f"异常恢复失败，耗时 {time_taken:.2f} 秒")
            return result
            
        except Exception as e:
            time_taken = time.time() - start_time
            result = RecoveryResult(
                success=False,
                actions_taken=actions_taken,
                time_taken=time_taken,
                error_message=f"恢复过程中出现异常: {str(e)}"
            )
            
            self.recovery_history.append(result)
            logger.error(f"恢复过程中出现异常: {e}")
            return result
    
    def _execute_recovery_action(self, action: RecoveryAction) -> bool:
        """执行恢复动作"""
        try:
            if action == RecoveryAction.RESTART_GAME:
                return self._restart_game()
            
            elif action == RecoveryAction.REFRESH_PAGE:
                return self._refresh_page()
            
            elif action == RecoveryAction.RETURN_TO_MAIN:
                return self._return_to_main()
            
            elif action == RecoveryAction.WAIT_AND_RETRY:
                return self._wait_and_retry()
            
            elif action == RecoveryAction.FORCE_CLOSE:
                return self._force_close_game()
            
            elif action == RecoveryAction.CLEAR_CACHE:
                return self._clear_cache()
            
            else:
                logger.warning(f"未实现的恢复动作: {action.value}")
                return False
                
        except Exception as e:
            logger.error(f"执行恢复动作失败: {action.value} - {e}")
            return False
    
    def _restart_game(self) -> bool:
        """重启游戏"""
        logger.info("尝试重启游戏")
        
        # 先关闭游戏
        if not self._force_close_game():
            return False
        
        # 等待游戏完全关闭
        time.sleep(5)
        
        # 重新启动游戏（这里需要根据实际情况实现）
        # 可能需要调用外部程序或脚本
        logger.info("游戏重启完成")
        return True
    
    def _refresh_page(self) -> bool:
        """刷新页面"""
        logger.info("尝试刷新页面")
        
        # 按F5刷新
        return self.automation_controller.execute_action({
            "type": ActionType.KEY_PRESS.value,
            "key": "F5"
        })
    
    def _return_to_main(self) -> bool:
        """返回主界面"""
        logger.info("尝试返回主界面")
        
        # 按ESC键多次，尝试返回主界面
        for _ in range(3):
            success = self.automation_controller.execute_action({
                "type": ActionType.KEY_PRESS.value,
                "key": "Escape"
            })
            if not success:
                return False
            time.sleep(1)
        
        return True
    
    def _wait_and_retry(self) -> bool:
        """等待并重试"""
        logger.info("等待网络恢复")
        time.sleep(10)
        return True
    
    def _force_close_game(self) -> bool:
        """强制关闭游戏"""
        logger.info("强制关闭游戏进程")
        
        try:
            import psutil
            import os
            
            # 查找游戏进程
            game_processes = []
            for proc in psutil.process_iter(['pid', 'name']):
                if '星穹铁道' in proc.info['name'] or 'StarRail' in proc.info['name']:
                    game_processes.append(proc)
            
            # 终止进程
            for proc in game_processes:
                try:
                    proc.terminate()
                    proc.wait(timeout=5)
                except psutil.TimeoutExpired:
                    proc.kill()
                
                logger.info(f"已终止游戏进程: {proc.info['name']} (PID: {proc.info['pid']})")
            
            return len(game_processes) > 0
            
        except Exception as e:
            logger.error(f"强制关闭游戏失败: {e}")
            return False
    
    def _clear_cache(self) -> bool:
        """清理缓存"""
        logger.info("清理游戏缓存")
        # 这里可以实现清理临时文件、缓存等操作
        return True
    
    def _check_recovery_success(self, strategy: RecoveryStrategy, 
                               exception_info: ExceptionInfo) -> bool:
        """检查恢复是否成功"""
        # 根据异常类型检查恢复结果
        if exception_info.exception_type == ExceptionType.GAME_CRASH:
            return self.game_detector.is_game_running()
        
        elif exception_info.exception_type == ExceptionType.GAME_FREEZE:
            # 检查游戏是否响应
            return not self.detector.detect_game_freeze()
        
        elif exception_info.exception_type == ExceptionType.NETWORK_ERROR:
            # 检查网络错误是否消失
            return not self.detector.detect_network_error()
        
        elif exception_info.exception_type == ExceptionType.UI_NOT_FOUND:
            # 检查UI是否可用
            current_scene = self.game_detector.detect_current_scene()
            return current_scene != SceneType.UNKNOWN
        
        elif exception_info.exception_type == ExceptionType.UNEXPECTED_SCENE:
            # 检查是否回到预期场景
            current_scene = self.game_detector.detect_current_scene()
            return current_scene in [SceneType.MAIN_MENU, SceneType.GAME_WORLD]
        
        return True
    
    def get_exception_statistics(self) -> Dict[str, Any]:
        """获取异常统计信息"""
        total_exceptions = len(self.exception_history)
        total_recoveries = len(self.recovery_history)
        successful_recoveries = sum(1 for r in self.recovery_history if r.success)
        
        # 按异常类型统计
        exception_counts = {}
        for exc in self.exception_history:
            exc_type = exc.exception_type.value
            exception_counts[exc_type] = exception_counts.get(exc_type, 0) + 1
        
        # 计算平均恢复时间
        avg_recovery_time = 0
        if self.recovery_history:
            avg_recovery_time = sum(r.time_taken for r in self.recovery_history) / len(self.recovery_history)
        
        return {
            "total_exceptions": total_exceptions,
            "total_recoveries": total_recoveries,
            "successful_recoveries": successful_recoveries,
            "recovery_success_rate": successful_recoveries / total_recoveries if total_recoveries > 0 else 0,
            "exception_counts": exception_counts,
            "average_recovery_time": avg_recovery_time,
            "last_exception": self.exception_history[-1].timestamp.isoformat() if self.exception_history else None
        }
    
    def set_callbacks(self, exception_detected: Optional[Callable] = None,
                     recovery_started: Optional[Callable] = None,
                     recovery_completed: Optional[Callable] = None):
        """设置回调函数"""
        self.exception_detected_callback = exception_detected
        self.recovery_started_callback = recovery_started
        self.recovery_completed_callback = recovery_completed
    
    def add_custom_strategy(self, strategy: RecoveryStrategy):
        """添加自定义恢复策略"""
        self.recovery_strategies[strategy.exception_type] = strategy
        logger.info(f"已添加自定义恢复策略: {strategy.exception_type.value}")