"""游戏检测器模块。

提供游戏窗口检测、进程识别和状态监控功能。
"""

import time
import psutil
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Set

try:
    import win32gui
    import win32process
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False


class GameStatus(Enum):
    """游戏状态枚举。"""
    
    NOT_DETECTED = "not_detected"
    DETECTED = "detected"
    RUNNING = "running"
    PAUSED = "paused"
    MINIMIZED = "minimized"
    FULLSCREEN = "fullscreen"


@dataclass
class GameInfo:
    """游戏信息数据类。"""
    
    name: str
    process_name: str
    window_title: str
    pid: Optional[int] = None
    hwnd: Optional[int] = None
    status: GameStatus = GameStatus.NOT_DETECTED
    detected_at: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    window_rect: Optional[tuple] = None
    is_foreground: bool = False


class GameDetector:
    """游戏检测器主类。"""
    
    def __init__(self):
        """初始化游戏检测器。"""
        self.known_games: Dict[str, GameInfo] = {}
        self.detected_games: Dict[str, GameInfo] = {}
        self.monitoring = False
        self._last_scan_time = 0
        self._scan_interval = 1.0  # 扫描间隔（秒）
        
        # 预定义的游戏列表
        self._initialize_known_games()
    
    def _initialize_known_games(self):
        """初始化已知游戏列表。"""
        known_game_configs = [
            {"name": "原神", "process_name": "YuanShen.exe", "window_title": "原神"},
            {"name": "崩坏：星穹铁道", "process_name": "StarRail.exe", "window_title": "崩坏：星穹铁道"},
            {"name": "绝区零", "process_name": "ZenlessZoneZero.exe", "window_title": "绝区零"},
            {"name": "明日方舟", "process_name": "ArknightsTap.exe", "window_title": "明日方舟"},
            {"name": "Steam", "process_name": "steam.exe", "window_title": "Steam"},
        ]
        
        for config in known_game_configs:
            game_info = GameInfo(
                name=config["name"],
                process_name=config["process_name"],
                window_title=config["window_title"]
            )
            self.known_games[config["name"]] = game_info
    
    def add_game(self, name: str, process_name: str, window_title: str) -> None:
        """添加游戏到检测列表。
        
        Args:
            name: 游戏名称
            process_name: 进程名称
            window_title: 窗口标题
        """
        game_info = GameInfo(
            name=name,
            process_name=process_name,
            window_title=window_title
        )
        self.known_games[name] = game_info
    
    def remove_game(self, name: str) -> bool:
        """从检测列表移除游戏。
        
        Args:
            name: 游戏名称
            
        Returns:
            是否成功移除
        """
        if name in self.known_games:
            del self.known_games[name]
            if name in self.detected_games:
                del self.detected_games[name]
            return True
        return False
    
    def scan_for_games(self) -> List[GameInfo]:
        """扫描当前运行的游戏。
        
        Returns:
            检测到的游戏列表
        """
        current_time = time.time()
        if current_time - self._last_scan_time < self._scan_interval:
            return list(self.detected_games.values())
        
        self._last_scan_time = current_time
        detected = []
        
        # 获取所有运行的进程
        running_processes = {proc.info['name'].lower(): proc.info 
                           for proc in psutil.process_iter(['pid', 'name', 'create_time'])}
        
        # 检查已知游戏
        for game_name, game_info in self.known_games.items():
            process_name_lower = game_info.process_name.lower()
            
            if process_name_lower in running_processes:
                proc_info = running_processes[process_name_lower]
                
                # 更新游戏信息
                updated_game = GameInfo(
                    name=game_info.name,
                    process_name=game_info.process_name,
                    window_title=game_info.window_title,
                    pid=proc_info['pid'],
                    status=GameStatus.RUNNING,
                    detected_at=game_info.detected_at or datetime.now(),
                    last_seen=datetime.now()
                )
                
                # 如果支持Windows API，获取窗口信息
                if WIN32_AVAILABLE:
                    self._update_window_info(updated_game)
                
                self.detected_games[game_name] = updated_game
                detected.append(updated_game)
            else:
                # 游戏未运行，从检测列表中移除
                if game_name in self.detected_games:
                    del self.detected_games[game_name]
        
        return detected
    
    def detect_game_window(self) -> Optional[Dict[str, Any]]:
        """检测游戏窗口.
        
        Returns:
            游戏窗口信息字典，如果未找到则返回None
        """
        try:
            # 尝试多种可能的窗口标题
            possible_titles = [
                "崩坏：星穹铁道",
                "Honkai: Star Rail",
                "崩坏星穹铁道",
                "Star Rail"
            ]
            
            window = None
            for title in possible_titles:
                windows = gw.getWindowsWithTitle(title)
                if windows:
                    window = windows[0]
                    logger.debug(f"找到游戏窗口: {title}")
                    break
            
            if window:
                # 验证窗口有效性
                if window.width <= 0 or window.height <= 0:
                    logger.warning(f"游戏窗口尺寸异常: {window.width}x{window.height}")
                    return None
                
                window_info = {
                    'title': window.title,
                    'left': window.left,
                    'top': window.top,
                    'width': window.width,
                    'height': window.height,
                    'is_active': window.isActive
                }
                
                logger.debug(f"游戏窗口信息: {window_info}")
                return window_info
            else:
                logger.debug("未找到游戏窗口")
                return None
                
        except Exception as e:
            logger.error(f"检测游戏窗口时出错: {str(e)}", exc_info=True)
            return None
    
    def _update_window_info(self, game_info: GameInfo) -> None:
        """更新游戏窗口信息（仅Windows）。
        
        Args:
            game_info: 游戏信息对象
        """
        if not WIN32_AVAILABLE or not game_info.pid:
            return
        
        def enum_windows_callback(hwnd, windows):
            if win32gui.IsWindowVisible(hwnd):
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                if pid == game_info.pid:
                    window_title = win32gui.GetWindowText(hwnd)
                    if game_info.window_title.lower() in window_title.lower():
                        windows.append((hwnd, window_title))
            return True
        
        windows = []
        try:
            win32gui.EnumWindows(enum_windows_callback, windows)
            
            if windows:
                hwnd, title = windows[0]
                game_info.hwnd = hwnd
                
                # 获取窗口位置和大小
                try:
                    rect = win32gui.GetWindowRect(hwnd)
                    game_info.window_rect = rect
                    
                    # 检查是否为前台窗口
                    foreground_hwnd = win32gui.GetForegroundWindow()
                    game_info.is_foreground = (hwnd == foreground_hwnd)
                    
                    # 检查窗口状态
                    if win32gui.IsIconic(hwnd):
                        game_info.status = GameStatus.MINIMIZED
                    elif game_info.is_foreground:
                        # 简单的全屏检测
                        screen_width = win32gui.GetSystemMetrics(0)
                        screen_height = win32gui.GetSystemMetrics(1)
                        if (rect[2] - rect[0] >= screen_width and 
                            rect[3] - rect[1] >= screen_height):
                            game_info.status = GameStatus.FULLSCREEN
                        else:
                            game_info.status = GameStatus.RUNNING
                    else:
                        game_info.status = GameStatus.RUNNING
                        
                except Exception:
                    # 如果获取窗口信息失败，保持基本状态
                    pass
                    
        except Exception:
            # 如果枚举窗口失败，保持基本状态
            pass
    
    def get_detected_games(self) -> List[GameInfo]:
        """获取当前检测到的游戏列表。
        
        Returns:
            检测到的游戏列表
        """
        return list(self.detected_games.values())
    
    def get_game_by_name(self, name: str) -> Optional[GameInfo]:
        """根据名称获取游戏信息。
        
        Args:
            name: 游戏名称
            
        Returns:
            游戏信息，如果未找到返回None
        """
        return self.detected_games.get(name)
    
    def is_game_running(self, name: str) -> bool:
        """检查指定游戏是否正在运行。
        
        Args:
            name: 游戏名称
            
        Returns:
            游戏是否正在运行
        """
        game_info = self.detected_games.get(name)
        return game_info is not None and game_info.status in [
            GameStatus.RUNNING, GameStatus.FULLSCREEN, GameStatus.MINIMIZED
        ]
    
    def get_foreground_game(self) -> Optional[GameInfo]:
        """获取当前前台的游戏。
        
        Returns:
            前台游戏信息，如果没有返回None
        """
        for game_info in self.detected_games.values():
            if game_info.is_foreground:
                return game_info
        return None
    
    def start_monitoring(self) -> None:
        """开始监控游戏。"""
        self.monitoring = True
    
    def stop_monitoring(self) -> None:
        """停止监控游戏。"""
        self.monitoring = False
    
    def get_statistics(self) -> Dict[str, any]:
        """获取检测统计信息。
        
        Returns:
            统计信息字典
        """
        return {
            "known_games_count": len(self.known_games),
            "detected_games_count": len(self.detected_games),
            "running_games": [game.name for game in self.detected_games.values() 
                             if game.status in [GameStatus.RUNNING, GameStatus.FULLSCREEN]],
            "monitoring": self.monitoring,
            "last_scan_time": self._last_scan_time
        }