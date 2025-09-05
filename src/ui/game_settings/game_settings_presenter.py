"""游戏设置展示器层

该模块定义了游戏设置的Presenter层，负责协调Model和View，处理用户交互和业务逻辑。
"""

from typing import Dict, Any, Optional
from PyQt6.QtCore import QObject, QTimer

from .game_settings_model import GameSettingsModel
from .game_settings_view import GameSettingsView
from src.utils.logger import logger


class GameSettingsPresenter(QObject):
    """游戏设置展示器类
    
    负责协调Model和View，处理用户交互和业务逻辑。
    """
    
    def __init__(self, model: GameSettingsModel, view: GameSettingsView, parent=None):
        super().__init__(parent)
        self.model = model
        self.view = view
        
        # 连接信号
        self._connect_view_signals()
        self._connect_model_signals()
        
        # 初始化数据
        self._init_data()
        
        logger.info("游戏设置展示器初始化完成")
    
    def _connect_view_signals(self):
        """连接View信号"""
        # 路径相关
        self.view.game_path_changed.connect(self.model.set_game_path)
        self.view.browse_path_requested.connect(self._on_browse_path_requested)
        self.view.auto_detect_requested.connect(self._on_auto_detect_requested)
        
        # 显示设置
        self.view.resolution_changed.connect(self.model.set_resolution)
        self.view.custom_resolution_changed.connect(self._on_custom_resolution_changed)
        self.view.ui_scale_changed.connect(self.model.set_ui_scale)
        
        # 窗口设置
        self.view.window_title_changed.connect(self.model.set_window_title)
        self.view.window_mode_changed.connect(self.model.set_window_mode)
        self.view.always_on_top_changed.connect(self.model.set_always_on_top)
        self.view.auto_focus_changed.connect(self.model.set_auto_focus)
        
        # 检测设置
        self.view.detection_timeout_changed.connect(self.model.set_detection_timeout)
        self.view.detection_interval_changed.connect(self.model.set_detection_interval)
        self.view.enable_detection_changed.connect(self.model.set_enable_detection)
        
        # 操作
        self.view.test_connection_requested.connect(self._on_test_connection_requested)
        self.view.reset_settings_requested.connect(self._on_reset_settings_requested)
        self.view.apply_settings_requested.connect(self._on_apply_settings_requested)
    
    def _connect_model_signals(self):
        """连接Model信号"""
        # 数据变化信号
        self.model.game_path_changed.connect(self.view.update_game_path)
        self.model.resolution_changed.connect(self.view.update_resolution)
        self.model.window_title_changed.connect(self.view.update_window_title)
        self.model.window_mode_changed.connect(self.view.update_window_mode)
        self.model.ui_scale_changed.connect(self.view.update_ui_scale)
        self.model.always_on_top_changed.connect(self.view.update_always_on_top)
        self.model.auto_focus_changed.connect(self.view.update_auto_focus)
        self.model.detection_timeout_changed.connect(self.view.update_detection_timeout)
        self.model.detection_interval_changed.connect(self.view.update_detection_interval)
        self.model.enable_detection_changed.connect(self.view.update_enable_detection)
        
        # 状态信号
        self.model.path_status_changed.connect(self.view.update_path_status)
        self.model.settings_validated.connect(self._on_settings_validated)
        
        # 错误信号
        self.model.error_occurred.connect(self._on_error_occurred)
    
    def _init_data(self):
        """初始化数据"""
        # 设置选项
        self.view.set_resolution_options(self.model.supported_resolutions)
        self.view.set_window_mode_options(self.model.window_modes)
        self.view.set_ui_scale_options(self.model.ui_scales)
        
        # 加载设置
        self.model.load_settings()
    
    # View信号处理方法
    def _on_browse_path_requested(self):
        """处理浏览路径请求"""
        try:
            file_path = self.view.show_file_dialog()
            if file_path:
                self.model.set_game_path(file_path)
                logger.info(f"用户选择游戏路径: {file_path}")
        except Exception as e:
            logger.error(f"浏览路径失败: {e}")
            self.view.show_message("错误", f"浏览路径失败：{str(e)}", "error")
    
    def _on_auto_detect_requested(self):
        """处理自动检测请求"""
        try:
            detected_path = self.model.auto_detect_game_path()
            if detected_path:
                self.view.show_message(
                    "检测成功", 
                    f"已检测到游戏路径：\n{detected_path}", 
                    "info"
                )
                logger.info(f"自动检测成功: {detected_path}")
            else:
                self.view.show_message(
                    "检测失败", 
                    "未能自动检测到游戏路径，请手动选择。", 
                    "info"
                )
                logger.info("自动检测失败")
        except Exception as e:
            logger.error(f"自动检测失败: {e}")
            self.view.show_message("错误", f"自动检测失败：{str(e)}", "error")
    
    def _on_custom_resolution_changed(self, width: int, height: int):
        """处理自定义分辨率变化"""
        try:
            resolution = f"{width}x{height}"
            self.model.set_resolution(resolution)
            logger.debug(f"自定义分辨率设置为: {resolution}")
        except Exception as e:
            logger.error(f"设置自定义分辨率失败: {e}")
    
    def _on_test_connection_requested(self):
        """处理测试连接请求"""
        try:
            self.view.set_loading_state(True)
            
            # 延迟执行测试，避免阻塞UI
            QTimer.singleShot(100, self._do_test_connection)
            
        except Exception as e:
            self.view.set_loading_state(False)
            logger.error(f"测试连接失败: {e}")
            self.view.show_message("错误", f"测试连接失败：{str(e)}", "error")
    
    def _do_test_connection(self):
        """执行测试连接"""
        try:
            success = self.model.test_game_connection()
            
            if success:
                self.view.show_message(
                    "测试结果", 
                    "游戏连接测试成功！\n\n检测到游戏窗口配置正常。", 
                    "info"
                )
                logger.info("游戏连接测试成功")
            
        except Exception as e:
            logger.error(f"执行测试连接失败: {e}")
            self.view.show_message("错误", f"测试连接失败：{str(e)}", "error")
        finally:
            self.view.set_loading_state(False)
    
    def _on_reset_settings_requested(self):
        """处理重置设置请求"""
        try:
            # 确认重置
            if self.view.show_confirmation(
                "确认重置", 
                "确定要重置所有游戏设置为默认值吗？\n\n此操作不可撤销。"
            ):
                self.model.reset_to_defaults()
                self.view.show_message("重置完成", "游戏设置已重置为默认值", "info")
                logger.info("用户重置游戏设置")
            
        except Exception as e:
            logger.error(f"重置设置失败: {e}")
            self.view.show_message("错误", f"重置设置失败：{str(e)}", "error")
    
    def _on_apply_settings_requested(self):
        """处理应用设置请求"""
        try:
            self.view.set_loading_state(True)
            
            # 延迟执行应用，避免阻塞UI
            QTimer.singleShot(100, self._do_apply_settings)
            
        except Exception as e:
            self.view.set_loading_state(False)
            logger.error(f"应用设置失败: {e}")
            self.view.show_message("错误", f"应用设置失败：{str(e)}", "error")
    
    def _do_apply_settings(self):
        """执行应用设置"""
        try:
            success = self.model.apply_settings()
            
            if success:
                self.view.show_message("应用成功", "游戏设置已成功应用", "info")
                logger.info("游戏设置应用成功")
            
        except Exception as e:
            logger.error(f"执行应用设置失败: {e}")
            self.view.show_message("错误", f"应用设置失败：{str(e)}", "error")
        finally:
            self.view.set_loading_state(False)
    
    # Model信号处理方法
    def _on_settings_validated(self, is_valid: bool, error_msg: str):
        """处理设置验证结果"""
        if not is_valid and error_msg:
            self.view.show_message("验证失败", error_msg, "warning")
    
    def _on_error_occurred(self, error_msg: str):
        """处理Model错误"""
        self.view.show_message("错误", error_msg, "error")
        logger.error(f"Model错误: {error_msg}")
    
    # 公共接口
    def load_settings(self):
        """加载设置"""
        try:
            self.model.load_settings()
            logger.info("加载游戏设置")
        except Exception as e:
            logger.error(f"加载设置失败: {e}")
            self.view.show_message("错误", f"加载设置失败：{str(e)}", "error")
    
    def get_current_settings(self) -> Dict[str, Any]:
        """获取当前设置"""
        return self.model.get_current_settings()
    
    def set_game_path(self, path: str):
        """设置游戏路径"""
        self.model.set_game_path(path)
    
    def set_resolution(self, resolution: str):
        """设置分辨率"""
        self.model.set_resolution(resolution)
    
    def set_window_title(self, title: str):
        """设置窗口标题"""
        self.model.set_window_title(title)
    
    def set_window_mode(self, mode: str):
        """设置窗口模式"""
        self.model.set_window_mode(mode)
    
    def set_ui_scale(self, scale: str):
        """设置界面缩放"""
        self.model.set_ui_scale(scale)
    
    def set_always_on_top(self, enabled: bool):
        """设置置顶状态"""
        self.model.set_always_on_top(enabled)
    
    def set_auto_focus(self, enabled: bool):
        """设置自动聚焦"""
        self.model.set_auto_focus(enabled)
    
    def set_detection_timeout(self, timeout: int):
        """设置检测超时"""
        self.model.set_detection_timeout(timeout)
    
    def set_detection_interval(self, interval: int):
        """设置检测间隔"""
        self.model.set_detection_interval(interval)
    
    def set_enable_detection(self, enabled: bool):
        """设置启用检测"""
        self.model.set_enable_detection(enabled)
    
    def validate_settings(self) -> tuple[bool, str]:
        """验证设置"""
        return self.model.validate_settings()
    
    def reset_to_defaults(self):
        """重置为默认设置"""
        try:
            if self.view.show_confirmation(
                "确认重置", 
                "确定要重置所有游戏设置为默认值吗？\n\n此操作不可撤销。"
            ):
                self.model.reset_to_defaults()
                logger.info("重置游戏设置")
        except Exception as e:
            logger.error(f"重置设置失败: {e}")
            self.view.show_message("错误", f"重置设置失败：{str(e)}", "error")
    
    def apply_settings(self) -> bool:
        """应用设置"""
        try:
            return self.model.apply_settings()
        except Exception as e:
            logger.error(f"应用设置失败: {e}")
            self.view.show_message("错误", f"应用设置失败：{str(e)}", "error")
            return False
    
    def test_game_connection(self) -> bool:
        """测试游戏连接"""
        try:
            return self.model.test_game_connection()
        except Exception as e:
            logger.error(f"测试连接失败: {e}")
            self.view.show_message("错误", f"测试连接失败：{str(e)}", "error")
            return False
    
    def auto_detect_game_path(self) -> Optional[str]:
        """自动检测游戏路径"""
        try:
            return self.model.auto_detect_game_path()
        except Exception as e:
            logger.error(f"自动检测失败: {e}")
            self.view.show_message("错误", f"自动检测失败：{str(e)}", "error")
            return None
    
    def set_enabled(self, enabled: bool):
        """设置启用状态"""
        self.view.set_enabled_state(enabled)
    
    def cleanup(self):
        """清理资源"""
        try:
            self.model.cleanup()
            self.view.cleanup()
            logger.info("游戏设置展示器清理完成")
        except Exception as e:
            logger.error(f"清理资源失败: {e}")