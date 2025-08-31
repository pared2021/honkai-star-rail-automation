import unittest
from unittest.mock import Mock, patch, MagicMock
import numpy as np
from pathlib import Path
import cv2

from src.core.game_detector import (
    GameDetector, WindowManager, TemplateMatcher,
    SceneType, GameWindow, UIElement, TemplateInfo
)


class TestGameDetector(unittest.TestCase):
    """GameDetector类的单元测试"""
    
    def setUp(self):
        """测试前的设置"""
        self.detector = GameDetector()
        
    @patch('src.core.game_detector.WindowManager')
    def test_init(self, mock_window_manager):
        """测试GameDetector初始化"""
        detector = GameDetector()
        self.assertIsInstance(detector.window_manager, type(mock_window_manager.return_value))
        self.assertIsInstance(detector.template_matcher, TemplateMatcher)
        self.assertIsNone(detector.current_window)
        self.assertEqual(detector.current_scene, SceneType.UNKNOWN)
        
    @patch('src.core.game_detector.WindowManager.find_game_window')
    def test_detect_game_window_success(self, mock_find_window):
        """测试成功检测游戏窗口"""
        mock_window = GameWindow(
            hwnd=12345,
            title="崩坏：星穹铁道",
            rect=(0, 0, 1920, 1080),
            is_active=True
        )
        mock_find_window.return_value = mock_window
        
        result = self.detector.detect_game_window()
        
        self.assertTrue(result)
        self.assertEqual(self.detector.current_window, mock_window)
        mock_find_window.assert_called_once()
        
    @patch('src.core.game_detector.WindowManager.find_game_window')
    def test_detect_game_window_failure(self, mock_find_window):
        """测试检测游戏窗口失败"""
        mock_find_window.return_value = None
        
        result = self.detector.detect_game_window()
        
        self.assertFalse(result)
        self.assertIsNone(self.detector.current_window)
        
    @patch('src.core.game_detector.WindowManager.capture_window')
    def test_capture_screenshot_success(self, mock_capture):
        """测试成功截取屏幕"""
        mock_image = np.zeros((1080, 1920, 3), dtype=np.uint8)
        mock_capture.return_value = mock_image
        
        # 设置当前窗口
        self.detector.current_window = GameWindow(
            hwnd=12345,
            title="崩坏：星穹铁道",
            rect=(0, 0, 1920, 1080),
            is_active=True
        )
        
        result = self.detector.capture_screenshot()
        
        self.assertIsNotNone(result)
        self.assertEqual(result.shape, (1080, 1920, 3))
        mock_capture.assert_called_once_with(self.detector.current_window)
        
    def test_capture_screenshot_no_window(self):
        """测试没有窗口时截取屏幕"""
        result = self.detector.capture_screenshot()
        self.assertIsNone(result)
        
    @patch('src.core.game_detector.TemplateMatcher.match_template')
    def test_identify_scene_main_menu(self, mock_match):
        """测试识别主菜单场景"""
        mock_match.return_value = [(100, 100, 0.9)]
        mock_image = np.zeros((1080, 1920, 3), dtype=np.uint8)
        
        result = self.detector.identify_scene(mock_image)
        
        self.assertEqual(result, SceneType.MAIN_MENU)
        self.assertEqual(self.detector.current_scene, SceneType.MAIN_MENU)
        
    @patch('src.core.game_detector.TemplateMatcher.match_template')
    def test_identify_scene_unknown(self, mock_match):
        """测试识别未知场景"""
        mock_match.return_value = []
        mock_image = np.zeros((1080, 1920, 3), dtype=np.uint8)
        
        result = self.detector.identify_scene(mock_image)
        
        self.assertEqual(result, SceneType.UNKNOWN)
        self.assertEqual(self.detector.current_scene, SceneType.UNKNOWN)
        
    @patch('src.core.game_detector.TemplateMatcher.match_template')
    def test_find_ui_element_success(self, mock_match):
        """测试成功查找UI元素"""
        mock_match.return_value = [(150, 200, 0.85)]
        mock_image = np.zeros((1080, 1920, 3), dtype=np.uint8)
        
        result = self.detector.find_ui_element(mock_image, "start_button")
        
        self.assertIsNotNone(result)
        self.assertEqual(result.name, "start_button")
        self.assertEqual(result.position, (150, 200))
        self.assertEqual(result.confidence, 0.85)
        
    @patch('src.core.game_detector.TemplateMatcher.match_template')
    def test_find_ui_element_failure(self, mock_match):
        """测试查找UI元素失败"""
        mock_match.return_value = []
        mock_image = np.zeros((1080, 1920, 3), dtype=np.uint8)
        
        result = self.detector.find_ui_element(mock_image, "nonexistent_button")
        
        self.assertIsNone(result)
        
    def test_is_game_active_with_window(self):
        """测试游戏窗口激活状态检查"""
        self.detector.current_window = GameWindow(
            hwnd=12345,
            title="崩坏：星穹铁道",
            rect=(0, 0, 1920, 1080),
            is_active=True
        )
        
        result = self.detector.is_game_active()
        self.assertTrue(result)
        
    def test_is_game_active_without_window(self):
        """测试没有窗口时的激活状态检查"""
        result = self.detector.is_game_active()
        self.assertFalse(result)
        
    def test_get_window_info(self):
        """测试获取窗口信息"""
        mock_window = GameWindow(
            hwnd=12345,
            title="崩坏：星穹铁道",
            rect=(0, 0, 1920, 1080),
            is_active=True
        )
        self.detector.current_window = mock_window
        
        result = self.detector.get_window_info()
        
        self.assertEqual(result, mock_window)
        
    def test_get_current_scene(self):
        """测试获取当前场景"""
        self.detector.current_scene = SceneType.COMBAT
        
        result = self.detector.get_current_scene()
        
        self.assertEqual(result, SceneType.COMBAT)


class TestWindowManager(unittest.TestCase):
    """WindowManager类的单元测试"""
    
    def setUp(self):
        """测试前的设置"""
        self.window_manager = WindowManager()
        
    @patch('win32gui.FindWindow')
    @patch('win32gui.GetWindowText')
    @patch('win32gui.GetWindowRect')
    @patch('win32gui.GetForegroundWindow')
    def test_find_game_window_success(self, mock_foreground, mock_rect, mock_text, mock_find):
        """测试成功查找游戏窗口"""
        mock_find.return_value = 12345
        mock_text.return_value = "崩坏：星穹铁道"
        mock_rect.return_value = (0, 0, 1920, 1080)
        mock_foreground.return_value = 12345
        
        result = self.window_manager.find_game_window()
        
        self.assertIsNotNone(result)
        self.assertEqual(result.hwnd, 12345)
        self.assertEqual(result.title, "崩坏：星穹铁道")
        self.assertEqual(result.rect, (0, 0, 1920, 1080))
        self.assertTrue(result.is_active)
        
    @patch('win32gui.FindWindow')
    def test_find_game_window_failure(self, mock_find):
        """测试查找游戏窗口失败"""
        mock_find.return_value = 0
        
        result = self.window_manager.find_game_window()
        
        self.assertIsNone(result)
        
    @patch('win32gui.GetDC')
    @patch('win32gui.CreateCompatibleDC')
    @patch('win32gui.CreateCompatibleBitmap')
    @patch('win32gui.SelectObject')
    @patch('win32gui.BitBlt')
    @patch('win32gui.GetBitmapBits')
    def test_capture_window(self, mock_bits, mock_blt, mock_select, mock_bitmap, mock_dc, mock_get_dc):
        """测试窗口截图"""
        mock_window = GameWindow(
            hwnd=12345,
            title="崩坏：星穹铁道",
            rect=(0, 0, 1920, 1080),
            is_active=True
        )
        
        # 模拟位图数据
        mock_bits.return_value = b'\x00' * (1920 * 1080 * 4)
        
        result = self.window_manager.capture_window(mock_window)
        
        self.assertIsNotNone(result)
        self.assertEqual(result.shape, (1080, 1920, 3))


class TestTemplateMatcher(unittest.TestCase):
    """TemplateMatcher类的单元测试"""
    
    def setUp(self):
        """测试前的设置"""
        self.matcher = TemplateMatcher()
        
    @patch('pathlib.Path.exists')
    @patch('cv2.imread')
    def test_load_template_success(self, mock_imread, mock_exists):
        """测试成功加载模板"""
        mock_exists.return_value = True
        mock_template = np.zeros((100, 100, 3), dtype=np.uint8)
        mock_imread.return_value = mock_template
        
        result = self.matcher.load_template("test_template")
        
        self.assertTrue(result)
        self.assertIn("test_template", self.matcher.templates)
        
    @patch('pathlib.Path.exists')
    def test_load_template_failure(self, mock_exists):
        """测试加载模板失败"""
        mock_exists.return_value = False
        
        result = self.matcher.load_template("nonexistent_template")
        
        self.assertFalse(result)
        self.assertNotIn("nonexistent_template", self.matcher.templates)
        
    @patch('cv2.matchTemplate')
    @patch('cv2.minMaxLoc')
    def test_match_template_success(self, mock_minmax, mock_match):
        """测试成功匹配模板"""
        # 设置模板
        template = np.zeros((50, 50, 3), dtype=np.uint8)
        self.matcher.templates["test_template"] = TemplateInfo(
            name="test_template",
            image=template,
            threshold=0.8
        )
        
        # 模拟匹配结果
        mock_result = np.array([[0.9]])
        mock_match.return_value = mock_result
        mock_minmax.return_value = (0.1, 0.9, (10, 10), (100, 100))
        
        image = np.zeros((200, 200, 3), dtype=np.uint8)
        result = self.matcher.match_template(image, "test_template")
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], (100, 100, 0.9))
        
    def test_match_template_not_loaded(self):
        """测试匹配未加载的模板"""
        image = np.zeros((200, 200, 3), dtype=np.uint8)
        result = self.matcher.match_template(image, "nonexistent_template")
        
        self.assertEqual(result, [])


if __name__ == '__main__':
    unittest.main()