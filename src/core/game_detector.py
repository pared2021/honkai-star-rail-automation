"""游戏检测器模块

负责游戏窗口检测、场景识别和UI元素定位
"""

import cv2
import numpy as np
import win32gui
import win32con
import win32ui
from PIL import Image
from typing import Optional, Tuple, List, Dict, Any
from dataclasses import dataclass
from enum import Enum
import os
import json
from pathlib import Path
import logging
from PIL import Image
import psutil
import time
import win32process

from .logger import get_logger
from .config_manager import ConfigManager

logger = get_logger(__name__)

class SceneType(Enum):
    """游戏场景类型"""
    UNKNOWN = "unknown"
    MAIN_MENU = "main_menu"
    GAME_WORLD = "game_world"
    COMBAT = "combat"
    INVENTORY = "inventory"
    MISSION = "mission"
    SHOP = "shop"
    MAIL = "mail"
    LOADING = "loading"
    DIALOGUE = "dialogue"

@dataclass
class GameWindow:
    """游戏窗口信息"""
    hwnd: int
    title: str
    rect: Tuple[int, int, int, int]  # (left, top, right, bottom)
    width: int
    height: int
    is_foreground: bool

@dataclass
class UIElement:
    """UI元素信息"""
    name: str
    position: Tuple[int, int]  # (x, y)
    size: Tuple[int, int]  # (width, height)
    confidence: float
    template_path: str
    scale_factor: float = 1.0  # 缩放因子

@dataclass
class TemplateInfo:
    """模板信息"""
    name: str
    category: str
    file_path: str
    confidence_threshold: float
    metadata: Dict[str, Any]

class TemplateMatcher:
    """模板匹配器"""
    
    def __init__(self, config_manager=None, templates_dir: str = None):
        self.config_manager = config_manager
        self.templates_dir = Path(templates_dir) if templates_dir else Path(self._get_config_value('template_matcher.templates_dir', 'assets/templates'))
        self.templates_cache = {}
        self.load_templates()
    
    def _get_config_value(self, key: str, default_value):
        """获取配置值"""
        if self.config_manager:
            return self.config_manager.get(key, default_value)
        return default_value
    
    def load_templates(self):
        """加载所有模板"""
        if not self.templates_dir.exists():
            logger.warning(f"Templates directory not found: {self.templates_dir}")
            return
        
        for category_dir in self.templates_dir.iterdir():
            if category_dir.is_dir():
                # 支持PNG和SVG格式
                for template_file in category_dir.glob("*.png"):
                    self._load_template_file(template_file, category_dir.name)
                for template_file in category_dir.glob("*.svg"):
                    self._load_template_file(template_file, category_dir.name)
    
    def _load_template_file(self, template_file: Path, category: str):
        """加载单个模板文件"""
        template_name = f"{category}_{template_file.stem}"
        try:
            if template_file.suffix.lower() == '.svg':
                # SVG文件需要转换为图像
                template = self._convert_svg_to_image(template_file)
            else:
                # PNG文件直接加载
                template = cv2.imread(str(template_file), cv2.IMREAD_COLOR)
            
            if template is not None:
                default_threshold = self._get_config_value('template_matcher.default_threshold', 0.8)
                self.templates_cache[template_name] = {
                    "image": template,
                    "path": str(template_file),
                    "category": category,
                    "threshold": default_threshold,
                    "original_size": template.shape[:2]  # 保存原始尺寸
                }
                logger.debug(f"Loaded template: {template_name}")
        except Exception as e:
            logger.error(f"Failed to load template {template_file}: {e}")
    
    def _convert_svg_to_image(self, svg_path: Path) -> Optional[np.ndarray]:
        """将SVG转换为OpenCV图像"""
        try:
            import cairosvg
            from io import BytesIO
            
            # 将SVG转换为PNG字节流
            png_bytes = cairosvg.svg2png(url=str(svg_path))
            
            # 转换为PIL图像
            pil_image = Image.open(BytesIO(png_bytes))
            
            # 转换为OpenCV格式
            opencv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGBA2BGR)
            
            return opencv_image
            
        except ImportError:
            logger.warning("cairosvg not installed, SVG templates will be skipped")
            return None
        except Exception as e:
            logger.error(f"Failed to convert SVG to image: {e}")
            return None
    
    def match_template(self, screenshot: np.ndarray, template_name: str, 
                      threshold: Optional[float] = None, scale_factors: Optional[List[float]] = None) -> Optional[UIElement]:
        """匹配模板，支持多分辨率适配"""
        if template_name not in self.templates_cache:
            logger.warning(f"Template not found: {template_name}")
            return None
        
        template_info = self.templates_cache[template_name]
        template = template_info["image"]
        confidence_threshold = threshold or template_info["threshold"]
        
        # 如果没有指定缩放因子，使用默认的多分辨率适配
        if scale_factors is None:
            scale_factors = self._calculate_scale_factors(screenshot.shape[:2], template_info["original_size"])
        
        best_match = None
        best_confidence = 0
        
        try:
            # 尝试不同的缩放因子
            for scale in scale_factors:
                scaled_template = self._scale_template(template, scale)
                if scaled_template is None:
                    continue
                    
                # 执行模板匹配
                result = cv2.matchTemplate(screenshot, scaled_template, cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                
                if max_val >= confidence_threshold and max_val > best_confidence:
                    h, w = scaled_template.shape[:2]
                    best_match = UIElement(
                        name=template_name,
                        position=max_loc,
                        size=(w, h),
                        confidence=max_val,
                        template_path=template_info["path"]
                    )
                    best_confidence = max_val
            
            if best_match is None:
                logger.debug(f"Template {template_name} not found, best confidence: {best_confidence:.3f}")
            
            return best_match
            
        except Exception as e:
            logger.error(f"Template matching failed for {template_name}: {e}")
            return None
    
    def _calculate_scale_factors(self, screenshot_size: Tuple[int, int], 
                               template_size: Tuple[int, int]) -> List[float]:
        """计算适合的缩放因子"""
        screen_h, screen_w = screenshot_size
        template_h, template_w = template_size
        
        # 基于屏幕分辨率计算缩放因子
        base_scales = self._get_config_value('template_matcher.base_scales', [1.0])  # 原始尺寸
        
        # 从配置获取额外的缩放因子
        extra_scales = self._get_config_value('template_matcher.scale_factors', [0.8, 1.2, 1.5])
        
        # 常见分辨率适配
        resolution_scales = self._get_config_value('template_matcher.resolution_scales', {
            'high': {'min_width': 1920, 'scales': extra_scales},
            'medium': {'min_width': 1366, 'max_width': 1919, 'scales': [0.7, 0.9, 1.1]},
            'low': {'max_width': 1365, 'scales': [0.5, 0.6, 0.8]}
        })
        
        additional_scales = []
        for res_name, res_config in resolution_scales.items():
            min_width = res_config.get('min_width', 0)
            max_width = res_config.get('max_width', float('inf'))
            if min_width <= screen_w <= max_width:
                additional_scales.extend(res_config.get('scales', []))
                break
        
        all_scales = base_scales + additional_scales
        
        # 过滤掉会导致模板过大或过小的缩放因子
        valid_scales = []
        for scale in all_scales:
            scaled_w = int(template_w * scale)
            scaled_h = int(template_h * scale)
            
            # 确保缩放后的模板不会超出屏幕或太小
            if (10 <= scaled_w <= screen_w - 10 and 
                10 <= scaled_h <= screen_h - 10):
                valid_scales.append(scale)
        
        return valid_scales if valid_scales else [1.0]
    
    def _scale_template(self, template: np.ndarray, scale: float) -> Optional[np.ndarray]:
        """缩放模板图像"""
        if scale == 1.0:
            return template
        
        try:
            h, w = template.shape[:2]
            new_w = int(w * scale)
            new_h = int(h * scale)
            
            if new_w <= 0 or new_h <= 0:
                return None
            
            scaled = cv2.resize(template, (new_w, new_h), interpolation=cv2.INTER_AREA)
            return scaled
        except Exception as e:
            logger.error(f"Failed to scale template: {e}")
            return None
    
    def match_multiple_templates(self, screenshot: np.ndarray, 
                               template_names: List[str], 
                               threshold: float = None) -> List[UIElement]:
        """匹配多个模板"""
        results = []
        for template_name in template_names:
            element = self.match_template(screenshot, template_name, threshold)
            if element:
                results.append(element)
        return results

class WindowManager:
    """窗口管理器"""
    
    def __init__(self, target_window_title: str = None, config_manager=None):
        self.config_manager = config_manager
        self.target_window_title = target_window_title or self._get_config_value('window_manager.target_window_title', "崩坏：星穹铁道")
        self.current_window = None
    
    def _get_config_value(self, key: str, default_value):
        """获取配置值"""
        if self.config_manager:
            return self.config_manager.get(key, default_value)
        return default_value
    
    def find_game_window(self) -> Optional[GameWindow]:
        """查找游戏窗口"""
        def enum_windows_callback(hwnd, windows):
            if win32gui.IsWindowVisible(hwnd):
                window_title = win32gui.GetWindowText(hwnd)
                if self.target_window_title in window_title:
                    windows.append(hwnd)
            return True
        
        windows = []
        win32gui.EnumWindows(enum_windows_callback, windows)
        
        if not windows:
            logger.warning(f"Game window not found: {self.target_window_title}")
            return None
        
        # 取第一个匹配的窗口
        hwnd = windows[0]
        try:
            rect = win32gui.GetWindowRect(hwnd)
            title = win32gui.GetWindowText(hwnd)
            width = rect[2] - rect[0]
            height = rect[3] - rect[1]
            is_foreground = win32gui.GetForegroundWindow() == hwnd
            
            game_window = GameWindow(
                hwnd=hwnd,
                title=title,
                rect=rect,
                width=width,
                height=height,
                is_foreground=is_foreground
            )
            
            self.current_window = game_window
            logger.info(f"Found game window: {title} ({width}x{height})")
            return game_window
            
        except Exception as e:
            logger.error(f"Failed to get window info: {e}")
            return None
    
    def capture_window(self, window: Optional[GameWindow] = None) -> Optional[np.ndarray]:
        """截取窗口图像"""
        target_window = window or self.current_window
        if not target_window:
            logger.error("No window to capture")
            return None
        
        try:
            hwnd = target_window.hwnd
            left, top, right, bottom = target_window.rect
            width = right - left
            height = bottom - top
            
            # 获取窗口设备上下文
            hwnd_dc = win32gui.GetWindowDC(hwnd)
            mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
            save_dc = mfc_dc.CreateCompatibleDC()
            
            # 创建位图
            save_bitmap = win32ui.CreateBitmap()
            save_bitmap.CreateCompatibleBitmap(mfc_dc, width, height)
            save_dc.SelectObject(save_bitmap)
            
            # 复制窗口内容
            save_dc.BitBlt((0, 0), (width, height), mfc_dc, (0, 0), win32con.SRCCOPY)
            
            # 转换为numpy数组
            bmp_info = save_bitmap.GetInfo()
            bmp_str = save_bitmap.GetBitmapBits(True)
            
            img = np.frombuffer(bmp_str, dtype='uint8')
            img.shape = (height, width, 4)
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            
            # 清理资源
            win32gui.DeleteObject(save_bitmap.GetHandle())
            save_dc.DeleteDC()
            mfc_dc.DeleteDC()
            win32gui.ReleaseDC(hwnd, hwnd_dc)
            
            return img
            
        except Exception as e:
            logger.error(f"Failed to capture window: {e}")
            return None
    
    def bring_window_to_front(self, window: Optional[GameWindow] = None) -> bool:
        """将窗口置于前台"""
        target_window = window or self.current_window
        if not target_window:
            return False
        
        try:
            win32gui.SetForegroundWindow(target_window.hwnd)
            win32gui.ShowWindow(target_window.hwnd, win32con.SW_RESTORE)
            return True
        except Exception as e:
            logger.error(f"Failed to bring window to front: {e}")
            return False

class GameDetector:
    """游戏检测器 - 统一的游戏窗口检测和场景识别"""
    
    def __init__(self, config_manager: ConfigManager = None, game_title: str = None):
        self.config_manager = config_manager
        self.game_title = game_title or self._get_game_title() if config_manager else "崩坏：星穹铁道"
        self.window_manager = WindowManager(self.game_title, config_manager)
        self.template_matcher = TemplateMatcher(config_manager=config_manager)
        self.current_scene = SceneType.UNKNOWN
        self.last_screenshot = None
        
        # 场景检测模板映射 - 使用实际创建的模板
        self.scene_templates = self._get_scene_templates()
        
    def _get_game_title(self) -> str:
        """获取游戏标题"""
        if self.config_manager:
            return self.config_manager.get('game_detector.game_title', '崩坏：星穹铁道')
        return '崩坏：星穹铁道'
    
    def _get_config_value(self, key: str, default_value):
        """获取配置值"""
        if self.config_manager:
            return self.config_manager.get(key, default_value)
        return default_value
    
    def _get_scene_templates(self) -> Dict[SceneType, List[str]]:
        """获取场景模板映射"""
        if self.config_manager:
            # 从配置管理器获取场景模板映射
            templates = self.config_manager.get('game_detector.scene_templates', {})
            if templates:
                result = {}
                for scene_name, template_list in templates.items():
                    try:
                        scene_type = SceneType(scene_name)
                        result[scene_type] = template_list
                    except ValueError:
                        logger.warning(f"Unknown scene type: {scene_name}")
                return result
        
        # 从配置管理器获取默认场景模板映射
        default_templates = self._get_config_value('game_detector.default_scene_templates', {
            'MAIN_MENU': ["main_menu_start_game", "main_menu_settings_button", "main_menu_exit_button"],
            'COMBAT': ["combat_attack_button", "combat_skill_button"],
            'INVENTORY': ["inventory_bag_icon", "inventory_item_slot"],
            'SHOP': ["shop_shop_icon", "shop_buy_button"],
            'MISSION': ["mission_mission_icon", "mission_complete_mark"],
            'MAIL': ["mail_mail_icon", "mail_claim_button"],
            'GAME_WORLD': []  # 游戏世界场景通过排除法确定
        })
        
        # 转换为SceneType枚举
        result = {}
        for scene_name, template_list in default_templates.items():
            try:
                scene_type = SceneType(scene_name)
                result[scene_type] = template_list
            except ValueError:
                logger.warning(f"Unknown scene type: {scene_name}")
        return result
    
    def detect_game_window(self) -> Optional[GameWindow]:
        """检测游戏窗口 - 支持多种查找方式"""
        # 首先尝试通过窗口标题查找
        window = self.window_manager.find_game_window()
        if window:
            return window
            
        # 如果标题查找失败，尝试通过进程名查找
        return self._find_window_by_process()
    
    def _find_window_by_process(self) -> Optional[GameWindow]:
        """通过进程名查找游戏窗口"""
        try:
            for proc in psutil.process_iter(['pid', 'name']):
                if 'StarRail' in proc.info['name'] or '星穹铁道' in proc.info['name']:
                    # 找到进程后，通过进程ID查找窗口
                    def enum_windows_proc(hwnd, windows):
                        if win32gui.IsWindowVisible(hwnd):
                            _, pid = win32process.GetWindowThreadProcessId(hwnd)
                            if pid == proc.info['pid']:
                                title = win32gui.GetWindowText(hwnd)
                                if title:  # 只考虑有标题的窗口
                                    rect = win32gui.GetWindowRect(hwnd)
                                    width = rect[2] - rect[0]
                                    height = rect[3] - rect[1]
                                    is_foreground = win32gui.GetForegroundWindow() == hwnd
                                    windows.append(GameWindow(
                                        hwnd=hwnd,
                                        title=title,
                                        rect=rect,
                                        width=width,
                                        height=height,
                                        is_foreground=is_foreground
                                    ))
                        return True
                    
                    windows = []
                    win32gui.EnumWindows(enum_windows_proc, windows)
                    if windows:
                        return windows[0]  # 返回第一个找到的窗口
        except Exception as e:
            logger.error(f"通过进程查找窗口失败: {e}")
        return None
    
    def capture_screenshot(self) -> Optional[np.ndarray]:
        """截取游戏截图"""
        screenshot = self.window_manager.capture_window()
        if screenshot is not None:
            self.last_screenshot = screenshot
        return screenshot
    
    def detect_current_scene(self, screenshot: Optional[np.ndarray] = None, 
                           confidence_threshold: float = None) -> SceneType:
        """检测当前游戏场景，使用增强的检测逻辑"""
        if confidence_threshold is None:
            confidence_threshold = self._get_config_value('game_detector.scene_confidence_threshold', 0.7)
            
        if screenshot is None:
            screenshot = self.capture_screenshot()
            if screenshot is None:
                return SceneType.UNKNOWN
        
        scene_scores = {}
        
        # 为每个场景计算置信度分数
        for scene_type, template_names in self.scene_templates.items():
            matches = self.template_matcher.match_multiple_templates(
                screenshot, template_names, confidence_threshold
            )
            
            if matches:
                # 计算场景分数：匹配数量 * 平均置信度
                avg_confidence = sum(match.confidence for match in matches) / len(matches)
                scene_score = len(matches) * avg_confidence
                scene_scores[scene_type] = scene_score
                
                logger.debug(f"Scene {scene_type.value}: {len(matches)} matches, "
                           f"avg confidence: {avg_confidence:.3f}, score: {scene_score:.3f}")
        
        if scene_scores:
            # 返回得分最高的场景
            best_scene = max(scene_scores.items(), key=lambda x: x[1])
            logger.info(f"Detected scene: {best_scene[0].value} (score: {best_scene[1]:.3f})")
            self.current_scene = best_scene[0]
            return best_scene[0]
        
        logger.warning("Could not determine current scene")
        self.current_scene = SceneType.GAME_WORLD
        return SceneType.GAME_WORLD
    
    def find_ui_element(self, template_name: str, 
                       screenshot: Optional[np.ndarray] = None) -> Optional[UIElement]:
        """查找UI元素"""
        if screenshot is None:
            screenshot = self.capture_screenshot()
        
        if screenshot is None:
            return None
        
        return self.template_matcher.match_template(screenshot, template_name)
    
    def find_multiple_ui_elements(self, template_names: List[str],
                                 screenshot: Optional[np.ndarray] = None) -> List[UIElement]:
        """查找多个UI元素"""
        if screenshot is None:
            screenshot = self.capture_screenshot()
        
        if screenshot is None:
            return []
        
        return self.template_matcher.match_multiple_templates(screenshot, template_names)
    
    def wait_for_ui_element(self, template_name: str, timeout: float = None,
                           check_interval: float = None) -> Optional[UIElement]:
        """等待UI元素出现"""
        if timeout is None:
            timeout = self._get_config_value('game_detector.ui_element_timeout', 10.0)
        if check_interval is None:
            check_interval = self._get_config_value('game_detector.check_interval', 0.5)
            
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            element = self.find_ui_element(template_name)
            if element:
                return element
            time.sleep(check_interval)
        
        logger.warning(f"UI element not found within timeout: {template_name}")
        return None
    
    def wait_for_template(self, template_paths: List[str], timeout: float = None, 
                         check_interval: float = None) -> Optional[Tuple[str, UIElement]]:
        """等待模板出现在屏幕上"""
        if timeout is None:
            timeout = self._get_config_value('game_detector.template_timeout', 10.0)
        if check_interval is None:
            check_interval = self._get_config_value('game_detector.check_interval', 0.5)
            
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            screenshot = self.capture_screenshot()
            if screenshot is None:
                time.sleep(check_interval)
                continue
                
            # 检查每个模板
            for template_name in template_paths:
                threshold = self._get_config_value('game_detector.template_threshold', 0.8)
                element = self.template_matcher.match_template(
                    screenshot, template_name, threshold=threshold
                )
                if element:
                    return (template_name, element)
            
            time.sleep(check_interval)
        
        return None
    
    def is_game_running(self) -> bool:
        """检查游戏是否正在运行"""
        window = self.detect_game_window()
        if not window:
            return False
            
        try:
            # 检查窗口是否仍然有效
            return win32gui.IsWindow(window.hwnd) and win32gui.IsWindowVisible(window.hwnd)
        except Exception:
            return False
    
    def get_game_status(self) -> Dict:
        """获取游戏状态信息"""
        return {
            "window_found": self.window_manager.find_game_window() is not None,
            "current_scene": self.current_scene.value if self.current_scene else "unknown",
            "last_screenshot_time": getattr(self, 'last_screenshot_time', None),
            "templates_loaded": len(self.template_matcher.templates_cache)
        }
    
    def visualize_detection_results(self, screenshot: np.ndarray, 
                                  elements: List[UIElement], 
                                  save_path: Optional[str] = None) -> np.ndarray:
        """可视化检测结果，在截图上标注UI元素"""
        result_image = screenshot.copy()
        
        for element in elements:
            x, y = element.position
            w, h = element.size
            
            # 绘制边框
            color = (0, 255, 0)  # 绿色
            thickness = 2
            cv2.rectangle(result_image, (x, y), (x + w, y + h), color, thickness)
            
            # 添加标签
            label = f"{element.name} ({element.confidence:.2f})"
            if element.scale_factor != 1.0:
                label += f" x{element.scale_factor:.1f}"
            
            # 计算文本位置
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.6
            font_thickness = 1
            
            # 获取文本尺寸
            (text_w, text_h), baseline = cv2.getTextSize(label, font, font_scale, font_thickness)
            
            # 绘制文本背景
            cv2.rectangle(result_image, 
                         (x, y - text_h - 10), 
                         (x + text_w, y), 
                         (0, 0, 0), -1)
            
            # 绘制文本
            cv2.putText(result_image, label, 
                       (x, y - 5), 
                       font, font_scale, (255, 255, 255), font_thickness)
        
        # 保存结果图像
        if save_path:
            try:
                cv2.imwrite(save_path, result_image)
                logger.info(f"Detection result saved to: {save_path}")
            except Exception as e:
                logger.error(f"Failed to save detection result: {e}")
        
        return result_image
    
    def detect_and_visualize_scene(self, save_path: Optional[str] = None) -> Tuple[SceneType, np.ndarray]:
        """检测场景并可视化结果"""
        screenshot = self.capture_screenshot()
        if screenshot is None:
            return SceneType.UNKNOWN, None
        
        # 检测当前场景
        scene_type = self.detect_current_scene(screenshot)
        
        # 获取场景相关的所有UI元素
        all_elements = []
        if scene_type in self.scene_templates:
            template_names = self.scene_templates[scene_type]
            elements = self.template_matcher.match_multiple_templates(
                screenshot, template_names, 0.6
            )
            all_elements.extend(elements)
        
        # 可视化结果
        result_image = self.visualize_detection_results(screenshot, all_elements, save_path)
        
        return scene_type, result_image
    
    def bring_game_to_front(self) -> bool:
        """将游戏窗口置于前台"""
        return self.window_manager.bring_window_to_front()