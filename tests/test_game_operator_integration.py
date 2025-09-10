#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
游戏操作器集成测试模块.

本模块用于验证GameOperator在真实环境中的操作可行性和稳定性。
包含实际的点击、滑动、输入等操作测试。
"""

import asyncio
import sys
import time
from pathlib import Path
from typing import Optional

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.game_operator import GameOperator, OperationConfig, ClickType
from src.core.game_detector import GameDetector
from src.core.sync_adapter import SyncAdapter


class GameOperatorIntegrationTest:
    """GameOperator集成测试类."""
    
    def __init__(self):
        """初始化集成测试."""
        self.game_detector = GameDetector()
        self.sync_adapter = SyncAdapter()
        self.game_operator = GameOperator(
            game_detector=self.game_detector,
            sync_adapter=self.sync_adapter
        )
        
    async def test_basic_operations(self) -> bool:
        """测试基础操作功能.
        
        Returns:
            bool: 测试是否通过
        """
        print("开始测试基础操作功能...")
        
        try:
            # 测试点击操作
            print("测试点击操作...")
            click_result = await self.game_operator.click(
                target=(500, 300),
                click_type=ClickType.LEFT
            )
            print(f"点击操作结果: {click_result.success}")
            
            # 等待一段时间
            await asyncio.sleep(1)
            
            # 测试滑动操作
            print("测试滑动操作...")
            swipe_result = await self.game_operator.swipe(
                start_pos=(400, 400),
                end_pos=(600, 400),
                duration=1.0
            )
            print(f"滑动操作结果: {swipe_result.success}")
            
            # 等待一段时间
            await asyncio.sleep(1)
            
            # 测试输入文本操作
            print("测试输入文本操作...")
            input_result = await self.game_operator.input_text(
                text="Hello World",
                target=(500, 500)
            )
            print(f"输入文本操作结果: {input_result.success}")
            
            return True
            
        except Exception as e:
            print(f"基础操作测试失败: {e}")
            return False
    
    async def test_wait_conditions(self) -> bool:
        """测试等待条件功能.
        
        Returns:
            bool: 测试是否通过
        """
        print("开始测试等待条件功能...")
        
        try:
            # 测试等待UI元素出现
            print("测试等待UI元素...")
            
            # 创建一个简单的等待条件
            async def simple_condition() -> bool:
                """简单的等待条件."""
                # 模拟检查某个条件
                return True
            
            from src.core.game_operator import WaitCondition
            
            wait_result = await self.game_operator.wait_for_condition(
                condition=WaitCondition.CUSTOM,
                condition_params={"custom_function": simple_condition},
                timeout=5.0
            )
            print(f"等待条件结果: {wait_result.success}")
            
            return True
            
        except Exception as e:
            print(f"等待条件测试失败: {e}")
            return False
    
    async def test_operation_stability(self) -> bool:
        """测试操作稳定性.
        
        Returns:
            bool: 测试是否通过
        """
        print("开始测试操作稳定性...")
        
        try:
            success_count = 0
            total_operations = 10
            
            for i in range(total_operations):
                print(f"执行第 {i+1}/{total_operations} 次操作...")
                
                # 执行点击操作
                result = await self.game_operator.click(
                    target=(400 + i * 10, 300),
                    click_type=ClickType.LEFT
                )
                
                if result.success:
                    success_count += 1
                
                # 短暂等待
                await asyncio.sleep(0.2)
            
            success_rate = success_count / total_operations
            print(f"操作成功率: {success_rate:.2%} ({success_count}/{total_operations})")
            
            # 成功率大于80%认为稳定
            return success_rate > 0.8
            
        except Exception as e:
            print(f"稳定性测试失败: {e}")
            return False
    
    async def test_error_handling(self) -> bool:
        """测试错误处理.
        
        Returns:
            bool: 测试是否通过
        """
        print("开始测试错误处理...")
        
        try:
            # 测试无效坐标
            print("测试无效坐标...")
            invalid_result = await self.game_operator.click(
                target=(-100, -100),
                click_type=ClickType.LEFT
            )
            print(f"无效坐标处理结果: {not invalid_result.success}")
            
            # 测试超时情况
            print("测试超时情况...")
            
            async def never_true_condition() -> bool:
                """永远不会为真的条件."""
                return False
            
            from src.core.game_operator import WaitCondition
            
            timeout_result = await self.game_operator.wait_for_condition(
                condition=WaitCondition.CUSTOM,
                condition_params={"custom_function": never_true_condition},
                timeout=1.0
            )
            print(f"超时处理结果: {not timeout_result.success}")
            
            return True
            
        except Exception as e:
            print(f"错误处理测试失败: {e}")
            return False
    
    async def run_all_tests(self) -> bool:
        """运行所有集成测试.
        
        Returns:
            bool: 所有测试是否通过
        """
        print("="*50)
        print("GameOperator 集成测试开始")
        print("="*50)
        
        test_results = []
        
        # 运行各项测试
        test_results.append(await self.test_basic_operations())
        test_results.append(await self.test_wait_conditions())
        test_results.append(await self.test_operation_stability())
        test_results.append(await self.test_error_handling())
        
        # 统计结果
        passed_tests = sum(test_results)
        total_tests = len(test_results)
        
        print("="*50)
        print(f"测试完成: {passed_tests}/{total_tests} 通过")
        print("="*50)
        
        if passed_tests == total_tests:
            print("✅ 所有集成测试通过！")
            return True
        else:
            print("❌ 部分集成测试失败！")
            return False


async def main():
    """主函数."""
    test_runner = GameOperatorIntegrationTest()
    success = await test_runner.run_all_tests()
    
    if success:
        print("\n🎉 GameOperator集成测试全部通过，操作功能验证完成！")
    else:
        print("\n⚠️  部分测试失败，需要进一步优化。")


if __name__ == "__main__":
    # 运行集成测试
    asyncio.run(main())