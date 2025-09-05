"""游戏设置MVP组合

该模块定义了游戏设置的MVP组合类，将Model、View和Presenter组合成一个完整的组件。
"""

from typing import Dict, Any, Optional
from PyQt6.QtCore import QObject, pyqtSignal

from .game_settings_model import GameSettingsModel
from .game_settings_view import GameSettingsView
from .game_settings_presenter import GameSettingsPresenter
from ...services.ui_service_facade import IUIServiceFacade
from src.utils.logger import logger


class GameSettingsMVP(QObject):
    """游戏设置MVP组合类
    
    将GameSettingsModel、GameSettingsView和GameSettingsPresenter组合成一个完整的组件。
    """
    
    # 业务信号
    settings_changed = pyqtSignal(str, str, object)  # 设置变化 (category, key, value)
    game_path_updated = pyqtSignal(str)  # 游戏路径更新
    resolution_updated = pyqtSignal(str)  # 分辨率更新
    window_settings_updated = pyqtSignal(dict)  # 窗口设置更新
    detection_settings_updated = pyqtSignal(dict)  # 检测设置更新
    
    # 状态信号
    validation_result = pyqtSignal(bool, str)  # 验证结果
    connection_test_result = pyqtSignal(bool, str)  # 连接测试结果
    settings_applied = pyqtSignal(bool)  # 设置应用结果
    settings_reset = pyqtSignal()  # 设置重置
    
    def __init__(self, ui_service: IUIServiceFacade, parent=None):
        super().__init__(parent)
        self.ui_service = ui_service
        
        # 创建MVP组件
        self._model = GameSettingsModel(ui_service, self)
        self._view = GameSettingsView()
        self._presenter = GameSettingsPresenter(self._model, self._view, self)
        
        # 连接业务信号
        self._connect_business_signals()
        
        logger.info("游戏设置MVP组合初始化完成")
    
    def _connect_business_signals(self):
        """连接业务信号"""
        # Model信号转发
        self._model.game_path_changed.connect(self.game_path_updated.emit)
        self._model.resolution_changed.connect(self.resolution_updated.emit)
        self._model.settings_validated.connect(self.validation_result.emit)
        
        # 组合信号
        self._model.window_title_changed.connect(self._on_window_settings_changed)
        self._model.window_mode_changed.connect(self._on_window_settings_changed)
        self._model.always_on_top_changed.connect(self._on_window_settings_changed)
        self._model.auto_focus_changed.connect(self._on_window_settings_changed)
        
        self._model.detection_timeout_changed.connect(self._on_detection_settings_changed)
        self._model.detection_interval_changed.connect(self._on_detection_settings_changed)
        self._model.enable_detection_changed.connect(self._on_detection_settings_changed)
        
        # 通用设置变化信号
        self._connect_settings_signals()
    
    def _connect_settings_signals(self):
        """连接设置变化信号"""
        self._model.game_path_changed.connect(
            lambda value: self.settings_changed.emit("game", "game_path", value)
        )
        self._model.resolution_changed.connect(
            lambda value: self.settings_changed.emit("game", "resolution", value)
        )
        self._model.window_title_changed.connect(
            lambda value: self.settings_changed.emit("game", "window_title", value)
        )
        self._model.window_mode_changed.connect(
            lambda value: self.settings_changed.emit("game", "window_mode", value)
        )
        self._model.ui_scale_changed.connect(
            lambda value: self.settings_changed.emit("game", "ui_scale", value)
        )
        self._model.always_on_top_changed.connect(
            lambda value: self.settings_changed.emit("game", "always_on_top", value)
        )
        self._model.auto_focus_changed.connect(
            lambda value: self.settings_changed.emit("game", "auto_focus", value)
        )
        self._model.detection_timeout_changed.connect(
            lambda value: self.settings_changed.emit("game", "detection_timeout", value)
        )
        self._model.detection_interval_changed.connect(
            lambda value: self.settings_changed.emit("game", "detection_interval", value)
        )
        self._model.enable_detection_changed.connect(
            lambda value: self.settings_changed.emit("game", "enable_detection", value)
        )
    
    def _on_window_settings_changed(self):
        """窗口设置变化处理"""
        window_settings = {
            "window_title": self._model.window_title,
            "window_mode": self._model.window_mode,
            "always_on_top": self._model.always_on_top,
            "auto_focus": self._model.auto_focus,
        }
        self.window_settings_updated.emit(window_settings)
    
    def _on_detection_settings_changed(self):
        """检测设置变化处理"""
        detection_settings = {
            "detection_timeout": self._model.detection_timeout,
            "detection_interval": self._model.detection_interval,
            "enable_detection": self._model.enable_detection,
        }
        self.detection_settings_updated.emit(detection_settings)
    
    # 属性访问器
    @property
    def model(self) -> GameSettingsModel:
        """获取Model"""
        return self._model
    
    @property
    def view(self) -> GameSettingsView:
        """获取View"""
        return self._view
    
    @property
    def presenter(self) -> GameSettingsPresenter:
        """获取Presenter"""
        return self._presenter
    
    @property
    def widget(self) -> GameSettingsView:
        """获取Widget（View的别名）"""
        return self._view
    
    # 公共接口
    def show(self):
        """显示组件"""
        self._view.show()
    
    def hide(self):
        """隐藏组件"""
        self._view.hide()
    
    def set_visible(self, visible: bool):
        """设置可见性"""
        self._view.setVisible(visible)
    
    def set_enabled(self, enabled: bool):
        """设置启用状态"""
        self._presenter.set_enabled(enabled)
    
    # 设置操作
    def load_settings(self):
        """加载设置"""
        self._presenter.load_settings()
    
    def get_current_settings(self) -> Dict[str, Any]:
        """获取当前设置"""
        return self._presenter.get_current_settings()
    
    def set_game_path(self, path: str):
        """设置游戏路径"""
        self._presenter.set_game_path(path)
    
    def set_resolution(self, resolution: str):
        """设置分辨率"""
        self._presenter.set_resolution(resolution)
    
    def set_window_title(self, title: str):
        """设置窗口标题"""
        self._presenter.set_window_title(title)
    
    def set_window_mode(self, mode: str):
        """设置窗口模式"""
        self._presenter.set_window_mode(mode)
    
    def set_ui_scale(self, scale: str):
        """设置界面缩放"""
        self._presenter.set_ui_scale(scale)
    
    def set_always_on_top(self, enabled: bool):
        """设置置顶状态"""
        self._presenter.set_always_on_top(enabled)
    
    def set_auto_focus(self, enabled: bool):
        """设置自动聚焦"""
        self._presenter.set_auto_focus(enabled)
    
    def set_detection_timeout(self, timeout: int):
        """设置检测超时"""
        self._presenter.set_detection_timeout(timeout)
    
    def set_detection_interval(self, interval: int):
        """设置检测间隔"""
        self._presenter.set_detection_interval(interval)
    
    def set_enable_detection(self, enabled: bool):
        """设置启用检测"""
        self._presenter.set_enable_detection(enabled)
    
    # 操作方法
    def validate_settings(self) -> tuple[bool, str]:
        """验证设置"""
        return self._presenter.validate_settings()
    
    def reset_to_defaults(self):
        """重置为默认设置"""
        try:
            self._presenter.reset_to_defaults()
            self.settings_reset.emit()
            logger.info("游戏设置重置完成")
        except Exception as e:
            logger.error(f"重置设置失败: {e}")
    
    def apply_settings(self) -> bool:
        """应用设置"""
        try:
            success = self._presenter.apply_settings()
            self.settings_applied.emit(success)
            if success:
                logger.info("游戏设置应用成功")
            return success
        except Exception as e:
            logger.error(f"应用设置失败: {e}")
            self.settings_applied.emit(False)
            return False
    
    def test_game_connection(self) -> bool:
        """测试游戏连接"""
        try:
            success = self._presenter.test_game_connection()
            result_msg = "连接测试成功" if success else "连接测试失败"
            self.connection_test_result.emit(success, result_msg)
            return success
        except Exception as e:
            error_msg = f"连接测试失败: {e}"
            logger.error(error_msg)
            self.connection_test_result.emit(False, error_msg)
            return False
    
    def auto_detect_game_path(self) -> Optional[str]:
        """自动检测游戏路径"""
        return self._presenter.auto_detect_game_path()
    
    # 状态查询
    def get_game_path(self) -> str:
        """获取游戏路径"""
        return self._model.game_path
    
    def get_resolution(self) -> str:
        """获取分辨率"""
        return self._model.resolution
    
    def get_window_title(self) -> str:
        """获取窗口标题"""
        return self._model.window_title
    
    def get_window_mode(self) -> str:
        """获取窗口模式"""
        return self._model.window_mode
    
    def get_ui_scale(self) -> str:
        """获取界面缩放"""
        return self._model.ui_scale
    
    def is_always_on_top(self) -> bool:
        """是否置顶"""
        return self._model.always_on_top
    
    def is_auto_focus(self) -> bool:
        """是否自动聚焦"""
        return self._model.auto_focus
    
    def get_detection_timeout(self) -> int:
        """获取检测超时"""
        return self._model.detection_timeout
    
    def get_detection_interval(self) -> int:
        """获取检测间隔"""
        return self._model.detection_interval
    
    def is_detection_enabled(self) -> bool:
        """是否启用检测"""
        return self._model.enable_detection
    
    def get_window_settings(self) -> Dict[str, Any]:
        """获取窗口设置"""
        return {
            "window_title": self._model.window_title,
            "window_mode": self._model.window_mode,
            "always_on_top": self._model.always_on_top,
            "auto_focus": self._model.auto_focus,
        }
    
    def get_detection_settings(self) -> Dict[str, Any]:
        """获取检测设置"""
        return {
            "detection_timeout": self._model.detection_timeout,
            "detection_interval": self._model.detection_interval,
            "enable_detection": self._model.enable_detection,
        }
    
    def get_display_settings(self) -> Dict[str, Any]:
        """获取显示设置"""
        return {
            "resolution": self._model.resolution,
            "ui_scale": self._model.ui_scale,
        }
    
    # 外部接口兼容性
    def get_widget(self) -> GameSettingsView:
        """获取Widget（兼容性接口）"""
        return self._view
    
    def get_settings_widget(self) -> GameSettingsView:
        """获取设置Widget（兼容性接口）"""
        return self._view
    
    # 批量设置
    def set_settings(self, settings: Dict[str, Any]):
        """批量设置"""
        try:
            for key, value in settings.items():
                if key == "game_path":
                    self.set_game_path(value)
                elif key == "resolution":
                    self.set_resolution(value)
                elif key == "window_title":
                    self.set_window_title(value)
                elif key == "window_mode":
                    self.set_window_mode(value)
                elif key == "ui_scale":
                    self.set_ui_scale(value)
                elif key == "always_on_top":
                    self.set_always_on_top(value)
                elif key == "auto_focus":
                    self.set_auto_focus(value)
                elif key == "detection_timeout":
                    self.set_detection_timeout(value)
                elif key == "detection_interval":
                    self.set_detection_interval(value)
                elif key == "enable_detection":
                    self.set_enable_detection(value)
                else:
                    logger.warning(f"未知设置项: {key}")
            
            logger.info("批量设置完成")
            
        except Exception as e:
            logger.error(f"批量设置失败: {e}")
    
    def cleanup(self):
        """清理资源"""
        try:
            self._presenter.cleanup()
            logger.info("游戏设置MVP组合清理完成")
        except Exception as e:
            logger.error(f"清理资源失败: {e}")