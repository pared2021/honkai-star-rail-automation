"""ConfigManager模块测试。

测试配置管理器的核心功能，包括配置加载、保存、验证、更新等。
"""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.core.config_manager import (
    AutomationConfig,
    ConfigManager,
    ConfigType,
    DetectionConfig,
    GameConfig,
    LoggingConfig,
    SystemConfig,
    UIConfig,
)


class TestConfigManager:
    """ConfigManager测试类。"""

    def setup_method(self):
        """测试前设置。"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = Path(self.temp_dir) / "test_config.json"
        self.config_manager = ConfigManager(str(self.config_file))

    def test_init_with_default_config(self):
        """测试使用默认配置初始化。"""
        manager = ConfigManager()
        assert manager.config_file == Path("config.json")
        assert len(manager._configs) == 6
        assert isinstance(manager.get_game_config(), GameConfig)
        assert isinstance(manager.get_ui_config(), UIConfig)
        assert isinstance(manager.get_detection_config(), DetectionConfig)
        assert isinstance(manager.get_automation_config(), AutomationConfig)
        assert isinstance(manager.get_logging_config(), LoggingConfig)
        assert isinstance(manager.get_system_config(), SystemConfig)

    def test_get_config_by_type(self):
        """测试按类型获取配置。"""
        game_config = self.config_manager.get_config(ConfigType.GAME)
        assert isinstance(game_config, GameConfig)
        assert game_config.window_title == "崩坏：星穹铁道"
        assert game_config.process_name == "StarRail.exe"

    def test_get_specific_configs(self):
        """测试获取特定类型配置。"""
        game_config = self.config_manager.get_game_config()
        assert game_config.screenshot_interval == 0.1
        assert game_config.template_threshold == 0.8

        ui_config = self.config_manager.get_ui_config()
        assert ui_config.template_dir == "templates"
        assert ui_config.visualization_enabled is True

        detection_config = self.config_manager.get_detection_config()
        assert detection_config.confidence_threshold == 0.8
        assert detection_config.scale_factors == [0.8, 0.9, 1.0, 1.1, 1.2]

        automation_config = self.config_manager.get_automation_config()
        assert automation_config.action_delay == 0.5
        assert automation_config.safe_mode_enabled is True

        logging_config = self.config_manager.get_logging_config()
        assert logging_config.level == "INFO"
        assert logging_config.file_enabled is True

        system_config = self.config_manager.get_system_config()
        assert system_config.work_dir == "."
        assert system_config.cache_enabled is True

    def test_set_config(self):
        """测试设置配置。"""
        new_game_config = GameConfig(
            window_title="新游戏",
            process_name="NewGame.exe",
            screenshot_interval=0.2
        )
        
        self.config_manager.set_config(ConfigType.GAME, new_game_config)
        
        retrieved_config = self.config_manager.get_game_config()
        assert retrieved_config.window_title == "新游戏"
        assert retrieved_config.process_name == "NewGame.exe"
        assert retrieved_config.screenshot_interval == 0.2

    def test_update_config(self):
        """测试更新配置字段。"""
        self.config_manager.update_config(
            ConfigType.GAME,
            window_title="更新的游戏",
            screenshot_interval=0.3
        )
        
        game_config = self.config_manager.get_game_config()
        assert game_config.window_title == "更新的游戏"
        assert game_config.screenshot_interval == 0.3
        # 其他字段应保持不变
        assert game_config.process_name == "StarRail.exe"

    def test_update_config_invalid_field(self):
        """测试更新不存在的配置字段。"""
        with patch.object(self.config_manager.logger, 'warning') as mock_warning:
            self.config_manager.update_config(
                ConfigType.GAME,
                invalid_field="value"
            )
            mock_warning.assert_called_once()

    def test_load_config_file_not_exists(self):
        """测试加载不存在的配置文件。"""
        non_existent_file = Path(self.temp_dir) / "non_existent.json"
        manager = ConfigManager(str(non_existent_file))
        
        # 应该使用默认配置
        assert manager.get_game_config().window_title == "崩坏：星穹铁道"

    def test_load_config_success(self):
        """测试成功加载配置文件。"""
        # 创建测试配置文件
        test_config = {
            "game": {
                "window_title": "测试游戏",
                "process_name": "TestGame.exe",
                "screenshot_interval": 0.5
            },
            "ui": {
                "template_dir": "test_templates",
                "visualization_enabled": False
            }
        }
        
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(test_config, f)
        
        # 重新加载配置
        result = self.config_manager.load_config()
        assert result is True
        
        # 验证配置已更新
        game_config = self.config_manager.get_game_config()
        assert game_config.window_title == "测试游戏"
        assert game_config.process_name == "TestGame.exe"
        assert game_config.screenshot_interval == 0.5
        
        ui_config = self.config_manager.get_ui_config()
        assert ui_config.template_dir == "test_templates"
        assert ui_config.visualization_enabled is False

    def test_load_config_invalid_json(self):
        """测试加载无效JSON配置文件。"""
        # 创建无效JSON文件
        with open(self.config_file, 'w') as f:
            f.write("invalid json content")
        
        result = self.config_manager.load_config()
        assert result is False

    def test_load_config_unknown_type(self):
        """测试加载包含未知配置类型的文件。"""
        test_config = {
            "unknown_type": {
                "some_field": "value"
            },
            "game": {
                "window_title": "测试游戏"
            }
        }
        
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(test_config, f)
        
        with patch.object(self.config_manager.logger, 'warning') as mock_warning:
            result = self.config_manager.load_config()
            assert result is True
            mock_warning.assert_called()

    def test_save_config_success(self):
        """测试成功保存配置文件。"""
        # 修改配置
        self.config_manager.update_config(
            ConfigType.GAME,
            window_title="保存测试游戏"
        )
        
        # 保存配置
        result = self.config_manager.save_config()
        assert result is True
        assert self.config_file.exists()
        
        # 验证保存的内容
        with open(self.config_file, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        
        assert saved_data["game"]["window_title"] == "保存测试游戏"

    def test_save_config_with_custom_file(self):
        """测试保存到自定义文件。"""
        custom_file = Path(self.temp_dir) / "custom_config.json"
        
        result = self.config_manager.save_config(str(custom_file))
        assert result is True
        assert custom_file.exists()
        assert self.config_manager.config_file == custom_file

    @patch('builtins.open', side_effect=PermissionError("Permission denied"))
    def test_save_config_permission_error(self, mock_open):
        """测试保存配置时权限错误。"""
        result = self.config_manager.save_config()
        assert result is False

    def test_get_value(self):
        """测试获取配置值。"""
        value = self.config_manager.get_value(ConfigType.GAME, "window_title")
        assert value == "崩坏：星穹铁道"
        
        # 测试不存在的字段
        value = self.config_manager.get_value(ConfigType.GAME, "non_existent", "default")
        assert value == "default"

    def test_set_value(self):
        """测试设置配置值。"""
        result = self.config_manager.set_value(ConfigType.GAME, "window_title", "新标题")
        assert result is True
        
        value = self.config_manager.get_value(ConfigType.GAME, "window_title")
        assert value == "新标题"
        
        # 测试设置不存在的字段
        result = self.config_manager.set_value(ConfigType.GAME, "non_existent", "value")
        assert result is False

    def test_reset_config_all(self):
        """测试重置所有配置。"""
        # 修改配置
        self.config_manager.update_config(ConfigType.GAME, window_title="修改的标题")
        
        # 重置所有配置
        self.config_manager.reset_config()
        
        # 验证配置已重置
        game_config = self.config_manager.get_game_config()
        assert game_config.window_title == "崩坏：星穹铁道"

    def test_reset_config_specific_type(self):
        """测试重置特定类型配置。"""
        # 修改游戏和UI配置
        self.config_manager.update_config(ConfigType.GAME, window_title="修改的游戏")
        self.config_manager.update_config(ConfigType.UI, template_dir="修改的目录")
        
        # 只重置游戏配置
        self.config_manager.reset_config(ConfigType.GAME)
        
        # 验证游戏配置已重置，UI配置未变
        game_config = self.config_manager.get_game_config()
        assert game_config.window_title == "崩坏：星穹铁道"
        
        ui_config = self.config_manager.get_ui_config()
        assert ui_config.template_dir == "修改的目录"

    def test_validate_config_valid(self):
        """测试验证有效配置。"""
        errors = self.config_manager.validate_config()
        assert len(errors) == 0

    def test_validate_config_invalid_game(self):
        """测试验证无效游戏配置。"""
        self.config_manager.update_config(
            ConfigType.GAME,
            screenshot_interval=-1,
            detection_timeout=0,
            template_threshold=1.5
        )
        
        errors = self.config_manager.validate_config()
        assert ConfigType.GAME.value in errors
        game_errors = errors[ConfigType.GAME.value]
        assert len(game_errors) == 3
        assert any("screenshot_interval必须大于0" in error for error in game_errors)
        assert any("detection_timeout必须大于0" in error for error in game_errors)
        assert any("template_threshold必须在0到1之间" in error for error in game_errors)

    def test_validate_config_invalid_detection(self):
        """测试验证无效检测配置。"""
        detection_config = self.config_manager.get_detection_config()
        detection_config.scale_factors = []
        
        errors = self.config_manager.validate_config()
        assert ConfigType.DETECTION.value in errors
        
        # 测试负数scale_factors
        detection_config.scale_factors = [-1, 0.5, 1.0]
        errors = self.config_manager.validate_config()
        assert ConfigType.DETECTION.value in errors

    def test_validate_config_invalid_automation(self):
        """测试验证无效自动化配置。"""
        self.config_manager.update_config(
            ConfigType.AUTOMATION,
            action_delay=-1,
            click_delay=-0.5
        )
        
        errors = self.config_manager.validate_config()
        assert ConfigType.AUTOMATION.value in errors
        automation_errors = errors[ConfigType.AUTOMATION.value]
        assert len(automation_errors) == 2

    def test_str_and_repr(self):
        """测试字符串表示。"""
        str_repr = str(self.config_manager)
        assert "ConfigManager" in str_repr
        assert str(self.config_file) in str_repr
        assert "configs=6" in str_repr
        
        repr_str = repr(self.config_manager)
        assert repr_str == str_repr

    def test_config_type_enum(self):
        """测试配置类型枚举。"""
        assert ConfigType.GAME.value == "game"
        assert ConfigType.UI.value == "ui"
        assert ConfigType.DETECTION.value == "detection"
        assert ConfigType.AUTOMATION.value == "automation"
        assert ConfigType.LOGGING.value == "logging"
        assert ConfigType.SYSTEM.value == "system"

    def test_config_dataclasses_defaults(self):
        """测试配置数据类的默认值。"""
        game_config = GameConfig()
        assert game_config.window_title == "崩坏：星穹铁道"
        assert game_config.max_retries == 3
        
        ui_config = UIConfig()
        assert ui_config.template_dir == "templates"
        assert ui_config.save_failed_detections is True
        
        detection_config = DetectionConfig()
        assert detection_config.confidence_threshold == 0.8
        assert detection_config.scale_factors == [0.8, 0.9, 1.0, 1.1, 1.2]
        
        automation_config = AutomationConfig()
        assert automation_config.action_delay == 0.5
        assert automation_config.max_action_retries == 3
        
        logging_config = LoggingConfig()
        assert logging_config.level == "INFO"
        assert logging_config.max_file_size == 10 * 1024 * 1024
        
        system_config = SystemConfig()
        assert system_config.work_dir == "."
        assert system_config.cache_size == 100

    def test_load_config_with_exception_in_config_type(self):
        """测试加载配置时配置类型处理异常。"""
        test_config = {
            "game": {
                "window_title": "测试游戏",
                "invalid_field": "value"  # 这会触发warning但不会异常
            }
        }
        
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(test_config, f)
        
        with patch.object(self.config_manager.logger, 'warning') as mock_warning:
            result = self.config_manager.load_config()
            assert result is True
            mock_warning.assert_called()

    def test_edge_cases(self):
        """测试边界情况。"""
        # 测试获取不存在的配置类型
        result = self.config_manager.get_config(None)
        assert result is None
        
        # 测试更新不存在的配置类型
        with patch.object(self.config_manager, '_configs', {}):
            self.config_manager.update_config(ConfigType.GAME, window_title="test")
            # 应该不会抛出异常