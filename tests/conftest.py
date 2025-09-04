"""简洁的pytest配置文件，避免复杂的异步操作"""

import os
from pathlib import Path
import tempfile

import pytest


@pytest.fixture(scope="session")
def temp_db_path():
    """创建临时数据库文件路径"""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    yield db_path

    # 清理临时文件
    try:
        if os.path.exists(db_path):
            os.unlink(db_path)
    except Exception:
        pass  # 忽略清理错误


@pytest.fixture(scope="function")
def clean_environment():
    """确保每个测试都有干净的环境"""
    # 测试前的设置
    yield
    # 测试后的清理（如果需要）
    pass


# 移除复杂的事件循环fixture，使用同步测试
# 如果需要异步测试，使用pytest-asyncio的默认配置
