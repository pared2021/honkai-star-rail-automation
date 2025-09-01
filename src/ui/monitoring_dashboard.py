# -*- coding: utf-8 -*-
"""
监控仪表板 - 实时显示系统状态和监控数据
"""

import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QProgressBar, QPushButton, QTextEdit,
    QTabWidget, QTableWidget, QTableWidgetItem,
    QGroupBox, QScrollArea, QFrame, QSplitter,
    QComboBox, QSpinBox, QCheckBox
)
from PyQt6.QtCore import QTimer, pyqtSignal, Qt, QThread, pyqtSlot
from PyQt6.QtGui import QFont, QPalette, QColor, QPixmap, QPainter
from PyQt6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis, QDateTimeAxis

from loguru import logger

from src.monitoring.logging_monitoring_service import (
    LoggingMonitoringService, LogLevel, MonitoringEventType
)
from core.performance_monitor import PerformanceLevel


class MetricsWidget(QWidget):
    """指标显示组件"""
    
    def __init__(self, title: str, value: str = "0", unit: str = "",
                 color: str = "#2196F3", parent=None):
        super().__init__(parent)
        self.title = title
        self.color = color
        
        self.setup_ui()
        self.update_value(value, unit)
    
    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 标题
        self.title_label = QLabel(self.title)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(10)
        font.setBold(True)
        self.title_label.setFont(font)
        
        # 数值
        self.value_label = QLabel("0")
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(24)
        font.setBold(True)
        self.value_label.setFont(font)
        self.value_label.setStyleSheet(f"color: {self.color};")
        
        # 单位
        self.unit_label = QLabel("")
        self.unit_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(8)
        self.unit_label.setFont(font)
        
        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)
        layout.addWidget(self.unit_label)
        
        self.setLayout(layout)
        
        # 设置样式
        self.setStyleSheet("""
            MetricsWidget {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 8px;
            }
        """)
        
        self.setFixedSize(120, 100)
    
    def update_value(self, value: str, unit: str = ""):
        """更新数值"""
        self.value_label.setText(str(value))
        self.unit_label.setText(unit)
    
    def set_color(self, color: str):
        """设置颜色"""
        self.color = color
        self.value_label.setStyleSheet(f"color: {color};")


class StatusIndicator(QWidget):
    """状态指示器"""
    
    def __init__(self, title: str, status: str = "unknown", parent=None):
        super().__init__(parent)
        self.title = title
        self.status = status
        
        self.setup_ui()
        self.update_status(status)
    
    def setup_ui(self):
        """设置UI"""
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 状态指示灯
        self.indicator = QLabel()
        self.indicator.setFixedSize(12, 12)
        self.indicator.setStyleSheet("""
            QLabel {
                border-radius: 6px;
                background-color: #ccc;
            }
        """)
        
        # 标题
        self.title_label = QLabel(self.title)
        font = QFont()
        font.setPointSize(9)
        self.title_label.setFont(font)
        
        # 状态文本
        self.status_label = QLabel("未知")
        font = QFont()
        font.setPointSize(9)
        font.setBold(True)
        self.status_label.setFont(font)
        
        layout.addWidget(self.indicator)
        layout.addWidget(self.title_label)
        layout.addStretch()
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
    
    def update_status(self, status: str):
        """更新状态"""
        self.status = status
        
        status_config = {
            'excellent': {'color': '#4CAF50', 'text': '优秀'},
            'good': {'color': '#8BC34A', 'text': '良好'},
            'fair': {'color': '#FFC107', 'text': '一般'},
            'poor': {'color': '#FF9800', 'text': '较差'},
            'critical': {'color': '#F44336', 'text': '严重'},
            'running': {'color': '#2196F3', 'text': '运行中'},
            'stopped': {'color': '#9E9E9E', 'text': '已停止'},
            'error': {'color': '#F44336', 'text': '错误'},
            'unknown': {'color': '#9E9E9E', 'text': '未知'}
        }
        
        config = status_config.get(status, status_config['unknown'])
        
        self.indicator.setStyleSheet(f"""
            QLabel {{
                border-radius: 6px;
                background-color: {config['color']};
            }}
        """)
        
        self.status_label.setText(config['text'])
        self.status_label.setStyleSheet(f"color: {config['color']};")


class LogViewer(QWidget):
    """日志查看器"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
        # 日志过滤配置
        self.current_level = None
        self.current_module = None
        self.max_logs = 1000
    
    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout()
        
        # 控制面板
        control_layout = QHBoxLayout()
        
        # 日志级别过滤
        control_layout.addWidget(QLabel("级别:"))
        self.level_combo = QComboBox()
        self.level_combo.addItems(["全部", "ERROR", "WARNING", "INFO", "DEBUG"])
        self.level_combo.currentTextChanged.connect(self.on_level_changed)
        control_layout.addWidget(self.level_combo)
        
        # 模块过滤
        control_layout.addWidget(QLabel("模块:"))
        self.module_combo = QComboBox()
        self.module_combo.setEditable(True)
        self.module_combo.addItem("全部")
        self.module_combo.currentTextChanged.connect(self.on_module_changed)
        control_layout.addWidget(self.module_combo)
        
        # 自动滚动
        self.auto_scroll_check = QCheckBox("自动滚动")
        self.auto_scroll_check.setChecked(True)
        control_layout.addWidget(self.auto_scroll_check)
        
        # 清空按钮
        clear_btn = QPushButton("清空")
        clear_btn.clicked.connect(self.clear_logs)
        control_layout.addWidget(clear_btn)
        
        # 导出按钮
        export_btn = QPushButton("导出")
        export_btn.clicked.connect(self.export_logs)
        control_layout.addWidget(export_btn)
        
        control_layout.addStretch()
        
        # 日志显示区域
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        
        layout.addLayout(control_layout)
        layout.addWidget(self.log_text)
        
        self.setLayout(layout)
    
    def add_log_entry(self, log_data: Dict[str, Any]):
        """添加日志条目"""
        # 应用过滤器
        if self.current_level and log_data.get('level') != self.current_level:
            return
        
        if self.current_module and self.current_module not in log_data.get('module', ''):
            return
        
        # 格式化日志
        timestamp = log_data.get('timestamp', '')
        level = log_data.get('level', '')
        module = log_data.get('module', '')
        message = log_data.get('message', '')
        
        # 设置颜色
        color_map = {
            'ERROR': '#F44336',
            'WARNING': '#FF9800',
            'INFO': '#2196F3',
            'DEBUG': '#9E9E9E'
        }
        color = color_map.get(level, '#000000')
        
        # 添加到文本框
        formatted_log = f"<span style='color: {color}'>[{timestamp}] [{level}] {module} - {message}</span><br>"
        self.log_text.insertHtml(formatted_log)
        
        # 自动滚动
        if self.auto_scroll_check.isChecked():
            scrollbar = self.log_text.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
        
        # 限制日志数量
        if self.log_text.document().blockCount() > self.max_logs:
            cursor = self.log_text.textCursor()
            cursor.movePosition(cursor.MoveOperation.Start)
            cursor.movePosition(cursor.MoveOperation.Down, cursor.MoveMode.KeepAnchor, 100)
            cursor.removeSelectedText()
    
    def on_level_changed(self, level: str):
        """日志级别改变"""
        self.current_level = level if level != "全部" else None
    
    def on_module_changed(self, module: str):
        """模块过滤改变"""
        self.current_module = module if module != "全部" else None
    
    def clear_logs(self):
        """清空日志"""
        self.log_text.clear()
    
    def export_logs(self):
        """导出日志"""
        # 这里可以实现日志导出功能
        logger.info("导出日志功能待实现")


class EventViewer(QTableWidget):
    """事件查看器"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
        # 事件数据
        self.events = []
        self.max_events = 500
    
    def setup_ui(self):
        """设置UI"""
        # 设置列
        headers = ["时间", "类型", "来源", "严重程度", "消息"]
        self.setColumnCount(len(headers))
        self.setHorizontalHeaderLabels(headers)
        
        # 设置列宽
        self.setColumnWidth(0, 150)  # 时间
        self.setColumnWidth(1, 120)  # 类型
        self.setColumnWidth(2, 100)  # 来源
        self.setColumnWidth(3, 80)   # 严重程度
        self.setColumnWidth(4, 300)  # 消息
        
        # 设置选择模式
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        # 设置样式
        self.setAlternatingRowColors(True)
        self.setStyleSheet("""
            QTableWidget {
                gridline-color: #ddd;
            }
            QTableWidget::item {
                padding: 5px;
            }
        """)
    
    def add_event(self, event_data: Dict[str, Any]):
        """添加事件"""
        self.events.append(event_data)
        
        # 限制事件数量
        if len(self.events) > self.max_events:
            self.events = self.events[-self.max_events:]
            self.refresh_table()
        else:
            self.add_event_row(event_data)
    
    def add_event_row(self, event_data: Dict[str, Any]):
        """添加事件行"""
        row = self.rowCount()
        self.insertRow(row)
        
        # 时间
        timestamp = event_data.get('timestamp', '')
        if timestamp:
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                timestamp = dt.strftime('%H:%M:%S')
            except:
                pass
        self.setItem(row, 0, QTableWidgetItem(timestamp))
        
        # 类型
        event_type = event_data.get('event_type', '')
        self.setItem(row, 1, QTableWidgetItem(event_type))
        
        # 来源
        source = event_data.get('source', '')
        self.setItem(row, 2, QTableWidgetItem(source))
        
        # 严重程度
        severity = event_data.get('severity', '')
        severity_item = QTableWidgetItem(severity)
        
        # 设置严重程度颜色
        if severity == 'critical':
            severity_item.setBackground(QColor('#FFEBEE'))
            severity_item.setForeground(QColor('#F44336'))
        elif severity == 'warning':
            severity_item.setBackground(QColor('#FFF3E0'))
            severity_item.setForeground(QColor('#FF9800'))
        elif severity == 'info':
            severity_item.setBackground(QColor('#E3F2FD'))
            severity_item.setForeground(QColor('#2196F3'))
        
        self.setItem(row, 3, severity_item)
        
        # 消息
        data = event_data.get('data', {})
        message = str(data) if data else ''
        if len(message) > 100:
            message = message[:100] + '...'
        self.setItem(row, 4, QTableWidgetItem(message))
        
        # 滚动到底部
        self.scrollToBottom()
    
    def refresh_table(self):
        """刷新表格"""
        self.setRowCount(0)
        for event in self.events:
            self.add_event_row(event)


class PerformanceChart(QChartView):
    """性能图表"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_chart()
        
        # 数据系列
        self.cpu_series = QLineSeries()
        self.cpu_series.setName("CPU使用率")
        
        self.memory_series = QLineSeries()
        self.memory_series.setName("内存使用率")
        
        # 添加到图表
        self.chart.addSeries(self.cpu_series)
        self.chart.addSeries(self.memory_series)
        
        # 设置坐标轴
        self.setup_axes()
        
        # 数据点数量限制
        self.max_points = 60  # 显示最近60个数据点
    
    def setup_chart(self):
        """设置图表"""
        self.chart = QChart()
        self.chart.setTitle("系统性能监控")
        self.chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        
        self.setChart(self.chart)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
    
    def setup_axes(self):
        """设置坐标轴"""
        # Y轴（百分比）
        self.y_axis = QValueAxis()
        self.y_axis.setRange(0, 100)
        self.y_axis.setTitleText("使用率 (%)")
        self.chart.addAxis(self.y_axis, Qt.AlignmentFlag.AlignLeft)
        
        # X轴（时间）
        self.x_axis = QValueAxis()
        self.x_axis.setRange(0, self.max_points)
        self.x_axis.setTitleText("时间")
        self.chart.addAxis(self.x_axis, Qt.AlignmentFlag.AlignBottom)
        
        # 关联系列到坐标轴
        self.cpu_series.attachAxis(self.x_axis)
        self.cpu_series.attachAxis(self.y_axis)
        self.memory_series.attachAxis(self.x_axis)
        self.memory_series.attachAxis(self.y_axis)
    
    def add_data_point(self, cpu_percent: float, memory_percent: float):
        """添加数据点"""
        # 获取当前点数
        cpu_count = self.cpu_series.count()
        memory_count = self.memory_series.count()
        
        # 添加新数据点
        self.cpu_series.append(cpu_count, cpu_percent)
        self.memory_series.append(memory_count, memory_percent)
        
        # 限制数据点数量
        if cpu_count >= self.max_points:
            self.cpu_series.removePoints(0, cpu_count - self.max_points + 1)
            # 重新编号X坐标
            for i in range(self.cpu_series.count()):
                point = self.cpu_series.at(i)
                self.cpu_series.replace(i, i, point.y())
        
        if memory_count >= self.max_points:
            self.memory_series.removePoints(0, memory_count - self.max_points + 1)
            # 重新编号X坐标
            for i in range(self.memory_series.count()):
                point = self.memory_series.at(i)
                self.memory_series.replace(i, i, point.y())
        
        # 更新X轴范围
        current_count = max(self.cpu_series.count(), self.memory_series.count())
        if current_count > 10:
            self.x_axis.setRange(current_count - self.max_points, current_count)


class MonitoringDashboard(QWidget):
    """监控仪表板主界面"""
    
    # 信号定义
    alert_received = pyqtSignal(str, str, dict)  # level, message, data
    
    def __init__(self, logging_monitoring_service: LoggingMonitoringService, parent=None):
        super().__init__(parent)
        
        self.logging_service = logging_monitoring_service
        
        self.setup_ui()
        self.setup_connections()
        
        # 更新定时器
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_dashboard)
        self.update_timer.start(5000)  # 5秒更新一次
        
        logger.info("监控仪表板初始化完成")
    
    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout()
        
        # 创建选项卡
        self.tab_widget = QTabWidget()
        
        # 概览选项卡
        self.overview_tab = self.create_overview_tab()
        self.tab_widget.addTab(self.overview_tab, "概览")
        
        # 性能选项卡
        self.performance_tab = self.create_performance_tab()
        self.tab_widget.addTab(self.performance_tab, "性能")
        
        # 日志选项卡
        self.log_tab = self.create_log_tab()
        self.tab_widget.addTab(self.log_tab, "日志")
        
        # 事件选项卡
        self.event_tab = self.create_event_tab()
        self.tab_widget.addTab(self.event_tab, "事件")
        
        layout.addWidget(self.tab_widget)
        self.setLayout(layout)
    
    def create_overview_tab(self) -> QWidget:
        """创建概览选项卡"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 系统状态组
        status_group = QGroupBox("系统状态")
        status_layout = QVBoxLayout()
        
        self.system_health_indicator = StatusIndicator("系统健康", "unknown")
        self.performance_indicator = StatusIndicator("性能状态", "unknown")
        self.task_monitor_indicator = StatusIndicator("任务监控", "unknown")
        self.automation_indicator = StatusIndicator("自动化服务", "unknown")
        
        status_layout.addWidget(self.system_health_indicator)
        status_layout.addWidget(self.performance_indicator)
        status_layout.addWidget(self.task_monitor_indicator)
        status_layout.addWidget(self.automation_indicator)
        status_group.setLayout(status_layout)
        
        # 关键指标组
        metrics_group = QGroupBox("关键指标")
        metrics_layout = QGridLayout()
        
        self.cpu_metric = MetricsWidget("CPU使用率", "0", "%", "#FF9800")
        self.memory_metric = MetricsWidget("内存使用率", "0", "%", "#2196F3")
        self.active_tasks_metric = MetricsWidget("活动任务", "0", "个", "#4CAF50")
        self.error_count_metric = MetricsWidget("错误数量", "0", "个", "#F44336")
        
        metrics_layout.addWidget(self.cpu_metric, 0, 0)
        metrics_layout.addWidget(self.memory_metric, 0, 1)
        metrics_layout.addWidget(self.active_tasks_metric, 1, 0)
        metrics_layout.addWidget(self.error_count_metric, 1, 1)
        metrics_group.setLayout(metrics_layout)
        
        # 最近告警组
        alerts_group = QGroupBox("最近告警")
        alerts_layout = QVBoxLayout()
        
        self.alerts_text = QTextEdit()
        self.alerts_text.setMaximumHeight(150)
        self.alerts_text.setReadOnly(True)
        alerts_layout.addWidget(self.alerts_text)
        alerts_group.setLayout(alerts_layout)
        
        # 布局
        top_layout = QHBoxLayout()
        top_layout.addWidget(status_group)
        top_layout.addWidget(metrics_group)
        
        layout.addLayout(top_layout)
        layout.addWidget(alerts_group)
        layout.addStretch()
        
        widget.setLayout(layout)
        return widget
    
    def create_performance_tab(self) -> QWidget:
        """创建性能选项卡"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 性能图表
        self.performance_chart = PerformanceChart()
        layout.addWidget(self.performance_chart)
        
        # 性能详情
        details_group = QGroupBox("性能详情")
        details_layout = QGridLayout()
        
        # 详细指标
        self.disk_usage_metric = MetricsWidget("磁盘使用率", "0", "%", "#9C27B0")
        self.cache_hit_rate_metric = MetricsWidget("缓存命中率", "0", "%", "#00BCD4")
        self.automation_rate_metric = MetricsWidget("自动化频率", "0", "/min", "#FF5722")
        self.response_time_metric = MetricsWidget("响应时间", "0", "ms", "#795548")
        
        details_layout.addWidget(self.disk_usage_metric, 0, 0)
        details_layout.addWidget(self.cache_hit_rate_metric, 0, 1)
        details_layout.addWidget(self.automation_rate_metric, 0, 2)
        details_layout.addWidget(self.response_time_metric, 0, 3)
        
        details_group.setLayout(details_layout)
        layout.addWidget(details_group)
        
        widget.setLayout(layout)
        return widget
    
    def create_log_tab(self) -> QWidget:
        """创建日志选项卡"""
        self.log_viewer = LogViewer()
        return self.log_viewer
    
    def create_event_tab(self) -> QWidget:
        """创建事件选项卡"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 事件统计
        stats_group = QGroupBox("事件统计")
        stats_layout = QHBoxLayout()
        
        self.total_events_metric = MetricsWidget("总事件", "0", "个", "#607D8B")
        self.critical_events_metric = MetricsWidget("严重事件", "0", "个", "#F44336")
        self.warning_events_metric = MetricsWidget("警告事件", "0", "个", "#FF9800")
        self.info_events_metric = MetricsWidget("信息事件", "0", "个", "#2196F3")
        
        stats_layout.addWidget(self.total_events_metric)
        stats_layout.addWidget(self.critical_events_metric)
        stats_layout.addWidget(self.warning_events_metric)
        stats_layout.addWidget(self.info_events_metric)
        stats_layout.addStretch()
        
        stats_group.setLayout(stats_layout)
        
        # 事件列表
        self.event_viewer = EventViewer()
        
        layout.addWidget(stats_group)
        layout.addWidget(self.event_viewer)
        
        widget.setLayout(layout)
        return widget
    
    def setup_connections(self):
        """设置信号连接"""
        # 连接日志服务信号
        self.logging_service.log_entry_added.connect(self.on_log_entry_added)
        self.logging_service.monitoring_event_triggered.connect(self.on_monitoring_event)
        self.logging_service.system_metrics_updated.connect(self.on_system_metrics_updated)
        self.logging_service.alert_triggered.connect(self.on_alert_triggered)
    
    @pyqtSlot(dict)
    def on_log_entry_added(self, log_data: Dict[str, Any]):
        """处理新日志条目"""
        self.log_viewer.add_log_entry(log_data)
    
    @pyqtSlot(dict)
    def on_monitoring_event(self, event_data: Dict[str, Any]):
        """处理监控事件"""
        self.event_viewer.add_event(event_data)
    
    @pyqtSlot(dict)
    def on_system_metrics_updated(self, metrics_data: Dict[str, Any]):
        """处理系统指标更新"""
        # 更新性能图表
        cpu_percent = metrics_data.get('cpu_percent', 0)
        memory_percent = metrics_data.get('memory_percent', 0)
        self.performance_chart.add_data_point(cpu_percent, memory_percent)
    
    @pyqtSlot(str, str, dict)
    def on_alert_triggered(self, level: str, message: str, data: Dict[str, Any]):
        """处理告警"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        # 设置颜色
        color_map = {
            'critical': '#F44336',
            'error': '#F44336',
            'warning': '#FF9800',
            'info': '#2196F3'
        }
        color = color_map.get(level, '#000000')
        
        # 添加到告警显示
        alert_html = f"<span style='color: {color}'>[{timestamp}] [{level.upper()}] {message}</span><br>"
        self.alerts_text.insertHtml(alert_html)
        
        # 滚动到底部
        scrollbar = self.alerts_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
        # 发射信号
        self.alert_received.emit(level, message, data)
    
    def update_dashboard(self):
        """更新仪表板数据"""
        try:
            # 获取仪表板数据
            dashboard_data = self.logging_service.get_dashboard_data()
            
            # 更新系统健康状态
            system_health = dashboard_data.get('system_health', {})
            health_status = system_health.get('status', 'unknown')
            self.system_health_indicator.update_status(health_status)
            
            # 更新性能状态
            performance = dashboard_data.get('performance', {})
            current_metrics = performance.get('current_metrics')
            if current_metrics:
                cpu_percent = current_metrics.get('cpu_percent', 0)
                memory_percent = current_metrics.get('memory_percent', 0)
                
                # 更新CPU和内存指标
                self.cpu_metric.update_value(f"{cpu_percent:.1f}", "%")
                self.memory_metric.update_value(f"{memory_percent:.1f}", "%")
                
                # 根据使用率设置颜色
                if cpu_percent > 80:
                    self.cpu_metric.set_color("#F44336")
                elif cpu_percent > 60:
                    self.cpu_metric.set_color("#FF9800")
                else:
                    self.cpu_metric.set_color("#4CAF50")
                
                if memory_percent > 85:
                    self.memory_metric.set_color("#F44336")
                elif memory_percent > 70:
                    self.memory_metric.set_color("#FF9800")
                else:
                    self.memory_metric.set_color("#4CAF50")
            
            # 更新任务统计
            tasks = dashboard_data.get('tasks', {})
            active_tasks = tasks.get('running', 0)
            self.active_tasks_metric.update_value(str(active_tasks), "个")
            
            # 更新错误统计
            logs = dashboard_data.get('logs', {})
            error_count = logs.get('error', 0)
            self.error_count_metric.update_value(str(error_count), "个")
            
            # 更新事件统计
            events = dashboard_data.get('events', {})
            self.total_events_metric.update_value(str(events.get('total', 0)), "个")
            self.critical_events_metric.update_value(str(events.get('critical', 0)), "个")
            self.warning_events_metric.update_value(str(events.get('warning', 0)), "个")
            self.info_events_metric.update_value(str(events.get('info', 0)), "个")
            
            # 更新服务状态指示器
            self.performance_indicator.update_status("running" if self.logging_service.performance_monitor.monitoring_active else "stopped")
            self.task_monitor_indicator.update_status("running" if self.logging_service.task_monitor.is_monitoring else "stopped")
            self.automation_indicator.update_status("running")  # 假设自动化服务正在运行
            
        except Exception as e:
            logger.error(f"更新仪表板失败: {e}")
    
    def start_monitoring(self):
        """开始监控"""
        self.logging_service.start()
        logger.info("监控仪表板开始监控")
    
    def stop_monitoring(self):
        """停止监控"""
        self.update_timer.stop()
        self.logging_service.stop()
        logger.info("监控仪表板停止监控")