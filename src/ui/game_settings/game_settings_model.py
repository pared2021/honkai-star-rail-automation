"""游戏设置模型层

该模块定义了游戏设置的Model层，负责管理游戏设置的数据状态和业务逻辑。
"""

import os
from typing import Dict, Any, Optional
from PyQt6.QtCore import QObject, pyqtSignal

from ...services.ui_service_facade import IUIServiceFacade
from src.utils.logger import logger


class GameSettingsModel(QObject):
    """游戏设置模型类
    
    负责管理游戏设置的数据状态和业务逻辑。
    """
    
    # 数据变化信号
    game_path_changed = pyqtSignal(str)  # 游戏路径变化
    resolution_changed = pyqtSignal(str)  # 分辨率变化
    window_title_changed = pyqtSignal(str)  # 窗口标题变化
    window_mode_changed = pyqtSignal(str)  # 窗口模式变化
    ui_scale_changed = pyqtSignal(str)  # 界面缩放变化
    always_on_top_changed = pyqtSignal(bool)  # 置顶状态变化
    auto_focus_changed = pyqtSignal(bool)  # 自动聚焦变化
    detection_timeout_changed = pyqtSignal(int)  # 检测超时变化
    detection_interval_changed = pyqtSignal(int)  # 检测间隔变化
    enable_detection_changed = pyqtSignal(bool)  # 启用检测变化
    
    # 状态信号
    path_status_changed = pyqtSignal(str, str)  # 路径状态变化 (状态文本, 样式)
    settings_validated = pyqtSignal(bool, str)  # 设置验证结果 (是否有效, 错误信息)
    
    # 错误信号
    error_occurred = pyqtSignal(str)  # 错误发生
    
    def __init__(self, ui_service: IUIServiceFacade, parent=None):
        super().__init__(parent)
        self.ui_service = ui_service
        
        # 游戏设置数据
        self._game_path = ""
        self._resolution = "1920x1080"
        self._window_title = "崩坏：星穹铁道"
        self._window_mode = "窗口化"
        self._ui_scale = "100%"
        self._always_on_top = False
        self._auto_focus = True
        self._detection_timeout = 30
        self._detection_interval = 1
        self._enable_detection = True
        
        # 路径状态
        self._path_status_text = "未设置游戏路径"
        self._path_status_style = "color: #ff6b6b; font-size: 11px;"
        
        # 常见游戏路径
        self._common_game_paths = [
            r"C:\Program Files\miHoYo\Star Rail\Game\StarRail.exe",
            r"C:\Program Files (x86)\miHoYo\Star Rail\Game\StarRail.exe",
            r"D:\miHoYo\Star Rail\Game\StarRail.exe",
            r"E:\miHoYo\Star Rail\Game\StarRail.exe",
            r"F:\miHoYo\Star Rail\Game\StarRail.exe",
        ]
        
        # 支持的分辨率
        self._supported_resolutions = [
            "1920x1080", "1366x768", "1280x720", "1600x900",
            "1440x900", "1680x1050", "2560x1440", "3840x2160", "自定义"
        ]
        
        # 窗口模式
        self._window_modes = ["全屏", "窗口化", "无边框窗口"]
        
        # 界面缩放选项
        self._ui_scales = ["75%", "100%", "125%", "150%", "175%", "200%"]
        
        logger.info("游戏设置模型初始化完成")
    
    # 属性访问器
    @property
    def game_path(self) -> str:
        return self._game_path
    
    @property
    def resolution(self) -> str:
        return self._resolution
    
    @property
    def window_title(self) -> str:
        return self._window_title
    
    @property
    def window_mode(self) -> str:
        return self._window_mode
    
    @property
    def ui_scale(self) -> str:
        return self._ui_scale
    
    @property
    def always_on_top(self) -> bool:
        return self._always_on_top
    
    @property
    def auto_focus(self) -> bool:
        return self._auto_focus
    
    @property
    def detection_timeout(self) -> int:
        return self._detection_timeout
    
    @property
    def detection_interval(self) -> int:
        return self._detection_interval
    
    @property
    def enable_detection(self) -> bool:
        return self._enable_detection
    
    @property
    def path_status_text(self) -> str:
        return self._path_status_text
    
    @property
    def path_status_style(self) -> str:
        return self._path_status_style
    
    @property
    def supported_resolutions(self) -> list:
        return self._supported_resolutions.copy()
    
    @property
    def window_modes(self) -> list:
        return self._window_modes.copy()
    
    @property
    def ui_scales(self) -> list:
        return self._ui_scales.copy()
    
    # 设置方法
    def set_game_path(self, path: str):
        """设置游戏路径"""
        if self._game_path != path:
            self._game_path = path
            self._update_path_status(path)
            self.game_path_changed.emit(path)
            self._save_setting("game_path", path)
    
    def set_resolution(self, resolution: str):
        """设置分辨率"""
        if self._resolution != resolution:
            self._resolution = resolution
            self.resolution_changed.emit(resolution)
            self._save_setting("resolution", resolution)
    
    def set_window_title(self, title: str):
        """设置窗口标题"""
        if self._window_title != title:
            self._window_title = title
            self.window_title_changed.emit(title)
            self._save_setting("window_title", title)
    
    def set_window_mode(self, mode: str):
        """设置窗口模式"""
        if self._window_mode != mode:
            self._window_mode = mode
            self.window_mode_changed.emit(mode)
            self._save_setting("window_mode", mode)
    
    def set_ui_scale(self, scale: str):
        """设置界面缩放"""
        if self._ui_scale != scale:
            self._ui_scale = scale
            self.ui_scale_changed.emit(scale)
            self._save_setting("ui_scale", scale)
    
    def set_always_on_top(self, enabled: bool):
        """设置置顶状态"""
        if self._always_on_top != enabled:
            self._always_on_top = enabled
            self.always_on_top_changed.emit(enabled)
            self._save_setting("always_on_top", enabled)
    
    def set_auto_focus(self, enabled: bool):
        """设置自动聚焦"""
        if self._auto_focus != enabled:
            self._auto_focus = enabled
            self.auto_focus_changed.emit(enabled)
            self._save_setting("auto_focus", enabled)
    
    def set_detection_timeout(self, timeout: int):
        """设置检测超时"""
        if self._detection_timeout != timeout:
            self._detection_timeout = timeout
            self.detection_timeout_changed.emit(timeout)
            self._save_setting("detection_timeout", timeout)
    
    def set_detection_interval(self, interval: int):
        """设置检测间隔"""
        if self._detection_interval != interval:
            self._detection_interval = interval
            self.detection_interval_changed.emit(interval)
            self._save_setting("detection_interval", interval)
    
    def set_enable_detection(self, enabled: bool):
        """设置启用检测"""
        if self._enable_detection != enabled:
            self._enable_detection = enabled
            self.enable_detection_changed.emit(enabled)
            self._save_setting("enable_detection", enabled)
    
    # 业务逻辑方法
    def load_settings(self):
        """加载设置"""
        try:
            game_config = self.ui_service.get_game_config()
            
            # 加载各项设置
            self._game_path = game_config.get("game_path", "")
            self._resolution = game_config.get("resolution", "1920x1080")
            self._window_title = game_config.get("window_title", "崩坏：星穹铁道")
            self._window_mode = game_config.get("window_mode", "窗口化")
            self._ui_scale = game_config.get("ui_scale", "100%")
            self._always_on_top = game_config.get("always_on_top", False)
            self._auto_focus = game_config.get("auto_focus", True)
            self._detection_timeout = game_config.get("detection_timeout", 30)
            self._detection_interval = game_config.get("detection_interval", 1)
            self._enable_detection = game_config.get("enable_detection", True)
            
            # 更新路径状态
            self._update_path_status(self._game_path)
            
            # 发射所有变化信号
            self.game_path_changed.emit(self._game_path)
            self.resolution_changed.emit(self._resolution)
            self.window_title_changed.emit(self._window_title)
            self.window_mode_changed.emit(self._window_mode)
            self.ui_scale_changed.emit(self._ui_scale)
            self.always_on_top_changed.emit(self._always_on_top)
            self.auto_focus_changed.emit(self._auto_focus)
            self.detection_timeout_changed.emit(self._detection_timeout)
            self.detection_interval_changed.emit(self._detection_interval)
            self.enable_detection_changed.emit(self._enable_detection)
            
            logger.info("游戏设置加载完成")
            
        except Exception as e:
            error_msg = f"加载游戏设置失败: {e}"
            logger.error(error_msg)
            self.error_occurred.emit(error_msg)
    
    def auto_detect_game_path(self) -> Optional[str]:
        """自动检测游戏路径"""
        try:
            for path in self._common_game_paths:
                if os.path.exists(path):
                    self.set_game_path(path)
                    logger.info(f"自动检测到游戏路径: {path}")
                    return path
            
            logger.info("未能自动检测到游戏路径")
            return None
            
        except Exception as e:
            error_msg = f"自动检测游戏路径失败: {e}"
            logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return None
    
    def validate_settings(self) -> tuple[bool, str]:
        """验证设置有效性"""
        try:
            # 验证游戏路径
            if self._game_path and not os.path.exists(self._game_path):
                error_msg = "游戏路径无效，请检查路径是否正确"
                self.settings_validated.emit(False, error_msg)
                return False, error_msg
            
            # 验证窗口标题
            if not self._window_title.strip():
                error_msg = "窗口标题不能为空"
                self.settings_validated.emit(False, error_msg)
                return False, error_msg
            
            # 验证自定义分辨率
            if self._resolution == "自定义":
                error_msg = "自定义分辨率需要在View层处理"
                self.settings_validated.emit(False, error_msg)
                return False, error_msg
            
            # 验证分辨率格式
            if "x" in self._resolution:
                try:
                    width, height = map(int, self._resolution.split("x"))
                    if width < 800 or height < 600:
                        error_msg = "分辨率不能小于 800x600"
                        self.settings_validated.emit(False, error_msg)
                        return False, error_msg
                except ValueError:
                    error_msg = "分辨率格式无效"
                    self.settings_validated.emit(False, error_msg)
                    return False, error_msg
            
            self.settings_validated.emit(True, "")
            return True, ""
            
        except Exception as e:
            error_msg = f"验证设置失败: {e}"
            logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return False, error_msg
    
    def reset_to_defaults(self):
        """重置为默认设置"""
        try:
            self.ui_service.reset_game_config()
            self.load_settings()
            logger.info("游戏设置已重置为默认值")
            
        except Exception as e:
            error_msg = f"重置设置失败: {e}"
            logger.error(error_msg)
            self.error_occurred.emit(error_msg)
    
    def apply_settings(self):
        """应用设置"""
        try:
            # 验证设置
            is_valid, error_msg = self.validate_settings()
            if not is_valid:
                return False
            
            # 保存配置
            self.ui_service.save_game_config()
            logger.info("游戏设置已应用")
            return True
            
        except Exception as e:
            error_msg = f"应用设置失败: {e}"
            logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return False
    
    def test_game_connection(self) -> bool:
        """测试游戏连接"""
        try:
            if not self._game_path or not os.path.exists(self._game_path):
                self.error_occurred.emit("请先设置有效的游戏路径")
                return False
            
            # 这里可以添加实际的游戏检测逻辑
            # 目前只是简单检查文件存在性
            logger.info("游戏连接测试完成")
            return True
            
        except Exception as e:
            error_msg = f"游戏连接测试失败: {e}"
            logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return False
    
    def get_current_settings(self) -> Dict[str, Any]:
        """获取当前设置"""
        return {
            "game_path": self._game_path,
            "resolution": self._resolution,
            "window_title": self._window_title,
            "window_mode": self._window_mode,
            "ui_scale": self._ui_scale,
            "always_on_top": self._always_on_top,
            "auto_focus": self._auto_focus,
            "detection_timeout": self._detection_timeout,
            "detection_interval": self._detection_interval,
            "enable_detection": self._enable_detection,
        }
    
    # 私有方法
    def _update_path_status(self, path: str):
        """更新路径状态"""
        if not path:
            self._path_status_text = "未设置游戏路径"
            self._path_status_style = "color: #ff6b6b; font-size: 11px;"
        elif os.path.exists(path):
            self._path_status_text = "✓ 路径有效"
            self._path_status_style = "color: #51cf66; font-size: 11px;"
        else:
            self._path_status_text = "✗ 路径无效"
            self._path_status_style = "color: #ff6b6b; font-size: 11px;"
        
        self.path_status_changed.emit(self._path_status_text, self._path_status_style)
    
    def _save_setting(self, key: str, value: Any):
        """保存单个设置"""
        try:
            self.ui_service.update_game_config(key, value)
        except Exception as e:
            logger.error(f"保存设置失败: {e}")
    
    def cleanup(self):
        """清理资源"""
        logger.info("游戏设置模型清理完成")