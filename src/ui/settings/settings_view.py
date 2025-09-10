"""设置界面视图模块.

提供应用程序设置的用户界面。
"""

from typing import Dict, Any, Optional
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QLineEdit, QSpinBox, QDoubleSpinBox,
    QCheckBox, QComboBox, QGroupBox, QTabWidget,
    QSlider, QTextEdit, QFileDialog, QMessageBox,
    QScrollArea, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
import json
import os


class GameSettingsWidget(QWidget):
    """游戏设置组件。"""
    
    def __init__(self, parent=None):
        """初始化游戏设置组件。"""
        super().__init__(parent)
        self._setup_ui()
        
    def _setup_ui(self):
        """设置用户界面。"""
        layout = QVBoxLayout(self)
        
        # 游戏路径设置
        game_group = QGroupBox("游戏设置")
        game_layout = QGridLayout(game_group)
        
        # 游戏路径
        game_layout.addWidget(QLabel("游戏路径:"), 0, 0)
        self.game_path_edit = QLineEdit()
        self.game_path_button = QPushButton("浏览")
        game_layout.addWidget(self.game_path_edit, 0, 1)
        game_layout.addWidget(self.game_path_button, 0, 2)
        
        # 游戏窗口设置
        game_layout.addWidget(QLabel("窗口模式:"), 1, 0)
        self.window_mode_combo = QComboBox()
        self.window_mode_combo.addItems(["全屏", "窗口化", "无边框窗口"])
        game_layout.addWidget(self.window_mode_combo, 1, 1, 1, 2)
        
        # 分辨率设置
        game_layout.addWidget(QLabel("分辨率:"), 2, 0)
        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems([
            "1920x1080", "1366x768", "1280x720", "1024x768", "自定义"
        ])
        game_layout.addWidget(self.resolution_combo, 2, 1, 1, 2)
        
        layout.addWidget(game_group)
        
        # 自动化设置
        automation_group = QGroupBox("自动化设置")
        automation_layout = QGridLayout(automation_group)
        
        # 操作延迟
        automation_layout.addWidget(QLabel("操作延迟(ms):"), 0, 0)
        self.operation_delay_spin = QSpinBox()
        self.operation_delay_spin.setRange(100, 5000)
        self.operation_delay_spin.setValue(500)
        automation_layout.addWidget(self.operation_delay_spin, 0, 1)
        
        # 重试次数
        automation_layout.addWidget(QLabel("重试次数:"), 1, 0)
        self.retry_count_spin = QSpinBox()
        self.retry_count_spin.setRange(1, 10)
        self.retry_count_spin.setValue(3)
        automation_layout.addWidget(self.retry_count_spin, 1, 1)
        
        # 超时时间
        automation_layout.addWidget(QLabel("超时时间(s):"), 2, 0)
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(5, 300)
        self.timeout_spin.setValue(30)
        automation_layout.addWidget(self.timeout_spin, 2, 1)
        
        # 启用日志
        self.enable_logging_check = QCheckBox("启用详细日志")
        automation_layout.addWidget(self.enable_logging_check, 3, 0, 1, 2)
        
        layout.addWidget(automation_group)
        
        # 连接信号
        self.game_path_button.clicked.connect(self._browse_game_path)
        
    def _browse_game_path(self):
        """浏览游戏路径。"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择游戏可执行文件", "", "可执行文件 (*.exe)"
        )
        if file_path:
            self.game_path_edit.setText(file_path)
            
    def get_settings(self) -> Dict[str, Any]:
        """获取设置数据。
        
        Returns:
            Dict[str, Any]: 设置数据字典
        """
        return {
            'game_path': self.game_path_edit.text(),
            'window_mode': self.window_mode_combo.currentText(),
            'resolution': self.resolution_combo.currentText(),
            'operation_delay': self.operation_delay_spin.value(),
            'retry_count': self.retry_count_spin.value(),
            'timeout': self.timeout_spin.value(),
            'enable_logging': self.enable_logging_check.isChecked()
        }
        
    def load_settings(self, settings: Dict[str, Any]):
        """加载设置数据。
        
        Args:
            settings: 设置数据字典
        """
        self.game_path_edit.setText(settings.get('game_path', ''))
        
        window_mode = settings.get('window_mode', '窗口化')
        index = self.window_mode_combo.findText(window_mode)
        if index >= 0:
            self.window_mode_combo.setCurrentIndex(index)
            
        resolution = settings.get('resolution', '1920x1080')
        index = self.resolution_combo.findText(resolution)
        if index >= 0:
            self.resolution_combo.setCurrentIndex(index)
            
        self.operation_delay_spin.setValue(settings.get('operation_delay', 500))
        self.retry_count_spin.setValue(settings.get('retry_count', 3))
        self.timeout_spin.setValue(settings.get('timeout', 30))
        self.enable_logging_check.setChecked(settings.get('enable_logging', False))


class PerformanceSettingsWidget(QWidget):
    """性能设置组件。"""
    
    def __init__(self, parent=None):
        """初始化性能设置组件。"""
        super().__init__(parent)
        self._setup_ui()
        
    def _setup_ui(self):
        """设置用户界面。"""
        layout = QVBoxLayout(self)
        
        # 性能设置
        performance_group = QGroupBox("性能设置")
        performance_layout = QGridLayout(performance_group)
        
        # CPU使用率限制
        performance_layout.addWidget(QLabel("CPU使用率限制(%):"), 0, 0)
        self.cpu_limit_slider = QSlider(Qt.Horizontal)
        self.cpu_limit_slider.setRange(10, 100)
        self.cpu_limit_slider.setValue(80)
        self.cpu_limit_label = QLabel("80%")
        performance_layout.addWidget(self.cpu_limit_slider, 0, 1)
        performance_layout.addWidget(self.cpu_limit_label, 0, 2)
        
        # 内存使用率限制
        performance_layout.addWidget(QLabel("内存使用率限制(%):"), 1, 0)
        self.memory_limit_slider = QSlider(Qt.Horizontal)
        self.memory_limit_slider.setRange(10, 100)
        self.memory_limit_slider.setValue(70)
        self.memory_limit_label = QLabel("70%")
        performance_layout.addWidget(self.memory_limit_slider, 1, 1)
        performance_layout.addWidget(self.memory_limit_label, 1, 2)
        
        # 并发任务数
        performance_layout.addWidget(QLabel("最大并发任务数:"), 2, 0)
        self.max_tasks_spin = QSpinBox()
        self.max_tasks_spin.setRange(1, 10)
        self.max_tasks_spin.setValue(3)
        performance_layout.addWidget(self.max_tasks_spin, 2, 1, 1, 2)
        
        # 启用性能监控
        self.enable_monitoring_check = QCheckBox("启用性能监控")
        self.enable_monitoring_check.setChecked(True)
        performance_layout.addWidget(self.enable_monitoring_check, 3, 0, 1, 3)
        
        layout.addWidget(performance_group)
        
        # 连接信号
        self.cpu_limit_slider.valueChanged.connect(
            lambda v: self.cpu_limit_label.setText(f"{v}%")
        )
        self.memory_limit_slider.valueChanged.connect(
            lambda v: self.memory_limit_label.setText(f"{v}%")
        )
        
    def get_settings(self) -> Dict[str, Any]:
        """获取设置数据。
        
        Returns:
            Dict[str, Any]: 设置数据字典
        """
        return {
            'cpu_limit': self.cpu_limit_slider.value(),
            'memory_limit': self.memory_limit_slider.value(),
            'max_tasks': self.max_tasks_spin.value(),
            'enable_monitoring': self.enable_monitoring_check.isChecked()
        }
        
    def load_settings(self, settings: Dict[str, Any]):
        """加载设置数据。
        
        Args:
            settings: 设置数据字典
        """
        cpu_limit = settings.get('cpu_limit', 80)
        self.cpu_limit_slider.setValue(cpu_limit)
        self.cpu_limit_label.setText(f"{cpu_limit}%")
        
        memory_limit = settings.get('memory_limit', 70)
        self.memory_limit_slider.setValue(memory_limit)
        self.memory_limit_label.setText(f"{memory_limit}%")
        
        self.max_tasks_spin.setValue(settings.get('max_tasks', 3))
        self.enable_monitoring_check.setChecked(settings.get('enable_monitoring', True))


class SettingsView(QWidget):
    """设置界面主视图。"""
    
    # 信号定义
    settingsChanged = pyqtSignal(dict)  # 设置变更信号
    
    def __init__(self, parent=None):
        """初始化设置视图。"""
        super().__init__(parent)
        self.settings_file = "config/settings.json"
        self._setup_ui()
        self._load_settings()
        
    def _setup_ui(self):
        """设置用户界面。"""
        layout = QVBoxLayout(self)
        
        # 标题
        title_label = QLabel("应用程序设置")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # 选项卡
        self.tab_widget = QTabWidget()
        
        # 游戏设置选项卡
        self.game_settings_widget = GameSettingsWidget()
        self.tab_widget.addTab(self.game_settings_widget, "游戏设置")
        
        # 性能设置选项卡
        self.performance_settings_widget = PerformanceSettingsWidget()
        self.tab_widget.addTab(self.performance_settings_widget, "性能设置")
        
        layout.addWidget(self.tab_widget)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        
        self.reset_button = QPushButton("重置默认")
        self.apply_button = QPushButton("应用")
        self.save_button = QPushButton("保存")
        
        button_layout.addWidget(self.reset_button)
        button_layout.addStretch()
        button_layout.addWidget(self.apply_button)
        button_layout.addWidget(self.save_button)
        
        layout.addLayout(button_layout)
        
        # 连接信号
        self.reset_button.clicked.connect(self._reset_settings)
        self.apply_button.clicked.connect(self._apply_settings)
        self.save_button.clicked.connect(self._save_settings)
        
    def _load_settings(self):
        """加载设置。"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    
                game_settings = settings.get('game', {})
                self.game_settings_widget.load_settings(game_settings)
                
                performance_settings = settings.get('performance', {})
                self.performance_settings_widget.load_settings(performance_settings)
                
        except Exception as e:
            QMessageBox.warning(self, "警告", f"加载设置失败: {e}")
            
    def _save_settings(self):
        """保存设置。"""
        try:
            settings = {
                'game': self.game_settings_widget.get_settings(),
                'performance': self.performance_settings_widget.get_settings()
            }
            
            # 确保配置目录存在
            os.makedirs(os.path.dirname(self.settings_file), exist_ok=True)
            
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
                
            QMessageBox.information(self, "成功", "设置已保存")
            self.settingsChanged.emit(settings)
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存设置失败: {e}")
            
    def _apply_settings(self):
        """应用设置。"""
        settings = {
            'game': self.game_settings_widget.get_settings(),
            'performance': self.performance_settings_widget.get_settings()
        }
        self.settingsChanged.emit(settings)
        QMessageBox.information(self, "成功", "设置已应用")
        
    def _reset_settings(self):
        """重置设置为默认值。"""
        reply = QMessageBox.question(
            self, "确认", "确定要重置所有设置为默认值吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 重置为默认设置
            default_game_settings = {
                'game_path': '',
                'window_mode': '窗口化',
                'resolution': '1920x1080',
                'operation_delay': 500,
                'retry_count': 3,
                'timeout': 30,
                'enable_logging': False
            }
            
            default_performance_settings = {
                'cpu_limit': 80,
                'memory_limit': 70,
                'max_tasks': 3,
                'enable_monitoring': True
            }
            
            self.game_settings_widget.load_settings(default_game_settings)
            self.performance_settings_widget.load_settings(default_performance_settings)
            
            QMessageBox.information(self, "成功", "设置已重置为默认值")
            
    def get_current_settings(self) -> Dict[str, Any]:
        """获取当前设置。
        
        Returns:
            Dict[str, Any]: 当前设置字典
        """
        return {
            'game': self.game_settings_widget.get_settings(),
            'performance': self.performance_settings_widget.get_settings()
        }