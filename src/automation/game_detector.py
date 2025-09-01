# -*- coding: utf-8 -*-
"""
游戏检测器 - 负责检测游戏窗口、状态和界面元素
"""

import time
import psutil
import cv2
import numpy as np
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any
from dataclasses import dataclass

import pyautogui
from PIL import Image, ImageGrab
from src.core.logger import get_logger

logger = get_logger(__name__)

from src.core.config_manager import ConfigManager, ConfigType


@dataclass
class GameWindow:
    """游戏窗口信息"""
    hwnd: int
    title: str
    rect: Tuple[int, int, int, int]  # (left, top, right, bottom)
    is_active: bool
    process_id: int


@dataclass
class DetectionResult:
    """检测结果"""
    found: bool
    confidence: float
    location: Optional[Tuple[int, int]] = None
    region: Optional[Tuple[int, int, int, int]] = None
    template_name: Optional[str] = None


class GameDetector:
    """游戏检测器类"""
    
    def __init__(self, config_manager: ConfigManager):
        """初始化游戏检测器
        
        Args:
            config_manager: 配置管理器
        """
        self.config_manager = config_manager
        
        # 检测配置
        self.detection_threshold = config_manager.get_setting(ConfigType.AUTOMATION_CONFIG, 'detection_threshold', 0.8)
        self.game_process_names = ['StarRail.exe', 'YuanShen.exe']  # 可能的游戏进程名
        
        # 模板图片缓存
        self.templates: Dict[str, np.ndarray] = {}
        self._load_templates()
        
        # 当前游戏窗口
        self.current_window: Optional[GameWindow] = None
        
        logger.info("游戏检测器初始化完成")
    
    def _load_templates(self):
        """加载模板图片"""
        templates_dir = Path(__file__).parent.parent.parent / "assets" / "templates"
        
        if not templates_dir.exists():
            logger.warning(f"模板目录不存在: {templates_dir}")
            return
        
        # 加载所有PNG模板图片
        for template_file in templates_dir.glob("*.png"):
            try:
                template_img = cv2.imread(str(template_file), cv2.IMREAD_COLOR)
                if template_img is not None:
                    self.templates[template_file.stem] = template_img
                    logger.debug(f"加载模板: {template_file.stem}")
            except Exception as e:
                logger.error(f"加载模板失败 {template_file}: {e}")
        
        logger.info(f"加载了 {len(self.templates)} 个模板图片")
    
    def find_game_window(self) -> Optional[GameWindow]:
        """查找游戏窗口
        
        Returns:
            GameWindow: 游戏窗口信息，如果未找到返回None
        """
        try:
            import win32gui
            import win32process
            
            def enum_windows_callback(hwnd, windows):
                if win32gui.IsWindowVisible(hwnd):
                    window_title = win32gui.GetWindowText(hwnd)
                    if self._is_game_window(window_title):
                        try:
                            _, process_id = win32process.GetWindowThreadProcessId(hwnd)
                            rect = win32gui.GetWindowRect(hwnd)
                            is_active = win32gui.GetForegroundWindow() == hwnd
                            
                            window = GameWindow(
                                hwnd=hwnd,
                                title=window_title,
                                rect=rect,
                                is_active=is_active,
                                process_id=process_id
                            )
                            windows.append(window)
                        except Exception as e:
                            logger.debug(f"获取窗口信息失败 {hwnd}: {e}")
            
            windows = []
            win32gui.EnumWindows(enum_windows_callback, windows)
            
            if windows:
                # 优先返回活动窗口
                for window in windows:
                    if window.is_active:
                        self.current_window = window
                        logger.info(f"找到活动游戏窗口: {window.title}")
                        return window
                
                # 如果没有活动窗口，返回第一个
                self.current_window = windows[0]
                logger.info(f"找到游戏窗口: {windows[0].title}")
                return windows[0]
            
        except ImportError:
            logger.warning("win32gui 模块未安装，使用备用方法检测游戏窗口")
            return self._find_game_window_fallback()
        except Exception as e:
            logger.error(f"查找游戏窗口失败: {e}")
        
        return None
    
    def _is_game_window(self, title: str) -> bool:
        """判断是否为游戏窗口
        
        Args:
            title: 窗口标题
            
        Returns:
            bool: 是否为游戏窗口
        """
        game_keywords = [
            "崩坏：星穹铁道", "Honkai: Star Rail", "StarRail",
            "原神", "Genshin Impact", "YuanShen"
        ]
        
        title_lower = title.lower()
        return any(keyword.lower() in title_lower for keyword in game_keywords)
    
    def _find_game_window_fallback(self) -> Optional[GameWindow]:
        """备用方法查找游戏窗口（通过进程）
        
        Returns:
            GameWindow: 游戏窗口信息
        """
        try:
            for proc in psutil.process_iter(['pid', 'name', 'exe']):
                try:
                    if proc.info['name'] in self.game_process_names:
                        # 找到游戏进程，创建虚拟窗口信息
                        window = GameWindow(
                            hwnd=0,
                            title=f"游戏进程: {proc.info['name']}",
                            rect=(0, 0, 1920, 1080),  # 默认分辨率
                            is_active=True,
                            process_id=proc.info['pid']
                        )
                        self.current_window = window
                        logger.info(f"通过进程找到游戏: {proc.info['name']}")
                        return window
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            logger.error(f"备用方法查找游戏窗口失败: {e}")
        
        return None
    
    def is_game_running(self) -> bool:
        """检查游戏是否在运行
        
        Returns:
            bool: 游戏是否在运行
        """
        try:
            for proc in psutil.process_iter(['name']):
                if proc.info['name'] in self.game_process_names:
                    return True
        except Exception as e:
            logger.error(f"检查游戏运行状态失败: {e}")
        
        return False
    
    def capture_screen(self, region: Optional[Tuple[int, int, int, int]] = None) -> Optional[np.ndarray]:
        """截取屏幕
        
        Args:
            region: 截取区域 (left, top, width, height)，None表示全屏
            
        Returns:
            np.ndarray: 截图的OpenCV图像，失败返回None
        """
        try:
            if region:
                # 截取指定区域
                screenshot = ImageGrab.grab(bbox=region)
            else:
                # 全屏截图
                screenshot = ImageGrab.grab()
            
            # 转换为OpenCV格式
            screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            return screenshot_cv
            
        except Exception as e:
            logger.error(f"截屏失败: {e}")
            return None
    
    def find_template(self, template_name: str, 
                     screenshot: Optional[np.ndarray] = None,
                     region: Optional[Tuple[int, int, int, int]] = None,
                     threshold: Optional[float] = None) -> DetectionResult:
        """在屏幕中查找模板
        
        Args:
            template_name: 模板名称
            screenshot: 截图，None表示重新截取
            region: 搜索区域
            threshold: 匹配阈值
            
        Returns:
            DetectionResult: 检测结果
        """
        if template_name not in self.templates:
            logger.warning(f"模板不存在: {template_name}")
            return DetectionResult(found=False, confidence=0.0)
        
        if threshold is None:
            threshold = self.detection_threshold
        
        try:
            # 获取截图
            if screenshot is None:
                screenshot = self.capture_screen(region)
                if screenshot is None:
                    return DetectionResult(found=False, confidence=0.0)
            
            # 获取模板
            template = self.templates[template_name]
            
            # 模板匹配
            result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            if max_val >= threshold:
                # 计算中心点位置
                template_h, template_w = template.shape[:2]
                center_x = max_loc[0] + template_w // 2
                center_y = max_loc[1] + template_h // 2
                
                # 如果指定了搜索区域，需要调整坐标
                if region:
                    center_x += region[0]
                    center_y += region[1]
                
                logger.debug(f"找到模板 {template_name}: 位置({center_x}, {center_y}), 置信度{max_val:.3f}")
                
                return DetectionResult(
                    found=True,
                    confidence=max_val,
                    location=(center_x, center_y),
                    region=region,
                    template_name=template_name
                )
            else:
                logger.debug(f"模板 {template_name} 未找到，最高置信度: {max_val:.3f}")
                return DetectionResult(found=False, confidence=max_val)
                
        except Exception as e:
            logger.error(f"模板匹配失败 {template_name}: {e}")
            return DetectionResult(found=False, confidence=0.0)
    
    def find_multiple_templates(self, template_names: List[str],
                              screenshot: Optional[np.ndarray] = None,
                              region: Optional[Tuple[int, int, int, int]] = None) -> Dict[str, DetectionResult]:
        """查找多个模板
        
        Args:
            template_names: 模板名称列表
            screenshot: 截图
            region: 搜索区域
            
        Returns:
            Dict[str, DetectionResult]: 检测结果字典
        """
        if screenshot is None:
            screenshot = self.capture_screen(region)
            if screenshot is None:
                return {name: DetectionResult(found=False, confidence=0.0) for name in template_names}
        
        results = {}
        for template_name in template_names:
            results[template_name] = self.find_template(template_name, screenshot, region)
        
        return results
    
    def wait_for_template(self, template_name: str, 
                         timeout: float = 10.0,
                         check_interval: float = 0.5,
                         region: Optional[Tuple[int, int, int, int]] = None) -> DetectionResult:
        """等待模板出现
        
        Args:
            template_name: 模板名称
            timeout: 超时时间（秒）
            check_interval: 检查间隔（秒）
            region: 搜索区域
            
        Returns:
            DetectionResult: 检测结果
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            result = self.find_template(template_name, region=region)
            if result.found:
                logger.info(f"等待模板成功: {template_name}, 耗时 {time.time() - start_time:.1f}s")
                return result
            
            time.sleep(check_interval)
        
        logger.warning(f"等待模板超时: {template_name}, 超时时间 {timeout}s")
        return DetectionResult(found=False, confidence=0.0)
    
    def get_game_region(self) -> Optional[Tuple[int, int, int, int]]:
        """获取游戏窗口区域
        
        Returns:
            Tuple: 游戏窗口区域 (left, top, right, bottom)
        """
        if self.current_window:
            return self.current_window.rect
        
        # 尝试重新查找游戏窗口
        window = self.find_game_window()
        if window:
            return window.rect
        
        return None
    
    def is_game_active(self) -> bool:
        """检查游戏窗口是否处于活动状态
        
        Returns:
            bool: 游戏窗口是否活动
        """
        if not self.current_window:
            return False
        
        try:
            import win32gui
            active_hwnd = win32gui.GetForegroundWindow()
            return active_hwnd == self.current_window.hwnd
        except ImportError:
            # 如果没有win32gui，假设游戏是活动的
            return True
        except Exception as e:
            logger.error(f"检查游戏活动状态失败: {e}")
            return False
    
    def activate_game_window(self) -> bool:
        """激活游戏窗口
        
        Returns:
            bool: 是否成功激活
        """
        if not self.current_window:
            logger.warning("没有找到游戏窗口")
            return False
        
        try:
            import win32gui
            win32gui.SetForegroundWindow(self.current_window.hwnd)
            logger.info("游戏窗口已激活")
            return True
        except ImportError:
            logger.warning("win32gui 模块未安装，无法激活窗口")
            return False
        except Exception as e:
            logger.error(f"激活游戏窗口失败: {e}")
            return False
    
    def is_game_detected(self) -> bool:
        """检查是否检测到游戏
        
        Returns:
            bool: 是否检测到游戏
        """
        return self.current_window is not None
    
    def get_current_game_window(self) -> Optional[GameWindow]:
        """获取当前游戏窗口
        
        Returns:
            Optional[GameWindow]: 当前游戏窗口，如果没有则返回None
        """
        return self.current_window
    
    def get_detection_stats(self) -> Dict[str, Any]:
        """获取检测统计信息
        
        Returns:
            Dict: 统计信息
        """
        return {
            'templates_loaded': len(self.templates),
            'template_names': list(self.templates.keys()),
            'detection_threshold': self.detection_threshold,
            'current_window': {
                'title': self.current_window.title if self.current_window else None,
                'active': self.is_game_active(),
                'rect': self.current_window.rect if self.current_window else None
            } if self.current_window else None,
            'game_running': self.is_game_running()
        }