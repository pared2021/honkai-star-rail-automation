#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
游戏检测功能测试脚本
用于验证GameDetector是否能正常检测游戏窗口和状态
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core.game_detector import GameDetector
from src.core.service_locator import ServiceLocator
from src.config.config_manager import ConfigManager
import time

def test_game_detection():
    """测试游戏检测功能"""
    print("=== 游戏检测功能测试 ===")
    
    try:
        # 初始化配置管理器
        config_manager = ConfigManager()
        
        # 初始化游戏检测器
        game_detector = GameDetector(config_manager)
        
        print("1. 检查游戏是否运行...")
        is_running = game_detector.is_game_running()
        print(f"   游戏运行状态: {is_running}")
        
        if is_running:
            print("\n2. 检测游戏窗口...")
            window = game_detector.detect_game_window()
            if window:
                print(f"   找到游戏窗口: {window.title}")
                print(f"   窗口句柄: {window.hwnd}")
                print(f"   窗口位置: {window.rect}")
            else:
                print("   未找到游戏窗口")
            
            print("\n3. 尝试截取游戏窗口...")
            screenshot = game_detector.capture_screenshot()
            if screenshot is not None:
                print(f"   截图成功，尺寸: {screenshot.shape}")
            else:
                print("   截图失败")
            
            print("\n4. 检测当前场景...")
            scene = game_detector.get_current_scene()
            print(f"   当前场景: {scene}")
            
            print("\n5. 测试UI元素检测...")
            # 测试常见的UI元素
            common_elements = ['inventory_bag_icon', 'main_menu_start_button']
            ui_elements = game_detector.detect_ui_elements(common_elements)
            if ui_elements:
                print(f"   检测到 {len(ui_elements)} 个UI元素:")
                for element in ui_elements:
                    print(f"     - {element.name}: 置信度 {element.confidence:.2f}")
            else:
                print("   未检测到UI元素")
        else:
            print("\n游戏未运行，请先启动崩坏：星穹铁道游戏")
            print("提示：请确保游戏窗口标题包含'崩坏：星穹铁道'或'Honkai: Star Rail'")
        
        print("\n=== 测试完成 ===")
        return is_running
        
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False

def continuous_monitoring():
    """持续监控游戏状态"""
    print("\n=== 开始持续监控 ===")
    print("按 Ctrl+C 停止监控")
    
    try:
        config_manager = ConfigManager()
        game_detector = GameDetector(config_manager)
        
        while True:
            is_running = game_detector.is_game_running()
            scene = game_detector.get_current_scene() if is_running else "游戏未运行"
            
            print(f"\r游戏状态: {'运行中' if is_running else '未运行'} | 当前场景: {scene}", end="", flush=True)
            time.sleep(2)
            
    except KeyboardInterrupt:
        print("\n\n监控已停止")
    except Exception as e:
        print(f"\n监控过程中发生错误: {e}")

if __name__ == "__main__":
    # 基础检测测试
    game_running = test_game_detection()
    
    # 如果游戏正在运行，询问是否进行持续监控
    if game_running:
        response = input("\n是否开始持续监控？(y/n): ")
        if response.lower() in ['y', 'yes', '是']:
            continuous_monitoring()
    
    print("\n测试脚本结束")