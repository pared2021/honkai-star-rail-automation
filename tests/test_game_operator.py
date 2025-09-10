"""GameOperator测试模块.

测试游戏操作器的各种功能。
"""

import asyncio
import pytest
import time
from unittest.mock import Mock, patch, AsyncMock
from typing import Tuple

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.core.game_operator import (
    GameOperator, 
    OperationConfig, 
    OperationResult, 
    ClickType, 
    WaitCondition,
    OperationMethod
)
from src.core.game_detector import GameDetector, UIElement
from src.core.sync_adapter import SyncAdapter


class TestGameOperator:
    """GameOperator测试类."""

    @pytest.fixture
    def mock_game_detector(self):
        """模拟游戏检测器."""
        detector = Mock(spec=GameDetector)
        detector.detect_ui_elements.return_value = [
            UIElement(
                name="test_button",
                position=(100, 100),
                size=(100, 50),
                confidence=0.9,
                template_path="test_button.png"
            )
        ]
        detector.capture_screen.return_value = b"fake_screenshot_data"
        return detector

    @pytest.fixture
    def mock_sync_adapter(self):
        """模拟同步适配器."""
        return Mock(spec=SyncAdapter)

    @pytest.fixture
    def game_operator(self, mock_game_detector, mock_sync_adapter):
        """创建游戏操作器实例."""
        return GameOperator(
            game_detector=mock_game_detector,
            sync_adapter=mock_sync_adapter
        )

    @pytest.mark.asyncio
    async def test_click_with_coordinates(self, game_operator):
        """测试使用坐标点击."""
        with patch('src.core.game_operator.pyautogui') as mock_pyautogui:
            mock_pyautogui.click = Mock()
            
            result = await game_operator.click((100, 200))
            
            assert result.success is True
            assert result.execution_time > 0
            assert result.metadata["position"] == (100, 200)
            assert result.metadata["click_type"] == "left"
            mock_pyautogui.click.assert_called_once_with(100, 200, button='left')

    @pytest.mark.asyncio
    async def test_click_with_ui_element(self, game_operator, mock_game_detector):
        """测试使用UI元素点击."""
        ui_element = UIElement(
            name="test_button",
            position=(100, 100),
            size=(100, 50),
            confidence=0.9,
            template_path="test_button.png"
        )
        
        with patch('src.core.game_operator.pyautogui') as mock_pyautogui:
            mock_pyautogui.click = Mock()
            
            result = await game_operator.click(ui_element)
            
            assert result.success is True
            assert result.metadata["position"] == (150, 125)
            mock_pyautogui.click.assert_called_once_with(150, 125, button='left')

    @pytest.mark.asyncio
    async def test_click_with_template_name(self, game_operator, mock_game_detector):
        """测试使用模板名称点击."""
        with patch('src.core.game_operator.pyautogui') as mock_pyautogui:
            mock_pyautogui.click = Mock()
            
            result = await game_operator.click("test_button")
            
            assert result.success is True
            assert result.metadata["position"] == (150, 125)
            # 可能会调用多次detect_ui_elements，所以只检查是否被调用
            assert mock_game_detector.detect_ui_elements.called
            mock_pyautogui.click.assert_called_once_with(150, 125, button='left')

    @pytest.mark.asyncio
    async def test_click_different_types(self, game_operator):
        """测试不同类型的点击."""
        with patch('src.core.game_operator.pyautogui') as mock_pyautogui:
            mock_pyautogui.click = Mock()
            mock_pyautogui.doubleClick = Mock()
            
            # 测试左键点击
            result = await game_operator.click((100, 100), ClickType.LEFT)
            assert result.success is True
            mock_pyautogui.click.assert_called_with(100, 100, button='left')
            
            # 测试右键点击
            result = await game_operator.click((100, 100), ClickType.RIGHT)
            assert result.success is True
            mock_pyautogui.click.assert_called_with(100, 100, button='right')
            
            # 测试双击
            result = await game_operator.click((100, 100), ClickType.DOUBLE)
            assert result.success is True
            mock_pyautogui.doubleClick.assert_called_with(100, 100)

    @pytest.mark.asyncio
    async def test_swipe_operation(self, game_operator):
        """测试滑动操作."""
        with patch('src.core.game_operator.pyautogui') as mock_pyautogui:
            mock_pyautogui.drag = Mock()
            
            result = await game_operator.swipe(
                start=(100, 100),
                end=(200, 200),
                duration=1.0
            )
            
            assert result.success is True
            assert result.metadata["start"] == (100, 100)
            assert result.metadata["end"] == (200, 200)
            assert result.metadata["duration"] == 1.0
            mock_pyautogui.drag.assert_called_once_with(100, 100, 200, 200, duration=1.0)

    @pytest.mark.asyncio
    async def test_input_text_without_target(self, game_operator):
        """测试无目标位置的文本输入."""
        with patch('src.core.game_operator.pyautogui') as mock_pyautogui:
            mock_pyautogui.typewrite = Mock()
            
            result = await game_operator.input_text("Hello World")
            
            assert result.success is True
            assert result.metadata["text"] == "Hello World"
            assert result.metadata["target"] is None
            mock_pyautogui.typewrite.assert_called_once_with("Hello World", interval=0.05)

    @pytest.mark.asyncio
    async def test_input_text_with_target(self, game_operator):
        """测试有目标位置的文本输入."""
        with patch('src.core.game_operator.pyautogui') as mock_pyautogui:
            mock_pyautogui.click = Mock()
            mock_pyautogui.typewrite = Mock()
            
            result = await game_operator.input_text("Hello World", target=(100, 100))
            
            assert result.success is True
            assert result.metadata["text"] == "Hello World"
            assert result.metadata["target"] == "(100, 100)"
            mock_pyautogui.click.assert_called_once_with(100, 100, button='left')
            mock_pyautogui.typewrite.assert_called_once_with("Hello World", interval=0.05)

    @pytest.mark.asyncio
    async def test_wait_for_ui_element_appears(self, game_operator, mock_game_detector):
        """测试等待UI元素出现."""
        # 模拟元素在第二次检测时出现
        mock_game_detector.detect_ui_elements.side_effect = [
            [],  # 第一次检测：未找到
            [UIElement(
                name="target_element",
                position=(100, 100),
                size=(50, 50),
                confidence=0.9,
                template_path="target.png"
            )]  # 第二次检测：找到
        ]
        
        result = await game_operator.wait_for_condition(
            condition=WaitCondition.UI_ELEMENT_APPEAR,
            condition_params={"element_name": "target_element"},
            timeout=5.0
        )
        
        assert result.success is True
        assert result.execution_time > 0
        assert mock_game_detector.detect_ui_elements.call_count == 2

    @pytest.mark.asyncio
    async def test_wait_for_ui_element_timeout(self, game_operator, mock_game_detector):
        """测试等待UI元素超时."""
        # 模拟元素始终未找到
        mock_game_detector.detect_ui_elements.return_value = []
        
        result = await game_operator.wait_for_condition(
            condition=WaitCondition.UI_ELEMENT_APPEAR,
            condition_params={"element_name": "missing_element"},
            timeout=1.0
        )
        
        assert result.success is False
        assert result.execution_time >= 1.0
        assert mock_game_detector.detect_ui_elements.call_count >= 1

    @pytest.mark.asyncio
    async def test_operation_with_screenshots(self, game_operator):
        """测试带截图的操作."""
        config = OperationConfig(
            screenshot_before=True,
            screenshot_after=True
        )
        
        with patch('src.core.game_operator.pyautogui') as mock_pyautogui:
            mock_pyautogui.click = Mock()
            
            result = await game_operator.click((100, 100), config=config)
            
            assert result.success is True
            assert result.screenshot_before == b"fake_screenshot_data"
            assert result.screenshot_after == b"fake_screenshot_data"

    @pytest.mark.asyncio
    async def test_operation_retry_mechanism(self, game_operator):
        """测试重试机制."""
        config = OperationConfig(
            retry_count=3,
            retry_delay=0.1
        )
        
        with patch('src.core.game_operator.pyautogui') as mock_pyautogui:
            # 模拟前两次失败，第三次成功
            mock_pyautogui.click = Mock(side_effect=[Exception("Failed"), Exception("Failed"), None])
            
            result = await game_operator.click((100, 100), config=config)
            
            # 当前实现有重试逻辑，第三次会成功
            assert result.success is True
            assert mock_pyautogui.click.call_count == 3

    def test_operation_history(self, game_operator):
        """测试操作历史记录."""
        # 初始状态应该为空
        history = game_operator.get_operation_history()
        assert len(history) == 0
        
        # 清空历史
        game_operator.clear_operation_history()
        history = game_operator.get_operation_history()
        assert len(history) == 0

    def test_config_management(self, game_operator):
        """测试配置管理."""
        # 获取默认配置
        default_config = game_operator.get_default_config()
        assert isinstance(default_config, OperationConfig)
        
        # 设置新的默认配置
        new_config = OperationConfig(
            timeout=60.0,
            retry_count=5,
            screenshot_before=True
        )
        game_operator.set_default_config(new_config)
        
        # 验证配置已更新
        updated_config = game_operator.get_default_config()
        assert updated_config.timeout == 60.0
        assert updated_config.retry_count == 5
        assert updated_config.screenshot_before is True

    @pytest.mark.asyncio
    async def test_click_target_not_found(self, game_operator, mock_game_detector):
        """测试点击目标未找到的情况."""
        # 模拟检测不到UI元素
        mock_game_detector.detect_ui_elements.return_value = []
        
        result = await game_operator.click("nonexistent_button")
        
        assert result.success is False
        assert "无法解析目标位置" in result.error_message

    @pytest.mark.asyncio
    async def test_swipe_target_not_found(self, game_operator, mock_game_detector):
        """测试滑动目标未找到的情况."""
        # 模拟检测不到UI元素
        mock_game_detector.detect_ui_elements.return_value = []
        
        result = await game_operator.swipe("start_button", "end_button")
        
        assert result.success is False
        assert "无法解析滑动位置" in result.error_message

    @pytest.mark.asyncio
    async def test_custom_wait_condition(self, game_operator):
        """测试自定义等待条件."""
        # 创建一个简单的自定义条件函数
        call_count = 0
        
        async def custom_condition():
            nonlocal call_count
            call_count += 1
            return call_count >= 2  # 第二次调用时返回True
        
        result = await game_operator.wait_for_condition(
            WaitCondition.CUSTOM,
            {"custom_function": custom_condition},
            timeout=5.0
        )
        
        assert result.success is True
        assert call_count >= 2


class TestOperationConfig:
    """OperationConfig测试类."""

    def test_default_config(self):
        """测试默认配置."""
        config = OperationConfig()
        
        assert config.method == OperationMethod.AUTO
        assert config.timeout == 30.0
        assert config.retry_count == 3
        assert config.retry_delay == 1.0
        assert config.verify_result is True
        assert config.screenshot_before is False
        assert config.screenshot_after is False

    def test_custom_config(self):
        """测试自定义配置."""
        config = OperationConfig(
            method=OperationMethod.WIN32_API,
            timeout=60.0,
            retry_count=5,
            retry_delay=2.0,
            verify_result=False,
            screenshot_before=True,
            screenshot_after=True
        )
        
        assert config.method == OperationMethod.WIN32_API
        assert config.timeout == 60.0
        assert config.retry_count == 5
        assert config.retry_delay == 2.0
        assert config.verify_result is False
        assert config.screenshot_before is True
        assert config.screenshot_after is True


class TestOperationResult:
    """OperationResult测试类."""

    def test_successful_result(self):
        """测试成功结果."""
        result = OperationResult(
            success=True,
            execution_time=1.5,
            metadata={"test": "value"}
        )
        
        assert result.success is True
        assert result.execution_time == 1.5
        assert result.error_message == ""
        assert result.metadata["test"] == "value"

    def test_failed_result(self):
        """测试失败结果."""
        result = OperationResult(
            success=False,
            execution_time=0.5,
            error_message="Operation failed"
        )
        
        assert result.success is False
        assert result.execution_time == 0.5
        assert result.error_message == "Operation failed"
        assert result.metadata == {}


if __name__ == "__main__":
    # 运行测试
    pytest.main(["-v", __file__])