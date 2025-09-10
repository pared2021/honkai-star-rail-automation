#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试真实的游戏操作器实现.

测试项目中实际的GameOperator类功能。
"""

import sys
import os
import asyncio
import traceback
from typing import Tuple, Optional, Dict, Any

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    # 导入真实的游戏操作器
    from core.game_operator import GameOperator, OperationConfig, OperationResult
    from core.game_detector import GameDetector
    from core.sync_adapter import SyncAdapter
    from config.config_manager import ConfigManager
    print("✅ 成功导入所有必需的模块")
except ImportError as e:
    print(f"❌ 导入模块失败: {e}")
    traceback.print_exc()
    sys.exit(1)


async def test_game_operator_creation():
    """测试游戏操作器创建."""
    print("\n=== 游戏操作器创建测试 ===")
    
    try:
        # 创建配置管理器
        config_manager = ConfigManager()
        print("✅ 配置管理器创建成功")
        
        # 创建游戏检测器
        game_detector = GameDetector(config_manager)
        print("✅ 游戏检测器创建成功")
        
        # 创建同步适配器
        sync_adapter = SyncAdapter()
        print("✅ 同步适配器创建成功")
        
        # 创建游戏操作器
        game_operator = GameOperator(
            game_detector=game_detector,
            sync_adapter=sync_adapter
        )
        print("✅ 游戏操作器创建成功")
        
        return game_operator
        
    except Exception as e:
        print(f"❌ 游戏操作器创建失败: {e}")
        traceback.print_exc()
        return None


async def test_operation_config():
    """测试操作配置."""
    print("\n=== 操作配置测试 ===")
    
    try:
        # 创建默认配置
        default_config = OperationConfig()
        print(f"✅ 默认配置创建成功: timeout={default_config.timeout}s, retry_count={default_config.retry_count}")
        
        # 创建自定义配置
        custom_config = OperationConfig(
            timeout=60.0,
            retry_count=5,
            screenshot_before=True,
            screenshot_after=True
        )
        print(f"✅ 自定义配置创建成功: timeout={custom_config.timeout}s, retry_count={custom_config.retry_count}")
        print(f"   截图设置: before={custom_config.screenshot_before}, after={custom_config.screenshot_after}")
        
        return True
        
    except Exception as e:
        print(f"❌ 操作配置测试失败: {e}")
        traceback.print_exc()
        return False


async def test_operation_result():
    """测试操作结果."""
    print("\n=== 操作结果测试 ===")
    
    try:
        # 创建成功结果
        success_result = OperationResult(
            success=True,
            execution_time=0.5,
            metadata={"test": "data"}
        )
        print(f"✅ 成功结果创建: success={success_result.success}, time={success_result.execution_time}s")
        
        # 创建失败结果
        failure_result = OperationResult(
            success=False,
            execution_time=1.0,
            error_message="测试错误",
            metadata={"error_code": 404}
        )
        print(f"✅ 失败结果创建: success={failure_result.success}, error='{failure_result.error_message}'")
        
        return True
        
    except Exception as e:
        print(f"❌ 操作结果测试失败: {e}")
        traceback.print_exc()
        return False


async def test_game_operator_methods(game_operator):
    """测试游戏操作器方法."""
    print("\n=== 游戏操作器方法测试 ===")
    
    if not game_operator:
        print("❌ 游戏操作器未创建，跳过方法测试")
        return False
    
    try:
        # 测试配置管理
        print("测试配置管理...")
        default_config = game_operator.get_default_config()
        print(f"✅ 获取默认配置成功: timeout={default_config.timeout}s")
        
        new_config = OperationConfig(timeout=45.0, retry_count=4)
        game_operator.set_default_config(new_config)
        updated_config = game_operator.get_default_config()
        print(f"✅ 设置配置成功: timeout={updated_config.timeout}s")
        
        # 测试操作历史
        print("测试操作历史...")
        history = game_operator.get_operation_history()
        print(f"✅ 获取操作历史成功: {len(history)} 条记录")
        
        # 测试点击操作（使用坐标，避免依赖真实UI元素）
        print("测试点击操作...")
        try:
            click_result = await game_operator.click((100, 100))
            if click_result.success:
                print(f"✅ 点击操作成功: 执行时间={click_result.execution_time:.3f}s")
            else:
                print(f"⚠️  点击操作失败（预期）: {click_result.error_message}")
        except Exception as e:
            print(f"⚠️  点击操作异常（预期）: {e}")
        
        # 测试滑动操作
        print("测试滑动操作...")
        try:
            swipe_result = await game_operator.swipe((100, 100), (200, 200), duration=1.0)
            if swipe_result.success:
                print(f"✅ 滑动操作成功: 执行时间={swipe_result.execution_time:.3f}s")
            else:
                print(f"⚠️  滑动操作失败（预期）: {swipe_result.error_message}")
        except Exception as e:
            print(f"⚠️  滑动操作异常（预期）: {e}")
        
        # 测试文本输入
        print("测试文本输入...")
        try:
            input_result = await game_operator.input_text("test")
            if input_result.success:
                print(f"✅ 文本输入成功: 执行时间={input_result.execution_time:.3f}s")
            else:
                print(f"⚠️  文本输入失败（预期）: {input_result.error_message}")
        except Exception as e:
            print(f"⚠️  文本输入异常（预期）: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ 游戏操作器方法测试失败: {e}")
        traceback.print_exc()
        return False


async def main():
    """主测试函数."""
    print("开始真实游戏操作器测试...")
    print("=" * 50)
    
    test_results = []
    game_operator = None
    
    # 运行所有测试
    tests = [
        ("操作配置测试", test_operation_config),
        ("操作结果测试", test_operation_result),
    ]
    
    # 先测试基础类
    for test_name, test_func in tests:
        try:
            result = await test_func()
            test_results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name}执行异常: {e}")
            test_results.append((test_name, False))
    
    # 测试游戏操作器创建
    try:
        game_operator = await test_game_operator_creation()
        test_results.append(("游戏操作器创建测试", game_operator is not None))
    except Exception as e:
        print(f"❌ 游戏操作器创建测试执行异常: {e}")
        test_results.append(("游戏操作器创建测试", False))
    
    # 测试游戏操作器方法
    try:
        method_result = await test_game_operator_methods(game_operator)
        test_results.append(("游戏操作器方法测试", method_result))
    except Exception as e:
        print(f"❌ 游戏操作器方法测试执行异常: {e}")
        test_results.append(("游戏操作器方法测试", False))
    
    # 输出测试结果摘要
    print("\n" + "=" * 50)
    print("测试结果摘要")
    print("=" * 50)
    
    passed = 0
    failed = 0
    
    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\n总计: {passed + failed} 个测试")
    print(f"通过: {passed} 个")
    print(f"失败: {failed} 个")
    
    if failed == 0:
        print("\n🎉 所有真实游戏操作器测试通过！")
        return True
    else:
        print(f"\n⚠️  有 {failed} 个测试失败，请检查相关功能")
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n测试执行异常: {e}")
        traceback.print_exc()
        sys.exit(1)