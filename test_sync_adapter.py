#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
同步适配器功能测试脚本
用于验证SyncAdapter在GUI和异步操作间的协调功能
"""

import sys
import asyncio
import time
import threading
from pathlib import Path
from datetime import datetime
from typing import Any, Callable

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core.sync_adapter import SyncAdapter
from src.core.config_manager import ConfigManager

def test_sync_adapter_basic():
    """测试同步适配器基础功能"""
    print("=== 同步适配器基础功能测试 ===")
    
    try:
        # 初始化同步适配器
        sync_adapter = SyncAdapter()
        print("✅ 同步适配器初始化成功")
        
        # 测试基本属性
        print(f"   适配器类型: {type(sync_adapter).__name__}")
        print(f"   初始化时间: {datetime.now()}")
        print(f"   初始状态: {sync_adapter.get_status()}")
        
        # 启动适配器
        print("\n2. 启动同步适配器...")
        start_result = sync_adapter.start()
        print(f"   启动结果: {'✅ 成功' if start_result else '❌ 失败'}")
        print(f"   运行状态: {sync_adapter.get_status()}")
        
        # 获取统计信息
        stats = sync_adapter.get_stats()
        print(f"\n3. 统计信息:")
        for key, value in stats.items():
            print(f"   {key}: {value}")
        
        # 停止适配器
        print("\n4. 停止同步适配器...")
        stop_result = sync_adapter.stop()
        print(f"   停止结果: {'✅ 成功' if stop_result else '❌ 失败'}")
        print(f"   最终状态: {sync_adapter.get_status()}")
        
        return start_result and stop_result
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_async_to_sync_execution():
    """测试异步到同步的执行转换"""
    print("\n=== 异步到同步执行测试 ===")
    
    try:
        sync_adapter = SyncAdapter()
        sync_adapter.start()  # 启动适配器
        
        # 定义一个异步函数
        async def async_task(delay: float, message: str) -> str:
            """模拟异步任务"""
            print(f"   🔄 开始异步任务: {message}")
            await asyncio.sleep(delay)
            result = f"任务完成: {message} (延迟: {delay}s)"
            print(f"   ✅ 异步任务完成: {result}")
            return result
        
        print("1. 测试简单异步任务执行...")
        start_time = time.time()
        
        # 使用同步适配器执行异步任务
        task_id = sync_adapter.run_async(async_task(0.5, "测试任务1"))
        print(f"   任务ID: {task_id}")
        
        # 等待任务完成并获取结果
        result = sync_adapter.wait_for_result(task_id, timeout=5.0)
        print(f"   结果: {result}")
        
        execution_time = time.time() - start_time
        print(f"   执行时间: {execution_time:.2f}s")
        
        # 停止适配器
        sync_adapter.stop()
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_callback_mechanism():
    """测试回调机制"""
    print("\n=== 回调机制测试 ===")
    
    try:
        sync_adapter = SyncAdapter()
        sync_adapter.start()  # 启动适配器
        callback_results = []
        
        # 定义回调函数
        def success_callback(result: Any) -> None:
            """成功回调"""
            callback_results.append(f"成功: {result}")
            print(f"   📞 成功回调触发: {result}")
        
        def error_callback(error: Exception) -> None:
            """错误回调"""
            callback_results.append(f"错误: {error}")
            print(f"   📞 错误回调触发: {error}")
        
        # 定义测试异步函数
        async def callback_test_task(should_fail: bool = False) -> str:
            """回调测试任务"""
            await asyncio.sleep(0.2)
            if should_fail:
                raise ValueError("模拟任务失败")
            return "回调测试成功"
        
        print("1. 测试成功回调...")
        
        # 注册回调函数
        from src.core.sync_adapter import CallbackType
        sync_adapter.register_callback(success_callback, CallbackType.SUCCESS)
        sync_adapter.register_callback(error_callback, CallbackType.ERROR)
        
        # 执行异步任务
        task_id = sync_adapter.run_async(callback_test_task(False))
        try:
            result = sync_adapter.wait_for_result(task_id, timeout=5.0)
            print(f"   任务结果: {result}")
        except Exception as e:
            print(f"   任务异常: {e}")
        
        print("\n2. 测试错误回调...")
        
        # 执行会失败的任务
        task_id2 = sync_adapter.run_async(callback_test_task(True))
        try:
            result = sync_adapter.wait_for_result(task_id2, timeout=5.0)
            print(f"   任务结果: {result}")
        except Exception as e:
            print(f"   任务异常: {e}")
        
        print(f"\n📊 回调结果统计:")
        for i, result in enumerate(callback_results, 1):
            print(f"   {i}. {result}")
        
        # 停止适配器
        sync_adapter.stop()
        return len(callback_results) > 0
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_thread_safety():
    """测试线程安全性"""
    print("\n=== 线程安全性测试 ===")
    
    try:
        sync_adapter = SyncAdapter()
        sync_adapter.start()  # 启动适配器
        results = []
        threads = []
        
        # 定义线程任务
        def thread_task(thread_id: int) -> None:
            """线程任务"""
            try:
                async def async_work() -> str:
                    await asyncio.sleep(0.1)
                    return f"线程{thread_id}完成"
                
                # 在每个线程中执行异步任务
                task_id = sync_adapter.run_async(async_work())
                result = sync_adapter.wait_for_result(task_id, timeout=5.0)
                
                results.append(result)
                print(f"   ✅ {result}")
                
            except Exception as e:
                results.append(f"线程{thread_id}失败: {e}")
                print(f"   ❌ 线程{thread_id}失败: {e}")
        
        print("1. 创建多个线程并发执行...")
        
        # 创建并启动多个线程
        for i in range(3):
            thread = threading.Thread(target=thread_task, args=(i+1,))
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        print(f"\n📊 线程执行结果:")
        for i, result in enumerate(results, 1):
            print(f"   {i}. {result}")
        
        # 检查是否所有线程都成功完成
        success_count = sum(1 for r in results if "完成" in str(r))
        print(f"\n✅ 成功线程数: {success_count}/{len(threads)}")
        
        # 停止适配器
        sync_adapter.stop()
        return success_count == len(threads)
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_error_handling():
    """测试错误处理"""
    print("\n=== 错误处理测试 ===")
    
    try:
        sync_adapter = SyncAdapter()
        sync_adapter.start()  # 启动适配器
        
        # 定义会出错的异步函数
        async def failing_task(error_type: str) -> str:
            """会失败的异步任务"""
            await asyncio.sleep(0.1)
            if error_type == "value_error":
                raise ValueError("模拟值错误")
            elif error_type == "runtime_error":
                raise RuntimeError("模拟运行时错误")
            elif error_type == "timeout":
                await asyncio.sleep(10)  # 模拟超时
                return "不应该到达这里"
            else:
                return "正常完成"
        
        test_cases = [
            ("正常情况", "normal"),
            ("值错误", "value_error"),
            ("运行时错误", "runtime_error")
        ]
        
        for case_name, error_type in test_cases:
            print(f"\n{case_name}测试:")
            try:
                task_id = sync_adapter.run_async(failing_task(error_type))
                result = sync_adapter.wait_for_result(task_id, timeout=5.0)
                print(f"   ✅ 结果: {result}")
            except Exception as e:
                print(f"   ❌ 捕获异常: {type(e).__name__}: {e}")
        
        # 停止适配器
        sync_adapter.stop()
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_performance():
    """测试性能"""
    print("\n=== 性能测试 ===")
    
    try:
        sync_adapter = SyncAdapter()
        sync_adapter.start()  # 启动适配器
        
        # 定义性能测试任务
        async def performance_task(task_id: int) -> str:
            """性能测试任务"""
            await asyncio.sleep(0.01)  # 短暂延迟
            return f"任务{task_id}完成"
        
        print("1. 执行多个小任务测试性能...")
        
        start_time = time.time()
        task_count = 10
        
        for i in range(task_count):
            task_id = sync_adapter.run_async(performance_task(i+1))
            result = sync_adapter.wait_for_result(task_id, timeout=5.0)
        
        total_time = time.time() - start_time
        avg_time = total_time / task_count
        
        print(f"   总执行时间: {total_time:.3f}s")
        print(f"   平均每任务: {avg_time:.3f}s")
        print(f"   任务数量: {task_count}")
        
        # 性能基准：平均每任务不超过0.1秒
        performance_ok = avg_time < 0.1
        print(f"   性能评估: {'✅ 良好' if performance_ok else '⚠️ 需要优化'}")
        
        # 停止适配器
        sync_adapter.stop()
        return performance_ok
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("开始同步适配器系统测试...\n")
    
    # 运行所有测试
    tests = [
        ("基础功能", test_sync_adapter_basic),
        ("异步到同步执行", test_async_to_sync_execution),
        ("回调机制", test_callback_mechanism),
        ("线程安全性", test_thread_safety),
        ("错误处理", test_error_handling),
        ("性能测试", test_performance)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"测试: {test_name}")
        print(f"{'='*50}")
        
        result = test_func()
        results.append((test_name, result))
    
    # 输出测试结果摘要
    print(f"\n{'='*50}")
    print("测试结果摘要")
    print(f"{'='*50}")
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    print(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！同步适配器系统工作正常。")
    else:
        print(f"\n⚠️  有 {total - passed} 个测试失败，需要检查相关功能。")
    
    print("\n测试脚本结束")