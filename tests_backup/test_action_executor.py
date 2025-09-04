#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ActionExecutor单元测试
测试基础操作模块的各种功能
"""

import unittest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.action_executor import (
    ActionExecutor, ActionResult, ActionType, ClickType, WaitType, LoopType,
    ClickAction, KeyAction, WaitAction, LoopAction
)


class TestActionExecutor(unittest.TestCase):
    """ActionExecutor测试类"""
    
    def setUp(self):
        """测试前置设置"""
        self.executor = ActionExecutor()
    
    def test_init(self):
        """测试初始化"""
        self.assertIsNotNone(self.executor)
        self.assertFalse(self.executor.is_running)
        self.assertIsNone(self.executor.current_action)
        
        # 检查统计信息初始化
        stats = self.executor.get_execution_stats()
        self.assertEqual(stats['total_actions'], 0)
        self.assertEqual(stats['successful_actions'], 0)
        self.assertEqual(stats['failed_actions'], 0)
        self.assertEqual(stats['success_rate'], 0.0)
    
    def test_random_offset(self):
        """测试随机偏移量生成"""
        offset_x, offset_y = self.executor.get_random_offset(5)
        self.assertIsInstance(offset_x, int)
        self.assertIsInstance(offset_y, int)
        self.assertTrue(-5 <= offset_x <= 5)
        self.assertTrue(-5 <= offset_y <= 5)
    
    def test_random_delay(self):
        """测试随机延迟"""
        base_delay = 1.0
        actual_delay = self.executor.add_random_delay(base_delay, 0.1)
        self.assertIsInstance(actual_delay, float)
        self.assertTrue(0.9 <= actual_delay <= 1.1)
    
    def test_click_action_creation(self):
        """测试ClickAction创建"""
        # 测试基本创建
        action = ClickAction(x=100, y=200)
        self.assertEqual(action.x, 100)
        self.assertEqual(action.y, 200)
        self.assertEqual(action.click_type, ClickType.SINGLE)
        
        # 测试字符串类型转换
        action = ClickAction(x=100, y=200, click_type="double")
        self.assertEqual(action.click_type, ClickType.DOUBLE)
    
    def test_key_action_creation(self):
        """测试KeyAction创建"""
        action = KeyAction(keys="space")
        self.assertEqual(action.keys, "space")
        self.assertEqual(action.action_type, "press")
        
        action = KeyAction(keys=["ctrl", "c"], action_type="combination")
        self.assertEqual(action.keys, ["ctrl", "c"])
        self.assertEqual(action.action_type, "combination")
    
    def test_wait_action_creation(self):
        """测试WaitAction创建"""
        action = WaitAction(wait_type="fixed", duration=2.0)
        self.assertEqual(action.wait_type, WaitType.FIXED)
        self.assertEqual(action.duration, 2.0)
    
    def test_loop_action_creation(self):
        """测试LoopAction创建"""
        action = LoopAction(loop_type="count", count=5)
        self.assertEqual(action.loop_type, LoopType.COUNT)
        self.assertEqual(action.count, 5)
        self.assertEqual(action.actions, [])
    
    @patch('src.core.action_executor.pyautogui')
    async def test_execute_click_single(self, mock_pyautogui):
        """测试单次点击执行"""
        action = ClickAction(x=100, y=200, click_type=ClickType.SINGLE)
        result = await self.executor.execute_click(action)
        
        self.assertTrue(result.success)
        self.assertIn("Click executed successfully", result.message)
        mock_pyautogui.click.assert_called_once()
    
    @patch('src.core.action_executor.pyautogui')
    async def test_execute_click_double(self, mock_pyautogui):
        """测试双击执行"""
        action = ClickAction(x=100, y=200, click_type=ClickType.DOUBLE)
        result = await self.executor.execute_click(action)
        
        self.assertTrue(result.success)
        mock_pyautogui.doubleClick.assert_called_once()
    
    @patch('src.core.action_executor.pyautogui')
    async def test_execute_click_right(self, mock_pyautogui):
        """测试右键点击执行"""
        action = ClickAction(x=100, y=200, click_type=ClickType.RIGHT)
        result = await self.executor.execute_click(action)
        
        self.assertTrue(result.success)
        mock_pyautogui.rightClick.assert_called_once()
    
    @patch('src.core.action_executor.pyautogui')
    async def test_execute_click_continuous(self, mock_pyautogui):
        """测试连续点击执行"""
        action = ClickAction(x=100, y=200, click_type=ClickType.CONTINUOUS, count=3)
        result = await self.executor.execute_click(action)
        
        self.assertTrue(result.success)
        self.assertEqual(mock_pyautogui.click.call_count, 3)
    
    @patch('src.core.action_executor.pyautogui')
    async def test_execute_key_press(self, mock_pyautogui):
        """测试按键执行"""
        action = KeyAction(keys="space", action_type="press")
        result = await self.executor.execute_key_action(action)
        
        self.assertTrue(result.success)
        mock_pyautogui.press.assert_called_once_with("space")
    
    @patch('src.core.action_executor.pyautogui')
    async def test_execute_key_combination(self, mock_pyautogui):
        """测试组合键执行"""
        action = KeyAction(keys=["ctrl", "c"], action_type="combination")
        result = await self.executor.execute_key_action(action)
        
        self.assertTrue(result.success)
        mock_pyautogui.hotkey.assert_called_once_with("ctrl", "c")
    
    @patch('src.core.action_executor.pyautogui')
    async def test_execute_text_input(self, mock_pyautogui):
        """测试文本输入"""
        text = "Hello World"
        result = await self.executor.execute_text_input(text)
        
        self.assertTrue(result.success)
        self.assertIn("Text input completed", result.message)
        mock_pyautogui.typewrite.assert_called_once_with(text, interval=0.01)
    
    async def test_execute_wait_fixed(self):
        """测试固定等待"""
        action = WaitAction(wait_type=WaitType.FIXED, duration=0.1)
        result = await self.executor.execute_wait(action)
        
        self.assertTrue(result.success)
        self.assertIn("Wait completed", result.message)
        self.assertGreaterEqual(result.execution_time, 0.1)
    
    async def test_execute_wait_random(self):
        """测试随机等待"""
        action = WaitAction(wait_type=WaitType.RANDOM, min_duration=0.1, max_duration=0.2)
        result = await self.executor.execute_wait(action)
        
        self.assertTrue(result.success)
        self.assertGreaterEqual(result.execution_time, 0.1)
        self.assertLessEqual(result.execution_time, 0.3)  # 允许一些误差
    
    async def test_execute_wait_condition_success(self):
        """测试条件等待成功"""
        condition_met = False
        
        def condition_func():
            nonlocal condition_met
            condition_met = True
            return True
        
        action = WaitAction(wait_type=WaitType.CONDITION, condition_func=condition_func, timeout=1.0)
        result = await self.executor.execute_wait(action)
        
        self.assertTrue(result.success)
        self.assertTrue(condition_met)
    
    async def test_execute_wait_condition_timeout(self):
        """测试条件等待超时"""
        def condition_func():
            return False  # 永远不满足条件
        
        action = WaitAction(wait_type=WaitType.CONDITION, condition_func=condition_func, timeout=0.1)
        result = await self.executor.execute_wait(action)
        
        self.assertFalse(result.success)
        self.assertIn("timeout", result.message.lower())
    
    async def test_execute_loop_count(self):
        """测试次数循环"""
        actions = [
            {"type": "wait", "params": {"wait_type": "fixed", "duration": 0.01}}
        ]
        
        loop_action = LoopAction(loop_type=LoopType.COUNT, count=3, actions=actions)
        result = await self.executor.execute_loop(loop_action)
        
        self.assertTrue(result.success)
        self.assertEqual(result.data["total_iterations"], 3)
        self.assertEqual(result.data["successful_iterations"], 3)
    
    async def test_execute_loop_condition(self):
        """测试条件循环"""
        iteration_count = 0
        
        def condition_func():
            nonlocal iteration_count
            iteration_count += 1
            return iteration_count < 3  # 执行3次后停止
        
        actions = [
            {"type": "wait", "params": {"wait_type": "fixed", "duration": 0.01}}
        ]
        
        loop_action = LoopAction(loop_type=LoopType.CONDITION, condition_func=condition_func, actions=actions)
        result = await self.executor.execute_loop(loop_action)
        
        self.assertTrue(result.success)
        self.assertEqual(result.data["total_iterations"], 2)  # 条件为False时停止
    
    @patch('src.core.action_executor.pyautogui')
    async def test_execute_scroll(self, mock_pyautogui):
        """测试滚动操作"""
        result = await self.executor.execute_scroll(100, 200, clicks=3, direction="up")
        
        self.assertTrue(result.success)
        mock_pyautogui.scroll.assert_called_once_with(3, x=100, y=200)
    
    @patch('src.core.action_executor.pyautogui')
    async def test_execute_drag(self, mock_pyautogui):
        """测试拖拽操作"""
        result = await self.executor.execute_drag(100, 200, 300, 400, duration=1.0)
        
        self.assertTrue(result.success)
        mock_pyautogui.drag.assert_called_once()
    
    async def test_execute_action_click(self):
        """测试通用操作执行 - 点击"""
        with patch('src.core.action_executor.pyautogui'):
            action_config = {
                "type": "click",
                "params": {"x": 100, "y": 200, "click_type": "single"}
            }
            
            result = await self.executor.execute_action(action_config)
            self.assertTrue(result.success)
            
            # 检查统计信息更新
            stats = self.executor.get_execution_stats()
            self.assertEqual(stats['total_actions'], 1)
            self.assertEqual(stats['successful_actions'], 1)
    
    async def test_execute_action_sequence(self):
        """测试操作序列执行"""
        with patch('src.core.action_executor.pyautogui'):
            actions = [
                {"type": "wait", "params": {"wait_type": "fixed", "duration": 0.01}},
                {"type": "click", "params": {"x": 100, "y": 200}},
                {"type": "wait", "params": {"wait_type": "fixed", "duration": 0.01}}
            ]
            
            results = await self.executor.execute_action_sequence(actions)
            
            self.assertEqual(len(results), 3)
            self.assertTrue(all(r.success for r in results))
    
    def test_is_action_safe(self):
        """测试操作安全检查"""
        # 安全的点击操作
        safe_action = {
            "type": "click",
            "params": {"x": 100, "y": 200}
        }
        self.assertTrue(self.executor.is_action_safe(safe_action))
        
        # 不安全的点击操作（超出屏幕范围）
        with patch('src.core.action_executor.pyautogui.size', return_value=(1920, 1080)):
            unsafe_action = {
                "type": "click",
                "params": {"x": 3000, "y": 2000}
            }
            self.assertFalse(self.executor.is_action_safe(unsafe_action))
    
    def test_stats_management(self):
        """测试统计信息管理"""
        # 初始状态
        stats = self.executor.get_execution_stats()
        self.assertEqual(stats['total_actions'], 0)
        
        # 手动更新统计信息
        self.executor.execution_stats['total_actions'] = 10
        self.executor.execution_stats['successful_actions'] = 8
        self.executor.execution_stats['failed_actions'] = 2
        self.executor.execution_stats['total_execution_time'] = 5.0
        
        stats = self.executor.get_execution_stats()
        self.assertEqual(stats['success_rate'], 0.8)
        self.assertEqual(stats['average_execution_time'], 0.5)
        
        # 重置统计信息
        self.executor.reset_stats()
        stats = self.executor.get_execution_stats()
        self.assertEqual(stats['total_actions'], 0)
    
    def test_stop_execution(self):
        """测试停止执行"""
        self.assertFalse(self.executor.is_running)
        self.executor.stop_execution()
        self.assertFalse(self.executor.is_running)


def run_async_test(test_func):
    """运行异步测试的辅助函数"""
    def wrapper(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(test_func(self))
        finally:
            loop.close()
    return wrapper


# 将异步测试方法转换为同步
for name, method in list(TestActionExecutor.__dict__.items()):
    if name.startswith('test_') and asyncio.iscoroutinefunction(method):
        setattr(TestActionExecutor, name, run_async_test(method))


if __name__ == '__main__':
    unittest.main()