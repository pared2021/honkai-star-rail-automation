"""游戏检测模块。

提供游戏状态检测和游戏窗口识别功能。
"""

import time
import logging
from typing import Optional, List, Dict, Any, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
import cv2
from pathlib import Path

# 可选依赖
try:
    import cairosvg
    from PIL import Image
    import io
    CAIROSVG_AVAILABLE = True
except (ImportError, OSError):
    CAIROSVG_AVAILABLE = False
    cairosvg = None
    Image = None
    io = None

try:
    import win32gui
    import win32ui
    import win32con
    import win32api
except ImportError:
    # 在非Windows环境下提供模拟实现
    win32gui = None
    win32ui = None
    win32con = None
    win32api = None

try:
    import psutil
except ImportError:
    psutil = None

from src.core.config_manager import ConfigManager


class SceneType(Enum):
    """场景类型枚举"""
    UNKNOWN = "unknown"
    MAIN_MENU = "main_menu"
    BATTLE = "battle"
    EXPLORATION = "exploration"
    DIALOGUE = "dialogue"
    INVENTORY = "inventory"
    SETTINGS = "settings"


@dataclass
class GameWindow:
    """游戏窗口信息"""
    hwnd: int
    title: str
    rect: Tuple[int, int, int, int]
    width: int
    height: int
    is_foreground: bool


@dataclass
class UIElement:
    """UI元素信息"""
    name: str
    position: Tuple[int, int]
    size: Tuple[int, int]
    confidence: float
    template_path: str

    @property
    def center(self) -> Tuple[int, int]:
        """获取元素中心点坐标"""
        x = self.position[0] + self.size[0] // 2
        y = self.position[1] + self.size[1] // 2
        return (x, y)

    @property
    def width(self) -> int:
        """获取元素宽度"""
        return self.size[0]

    @property
    def height(self) -> int:
        """获取元素高度"""
        return self.size[1]
    
    @property
    def top_left(self) -> Tuple[int, int]:
        """获取左上角坐标"""
        return self.position
    
    @property
    def bottom_right(self) -> Tuple[int, int]:
        """获取右下角坐标"""
        return (self.position[0] + self.size[0], self.position[1] + self.size[1])


@dataclass(frozen=True)
class TemplateInfo:
    """模板信息"""
    name: str
    image: np.ndarray
    threshold: float
    path: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class TemplateMatcher:
    """模板匹配器"""

    def __init__(self):
        self.templates_cache: Dict[str, Dict[str, Any]] = {}
        self.template_info_cache: Dict[str, TemplateInfo] = {}
        self.logger = logging.getLogger(__name__)



    def _load_template_file(self, template_path: Path, category: str) -> None:
        """加载单个模板文件"""
        try:
            if template_path.suffix.lower() == '.svg':
                image = self._convert_svg_to_image(template_path)
            else:
                image = cv2.imread(str(template_path))

            if image is not None:
                template_name = f"{category}_{template_path.stem}"
                self.templates_cache[template_name] = {
                    "image": image,
                    "threshold": 0.8,  # 默认阈值
                    "path": str(template_path),
                    "category": category,
                    "original_size": image.shape[:2]
                }
                self.logger.debug(f"加载模板: {template_name}")
        except Exception as e:
            self.logger.error(f"加载模板失败 {template_path}: {e}")
    
    def load_templates(self, templates_dir: str) -> None:
        """从目录加载所有模板
        
        Args:
            templates_dir: 模板目录路径
        """
        import os
        
        # 处理Mock对象或无效路径
        try:
            templates_dir_str = str(templates_dir)
        except:
            self.logger.warning(f"Invalid templates directory: {templates_dir}")
            return
            
        if not os.path.exists(templates_dir_str):
            self.logger.warning(f"Templates directory not found: {templates_dir_str}")
            return
        
        for filename in os.listdir(templates_dir_str):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.svg')):
                template_path = os.path.join(templates_dir_str, filename)
                self.load_template(template_path)

    def load_template(self, template_path: str, threshold: float = 0.8) -> Optional[TemplateInfo]:
        """加载模板图像
        
        Args:
            template_path: 模板文件路径
            threshold: 匹配阈值
            
        Returns:
            TemplateInfo对象，如果加载失败则返回None
        """
        try:
            import os
            template_name = os.path.splitext(os.path.basename(template_path))[0]
            
            # 检查是否已缓存
            if template_name in self.template_info_cache:
                return self.template_info_cache[template_name]
            
            # 加载图像
            if template_path.lower().endswith('.svg'):
                # SVG文件处理
                if not CAIROSVG_AVAILABLE:
                    self.logger.warning(f"cairosvg not available, skipping SVG template: {template_path}")
                    return None
                try:
                    with open(template_path, 'r', encoding='utf-8') as f:
                        svg_content = f.read()
                    image = self._convert_svg_to_image(svg_content)
                    if image is None:
                        self.logger.warning(f"Failed to convert SVG template: {template_path}")
                        return None
                except Exception as e:
                    self.logger.warning(f"Error reading SVG file {template_path}: {e}")
                    return None
            else:
                # 普通图像文件
                image = cv2.imread(template_path)
                if image is None:
                    self.logger.warning(f"Failed to load template: {template_path}")
                    return None
            
            # 创建模板信息
            template_info = TemplateInfo(
                name=template_name,
                image=image,
                threshold=threshold,
                path=template_path
            )
            
            # 缓存模板信息和图像
            self.template_info_cache[template_name] = template_info
            self.templates_cache[template_name] = {
                "image": image,
                "threshold": threshold,
                "path": template_path,
                "category": "custom",
                "original_size": image.shape[:2]
            }
            
            self.logger.info(f"Loaded template: {template_name}")
            return template_info
            
        except Exception as e:
            self.logger.error(f"Error loading template {template_path}: {e}")
            return None

    def _convert_svg_to_image(self, svg_content: str) -> Optional[np.ndarray]:
        """将SVG内容转换为图像
        
        Args:
            svg_content: SVG文件内容
            
        Returns:
            转换后的图像数组，如果转换失败则返回None
        """
        if not CAIROSVG_AVAILABLE:
            self.logger.warning("cairosvg not available, cannot convert SVG")
            return None
            
        try:
            # 使用cairosvg将SVG转换为PNG字节
            png_bytes = cairosvg.svg2png(bytestring=svg_content.encode('utf-8'))
            
            # 使用PIL加载PNG字节
            image_pil = Image.open(io.BytesIO(png_bytes))
            
            # 转换为RGB模式（如果不是的话）
            if image_pil.mode != 'RGB':
                image_pil = image_pil.convert('RGB')
            
            # 转换为numpy数组
            image_array = np.array(image_pil)
            
            # 转换为BGR格式（OpenCV使用BGR）
            image_bgr = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)
            
            return image_bgr
            
        except Exception as e:
            self.logger.error(f"Failed to convert SVG to image: {e}")
            return None
    
    def _calculate_scale_factors(self, template_shape: Tuple[int, int], 
                               screenshot_shape: Tuple[int, int]) -> List[float]:
        """计算缩放因子
        
        Args:
            template_shape: 模板图像形状 (height, width)
            screenshot_shape: 截图形状 (height, width)
            
        Returns:
            缩放因子列表
        """
        # 基础缩放范围
        scale_factors = [0.8, 0.9, 1.0, 1.1, 1.2]
        
        # 根据图像大小调整缩放范围
        template_h, template_w = template_shape[:2]
        screenshot_h, screenshot_w = screenshot_shape[:2]
        
        # 如果模板太大，添加更小的缩放因子
        if template_w > screenshot_w * 0.5 or template_h > screenshot_h * 0.5:
            scale_factors.extend([0.5, 0.6, 0.7])
        
        # 如果模板很小，添加更大的缩放因子
        if template_w < screenshot_w * 0.1 and template_h < screenshot_h * 0.1:
            scale_factors.extend([1.3, 1.4, 1.5])
        
        return sorted(set(scale_factors))
    
    def _scale_template(self, template: np.ndarray, scale_factor: float) -> np.ndarray:
        """缩放模板图像
        
        Args:
            template: 原始模板图像
            scale_factor: 缩放因子
            
        Returns:
            缩放后的模板图像
        """
        if scale_factor == 1.0:
            return template
        
        height, width = template.shape[:2]
        new_width = int(width * scale_factor)
        new_height = int(height * scale_factor)
        
        return cv2.resize(template, (new_width, new_height), interpolation=cv2.INTER_AREA)

    def match_template(self, screenshot: np.ndarray, template_name: Union[str, TemplateInfo]) -> Optional[UIElement]:
        """在截图中匹配模板
        
        Args:
            screenshot: 游戏截图
            template_name: 模板名称或TemplateInfo对象
            
        Returns:
            匹配到的UI元素，如果未找到则返回None
        """
        try:
            # 获取模板信息
            if isinstance(template_name, str):
                if template_name not in self.template_info_cache:
                    self.logger.warning(f"Template not found: {template_name}")
                    return None
                template_info = self.template_info_cache[template_name]
                template_image = template_info.image
                threshold = template_info.threshold
                template_path = template_info.path
            else:
                template_info = template_name
                template_image = template_info.image
                threshold = template_info.threshold
                template_path = template_info.path
            
            # 执行模板匹配
            result = cv2.matchTemplate(screenshot, template_image, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            if max_val >= threshold:
                # 计算边界框
                h, w = template_image.shape[:2]
                top_left = max_loc
                bottom_right = (top_left[0] + w, top_left[1] + h)
                
                return UIElement(
                    name=template_info.name,
                    position=top_left,
                    size=(w, h),
                    confidence=max_val,
                    template_path=template_path
                )
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error matching template: {e}")
            return None

    def match_multiple_templates(self, screenshot: np.ndarray, template_names: List[str]) -> List[UIElement]:
        """匹配多个模板"""
        results = []
        for template_name in template_names:
            element = self.match_template(screenshot, template_name)
            if element:
                results.append(element)
        return results




class WindowManager:
    """窗口管理器"""

    def __init__(self):
        self.current_window: Optional[GameWindow] = None
        self.logger = logging.getLogger(__name__)
        self.game_titles = ["崩坏：星穹铁道", "Honkai: Star Rail", "StarRail"]

    def find_game_window(self) -> Optional[GameWindow]:
        """查找游戏窗口"""
        if win32gui is None:
            self.logger.warning("win32gui不可用，无法查找窗口")
            return None

        found_windows = []
        
        def enum_callback(hwnd, param):
            if win32gui.IsWindowVisible(hwnd):
                window_title = win32gui.GetWindowText(hwnd)
                if any(title in window_title for title in self.game_titles):
                    rect = win32gui.GetWindowRect(hwnd)
                    width = rect[2] - rect[0]
                    height = rect[3] - rect[1]
                    is_foreground = win32gui.GetForegroundWindow() == hwnd
                    
                    game_window = GameWindow(
                        hwnd=hwnd,
                        title=window_title,
                        rect=rect,
                        width=width,
                        height=height,
                        is_foreground=is_foreground
                    )
                    found_windows.append(game_window)
            return True

        try:
            win32gui.EnumWindows(enum_callback, None)
            
            if found_windows:
                # 优先返回前台窗口
                for window in found_windows:
                    if window.is_foreground:
                        self.current_window = window
                        return window
                
                # 如果没有前台窗口，返回第一个
                self.current_window = found_windows[0]
                return found_windows[0]
                
        except Exception as e:
            self.logger.error(f"查找游戏窗口失败: {e}")
            
        return None

    def capture_window(self, game_window: GameWindow) -> Optional[np.ndarray]:
        """截取窗口图像"""
        if win32gui is None or win32ui is None:
            self.logger.warning("Windows API不可用，无法截取窗口")
            return None

        try:
            hwnd = game_window.hwnd
            width = game_window.width
            height = game_window.height

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

            # 获取位图数据
            bmp_info = save_bitmap.GetInfo()
            bmp_str = save_bitmap.GetBitmapBits(True)

            # 转换为numpy数组
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
            self.logger.error(f"截取窗口失败: {e}")
            return None

    def bring_window_to_front(self, game_window: GameWindow) -> bool:
        """将窗口置于前台"""
        if win32gui is None:
            return False

        try:
            hwnd = game_window.hwnd
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            win32gui.SetForegroundWindow(hwnd)
            return True
        except Exception as e:
            self.logger.error(f"窗口置前失败: {e}")
            return False


class GameDetector:
    """游戏检测器主类"""

    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.window_manager = WindowManager()
        self.template_matcher = TemplateMatcher()
        self.current_scene = SceneType.UNKNOWN
        self.last_screenshot: Optional[np.ndarray] = None
        self.logger = logging.getLogger(__name__)
        
        # 加载模板
        templates_dir = getattr(config_manager, 'templates_dir', 'templates')
        self.template_matcher.load_templates(templates_dir)

    def detect_game_window(self) -> Optional[GameWindow]:
        """检测游戏窗口"""
        window = self.window_manager.find_game_window()
        if window:
            self.window_manager.current_window = window
        return window

    def _find_window_by_process(self) -> Optional[GameWindow]:
        """通过进程名查找窗口"""
        if psutil is None:
            return None
            
        try:
            for proc in psutil.process_iter(['name']):
                if 'StarRail' in proc.info['name']:
                    return self.window_manager.find_game_window()
        except Exception as e:
            self.logger.error(f"通过进程查找窗口失败: {e}")
        return None

    def capture_screenshot(self) -> Optional[np.ndarray]:
        """截取游戏截图"""
        if not self.window_manager.current_window:
            return None
            
        screenshot = self.window_manager.capture_window(self.window_manager.current_window)
        if screenshot is not None:
            self.last_screenshot = screenshot
        return screenshot

    def find_ui_element(self, template_name: str) -> Optional[UIElement]:
        """查找UI元素"""
        screenshot = self.capture_screenshot()
        if screenshot is None:
            return None
            
        return self.template_matcher.match_template(screenshot, template_name)

    def find_multiple_ui_elements(self, template_names: List[str]) -> List[UIElement]:
        """查找多个UI元素"""
        screenshot = self.capture_screenshot()
        if screenshot is None:
            return []
            
        return self.template_matcher.match_multiple_templates(screenshot, template_names)

    def wait_for_ui_element(self, template_name: str, timeout: float = 10.0, interval: float = 0.5) -> Optional[UIElement]:
        """等待UI元素出现"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            element = self.find_ui_element(template_name)
            if element:
                return element
            time.sleep(interval)
            
        return None

    def wait_for_template(self, template_name: str, timeout: float = 10.0, interval: float = 0.5) -> Optional[UIElement]:
        """等待模板出现（别名方法）"""
        return self.wait_for_ui_element(template_name, timeout, interval)

    def is_game_running(self) -> bool:
        """检查游戏是否运行"""
        window = self.detect_game_window()
        if not window:
            return False
            
        try:
            if win32gui:
                return win32gui.IsWindow(window.hwnd) and win32gui.IsWindowVisible(window.hwnd)
        except:
            pass
            
        return False

    def get_game_status(self) -> Dict[str, Any]:
        """获取游戏状态"""
        window = self.window_manager.find_game_window()
        
        return {
            'window_found': window is not None,
            'current_scene': self.current_scene.value,
            'templates_loaded': len(self.template_matcher.templates_cache),
            'window_info': {
                'title': window.title if window else None,
                'size': (window.width, window.height) if window else None,
                'is_foreground': window.is_foreground if window else False
            } if window else None
        }

    def bring_game_to_front(self) -> bool:
        """将游戏窗口置于前台"""
        if not self.window_manager.current_window:
            return False
            
        return self.window_manager.bring_window_to_front(self.window_manager.current_window)

    def detect_current_scene(self) -> SceneType:
        """检测当前场景"""
        screenshot = self.capture_screenshot()
        if screenshot is None:
            return SceneType.UNKNOWN
            
        # 定义场景检测模板
        scene_templates = {
            SceneType.MAIN_MENU: ['ui_main_menu', 'ui_start_button'],
            SceneType.BATTLE: ['ui_battle_ui', 'ui_skill_button'],
            SceneType.EXPLORATION: ['ui_minimap', 'ui_character_icon'],
            SceneType.DIALOGUE: ['ui_dialogue_box', 'ui_next_button'],
            SceneType.INVENTORY: ['ui_inventory', 'ui_item_grid'],
            SceneType.SETTINGS: ['ui_settings', 'ui_options_menu']
        }
        
        best_scene = SceneType.UNKNOWN
        best_confidence = 0.0
        
        for scene_type, templates in scene_templates.items():
            elements = self.template_matcher.match_multiple_templates(screenshot, templates)
            if elements:
                # 使用最高置信度作为场景置信度
                max_confidence = max(element.confidence for element in elements)
                if max_confidence > best_confidence:
                    best_confidence = max_confidence
                    best_scene = scene_type
        
        self.current_scene = best_scene
        return best_scene

    def visualize_detection_results(self, screenshot: np.ndarray, elements: List[UIElement], save_path: Optional[str] = None) -> np.ndarray:
        """可视化检测结果"""
        result_img = screenshot.copy()
        
        for element in elements:
            # 绘制边界框
            cv2.rectangle(result_img, element.top_left, element.bottom_right, (0, 255, 0), 2)
            
            # 绘制标签
            label = f"{element.name}: {element.confidence:.2f}"
            cv2.putText(result_img, label, 
                       (element.top_left[0], element.top_left[1] - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        
        if save_path:
            cv2.imwrite(save_path, result_img)
            
        return result_img

    def detect_and_visualize_scene(self, save_path: Optional[str] = None) -> Optional[np.ndarray]:
        """检测并可视化当前场景"""
        screenshot = self.capture_screenshot()
        if screenshot is None:
            return None
            
        scene = self.detect_current_scene()
        
        # 获取当前场景的所有检测到的元素
        all_templates = list(self.template_matcher.templates_cache.keys())
        elements = self.template_matcher.match_multiple_templates(screenshot, all_templates)
        
        return self.visualize_detection_results(screenshot, elements, save_path)