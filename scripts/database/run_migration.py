#!/usr/bin/env python3
"""
数据库迁移脚本
运行数据库迁移文件来创建或更新数据库表结构
"""

import sqlite3
import os
import sys
from pathlib import Path

def run_migration(db_path: str, migration_file: str):
    """运行数据库迁移"""
    try:
        # 确保数据库目录存在
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
        
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 读取迁移文件
        with open(migration_file, 'r', encoding='utf-8') as f:
            migration_sql = f.read()
        
        # 执行迁移
        cursor.executescript(migration_sql)
        conn.commit()
        
        print(f"✅ 数据库迁移成功: {migration_file} -> {db_path}")
        
        # 验证表是否创建成功
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"📋 创建的表: {[table[0] for table in tables]}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 数据库迁移失败: {e}")
        return False

def main():
    """主函数"""
    # 项目根目录
    project_root = Path(__file__).parent
    
    # 数据库文件路径
    db_path = project_root / "data" / "app.db"
    
    # 迁移文件路径
    migration_file = project_root / "migrations" / "001_initial_schema.sql"
    
    if not migration_file.exists():
        print(f"❌ 迁移文件不存在: {migration_file}")
        sys.exit(1)
    
    print(f"🚀 开始数据库迁移...")
    print(f"📁 数据库路径: {db_path}")
    print(f"📄 迁移文件: {migration_file}")
    
    success = run_migration(str(db_path), str(migration_file))
    
    if success:
        print("🎉 数据库迁移完成!")
        sys.exit(0)
    else:
        print("💥 数据库迁移失败!")
        sys.exit(1)

if __name__ == "__main__":
    main()