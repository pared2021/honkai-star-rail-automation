"""监控界面组件.

提供系统状态和性能指标的实时显示功能。
"""

import time
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QProgressBar, QTextEdit, QGroupBox,
    QPushButton, QScrollArea, QFrame
)
from PyQt6.QtCore import QTimer, pyqtSignal
from PyQt6.QtGui import QFont
from src.core.service_locator import get_service
from src.monitoring import get_monitoring_system
import psutil


class MonitoringWidget(QWidget):
    """监控界面组件."""
    
    # 信号定义
    status_updated = pyqtSignal(str)  # 状态更新信号
    
    def __init__(self, parent=None):
        """初始化监控界面.
        
        Args:
            parent: 父组件
        """
        super().__init__(parent)
        self.monitoring_system = get_monitoring_system()
        self.update_timer = QTimer()
        self.setup_ui()
        self.setup_timer()
        
    def setup_ui(self):
        """设置界面布局."""
        layout = QVBoxLayout(self)
        
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # 系统状态组
        system_group = self.create_system_status_group()
        scroll_layout.addWidget(system_group)
        
        # 应用状态组
        app_group = self.create_app_status_group()
        scroll_layout.addWidget(app_group)
        
        # 任务监控组
        task_group = self.create_task_monitoring_group()
        scroll_layout.addWidget(task_group)
        
        # 日志显示组
        log_group = self.create_log_display_group()
        scroll_layout.addWidget(log_group)
        
        # 控制按钮
        control_layout = QHBoxLayout()
        self.start_monitoring_btn = QPushButton("开始监控")
        self.stop_monitoring_btn = QPushButton("停止监控")
        self.clear_logs_btn = QPushButton("清空日志")
        self.export_data_btn = QPushButton("导出数据")
        
        control_layout.addWidget(self.start_monitoring_btn)
        control_layout.addWidget(self.stop_monitoring_btn)
        control_layout.addWidget(self.clear_logs_btn)
        control_layout.addWidget(self.export_data_btn)
        control_layout.addStretch()
        
        scroll_layout.addLayout(control_layout)
        
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)
        
        # 连接信号
        self.start_monitoring_btn.clicked.connect(self.start_monitoring)
        self.stop_monitoring_btn.clicked.connect(self.stop_monitoring)
        self.clear_logs_btn.clicked.connect(self.clear_logs)
        self.export_data_btn.clicked.connect(self.export_data)
        
    def create_system_status_group(self):
        """创建系统状态组."""
        group = QGroupBox("系统状态")
        layout = QGridLayout(group)
        
        # CPU使用率
        layout.addWidget(QLabel("CPU使用率:"), 0, 0)
        self.cpu_progress = QProgressBar()
        self.cpu_progress.setRange(0, 100)
        self.cpu_label = QLabel("0%")
        layout.addWidget(self.cpu_progress, 0, 1)
        layout.addWidget(self.cpu_label, 0, 2)
        
        # 内存使用率
        layout.addWidget(QLabel("内存使用率:"), 1, 0)
        self.memory_progress = QProgressBar()
        self.memory_progress.setRange(0, 100)
        self.memory_label = QLabel("0%")
        layout.addWidget(self.memory_progress, 1, 1)
        layout.addWidget(self.memory_label, 1, 2)
        
        # 磁盘使用率
        layout.addWidget(QLabel("磁盘使用率:"), 2, 0)
        self.disk_progress = QProgressBar()
        self.disk_progress.setRange(0, 100)
        self.disk_label = QLabel("0%")
        layout.addWidget(self.disk_progress, 2, 1)
        layout.addWidget(self.disk_label, 2, 2)
        
        # 网络状态
        layout.addWidget(QLabel("网络状态:"), 3, 0)
        self.network_label = QLabel("正常")
        layout.addWidget(self.network_label, 3, 1, 1, 2)
        
        return group
        
    def create_app_status_group(self):
        """创建应用状态组."""
        group = QGroupBox("应用状态")
        layout = QGridLayout(group)
        
        # 运行时间
        layout.addWidget(QLabel("运行时间:"), 0, 0)
        self.uptime_label = QLabel("00:00:00")
        layout.addWidget(self.uptime_label, 0, 1)
        
        # 游戏检测状态
        layout.addWidget(QLabel("游戏检测:"), 1, 0)
        self.game_status_label = QLabel("未检测到")
        layout.addWidget(self.game_status_label, 1, 1)
        
        # 自动化状态
        layout.addWidget(QLabel("自动化状态:"), 2, 0)
        self.automation_status_label = QLabel("已停止")
        layout.addWidget(self.automation_status_label, 2, 1)
        
        # 数据库状态
        layout.addWidget(QLabel("数据库状态:"), 3, 0)
        self.database_status_label = QLabel("正常")
        layout.addWidget(self.database_status_label, 3, 1)
        
        return group
        
    def create_task_monitoring_group(self):
        """创建任务监控组."""
        group = QGroupBox("任务监控")
        layout = QGridLayout(group)
        
        # 总任务数
        layout.addWidget(QLabel("总任务数:"), 0, 0)
        self.total_tasks_label = QLabel("0")
        layout.addWidget(self.total_tasks_label, 0, 1)
        
        # 成功任务数
        layout.addWidget(QLabel("成功任务数:"), 1, 0)
        self.success_tasks_label = QLabel("0")
        layout.addWidget(self.success_tasks_label, 1, 1)
        
        # 失败任务数
        layout.addWidget(QLabel("失败任务数:"), 2, 0)
        self.failed_tasks_label = QLabel("0")
        layout.addWidget(self.failed_tasks_label, 2, 1)
        
        # 成功率
        layout.addWidget(QLabel("成功率:"), 3, 0)
        self.success_rate_label = QLabel("0%")
        layout.addWidget(self.success_rate_label, 3, 1)
        
        return group
        
    def create_log_display_group(self):
        """创建日志显示组."""
        group = QGroupBox("实时日志")
        layout = QVBoxLayout(group)
        
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setMaximumHeight(200)
        
        # 设置等宽字体
        font = QFont("Consolas", 9)
        font.setStyleHint(QFont.Monospace)
        self.log_display.setFont(font)
        
        layout.addWidget(self.log_display)
        
        return group
        
    def setup_timer(self):
        """设置更新定时器."""
        self.update_timer.timeout.connect(self.update_monitoring_data)
        self.update_timer.start(2000)  # 每2秒更新一次
        self.start_time = time.time()
        
    def update_monitoring_data(self):
        """更新监控数据."""
        try:
            # 更新系统状态
            self.update_system_status()
            
            # 更新应用状态
            self.update_app_status()
            
            # 更新任务监控
            self.update_task_monitoring()
            
        except Exception as e:
            self.add_log(f"更新监控数据时出错: {str(e)}")
            
    def update_system_status(self):
        """更新系统状态."""
        # CPU使用率
        cpu_percent = psutil.cpu_percent(interval=None)
        self.cpu_progress.setValue(int(cpu_percent))
        self.cpu_label.setText(f"{cpu_percent:.1f}%")
        
        # 内存使用率
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        self.memory_progress.setValue(int(memory_percent))
        self.memory_label.setText(f"{memory_percent:.1f}%")
        
        # 磁盘使用率
        disk = psutil.disk_usage('/')
        disk_percent = (disk.used / disk.total) * 100
        self.disk_progress.setValue(int(disk_percent))
        self.disk_label.setText(f"{disk_percent:.1f}%")
        
        # 网络状态（简化检查）
        try:
            net_io = psutil.net_io_counters()
            if net_io.bytes_sent > 0 or net_io.bytes_recv > 0:
                self.network_label.setText("正常")
            else:
                self.network_label.setText("无活动")
        except:
            self.network_label.setText("未知")
            
    def update_app_status(self):
        """更新应用状态."""
        # 运行时间
        uptime = time.time() - self.start_time
        hours = int(uptime // 3600)
        minutes = int((uptime % 3600) // 60)
        seconds = int(uptime % 60)
        self.uptime_label.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")
        
        # 游戏检测状态（模拟）
        self.game_status_label.setText("未检测到")
        
        # 自动化状态（模拟）
        self.automation_status_label.setText("已停止")
        
        # 数据库状态（模拟）
        self.database_status_label.setText("正常")
        
    def update_task_monitoring(self):
        """更新任务监控."""
        # 这里应该从数据库或监控系统获取真实数据
        # 目前使用模拟数据
        total = 0
        success = 0
        failed = 0
        
        self.total_tasks_label.setText(str(total))
        self.success_tasks_label.setText(str(success))
        self.failed_tasks_label.setText(str(failed))
        
        if total > 0:
            success_rate = (success / total) * 100
            self.success_rate_label.setText(f"{success_rate:.1f}%")
        else:
            self.success_rate_label.setText("0%")
            
    def add_log(self, message: str):
        """添加日志消息.
        
        Args:
            message: 日志消息
        """
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.log_display.append(log_entry)
        
        # 限制日志行数
        if self.log_display.document().blockCount() > 1000:
            cursor = self.log_display.textCursor()
            cursor.movePosition(cursor.Start)
            cursor.select(cursor.BlockUnderCursor)
            cursor.removeSelectedText()
            
    def start_monitoring(self):
        """开始监控."""
        if self.monitoring_system:
            self.monitoring_system.start()
        self.add_log("监控系统已启动")
        self.start_monitoring_btn.setEnabled(False)
        self.stop_monitoring_btn.setEnabled(True)
        
    def stop_monitoring(self):
        """停止监控."""
        if self.monitoring_system:
            self.monitoring_system.stop()
        self.add_log("监控系统已停止")
        self.start_monitoring_btn.setEnabled(True)
        self.stop_monitoring_btn.setEnabled(False)
        
    def clear_logs(self):
        """清空日志."""
        self.log_display.clear()
        self.add_log("日志已清空")
        
    def export_data(self):
        """导出监控数据."""
        # 这里应该实现数据导出功能
        self.add_log("数据导出功能待实现")
        
    def closeEvent(self, event):
        """关闭事件处理."""
        self.update_timer.stop()
        super().closeEvent(event)