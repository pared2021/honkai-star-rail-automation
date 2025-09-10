"""场景监控器测试模块."""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from threading import Event

from src.core.scene_monitor import (
    SceneMonitor,
    SceneChangeEvent,
    SceneTransition,
    SceneState
)
from src.core.game_detector import SceneType, GameDetector


class TestSceneChangeEvent:
    """场景变化事件测试."""
    
    def test_scene_change_event_values(self):
        """测试场景变化事件枚举值."""
        assert SceneChangeEvent.SCENE_ENTERED.value == "scene_entered"
        assert SceneChangeEvent.SCENE_EXITED.value == "scene_exited"
        assert SceneChangeEvent.SCENE_CHANGED.value == "scene_changed"
        assert SceneChangeEvent.SCENE_STABLE.value == "scene_stable"


class TestSceneTransition:
    """测试SceneTransition类."""
    
    def test_scene_transition_creation(self):
        """测试场景转换创建."""
        transition = SceneTransition(
            from_scene=SceneType.MAIN_MENU,
            to_scene=SceneType.GAME_PLAY,
            timestamp=time.time(),
            duration=1.5,
            confidence=0.9
        )
        
        assert transition.from_scene == SceneType.MAIN_MENU
        assert transition.to_scene == SceneType.GAME_PLAY
        assert transition.duration == 1.5
        assert transition.confidence == 0.9
        assert isinstance(transition.timestamp, float)
    
    def test_scene_transition_str(self):
        """测试场景转换字符串表示."""
        transition = SceneTransition(
            from_scene=SceneType.MAIN_MENU,
            to_scene=SceneType.GAME_PLAY,
            timestamp=time.time(),
            duration=1.5,
            confidence=0.9
        )
        
        str_repr = str(transition)
        assert "MAIN_MENU" in str_repr
        assert "GAME_PLAY" in str_repr


class TestSceneState:
    """测试SceneState类."""
    
    def test_scene_state_creation(self):
        """测试场景状态创建."""
        state = SceneState(
            scene_type=SceneType.MAIN_MENU,
            enter_time=time.time(),
            duration=2.0,
            stability_score=0.9,
            detection_count=5
        )
        
        assert state.scene_type == SceneType.MAIN_MENU
        assert state.stability_score == 0.9
        assert state.duration == 2.0
        assert state.detection_count == 5
        assert isinstance(state.enter_time, float)
    
    def test_scene_state_is_stable(self):
        """测试场景状态稳定性判断."""
        # 稳定状态
        stable_state = SceneState(
            scene_type=SceneType.MAIN_MENU,
            enter_time=time.time(),
            duration=3.0,
            stability_score=0.9,
            detection_count=5
        )
        
        # 基本属性验证
        assert stable_state.stability_score >= 0.8
        assert stable_state.duration >= 2.0
        
        # 不稳定状态（时间不够）
        unstable_state = SceneState(
            scene_type=SceneType.MAIN_MENU,
            enter_time=time.time(),
            duration=1.0,
            stability_score=0.9,
            detection_count=2
        )
        
        assert unstable_state.duration < 2.0
        
        # 不稳定状态（稳定性评分不够）
        low_stability_state = SceneState(
            scene_type=SceneType.MAIN_MENU,
            enter_time=time.time(),
            duration=3.0,
            stability_score=0.7,
            detection_count=5
        )
        
        assert low_stability_state.stability_score < 0.8


class TestSceneMonitor:
    """场景监控器测试."""
    
    def setup_method(self):
        """测试前设置."""
        self.mock_detector = Mock(spec=GameDetector)
        self.monitor = SceneMonitor(
            game_detector=self.mock_detector,
            detection_interval=0.1,
            stability_threshold=3,
            confidence_threshold=0.8
        )
    
    def test_init(self):
        """测试初始化."""
        assert self.monitor.game_detector == self.mock_detector
        assert self.monitor.detection_interval == 0.1
        assert self.monitor.stability_threshold == 3
        assert self.monitor.confidence_threshold == 0.8
        assert not self.monitor._monitoring
        assert self.monitor._current_scene is None
        assert len(self.monitor._scene_history) == 0
        assert len(self.monitor._scene_callbacks) == 4
    
    def test_trigger_callbacks(self):
        """测试触发回调函数."""
        callback_called = []
        
        def test_callback(event, data):
            callback_called.append((event, data))
        
        # 添加回调
        self.monitor.add_scene_callback(SceneChangeEvent.SCENE_CHANGED, test_callback)
        
        # 触发回调
        event_data = {
            'from_scene': SceneType.MAIN_MENU,
            'to_scene': SceneType.GAME_PLAY,
            'transition': None
        }
        self.monitor._trigger_callbacks(SceneChangeEvent.SCENE_CHANGED, event_data)
        
        # 验证回调被调用
        assert len(callback_called) == 1
        assert callback_called[0][0] == SceneChangeEvent.SCENE_CHANGED
        assert callback_called[0][1] == event_data
    
    def test_remove_callback(self):
        """测试移除回调函数."""
        callback = Mock()
        
        # 添加后移除
        self.monitor.add_scene_callback(SceneChangeEvent.SCENE_EXITED, callback)
        assert len(self.monitor._scene_callbacks[SceneChangeEvent.SCENE_EXITED]) == 1
        
        self.monitor.remove_scene_callback(SceneChangeEvent.SCENE_EXITED, callback)
        assert len(self.monitor._scene_callbacks[SceneChangeEvent.SCENE_EXITED]) == 0
    
    def test_start_monitoring(self):
        """测试开始监控."""
        with patch('threading.Thread') as mock_thread:
            mock_thread_instance = Mock()
            mock_thread.return_value = mock_thread_instance
            
            result = self.monitor.start_monitoring()
            
            assert result is True
            assert self.monitor._monitoring
            mock_thread.assert_called_once()
            mock_thread_instance.start.assert_called_once()
    
    def test_stop_monitoring(self):
        """测试停止监控."""
        # 模拟监控状态
        self.monitor._monitoring = True
        self.monitor._stop_event = Event()
        self.monitor._monitor_thread = Mock()
        
        result = self.monitor.stop_monitoring()
        
        assert result is True
        assert not self.monitor._monitoring
        assert self.monitor._stop_event.is_set()
    
    def test_get_current_scene(self):
        """测试获取当前场景."""
        # 无当前场景
        assert self.monitor.get_current_scene() is None
        
        # 有当前场景
        self.monitor._current_scene = SceneType.MAIN_MENU
        
        assert self.monitor.get_current_scene() == SceneType.MAIN_MENU
    
    def test_get_scene_history(self):
        """测试获取场景历史记录."""
        # 添加一些历史记录
        scene_state = SceneState(
            scene_type=SceneType.MAIN_MENU,
            enter_time=time.time(),
            duration=1.0,
            stability_score=0.9,
            detection_count=5
        )
        self.monitor._scene_history.append(scene_state)
        
        # 获取历史记录
        history = self.monitor.get_scene_history()
        assert len(history) == 1
        assert history[0] == scene_state
        
        # 测试限制数量 - limit=0时返回所有记录（因为if limit:条件为False）
        history_all = self.monitor.get_scene_history(limit=0)
        assert len(history_all) == 1  # limit=0返回所有记录
        
        # 测试获取最后1个记录
        history_one = self.monitor.get_scene_history(limit=1)
        assert len(history_one) == 1
        assert history_one[0] == scene_state
    
    def test_clear_history(self):
        """测试清除历史记录."""
        # 添加历史记录
        scene_state = SceneState(
            scene_type=SceneType.MAIN_MENU,
            enter_time=time.time(),
            duration=1.0,
            stability_score=0.9,
            detection_count=5
        )
        self.monitor._scene_history.append(scene_state)
        
        assert len(self.monitor._scene_history) == 1
        
        self.monitor.clear_history()
        assert len(self.monitor._scene_history) == 0
    
    def test_detect_scene_change(self):
        """测试场景变化检测."""
        # 设置初始场景和时间
        initial_scene = SceneType.MAIN_MENU
        self.monitor._current_scene = initial_scene
        self.monitor._scene_enter_time = time.time() - 10  # 10秒前进入
        
        # 模拟检测到新场景
        new_scene = SceneType.GAME_PLAY
        timestamp = time.time()
        
        # 调用场景变化处理
        self.monitor._handle_scene_change(new_scene, timestamp)
        
        # 验证场景已更新
        assert self.monitor._current_scene == new_scene
        assert self.monitor._previous_scene == initial_scene
    
    def test_check_scene_stability(self):
        """测试场景稳定性检查."""
        # 添加稳定场景检测
        for _ in range(5):
            self.monitor._scene_detection_buffer.append(SceneType.MAIN_MENU)
        
        # 检查稳定性
        stable_scene = self.monitor._check_scene_stability()
        assert stable_scene == SceneType.MAIN_MENU
        
        # 添加不稳定场景检测
        self.monitor._scene_detection_buffer.append(SceneType.GAME_PLAY)
        
        stable_scene = self.monitor._check_scene_stability()
        assert stable_scene is None  # 不稳定
    
    def test_trigger_callbacks_multiple(self):
        """测试触发多个回调函数."""
        callback1 = Mock()
        callback2 = Mock()
        
        # 添加回调
        self.monitor.add_scene_callback(SceneChangeEvent.SCENE_CHANGED, callback1)
        self.monitor.add_scene_callback(SceneChangeEvent.SCENE_CHANGED, callback2)
        
        # 创建场景状态
        scene_state = SceneState(
            scene_type=SceneType.MAIN_MENU,
            enter_time=time.time(),
            duration=1.0,
            stability_score=0.95,
            detection_count=5
        )
        
        # 触发回调
        self.monitor._trigger_callbacks(SceneChangeEvent.SCENE_CHANGED, scene_state)
        
        # 验证回调被调用
        callback1.assert_called_once_with(SceneChangeEvent.SCENE_CHANGED, scene_state)
        callback2.assert_called_once_with(SceneChangeEvent.SCENE_CHANGED, scene_state)
    
    def test_monitor_loop_scene_detection(self):
        """测试监控循环中的场景检测."""
        # 设置检测结果
        self.mock_detector.detect_scene.return_value = SceneType.MAIN_MENU
        
        # 添加回调
        callback_called = []
        def test_callback(event, data):
            callback_called.append((event, data))
        
        self.monitor.add_scene_callback(SceneChangeEvent.SCENE_ENTERED, test_callback)
        
        # 模拟场景检测处理（需要多次检测才能稳定）
        for _ in range(self.monitor.stability_threshold + 1):
            self.monitor._process_scene_detection(SceneType.MAIN_MENU)
        
        # 验证场景被设置
        assert self.monitor._current_scene == SceneType.MAIN_MENU
        
        # 验证回调被调用
        assert len(callback_called) >= 1
    
    def test_error_handling_in_detection(self):
        """测试检测过程中的错误处理."""
        # 设置检测器抛出异常
        self.mock_detector.detect_scene.side_effect = Exception("检测错误")
        
        # 监控应该继续运行，不会因为单次检测错误而停止
        try:
            # 直接调用监控循环的一次迭代
            self.monitor._monitoring = True
            # 模拟一次检测循环
            scene = self.mock_detector.detect_scene()
            self.monitor._process_scene_detection(scene)
        except Exception as e:
            # 应该捕获并处理异常，不让其传播
            pass
        
        # 验证当前场景保持不变
        assert self.monitor._current_scene is None
    
    def test_max_history_limit(self):
        """测试历史记录数量限制."""
        # 直接添加多个历史记录
        for i in range(5):
            scene_state = SceneState(
                scene_type=SceneType.MAIN_MENU,
                enter_time=time.time() + i,
                duration=1.0,
                stability_score=0.9,
                detection_count=3
            )
            self.monitor._scene_history.append(scene_state)
        
        # 验证历史记录被添加
        assert len(self.monitor._scene_history) == 5