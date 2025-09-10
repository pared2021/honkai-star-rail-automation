"""OCR集成测试模块.

测试OCR功能与GameDetector的集成。"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from src.core.game_detector import GameDetector, GameWindow
from src.config.config_manager import ConfigManager


class TestOCRIntegration:
    """OCR集成测试类."""

    def setup_method(self):
        """设置测试环境."""
        self.config_manager = ConfigManager()
        self.detector = GameDetector(self.config_manager)
        
        # 创建模拟游戏窗口
        self.mock_window = GameWindow(
            hwnd=12345,
            title="Test Game",
            rect=(100, 100, 900, 700),
            width=800,
            height=600,
            is_foreground=True
        )
        
        # 创建测试截图数据
        self.test_screenshot = np.zeros((600, 800, 3), dtype=np.uint8)
        self.test_screenshot_bytes = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x03 \x00\x00\x02X\x08\x02\x00\x00\x00'

    @patch('src.core.game_detector.cv2')
    def test_recognize_text_in_region_success(self, mock_cv2):
        """测试区域文本识别成功."""
        # 设置模拟
        mock_cv2.imencode.return_value = (True, np.array([1, 2, 3]))
        self.detector.game_window = self.mock_window
        
        with patch.object(self.detector, 'capture_screenshot', return_value=self.test_screenshot):
            with patch.object(self.detector.template_matcher, 'recognize_text', return_value="Test Text"):
                result = self.detector.recognize_text_in_region((10, 10, 100, 50))
                
                assert result == "Test Text"
                self.detector.template_matcher.recognize_text.assert_called_once()

    @patch('src.core.game_detector.cv2')
    def test_recognize_text_in_region_no_screenshot(self, mock_cv2):
        """测试无截图时的文本识别."""
        with patch.object(self.detector, 'capture_screenshot', return_value=None):
            result = self.detector.recognize_text_in_region((10, 10, 100, 50))
            assert result is None

    @patch('src.core.game_detector.cv2')
    def test_find_text_in_screen_success(self, mock_cv2):
        """测试屏幕文本查找成功."""
        # 设置模拟
        mock_cv2.imencode.return_value = (True, np.array([1, 2, 3]))
        self.detector.game_window = self.mock_window
        
        expected_result = {
            'found': True,
            'text': 'Test Text',
            'position': (50, 50),
            'confidence': 0.95
        }
        
        with patch.object(self.detector, 'capture_screenshot', return_value=self.test_screenshot):
            with patch.object(self.detector.template_matcher, 'find_text', return_value=expected_result):
                result = self.detector.find_text_in_screen("Test Text")
                
                assert result == expected_result
                self.detector.template_matcher.find_text.assert_called_once()

    @patch('src.core.game_detector.cv2')
    def test_find_text_in_screen_with_region(self, mock_cv2):
        """测试指定区域的文本查找."""
        # 设置模拟
        mock_cv2.imencode.return_value = (True, np.array([1, 2, 3]))
        self.detector.game_window = self.mock_window
        
        region = (10, 10, 200, 100)
        expected_result = {
            'found': True,
            'text': 'Region Text',
            'position': (50, 50),
            'confidence': 0.90
        }
        
        with patch.object(self.detector, 'capture_screenshot', return_value=self.test_screenshot):
            with patch.object(self.detector.template_matcher, 'find_text', return_value=expected_result):
                result = self.detector.find_text_in_screen("Region Text", region)
                
                assert result == expected_result
                self.detector.template_matcher.find_text.assert_called_once_with(
                    "Region Text", mock_cv2.imencode.return_value[1].tobytes(), region
                )

    @patch('src.core.game_detector.cv2')
    def test_extract_all_text_from_screen_success(self, mock_cv2):
        """测试提取所有文本成功."""
        # 设置模拟
        mock_cv2.imencode.return_value = (True, np.array([1, 2, 3]))
        self.detector.game_window = self.mock_window
        
        expected_result = [
            {'text': 'Text 1', 'position': (10, 10), 'confidence': 0.95},
            {'text': 'Text 2', 'position': (50, 50), 'confidence': 0.90}
        ]
        
        with patch.object(self.detector, 'capture_screenshot', return_value=self.test_screenshot):
            with patch.object(self.detector.template_matcher, 'extract_all_text', return_value=expected_result):
                result = self.detector.extract_all_text_from_screen()
                
                assert result == expected_result
                self.detector.template_matcher.extract_all_text.assert_called_once()

    @patch('src.core.game_detector.cv2')
    def test_extract_all_text_from_screen_empty(self, mock_cv2):
        """测试提取所有文本为空."""
        # 设置模拟
        mock_cv2.imencode.return_value = (True, np.array([1, 2, 3]))
        self.detector.game_window = self.mock_window
        
        with patch.object(self.detector, 'capture_screenshot', return_value=self.test_screenshot):
            with patch.object(self.detector.template_matcher, 'extract_all_text', return_value=[]):
                result = self.detector.extract_all_text_from_screen()
                
                assert result == []

    @patch('src.core.game_detector.cv2')
    @patch('time.time')
    @patch('time.sleep')
    def test_wait_for_text_success(self, mock_sleep, mock_time, mock_cv2):
        """测试等待文本出现成功."""
        # 设置模拟
        mock_cv2.imencode.return_value = (True, np.array([1, 2, 3]))
        mock_time.side_effect = [0, 1, 2]  # 模拟时间流逝
        self.detector.game_window = self.mock_window
        
        expected_result = {
            'found': True,
            'text': 'Target Text',
            'position': (100, 100),
            'confidence': 0.95
        }
        
        with patch.object(self.detector, 'capture_screenshot', return_value=self.test_screenshot):
            with patch.object(self.detector.template_matcher, 'find_text', return_value=expected_result):
                result = self.detector.wait_for_text("Target Text", timeout=5.0)
                
                assert result == expected_result

    @patch('src.core.game_detector.cv2')
    @patch('time.time')
    @patch('time.sleep')
    def test_wait_for_text_timeout(self, mock_sleep, mock_time, mock_cv2):
        """测试等待文本超时."""
        # 设置模拟
        mock_cv2.imencode.return_value = (True, np.array([1, 2, 3]))
        mock_time.side_effect = [0, 1, 2, 3, 4, 5, 6]  # 模拟超时
        self.detector.game_window = self.mock_window
        
        with patch.object(self.detector, 'capture_screenshot', return_value=self.test_screenshot):
            with patch.object(self.detector.template_matcher, 'find_text', return_value=None):
                result = self.detector.wait_for_text("Missing Text", timeout=5.0)
                
                assert result is None

    @patch('src.core.game_detector.cv2')
    def test_is_text_present_true(self, mock_cv2):
        """测试文本存在检查为真."""
        # 设置模拟
        mock_cv2.imencode.return_value = (True, np.array([1, 2, 3]))
        self.detector.game_window = self.mock_window
        
        expected_result = {
            'found': True,
            'text': 'Present Text',
            'position': (50, 50),
            'confidence': 0.90
        }
        
        with patch.object(self.detector, 'capture_screenshot', return_value=self.test_screenshot):
            with patch.object(self.detector.template_matcher, 'find_text', return_value=expected_result):
                result = self.detector.is_text_present("Present Text")
                
                assert result is True

    @patch('src.core.game_detector.cv2')
    def test_is_text_present_false(self, mock_cv2):
        """测试文本存在检查为假."""
        # 设置模拟
        mock_cv2.imencode.return_value = (True, np.array([1, 2, 3]))
        self.detector.game_window = self.mock_window
        
        with patch.object(self.detector, 'capture_screenshot', return_value=self.test_screenshot):
            with patch.object(self.detector.template_matcher, 'find_text', return_value=None):
                result = self.detector.is_text_present("Missing Text")
                
                assert result is False

    def test_ocr_integration_disabled(self):
        """测试OCR功能禁用时的行为."""
        # 禁用OCR功能
        self.detector.template_matcher.enable_ocr = False
        self.detector.template_matcher.ocr_detector = None
        
        result = self.detector.recognize_text_in_region((10, 10, 100, 50))
        assert result is None
        
        result = self.detector.find_text_in_screen("Test")
        assert result is None
        
        result = self.detector.extract_all_text_from_screen()
        assert result == []

    @patch('src.core.game_detector.cv2')
    def test_ocr_methods_exception_handling(self, mock_cv2):
        """测试OCR方法的异常处理."""
        # 设置模拟抛出异常
        mock_cv2.imencode.side_effect = Exception("Test exception")
        self.detector.game_window = self.mock_window
        
        with patch.object(self.detector, 'capture_screenshot', return_value=self.test_screenshot):
            result = self.detector.recognize_text_in_region((10, 10, 100, 50))
            assert result is None
            
            result = self.detector.find_text_in_screen("Test")
            assert result is None
            
            result = self.detector.extract_all_text_from_screen()
            assert result == []
            
            result = self.detector.is_text_present("Test")
            assert result is False