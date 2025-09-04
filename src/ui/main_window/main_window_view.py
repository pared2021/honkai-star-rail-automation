# -*- coding: utf-8 -*-
"""
主窗口视图 - MVP模式的View层实现
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QAction, QColor, QFont, QIcon, QPalette
from ...gui.common.gui_components import (
    BaseWidget,
    QCheckBox,
    QComboBox,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenu,
    QMenuBar,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QSplitter,
    QStatusBar,
    QTabWidget,
    QTextEdit,
    QToolBar,
    QVBoxLayout,
    QWidget,
)
from loguru import logger

from src.ui.mvp.base_view import BaseView

# from src.ui.monitoring_dashboard import (
#     MonitoringDashboard, MetricsWidget, StatusIndicator
# )


class MainWindowView(QMainWindow, BaseWidget, BaseView):
    """
    主窗口视图类 - 负责主窗口的界面展示和用户交互

    采用MVP模式，只负责界面逻辑，不包含业务逻辑
    """

    # 用户交互信号
    start_automation_requested = pyqtSignal()
    stop_automation_requested = pyqtSignal()
    pause_automation_requested = pyqtSignal()
    settings_requested = pyqtSignal()
    task_management_requested = pyqtSignal()
    monitoring_requested = pyqtSignal()
    about_requested = pyqtSignal()
    exit_requested = pyqtSignal()

    # 任务操作信号
    create_task_requested = pyqtSignal()
    edit_task_requested = pyqtSignal(int)  # task_id
    delete_task_requested = pyqtSignal(int)  # task_id
    execute_task_requested = pyqtSignal(int)  # task_id

    # 配置变更信号
    config_changed = pyqtSignal(str, Any)  # key, value

    def __init__(self, parent=None):
        super().__init__(parent)

        # 界面组件
        self.central_widget = None
        self.monitoring_dashboard = None
        self.status_bar = None
        self.toolbar = None

        # 控制按钮
        self.start_btn = None
        self.stop_btn = None
        self.pause_btn = None

        # 状态指示器
        self.automation_status_indicator = None
        self.system_status_indicator = None

        # 快速统计指标
        self.active_tasks_metric = None
        self.completed_tasks_metric = None
        self.error_count_metric = None
        self.uptime_metric = None

        # 初始化界面
        self._setup_ui()
        self.setup_connections()

        logger.info("主窗口视图初始化完成")

    def _update_field_display(self, field_name: str, value: Any):
        """更新特定字段的显示

        Args:
            field_name: 字段名
            value: 新值
        """
        try:
            if field_name == "automation_status":
                self._update_automation_status(value)
            elif field_name == "system_status":
                self._update_system_status(value)
            elif field_name == "active_tasks":
                if self.active_tasks_metric:
                    self.active_tasks_metric.setText(f"活跃任务: {value}")
            elif field_name == "completed_tasks":
                if self.completed_tasks_metric:
                    self.completed_tasks_metric.setText(f"已完成: {value}")
            elif field_name == "error_count":
                if self.error_count_metric:
                    self.error_count_metric.setText(f"错误数: {value}")
            elif field_name == "uptime":
                if self.uptime_metric:
                    self.uptime_metric.setText(f"运行时间: {value}")
            else:
                logger.warning(f"未知字段: {field_name}")
        except Exception as e:
            logger.error(f"更新字段显示失败: {field_name}, 错误: {e}")

    def connect_signals(self):
        """连接信号槽"""
        # 这里可以连接内部信号
        pass

    def _update_automation_status(self, status: str):
        """更新自动化状态"""
        if self.automation_status_indicator:
            self.automation_status_indicator.setText(f"自动化状态: {status}")

    def _update_system_status(self, status: str):
        """更新系统状态"""
        if self.system_status_indicator:
            self.system_status_indicator.setText(f"系统状态: {status}")

    def _setup_ui(self):
        """设置用户界面"""
        self.setWindowTitle("星铁自动化助手")
        self.setMinimumSize(1200, 800)

        # 设置应用图标
        # self.setWindowIcon(QIcon("resources/icons/app.ico"))

        # 创建菜单栏
        self.create_menu_bar()

        # 创建工具栏
        self.create_toolbar()

        # 创建中央部件
        self.create_central_widget()

        # 创建状态栏
        self.create_status_bar()

        # 设置样式
        self.setup_styles()

    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()

        # 文件菜单
        file_menu = menubar.addMenu("文件(&F)")

        settings_action = QAction("设置(&S)", self)
        settings_action.setShortcut("Ctrl+S")
        settings_action.triggered.connect(self.settings_requested.emit)
        file_menu.addAction(settings_action)

        file_menu.addSeparator()

        exit_action = QAction("退出(&X)", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.exit_requested.emit)
        file_menu.addAction(exit_action)

        # 任务菜单
        task_menu = menubar.addMenu("任务(&T)")

        task_mgmt_action = QAction("任务管理(&M)", self)
        task_mgmt_action.setShortcut("Ctrl+T")
        task_mgmt_action.triggered.connect(self.task_management_requested.emit)
        task_menu.addAction(task_mgmt_action)

        task_menu.addSeparator()

        create_task_action = QAction("新建任务(&N)", self)
        create_task_action.setShortcut("Ctrl+N")
        create_task_action.triggered.connect(self.create_task_requested.emit)
        task_menu.addAction(create_task_action)

        # 监控菜单
        monitor_menu = menubar.addMenu("监控(&M)")

        monitoring_action = QAction("监控面板(&D)", self)
        monitoring_action.setShortcut("Ctrl+M")
        monitoring_action.triggered.connect(self.monitoring_requested.emit)
        monitor_menu.addAction(monitoring_action)

        # 帮助菜单
        help_menu = menubar.addMenu("帮助(&H)")

        about_action = QAction("关于(&A)", self)
        about_action.triggered.connect(self.about_requested.emit)
        help_menu.addAction(about_action)

    def create_toolbar(self):
        """创建工具栏"""
        self.toolbar = self.addToolBar("主工具栏")
        self.toolbar.setMovable(False)

        # 自动化控制按钮
        self.start_btn = QPushButton("开始自动化")
        self.start_btn.setStyleSheet(
            """
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
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """
        )
        self.start_btn.clicked.connect(self.start_automation_requested.emit)

        self.pause_btn = QPushButton("暂停")
        self.pause_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e68900;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """
        )
        self.pause_btn.clicked.connect(self.pause_automation_requested.emit)
        self.pause_btn.setEnabled(False)

        self.stop_btn = QPushButton("停止")
        self.stop_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #F44336;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """
        )
        self.stop_btn.clicked.connect(self.stop_automation_requested.emit)
        self.stop_btn.setEnabled(False)

        # 添加到工具栏
        self.toolbar.addWidget(self.start_btn)
        self.toolbar.addWidget(self.pause_btn)
        self.toolbar.addWidget(self.stop_btn)

        self.toolbar.addSeparator()

        # 快速访问按钮
        task_mgmt_btn = QPushButton("任务管理")
        task_mgmt_btn.clicked.connect(self.task_management_requested.emit)
        self.toolbar.addWidget(task_mgmt_btn)

        settings_btn = QPushButton("设置")
        settings_btn.clicked.connect(self.settings_requested.emit)
        self.toolbar.addWidget(settings_btn)

    def create_central_widget(self):
        """创建中央部件"""
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        layout = QVBoxLayout()

        # 创建主要内容区域
        main_splitter = self.create_splitter(Qt.Orientation.Horizontal)

        # 左侧控制面板
        control_panel = self.create_control_panel()
        main_splitter.addWidget(control_panel)

        # 右侧监控面板
        # self.monitoring_dashboard = MonitoringDashboard()
        # main_splitter.addWidget(self.monitoring_dashboard)

        # 临时替代监控面板
        temp_widget = QWidget()
        temp_layout = QVBoxLayout()
        temp_label = QLabel("监控面板 (暂时禁用)")
        temp_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        temp_layout.addWidget(temp_label)
        temp_widget.setLayout(temp_layout)
        main_splitter.addWidget(temp_widget)

        # 设置分割比例
        main_splitter.setSizes([300, 900])

        layout.addWidget(main_splitter)
        self.central_widget.setLayout(layout)

    def create_control_panel(self) -> QWidget:
        """创建控制面板"""
        panel = QWidget()
        layout = self.create_vbox_layout()

        # 系统状态组
        status_group = QGroupBox("系统状态")
        status_layout = QVBoxLayout()

        # self.automation_status_indicator = StatusIndicator("自动化服务", "stopped")
        # self.system_status_indicator = StatusIndicator("系统健康", "good")

        # 临时替代状态指示器
        temp_status_label = QLabel("状态指示器 (暂时禁用)")
        status_layout.addWidget(temp_status_label)
        # status_layout.addWidget(self.automation_status_indicator)
        # status_layout.addWidget(self.system_status_indicator)
        status_group.setLayout(status_layout)

        # 快速统计组
        stats_group = QGroupBox("快速统计")
        stats_layout = QGridLayout()

        # self.active_tasks_metric = MetricsWidget("活跃任务", "0", "个", "#2196F3")
        # self.completed_tasks_metric = MetricsWidget("已完成", "0", "个", "#4CAF50")
        # self.error_count_metric = MetricsWidget("错误数", "0", "个", "#F44336")
        # self.uptime_metric = MetricsWidget("运行时间", "0", "分钟", "#9C27B0")

        # 临时替代指标组件
        temp_metrics_label = QLabel("指标组件 (暂时禁用)")
        stats_layout.addWidget(temp_metrics_label, 0, 0, 2, 2)
        # stats_layout.addWidget(self.active_tasks_metric, 0, 0)
        # stats_layout.addWidget(self.completed_tasks_metric, 0, 1)
        # stats_layout.addWidget(self.error_count_metric, 1, 0)
        # stats_layout.addWidget(self.uptime_metric, 1, 1)

        stats_group.setLayout(stats_layout)

        # 快速操作组
        actions_group = QGroupBox("快速操作")
        actions_layout = QVBoxLayout()

        create_task_btn = QPushButton("新建任务")
        create_task_btn.clicked.connect(self.create_task_requested.emit)

        task_mgmt_btn = QPushButton("任务管理")
        task_mgmt_btn.clicked.connect(self.task_management_requested.emit)

        monitoring_btn = QPushButton("监控详情")
        monitoring_btn.clicked.connect(self.monitoring_requested.emit)

        actions_layout.addWidget(create_task_btn)
        actions_layout.addWidget(task_mgmt_btn)
        actions_layout.addWidget(monitoring_btn)
        actions_layout.addStretch()

        actions_group.setLayout(actions_layout)

        # 添加到主布局
        layout.addWidget(status_group)
        layout.addWidget(stats_group)
        layout.addWidget(actions_group)
        layout.addStretch()

        panel.setLayout(layout)
        return panel

    def create_status_bar(self):
        """创建状态栏"""
        self.status_bar = self.statusBar()

        # 默认状态消息
        self.status_bar.showMessage("就绪")

        # 添加永久部件
        self.status_bar.addPermanentWidget(QLabel("星铁自动化助手 v1.0"))

    def setup_styles(self):
        """设置样式"""
        self.setStyleSheet(
            """
            QMainWindow {
                background-color: #f5f5f5;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 5px;
                margin-top: 1ex;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QPushButton {
                background-color: #ffffff;
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 6px 12px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #e6e6e6;
            }
            QPushButton:pressed {
                background-color: #d4d4d4;
            }
        """
        )

    def setup_connections(self):
        """设置内部信号连接"""
        # 监控面板的信号连接
        if self.monitoring_dashboard:
            self.monitoring_dashboard.alert_received.connect(self.on_alert_received)

    # === 界面更新方法 ===

    def update_automation_status(self, status: str):
        """更新自动化状态"""
        if self.automation_status_indicator:
            self.automation_status_indicator.update_status(status)

        # 更新按钮状态
        if status == "running":
            self.start_btn.setEnabled(False)
            self.pause_btn.setEnabled(True)
            self.stop_btn.setEnabled(True)
        elif status == "paused":
            self.start_btn.setEnabled(True)
            self.pause_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
        else:  # stopped
            self.start_btn.setEnabled(True)
            self.pause_btn.setEnabled(False)
            self.stop_btn.setEnabled(False)

    def update_system_status(self, status: str):
        """更新系统状态"""
        if self.system_status_indicator:
            self.system_status_indicator.update_status(status)

    def update_task_statistics(self, stats: Dict[str, Any]):
        """更新任务统计"""
        if self.active_tasks_metric:
            self.active_tasks_metric.update_value(str(stats.get("active", 0)), "个")

        if self.completed_tasks_metric:
            self.completed_tasks_metric.update_value(
                str(stats.get("completed", 0)), "个"
            )

        if self.error_count_metric:
            self.error_count_metric.update_value(str(stats.get("errors", 0)), "个")

    def update_uptime(self, uptime_minutes: int):
        """更新运行时间"""
        if self.uptime_metric:
            if uptime_minutes < 60:
                self.uptime_metric.update_value(str(uptime_minutes), "分钟")
            else:
                hours = uptime_minutes // 60
                minutes = uptime_minutes % 60
                self.uptime_metric.update_value(f"{hours}:{minutes:02d}", "小时")

    def show_status_message(self, message: str, timeout: int = 0):
        """显示状态消息"""
        if self.status_bar:
            self.status_bar.showMessage(message, timeout)

    def show_error_message(self, title: str, message: str):
        """显示错误消息"""
        from PyQt6.QtWidgets import QMessageBox

        QMessageBox.critical(self, title, message)

    def show_info_message(self, title: str, message: str):
        """显示信息消息"""
        from PyQt6.QtWidgets import QMessageBox

        QMessageBox.information(self, title, message)

    def show_warning_message(self, title: str, message: str):
        """显示警告消息"""
        from PyQt6.QtWidgets import QMessageBox

        QMessageBox.warning(self, title, message)

    def confirm_action(self, title: str, message: str) -> bool:
        """确认操作"""
        from PyQt6.QtWidgets import QMessageBox

        reply = QMessageBox.question(
            self,
            title,
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        return reply == QMessageBox.StandardButton.Yes

    # === 事件处理方法 ===

    def on_alert_received(self, level: str, message: str, data: Dict[str, Any]):
        """处理告警"""
        # 在状态栏显示告警
        self.show_status_message(f"[{level.upper()}] {message}", 5000)

        # 严重告警弹窗提示
        if level in ["critical", "error"]:
            self.show_error_message("系统告警", message)

    def closeEvent(self, event):
        """窗口关闭事件"""
        if self.confirm_action("确认退出", "确定要退出星铁自动化助手吗？"):
            self.exit_requested.emit()
            event.accept()
        else:
            event.ignore()

    # === BaseView接口实现 ===

    def show_loading(self, message: str = "加载中..."):
        """显示加载状态"""
        self.show_status_message(message)

    def hide_loading(self):
        """隐藏加载状态"""
        self.show_status_message("就绪")

    def show_error(self, error: str):
        """显示错误"""
        self.show_error_message("错误", error)

    def update_data(self, data: Dict[str, Any]):
        """更新数据显示"""
        # 更新自动化状态
        if "automation_status" in data:
            self.update_automation_status(data["automation_status"])

        # 更新系统状态
        if "system_status" in data:
            self.update_system_status(data["system_status"])

        # 更新任务统计
        if "task_statistics" in data:
            self.update_task_statistics(data["task_statistics"])

        # 更新运行时间
        if "uptime_minutes" in data:
            self.update_uptime(data["uptime_minutes"])

    def set_enabled(self, enabled: bool):
        """设置启用状态"""
        self.setEnabled(enabled)

    def get_user_input(self, prompt: str) -> Optional[str]:
        """获取用户输入"""
        from PyQt6.QtWidgets import QInputDialog

        text, ok = QInputDialog.getText(self, "输入", prompt)
        return text if ok else None
