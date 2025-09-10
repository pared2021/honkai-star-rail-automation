"""游戏场景监控模块.

提供场景变化检测、场景转换回调和场景识别优化功能。
"""

import time
import threading
from typing import Optional, Callable, Dict, Any, List
from dataclasses import dataclass
from enum import Enum
from .game_detector import SceneType, GameDetector
import logging


class SceneChangeEvent(Enum):
    """场景变化事件类型."""
    
    SCENE_ENTERED = "scene_entered"
    SCENE_EXITED = "scene_exited"
    SCENE_CHANGED = "scene_changed"
    SCENE_STABLE = "scene_stable"


@dataclass
class SceneTransition:
    """场景转换信息."""
    
    from_scene: SceneType
    to_scene: SceneType
    timestamp: float
    duration: float  # 转换持续时间
    confidence: float  # 转换置信度


@dataclass
class SceneState:
    """场景状态信息."""
    
    scene_type: SceneType
    enter_time: float
    duration: float
    stability_score: float  # 场景稳定性评分
    detection_count: int  # 检测次数


class SceneMonitor:
    """游戏场景监控器.
    
    提供场景变化检测、场景转换回调和场景识别优化功能。
    """
    
    def __init__(
        self,
        game_detector: GameDetector,
        detection_interval: float = 1.0,
        stability_threshold: int = 3,
        confidence_threshold: float = 0.8
    ):
        """初始化场景监控器.
        
        Args:
            game_detector: 游戏检测器实例
            detection_interval: 检测间隔（秒）
            stability_threshold: 场景稳定性阈值（连续检测次数）
            confidence_threshold: 场景置信度阈值
        """
        self.game_detector = game_detector
        self.detection_interval = detection_interval
        self.stability_threshold = stability_threshold
        self.confidence_threshold = confidence_threshold
        
        # 监控状态
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        # 场景状态
        self._current_scene: Optional[SceneType] = None
        self._previous_scene: Optional[SceneType] = None
        self._scene_history: List[SceneState] = []
        self._transition_history: List[SceneTransition] = []
        
        # 场景稳定性跟踪
        self._scene_detection_buffer: List[SceneType] = []
        self._scene_enter_time: Optional[float] = None
        self._scene_detection_count = 0
        
        # 回调函数
        self._scene_callbacks: Dict[SceneChangeEvent, List[Callable]] = {
            SceneChangeEvent.SCENE_ENTERED: [],
            SceneChangeEvent.SCENE_EXITED: [],
            SceneChangeEvent.SCENE_CHANGED: [],
            SceneChangeEvent.SCENE_STABLE: []
        }
        
        # 日志
        self.logger = logging.getLogger(__name__)
    
    def start_monitoring(self) -> bool:
        """开始场景监控.
        
        Returns:
            bool: 启动成功返回True
        """
        if self._monitoring:
            self.logger.warning("Scene monitoring is already running")
            return False
        
        try:
            self._monitoring = True
            self._stop_event.clear()
            self._monitor_thread = threading.Thread(
                target=self._monitor_loop,
                daemon=True
            )
            self._monitor_thread.start()
            self.logger.info("Scene monitoring started")
            return True
        except Exception as e:
            self.logger.error(f"Failed to start scene monitoring: {e}")
            self._monitoring = False
            return False
    
    def stop_monitoring(self) -> bool:
        """停止场景监控.
        
        Returns:
            bool: 停止成功返回True
        """
        if not self._monitoring:
            return True
        
        try:
            self._monitoring = False
            self._stop_event.set()
            
            if self._monitor_thread and self._monitor_thread.is_alive():
                self._monitor_thread.join(timeout=5.0)
            
            self.logger.info("Scene monitoring stopped")
            return True
        except Exception as e:
            self.logger.error(f"Failed to stop scene monitoring: {e}")
            return False
    
    def _monitor_loop(self):
        """监控循环."""
        while self._monitoring and not self._stop_event.is_set():
            try:
                # 检测当前场景
                detected_scene = self.game_detector.detect_scene()
                self._process_scene_detection(detected_scene)
                
                # 等待下次检测
                if not self._stop_event.wait(self.detection_interval):
                    continue
                else:
                    break
                    
            except Exception as e:
                self.logger.error(f"Error in scene monitoring loop: {e}")
                time.sleep(self.detection_interval)
    
    def _process_scene_detection(self, detected_scene: SceneType):
        """处理场景检测结果.
        
        Args:
            detected_scene: 检测到的场景类型
        """
        current_time = time.time()
        
        # 添加到检测缓冲区
        self._scene_detection_buffer.append(detected_scene)
        
        # 保持缓冲区大小
        if len(self._scene_detection_buffer) > self.stability_threshold * 2:
            self._scene_detection_buffer.pop(0)
        
        # 检查场景稳定性
        stable_scene = self._check_scene_stability()
        
        if stable_scene and stable_scene != self._current_scene:
            # 场景发生变化
            self._handle_scene_change(stable_scene, current_time)
        elif stable_scene == self._current_scene and self._current_scene:
            # 场景保持稳定
            self._scene_detection_count += 1
            self._trigger_callbacks(SceneChangeEvent.SCENE_STABLE, {
                'scene': self._current_scene,
                'duration': current_time - (self._scene_enter_time or current_time),
                'detection_count': self._scene_detection_count
            })
    
    def _check_scene_stability(self) -> Optional[SceneType]:
        """检查场景稳定性.
        
        Returns:
            Optional[SceneType]: 稳定的场景类型，如果不稳定返回None
        """
        if len(self._scene_detection_buffer) < self.stability_threshold:
            return None
        
        # 检查最近的检测结果是否一致
        recent_detections = self._scene_detection_buffer[-self.stability_threshold:]
        
        # 计算每个场景类型的出现次数
        scene_counts = {}
        for scene in recent_detections:
            scene_counts[scene] = scene_counts.get(scene, 0) + 1
        
        # 找到出现次数最多的场景
        if not scene_counts:
            return None
        
        most_common_scene = max(scene_counts, key=scene_counts.get)
        most_common_count = scene_counts[most_common_scene]
        
        # 检查是否达到稳定性阈值
        stability_ratio = most_common_count / len(recent_detections)
        
        if stability_ratio >= self.confidence_threshold:
            return most_common_scene
        
        return None
    
    def _handle_scene_change(self, new_scene: SceneType, timestamp: float):
        """处理场景变化.
        
        Args:
            new_scene: 新场景类型
            timestamp: 变化时间戳
        """
        old_scene = self._current_scene
        
        # 记录场景退出
        if old_scene and self._scene_enter_time:
            duration = timestamp - self._scene_enter_time
            
            # 添加到场景历史
            scene_state = SceneState(
                scene_type=old_scene,
                enter_time=self._scene_enter_time,
                duration=duration,
                stability_score=self._calculate_stability_score(),
                detection_count=self._scene_detection_count
            )
            self._scene_history.append(scene_state)
            
            # 触发场景退出回调
            self._trigger_callbacks(SceneChangeEvent.SCENE_EXITED, {
                'scene': old_scene,
                'duration': duration,
                'stability_score': scene_state.stability_score
            })
        
        # 记录场景转换
        if old_scene and old_scene != new_scene:
            transition = SceneTransition(
                from_scene=old_scene,
                to_scene=new_scene,
                timestamp=timestamp,
                duration=timestamp - (self._scene_enter_time or timestamp),
                confidence=self._calculate_transition_confidence()
            )
            self._transition_history.append(transition)
            
            # 触发场景变化回调
            self._trigger_callbacks(SceneChangeEvent.SCENE_CHANGED, {
                'from_scene': old_scene,
                'to_scene': new_scene,
                'transition': transition
            })
        
        # 更新当前场景
        self._previous_scene = self._current_scene
        self._current_scene = new_scene
        self._scene_enter_time = timestamp
        self._scene_detection_count = 1
        
        # 触发场景进入回调
        self._trigger_callbacks(SceneChangeEvent.SCENE_ENTERED, {
            'scene': new_scene,
            'previous_scene': old_scene,
            'timestamp': timestamp
        })
        
        self.logger.info(f"Scene changed: {old_scene} -> {new_scene}")
    
    def _calculate_stability_score(self) -> float:
        """计算场景稳定性评分.
        
        Returns:
            float: 稳定性评分 (0.0-1.0)
        """
        if not self._scene_detection_buffer:
            return 0.0
        
        # 计算当前场景在缓冲区中的占比
        current_scene_count = sum(
            1 for scene in self._scene_detection_buffer 
            if scene == self._current_scene
        )
        
        return current_scene_count / len(self._scene_detection_buffer)
    
    def _calculate_transition_confidence(self) -> float:
        """计算场景转换置信度.
        
        Returns:
            float: 转换置信度 (0.0-1.0)
        """
        if len(self._scene_detection_buffer) < self.stability_threshold:
            return 0.0
        
        # 基于最近检测结果的一致性计算置信度
        recent_detections = self._scene_detection_buffer[-self.stability_threshold:]
        new_scene_count = sum(
            1 for scene in recent_detections 
            if scene == self._current_scene
        )
        
        return new_scene_count / len(recent_detections)
    
    def _trigger_callbacks(self, event: SceneChangeEvent, data: Dict[str, Any]):
        """触发回调函数.
        
        Args:
            event: 事件类型
            data: 事件数据
        """
        callbacks = self._scene_callbacks.get(event, [])
        
        for callback in callbacks:
            try:
                callback(event, data)
            except Exception as e:
                self.logger.error(f"Error in scene callback: {e}")
    
    def add_scene_callback(
        self, 
        event: SceneChangeEvent, 
        callback: Callable[[SceneChangeEvent, Dict[str, Any]], None]
    ):
        """添加场景回调函数.
        
        Args:
            event: 事件类型
            callback: 回调函数
        """
        if event not in self._scene_callbacks:
            self._scene_callbacks[event] = []
        
        self._scene_callbacks[event].append(callback)
    
    def remove_scene_callback(
        self, 
        event: SceneChangeEvent, 
        callback: Callable[[SceneChangeEvent, Dict[str, Any]], None]
    ):
        """移除场景回调函数.
        
        Args:
            event: 事件类型
            callback: 回调函数
        """
        if event in self._scene_callbacks:
            try:
                self._scene_callbacks[event].remove(callback)
            except ValueError:
                pass
    
    def get_current_scene(self) -> Optional[SceneType]:
        """获取当前场景.
        
        Returns:
            Optional[SceneType]: 当前场景类型
        """
        return self._current_scene
    
    def get_scene_history(self, limit: Optional[int] = None) -> List[SceneState]:
        """获取场景历史.
        
        Args:
            limit: 返回记录数限制
            
        Returns:
            List[SceneState]: 场景历史记录
        """
        if limit:
            return self._scene_history[-limit:]
        return self._scene_history.copy()
    
    def get_transition_history(self, limit: Optional[int] = None) -> List[SceneTransition]:
        """获取场景转换历史.
        
        Args:
            limit: 返回记录数限制
            
        Returns:
            List[SceneTransition]: 场景转换历史记录
        """
        if limit:
            return self._transition_history[-limit:]
        return self._transition_history.copy()
    
    def get_monitoring_status(self) -> Dict[str, Any]:
        """获取监控状态.
        
        Returns:
            Dict[str, Any]: 监控状态信息
        """
        return {
            'monitoring': self._monitoring,
            'current_scene': self._current_scene.value if self._current_scene else None,
            'previous_scene': self._previous_scene.value if self._previous_scene else None,
            'scene_enter_time': self._scene_enter_time,
            'detection_count': self._scene_detection_count,
            'scene_history_count': len(self._scene_history),
            'transition_history_count': len(self._transition_history),
            'detection_interval': self.detection_interval,
            'stability_threshold': self.stability_threshold,
            'confidence_threshold': self.confidence_threshold
        }
    
    def clear_history(self):
        """清空历史记录."""
        self._scene_history.clear()
        self._transition_history.clear()
        self._scene_detection_buffer.clear()
        self.logger.info("Scene history cleared")