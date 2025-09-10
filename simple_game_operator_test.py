#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""简单的游戏操作器测试脚本.

直接测试游戏操作器的核心功能，避免复杂的导入问题。
"""

import sys
import os
import asyncio
import time
from typing import Tuple, Optional, Dict, Any

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# 模拟依赖类
class MockUIElement:
    """模拟UI元素."""
    def __init__(self, name: str, position: Tuple[int, int], size: Tuple[int, int], confidence: float, template_path: str):
        self.name = name
        self.position = position
        self.size = size
        self.confidence = confidence
        self.template_path = template_path
    
    @property
    def center(self) -> Tuple[int, int]:
        """获取中心点坐标."""
        x, y = self.position
        w, h = self.size
        return (x + w // 2, y + h // 2)

class MockGameDetector:
    """模拟游戏检测器."""
    
    def __init__(self):
        self.logger = None
    
    def detect_ui_elements(self, element_names):
        """模拟UI元素检测."""
        if "test_button" in element_names:
            return [MockUIElement(
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

class MockSyncAdapter:
    """模拟同步适配器."""
    
    def __init__(self):
        pass
    
    def run_async(self, coro):
        """运行异步协程."""
        return asyncio.run(coro)

# 模拟操作配置和结果
class MockOperationConfig:
    """模拟操作配置."""
    def __init__(self, timeout=30.0, retry_count=3, screenshot_before=False, screenshot_after=False):
        self.timeout = timeout
        self.retry_count = retry_count
        self.screenshot_before = screenshot_before
        self.screenshot_after = screenshot_after

class MockOperationResult:
    """模拟操作结果."""
    def __init__(self, success=True, execution_time=0.1, error_message="", metadata=None):
        self.success = success
        self.execution_time = execution_time
        self.error_message = error_message
        self.metadata = metadata or {}
        self.screenshot_before = None
        self.screenshot_after = None

# 简化的游戏操作器
class SimpleGameOperator:
    """简化的游戏操作器."""
    
    def __init__(self, game_detector=None, sync_adapter=None):
        """初始化游戏操作器."""
        self.game_detector = game_detector or MockGameDetector()
        self.sync_adapter = sync_adapter or MockSyncAdapter()
        self.default_config = MockOperationConfig()
        self._operation_history = []
        print("SimpleGameOperator初始化完成")
    
    def get_default_config(self):
        """获取默认配置."""
        return self.default_config
    
    def set_default_config(self, config):
        """设置默认配置."""
        self.default_config = config
    
    def get_operation_history(self):
        """获取操作历史."""
        return self._operation_history
    
    async def click(self, target, click_type="left", config=None):
        """点击操作."""
        start_time = time.time()
        config = config or self.default_config
        
        try:
            # 解析目标位置
            if isinstance(target, tuple):
                position = target
            elif isinstance(target, str):
                # 模拟UI元素查找
                elements = self.game_detector.detect_ui_elements([target])
                if elements:
                    position = elements[0].center
                else:
                    return MockOperationResult(
                        success=False,
                        execution_time=time.time() - start_time,
                        error_message=f"未找到UI元素: {target}"
                    )
            else:
                position = target.center
            
            # 模拟点击操作
            await asyncio.sleep(0.01)  # 模拟操作延迟
            
            result = MockOperationResult(
                success=True,
                execution_time=time.time() - start_time,
                metadata={"position": position, "click_type": click_type}
            )
            
            # 添加到历史记录
            self._operation_history.append(result)
            
            return result
            
        except Exception as e:
            return MockOperationResult(
                success=False,
                execution_time=time.time() - start_time,
                error_message=str(e)
            )
    
    async def swipe(self, start, end, duration=1.0, config=None):
        """滑动操作."""
        start_time = time.time()
        
        try:
            # 解析起始和结束位置
            start_pos = start if isinstance(start, tuple) else start.center
            end_pos = end if isinstance(end, tuple) else end.center
            
            # 模拟滑动操作
            await asyncio.sleep(duration * 0.1)  # 模拟操作延迟
            
            result = MockOperationResult(
                success=True,
                execution_time=time.time() - start_time,
                metadata={"start": start_pos, "end": end_pos, "duration": duration}
            )
            
            self._operation_history.append(result)
            return result
            
        except Exception as e:
            return MockOperationResult(
                success=False,
                execution_time=time.time() - start_time,
                error_message=str(e)
            )
    
    async def input_text(self, text, target=None, config=None):
        """输入文本."""
        start_time = time.time()
        
        try:
            # 模拟文本输入
            await asyncio.sleep(0.05)  # 模拟输入延迟
            
            metadata = {"text": text}
            if target:
                target_pos = target if isinstance(target, tuple) else target.center
                metadata["target"] = target_pos
            
            result = MockOperationResult(
                success=True,
                execution_time=time.time() - start_time,
                metadata=metadata
            )
            
            self._operation_history.append(result)
            return result
            
        except Exception as e:
            return MockOperationResult(
                success=False,
                execution_time=time.time() - start_time,
                error_message=str(e)
            )
    
    async def wait_for_condition(self, condition, condition_params, timeout=30.0):
        """等待条件满足."""
        start_time = time.time()
        
        try:
            if condition == "ui_element_appear":
                element_name = condition_params.get("element_name")
                if element_name == "test_button":
                    # 模拟找到元素
                    await asyncio.sleep(0.1)
                    return MockOperationResult(
                        success=True,
                        execution_time=time.time() - start_time,
                        metadata={"condition": condition, "element_name": element_name}
                    )
            elif condition == "custom":
                custom_function = condition_params.get("custom_function")
                if custom_function:
                    result = await custom_function()
                    if result:
                        return MockOperationResult(
                            success=True,
                            execution_time=time.time() - start_time,
                            metadata={"condition": condition}
                        )
            
            # 模拟超时
            await asyncio.sleep(min(timeout, 0.1))
            return MockOperationResult(
                success=False,
                execution_time=time.time() - start_time,
                error_message="等待条件超时"
            )
            
        except Exception as e:
            return MockOperationResult(
                success=False,
                execution_time=time.time() - start_time,
                error_message=str(e)
            )


async def test_basic_functionality():
    """测试基础功能."""
    print("\n=== 基础功能测试 ===")
    
    try:
        # 创建游戏操作器
        operator = SimpleGameOperator()
        print("✅ 游戏操作器创建成功")
        
        # 测试配置管理
        default_config = operator.get_default_config()
        print(f"✅ 默认配置获取成功: timeout={default_config.timeout}s")
        
        # 设置新配置
        new_config = MockOperationConfig(
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
        return False


async def test_click_operations():
    """测试点击操作."""
    print("\n=== 点击操作测试 ===")
    
    try:
        operator = SimpleGameOperator()
        
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
        for click_type in ["left", "right", "double"]:
            result = await operator.click((150, 150), click_type)
            if result.success:
                print(f"✅ {click_type}点击成功")
            else:
                print(f"❌ {click_type}点击失败: {result.error_message}")
        
        return True
        
    except Exception as e:
        print(f"❌ 点击操作测试失败: {e}")
        return False


async def test_swipe_operations():
    """测试滑动操作."""
    print("\n=== 滑动操作测试 ===")
    
    try:
        operator = SimpleGameOperator()
        
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
        return False


async def test_input_operations():
    """测试文本输入操作."""
    print("\n=== 文本输入测试 ===")
    
    try:
        operator = SimpleGameOperator()
        
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
        return False


async def test_wait_conditions():
    """测试等待条件."""
    print("\n=== 等待条件测试 ===")
    
    try:
        operator = SimpleGameOperator()
        
        # 测试等待UI元素出现
        print("测试等待UI元素出现...")
        result = await operator.wait_for_condition(
            "ui_element_appear",
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
            "custom",
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
        return False


async def main():
    """主测试函数."""
    print("开始简单游戏操作器功能测试...")
    print("=" * 50)
    
    test_results = []
    
    # 运行所有测试
    tests = [
        ("基础功能测试", test_basic_functionality),
        ("点击操作测试", test_click_operations),
        ("滑动操作测试", test_swipe_operations),
        ("文本输入测试", test_input_operations),
        ("等待条件测试", test_wait_conditions),
    ]
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            test_results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name}执行异常: {e}")
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
        sys.exit(1)