"""GameDetector功能实现测试.

测试GameDetector的实际功能实现，包括游戏检测、窗口识别、截图等。
"""

import unittest
from unittest.mock import MagicMock, patch, Mock
import sys
import os
import pytest

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.game_detector import GameDetector, SceneType, GameWindow, UIElement, WindowManager
from src.config.config_manager import ConfigManager
from src.interfaces.automation_interface import IGameDetector


class TestGameDetectorImplementation:
    """GameDetector实现测试类."""
    
    def setup_method(self):
        """测试前置设置。"""
        # 创建一个Mock的ConfigManager实例
        self.config_manager = MagicMock(spec=ConfigManager)
        
        # Mock get方法来返回配置
        def mock_get(key, default=None):
            config_data = {
                'game_detector': {
                    'templates_dir': 'templates',
                    'screenshot_interval': 1.0,
                    'detection_threshold': 0.8
                },
                'game_titles': ['StarRail', 'YuanShen']
            }
            return config_data.get(key, default)
            
        self.config_manager.get.side_effect = mock_get
        self.detector = GameDetector(self.config_manager)
        

        
    def test_interface_implementation(self):
        """测试接口实现."""
        detector = self.detector
        
        # 验证接口方法存在
        assert hasattr(detector, 'detect_game_window')
        assert hasattr(detector, 'is_game_running')
        assert hasattr(detector, 'capture_screen')
        assert hasattr(detector, 'find_template')
        assert hasattr(detector, 'get_game_status')
        
        # 验证方法可调用
        assert callable(detector.detect_game_window)
        assert callable(detector.is_game_running)
        assert callable(detector.capture_screen)
        assert callable(detector.find_template)
        assert callable(detector.get_game_status)
    
    @patch.object(WindowManager, 'find_game_windows')
    def test_is_game_running_with_process(self, mock_find_windows):
        """测试游戏窗口检测功能。"""
        detector = self.detector
        
        # 模拟找到游戏窗口
        mock_window = GameWindow(
            hwnd=12345,
            title="崩坏：星穹铁道",
            rect=(0, 0, 1920, 1080),
            width=1920,
            height=1080,
            is_foreground=True
        )
        mock_find_windows.return_value = [mock_window]
        
        result = detector.is_game_running()
        assert result is True
        assert detector.game_window == mock_window
        
        # 模拟没有找到游戏窗口
        mock_find_windows.return_value = []
        
        result = detector.is_game_running()
        assert result is False
        assert detector.game_window is None
    
    @patch('src.core.game_detector.win32gui', None)
    def test_is_game_running_without_win32gui(self):
        """测试没有win32gui时的处理。"""
        detector = self.detector
        
        result = detector.is_game_running()
        assert result is False
    
    @patch('src.core.game_detector.win32gui')
    def test_detect_game_window_success(self, mock_win32gui):
        """测试游戏窗口检测成功."""
        detector = self.detector
        
        # 模拟窗口枚举
        def mock_enum_windows(callback, param):
            # 模拟找到游戏窗口
            callback(12345, param)
            return True
        
        mock_win32gui.EnumWindows.side_effect = mock_enum_windows
        mock_win32gui.IsWindowVisible.return_value = True
        mock_win32gui.GetWindowText.return_value = "崩坏：星穹铁道"
        mock_win32gui.GetClassName.return_value = "UnityWndClass"
        mock_win32gui.GetWindowRect.return_value = (100, 100, 1920, 1080)
        
        result = detector.detect_game_window()
        
        assert result is not None
        assert result.title == "崩坏：星穹铁道"
        assert result.hwnd == 12345
        assert result.width == 1820
        assert result.height == 980
    
    @patch('src.core.game_detector.win32gui', None)
    def test_detect_game_window_without_win32gui(self):
        """测试没有win32gui时的处理."""
        detector = self.detector
        
        result = detector.detect_game_window()
        assert result is None
    
    @patch('src.core.game_detector.cv2')
    @patch('src.core.game_detector.Image')
    def test_find_template_success(self, mock_image, mock_cv2):
        """测试模板匹配成功."""
        detector = self.detector
        
        # 模拟截图数据 - 需要mock capture_screenshot而不是capture_screen
        import numpy as np
        fake_screenshot = np.zeros((100, 100, 3), dtype=np.uint8)
        detector.capture_screenshot = MagicMock(return_value=fake_screenshot)
        
        # 模拟PIL图像
        mock_pil_img = MagicMock()
        mock_image.open.return_value = mock_pil_img
        
        # 模拟OpenCV操作
        mock_cv2.cvtColor.return_value = fake_screenshot
        mock_cv2.imread.return_value = np.zeros((50, 50, 3), dtype=np.uint8)  # 模拟模板图像
        mock_cv2.matchTemplate.return_value = np.array([[0.9]])
        mock_cv2.minMaxLoc.return_value = (0.1, 0.9, (10, 20), (100, 200))
        
        # 模拟文件存在
        with patch('os.path.exists', return_value=True):
            result = detector.find_template('test_template.png', 0.8)
        
        assert result is not None
        assert result['found'] is True
        assert result['confidence'] == 0.9
        assert result['center'] == (125, 225)  # 100 + 50//2, 200 + 50//2
    
    @patch('src.core.game_detector.cv2', None)
    def test_find_template_without_opencv(self):
        """测试没有OpenCV时的处理."""
        detector = self.detector
        
        result = detector.find_template('test_template.png')
        assert result is None
    
    def test_get_game_status_comprehensive(self):
        """测试游戏状态获取功能."""
        detector = self.detector
        
        # 模拟各种状态
        detector.is_game_running = MagicMock(return_value=True)
        mock_window = MagicMock()
        mock_window.title = '崩坏：星穹铁道'
        mock_window.width = 1920
        mock_window.height = 1080
        mock_window.hwnd = 12345
        detector.detect_game_window = MagicMock(return_value=mock_window)
        detector.capture_screen = MagicMock(return_value=b'screenshot_data')
        
        result = detector.get_game_status()
        
        assert result['game_running'] is True
        assert result['window_found'] is True
        assert result['screenshot_available'] is True
        assert result['overall_status'] == 'ready'
        assert 'window_info' in result
        assert result['window_info']['title'] == '崩坏：星穹铁道'
    
    def test_get_game_status_partial(self):
        """测试部分功能可用的状态."""
        detector = self.detector
        
        # 模拟游戏运行但截图失败
        detector.is_game_running = MagicMock(return_value=True)
        mock_window = MagicMock()
        mock_window.title = '原神'
        mock_window.width = 1920
        mock_window.height = 1080
        mock_window.hwnd = 54321
        detector.detect_game_window = MagicMock(return_value=mock_window)
        detector.capture_screen = MagicMock(return_value=None)
        
        result = detector.get_game_status()
        
        assert result['game_running'] is True
        assert result['window_found'] is True
        assert result['screenshot_available'] is False
        assert result['overall_status'] == 'partial'
    
    def test_get_game_status_not_running(self):
        """测试游戏未运行状态."""
        detector = self.detector
        
        # 模拟游戏未运行
        detector.is_game_running = MagicMock(return_value=False)
        detector.detect_game_window = MagicMock(return_value=None)
        detector.capture_screen = MagicMock(return_value=None)
        
        result = detector.get_game_status()
        
        assert result['game_running'] is False
        assert result['window_found'] is False
        assert result['screenshot_available'] is False
        assert result['overall_status'] == 'not_running'
    
    def test_initialization_with_game_processes(self):
        """测试初始化时游戏进程列表设置."""
        detector = self.detector
        
        assert hasattr(detector, 'game_processes')
        assert isinstance(detector.game_processes, list)
        assert len(detector.game_processes) > 0
        assert 'StarRail.exe' in detector.game_processes


if __name__ == '__main__':
    pytest.main([__file__, '-v'])