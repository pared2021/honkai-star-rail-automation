#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
游戏检测器功能测试脚本

用于验证GameDetector的实际功能，包括：
1. 游戏进程检测
2. 窗口识别和管理
3. 截图功能
4. 模板匹配
5. 场景检测
"""

import sys
import os
import time
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

try:
    from core.game_detector import GameDetector
    from core.config_manager import ConfigManager
    from core.logger import setup_logger
except ImportError as e:
    print(f"导入模块失败: {e}")
    print("请确保项目结构正确")
    sys.exit(1)

def test_game_detector():
    """测试GameDetector功能."""
    print("=== 游戏检测器功能测试 ===")
    
    # 初始化日志
    logger = setup_logger("INFO")
    
    # 初始化配置管理器
    config_manager = ConfigManager()
    
    # 初始化游戏检测器
    print("\n1. 初始化游戏检测器...")
    try:
        detector = GameDetector(config_manager)
        print("✓ 游戏检测器初始化成功")
    except Exception as e:
        print(f"✗ 游戏检测器初始化失败: {e}")
        return False
    
    # 测试游戏进程检测
    print("\n2. 测试游戏进程检测...")
    try:
        is_running = detector.is_game_running()
        print(f"游戏运行状态: {is_running}")
        if is_running:
            print("✓ 检测到游戏进程")
        else:
            print("! 未检测到游戏进程（这是正常的，如果没有运行游戏）")
    except Exception as e:
        print(f"✗ 游戏进程检测失败: {e}")
    
    # 测试窗口检测
    print("\n3. 测试游戏窗口检测...")
    try:
        window_info = detector.detect_game_window()
        if window_info:
            print(f"✓ 检测到游戏窗口: {window_info['title']}")
            print(f"  窗口尺寸: {window_info['width']}x{window_info['height']}")
            print(f"  窗口类名: {window_info['class_name']}")
        else:
            print("! 未检测到游戏窗口（如果没有运行游戏，这是正常的）")
    except Exception as e:
        print(f"✗ 游戏窗口检测失败: {e}")
    
    # 测试游戏状态获取
    print("\n4. 测试游戏状态获取...")
    try:
        status = detector.get_game_status()
        print(f"游戏状态: {status['overall_status']}")
        print(f"进程运行: {status['game_running']}")
        print(f"窗口检测: {status['window_detected']}")
        print(f"截图可用: {status['screenshot_available']}")
        
        if status['window_info']:
            print(f"窗口信息: {status['window_info']}")
        
        if status['overall_status'] == 'ready':
            print("✓ 游戏检测器完全就绪")
        elif status['overall_status'] == 'partial':
            print("! 游戏检测器部分就绪")
        else:
            print(f"! 游戏检测器状态: {status['overall_status']}")
            
    except Exception as e:
        print(f"✗ 游戏状态获取失败: {e}")
    
    # 测试截图功能
    print("\n5. 测试截图功能...")
    try:
        screenshot_data = detector.capture_screen()
        if screenshot_data:
            print(f"✓ 截图成功，数据大小: {len(screenshot_data)} 字节")
            
            # 保存测试截图
            screenshot_path = project_root / "test_screenshot.png"
            with open(screenshot_path, 'wb') as f:
                f.write(screenshot_data)
            print(f"✓ 截图已保存到: {screenshot_path}")
        else:
            print("! 截图失败（如果没有游戏窗口，这是正常的）")
    except Exception as e:
        print(f"✗ 截图功能测试失败: {e}")
    
    # 测试模板匹配功能
    print("\n6. 测试模板匹配功能...")
    try:
        # 检查模板目录
        templates_dir = project_root / "assets" / "templates"
        if templates_dir.exists():
            print(f"✓ 模板目录存在: {templates_dir}")
            
            # 列出可用模板
            template_files = list(templates_dir.glob("*.png"))
            if template_files:
                print(f"可用模板: {[f.name for f in template_files]}")
                
                # 测试第一个模板
                test_template = template_files[0]
                result = detector.find_template(str(test_template))
                if result:
                    if result.get('found'):
                        print(f"✓ 模板匹配成功: {test_template.name}")
                        print(f"  置信度: {result['confidence']:.3f}")
                        print(f"  中心位置: {result['center']}")
                    else:
                        print(f"! 模板未匹配: {test_template.name}")
                else:
                    print(f"! 模板匹配返回空结果: {test_template.name}")
            else:
                print("! 模板目录为空")
        else:
            print(f"! 模板目录不存在: {templates_dir}")
    except Exception as e:
        print(f"✗ 模板匹配功能测试失败: {e}")
    
    # 测试场景检测
    print("\n7. 测试场景检测...")
    try:
        current_scene = detector.detect_current_scene()
        print(f"当前场景: {current_scene}")
        
        if current_scene.name != 'UNKNOWN':
            print(f"✓ 场景检测成功: {current_scene.name}")
        else:
            print("! 场景检测结果为未知（如果没有游戏运行，这是正常的）")
    except Exception as e:
        print(f"✗ 场景检测失败: {e}")
    
    print("\n=== 测试完成 ===")
    return True

def test_template_loading():
    """测试模板加载功能."""
    print("\n=== 模板加载测试 ===")
    
    try:
        detector = GameDetector()
        
        # 检查模板缓存
        template_cache = detector.template_matcher.template_info_cache
        print(f"已加载模板数量: {len(template_cache)}")
        
        if template_cache:
            print("已加载的模板:")
            for name, info in template_cache.items():
                print(f"  - {name}: {info.path}")
            print("✓ 模板加载成功")
        else:
            print("! 未加载任何模板")
            
    except Exception as e:
        print(f"✗ 模板加载测试失败: {e}")

def test_window_management():
    """测试窗口管理功能."""
    print("\n=== 窗口管理测试 ===")
    
    try:
        detector = GameDetector()
        window_manager = detector.window_manager
        
        # 查找所有游戏窗口
        game_titles = detector.game_titles
        windows = window_manager.find_game_windows(game_titles)
        
        print(f"搜索的游戏标题: {game_titles}")
        print(f"找到的窗口数量: {len(windows)}")
        
        if windows:
            for i, window in enumerate(windows):
                print(f"窗口 {i+1}:")
                print(f"  标题: {window.title}")
                print(f"  尺寸: {window.width}x{window.height}")
                print(f"  位置: {window.rect}")
                print(f"  前台: {window.is_foreground}")
            print("✓ 窗口管理功能正常")
        else:
            print("! 未找到游戏窗口")
            
    except Exception as e:
        print(f"✗ 窗口管理测试失败: {e}")

if __name__ == "__main__":
    print("游戏检测器功能测试")
    print("=" * 50)
    
    # 运行所有测试
    test_game_detector()
    test_template_loading()
    test_window_management()
    
    print("\n测试完成！")
    print("\n注意：")
    print("- 如果没有运行游戏，某些测试结果为'未检测到'是正常的")
    print("- 要完整测试功能，请先运行支持的游戏")
    print("- 支持的游戏包括：崩坏：星穹铁道、原神、崩坏3等")