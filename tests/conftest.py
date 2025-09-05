#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import tempfile

import pytest

# 添加项目根目录和src目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src_path = os.path.join(project_root, "src")

if project_root not in sys.path:
    sys.path.insert(0, project_root)
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# 设置环境变量
os.environ["PYTHONPATH"] = (
    f"{src_path}{os.pathsep}{project_root}{os.pathsep}{os.environ.get('PYTHONPATH', '')}"
)


@pytest.fixture
def temp_db_path():
    """创建临时数据库文件路径。"""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as temp_file:
        temp_path = temp_file.name
    
    yield temp_path
    
    # 清理临时文件
    if os.path.exists(temp_path):
        os.unlink(temp_path)
