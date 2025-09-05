#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库初始化脚本
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.database.db_manager import DatabaseManager

def main():
    """初始化数据库"""
    try:
        print("开始初始化数据库...")
        db = DatabaseManager()
        db.initialize_database()
        print("数据库初始化完成！")
        
        # 验证数据库状态
        stats = db.get_database_stats()
        print(f"数据库统计信息: {stats}")
        
    except Exception as e:
        print(f"数据库初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())