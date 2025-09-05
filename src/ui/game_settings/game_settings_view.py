"""游戏设置视图层

该模块定义了游戏设置的View层，负责UI界面的展示和用户交互。
"""

from typing import Dict, Any, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
    QLabel, QLineEdit, QPushButton, QComboBox, QSpinBox, QCheckBox,
    QFileDialog, QMessageBox, QFrame
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont

from src.ui.base.settings_widget import SettingsWidget
from src.utils.logger import logger


class GameSettingsView(SettingsWidget):
    """游戏设置视图类
    
    负责游戏设置界面的展示和用户交互。
    """
    
    # 用户交互信号
    game_path_changed = pyqtSignal(str)  # 游戏路径变化
    browse_path_requested = pyqtSignal()  # 请求浏览路径
    auto_detect_requested = pyqtSignal()  # 请求自动检测
    resolution_changed = pyqtSignal(str)  # 分辨率变化
    custom_resolution_changed = pyqtSignal(int, int)  # 自定义分辨率变化
    window_title_changed = pyqtSignal(str)  # 窗口标题变化
    window_mode_changed = pyqtSignal(str)  # 窗口模式变化
    ui_scale_changed = pyqtSignal(str)  # 界面缩放变化
    always_on_top_changed = pyqtSignal(bool)  # 置顶状态变化
    auto_focus_changed = pyqtSignal(bool)  # 自动聚焦变化
    detection_timeout_changed = pyqtSignal(int)  # 检测超时变化
    detection_interval_changed = pyqtSignal(int)  # 检测间隔变化
    enable_detection_changed = pyqtSignal(bool)  # 启用检测变化
    
    # 操作信号
    test_connection_requested = pyqtSignal()  # 请求测试连接
    reset_settings_requested = pyqtSignal()  # 请求重置设置
    apply_settings_requested = pyqtSignal()  # 请求应用设置
    
    def __init__(self, parent=None):
        super().__init__("游戏设置", parent)
        
        # UI组件
        self.game_path_edit = None
        self.path_status_label = None
        self.browse_button = None
        self.auto_detect_button = None
        self.resolution_combo = None
        self.custom_width_spin = None
        self.custom_height_spin = None
        self.window_title_edit = None
        self.window_mode_combo = None
        self.scale_combo = None
        self.always_on_top_check = None
        self.auto_focus_check = None
        self.detection_timeout_spin = None
        self.detection_interval_spin = None
        self.enable_detection_check = None
        self.test_button = None
        self.reset_button = None
        self.apply_button = None
        
        # 初始化UI
        self._init_ui()
        self._connect_signals()
        
        logger.info("游戏设置视图初始化完成")
    
    def _init_ui(self):
        """初始化UI界面"""
        layout = QVBoxLayout(self.content_widget)
        layout_spacing = self._get_config_value('ui.game_settings.layout_spacing', 15)
        layout.setSpacing(layout_spacing)
        
        # 创建各个设置组
        layout.addWidget(self._create_path_group())
        layout.addWidget(self._create_display_group())
        layout.addWidget(self._create_window_group())
        layout.addWidget(self._create_detection_group())
        layout.addWidget(self._create_button_layout())
        
        layout.addStretch()
    
    def _create_path_group(self) -> QGroupBox:
        """创建游戏路径设置组"""
        group = QGroupBox("游戏路径")
        layout = QVBoxLayout(group)
        
        # 路径输入
        path_layout = QHBoxLayout()
        self.game_path_edit = QLineEdit()
        self.game_path_edit.setPlaceholderText("请选择游戏可执行文件路径...")
        
        self.browse_button = QPushButton("浏览")
        self.browse_button.setFixedWidth(80)
        
        self.auto_detect_button = QPushButton("自动检测")
        self.auto_detect_button.setFixedWidth(80)
        
        path_layout.addWidget(self.game_path_edit)
        path_layout.addWidget(self.browse_button)
        path_layout.addWidget(self.auto_detect_button)
        
        # 路径状态
        self.path_status_label = QLabel("未设置游戏路径")
        self.path_status_label.setStyleSheet("color: #ff6b6b; font-size: 11px;")
        
        layout.addLayout(path_layout)
        layout.addWidget(self.path_status_label)
        
        return group
    
    def _create_display_group(self) -> QGroupBox:
        """创建显示设置组"""
        group = QGroupBox("显示设置")
        layout = QGridLayout(group)
        
        # 分辨率设置
        layout.addWidget(QLabel("分辨率:"), 0, 0)
        self.resolution_combo = QComboBox()
        layout.addWidget(self.resolution_combo, 0, 1)
        
        # 自定义分辨率
        layout.addWidget(QLabel("自定义分辨率:"), 1, 0)
        custom_layout = QHBoxLayout()
        
        self.custom_width_spin = QSpinBox()
        custom_width_min = self._get_config_value('ui.game_settings.custom_width_min', 800)
        custom_width_max = self._get_config_value('ui.game_settings.custom_width_max', 7680)
        custom_width_default = self._get_config_value('ui.game_settings.custom_width_default', 1920)
        self.custom_width_spin.setRange(custom_width_min, custom_width_max)
        self.custom_width_spin.setValue(custom_width_default)
        self.custom_width_spin.setSuffix(" px")
        self.custom_width_spin.setEnabled(False)
        
        custom_layout.addWidget(self.custom_width_spin)
        custom_layout.addWidget(QLabel("×"))
        
        self.custom_height_spin = QSpinBox()
        custom_height_min = self._get_config_value('ui.game_settings.custom_height_min', 600)
        custom_height_max = self._get_config_value('ui.game_settings.custom_height_max', 4320)
        custom_height_default = self._get_config_value('ui.game_settings.custom_height_default', 1080)
        self.custom_height_spin.setRange(custom_height_min, custom_height_max)
        self.custom_height_spin.setValue(custom_height_default)
        self.custom_height_spin.setSuffix(" px")
        self.custom_height_spin.setEnabled(False)
        
        custom_layout.addWidget(self.custom_height_spin)
        custom_layout.addStretch()
        
        layout.addLayout(custom_layout, 1, 1)
        
        # 界面缩放
        layout.addWidget(QLabel("界面缩放:"), 2, 0)
        self.scale_combo = QComboBox()
        layout.addWidget(self.scale_combo, 2, 1)
        
        return group
    
    def _create_window_group(self) -> QGroupBox:
        """创建窗口设置组"""
        group = QGroupBox("窗口设置")
        layout = QGridLayout(group)
        
        # 窗口标题
        layout.addWidget(QLabel("窗口标题:"), 0, 0)
        self.window_title_edit = QLineEdit()
        self.window_title_edit.setPlaceholderText("游戏窗口标题...")
        layout.addWidget(self.window_title_edit, 0, 1)
        
        # 窗口模式
        layout.addWidget(QLabel("窗口模式:"), 1, 0)
        self.window_mode_combo = QComboBox()
        layout.addWidget(self.window_mode_combo, 1, 1)
        
        # 窗口选项
        options_layout = QVBoxLayout()
        
        self.always_on_top_check = QCheckBox("窗口置顶")
        self.auto_focus_check = QCheckBox("自动聚焦到游戏窗口")
        
        options_layout.addWidget(self.always_on_top_check)
        options_layout.addWidget(self.auto_focus_check)
        
        layout.addWidget(QLabel("窗口选项:"), 2, 0)
        layout.addLayout(options_layout, 2, 1)
        
        return group
    
    def _create_detection_group(self) -> QGroupBox:
        """创建检测设置组"""
        group = QGroupBox("检测设置")
        layout = QGridLayout(group)
        
        # 启用检测
        self.enable_detection_check = QCheckBox("启用游戏窗口检测")
        layout.addWidget(self.enable_detection_check, 0, 0, 1, 2)
        
        # 检测超时
        layout.addWidget(QLabel("检测超时:"), 1, 0)
        self.detection_timeout_spin = QSpinBox()
        detection_timeout_min = self._get_config_value('ui.game_settings.detection_timeout_min', 5)
        detection_timeout_max = self._get_config_value('ui.game_settings.detection_timeout_max', 300)
        detection_timeout_default = self._get_config_value('ui.game_settings.detection_timeout_default', 30)
        self.detection_timeout_spin.setRange(detection_timeout_min, detection_timeout_max)
        self.detection_timeout_spin.setValue(detection_timeout_default)
        self.detection_timeout_spin.setSuffix(" 秒")
        layout.addWidget(self.detection_timeout_spin, 1, 1)
        
        # 检测间隔
        layout.addWidget(QLabel("检测间隔:"), 2, 0)
        self.detection_interval_spin = QSpinBox()
        detection_interval_min = self._get_config_value('ui.game_settings.detection_interval_min', 1)
        detection_interval_max = self._get_config_value('ui.game_settings.detection_interval_max', 10)
        detection_interval_default = self._get_config_value('ui.game_settings.detection_interval_default', 1)
        self.detection_interval_spin.setRange(detection_interval_min, detection_interval_max)
        self.detection_interval_spin.setValue(detection_interval_default)
        self.detection_interval_spin.setSuffix(" 秒")
        layout.addWidget(self.detection_interval_spin, 2, 1)
        
        return group
    
    def _create_button_layout(self) -> QWidget:
        """创建按钮布局"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        
        self.test_button = QPushButton("测试游戏连接")
        self.reset_button = QPushButton("重置为默认")
        self.apply_button = QPushButton("应用设置")
        
        # 设置按钮样式
        self.test_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        
        self.apply_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        
        layout.addWidget(self.test_button)
        layout.addStretch()
        layout.addWidget(self.reset_button)
        layout.addWidget(self.apply_button)
        
        return widget
    
    def _connect_signals(self):
        """连接信号与槽"""
        # 路径相关
        self.game_path_edit.textChanged.connect(self.game_path_changed.emit)
        self.browse_button.clicked.connect(self.browse_path_requested.emit)
        self.auto_detect_button.clicked.connect(self.auto_detect_requested.emit)
        
        # 显示设置
        self.resolution_combo.currentTextChanged.connect(self._on_resolution_changed)
        self.custom_width_spin.valueChanged.connect(self._on_custom_resolution_changed)
        self.custom_height_spin.valueChanged.connect(self._on_custom_resolution_changed)
        self.scale_combo.currentTextChanged.connect(self.ui_scale_changed.emit)
        
        # 窗口设置
        self.window_title_edit.textChanged.connect(self.window_title_changed.emit)
        self.window_mode_combo.currentTextChanged.connect(self.window_mode_changed.emit)
        self.always_on_top_check.toggled.connect(self.always_on_top_changed.emit)
        self.auto_focus_check.toggled.connect(self.auto_focus_changed.emit)
        
        # 检测设置
        self.detection_timeout_spin.valueChanged.connect(self.detection_timeout_changed.emit)
        self.detection_interval_spin.valueChanged.connect(self.detection_interval_changed.emit)
        self.enable_detection_check.toggled.connect(self.enable_detection_changed.emit)
        
        # 按钮
        self.test_button.clicked.connect(self.test_connection_requested.emit)
        self.reset_button.clicked.connect(self.reset_settings_requested.emit)
        self.apply_button.clicked.connect(self.apply_settings_requested.emit)
    
    def _on_resolution_changed(self, resolution: str):
        """分辨率改变处理"""
        is_custom = resolution == "自定义"
        self.custom_width_spin.setEnabled(is_custom)
        self.custom_height_spin.setEnabled(is_custom)
        
        if is_custom:
            self._on_custom_resolution_changed()
        else:
            self.resolution_changed.emit(resolution)
    
    def _on_custom_resolution_changed(self):
        """自定义分辨率改变处理"""
        if self.resolution_combo.currentText() == "自定义":
            width = self.custom_width_spin.value()
            height = self.custom_height_spin.value()
            self.custom_resolution_changed.emit(width, height)
    
    # 数据更新方法
    def update_game_path(self, path: str):
        """更新游戏路径"""
        if self.game_path_edit.text() != path:
            self.game_path_edit.setText(path)
    
    def update_path_status(self, text: str, style: str):
        """更新路径状态"""
        self.path_status_label.setText(text)
        self.path_status_label.setStyleSheet(style)
    
    def update_resolution(self, resolution: str):
        """更新分辨率"""
        index = self.resolution_combo.findText(resolution)
        if index >= 0:
            self.resolution_combo.setCurrentIndex(index)
        elif "x" in resolution:
            # 自定义分辨率
            custom_index = self.resolution_combo.findText("自定义")
            if custom_index >= 0:
                self.resolution_combo.setCurrentIndex(custom_index)
                try:
                    width, height = map(int, resolution.split("x"))
                    self.custom_width_spin.setValue(width)
                    self.custom_height_spin.setValue(height)
                except ValueError:
                    pass
    
    def update_window_title(self, title: str):
        """更新窗口标题"""
        if self.window_title_edit.text() != title:
            self.window_title_edit.setText(title)
    
    def update_window_mode(self, mode: str):
        """更新窗口模式"""
        index = self.window_mode_combo.findText(mode)
        if index >= 0:
            self.window_mode_combo.setCurrentIndex(index)
    
    def update_ui_scale(self, scale: str):
        """更新界面缩放"""
        index = self.scale_combo.findText(scale)
        if index >= 0:
            self.scale_combo.setCurrentIndex(index)
    
    def update_always_on_top(self, enabled: bool):
        """更新置顶状态"""
        self.always_on_top_check.setChecked(enabled)
    
    def update_auto_focus(self, enabled: bool):
        """更新自动聚焦"""
        self.auto_focus_check.setChecked(enabled)
    
    def update_detection_timeout(self, timeout: int):
        """更新检测超时"""
        self.detection_timeout_spin.setValue(timeout)
    
    def update_detection_interval(self, interval: int):
        """更新检测间隔"""
        self.detection_interval_spin.setValue(interval)
    
    def update_enable_detection(self, enabled: bool):
        """更新启用检测"""
        self.enable_detection_check.setChecked(enabled)
    
    # 选项设置方法
    def set_resolution_options(self, resolutions: list):
        """设置分辨率选项"""
        self.resolution_combo.clear()
        self.resolution_combo.addItems(resolutions)
    
    def set_window_mode_options(self, modes: list):
        """设置窗口模式选项"""
        self.window_mode_combo.clear()
        self.window_mode_combo.addItems(modes)
    
    def set_ui_scale_options(self, scales: list):
        """设置界面缩放选项"""
        self.scale_combo.clear()
        self.scale_combo.addItems(scales)
    
    # 对话框方法
    def show_file_dialog(self) -> Optional[str]:
        """显示文件选择对话框"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择游戏可执行文件", "", "可执行文件 (*.exe);;所有文件 (*.*)"
        )
        return file_path if file_path else None
    
    def show_message(self, title: str, message: str, msg_type: str = "info"):
        """显示消息对话框"""
        if msg_type == "info":
            QMessageBox.information(self, title, message)
        elif msg_type == "warning":
            QMessageBox.warning(self, title, message)
        elif msg_type == "error":
            QMessageBox.critical(self, title, message)
    
    def show_confirmation(self, title: str, message: str) -> bool:
        """显示确认对话框"""
        reply = QMessageBox.question(
            self, title, message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        return reply == QMessageBox.StandardButton.Yes
    
    # 状态控制方法
    def set_loading_state(self, loading: bool):
        """设置加载状态"""
        self.setEnabled(not loading)
    
    def set_enabled_state(self, enabled: bool):
        """设置启用状态"""
        self.setEnabled(enabled)
    
    # 获取当前值方法
    def get_current_values(self) -> Dict[str, Any]:
        """获取当前界面值"""
        resolution = self.resolution_combo.currentText()
        if resolution == "自定义":
            width = self.custom_width_spin.value()
            height = self.custom_height_spin.value()
            resolution = f"{width}x{height}"
        
        return {
            "game_path": self.game_path_edit.text(),
            "resolution": resolution,
            "window_title": self.window_title_edit.text(),
            "window_mode": self.window_mode_combo.currentText(),
            "ui_scale": self.scale_combo.currentText(),
            "always_on_top": self.always_on_top_check.isChecked(),
            "auto_focus": self.auto_focus_check.isChecked(),
            "detection_timeout": self.detection_timeout_spin.value(),
            "detection_interval": self.detection_interval_spin.value(),
            "enable_detection": self.enable_detection_check.isChecked(),
        }
    
    def cleanup(self):
        """清理资源"""
        logger.info("游戏设置视图清理完成")