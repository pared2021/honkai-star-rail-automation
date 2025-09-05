"""GameDetector模块单元测试。"""

from pathlib import Path
import unittest
from unittest.mock import MagicMock, Mock, patch

import numpy as np

from src.core.game_detector import (
    GameDetector,
    GameWindow,
    SceneType,
    TemplateInfo,
    TemplateMatcher,
    UIElement,
    WindowManager,
)


class TestTemplateMatcher(unittest.TestCase):
    """TemplateMatcher测试类。"""

    def setUp(self):
        """设置测试环境。"""
        self.matcher = TemplateMatcher()

    def test_init(self):
        """测试初始化。"""
        self.assertIsInstance(self.matcher.template_info_cache, dict)
        self.assertEqual(len(self.matcher.template_info_cache), 0)

    @patch("os.path.exists")
    @patch("cv2.imread")
    def test_load_template_success(self, mock_imread, mock_exists):
        """测试成功加载模板。"""
        # 模拟文件存在
        mock_exists.return_value = True
        # 模拟图像数据
        mock_image = np.zeros((100, 100, 3), dtype=np.uint8)
        mock_imread.return_value = mock_image

        template_info = self.matcher.load_template("test.png", 0.8)

        self.assertIsNotNone(template_info)
        self.assertEqual(template_info.name, "test")
        self.assertEqual(template_info.threshold, 0.8)
        self.assertEqual(template_info.path, "test.png")
        np.testing.assert_array_equal(template_info.image, mock_image)

    @patch("cv2.imread")
    def test_load_template_failure(self, mock_imread):
        """测试加载模板失败。"""
        mock_imread.return_value = None

        template_info = self.matcher.load_template("nonexistent.png")

        self.assertIsNone(template_info)

    @patch("os.path.exists")
    @patch("os.listdir")
    def test_load_templates_directory_not_found(self, mock_listdir, mock_exists):
        """测试目录不存在的情况。"""
        mock_exists.return_value = False

        self.matcher.load_templates("/nonexistent/path")

        mock_listdir.assert_not_called()

    @patch("cv2.matchTemplate")
    @patch("cv2.minMaxLoc")
    def test_match_template_success(self, mock_minmaxloc, mock_matchtemplate):
        """测试模板匹配成功。"""
        # 设置模拟数据
        screenshot = np.zeros((200, 200, 3), dtype=np.uint8)
        template_image = np.zeros((50, 50, 3), dtype=np.uint8)

        # 创建模板信息
        template_info = TemplateInfo(
            name="test_template", image=template_image, threshold=0.8, path="test.png"
        )
        self.matcher.template_info_cache["test_template"] = template_info

        # 模拟匹配结果
        mock_result = np.array([[0.9]])
        mock_matchtemplate.return_value = mock_result
        mock_minmaxloc.return_value = (0.5, 0.9, (10, 20), (10, 20))

        element = self.matcher.match_template(screenshot, "test_template")

        self.assertIsNotNone(element)
        self.assertEqual(element.name, "test_template")
        self.assertEqual(element.position, (10, 20))
        self.assertEqual(element.confidence, 0.9)

    def test_match_template_not_found(self):
        """测试模板不存在的情况。"""
        screenshot = np.zeros((200, 200, 3), dtype=np.uint8)

        element = self.matcher.match_template(screenshot, "nonexistent")

        self.assertIsNone(element)


class TestWindowManager(unittest.TestCase):
    """WindowManager测试类。"""

    def setUp(self):
        """设置测试环境。"""
        self.window_manager = WindowManager()

    @patch("src.core.game_detector.win32gui")
    def test_find_game_windows_success(self, mock_win32gui):
        """测试成功找到游戏窗口。"""
        # 模拟Windows API调用
        mock_win32gui.EnumWindows = Mock()
        mock_win32gui.GetWindowText.return_value = "Test Game"
        mock_win32gui.GetWindowRect.return_value = (0, 0, 800, 600)
        mock_win32gui.IsWindowVisible.return_value = True
        mock_win32gui.GetForegroundWindow.return_value = 12345

        # 模拟枚举窗口的回调
        def mock_enum_windows(callback, lparam):
            callback(12345, lparam)
            return True

        mock_win32gui.EnumWindows.side_effect = mock_enum_windows

        windows = self.window_manager.find_game_windows(["Test Game"])

        self.assertEqual(len(windows), 1)
        window = windows[0]
        self.assertEqual(window.hwnd, 12345)
        self.assertEqual(window.title, "Test Game")
        self.assertEqual(window.rect, (0, 0, 800, 600))
        self.assertEqual(window.width, 800)
        self.assertEqual(window.height, 600)
        self.assertTrue(window.is_foreground)

    @patch("src.core.game_detector.win32gui", None)
    def test_find_game_windows_no_win32gui(self):
        """测试在没有win32gui的情况下。"""
        windows = self.window_manager.find_game_windows(["Test Game"])

        self.assertEqual(len(windows), 0)


class TestGameDetector(unittest.TestCase):
    """GameDetector测试类。"""

    def setUp(self):
        """设置测试环境。"""
        with patch("src.core.game_detector.ConfigManager"):
            self.detector = GameDetector()

    def test_init(self):
        """测试初始化。"""
        self.assertIsNotNone(self.detector.template_matcher)
        self.assertIsNotNone(self.detector.window_manager)
        self.assertEqual(self.detector.current_scene, SceneType.UNKNOWN)

    @patch.object(WindowManager, "find_game_windows")
    def test_is_game_running_true(self, mock_find_windows):
        """测试游戏正在运行。"""
        mock_window = GameWindow(
            hwnd=12345,
            title="Test Game",
            rect=(0, 0, 800, 600),
            width=800,
            height=600,
            is_foreground=True,
        )
        mock_find_windows.return_value = [mock_window]

        result = self.detector.is_game_running()

        self.assertTrue(result)

    @patch.object(WindowManager, "find_game_windows")
    def test_is_game_running_false(self, mock_find_windows):
        """测试游戏未运行。"""
        mock_find_windows.return_value = []

        result = self.detector.is_game_running()

        self.assertFalse(result)

    @patch.object(WindowManager, "capture_window")
    @patch.object(TemplateMatcher, "match_template")
    def test_detect_ui_elements(self, mock_match, mock_capture):
        """测试UI元素检测。"""
        # 模拟截图
        mock_screenshot = np.zeros((600, 800, 3), dtype=np.uint8)
        mock_capture.return_value = mock_screenshot

        # 模拟匹配结果
        mock_element = UIElement(
            name="test_button",
            position=(100, 200),
            size=(50, 30),
            confidence=0.9,
            template_path="test.png",
        )
        mock_match.return_value = mock_element

        # 设置游戏窗口
        self.detector.game_window = GameWindow(
            hwnd=12345,
            title="Test Game",
            rect=(0, 0, 800, 600),
            width=800,
            height=600,
            is_foreground=True,
        )

        elements = self.detector.detect_ui_elements(["test_button"])

        self.assertEqual(len(elements), 1)
        self.assertEqual(elements[0].name, "test_button")
        self.assertEqual(elements[0].confidence, 0.9)

    def test_detect_ui_elements_no_window(self):
        """测试没有游戏窗口时的UI元素检测。"""
        self.detector.game_window = None

        elements = self.detector.detect_ui_elements(["test_button"])

        self.assertEqual(len(elements), 0)


class TestUIElement(unittest.TestCase):
    """UIElement测试类。"""

    def setUp(self):
        """设置测试环境。"""
        self.element = UIElement(
            name="test_element",
            position=(100, 200),
            size=(50, 30),
            confidence=0.9,
            template_path="test.png",
        )

    def test_center_property(self):
        """测试中心点属性。"""
        center = self.element.center
        self.assertEqual(center, (125, 215))

    def test_width_property(self):
        """测试宽度属性。"""
        self.assertEqual(self.element.width, 50)

    def test_height_property(self):
        """测试高度属性。"""
        self.assertEqual(self.element.height, 30)

    def test_top_left_property(self):
        """测试左上角属性。"""
        self.assertEqual(self.element.top_left, (100, 200))

    def test_bottom_right_property(self):
        """测试右下角属性。"""
        self.assertEqual(self.element.bottom_right, (150, 230))


if __name__ == "__main__":
    unittest.main()
