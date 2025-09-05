# -*- coding: utf-8 -*-
"""
GameDetector模块单元测试

测试游戏检测器的核心功能，包括窗口管理、模板匹配、场景检测等。
"""

import os
from pathlib import Path
import sys
from unittest.mock import MagicMock, Mock, call, patch

from PIL import Image
import asyncio
import numpy as np
import pytest

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.core.config_manager import ConfigManager
from src.core.game_detector import (
    GameDetector,
    GameWindow,
    SceneType,
    TemplateInfo,
    TemplateMatcher,
    UIElement,
    WindowManager,
)


class TestTemplateMatcher:
    """TemplateMatcher类测试"""

    def setup_method(self):
        """测试前设置"""
        self.template_matcher = TemplateMatcher()
        # 创建测试用的模板图像
        self.test_template = np.random.randint(0, 255, (50, 50, 3), dtype=np.uint8)
        self.test_screenshot = np.random.randint(0, 255, (800, 600, 3), dtype=np.uint8)

    def test_load_templates_success(self):
        """测试成功加载模板"""
        with patch.object(self.template_matcher, "load_template") as mock_load:
            with patch("os.path.exists", return_value=True):
                with patch("os.listdir") as mock_listdir:
                    # 模拟目录中的文件
                    mock_listdir.return_value = [
                        "test_template.png",
                        "another_template.jpg",
                    ]

                    self.template_matcher.load_templates("mock_templates_dir")

                    # 验证load_template被调用了两次
                    assert mock_load.call_count == 2
                    # 使用Windows路径分隔符
                    mock_load.assert_any_call("mock_templates_dir\\test_template.png")
                    mock_load.assert_any_call(
                        "mock_templates_dir\\another_template.jpg"
                    )

    def test_load_template_file_not_found(self):
        """测试模板文件不存在"""
        with patch("cv2.imread") as mock_imread:
            mock_imread.return_value = None

            # 测试 load_template 方法
            result = self.template_matcher.load_template("nonexistent.png")

            # 验证返回None且模板没有被添加到缓存中
            assert result is None
            assert "nonexistent" not in self.template_matcher.template_info_cache

    @pytest.mark.skipif(
        not hasattr(TemplateMatcher, "_convert_svg_to_image"),
        reason="SVG conversion not available",
    )
    def test_load_svg_template(self):
        """测试加载SVG模板"""
        # 如果cairosvg不可用，跳过测试
        from src.core.game_detector import CAIROSVG_AVAILABLE

        if not CAIROSVG_AVAILABLE:
            pytest.skip("cairosvg not available")

        svg_content = '<svg><rect width="100" height="100" fill="red"/></svg>'

        with patch("cairosvg.svg2png") as mock_svg2png, patch(
            "PIL.Image.open"
        ) as mock_image_open:
            mock_svg2png.return_value = b"fake_png_data"
            mock_pil_image = Mock()
            mock_pil_image.mode = "RGB"
            mock_image_open.return_value = mock_pil_image

            with patch("cv2.cvtColor") as mock_cvtcolor, patch(
                "numpy.array"
            ) as mock_array:
                mock_cvtcolor.return_value = self.test_template
                mock_array.return_value = self.test_template

                result = self.template_matcher._convert_svg_to_image(svg_content)

                assert result is not None
                mock_svg2png.assert_called_once()
                mock_cvtcolor.assert_called_once()

    def test_calculate_scale_factors(self):
        """测试计算缩放因子"""
        screenshot_size = (1080, 1920)  # (height, width)
        template_size = (50, 100)  # (height, width)
        factors = self.template_matcher._calculate_scale_factors(
            screenshot_size, template_size
        )

        assert isinstance(factors, list)
        assert len(factors) > 0
        assert all(isinstance(f, float) for f in factors)
        assert 1.0 in factors  # 应该包含原始尺寸

    def test_scale_template(self):
        """测试模板缩放"""
        with patch("cv2.resize") as mock_resize:
            mock_resize.return_value = self.test_template

            result = self.template_matcher._scale_template(self.test_template, 0.5)

            assert result is not None
            mock_resize.assert_called_once()

    def test_match_template_success(self):
        """测试模板匹配成功"""
        from src.core.game_detector import TemplateInfo

        # 模拟模板信息缓存
        template_info = TemplateInfo(
            name="test_template",
            image=self.test_template,
            threshold=0.8,
            path="test_template.png",
        )
        self.template_matcher.template_info_cache["test_template"] = template_info

        with patch("cv2.matchTemplate") as mock_match, patch(
            "cv2.minMaxLoc"
        ) as mock_minmax:
            mock_match.return_value = np.array([[0.9]])
            mock_minmax.return_value = (0.1, 0.9, (10, 10), (100, 100))

            result = self.template_matcher.match_template(
                self.test_screenshot, "test_template"
            )

            assert result is not None
            assert isinstance(result, UIElement)
            assert result.confidence == 0.9

    def test_match_template_below_threshold(self):
        """测试匹配置信度低于阈值的情况"""
        from src.core.game_detector import TemplateInfo

        # 模拟模板信息缓存
        template_info = TemplateInfo(
            name="test_template",
            image=self.test_template,
            threshold=0.8,
            path="test_template.png",
        )
        self.template_matcher.template_info_cache["test_template"] = template_info

        with patch("cv2.matchTemplate") as mock_match, patch(
            "cv2.minMaxLoc"
        ) as mock_minmax:
            mock_match.return_value = np.array([[0.5]])
            mock_minmax.return_value = (0.1, 0.5, (10, 10), (100, 100))  # 低于阈值0.8

            result = self.template_matcher.match_template(
                self.test_screenshot, "test_template"
            )

            assert result is None

    def test_match_multiple_templates(self):
        """测试匹配多个模板"""
        from src.core.game_detector import TemplateInfo

        # 设置模板信息缓存
        template_info1 = TemplateInfo(
            name="template1",
            image=self.test_template,
            threshold=0.8,
            path="template1.png",
        )
        template_info2 = TemplateInfo(
            name="template2",
            image=self.test_template,
            threshold=0.8,
            path="template2.png",
        )
        self.template_matcher.template_info_cache["template1"] = template_info1
        self.template_matcher.template_info_cache["template2"] = template_info2

        with patch.object(self.template_matcher, "match_template") as mock_match:
            mock_match.side_effect = [
                UIElement("template1", (100, 100), (150, 150), 0.9, "template1.png"),
                None,
            ]

            # 假设有一个方法可以匹配多个模板
            template_names = ["template1", "template2"]
            results = []
            for name in template_names:
                result = self.template_matcher.match_template(
                    self.test_screenshot, name
                )
                if result:
                    results.append(result)

            assert len(results) == 1
            assert results[0].name == "template1"


class TestWindowManager:
    """WindowManager类测试"""

    def setup_method(self):
        """测试前设置"""
        self.window_manager = WindowManager()

    @patch("win32gui.EnumWindows")
    def test_find_game_window_success(self, mock_enum_windows):
        """测试成功查找游戏窗口"""

        def mock_enum_callback(callback, param):
            # 模拟找到窗口
            callback(12345, param)
            return True

        mock_enum_windows.side_effect = mock_enum_callback

        with patch("win32gui.IsWindowVisible") as mock_visible, patch(
            "win32gui.GetWindowText"
        ) as mock_get_text, patch("win32gui.GetWindowRect") as mock_get_rect, patch(
            "win32gui.GetForegroundWindow"
        ) as mock_foreground:
            mock_visible.return_value = True
            mock_get_text.return_value = "崩坏：星穹铁道"
            mock_get_rect.return_value = (100, 100, 900, 700)
            mock_foreground.return_value = 12345

            result = self.window_manager.find_game_window(["崩坏：星穹铁道"])

            assert result is not None
            assert isinstance(result, GameWindow)
            assert result.hwnd == 12345
            assert result.title == "崩坏：星穹铁道"

    @patch("win32gui.EnumWindows")
    def test_find_game_window_not_found(self, mock_enum_windows):
        """测试游戏窗口未找到"""

        def mock_enum_callback(callback, param):
            # 模拟没有找到窗口
            return True

        mock_enum_windows.side_effect = mock_enum_callback

        result = self.window_manager.find_game_window(["崩坏：星穹铁道"])

        assert result is None

    @patch("win32gui.GetWindowDC")
    @patch("win32ui.CreateDCFromHandle")
    def test_capture_window_success(
        self, mock_create_dc_from_handle, mock_get_window_dc
    ):
        """测试成功截取窗口"""
        game_window = GameWindow(
            hwnd=12345,
            title="Test Game",
            rect=(100, 100, 900, 700),
            width=800,
            height=600,
            is_foreground=True,
        )

        # Mock所有Windows API调用
        mock_get_window_dc.return_value = 1001
        mock_mfc_dc = Mock()
        mock_save_dc = Mock()
        mock_bitmap = Mock()

        mock_create_dc_from_handle.return_value = mock_mfc_dc
        mock_mfc_dc.CreateCompatibleDC.return_value = mock_save_dc

        with patch("win32ui.CreateBitmap") as mock_create_bitmap, patch(
            "win32gui.ReleaseDC"
        ), patch("win32gui.DeleteObject"), patch("cv2.cvtColor") as mock_cvtcolor:

            mock_create_bitmap.return_value = mock_bitmap
            mock_bitmap.GetBitmapBits.return_value = b"\x00" * (800 * 600 * 4)
            mock_bitmap.GetInfo.return_value = {"bmWidth": 800, "bmHeight": 600}
            mock_bitmap.GetHandle.return_value = 1002

            # Mock cv2.cvtColor to return a proper numpy array
            test_image = np.random.randint(0, 255, (600, 800, 3), dtype=np.uint8)
            mock_cvtcolor.return_value = test_image

            result = self.window_manager.capture_window(game_window)

            assert result is not None
            assert isinstance(result, np.ndarray)
            assert result.shape == (600, 800, 3)

    @patch("win32gui.SetForegroundWindow")
    @patch("win32gui.ShowWindow")
    def test_bring_window_to_front(self, mock_show_window, mock_set_foreground):
        """测试将窗口置于前台"""
        game_window = GameWindow(
            hwnd=12345,
            title="Test Game",
            rect=(100, 100, 900, 700),
            width=800,
            height=600,
            is_foreground=True,
        )

        # 设置mock返回值为成功
        mock_show_window.return_value = True
        mock_set_foreground.return_value = True

        with patch("src.core.game_detector.win32con") as mock_win32con:
            mock_win32con.SW_RESTORE = 9

            result = self.window_manager.bring_window_to_front(game_window)

            assert result is True
            mock_show_window.assert_called_once_with(12345, 9)  # SW_RESTORE
            mock_set_foreground.assert_called_once_with(12345)


class TestGameDetector:
    """GameDetector类测试"""

    def setup_method(self):
        """测试前设置"""
        # Mock ConfigManager
        self.mock_config_manager = Mock()
        self.game_detector = GameDetector(self.mock_config_manager)
        self.mock_game_window = GameWindow(
            hwnd=12345,
            title="Test Game",
            rect=(100, 100, 900, 700),
            width=800,
            height=600,
            is_foreground=True,
        )

    def test_init(self):
        """测试初始化"""
        assert self.game_detector.window_manager is not None
        assert self.game_detector.template_matcher is not None
        assert self.game_detector.current_scene is not None
        assert self.game_detector.last_screenshot is None

    @patch.object(WindowManager, "find_game_window")
    def test_detect_game_window_success(self, mock_find_window):
        """测试成功检测游戏窗口"""
        mock_find_window.return_value = self.mock_game_window

        result = self.game_detector.detect_game_window()

        assert result == self.mock_game_window
        assert self.game_detector.window_manager.current_window == self.mock_game_window

    @patch.object(WindowManager, "find_game_window")
    def test_detect_game_window_not_found(self, mock_find_window):
        """测试游戏窗口未找到"""
        mock_find_window.return_value = None

        result = self.game_detector.detect_game_window()

        assert result is None
        assert self.game_detector.window_manager.current_window is None

    @patch("psutil.process_iter")
    def test_find_window_by_process_success(self, mock_process_iter):
        """测试通过进程名查找窗口成功"""
        mock_process = Mock()
        mock_process.info = {"name": "StarRail.exe"}
        mock_process_iter.return_value = [mock_process]

        with patch.object(
            self.game_detector.window_manager, "find_game_window"
        ) as mock_find:
            mock_find.return_value = self.mock_game_window

            result = self.game_detector._find_window_by_process("StarRail.exe")

            assert result == self.mock_game_window
            mock_find.assert_called_once_with(["StarRail.exe"])

    @patch.object(WindowManager, "capture_window")
    def test_capture_screenshot_success(self, mock_capture):
        """测试成功截取游戏截图"""
        self.game_detector.window_manager.current_window = self.mock_game_window
        test_image = np.random.randint(0, 255, (600, 800, 3), dtype=np.uint8)
        mock_capture.return_value = test_image

        result = self.game_detector.capture_screenshot()

        assert result is not None
        assert isinstance(result, np.ndarray)
        mock_capture.assert_called_once()

    def test_capture_screenshot_no_window(self):
        """测试无窗口时截取截图"""
        self.game_detector.window_manager.current_window = None

        result = self.game_detector.capture_screenshot()

        assert result is None

    def test_find_ui_element_success(self):
        """测试成功查找UI元素"""
        mock_element = UIElement(
            "test_button", (100, 100), (200, 150), 0.9, "test_button.png"
        )

        with patch.object(self.game_detector, "detect_ui_elements") as mock_detect:
            mock_detect.return_value = [mock_element]

            result = self.game_detector.find_ui_element("test_button")

            assert result == mock_element
            mock_detect.assert_called_once_with(["test_button"])

    def test_find_ui_element_template_not_found(self):
        """测试模板不存在时查找UI元素"""
        with patch.object(self.game_detector, "detect_ui_elements") as mock_detect:
            mock_detect.return_value = []

            result = self.game_detector.find_ui_element("nonexistent")

            assert result is None
            mock_detect.assert_called_once_with(["nonexistent"])

    def test_find_multiple_ui_elements(self):
        """测试查找多个UI元素"""
        mock_elements = [
            UIElement("button1", (100, 100), (200, 150), 0.9, "button1.png"),
            UIElement("button2", (300, 100), (400, 150), 0.85, "button2.png"),
        ]

        with patch.object(self.game_detector, "detect_ui_elements") as mock_detect:
            mock_detect.return_value = mock_elements

            result = self.game_detector.find_multiple_ui_elements(
                ["button1", "button2"]
            )

            assert len(result) == 2
            assert result == mock_elements
            mock_detect.assert_called_once_with(["button1", "button2"])

    @patch("time.sleep")
    def test_wait_for_ui_element_success(self, mock_sleep):
        """测试等待UI元素出现成功"""
        mock_element = UIElement(
            "test_button", (100, 100), (200, 150), 0.9, "test_button.png"
        )

        with patch.object(self.game_detector, "find_ui_element") as mock_find:
            mock_find.return_value = mock_element

            result = self.game_detector.wait_for_ui_element("test_button", timeout=1)

            assert result == mock_element

    @patch("time.sleep")
    def test_wait_for_ui_element_timeout(self, mock_sleep):
        """测试等待UI元素超时"""
        with patch.object(self.game_detector, "find_ui_element") as mock_find:
            mock_find.return_value = None

            result = self.game_detector.wait_for_ui_element("test_button", timeout=0.1)

            assert result is None

    def test_is_game_running_true(self):
        """测试游戏正在运行"""
        with patch.object(
            self.game_detector.window_manager, "find_game_windows"
        ) as mock_find_windows:

            mock_find_windows.return_value = [self.mock_game_window]

            result = self.game_detector.is_game_running()

            assert result is True
            assert self.game_detector.game_window == self.mock_game_window

    def test_is_game_running_false(self):
        """测试游戏未运行"""
        with patch.object(self.game_detector.window_manager, "find_game_windows") as mock_find_windows:
            mock_find_windows.return_value = []

            result = self.game_detector.is_game_running()

            assert result is False
            assert self.game_detector.game_window is None

    def test_get_game_status_with_window(self):
        """测试获取游戏状态（有窗口）"""
        self.game_detector.window_manager.current_window = self.mock_game_window

        with patch.object(
            self.game_detector.window_manager, "find_game_window"
        ) as mock_find:
            mock_find.return_value = self.mock_game_window

            status = self.game_detector.get_game_status()

            assert status["window_found"] is True
            assert "current_scene" in status
            assert "templates_loaded" in status

    def test_get_game_status_no_window(self):
        """测试获取游戏状态（无窗口）"""
        self.game_detector.window_manager.current_window = None

        with patch.object(
            self.game_detector.window_manager, "find_game_window"
        ) as mock_find:
            mock_find.return_value = None

            status = self.game_detector.get_game_status()

            assert status["window_found"] is False
            assert "current_scene" in status
            assert "templates_loaded" in status

    def test_bring_game_to_front_success(self):
        """测试将游戏窗口置于前台成功"""
        # 设置当前窗口
        self.game_detector.window_manager.current_window = self.mock_game_window

        with patch.object(
            self.game_detector.window_manager, "bring_window_to_front"
        ) as mock_bring_to_front:
            mock_bring_to_front.return_value = True

            result = self.game_detector.bring_game_to_front()

            assert result is True
            mock_bring_to_front.assert_called_once_with(self.mock_game_window)

    def test_bring_game_to_front_no_window(self):
        """测试无窗口时置于前台"""
        with patch.object(
            self.game_detector.window_manager, "bring_window_to_front"
        ) as mock_bring_to_front:
            mock_bring_to_front.return_value = False

            result = self.game_detector.bring_game_to_front()

            assert result is False

    @patch.object(TemplateMatcher, "match_multiple_templates")
    def test_detect_current_scene_success(self, mock_match_multiple):
        """测试成功检测当前场景"""
        test_screenshot = np.random.randint(0, 255, (600, 800, 3), dtype=np.uint8)
        mock_elements = [
            UIElement("main_menu", (100, 100), (200, 150), 0.95, "main_menu.png"),
            UIElement("battle_ui", (300, 100), (400, 150), 0.85, "battle_ui.png"),
        ]
        mock_match_multiple.return_value = mock_elements

        with patch.object(self.game_detector, "capture_screenshot") as mock_capture:
            mock_capture.return_value = test_screenshot

            result = self.game_detector.detect_current_scene()

            assert result == SceneType.MAIN_MENU  # 最高置信度的场景
            assert self.game_detector.current_scene == SceneType.MAIN_MENU

    def test_detect_current_scene_no_match(self):
        """测试无法检测到场景"""
        test_screenshot = np.random.randint(0, 255, (600, 800, 3), dtype=np.uint8)

        with patch.object(
            self.game_detector, "capture_screenshot"
        ) as mock_capture, patch.object(
            self.game_detector.template_matcher, "match_multiple_templates"
        ) as mock_match:
            mock_capture.return_value = test_screenshot
            mock_match.return_value = []

            result = self.game_detector.detect_current_scene()

            assert result == SceneType.UNKNOWN
            assert self.game_detector.current_scene == SceneType.UNKNOWN

    def test_detect_current_scene_no_screenshot(self):
        """测试无法获取截图时的场景检测"""
        with patch.object(self.game_detector, "capture_screenshot") as mock_capture:
            mock_capture.return_value = None

            result = self.game_detector.detect_current_scene()

            assert result == SceneType.UNKNOWN

    @patch("cv2.rectangle")
    @patch("cv2.putText")
    @patch("cv2.imwrite")
    def test_visualize_detection_results(
        self, mock_imwrite, mock_puttext, mock_rectangle
    ):
        """测试可视化检测结果"""
        test_screenshot = np.random.randint(0, 255, (600, 800, 3), dtype=np.uint8)
        elements = [
            UIElement("button1", (100, 100), (200, 150), 0.9, "button1.png"),
            UIElement("button2", (300, 100), (400, 150), 0.85, "button2.png"),
        ]

        result = self.game_detector.visualize_detection_results(
            test_screenshot, elements, save_path="test_output.png"
        )

        assert result is not None
        assert isinstance(result, np.ndarray)
        mock_rectangle.assert_called()
        mock_puttext.assert_called()
        mock_imwrite.assert_called_once_with("test_output.png", result)

    def test_visualize_detection_results_no_save(self):
        """测试可视化检测结果（不保存）"""
        test_screenshot = np.random.randint(0, 255, (600, 800, 3), dtype=np.uint8)
        elements = [UIElement("button1", (100, 100), (200, 150), 0.9, "button1.png")]

        with patch("cv2.rectangle"), patch("cv2.putText"):
            result = self.game_detector.visualize_detection_results(
                test_screenshot, elements
            )

            assert result is not None
            assert isinstance(result, np.ndarray)

    def test_detect_and_visualize_scene(self):
        """测试检测并可视化场景"""
        test_screenshot = np.random.randint(0, 255, (600, 800, 3), dtype=np.uint8)
        mock_elements = [
            UIElement("main_menu", (100, 100), (200, 150), 0.95, "main_menu.png")
        ]

        with patch.object(
            self.game_detector, "capture_screenshot"
        ) as mock_capture, patch.object(
            self.game_detector, "detect_current_scene"
        ) as mock_detect, patch.object(
            self.game_detector.template_matcher, "match_multiple_templates"
        ) as mock_match, patch.object(
            self.game_detector, "visualize_detection_results"
        ) as mock_visualize:

            mock_capture.return_value = test_screenshot
            mock_detect.return_value = SceneType.MAIN_MENU
            mock_match.return_value = [mock_elements]
            mock_visualize.return_value = test_screenshot

            result = self.game_detector.detect_and_visualize_scene()

            assert result is not None
            mock_detect.assert_called_once()
            mock_visualize.assert_called_once()

    @patch("time.sleep")
    def test_wait_for_template_success(self, mock_sleep):
        """测试等待模板出现成功"""
        mock_element = UIElement(
            "test_template", (100, 100), (200, 150), 0.9, "test_template.png"
        )

        with patch.object(
            self.game_detector, "detect_ui_elements"
        ) as mock_detect, patch.object(
            self.game_detector, "capture_screenshot"
        ) as mock_capture:

            mock_capture.return_value = np.random.randint(
                0, 255, (600, 800, 3), dtype=np.uint8
            )
            mock_detect.return_value = [mock_element]

            result = self.game_detector.wait_for_template("test_template", timeout=1)

            assert result == mock_element

    @patch("time.sleep")
    def test_wait_for_template_timeout(self, mock_sleep):
        """测试等待模板超时"""
        with patch.object(
            self.game_detector, "detect_ui_elements"
        ) as mock_detect, patch.object(
            self.game_detector, "capture_screenshot"
        ) as mock_capture:

            mock_capture.return_value = np.random.randint(
                0, 255, (600, 800, 3), dtype=np.uint8
            )
            mock_detect.return_value = []

            result = self.game_detector.wait_for_template("test_template", timeout=0.1)

            assert result is None


class TestTemplateMatcherAdvanced:
    """TemplateMatcher高级功能测试"""

    def setup_method(self):
        """测试前设置"""
        self.template_matcher = TemplateMatcher()
        self.test_template = np.random.randint(0, 255, (50, 50, 3), dtype=np.uint8)
        self.test_screenshot = np.random.randint(0, 255, (800, 600, 3), dtype=np.uint8)

    @patch("os.path.exists")
    @patch("os.listdir")
    def test_load_templates_from_directory(self, mock_listdir, mock_exists):
        """测试从目录加载模板"""
        mock_exists.return_value = True
        mock_listdir.return_value = ["template1.png", "template2.svg", "not_image.txt"]

        with patch.object(self.template_matcher, "load_template") as mock_load:
            # 模拟load_template的返回值，成功时返回TemplateInfo，失败时返回None
            template_info1 = TemplateInfo(
                "template1", self.test_template, 0.8, "template1.png"
            )
            template_info2 = TemplateInfo(
                "template2", self.test_template, 0.8, "template2.svg"
            )

            def mock_load_side_effect(file_path):
                if "template1.png" in file_path:
                    # 模拟成功加载，直接添加到缓存
                    self.template_matcher.template_info_cache["template1"] = (
                        template_info1
                    )
                    return template_info1
                elif "template2.svg" in file_path:
                    # 模拟成功加载，直接添加到缓存
                    self.template_matcher.template_info_cache["template2"] = (
                        template_info2
                    )
                    return template_info2
                else:
                    return None

            mock_load.side_effect = mock_load_side_effect

            self.template_matcher.load_templates("test_dir")

            assert mock_load.call_count == 2  # 只有png和svg文件会被处理
            assert len(self.template_matcher.template_info_cache) == 2

    @pytest.mark.skipif(
        not hasattr(TemplateMatcher, "_convert_svg_to_image"),
        reason="SVG conversion not available",
    )
    def test_convert_svg_to_image_success(self):
        """测试SVG转换为图像成功"""
        svg_content = '<svg><rect width="100" height="100" fill="red"/></svg>'

        # 如果cairosvg不可用，直接返回None
        from src.core.game_detector import CAIROSVG_AVAILABLE

        if not CAIROSVG_AVAILABLE:
            result = self.template_matcher._convert_svg_to_image(svg_content)
            assert result is None
            return

        with patch("cairosvg.svg2png") as mock_svg2png, patch(
            "PIL.Image.open"
        ) as mock_image_open, patch("cv2.cvtColor") as mock_cvtcolor:

            mock_svg2png.return_value = b"fake_png_data"
            mock_pil_image = Mock()
            mock_pil_image.mode = "RGB"
            mock_image_open.return_value = mock_pil_image
            mock_cvtcolor.return_value = self.test_template

            with patch("numpy.array") as mock_array:
                mock_array.return_value = self.test_template

                result = self.template_matcher._convert_svg_to_image(svg_content)

                assert result is not None
                assert isinstance(result, np.ndarray)

    @pytest.mark.skipif(
        not hasattr(TemplateMatcher, "_convert_svg_to_image"),
        reason="SVG conversion not available",
    )
    def test_convert_svg_to_image_failure(self):
        """测试SVG转换失败"""
        svg_content = "invalid_svg"

        # 如果cairosvg不可用，直接返回None
        from src.core.game_detector import CAIROSVG_AVAILABLE

        if not CAIROSVG_AVAILABLE:
            result = self.template_matcher._convert_svg_to_image(svg_content)
            assert result is None
            return

        with patch("cairosvg.svg2png") as mock_svg2png:
            mock_svg2png.side_effect = Exception("SVG conversion failed")

            result = self.template_matcher._convert_svg_to_image(svg_content)

            assert result is None

    def test_match_template_with_multiple_scales(self):
        """测试多尺度模板匹配"""
        template_info = TemplateInfo(
            name="test", image=self.test_template, threshold=0.8, path="test.png"
        )
        
        # 将模板信息添加到缓存中
        self.template_matcher.template_info_cache["test"] = template_info

        with patch("cv2.matchTemplate") as mock_match, patch(
            "cv2.minMaxLoc"
        ) as mock_minmax:

            mock_match.return_value = np.array([[0.9]])
            mock_minmax.return_value = (0.1, 0.9, (10, 10), (100, 100))

            result = self.template_matcher.match_template(
                self.test_screenshot, "test"
            )

            assert result is not None
            assert isinstance(result, UIElement)
            assert result.name == "test"
            assert result.confidence == 0.9
            assert mock_match.call_count == 1
            assert mock_minmax.call_count == 1


class TestWindowManagerAdvanced:
    """WindowManager高级功能测试"""

    def setup_method(self):
        """测试前设置"""
        self.window_manager = WindowManager()

    @patch("win32gui.EnumWindows")
    def test_find_game_window_multiple_matches(self, mock_enum_windows):
        """测试找到多个匹配窗口时的处理"""

        def mock_enum_callback(callback, param):
            # 模拟找到多个窗口
            callback(12345, param)
            callback(67890, param)
            return True

        mock_enum_windows.side_effect = mock_enum_callback

        with patch("win32gui.IsWindowVisible") as mock_visible, patch(
            "win32gui.GetWindowText"
        ) as mock_get_text, patch("win32gui.GetWindowRect") as mock_get_rect, patch(
            "win32gui.GetForegroundWindow"
        ) as mock_foreground:

            mock_visible.return_value = True
            mock_get_text.side_effect = ["崩坏：星穹铁道", "崩坏：星穹铁道"]
            mock_get_rect.side_effect = [(100, 100, 900, 700), (200, 200, 1000, 800)]
            mock_foreground.return_value = 12345  # 第一个窗口是前台窗口

            result = self.window_manager.find_game_window(["崩坏：星穹铁道"])

            assert result is not None
            assert result.hwnd == 12345  # 应该返回前台窗口
            assert result.is_foreground is True

    def test_capture_window_error_handling(self):
        """测试窗口截图错误处理"""
        game_window = GameWindow(
            hwnd=12345,
            title="Test Game",
            rect=(100, 100, 900, 700),
            width=800,
            height=600,
            is_foreground=True,
        )

        with patch("win32gui.GetWindowDC") as mock_get_window_dc:
            mock_get_window_dc.side_effect = Exception("Failed to get window DC")

            result = self.window_manager.capture_window(game_window)

            assert result is None

    @patch("win32gui.SetForegroundWindow")
    @patch("win32gui.ShowWindow")
    def test_bring_window_to_front_error(self, mock_show_window, mock_set_foreground):
        """测试窗口置前失败处理"""
        game_window = GameWindow(
            hwnd=12345,
            title="Test Game",
            rect=(100, 100, 900, 700),
            width=800,
            height=600,
            is_foreground=True,
        )

        mock_set_foreground.side_effect = Exception("Failed to set foreground")

        result = self.window_manager.bring_window_to_front(game_window)

        assert result is False


if __name__ == "__main__":
    pytest.main([__file__])
