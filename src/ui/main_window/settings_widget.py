"""设置界面组件.

提供配置项的编辑和管理功能。
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QSpinBox, QCheckBox, 
    QPushButton, QScrollArea, QGroupBox, QComboBox
)
from PyQt6.QtCore import pyqtSignal
from src.core.service_locator import get_service
from src.core.config_manager import ConfigManager


class SettingsWidget(QWidget):
    """设置界面组件."""
    
    # 信号定义
    config_changed = pyqtSignal(str, object)  # 配置项改变信号
    
    def __init__(self, parent=None):
        """初始化设置界面.
        
        Args:
            parent: 父组件
        """
        super().__init__(parent)
        self.config_manager = get_service(ConfigManager)
        self.setup_ui()
        self.load_config()
        
    def setup_ui(self):
        """设置界面布局."""
        layout = QVBoxLayout(self)
        
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # 游戏设置组
        game_group = self.create_game_settings_group()
        scroll_layout.addWidget(game_group)
        
        # UI设置组
        ui_group = self.create_ui_settings_group()
        scroll_layout.addWidget(ui_group)
        
        # 自动化设置组
        automation_group = self.create_automation_settings_group()
        scroll_layout.addWidget(automation_group)
        
        # 日志设置组
        logging_group = self.create_logging_settings_group()
        scroll_layout.addWidget(logging_group)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        self.save_button = QPushButton("保存设置")
        self.reset_button = QPushButton("重置默认")
        self.reload_button = QPushButton("重新加载")
        
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.reset_button)
        button_layout.addWidget(self.reload_button)
        button_layout.addStretch()
        
        scroll_layout.addLayout(button_layout)
        
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)
        
        # 连接信号
        self.save_button.clicked.connect(self.save_config)
        self.reset_button.clicked.connect(self.reset_config)
        self.reload_button.clicked.connect(self.load_config)
        
    def create_game_settings_group(self):
        """创建游戏设置组."""
        group = QGroupBox("游戏设置")
        layout = QFormLayout(group)
        
        # 游戏路径
        self.game_path_edit = QLineEdit()
        layout.addRow("游戏路径:", self.game_path_edit)
        
        # 游戏分辨率
        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems(["1920x1080", "1366x768", "1280x720", "自定义"])
        layout.addRow("游戏分辨率:", self.resolution_combo)
        
        # 自动检测游戏
        self.auto_detect_game = QCheckBox("自动检测游戏窗口")
        layout.addRow(self.auto_detect_game)
        
        return group
        
    def create_ui_settings_group(self):
        """创建UI设置组."""
        group = QGroupBox("界面设置")
        layout = QFormLayout(group)
        
        # 主题
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["浅色", "深色", "自动"])
        layout.addRow("主题:", self.theme_combo)
        
        # 语言
        self.language_combo = QComboBox()
        self.language_combo.addItems(["中文", "English"])
        layout.addRow("语言:", self.language_combo)
        
        # 窗口置顶
        self.always_on_top = QCheckBox("窗口置顶")
        layout.addRow(self.always_on_top)
        
        # 最小化到托盘
        self.minimize_to_tray = QCheckBox("最小化到系统托盘")
        layout.addRow(self.minimize_to_tray)
        
        return group
        
    def create_automation_settings_group(self):
        """创建自动化设置组."""
        group = QGroupBox("自动化设置")
        layout = QFormLayout(group)
        
        # 自动执行间隔
        self.auto_interval_spin = QSpinBox()
        self.auto_interval_spin.setRange(1, 3600)
        self.auto_interval_spin.setSuffix(" 秒")
        layout.addRow("执行间隔:", self.auto_interval_spin)
        
        # 错误重试次数
        self.retry_count_spin = QSpinBox()
        self.retry_count_spin.setRange(0, 10)
        layout.addRow("错误重试次数:", self.retry_count_spin)
        
        # 启用通知
        self.enable_notifications = QCheckBox("启用任务完成通知")
        layout.addRow(self.enable_notifications)
        
        return group
        
    def create_logging_settings_group(self):
        """创建日志设置组."""
        group = QGroupBox("日志设置")
        layout = QFormLayout(group)
        
        # 日志级别
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        layout.addRow("日志级别:", self.log_level_combo)
        
        # 日志文件大小限制
        self.log_size_spin = QSpinBox()
        self.log_size_spin.setRange(1, 100)
        self.log_size_spin.setSuffix(" MB")
        layout.addRow("日志文件大小限制:", self.log_size_spin)
        
        # 保留日志文件数量
        self.log_files_spin = QSpinBox()
        self.log_files_spin.setRange(1, 50)
        layout.addRow("保留日志文件数量:", self.log_files_spin)
        
        return group
        
    def load_config(self):
        """加载配置到界面."""
        if not self.config_manager:
            return
            
        # 游戏设置
        self.game_path_edit.setText(self.config_manager.get("game_path", ""))
        resolution = self.config_manager.get("game_resolution", "1920x1080")
        index = self.resolution_combo.findText(resolution)
        if index >= 0:
            self.resolution_combo.setCurrentIndex(index)
        self.auto_detect_game.setChecked(self.config_manager.get("auto_detect_game", True))
        
        # UI设置
        theme = self.config_manager.get("ui_theme", "浅色")
        index = self.theme_combo.findText(theme)
        if index >= 0:
            self.theme_combo.setCurrentIndex(index)
        language = self.config_manager.get("ui_language", "中文")
        index = self.language_combo.findText(language)
        if index >= 0:
            self.language_combo.setCurrentIndex(index)
        self.always_on_top.setChecked(self.config_manager.get("always_on_top", False))
        self.minimize_to_tray.setChecked(self.config_manager.get("minimize_to_tray", True))
        
        # 自动化设置
        self.auto_interval_spin.setValue(self.config_manager.get("auto_interval", 30))
        self.retry_count_spin.setValue(self.config_manager.get("retry_count", 3))
        self.enable_notifications.setChecked(self.config_manager.get("enable_notifications", True))
        
        # 日志设置
        log_level = self.config_manager.get("log_level", "INFO")
        index = self.log_level_combo.findText(log_level)
        if index >= 0:
            self.log_level_combo.setCurrentIndex(index)
        self.log_size_spin.setValue(self.config_manager.get("log_size_mb", 10))
        self.log_files_spin.setValue(self.config_manager.get("log_files_count", 5))
        
    def save_config(self):
        """保存配置."""
        if not self.config_manager:
            return
            
        try:
            # 游戏设置
            self.config_manager.set("game_path", self.game_path_edit.text())
            self.config_manager.set("game_resolution", self.resolution_combo.currentText())
            self.config_manager.set("auto_detect_game", self.auto_detect_game.isChecked())
            
            # UI设置
            self.config_manager.set("ui_theme", self.theme_combo.currentText())
            self.config_manager.set("ui_language", self.language_combo.currentText())
            self.config_manager.set("always_on_top", self.always_on_top.isChecked())
            self.config_manager.set("minimize_to_tray", self.minimize_to_tray.isChecked())
            
            # 自动化设置
            self.config_manager.set("auto_interval", self.auto_interval_spin.value())
            self.config_manager.set("retry_count", self.retry_count_spin.value())
            self.config_manager.set("enable_notifications", self.enable_notifications.isChecked())
            
            # 日志设置
            self.config_manager.set("log_level", self.log_level_combo.currentText())
            self.config_manager.set("log_size_mb", self.log_size_spin.value())
            self.config_manager.set("log_files_count", self.log_files_spin.value())
            
            # 保存到文件
            self.config_manager.save()
            
            QMessageBox.information(self, "成功", "配置已保存")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存配置失败: {str(e)}")
            
    def reset_config(self):
        """重置为默认配置."""
        reply = QMessageBox.question(
            self, "确认", "确定要重置为默认配置吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 重置为默认值
            self.game_path_edit.setText("")
            self.resolution_combo.setCurrentText("1920x1080")
            self.auto_detect_game.setChecked(True)
            
            self.theme_combo.setCurrentText("浅色")
            self.language_combo.setCurrentText("中文")
            self.always_on_top.setChecked(False)
            self.minimize_to_tray.setChecked(True)
            
            self.auto_interval_spin.setValue(30)
            self.retry_count_spin.setValue(3)
            self.enable_notifications.setChecked(True)
            
            self.log_level_combo.setCurrentText("INFO")
            self.log_size_spin.setValue(10)
            self.log_files_spin.setValue(5)