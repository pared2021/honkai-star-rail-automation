#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import traceback
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print(f"Python version: {sys.version}")
print(f"Project root: {project_root}")
print(f"Python path: {sys.path[:3]}")

try:
    print("Importing src.main...")
    import src.main
    print("src.main imported successfully")
    
    print("Calling main()...")
    src.main.main()
    print("main() completed successfully")
    
except ImportError as e:
    print(f"Import error: {e}")
    traceback.print_exc()
except Exception as e:
    print(f"Runtime error: {e}")
    traceback.print_exc()