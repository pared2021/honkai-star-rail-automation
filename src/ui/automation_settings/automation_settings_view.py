"""自动化设置视图模块.

实现自动化设置界面的视图组件。
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QPushButton, QLabel, QProgressBar, QTextEdit,
    QComboBox, QSpinBox, QCheckBox, QFrame,
    QSplitter, QScrollArea
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QPalette, QColor
from typing import Dict, Any, Optional


class AutomationControlWidget(QWidget):
    """自动化控制组件."""
    
    # 信号定义
    start_automation = pyqtSignal()
    pause_automation = pyqtSignal()
    stop_automation = pyqtSignal()
    resume_automation = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.automation_status = "stopped"  # stopped, running, paused
        self.setup_ui()
        self.connect_signals()
        
    def setup_ui(self):
        """设置UI界面."""
        layout = QVBoxLayout(self)
        
        # 状态显示区域
        self.setup_status_area(layout)
        
        # 控制按钮区域
        self.setup_control_buttons(layout)
        
        # 进度显示区域
        self.setup_progress_area(layout)
        
    def setup_status_area(self, layout):
        """设置状态显示区域."""
        status_group = QGroupBox("自动化状态")
        status_layout = QVBoxLayout(status_group)
        
        # 状态标签
        self.status_label = QLabel("状态: 已停止")
        self.status_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #666;
                padding: 5px;
            }
        """)
        
        # 运行时间标签
        self.runtime_label = QLabel("运行时间: 00:00:00")
        self.runtime_label.setStyleSheet("font-size: 12px; color: #888;")
        
        # 任务计数标签
        self.task_count_label = QLabel("已完成任务: 0")
        self.task_count_label.setStyleSheet("font-size: 12px; color: #888;")
        
        status_layout.addWidget(self.status_label)
        status_layout.addWidget(self.runtime_label)
        status_layout.addWidget(self.task_count_label)
        
        layout.addWidget(status_group)
        
    def setup_control_buttons(self, layout):
        """设置控制按钮区域."""
        control_group = QGroupBox("自动化控制")
        control_layout = QHBoxLayout(control_group)
        
        # 开始按钮
        self.start_button = QPushButton("开始自动化")
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        
        # 暂停/恢复按钮
        self.pause_button = QPushButton("暂停")
        self.pause_button.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #e68900;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.pause_button.setEnabled(False)
        
        # 停止按钮
        self.stop_button = QPushButton("停止")
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.stop_button.setEnabled(False)
        
        control_layout.addWidget(self.start_button)
        control_layout.addWidget(self.pause_button)
        control_layout.addWidget(self.stop_button)
        control_layout.addStretch()
        
        layout.addWidget(control_group)
        
    def setup_progress_area(self, layout):
        """设置进度显示区域."""
        progress_group = QGroupBox("执行进度")
        progress_layout = QVBoxLayout(progress_group)
        
        # 总体进度条
        self.overall_progress = QProgressBar()
        self.overall_progress.setStyleSheet("""
            QProgressBar {
                border: 2px solid grey;
                border-radius: 5px;
                text-align: center;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 3px;
            }
        """)
        
        # 当前任务进度条
        self.current_task_progress = QProgressBar()
        self.current_task_progress.setStyleSheet("""
            QProgressBar {
                border: 2px solid grey;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #2196F3;
                border-radius: 3px;
            }
        """)
        
        # 进度标签
        self.overall_progress_label = QLabel("总体进度: 0%")
        self.current_task_label = QLabel("当前任务: 无")
        
        progress_layout.addWidget(self.overall_progress_label)
        progress_layout.addWidget(self.overall_progress)
        progress_layout.addWidget(self.current_task_label)
        progress_layout.addWidget(self.current_task_progress)
        
        layout.addWidget(progress_group)
        
    def connect_signals(self):
        """连接信号."""
        self.start_button.clicked.connect(self.on_start_clicked)
        self.pause_button.clicked.connect(self.on_pause_clicked)
        self.stop_button.clicked.connect(self.on_stop_clicked)
        
    def on_start_clicked(self):
        """开始按钮点击处理."""
        self.start_automation.emit()
        
    def on_pause_clicked(self):
        """暂停/恢复按钮点击处理."""
        if self.automation_status == "running":
            self.pause_automation.emit()
        elif self.automation_status == "paused":
            self.resume_automation.emit()
            
    def on_stop_clicked(self):
        """停止按钮点击处理."""
        self.stop_automation.emit()
        
    def update_status(self, status: str, runtime: str = None, task_count: int = None):
        """更新状态显示."""
        self.automation_status = status
        
        status_text = {
            "stopped": "已停止",
            "running": "运行中",
            "paused": "已暂停"
        }.get(status, "未知")
        
        status_color = {
            "stopped": "#666",
            "running": "#4CAF50",
            "paused": "#FF9800"
        }.get(status, "#666")
        
        self.status_label.setText(f"状态: {status_text}")
        self.status_label.setStyleSheet(f"""
            QLabel {{
                font-size: 14px;
                font-weight: bold;
                color: {status_color};
                padding: 5px;
            }}
        """)
        
        if runtime:
            self.runtime_label.setText(f"运行时间: {runtime}")
            
        if task_count is not None:
            self.task_count_label.setText(f"已完成任务: {task_count}")
            
        # 更新按钮状态
        self.update_button_states()
        
    def update_button_states(self):
        """更新按钮状态."""
        if self.automation_status == "stopped":
            self.start_button.setEnabled(True)
            self.start_button.setText("开始自动化")
            self.pause_button.setEnabled(False)
            self.pause_button.setText("暂停")
            self.stop_button.setEnabled(False)
        elif self.automation_status == "running":
            self.start_button.setEnabled(False)
            self.pause_button.setEnabled(True)
            self.pause_button.setText("暂停")
            self.stop_button.setEnabled(True)
        elif self.automation_status == "paused":
            self.start_button.setEnabled(False)
            self.pause_button.setEnabled(True)
            self.pause_button.setText("恢复")
            self.stop_button.setEnabled(True)
            
    def update_progress(self, overall_progress: int, current_task_progress: int = None, 
                      current_task_name: str = None):
        """更新进度显示."""
        self.overall_progress.setValue(overall_progress)
        self.overall_progress_label.setText(f"总体进度: {overall_progress}%")
        
        if current_task_progress is not None:
            self.current_task_progress.setValue(current_task_progress)
            
        if current_task_name:
            self.current_task_label.setText(f"当前任务: {current_task_name}")


class AutomationSettingsView(QWidget):
    """自动化设置视图."""
    
    # 信号定义
    settings_changed = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.connect_signals()
        
    def setup_ui(self):
        """设置UI界面."""
        layout = QVBoxLayout(self)
        
        # 创建分割器
        splitter = QSplitter(Qt.Vertical)
        
        # 自动化控制组件
        self.control_widget = AutomationControlWidget()
        splitter.addWidget(self.control_widget)
        
        # 设置区域
        self.setup_settings_area(splitter)
        
        # 设置分割器比例
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        
        layout.addWidget(splitter)
        
    def setup_settings_area(self, parent):
        """设置配置区域."""
        settings_widget = QWidget()
        settings_layout = QVBoxLayout(settings_widget)
        
        # 基本设置组
        basic_group = QGroupBox("基本设置")
        basic_layout = QVBoxLayout(basic_group)
        
        # 自动重试设置
        retry_layout = QHBoxLayout()
        retry_layout.addWidget(QLabel("失败重试次数:"))
        self.retry_spinbox = QSpinBox()
        self.retry_spinbox.setRange(0, 10)
        self.retry_spinbox.setValue(3)
        retry_layout.addWidget(self.retry_spinbox)
        retry_layout.addStretch()
        
        # 延迟设置
        delay_layout = QHBoxLayout()
        delay_layout.addWidget(QLabel("操作间隔(秒):"))
        self.delay_spinbox = QSpinBox()
        self.delay_spinbox.setRange(1, 60)
        self.delay_spinbox.setValue(2)
        delay_layout.addWidget(self.delay_spinbox)
        delay_layout.addStretch()
        
        # 自动保存设置
        self.auto_save_checkbox = QCheckBox("自动保存进度")
        self.auto_save_checkbox.setChecked(True)
        
        basic_layout.addLayout(retry_layout)
        basic_layout.addLayout(delay_layout)
        basic_layout.addWidget(self.auto_save_checkbox)
        
        settings_layout.addWidget(basic_group)
        settings_layout.addStretch()
        
        parent.addWidget(settings_widget)
        
    def connect_signals(self):
        """连接信号."""
        self.retry_spinbox.valueChanged.connect(self.on_settings_changed)
        self.delay_spinbox.valueChanged.connect(self.on_settings_changed)
        self.auto_save_checkbox.toggled.connect(self.on_settings_changed)
        
    def on_settings_changed(self):
        """设置变更处理."""
        settings = {
            'retry_count': self.retry_spinbox.value(),
            'operation_delay': self.delay_spinbox.value(),
            'auto_save': self.auto_save_checkbox.isChecked()
        }
        self.settings_changed.emit(settings)
        
    def get_control_widget(self) -> AutomationControlWidget:
        """获取控制组件."""
        return self.control_widget
        
    def get_settings(self) -> Dict[str, Any]:
        """获取当前设置."""
        return {
            'retry_count': self.retry_spinbox.value(),
            'operation_delay': self.delay_spinbox.value(),
            'auto_save': self.auto_save_checkbox.isChecked()
        }
        
    def set_settings(self, settings: Dict[str, Any]):
        """设置配置值."""
        if 'retry_count' in settings:
            self.retry_spinbox.setValue(settings['retry_count'])
        if 'operation_delay' in settings:
            self.delay_spinbox.setValue(settings['operation_delay'])
        if 'auto_save' in settings:
            self.auto_save_checkbox.setChecked(settings['auto_save'])
