#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""游戏操作器功能测试脚本.

测试游戏操作器的核心功能，包括点击、滑动、文本输入等操作。
"""

import asyncio
import sys
import os
import time
from typing import Tuple, Optional

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    # 使用绝对导入
    import core.game_operator as game_op
    import core.game_detector as game_det
    import core.sync_adapter as sync_ad
    import config.config_manager as config_mgr
except ImportError as e:
    print(f"导入模块失败: {e}")
    print("请确保所有依赖模块都已正确安装")
    sys.exit(1)


class MockGameDetector:
    """模拟游戏检测器."""
    
    def __init__(self):
        self.logger = None
    
    def detect_ui_elements(self, element_names):
        """模拟UI元素检测."""
        if "test_button" in element_names:
            return [game_det.UIElement(
                name="test_button",
                position=(100, 100),
                size=(100, 50),
                confidence=0.9,
                template_path="test_button.png"
            )]
        return []
    
    def capture_screen(self):
        """模拟屏幕截图."""
        return b"fake_screenshot_data"
    
    def detect_scene(self):
        """模拟场景检测."""
        return game_det.SceneType.MAIN_MENU
    
    def get_game_window(self):
        """模拟获取游戏窗口."""
        return game_det.GameWindow(
            hwnd=12345,
            title="崩坏星穹铁道",
            rect=(0, 0, 1920, 1080),
            width=1920,
            height=1080,
            is_foreground=True
        )


class MockSyncAdapter:
    """模拟同步适配器."""
    
    def __init__(self):
        pass
    
    def run_async(self, coro):
        """运行异步协程."""
        return asyncio.run(coro)


async def test_game_operator_basic_functionality():
    """测试游戏操作器基础功能."""
    print("\n=== 游戏操作器基础功能测试 ===")
    
    try:
        # 创建模拟依赖
        mock_detector = MockGameDetector()
        mock_adapter = MockSyncAdapter()
        
        # 创建游戏操作器实例
        operator = game_op.GameOperator(
            game_detector=mock_detector,
            sync_adapter=mock_adapter
        )
        
        print("✅ 游戏操作器创建成功")
        
        # 测试配置管理
        default_config = operator.get_default_config()
        print(f"✅ 默认配置获取成功: timeout={default_config.timeout}s")
        
        # 设置新配置
        new_config = game_op.OperationConfig(
            timeout=60.0,
            retry_count=5,
            screenshot_before=True
        )
        operator.set_default_config(new_config)
        updated_config = operator.get_default_config()
        print(f"✅ 配置更新成功: timeout={updated_config.timeout}s, retry_count={updated_config.retry_count}")
        
        # 测试操作历史
        history = operator.get_operation_history()
        print(f"✅ 操作历史获取成功: {len(history)} 条记录")
        
        return True
        
    except Exception as e:
        print(f"❌ 基础功能测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_click_operations():
    """测试点击操作."""
    print("\n=== 点击操作测试 ===")
    
    try:
        # 创建模拟依赖
        mock_detector = MockGameDetector()
        mock_adapter = MockSyncAdapter()
        
        # 创建游戏操作器实例
        operator = game_op.GameOperator(
            game_detector=mock_detector,
            sync_adapter=mock_adapter
        )
        
        # 测试坐标点击
        print("测试坐标点击...")
        result = await operator.click((100, 200))
        if result.success:
            print(f"✅ 坐标点击成功: 位置({result.metadata.get('position')})")
        else:
            print(f"❌ 坐标点击失败: {result.error_message}")
        
        # 测试UI元素点击
        print("测试UI元素点击...")
        result = await operator.click("test_button")
        if result.success:
            print(f"✅ UI元素点击成功: 位置({result.metadata.get('position')})")
        else:
            print(f"❌ UI元素点击失败: {result.error_message}")
        
        # 测试不同点击类型
        print("测试不同点击类型...")
        for click_type in [game_op.ClickType.LEFT, game_op.ClickType.RIGHT, game_op.ClickType.DOUBLE]:
            result = await operator.click((150, 150), click_type)
            if result.success:
                print(f"✅ {click_type.value}点击成功")
            else:
                print(f"❌ {click_type.value}点击失败: {result.error_message}")
        
        return True
        
    except Exception as e:
        print(f"❌ 点击操作测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_swipe_operations():
    """测试滑动操作."""
    print("\n=== 滑动操作测试 ===")
    
    try:
        # 创建模拟依赖
        mock_detector = MockGameDetector()
        mock_adapter = MockSyncAdapter()
        
        # 创建游戏操作器实例
        operator = game_op.GameOperator(
            game_detector=mock_detector,
            sync_adapter=mock_adapter
        )
        
        # 测试坐标滑动
        print("测试坐标滑动...")
        result = await operator.swipe(
            start=(100, 100),
            end=(200, 200),
            duration=1.0
        )
        if result.success:
            print(f"✅ 坐标滑动成功: {result.metadata.get('start')} -> {result.metadata.get('end')}")
        else:
            print(f"❌ 坐标滑动失败: {result.error_message}")
        
        return True
        
    except Exception as e:
        print(f"❌ 滑动操作测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_input_operations():
    """测试文本输入操作."""
    print("\n=== 文本输入测试 ===")
    
    try:
        # 创建模拟依赖
        mock_detector = MockGameDetector()
        mock_adapter = MockSyncAdapter()
        
        # 创建游戏操作器实例
        operator = game_op.GameOperator(
            game_detector=mock_detector,
            sync_adapter=mock_adapter
        )
        
        # 测试无目标文本输入
        print("测试无目标文本输入...")
        result = await operator.input_text("Hello World")
        if result.success:
            print(f"✅ 无目标文本输入成功: '{result.metadata.get('text')}'")
        else:
            print(f"❌ 无目标文本输入失败: {result.error_message}")
        
        # 测试有目标文本输入
        print("测试有目标文本输入...")
        result = await operator.input_text("Test Input", target=(100, 100))
        if result.success:
            print(f"✅ 有目标文本输入成功: '{result.metadata.get('text')}' at {result.metadata.get('target')}")
        else:
            print(f"❌ 有目标文本输入失败: {result.error_message}")
        
        return True
        
    except Exception as e:
        print(f"❌ 文本输入测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_wait_conditions():
    """测试等待条件."""
    print("\n=== 等待条件测试 ===")
    
    try:
        # 创建模拟依赖
        mock_detector = MockGameDetector()
        mock_adapter = MockSyncAdapter()
        
        # 创建游戏操作器实例
        operator = game_op.GameOperator(
            game_detector=mock_detector,
            sync_adapter=mock_adapter
        )
        
        # 测试等待UI元素出现
        print("测试等待UI元素出现...")
        result = await operator.wait_for_condition(
            game_op.WaitCondition.UI_ELEMENT_APPEAR,
            {"element_name": "test_button"},
            timeout=2.0
        )
        if result.success:
            print("✅ 等待UI元素出现成功")
        else:
            print(f"❌ 等待UI元素出现失败: {result.error_message}")
        
        # 测试自定义等待条件
        print("测试自定义等待条件...")
        
        async def custom_condition():
            return True  # 立即返回True
        
        result = await operator.wait_for_condition(
            game_op.WaitCondition.CUSTOM,
            {"custom_function": custom_condition},
            timeout=1.0
        )
        if result.success:
            print("✅ 自定义等待条件成功")
        else:
            print(f"❌ 自定义等待条件失败: {result.error_message}")
        
        return True
        
    except Exception as e:
        print(f"❌ 等待条件测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_operation_with_config():
    """测试带配置的操作."""
    print("\n=== 配置操作测试 ===")
    
    try:
        # 创建模拟依赖
        mock_detector = MockGameDetector()
        mock_adapter = MockSyncAdapter()
        
        # 创建游戏操作器实例
        operator = game_op.GameOperator(
            game_detector=mock_detector,
            sync_adapter=mock_adapter
        )
        
        # 测试带截图的操作
        print("测试带截图的操作...")
        config = game_op.OperationConfig(
            screenshot_before=True,
            screenshot_after=True,
            timeout=10.0
        )
        
        result = await operator.click((100, 100), config=config)
        if result.success:
            has_before = result.screenshot_before is not None
            has_after = result.screenshot_after is not None
            print(f"✅ 带截图操作成功: 前截图={has_before}, 后截图={has_after}")
        else:
            print(f"❌ 带截图操作失败: {result.error_message}")
        
        return True
        
    except Exception as e:
        print(f"❌ 配置操作测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主测试函数."""
    print("开始游戏操作器功能测试...")
    print("=" * 50)
    
    test_results = []
    
    # 运行所有测试
    tests = [
        ("基础功能测试", test_game_operator_basic_functionality),
        ("点击操作测试", test_click_operations),
        ("滑动操作测试", test_swipe_operations),
        ("文本输入测试", test_input_operations),
        ("等待条件测试", test_wait_conditions),
        ("配置操作测试", test_operation_with_config),
    ]
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            test_results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name}执行异常: {e}")
            import traceback
            traceback.print_exc()
            test_results.append((test_name, False))
    
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
        print("\n🎉 所有游戏操作器功能测试通过！")
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
        import traceback
        traceback.print_exc()
        sys.exit(1)