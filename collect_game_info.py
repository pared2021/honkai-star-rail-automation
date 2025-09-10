#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
游戏信息收集脚本
用于收集当前游戏状态和相关信息
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core.service_locator import initialize_services, get_service
from src.core.game_detector import GameDetector
from src.core.config_manager import ConfigManager
import time

def collect_game_info():
    """收集游戏信息"""
    print("=== 崩坏星穹铁道自动化助手 - 游戏信息收集 ===")
    print()
    
    try:
        # 初始化服务
        initialize_services()
        
        # 获取游戏检测器
        try:
            game_detector = get_service(GameDetector)
        except ValueError:
            # 如果服务未注册，直接创建实例
            config_manager = get_service(ConfigManager)
            game_detector = GameDetector(config_manager)
        
        print("1. 检查游戏运行状态...")
        is_running = game_detector.is_game_running()
        print(f"   游戏运行状态: {'运行中' if is_running else '未运行'}")
        
        if is_running:
            print("\n2. 获取游戏窗口信息...")
            game_window = game_detector.detect_game_window()
            if game_window:
                print(f"   窗口标题: {game_window.title}")
                print(f"   窗口句柄: {game_window.hwnd}")
                print(f"   窗口矩形: {game_window.rect}")
                print(f"   窗口大小: {game_window.width} x {game_window.height}")
                print(f"   是否前台: {game_window.is_foreground}")
            
            print("\n3. 检测当前场景...")
            current_scene = game_detector.detect_current_scene()
            print(f"   当前场景: {current_scene}")
            
            print("\n4. 检测UI元素...")
            # 检测常见的UI元素
            common_elements = ['inventory_bag_icon', 'main_menu_start_button']
            ui_elements = game_detector.detect_ui_elements(common_elements)
            if ui_elements:
                print(f"   检测到 {len(ui_elements)} 个UI元素:")
                for element in ui_elements[:5]:  # 只显示前5个
                    print(f"     - {element.name}: 置信度 {element.confidence:.2f}")
            else:
                print("   未检测到UI元素")
            
            print("\n5. 截取游戏截图...")
            screenshot = game_detector.capture_screenshot()
            if screenshot is not None:
                print("   截图成功")
                print(f"   截图尺寸: {screenshot.shape if hasattr(screenshot, 'shape') else 'unknown'}")
                # 保存截图到文件
                screenshot_path = "game_screenshot.png"
                try:
                    import cv2
                    cv2.imwrite(screenshot_path, screenshot)
                    print(f"   截图已保存到: {screenshot_path}")
                except Exception as e:
                    print(f"   保存截图失败: {e}")
            else:
                print("   截图失败")
        
        print("\n6. 获取游戏状态...")
        # 获取完整的游戏状态
        game_status = game_detector.get_game_status()
        print(f"   整体状态: {game_status.get('overall_status', 'unknown')}")
        print(f"   游戏进程: {'运行中' if game_status.get('game_running', False) else '未运行'}")
        print(f"   窗口检测: {'成功' if game_status.get('window_found', False) else '失败'}")
        print(f"   截图功能: {'可用' if game_status.get('screenshot_available', False) else '不可用'}")
        print(f"   已加载模板: {game_status.get('templates_loaded', 0)} 个")
        
        if 'error' in game_status:
            print(f"   错误信息: {game_status['error']}")
        
        print("\n=== 信息收集完成 ===")
        return True
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    collect_game_info()