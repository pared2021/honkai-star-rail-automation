#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""集成测试脚本.

测试项目的核心功能模块是否正常工作。
"""

import sys
import traceback
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_module_imports():
    """测试模块导入。"""
    try:
        # 测试核心模块
        from src.core.task_manager import TaskManager
        from src.core.service_locator import ServiceLocator
        from src.config.config_manager import ConfigManager
        from src.database.db_manager import DatabaseManager
        
        # 测试游戏检测模块
        from src.game.game_detector import GameDetector
        
        print("✓ 所有核心模块导入成功")
        return True
    except Exception as e:
        print(f"❌ 模块导入失败: {e}")
        return False


def test_config_system():
    """测试配置系统."""
    print("\n=== 测试配置系统 ===")
    
    try:
        from src.config.app_config import AppConfigManager
        from src.config.config_loader import ConfigLoader, ConfigFormat
        
        # 测试配置加载器
        loader = ConfigLoader()
        print("✓ ConfigLoader 创建成功")
        
        # 测试应用配置管理器
        config_manager = AppConfigManager()
        print("✓ AppConfigManager 创建成功")
        
        # 测试配置加载
        config = config_manager.load_config()
        print(f"✓ 配置加载成功: {type(config).__name__}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 配置系统测试失败: {e}")
        traceback.print_exc()
        return False


def test_database_system():
    """测试数据库系统."""
    print("\n=== 测试数据库系统 ===")
    
    try:
        from src.database.db_manager import DatabaseManager
        
        # 创建测试数据库
        db_manager = DatabaseManager(":memory:")  # 使用内存数据库
        print("✓ DatabaseManager 创建成功")
        
        # 初始化数据库
        db_manager.initialize_database()
        print("✓ 数据库初始化成功")
        
        # 测试连接
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            print(f"✓ 数据库表创建成功: {[table[0] for table in tables]}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 数据库系统测试失败: {e}")
        traceback.print_exc()
        return False


def test_monitoring_system():
    """测试监控系统."""
    print("\n=== 测试监控系统 ===")
    
    try:
        from src.monitoring.metrics_collector import MetricsCollector
        from src.monitoring.alert_manager import AlertManager
        from src.monitoring.task_monitor import TaskMonitor, MonitoringLevel
        
        # 测试指标收集器
        metrics = MetricsCollector()
        metrics.record_counter("test_counter", 1)
        print("✓ MetricsCollector 工作正常")
        
        # 测试告警管理器
        alert_manager = AlertManager()
        print("✓ AlertManager 创建成功")
        
        # 测试任务监控器
        task_monitor = TaskMonitor(MonitoringLevel.BASIC)
        task_monitor.start_monitoring()
        print("✓ TaskMonitor 启动成功")
        task_monitor.stop_monitoring()
        
        return True
        
    except Exception as e:
        print(f"\n❌ 监控系统测试失败: {e}")
        traceback.print_exc()
        return False


def test_task_system():
    """测试任务系统."""
    print("\n=== 测试任务系统 ===")
    
    try:
        from src.core.task_manager import TaskManager, Task, TaskType, TaskPriority
        
        # 创建任务管理器
        task_manager = TaskManager()
        print("✓ TaskManager 创建成功")
        
        # 创建测试任务
        test_task = Task(
            id="test_001",
            name="测试任务",
            task_type=TaskType.DAILY_TASK,
            priority=TaskPriority.NORMAL
        )
        
        # 测试任务创建（使用简单的测试函数）
        def test_func():
            return "测试结果"
        
        # 注意：这里只是测试Task类的创建，不调用实际的create_task方法
        print(f"✓ Task类创建成功: {test_task}")
        
        # 测试任务管理器的基本功能
        stats = task_manager.get_task_statistics()
        print(f"✓ 任务统计获取成功: {stats}")
        
        print("✓ 任务系统测试通过")
        return True
        
    except Exception as e:
        print(f"\n❌ 任务系统测试失败: {e}")
        traceback.print_exc()
        return False


def test_game_detection():
    """测试游戏检测."""
    print("\n=== 测试游戏检测 ===")
    
    try:
        from src.game.game_detector import GameDetector
        
        # 创建游戏检测器
        detector = GameDetector()
        print("✓ GameDetector 创建成功")
        
        # 注意：这里不实际检测游戏，只测试创建
        print("✓ 游戏检测模块可用")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 游戏检测测试失败: {e}")
        traceback.print_exc()
        return False


def main():
    """主测试函数。"""
    print("崩坏星穹铁道自动化助手 - 集成测试")
    print("=" * 50)
    
    # 测试列表
    tests = [
        ("模块导入", test_module_imports),
        ("配置系统", test_config_system),
        ("数据库系统", test_database_system),
        ("监控系统", test_monitoring_system),
        ("任务系统", test_task_system),
        ("游戏检测", test_game_detection),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"\n✓ {test_name} 测试通过")
            else:
                print(f"\n❌ {test_name} 测试失败")
        except Exception as e:
            print(f"\n❌ {test_name} 测试异常: {e}")
    
    print("\n" + "=" * 50)
    print(f"测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！项目集成正常。")
        return 0
    else:
        print("⚠️  部分测试失败，请检查相关模块。")
        return 1


if __name__ == "__main__":
    sys.exit(main())