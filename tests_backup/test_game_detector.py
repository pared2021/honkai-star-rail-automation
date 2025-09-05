from pathlib import Path
import unittest
from unittest.mock import MagicMock, Mock, patch

import cv2
import numpy as np

from src.core.config_manager import ConfigManager
from src.core.game_detector import (
    GameDetector,
    GameWindow,
    SceneType,
    TemplateMatcher,
    UIElement,
    WindowManager,
)


class TestGameDetector(unittest.TestCase):
    """GameDetector类的单元测试"""

    def setUp(self):
        """测试前的设置"""
        self.mock_config = Mock(spec=ConfigManager)
        self.detector = GameDetector(self.mock_config)

    @patch("src.core.game_detector.WindowManager")
    def test_init(self, mock_window_manager):
        """测试GameDetector初始化"""
        mock_config = Mock(spec=ConfigManager)
        detector = GameDetector(mock_config)
        self.assertIsInstance(
            detector.window_manager, type(mock_window_manager.return_value)
        )
        self.assertIsInstance(detector.template_matcher, TemplateMatcher)
        self.assertEqual(detector.current_scene, SceneType.UNKNOWN)

    @patch("src.core.game_detector.WindowManager.find_game_window")
    def test_detect_game_window_success(self, mock_find_window):
        """测试成功检测游戏窗口"""
        mock_window = GameWindow(
            hwnd=12345,
            title="崩坏：星穹铁道",
            rect=(0, 0, 1920, 1080),
            width=1920,
            height=1080,
            is_foreground=True,
        )
        mock_find_window.return_value = mock_window

        result = self.detector.detect_game_window()

        self.assertTrue(result)
        mock_find_window.assert_called_once()

    @patch("src.core.game_detector.WindowManager.find_game_window")
    def test_detect_game_window_failure(self, mock_find_window):
        """测试检测游戏窗口失败"""
        mock_find_window.return_value = None

        result = self.detector.detect_game_window()

        self.assertFalse(result)

    def test_capture_screenshot_success(self):
        """测试成功截取游戏截图"""
        mock_screenshot = np.zeros((1080, 1920, 3), dtype=np.uint8)
        with patch.object(
            self.detector.window_manager, "capture_window", return_value=mock_screenshot
        ):
            result = self.detector.capture_screenshot()

            self.assertIsNotNone(result)
            self.assertEqual(result.shape, (1080, 1920, 3))

    def test_capture_screenshot_no_window(self):
        """测试没有窗口时截取屏幕"""
        result = self.detector.capture_screenshot()
        self.assertIsNone(result)

    def test_identify_scene_main_menu(self):
        """测试识别主菜单场景"""
        mock_screenshot = np.zeros((100, 100, 3), dtype=np.uint8)
        mock_elements = [
            UIElement(
                name="main_menu_start_game",
                position=(100, 200),
                size=(50, 30),
                confidence=0.9,
                template_path="main_menu_start_game.png",
                scale_factor=1.0,
            )
        ]
        with patch.object(
            self.detector.template_matcher,
            "match_multiple_templates",
            return_value=mock_elements,
        ):
            scene = self.detector.detect_current_scene(mock_screenshot)
            self.assertEqual(scene, SceneType.MAIN_MENU)

    def test_identify_scene_unknown(self):
        """测试识别未知场景"""
        mock_screenshot = np.zeros((100, 100, 3), dtype=np.uint8)
        with patch.object(
            self.detector.template_matcher, "match_multiple_templates", return_value=[]
        ):
            scene = self.detector.detect_current_scene(mock_screenshot)
            self.assertEqual(scene, SceneType.GAME_WORLD)

    @patch("src.core.game_detector.TemplateMatcher.match_template")
    def test_find_ui_element_success(self, mock_match):
        """测试成功查找UI元素"""
        mock_element = UIElement(
            name="start_button",
            position=(150, 200),
            size=(50, 30),
            confidence=0.85,
            template_path="start_button.png",
            scale_factor=1.0,
        )
        mock_match.return_value = mock_element
        mock_image = np.zeros((1080, 1920, 3), dtype=np.uint8)

        result = self.detector.find_ui_element(mock_image, "start_button")

        self.assertIsNotNone(result)
        self.assertEqual(result.name, "start_button")
        self.assertEqual(result.position, (150, 200))
        self.assertEqual(result.confidence, 0.85)

    def test_find_ui_element_failure(self):
        """测试查找UI元素失败"""
        mock_screenshot = np.zeros((100, 100, 3), dtype=np.uint8)
        with patch.object(
            self.detector, "capture_screenshot", return_value=mock_screenshot
        ):
            with patch.object(
                self.detector.template_matcher, "match_template", return_value=None
            ):
                result = self.detector.find_ui_element("test_template")
                self.assertIsNone(result)

    def test_is_game_active_with_window(self):
        """测试游戏窗口激活状态检查"""
        mock_window = GameWindow(
            hwnd=12345,
            title="崩坏：星穹铁道",
            rect=(0, 0, 1920, 1080),
            width=1920,
            height=1080,
            is_foreground=True,
        )
        with patch.object(
            self.detector, "detect_game_window", return_value=mock_window
        ):
            result = self.detector.is_game_running()
            self.assertTrue(result)

    def test_is_game_active_without_window(self):
        """测试没有窗口时的激活状态检查"""
        result = self.detector.is_game_running()
        self.assertFalse(result)

    def test_get_game_status(self):
        """测试获取游戏状态信息"""
        mock_window = GameWindow(
            hwnd=12345,
            title="崩坏：星穹铁道",
            rect=(0, 0, 1920, 1080),
            width=1920,
            height=1080,
            is_foreground=True,
        )

        with patch.object(
            self.detector.window_manager, "find_game_window", return_value=mock_window
        ):
            info = self.detector.get_game_status()

            self.assertIsNotNone(info)
            self.assertIn("window_found", info)
            self.assertTrue(info["window_found"])

    def test_get_current_scene(self):
        """测试获取当前场景"""
        self.detector.current_scene = SceneType.COMBAT

        result = self.detector.current_scene

        self.assertEqual(result, SceneType.COMBAT)


class TestWindowManager(unittest.TestCase):
    """WindowManager类的单元测试"""

    def setUp(self):
        """测试前的设置"""
        self.window_manager = WindowManager()

    @patch("win32gui.EnumWindows")
    @patch("win32gui.IsWindowVisible")
    @patch("win32gui.GetWindowText")
    @patch("win32gui.GetWindowRect")
    @patch("win32gui.GetForegroundWindow")
    def test_find_game_window_success(
        self, mock_foreground, mock_rect, mock_text, mock_visible, mock_enum
    ):
        """测试成功查找游戏窗口"""

        def mock_enum_callback(callback, param):
            callback(12345, param)
            return True

        mock_enum.side_effect = mock_enum_callback
        mock_visible.return_value = True
        mock_text.return_value = "崩坏：星穹铁道"
        mock_rect.return_value = (0, 0, 1920, 1080)
        mock_foreground.return_value = 12345

        result = self.window_manager.find_game_window()

        self.assertIsNotNone(result)
        self.assertEqual(result.hwnd, 12345)
        self.assertEqual(result.title, "崩坏：星穹铁道")
        self.assertEqual(result.rect, (0, 0, 1920, 1080))
        self.assertTrue(result.is_foreground)

    @patch("win32gui.EnumWindows")
    def test_find_game_window_failure(self, mock_enum):
        """测试查找游戏窗口失败"""

        def mock_enum_callback(callback, param):
            # 不调用callback，模拟没有找到窗口
            return True

        mock_enum.side_effect = mock_enum_callback

        result = self.window_manager.find_game_window()

        self.assertIsNone(result)

    @patch("src.core.game_detector.WindowManager.capture_window")
    def test_capture_window(self, mock_capture):
        """测试窗口截图"""
        mock_window = GameWindow(
            hwnd=12345,
            title="崩坏：星穹铁道",
            rect=(0, 0, 1920, 1080),
            width=1920,
            height=1080,
            is_foreground=True,
        )

        # 模拟返回截图数据
        mock_image = np.zeros((1080, 1920, 3), dtype=np.uint8)
        mock_capture.return_value = mock_image

        result = self.window_manager.capture_window(mock_window)

        self.assertIsNotNone(result)
        self.assertEqual(result.shape, (1080, 1920, 3))


class TestTemplateMatcher(unittest.TestCase):
    """TemplateMatcher类的单元测试"""

    def setUp(self):
        """测试前的设置"""
        self.matcher = TemplateMatcher()

    @patch("pathlib.Path.exists")
    @patch("cv2.imread")
    def test_load_templates_success(self, mock_imread, mock_exists):
        """测试成功加载模板"""
        mock_exists.return_value = True
        mock_template = np.zeros((100, 100, 3), dtype=np.uint8)
        mock_imread.return_value = mock_template

        # 测试加载模板功能
        self.matcher.load_templates()

        # 验证模板缓存存在
        self.assertIsInstance(self.matcher.templates_cache, dict)

    @patch("pathlib.Path.exists")
    def test_load_templates_no_directory(self, mock_exists):
        """测试模板目录不存在"""
        mock_exists.return_value = False

        # 先清空缓存
        self.matcher.templates_cache = {}
        self.matcher.load_templates()

        self.assertEqual(len(self.matcher.templates_cache), 0)

    @patch("cv2.matchTemplate")
    @patch("cv2.minMaxLoc")
    def test_match_template_success(self, mock_minmax, mock_match):
        """测试成功匹配模板"""
        # 设置模板
        template = np.zeros((50, 50, 3), dtype=np.uint8)
        self.matcher.templates_cache["test_template"] = {
            "image": template,
            "path": "test_path",
            "category": "test",
            "threshold": 0.8,
            "original_size": (50, 50),
        }

        # 模拟匹配结果
        mock_result = np.array([[0.9]])
        mock_match.return_value = mock_result
        mock_minmax.return_value = (0.1, 0.9, (10, 10), (100, 100))

        image = np.zeros((200, 200, 3), dtype=np.uint8)
        result = self.matcher.match_template(image, "test_template")

        self.assertIsNotNone(result)
        self.assertEqual(result.name, "test_template")
        self.assertEqual(result.position, (100, 100))
        self.assertEqual(result.confidence, 0.9)

    def test_match_template_not_loaded(self):
        """测试匹配未加载的模板"""
        image = np.zeros((200, 200, 3), dtype=np.uint8)
        result = self.matcher.match_template(image, "nonexistent_template")

        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
