"""ConfigManager测试模块.

测试配置管理器的各种功能和边界情况。
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import mock_open, patch

import pytest

from src.config.config_manager import ConfigManager


class TestConfigManager:
    """ConfigManager测试类."""

    def test_init_with_default_config_file(self):
        """测试使用默认配置文件初始化."""
        with patch.object(ConfigManager, '_load_config'):
            manager = ConfigManager()
            assert manager._config_file == "config.json"

    def test_init_with_custom_config_file(self):
        """测试使用自定义配置文件初始化."""
        with patch.object(ConfigManager, '_load_config'):
            manager = ConfigManager("custom_config.json")
            assert manager._config_file == "custom_config.json"

    def test_load_config_file_exists_valid_json(self):
        """测试加载存在的有效JSON配置文件."""
        test_config = {"key1": "value1", "key2": 42}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_config, f)
            temp_file = f.name
        
        try:
            manager = ConfigManager(temp_file)
            assert manager._config_data == test_config
        finally:
            os.unlink(temp_file)

    def test_load_config_file_not_exists(self):
        """测试加载不存在的配置文件."""
        manager = ConfigManager("non_existent_file.json")
        assert manager._config_data == {}

    def test_load_config_invalid_json(self):
        """测试加载无效JSON配置文件."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("invalid json content")
            temp_file = f.name
        
        try:
            manager = ConfigManager(temp_file)
            assert manager._config_data == {}
        finally:
            os.unlink(temp_file)

    def test_load_config_io_error(self):
        """测试加载配置文件时的IO错误."""
        with patch('builtins.open', side_effect=IOError("Permission denied")):
            with patch('pathlib.Path.exists', return_value=True):
                manager = ConfigManager("test_config.json")
                assert manager._config_data == {}

    def test_get_existing_key(self):
        """测试获取存在的配置键."""
        with patch.object(ConfigManager, '_load_config'):
            manager = ConfigManager()
            manager._config_data = {"test_key": "test_value"}
            
            result = manager.get("test_key")
            assert result == "test_value"

    def test_get_non_existing_key_with_default(self):
        """测试获取不存在的配置键并提供默认值."""
        with patch.object(ConfigManager, '_load_config'):
            manager = ConfigManager()
            manager._config_data = {}
            
            result = manager.get("non_existent_key", "default_value")
            assert result == "default_value"

    def test_get_non_existing_key_without_default(self):
        """测试获取不存在的配置键且不提供默认值."""
        with patch.object(ConfigManager, '_load_config'):
            manager = ConfigManager()
            manager._config_data = {}
            
            result = manager.get("non_existent_key")
            assert result is None

    def test_set_new_key(self):
        """测试设置新的配置键."""
        with patch.object(ConfigManager, '_load_config'):
            manager = ConfigManager()
            manager._config_data = {}
            
            manager.set("new_key", "new_value")
            assert manager._config_data["new_key"] == "new_value"

    def test_set_existing_key(self):
        """测试更新已存在的配置键."""
        with patch.object(ConfigManager, '_load_config'):
            manager = ConfigManager()
            manager._config_data = {"existing_key": "old_value"}
            
            manager.set("existing_key", "new_value")
            assert manager._config_data["existing_key"] == "new_value"

    def test_save_success(self):
        """测试成功保存配置文件."""
        test_config = {"key1": "value1", "key2": 42}
        
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = os.path.join(temp_dir, "test_config.json")
            
            with patch.object(ConfigManager, '_load_config'):
                manager = ConfigManager(config_file)
                manager._config_data = test_config
                
                manager.save()
                
                # 验证文件已保存
                assert os.path.exists(config_file)
                
                # 验证文件内容
                with open(config_file, 'r', encoding='utf-8') as f:
                    saved_config = json.load(f)
                assert saved_config == test_config

    def test_save_create_parent_directories(self):
        """测试保存时创建父目录."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = os.path.join(temp_dir, "subdir", "test_config.json")
            
            with patch.object(ConfigManager, '_load_config'):
                manager = ConfigManager(config_file)
                manager._config_data = {"test": "value"}
                
                manager.save()
                
                # 验证父目录已创建
                assert os.path.exists(os.path.dirname(config_file))
                assert os.path.exists(config_file)

    def test_save_io_error(self):
        """测试保存配置文件时的IO错误."""
        with patch('builtins.open', side_effect=IOError("Permission denied")):
            with patch.object(ConfigManager, '_load_config'):
                manager = ConfigManager("test_config.json")
                manager._config_data = {"test": "value"}
                
                # 应该不抛出异常
                manager.save()

    def test_reload(self):
        """测试重新加载配置文件."""
        initial_config = {"key1": "value1"}
        updated_config = {"key1": "updated_value", "key2": "value2"}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(initial_config, f)
            temp_file = f.name
        
        try:
            # 初始加载
            manager = ConfigManager(temp_file)
            assert manager._config_data == initial_config
            
            # 更新文件内容
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(updated_config, f)
            
            # 重新加载
            manager.reload()
            assert manager._config_data == updated_config
        finally:
            os.unlink(temp_file)

    def test_get_all(self):
        """测试获取所有配置."""
        test_config = {"key1": "value1", "key2": 42, "key3": [1, 2, 3]}
        
        with patch.object(ConfigManager, '_load_config'):
            manager = ConfigManager()
            manager._config_data = test_config
            
            result = manager.get_all()
            
            # 验证返回的是副本
            assert result == test_config
            assert result is not manager._config_data
            
            # 修改返回的字典不应影响原始数据
            result["new_key"] = "new_value"
            assert "new_key" not in manager._config_data

    def test_get_all_empty_config(self):
        """测试获取空配置."""
        with patch.object(ConfigManager, '_load_config'):
            manager = ConfigManager()
            manager._config_data = {}
            
            result = manager.get_all()
            assert result == {}

    def test_complex_data_types(self):
        """测试复杂数据类型的配置."""
        complex_config = {
            "string": "test",
            "number": 42,
            "float": 3.14,
            "boolean": True,
            "list": [1, 2, 3],
            "dict": {"nested": "value"},
            "null": None
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(complex_config, f)
            temp_file = f.name
        
        try:
            manager = ConfigManager(temp_file)
            
            # 测试各种数据类型
            assert manager.get("string") == "test"
            assert manager.get("number") == 42
            assert manager.get("float") == 3.14
            assert manager.get("boolean") is True
            assert manager.get("list") == [1, 2, 3]
            assert manager.get("dict") == {"nested": "value"}
            assert manager.get("null") is None
        finally:
            os.unlink(temp_file)

    def test_unicode_support(self):
        """测试Unicode字符支持."""
        unicode_config = {
            "chinese": "中文测试",
            "emoji": "🚀🎉",
            "special": "àáâãäåæçèéêë"
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(unicode_config, f, ensure_ascii=False)
            temp_file = f.name
        
        try:
            manager = ConfigManager(temp_file)
            
            assert manager.get("chinese") == "中文测试"
            assert manager.get("emoji") == "🚀🎉"
            assert manager.get("special") == "àáâãäåæçèéêë"
        finally:
            os.unlink(temp_file)

    def test_integration_workflow(self):
        """测试完整的工作流程."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = os.path.join(temp_dir, "integration_test.json")
            
            # 创建配置管理器
            manager = ConfigManager(config_file)
            
            # 设置一些配置
            manager.set("app_name", "Test App")
            manager.set("version", "1.0.0")
            manager.set("debug", True)
            
            # 保存配置
            manager.save()
            
            # 创建新的配置管理器实例
            new_manager = ConfigManager(config_file)
            
            # 验证配置已正确加载
            assert new_manager.get("app_name") == "Test App"
            assert new_manager.get("version") == "1.0.0"
            assert new_manager.get("debug") is True
            
            # 更新配置
            new_manager.set("version", "1.1.0")
            new_manager.set("new_feature", "enabled")
            
            # 保存并重新加载
            new_manager.save()
            new_manager.reload()
            
            # 验证更新
            assert new_manager.get("version") == "1.1.0"
            assert new_manager.get("new_feature") == "enabled"
            assert new_manager.get("app_name") == "Test App"  # 原有配置保持不变