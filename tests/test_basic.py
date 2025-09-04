"""基础测试 - 验证测试框架"""

import os
import sys

import pytest


class TestBasic:
    """基础测试类"""

    def test_python_version(self):
        """测试Python版本"""
        assert sys.version_info >= (3, 6), "需要Python 3.6或更高版本"

    def test_pytest_working(self):
        """测试pytest是否正常工作"""
        assert True, "pytest基本功能正常"

    def test_simple_math(self):
        """测试简单数学运算"""
        assert 1 + 1 == 2
        assert 2 * 3 == 6
        assert 10 / 2 == 5
        assert 2**3 == 8

    def test_string_operations(self):
        """测试字符串操作"""
        text = "Hello World"
        assert len(text) == 11
        assert text.upper() == "HELLO WORLD"
        assert text.lower() == "hello world"
        assert "World" in text

    def test_list_operations(self):
        """测试列表操作"""
        numbers = [1, 2, 3, 4, 5]
        assert len(numbers) == 5
        assert numbers[0] == 1
        assert numbers[-1] == 5
        assert sum(numbers) == 15
        assert max(numbers) == 5
        assert min(numbers) == 1

    def test_dict_operations(self):
        """测试字典操作"""
        data = {"name": "测试", "value": 100, "active": True}
        assert data["name"] == "测试"
        assert data["value"] == 100
        assert data["active"] is True
        assert len(data) == 3
        assert "name" in data

    def test_exception_handling(self):
        """测试异常处理"""
        with pytest.raises(ZeroDivisionError):
            result = 1 / 0

        with pytest.raises(KeyError):
            data = {"a": 1}
            value = data["b"]

        with pytest.raises(IndexError):
            numbers = [1, 2, 3]
            value = numbers[10]

    def test_file_operations(self, temp_db_path):
        """测试文件操作"""
        # 验证临时文件存在
        assert os.path.exists(temp_db_path)

        # 测试文件写入和读取
        test_file = temp_db_path + ".txt"

        # 写入文件
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("测试内容\n第二行")

        # 读取文件
        with open(test_file, "r", encoding="utf-8") as f:
            content = f.read()

        assert "测试内容" in content
        assert "第二行" in content

        # 清理测试文件
        if os.path.exists(test_file):
            os.unlink(test_file)

    def test_environment_variables(self):
        """测试环境变量"""
        # 设置测试环境变量
        os.environ["TEST_VAR"] = "test_value"

        # 验证环境变量
        assert os.environ.get("TEST_VAR") == "test_value"

        # 清理环境变量
        del os.environ["TEST_VAR"]
        assert os.environ.get("TEST_VAR") is None

    def test_import_paths(self):
        """测试导入路径"""
        # 验证项目路径在sys.path中
        project_root = os.path.join(os.path.dirname(__file__), "..")
        src_path = os.path.join(project_root, "src")

        # 这些路径应该已经在conftest.py中添加
        # 只是验证路径存在
        assert os.path.exists(project_root)

        # 如果src目录存在，验证它
        if os.path.exists(src_path):
            assert os.path.isdir(src_path)

    @pytest.mark.parametrize(
        "input_value,expected", [(1, 2), (2, 4), (3, 6), (4, 8), (5, 10)]
    )
    def test_parametrized(self, input_value, expected):
        """测试参数化测试"""
        result = input_value * 2
        assert result == expected
