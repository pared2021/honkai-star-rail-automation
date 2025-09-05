#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

# 添加项目根目录和src目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src_path = os.path.join(project_root, 'src')

if project_root not in sys.path:
    sys.path.insert(0, project_root)
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# 设置环境变量
os.environ['PYTHONPATH'] = f"{src_path}{os.pathsep}{project_root}{os.pathsep}{os.environ.get('PYTHONPATH', '')}"