#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
游戏操作器完整功能测试
测试GameOperator的所有核心功能实现
"""

import sys
import os
import asyncio
import time
from typing import Dict, Any, Optional, Tuple

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    # 导入核心模块
    from core.game_operator import (
        GameOperator, OperationConfig, OperationResult, 
        ClickType, OperationMethod, WaitCondition
    )
    from core.game_detector import GameDetector, UIElement, SceneType
    from core.sync_adapter import SyncAdapter
    from config.config_manager import ConfigManager
    print("✅ 所有模块导入成功")
except ImportError as e:
    print(f"❌ 导入模块失败: {e}")
    sys.exit(1)

class MockGameDetector:
    """模拟游戏检测器"""
    
    def __init__(self):
        self.current_scene = SceneType.MAIN_MENU
        self.ui_elements = {
            'start_button': UIElement(name='start_button', center=(100, 100), confidence=0.9),
            'settings_button': UIElement(name='settings_button', center=(200, 200), confidence=0.8),
            'exit_button': UIElement(name='exit_button', center=(300, 300), confidence=0.7)
        }
    
    def detect_scene(self) -> SceneType:
        return self.current_scene
    
    def detect_ui_elements(self, element_names: list) -> list:
        return [self.ui_elements[name] for name in element_names if name in self.ui_elements]
    
    def capture_screen(self) -> Optional[bytes]:
        return b'mock_screenshot_data'
    
    def find_template(self, template_path: str) -> Optional[Tuple[int, int]]:
        # 模拟模板匹配
        return (150, 150)

class MockSyncAdapter:
    """模拟同步适配器"""
    
    def __init__(self):
        pass
    
    def sync_call(self, async_func, *args, **kwargs):
        """同步调用异步函数"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(async_func(*args, **kwargs))
        finally:
            loop.close()

class MockConfigManager:
    """模拟配置管理器"""
    
    def __init__(self):
        self.config = {
            'operation': {
                'default_timeout': 30.0,
                'retry_count': 2,
                'screenshot_before': False,
                'screenshot_after': False,
                'verify_result': True,
                'method': 'pyautogui'
            }
        }
    
    def get(self, key: str, default=None):
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

async def test_game_operator_initialization():
    """测试游戏操作器初始化"""
    print("\n=== 游戏操作器初始化测试 ===")
    
    try:
        # 创建模拟依赖
        game_detector = MockGameDetector()
        sync_adapter = MockSyncAdapter()
        config_manager = MockConfigManager()
        
        # 创建游戏操作器
        operator = GameOperator(game_detector, sync_adapter, config_manager)
        
        # 检查初始化状态
        assert operator.game_detector is not None
        assert operator.sync_adapter is not None
        assert operator.config_manager is not None
        assert operator.default_config is not None
        assert len(operator.get_operation_history()) == 0
        
        print("✅ 游戏操作器初始化成功")
        return operator
        
    except Exception as e:
        print(f"❌ 游戏操作器初始化失败: {e}")
        return None

async def test_click_operations(operator: GameOperator):
    """测试点击操作"""
    print("\n=== 点击操作测试 ===")
    
    try:
        # 测试坐标点击
        result = await operator.click((100, 100), ClickType.LEFT)
        assert isinstance(result, OperationResult)
        print(f"✅ 坐标点击测试: {result.success}")
        
        # 测试UI元素点击
        result = await operator.click('start_button', ClickType.LEFT)
        assert isinstance(result, OperationResult)
        print(f"✅ UI元素点击测试: {result.success}")
        
        # 测试不同点击类型
        for click_type in [ClickType.RIGHT, ClickType.MIDDLE, ClickType.DOUBLE]:
            result = await operator.click((200, 200), click_type)
            print(f"✅ {click_type.value}点击测试: {result.success}")
        
        # 测试带配置的点击
        config = OperationConfig(
            timeout=10.0,
            retry_count=1,
            screenshot_before=True,
            screenshot_after=True
        )
        result = await operator.click((300, 300), config=config)
        print(f"✅ 带配置点击测试: {result.success}")
        
        return True
        
    except Exception as e:
        print(f"❌ 点击操作测试失败: {e}")
        return False

async def test_swipe_operations(operator: GameOperator):
    """测试滑动操作"""
    print("\n=== 滑动操作测试 ===")
    
    try:
        # 测试坐标滑动
        result = await operator.swipe((100, 100), (200, 200), duration=1.0)
        assert isinstance(result, OperationResult)
        print(f"✅ 坐标滑动测试: {result.success}")
        
        # 测试UI元素滑动
        result = await operator.swipe('start_button', 'settings_button', duration=0.5)
        assert isinstance(result, OperationResult)
        print(f"✅ UI元素滑动测试: {result.success}")
        
        # 测试不同持续时间的滑动
        for duration in [0.3, 1.0, 2.0]:
            result = await operator.swipe((50, 50), (150, 150), duration=duration)
            print(f"✅ {duration}秒滑动测试: {result.success}")
        
        return True
        
    except Exception as e:
        print(f"❌ 滑动操作测试失败: {e}")
        return False

async def test_text_input_operations(operator: GameOperator):
    """测试文本输入操作"""
    print("\n=== 文本输入测试 ===")
    
    try:
        # 测试无目标文本输入
        result = await operator.input_text("Hello World")
        assert isinstance(result, OperationResult)
        print(f"✅ 无目标文本输入测试: {result.success}")
        
        # 测试有目标文本输入
        result = await operator.input_text("Test Input", target=(100, 100))
        assert isinstance(result, OperationResult)
        print(f"✅ 有目标文本输入测试: {result.success}")
        
        # 测试UI元素文本输入
        result = await operator.input_text("UI Element Input", target='start_button')
        assert isinstance(result, OperationResult)
        print(f"✅ UI元素文本输入测试: {result.success}")
        
        # 测试特殊字符输入
        special_text = "!@#$%^&*()_+-=[]{}|;':,.<>?"
        result = await operator.input_text(special_text)
        print(f"✅ 特殊字符输入测试: {result.success}")
        
        return True
        
    except Exception as e:
        print(f"❌ 文本输入测试失败: {e}")
        return False

async def test_wait_conditions(operator: GameOperator):
    """测试等待条件"""
    print("\n=== 等待条件测试 ===")
    
    try:
        # 测试等待UI元素出现
        result = await operator.wait_for_condition(
            WaitCondition.UI_ELEMENT_APPEAR,
            {"element_name": "start_button"},
            timeout=5.0
        )
        assert isinstance(result, OperationResult)
        print(f"✅ 等待UI元素出现测试: {result.success}")
        
        # 测试等待UI元素消失
        result = await operator.wait_for_condition(
            WaitCondition.UI_ELEMENT_DISAPPEAR,
            {"element_name": "nonexistent_button"},
            timeout=2.0
        )
        print(f"✅ 等待UI元素消失测试: {result.success}")
        
        # 测试等待场景切换
        result = await operator.wait_for_condition(
            WaitCondition.SCENE_CHANGE,
            {"target_scene": "MAIN_MENU"},
            timeout=3.0
        )
        print(f"✅ 等待场景切换测试: {result.success}")
        
        # 测试自定义等待条件
        async def custom_condition():
            return True  # 总是返回True
        
        result = await operator.wait_for_condition(
            WaitCondition.CUSTOM,
            {"custom_function": custom_condition},
            timeout=1.0
        )
        print(f"✅ 自定义等待条件测试: {result.success}")
        
        return True
        
    except Exception as e:
        print(f"❌ 等待条件测试失败: {e}")
        return False

async def test_operation_history(operator: GameOperator):
    """测试操作历史"""
    print("\n=== 操作历史测试 ===")
    
    try:
        # 获取当前历史记录数量
        initial_count = len(operator.get_operation_history())
        
        # 执行一些操作
        await operator.click((100, 100))
        await operator.swipe((100, 100), (200, 200))
        await operator.input_text("test")
        
        # 检查历史记录是否增加
        final_count = len(operator.get_operation_history())
        assert final_count > initial_count
        print(f"✅ 操作历史记录: {initial_count} -> {final_count}")
        
        # 测试清空历史
        operator.clear_operation_history()
        assert len(operator.get_operation_history()) == 0
        print("✅ 清空操作历史成功")
        
        return True
        
    except Exception as e:
        print(f"❌ 操作历史测试失败: {e}")
        return False

async def test_configuration_management(operator: GameOperator):
    """测试配置管理"""
    print("\n=== 配置管理测试 ===")
    
    try:
        # 获取默认配置
        default_config = operator.get_default_config()
        assert isinstance(default_config, OperationConfig)
        print("✅ 获取默认配置成功")
        
        # 设置新的默认配置
        new_config = OperationConfig(
            timeout=60.0,
            retry_count=5,
            screenshot_before=True,
            screenshot_after=True,
            verify_result=False,
            method=OperationMethod.WIN32_API
        )
        operator.set_default_config(new_config)
        
        # 验证配置是否更新
        updated_config = operator.get_default_config()
        assert updated_config.timeout == 60.0
        assert updated_config.retry_count == 5
        print("✅ 设置默认配置成功")
        
        return True
        
    except Exception as e:
        print(f"❌ 配置管理测试失败: {e}")
        return False

async def main():
    """主测试函数"""
    print("开始游戏操作器完整功能测试...")
    
    # 初始化测试
    operator = await test_game_operator_initialization()
    if not operator:
        print("\n❌ 初始化失败，终止测试")
        return
    
    # 运行所有测试
    tests = [
        ("点击操作", test_click_operations),
        ("滑动操作", test_swipe_operations),
        ("文本输入", test_text_input_operations),
        ("等待条件", test_wait_conditions),
        ("操作历史", test_operation_history),
        ("配置管理", test_configuration_management)
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = await test_func(operator)
        except Exception as e:
            print(f"❌ {test_name}测试异常: {e}")
            results[test_name] = False
    
    # 输出测试结果摘要
    print("\n" + "="*50)
    print("测试结果摘要")
    print("="*50)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results.items():
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{test_name}: {status}")
        if success:
            passed += 1
    
    print(f"\n总计: {total} 个测试")
    print(f"通过: {passed} 个")
    print(f"失败: {total - passed} 个")
    
    if passed == total:
        print("\n🎉 所有游戏操作器功能测试通过！")
    else:
        print(f"\n⚠️  有 {total - passed} 个测试失败，需要进一步检查")

if __name__ == "__main__":
    asyncio.run(main())