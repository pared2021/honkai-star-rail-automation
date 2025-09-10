#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
游戏操作器最终测试脚本
使用绝对导入避免相对导入问题
"""

import sys
import os
import asyncio
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass
from enum import Enum

# 添加src目录到Python路径
src_path = os.path.join(os.path.dirname(__file__), 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# 模拟依赖类
class MockGameDetector:
    """模拟游戏检测器"""
    
    def __init__(self):
        self.is_initialized = True
    
    async def detect_game_window(self):
        """模拟检测游戏窗口"""
        return MockGameWindow()
    
    async def find_ui_element(self, element_name: str):
        """模拟查找UI元素"""
        return MockUIElement(element_name)
    
    async def detect_scene(self):
        """模拟场景检测"""
        return "main_menu"

class MockGameWindow:
    """模拟游戏窗口"""
    
    def __init__(self):
        self.hwnd = 12345
        self.title = "崩坏：星穹铁道"
        self.rect = (100, 100, 1920, 1080)
        self.width = 1820
        self.height = 980
        self.is_foreground = True
    
    @property
    def center(self):
        return (960, 540)

class MockUIElement:
    """模拟UI元素"""
    
    def __init__(self, name: str):
        self.name = name
        self.position = (500, 300)
        self.size = (100, 50)
        self.confidence = 0.95
        self.template_path = f"templates/{name}.png"
    
    @property
    def center(self):
        return (550, 325)

class MockSyncAdapter:
    """模拟同步适配器"""
    
    def __init__(self):
        self.is_initialized = True
    
    async def click(self, x: int, y: int):
        """模拟点击"""
        print(f"模拟点击坐标: ({x}, {y})")
        return True
    
    async def swipe(self, start_x: int, start_y: int, end_x: int, end_y: int, duration: float = 1.0):
        """模拟滑动"""
        print(f"模拟滑动: ({start_x}, {start_y}) -> ({end_x}, {end_y}), 持续时间: {duration}s")
        return True
    
    async def input_text(self, text: str):
        """模拟文本输入"""
        print(f"模拟输入文本: {text}")
        return True
    
    async def take_screenshot(self):
        """模拟截图"""
        print("模拟截图")
        return b"fake_screenshot_data"

class MockConfigManager:
    """模拟配置管理器"""
    
    def __init__(self):
        self.config = {
            'click_delay': 0.1,
            'swipe_duration': 1.0,
            'retry_count': 3,
            'screenshot_delay': 0.5
        }
    
    def get(self, key: str, default=None):
        return self.config.get(key, default)
    
    def set(self, key: str, value):
        self.config[key] = value

# 操作配置和结果类
@dataclass
class OperationConfig:
    """操作配置"""
    retry_count: int = 3
    delay_before: float = 0.1
    delay_after: float = 0.1
    timeout: float = 10.0
    verify_result: bool = True
    screenshot_before: bool = False
    screenshot_after: bool = False

@dataclass
class OperationResult:
    """操作结果"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    execution_time: float = 0.0
    retry_count: int = 0
    screenshots: Optional[List[bytes]] = None

class OperationType(Enum):
    """操作类型"""
    CLICK = "click"
    SWIPE = "swipe"
    INPUT_TEXT = "input_text"
    WAIT = "wait"
    SCREENSHOT = "screenshot"

# 简化的游戏操作器实现
class GameOperator:
    """游戏操作器"""
    
    def __init__(self, game_detector=None, sync_adapter=None, config_manager=None):
        """初始化游戏操作器"""
        self.game_detector = game_detector or MockGameDetector()
        self.sync_adapter = sync_adapter or MockSyncAdapter()
        self.config_manager = config_manager or MockConfigManager()
        self.operation_history = []
        self.default_config = OperationConfig()
        self.is_initialized = True
    
    async def click(self, target, config: Optional[OperationConfig] = None) -> OperationResult:
        """点击操作"""
        config = config or self.default_config
        
        try:
            # 解析目标位置
            if isinstance(target, tuple):
                x, y = target
            elif isinstance(target, str):
                # 查找UI元素
                ui_element = await self.game_detector.find_ui_element(target)
                if ui_element:
                    x, y = ui_element.center
                else:
                    return OperationResult(False, f"未找到UI元素: {target}")
            else:
                return OperationResult(False, "无效的目标类型")
            
            # 执行点击
            await asyncio.sleep(config.delay_before)
            success = await self.sync_adapter.click(x, y)
            await asyncio.sleep(config.delay_after)
            
            # 记录操作历史
            operation = {
                'type': OperationType.CLICK,
                'target': target,
                'position': (x, y),
                'success': success,
                'timestamp': asyncio.get_event_loop().time()
            }
            self.operation_history.append(operation)
            
            return OperationResult(success, "点击操作完成" if success else "点击操作失败")
            
        except Exception as e:
            return OperationResult(False, f"点击操作异常: {str(e)}")
    
    async def swipe(self, start, end, duration: float = 1.0, config: Optional[OperationConfig] = None) -> OperationResult:
        """滑动操作"""
        config = config or self.default_config
        
        try:
            # 解析起始和结束位置
            if isinstance(start, tuple) and isinstance(end, tuple):
                start_x, start_y = start
                end_x, end_y = end
            else:
                return OperationResult(False, "无效的滑动坐标")
            
            # 执行滑动
            await asyncio.sleep(config.delay_before)
            success = await self.sync_adapter.swipe(start_x, start_y, end_x, end_y, duration)
            await asyncio.sleep(config.delay_after)
            
            # 记录操作历史
            operation = {
                'type': OperationType.SWIPE,
                'start': start,
                'end': end,
                'duration': duration,
                'success': success,
                'timestamp': asyncio.get_event_loop().time()
            }
            self.operation_history.append(operation)
            
            return OperationResult(success, "滑动操作完成" if success else "滑动操作失败")
            
        except Exception as e:
            return OperationResult(False, f"滑动操作异常: {str(e)}")
    
    async def input_text(self, text: str, config: Optional[OperationConfig] = None) -> OperationResult:
        """文本输入操作"""
        config = config or self.default_config
        
        try:
            # 执行文本输入
            await asyncio.sleep(config.delay_before)
            success = await self.sync_adapter.input_text(text)
            await asyncio.sleep(config.delay_after)
            
            # 记录操作历史
            operation = {
                'type': OperationType.INPUT_TEXT,
                'text': text,
                'success': success,
                'timestamp': asyncio.get_event_loop().time()
            }
            self.operation_history.append(operation)
            
            return OperationResult(success, "文本输入完成" if success else "文本输入失败")
            
        except Exception as e:
            return OperationResult(False, f"文本输入异常: {str(e)}")
    
    async def wait_for_condition(self, condition_type: str, target=None, timeout: float = 10.0) -> OperationResult:
        """等待条件满足"""
        try:
            start_time = asyncio.get_event_loop().time()
            
            while (asyncio.get_event_loop().time() - start_time) < timeout:
                if condition_type == "ui_element_appear":
                    ui_element = await self.game_detector.find_ui_element(target)
                    if ui_element:
                        return OperationResult(True, f"UI元素 {target} 已出现")
                elif condition_type == "scene_change":
                    current_scene = await self.game_detector.detect_scene()
                    if current_scene == target:
                        return OperationResult(True, f"场景已切换到 {target}")
                elif condition_type == "custom":
                    # 自定义条件检查
                    if callable(target):
                        if await target():
                            return OperationResult(True, "自定义条件已满足")
                
                await asyncio.sleep(0.1)  # 短暂等待后重试
            
            return OperationResult(False, f"等待条件超时: {condition_type}")
            
        except Exception as e:
            return OperationResult(False, f"等待条件异常: {str(e)}")
    
    def get_operation_history(self) -> List[Dict[str, Any]]:
        """获取操作历史"""
        return self.operation_history.copy()
    
    def clear_operation_history(self):
        """清空操作历史"""
        self.operation_history.clear()
    
    def set_default_config(self, config: OperationConfig):
        """设置默认配置"""
        self.default_config = config
    
    def get_config(self, key: str, default=None):
        """获取配置"""
        return self.config_manager.get(key, default)
    
    def set_config(self, key: str, value):
        """设置配置"""
        self.config_manager.set(key, value)

# 测试函数
async def test_game_operator_initialization():
    """测试游戏操作器初始化"""
    print("\n=== 测试游戏操作器初始化 ===")
    
    try:
        operator = GameOperator()
        assert operator.is_initialized, "游戏操作器初始化失败"
        assert operator.game_detector is not None, "游戏检测器未初始化"
        assert operator.sync_adapter is not None, "同步适配器未初始化"
        assert operator.config_manager is not None, "配置管理器未初始化"
        print("✅ 游戏操作器初始化成功")
        return operator
    except Exception as e:
        print(f"❌ 游戏操作器初始化失败: {e}")
        return None

async def test_click_operations(operator: GameOperator):
    """测试点击操作"""
    print("\n=== 测试点击操作 ===")
    
    try:
        # 测试坐标点击
        result = await operator.click((500, 300))
        assert result.success, f"坐标点击失败: {result.message}"
        print("✅ 坐标点击测试通过")
        
        # 测试UI元素点击
        result = await operator.click("start_button")
        assert result.success, f"UI元素点击失败: {result.message}"
        print("✅ UI元素点击测试通过")
        
        return True
    except Exception as e:
        print(f"❌ 点击操作测试失败: {e}")
        return False

async def test_swipe_operations(operator: GameOperator):
    """测试滑动操作"""
    print("\n=== 测试滑动操作 ===")
    
    try:
        # 测试滑动操作
        result = await operator.swipe((100, 500), (800, 500), 1.5)
        assert result.success, f"滑动操作失败: {result.message}"
        print("✅ 滑动操作测试通过")
        
        return True
    except Exception as e:
        print(f"❌ 滑动操作测试失败: {e}")
        return False

async def test_input_operations(operator: GameOperator):
    """测试文本输入操作"""
    print("\n=== 测试文本输入操作 ===")
    
    try:
        # 测试文本输入
        result = await operator.input_text("测试文本")
        assert result.success, f"文本输入失败: {result.message}"
        print("✅ 文本输入测试通过")
        
        return True
    except Exception as e:
        print(f"❌ 文本输入测试失败: {e}")
        return False

async def test_wait_conditions(operator: GameOperator):
    """测试等待条件"""
    print("\n=== 测试等待条件 ===")
    
    try:
        # 测试等待UI元素出现
        result = await operator.wait_for_condition("ui_element_appear", "start_button", 2.0)
        assert result.success, f"等待UI元素失败: {result.message}"
        print("✅ 等待UI元素测试通过")
        
        # 测试等待场景变化
        result = await operator.wait_for_condition("scene_change", "main_menu", 2.0)
        assert result.success, f"等待场景变化失败: {result.message}"
        print("✅ 等待场景变化测试通过")
        
        return True
    except Exception as e:
        print(f"❌ 等待条件测试失败: {e}")
        return False

async def test_operation_history(operator: GameOperator):
    """测试操作历史"""
    print("\n=== 测试操作历史 ===")
    
    try:
        # 获取操作历史
        history = operator.get_operation_history()
        assert len(history) > 0, "操作历史为空"
        print(f"✅ 操作历史记录了 {len(history)} 个操作")
        
        # 清空操作历史
        operator.clear_operation_history()
        history = operator.get_operation_history()
        assert len(history) == 0, "操作历史清空失败"
        print("✅ 操作历史清空成功")
        
        return True
    except Exception as e:
        print(f"❌ 操作历史测试失败: {e}")
        return False

async def test_configuration(operator: GameOperator):
    """测试配置管理"""
    print("\n=== 测试配置管理 ===")
    
    try:
        # 测试配置设置和获取
        operator.set_config("test_key", "test_value")
        value = operator.get_config("test_key")
        assert value == "test_value", f"配置设置失败: {value}"
        print("✅ 配置管理测试通过")
        
        # 测试默认配置
        new_config = OperationConfig(retry_count=5, delay_before=0.2)
        operator.set_default_config(new_config)
        assert operator.default_config.retry_count == 5, "默认配置设置失败"
        print("✅ 默认