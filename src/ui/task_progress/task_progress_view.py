"""任务进度显示视图模块.

实现任务进度显示界面的视图组件。
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar,
    QScrollArea, QFrame, QGridLayout, QPushButton, QSplitter,
    QTreeWidget, QTreeWidgetItem, QHeaderView, QGroupBox
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QPalette, QColor
from typing import Dict, Any, Optional


class TaskProgressWidget(QFrame):
    """单个任务进度组件."""
    
    # 信号定义
    pause_requested = pyqtSignal(str)  # task_id
    resume_requested = pyqtSignal(str)  # task_id
    cancel_requested = pyqtSignal(str)  # task_id
    
    def __init__(self, task_id: str, task_name: str, parent=None):
        super().__init__(parent)
        
        self.task_id = task_id
        self.task_name = task_name
        
        self.setup_ui()
        self.setup_style()
        
    def setup_ui(self):
        """设置UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(5)
        
        # 任务标题行
        title_layout = QHBoxLayout()
        
        self.name_label = QLabel(self.task_name)
        self.name_label.setFont(QFont("Arial", 10, QFont.Bold))
        title_layout.addWidget(self.name_label)
        
        title_layout.addStretch()
        
        self.status_label = QLabel("待处理")
        self.status_label.setFont(QFont("Arial", 9))
        title_layout.addWidget(self.status_label)
        
        layout.addLayout(title_layout)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        layout.addWidget(self.progress_bar)
        
        # 详细信息行
        info_layout = QGridLayout()
        info_layout.setSpacing(5)
        
        # 当前步骤
        info_layout.addWidget(QLabel("当前步骤:"), 0, 0)
        self.step_label = QLabel("-")
        self.step_label.setFont(QFont("Arial", 8))
        info_layout.addWidget(self.step_label, 0, 1)
        
        # 已用时间
        info_layout.addWidget(QLabel("已用时间:"), 0, 2)
        self.elapsed_label = QLabel("00:00:00")
        self.elapsed_label.setFont(QFont("Arial", 8))
        info_layout.addWidget(self.elapsed_label, 0, 3)
        
        # 剩余时间
        info_layout.addWidget(QLabel("剩余时间:"), 1, 0)
        self.remaining_label = QLabel("-")
        self.remaining_label.setFont(QFont("Arial", 8))
        info_layout.addWidget(self.remaining_label, 1, 1)
        
        # 步骤进度
        info_layout.addWidget(QLabel("步骤进度:"), 1, 2)
        self.steps_label = QLabel("0/0")
        self.steps_label.setFont(QFont("Arial", 8))
        info_layout.addWidget(self.steps_label, 1, 3)
        
        layout.addLayout(info_layout)
        
        # 控制按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.pause_button = QPushButton("暂停")
        self.pause_button.setFixedSize(60, 25)
        self.pause_button.clicked.connect(self.on_pause_clicked)
        button_layout.addWidget(self.pause_button)
        
        self.cancel_button = QPushButton("取消")
        self.cancel_button.setFixedSize(60, 25)
        self.cancel_button.clicked.connect(self.on_cancel_clicked)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        
        # 错误信息（默认隐藏）
        self.error_label = QLabel()
        self.error_label.setStyleSheet("color: red; font-size: 8pt;")
        self.error_label.setWordWrap(True)
        self.error_label.hide()
        layout.addWidget(self.error_label)
        
    def setup_style(self):
        """设置样式."""
        self.setFrameStyle(QFrame.Box)
        self.setLineWidth(1)
        self.setStyleSheet("""
            TaskProgressWidget {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 5px;
            }
            QLabel {
                color: #495057;
            }
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 3px;
                font-size: 8pt;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:pressed {
                background-color: #004085;
            }
        """)
        
    def update_progress(self, progress_data: Dict[str, Any]):
        """更新进度显示."""
        status = progress_data.get('status', 'pending')
        progress = progress_data.get('progress', 0)
        current_step = progress_data.get('current_step', '')
        elapsed_time = progress_data.get('elapsed_time', 0)
        remaining_time = progress_data.get('remaining_time')
        completed_steps = progress_data.get('completed_steps', 0)
        total_steps = progress_data.get('total_steps', 0)
        error_message = progress_data.get('error_message', '')
        
        # 更新状态
        status_text = {
            'pending': '待处理',
            'running': '运行中',
            'completed': '已完成',
            'failed': '失败',
            'paused': '已暂停'
        }.get(status, status)
        
        self.status_label.setText(status_text)
        
        # 更新进度条
        self.progress_bar.setValue(progress)
        
        # 更新当前步骤
        self.step_label.setText(current_step or "-")
        
        # 更新时间
        self.elapsed_label.setText(self.format_time(elapsed_time))
        
        if remaining_time is not None:
            self.remaining_label.setText(self.format_time(remaining_time))
        else:
            self.remaining_label.setText("-")
            
        # 更新步骤进度
        self.steps_label.setText(f"{completed_steps}/{total_steps}")
        
        # 更新按钮状态
        if status == 'running':
            self.pause_button.setText("暂停")
            self.pause_button.setEnabled(True)
            self.cancel_button.setEnabled(True)
        elif status == 'paused':
            self.pause_button.setText("继续")
            self.pause_button.setEnabled(True)
            self.cancel_button.setEnabled(True)
        elif status in ['completed', 'failed']:
            self.pause_button.setEnabled(False)
            self.cancel_button.setEnabled(False)
        else:
            self.pause_button.setEnabled(False)
            self.cancel_button.setEnabled(False)
            
        # 显示错误信息
        if error_message:
            self.error_label.setText(f"错误: {error_message}")
            self.error_label.show()
        else:
            self.error_label.hide()
            
        # 更新样式
        self.update_status_style(status)
        
    def update_status_style(self, status: str):
        """根据状态更新样式."""
        color_map = {
            'pending': '#6c757d',
            'running': '#007bff',
            'completed': '#28a745',
            'failed': '#dc3545',
            'paused': '#ffc107'
        }
        
        color = color_map.get(status, '#6c757d')
        self.status_label.setStyleSheet(f"color: {color}; font-weight: bold;")
        
        if status == 'completed':
            self.progress_bar.setStyleSheet("""
                QProgressBar::chunk {
                    background-color: #28a745;
                }
            """)
        elif status == 'failed':
            self.progress_bar.setStyleSheet("""
                QProgressBar::chunk {
                    background-color: #dc3545;
                }
            """)
        elif status == 'paused':
            self.progress_bar.setStyleSheet("""
                QProgressBar::chunk {
                    background-color: #ffc107;
                }
            """)
        else:
            self.progress_bar.setStyleSheet("""
                QProgressBar::chunk {
                    background-color: #007bff;
                }
            """)
            
    def format_time(self, seconds: int) -> str:
        """格式化时间显示."""
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        
    def on_pause_clicked(self):
        """暂停/继续按钮点击."""
        if self.pause_button.text() == "暂停":
            self.pause_requested.emit(self.task_id)
        else:
            self.resume_requested.emit(self.task_id)
            
    def on_cancel_clicked(self):
        """取消按钮点击."""
        self.cancel_requested.emit(self.task_id)


class OverallProgressWidget(QGroupBox):
    """整体进度组件."""
    
    def __init__(self, parent=None):
        super().__init__("整体进度", parent)
        
        self.setup_ui()
        
    def setup_ui(self):
        """设置UI."""
        layout = QVBoxLayout(self)
        
        # 整体进度条
        self.overall_progress_bar = QProgressBar()
        self.overall_progress_bar.setRange(0, 100)
        self.overall_progress_bar.setValue(0)
        self.overall_progress_bar.setTextVisible(True)
        self.overall_progress_bar.setFixedHeight(25)
        layout.addWidget(self.overall_progress_bar)
        
        # 统计信息
        stats_layout = QGridLayout()
        
        # 任务统计
        stats_layout.addWidget(QLabel("总任务:"), 0, 0)
        self.total_tasks_label = QLabel("0")
        stats_layout.addWidget(self.total_tasks_label, 0, 1)
        
        stats_layout.addWidget(QLabel("已完成:"), 0, 2)
        self.completed_tasks_label = QLabel("0")
        stats_layout.addWidget(self.completed_tasks_label, 0, 3)
        
        stats_layout.addWidget(QLabel("运行中:"), 1, 0)
        self.running_tasks_label = QLabel("0")
        stats_layout.addWidget(self.running_tasks_label, 1, 1)
        
        stats_layout.addWidget(QLabel("失败:"), 1, 2)
        self.failed_tasks_label = QLabel("0")
        stats_layout.addWidget(self.failed_tasks_label, 1, 3)
        
        # 时间统计
        stats_layout.addWidget(QLabel("总用时:"), 2, 0)
        self.total_elapsed_label = QLabel("00:00:00")
        stats_layout.addWidget(self.total_elapsed_label, 2, 1)
        
        stats_layout.addWidget(QLabel("预计剩余:"), 2, 2)
        self.total_remaining_label = QLabel("-")
        stats_layout.addWidget(self.total_remaining_label, 2, 3)
        
        layout.addLayout(stats_layout)
        
    def update_progress(self, progress_data: Dict[str, Any]):
        """更新整体进度."""
        overall_progress = progress_data.get('overall_progress', 0)
        total_tasks = progress_data.get('total_tasks', 0)
        completed_tasks = progress_data.get('completed_tasks', 0)
        running_tasks = progress_data.get('running_tasks', 0)
        failed_tasks = progress_data.get('failed_tasks', 0)
        elapsed_total_time = progress_data.get('elapsed_total_time', 0)
        remaining_total_time = progress_data.get('remaining_total_time')
        
        # 更新进度条
        self.overall_progress_bar.setValue(overall_progress)
        
        # 更新统计
        self.total_tasks_label.setText(str(total_tasks))
        self.completed_tasks_label.setText(str(completed_tasks))
        self.running_tasks_label.setText(str(running_tasks))
        self.failed_tasks_label.setText(str(failed_tasks))
        
        # 更新时间
        self.total_elapsed_label.setText(self.format_time(elapsed_total_time))
        
        if remaining_total_time is not None:
            self.total_remaining_label.setText(self.format_time(remaining_total_time))
        else:
            self.total_remaining_label.setText("-")
            
    def format_time(self, seconds: int) -> str:
        """格式化时间显示."""
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


class TaskProgressView(QWidget):
    """任务进度显示视图."""
    
    # 信号定义
    task_pause_requested = pyqtSignal(str)  # task_id
    task_resume_requested = pyqtSignal(str)  # task_id
    task_cancel_requested = pyqtSignal(str)  # task_id
    refresh_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 任务进度组件字典
        self.task_widgets: Dict[str, TaskProgressWidget] = {}
        
        self.setup_ui()
        self.setup_timer()
        
    def setup_ui(self):
        """设置UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # 整体进度组件
        self.overall_widget = OverallProgressWidget()
        layout.addWidget(self.overall_widget)
        
        # 任务列表滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # 任务列表容器
        self.tasks_container = QWidget()
        self.tasks_layout = QVBoxLayout(self.tasks_container)
        self.tasks_layout.setSpacing(5)
        self.tasks_layout.addStretch()
        
        scroll_area.setWidget(self.tasks_container)
        layout.addWidget(scroll_area)
        
        # 控制按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.refresh_button = QPushButton("刷新")
        self.refresh_button.clicked.connect(self.refresh_requested.emit)
        button_layout.addWidget(self.refresh_button)
        
        self.clear_button = QPushButton("清除已完成")
        self.clear_button.clicked.connect(self.clear_completed_tasks)
        button_layout.addWidget(self.clear_button)
        
        layout.addLayout(button_layout)
        
    def setup_timer(self):
        """设置定时器."""
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_requested.emit)
        self.refresh_timer.start(2000)  # 每2秒刷新一次
        
    def add_task_widget(self, task_id: str, task_name: str) -> TaskProgressWidget:
        """添加任务组件."""
        if task_id not in self.task_widgets:
            widget = TaskProgressWidget(task_id, task_name)
            
            # 连接信号
            widget.pause_requested.connect(self.task_pause_requested.emit)
            widget.resume_requested.connect(self.task_resume_requested.emit)
            widget.cancel_requested.connect(self.task_cancel_requested.emit)
            
            # 添加到布局
            self.tasks_layout.insertWidget(self.tasks_layout.count() - 1, widget)
            self.task_widgets[task_id] = widget
            
        return self.task_widgets[task_id]
        
    def update_task_progress(self, task_id: str, progress_data: Dict[str, Any]):
        """更新任务进度."""
        if task_id in self.task_widgets:
            self.task_widgets[task_id].update_progress(progress_data)
        else:
            # 如果任务组件不存在，创建它
            task_name = progress_data.get('task_name', f'任务 {task_id}')
            widget = self.add_task_widget(task_id, task_name)
            widget.update_progress(progress_data)
            
    def update_overall_progress(self, progress_data: Dict[str, Any]):
        """更新整体进度."""
        self.overall_widget.update_progress(progress_data)
        
    def remove_task_widget(self, task_id: str):
        """移除任务组件."""
        if task_id in self.task_widgets:
            widget = self.task_widgets[task_id]
            self.tasks_layout.removeWidget(widget)
            widget.deleteLater()
            del self.task_widgets[task_id]
            
    def clear_completed_tasks(self):
        """清除已完成的任务."""
        completed_tasks = []
        for task_id, widget in self.task_widgets.items():
            if widget.status_label.text() in ['已完成', '失败']:
                completed_tasks.append(task_id)
                
        for task_id in completed_tasks:
            self.remove_task_widget(task_id)
            
    def clear_all_tasks(self):
        """清除所有任务."""
        for task_id in list(self.task_widgets.keys()):
            self.remove_task_widget(task_id)
            
    def get_task_count(self) -> int:
        """获取任务数量."""
        return len(self.task_widgets)
        
    def cleanup(self):
        """清理资源."""
        if self.refresh_timer.isActive():
            self.refresh_timer.stop()