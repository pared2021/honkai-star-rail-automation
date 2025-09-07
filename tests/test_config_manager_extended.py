"""ConfigManager扩展测试用例.

测试ConfigManager类的主要功能，包括：
- 配置文件加载和保存
- 配置值的获取和设置
- 配置重载
- 错误处理
"""

import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock

from src.config.config_manager import ConfigManager


class TestConfigManager:
    """ConfigManager测试类."""

    def setup_method(self):
        """测试前设置."""
        # 使用临时文件进行测试
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.temp_dir, "test_config.json")

    def teardown_method(self):
        """测试后清理."""
        # 清理临时文件和目录
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_init_with_default_config_file(self):
        """测试使用默认配置文件初始化."""
        manager = ConfigManager()
        assert manager._config_file == "config.json"
        assert isinstance(manager._config_data, dict)

    def test_init_with_custom_config_file(self):
        """测试使用自定义配置文件初始化."""
        manager = ConfigManager(self.config_file)
        assert manager._config_file == self.config_file
        assert isinstance(manager._config_data, dict)

    def test_init_with_existing_config_file(self):
        """测试使用已存在的配置文件初始化."""
        # 创建配置文件
        config_data = {"test_key": "test_value", "number": 42}
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(config_data, f)

        manager = ConfigManager(self.config_file)
        assert manager._config_data == config_data
        assert manager.get("test_key") == "test_value"
        assert manager.get("number") == 42

    def test_init_with_invalid_json_file(self):
        """测试使用无效JSON文件初始化."""
        # 创建无效的JSON文件
        with open(self.config_file, "w", encoding="utf-8") as f:
            f.write("invalid json content {")

        manager = ConfigManager(self.config_file)
        assert manager._config_data == {}  # 应该回退到空字典

    def test_init_with_io_error(self):
        """测试文件IO错误处理."""
        with patch("builtins.open", side_effect=IOError("Permission denied")):
            manager = ConfigManager(self.config_file)
            assert manager._config_data == {}  # 应该回退到空字典

    def test_get_existing_key(self):
        """测试获取存在的配置键."""
        manager = ConfigManager(self.config_file)
        manager._config_data = {"existing_key": "value"}
        
        result = manager.get("existing_key")
        assert result == "value"

    def test_get_non_existing_key_with_default(self):
        """测试获取不存在的配置键（带默认值）."""
        manager = ConfigManager(self.config_file)
        
        result = manager.get("non_existing_key", "default_value")
        assert result == "default_value"

    def test_get_non_existing_key_without_default(self):
        """测试获取不存在的配置键（不带默认值）."""
        manager = ConfigManager(self.config_file)
        
        result = manager.get("non_existing_key")
        assert result is None

    def test_get_with_different_data_types(self):
        """测试获取不同数据类型的配置值."""
        manager = ConfigManager(self.config_file)
        manager._config_data = {
            "string_value": "hello",
            "int_value": 123,
            "float_value": 45.67,
            "bool_value": True,
            "list_value": [1, 2, 3],
            "dict_value": {"nested": "value"}
        }
        
        assert manager.get("string_value") == "hello"
        assert manager.get("int_value") == 123
        assert manager.get("float_value") == 45.67
        assert manager.get("bool_value") is True
        assert manager.get("list_value") == [1, 2, 3]
        assert manager.get("dict_value") == {"nested": "value"}

    def test_set_new_key(self):
        """测试设置新的配置键."""
        manager = ConfigManager(self.config_file)
        
        manager.set("new_key", "new_value")
        assert manager._config_data["new_key"] == "new_value"
        assert manager.get("new_key") == "new_value"

    def test_set_existing_key(self):
        """测试设置已存在的配置键."""
        manager = ConfigManager(self.config_file)
        manager._config_data = {"existing_key": "old_value"}
        
        manager.set("existing_key", "new_value")
        assert manager._config_data["existing_key"] == "new_value"
        assert manager.get("existing_key") == "new_value"

    def test_set_different_data_types(self):
        """测试设置不同数据类型的配置值."""
        manager = ConfigManager(self.config_file)
        
        manager.set("string_key", "string_value")
        manager.set("int_key", 42)
        manager.set("float_key", 3.14)
        manager.set("bool_key", False)
        manager.set("list_key", ["a", "b", "c"])
        manager.set("dict_key", {"key": "value"})
        
        assert manager.get("string_key") == "string_value"
        assert manager.get("int_key") == 42
        assert manager.get("float_key") == 3.14
        assert manager.get("bool_key") is False
        assert manager.get("list_key") == ["a", "b", "c"]
        assert manager.get("dict_key") == {"key": "value"}

    def test_save_to_new_file(self):
        """测试保存到新文件."""
        manager = ConfigManager(self.config_file)
        manager.set("test_key", "test_value")
        manager.set("number", 123)
        
        manager.save()
        
        # 验证文件已创建并包含正确内容
        assert os.path.exists(self.config_file)
        with open(self.config_file, "r", encoding="utf-8") as f:
            saved_data = json.load(f)
        
        assert saved_data["test_key"] == "test_value"
        assert saved_data["number"] == 123

    def test_save_to_existing_file(self):
        """测试保存到已存在的文件."""
        # 先创建一个配置文件
        initial_data = {"old_key": "old_value"}
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(initial_data, f)
        
        manager = ConfigManager(self.config_file)
        manager.set("new_key", "new_value")
        manager.save()
        
        # 验证文件内容已更新
        with open(self.config_file, "r", encoding="utf-8") as f:
            saved_data = json.load(f)
        
        assert saved_data["old_key"] == "old_value"
        assert saved_data["new_key"] == "new_value"

    def test_save_creates_directory(self):
        """测试保存时创建目录."""
        nested_config_file = os.path.join(self.temp_dir, "nested", "config.json")
        manager = ConfigManager(nested_config_file)
        manager.set("test_key", "test_value")
        
        manager.save()
        
        # 验证目录和文件都已创建
        assert os.path.exists(os.path.dirname(nested_config_file))
        assert os.path.exists(nested_config_file)

    def test_save_with_io_error(self):
        """测试保存时的IO错误处理."""
        manager = ConfigManager(self.config_file)
        manager.set("test_key", "test_value")
        
        with patch("builtins.open", side_effect=IOError("Permission denied")):
            # 应该不抛出异常
            manager.save()

    def test_save_with_unicode_content(self):
        """测试保存包含Unicode字符的内容."""
        manager = ConfigManager(self.config_file)
        manager.set("chinese_text", "你好世界")
        manager.set("emoji", "😀🎉")
        
        manager.save()
        
        # 验证Unicode内容正确保存
        with open(self.config_file, "r", encoding="utf-8") as f:
            saved_data = json.load(f)
        
        assert saved_data["chinese_text"] == "你好世界"
        assert saved_data["emoji"] == "😀🎉"

    def test_reload_with_existing_file(self):
        """测试重载已存在的配置文件."""
        # 初始化管理器
        manager = ConfigManager(self.config_file)
        manager.set("initial_key", "initial_value")
        manager.save()
        
        # 修改内存中的配置
        manager.set("memory_key", "memory_value")
        assert manager.get("memory_key") == "memory_value"
        
        # 重载配置
        manager.reload()
        
        # 验证内存中的修改被丢弃，文件中的配置被重载
        assert manager.get("initial_key") == "initial_value"
        assert manager.get("memory_key") is None

    def test_reload_with_modified_file(self):
        """测试重载被外部修改的配置文件."""
        # 初始化管理器
        manager = ConfigManager(self.config_file)
        manager.set("original_key", "original_value")
        manager.save()
        
        # 外部修改配置文件
        external_data = {"external_key": "external_value"}
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(external_data, f)
        
        # 重载配置
        manager.reload()
        
        # 验证外部修改被加载
        assert manager.get("external_key") == "external_value"
        assert manager.get("original_key") is None

    def test_reload_with_non_existing_file(self):
        """测试重载不存在的配置文件."""
        manager = ConfigManager(self.config_file)
        manager.set("test_key", "test_value")
        
        # 删除配置文件
        if os.path.exists(self.config_file):
            os.remove(self.config_file)
        
        # 重载配置
        manager.reload()
        
        # 验证配置被清空
        assert manager._config_data == {}
        assert manager.get("test_key") is None

    def test_reload_with_invalid_json(self):
        """测试重载无效JSON文件."""
        manager = ConfigManager(self.config_file)
        manager.set("test_key", "test_value")
        
        # 创建无效的JSON文件
        with open(self.config_file, "w", encoding="utf-8") as f:
            f.write("invalid json {")
        
        # 重载配置
        manager.reload()
        
        # 验证配置被重置为空字典
        assert manager._config_data == {}
        assert manager.get("test_key") is None

    def test_get_all_empty_config(self):
        """测试获取空配置的所有内容."""
        manager = ConfigManager(self.config_file)
        
        all_config = manager.get_all()
        assert all_config == {}
        assert isinstance(all_config, dict)

    def test_get_all_with_data(self):
        """测试获取包含数据的所有配置."""
        manager = ConfigManager(self.config_file)
        test_data = {
            "key1": "value1",
            "key2": 42,
            "key3": [1, 2, 3],
            "key4": {"nested": "value"}
        }
        
        for key, value in test_data.items():
            manager.set(key, value)
        
        all_config = manager.get_all()
        assert all_config == test_data

    def test_get_all_returns_copy(self):
        """测试get_all返回配置的副本."""
        manager = ConfigManager(self.config_file)
        manager.set("test_key", "test_value")
        
        all_config = manager.get_all()
        
        # 修改返回的字典不应影响原始配置
        all_config["new_key"] = "new_value"
        assert manager.get("new_key") is None
        assert "new_key" not in manager._config_data

    def test_complex_nested_data(self):
        """测试复杂嵌套数据的处理."""
        manager = ConfigManager(self.config_file)
        complex_data = {
            "database": {
                "host": "localhost",
                "port": 5432,
                "credentials": {
                    "username": "admin",
                    "password": "secret"
                }
            },
            "features": {
                "enabled": ["feature1", "feature2"],
                "disabled": ["feature3"]
            }
        }
        
        manager.set("app_config", complex_data)
        manager.save()
        
        # 重新加载验证
        manager.reload()
        retrieved_data = manager.get("app_config")
        
        assert retrieved_data == complex_data
        assert retrieved_data["database"]["host"] == "localhost"
        assert retrieved_data["database"]["credentials"]["username"] == "admin"
        assert "feature1" in retrieved_data["features"]["enabled"]

    def test_config_file_path_handling(self):
        """测试配置文件路径处理."""
        # 测试相对路径
        relative_path = "relative_config.json"
        manager1 = ConfigManager(relative_path)
        assert manager1._config_file == relative_path
        
        # 测试绝对路径
        absolute_path = os.path.abspath(self.config_file)
        manager2 = ConfigManager(absolute_path)
        assert manager2._config_file == absolute_path
        
        # 测试Path对象
        path_obj = Path(self.config_file)
        manager3 = ConfigManager(str(path_obj))
        assert manager3._config_file == str(path_obj)

    def test_empty_string_key(self):
        """测试空字符串键的处理."""
        manager = ConfigManager(self.config_file)
        
        # 设置空字符串键
        manager.set("", "empty_key_value")
        assert manager.get("") == "empty_key_value"
        
        # 保存和重载
        manager.save()
        manager.reload()
        assert manager.get("") == "empty_key_value"

    def test_none_value_handling(self):
        """测试None值的处理."""
        manager = ConfigManager(self.config_file)
        
        # 设置None值
        manager.set("none_key", None)
        assert manager.get("none_key") is None
        
        # 区分None值和不存在的键
        assert manager.get("non_existing_key") is None
        assert "none_key" in manager._config_data
        assert "non_existing_key" not in manager._config_data

    def test_large_config_data(self):
        """测试大量配置数据的处理."""
        manager = ConfigManager(self.config_file)
        
        # 生成大量配置数据
        for i in range(1000):
            manager.set(f"key_{i}", f"value_{i}")
        
        # 验证所有数据都正确设置
        for i in range(1000):
            assert manager.get(f"key_{i}") == f"value_{i}"
        
        # 保存和重载
        manager.save()
        manager.reload()
        
        # 验证重载后数据仍然正确
        for i in range(0, 1000, 100):  # 抽样检查
            assert manager.get(f"key_{i}") == f"value_{i}"

    def test_concurrent_access_simulation(self):
        """测试模拟并发访问."""
        manager = ConfigManager(self.config_file)
        
        # 模拟多个操作
        operations = [
            ("set", "key1", "value1"),
            ("get", "key1", None),
            ("set", "key2", "value2"),
            ("save", None, None),
            ("reload", None, None),
            ("get", "key1", None),
            ("get_all", None, None)
        ]
        
        for op, key, value in operations:
            if op == "set":
                manager.set(key, value)
            elif op == "get":
                result = manager.get(key)
                if key in manager._config_data:
                    assert result is not None
            elif op == "save":
                manager.save()
            elif op == "reload":
                manager.reload()
            elif op == "get_all":
                all_config = manager.get_all()
                assert isinstance(all_config, dict)

    @patch('pathlib.Path.exists')
    def test_path_exists_mock(self, mock_exists):
        """测试使用mock的路径存在检查."""
        mock_exists.return_value = False
        
        manager = ConfigManager(self.config_file)
        assert manager._config_data == {}
        
        mock_exists.return_value = True
        with patch('builtins.open', mock_open(read_data='{"test": "value"}')):
            manager.reload()
            assert manager.get("test") == "value"

    def test_json_serialization_edge_cases(self):
        """测试JSON序列化边界情况."""
        manager = ConfigManager(self.config_file)
        
        # 测试特殊字符
        special_chars = "\n\t\r\"\\'"
        manager.set("special_chars", special_chars)
        manager.save()
        manager.reload()
        assert manager.get("special_chars") == special_chars
        
        # 测试数字边界值
        manager.set("max_int", 2**63 - 1)
        manager.set("min_int", -(2**63))
        manager.set("float_precision", 1.23456789012345)
        manager.save()
        manager.reload()
        
        assert manager.get("max_int") == 2**63 - 1
        assert manager.get("min_int") == -(2**63)
        assert abs(manager.get("float_precision") - 1.23456789012345) < 1e-10