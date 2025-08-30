# -*- coding: utf-8 -*-
"""
主窗口 - 应用程序的主界面
"""

import sys
from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTabWidget, QMenuBar, QStatusBar, QToolBar,
    QMessageBox, QSplitter, QTextEdit,
    QLabel, QPushButton, QFrame
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt6.QtGui import QIcon, QFont, QPixmap, QAction

from loguru import logger
from ..core.config_manager import ConfigManager
from ..database.db_manager import DatabaseManager
from ..automation.automation_controller import TaskStatus
from ..automation.task_monitor import TaskMonitor
from ..automation.automation_controller import AutomationController


class MainWindow(QMainWindow):
    """主窗口类"""
    
    # 信号定义
    task_started = pyqtSignal(str)  # 任务开始信号
    task_stopped = pyqtSignal(str)  # 任务停止信号
    status_changed = pyqtSignal(str)  # 状态变化信号
    
    def __init__(self, config_manager: Optional[ConfigManager] = None, db_manager: Optional[DatabaseManager] = None):
        """初始化主窗口
        
        Args:
            config_manager: 配置管理器
            db_manager: 数据库管理器
        """
        super().__init__()
        
        # 如果没有传入管理器，则创建默认实例
        if config_manager is None:
            from ..core.config_manager import ConfigManager
            config_manager = ConfigManager()
        if db_manager is None:
            from ..database.db_manager import DatabaseManager
            db_manager = DatabaseManager()
            db_manager.initialize_database()
        
        self.config_manager = config_manager
        self.db_manager = db_manager
        
        # 创建自动化控制器
        self.automation_controller = AutomationController(
            config_manager=self.config_manager,
            db_manager=self.db_manager
        )
        
        # 创建任务监控器
        self.task_monitor = TaskMonitor(
            db_manager=self.db_manager,
            automation_controller=self.automation_controller
        )
        
        # 窗口状态
        self.current_task_id: Optional[str] = None
        self.is_automation_running = False
        
        # 初始化UI
        self._init_ui()
        self._init_menu_bar()
        self._init_tool_bar()
        self._init_status_bar()
        self._connect_signals()
        
        # 状态更新定时器
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self._update_status)
        self.status_timer.start(1000)  # 每秒更新一次
        
        logger.info("主窗口初始化完成")
    
    def _init_ui(self):
        """初始化用户界面"""
        # 设置窗口属性
        self.setWindowTitle("崩坏星穹铁道自动化助手 v1.0.0")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)
        
        # 设置窗口图标（如果存在）
        icon_path = Path(__file__).parent.parent.parent / "assets" / "icon.ico"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # 创建分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # 左侧面板 - 功能选择和控制
        left_panel = self._create_left_panel()
        splitter.addWidget(left_panel)
        
        # 右侧面板 - 主要工作区域
        right_panel = self._create_right_panel()
        splitter.addWidget(right_panel)
        
        # 设置分割器比例
        splitter.setSizes([300, 900])
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
    
    def _create_left_panel(self) -> QWidget:
        """创建左侧控制面板"""
        panel = QFrame()
        panel.setFrameStyle(QFrame.Shape.StyledPanel)
        panel.setMaximumWidth(350)
        panel.setMinimumWidth(280)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # 标题
        title_label = QLabel("控制面板")
        title_label.setFont(QFont("Microsoft YaHei", 12, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # 快速操作按钮
        self.start_btn = QPushButton("开始自动化")
        self.start_btn.setMinimumHeight(40)
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.start_btn.clicked.connect(self._on_start_automation)
        layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("停止自动化")
        self.stop_btn.setMinimumHeight(40)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
            QPushButton:pressed {
                background-color: #c1170a;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.stop_btn.clicked.connect(self._on_stop_automation)
        layout.addWidget(self.stop_btn)
        
        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line)
        
        # 状态信息
        status_label = QLabel("状态信息")
        status_label.setFont(QFont("Microsoft YaHei", 10, QFont.Weight.Bold))
        layout.addWidget(status_label)
        
        self.status_text = QTextEdit()
        self.status_text.setMaximumHeight(200)
        self.status_text.setReadOnly(True)
        self.status_text.setStyleSheet("""
            QTextEdit {
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                border-radius: 3px;
                padding: 5px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 9pt;
            }
        """)
        layout.addWidget(self.status_text)
        
        # 弹性空间
        layout.addStretch()
        
        return panel
    
    def _create_right_panel(self) -> QWidget:
        """创建右侧主工作区"""
        # 创建标签页控件
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.North)
        self.tab_widget.setMovable(True)
        
        # 任务管理标签页
        task_tab = self._create_task_tab()
        self.tab_widget.addTab(task_tab, "任务管理")
        
        # 游戏设置标签页
        game_tab = self._create_game_tab()
        self.tab_widget.addTab(game_tab, "游戏设置")
        
        # 自动化配置标签页
        automation_tab = self._create_automation_tab()
        self.tab_widget.addTab(automation_tab, "自动化配置")
        
        # 日志查看标签页
        log_tab = self._create_log_tab()
        self.tab_widget.addTab(log_tab, "执行日志")
        
        return self.tab_widget
    
    def _create_task_tab(self) -> QWidget:
        """创建任务管理标签页"""
        from .task_creation_widget import TaskCreationWidget
        from .task_list_widget import TaskListWidget
        from ..core.task_manager import TaskManager
        
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # 创建任务管理器实例
        self.task_manager = TaskManager(self.db_manager)
        
        # 创建水平分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)
        
        # 左侧：任务列表
        self.task_list_widget = TaskListWidget(self.task_manager)
        splitter.addWidget(self.task_list_widget)
        
        # 右侧：任务创建/编辑
        self.task_creation_widget = TaskCreationWidget(self.task_manager)
        splitter.addWidget(self.task_creation_widget)
        
        # 设置分割器比例
        splitter.setSizes([700, 400])
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 0)
        
        # 连接信号
        self._connect_task_signals()
        
        return widget
    
    def _create_game_tab(self) -> QWidget:
        """创建游戏设置标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 占位符内容
        label = QLabel("游戏设置")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setFont(QFont("Microsoft YaHei", 16))
        layout.addWidget(label)
        
        placeholder = QLabel("此处将显示游戏路径设置、分辨率配置、窗口检测等功能")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setStyleSheet("color: #666; font-size: 12px;")
        layout.addWidget(placeholder)
        
        return widget
    
    def _create_automation_tab(self) -> QWidget:
        """创建自动化配置标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 占位符内容
        label = QLabel("自动化配置")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setFont(QFont("Microsoft YaHei", 16))
        layout.addWidget(label)
        
        placeholder = QLabel("此处将显示自动化参数设置、安全选项、检测阈值等配置")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setStyleSheet("color: #666; font-size: 12px;")
        layout.addWidget(placeholder)
        
        return widget
    
    def _create_log_tab(self) -> QWidget:
        """创建日志查看标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 日志显示区域
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #333;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 9pt;
                line-height: 1.2;
            }
        """)
        layout.addWidget(self.log_text)
        
        return widget
    
    def _init_menu_bar(self):
        """初始化菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件")
        
        # 导入配置
        import_action = QAction("导入配置", self)
        import_action.triggered.connect(self._import_config)
        file_menu.addAction(import_action)
        
        # 导出配置
        export_action = QAction("导出配置", self)
        export_action.triggered.connect(self._export_config)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        # 退出
        exit_action = QAction("退出", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 工具菜单
        tools_menu = menubar.addMenu("工具")
        
        # 数据库管理
        db_action = QAction("数据库管理", self)
        db_action.triggered.connect(self._open_db_manager)
        tools_menu.addAction(db_action)
        
        # 日志管理
        log_action = QAction("日志管理", self)
        log_action.triggered.connect(self._open_log_manager)
        tools_menu.addAction(log_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助")
        
        # 关于
        about_action = QAction("关于", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _init_tool_bar(self):
        """初始化工具栏"""
        toolbar = self.addToolBar("主工具栏")
        toolbar.setMovable(False)
        
        # 开始按钮
        start_action = QAction("开始", self)
        start_action.triggered.connect(self._on_start_automation)
        toolbar.addAction(start_action)
        
        # 停止按钮
        stop_action = QAction("停止", self)
        stop_action.triggered.connect(self._on_stop_automation)
        toolbar.addAction(stop_action)
        
        toolbar.addSeparator()
        
        # 设置按钮
        settings_action = QAction("设置", self)
        settings_action.triggered.connect(self._open_settings)
        toolbar.addAction(settings_action)
    
    def _init_status_bar(self):
        """初始化状态栏"""
        self.status_bar = self.statusBar()
        
        # 状态标签
        self.status_label = QLabel("就绪")
        self.status_bar.addWidget(self.status_label)
        
        # 任务信息标签
        self.task_label = QLabel("无活动任务")
        self.status_bar.addPermanentWidget(self.task_label)
        
        # 时间标签
        self.time_label = QLabel()
        self.status_bar.addPermanentWidget(self.time_label)
    
    def _connect_signals(self):
        """连接信号和槽"""
        self.task_started.connect(self._on_task_started)
        self.task_stopped.connect(self._on_task_stopped)
        self.status_changed.connect(self._on_status_changed)
        
        # 连接任务监控器信号
        self.task_monitor.task_status_changed.connect(self._on_monitor_task_status_changed)
        self.task_monitor.task_progress_updated.connect(self._on_monitor_task_progress_updated)
        self.task_monitor.task_message_updated.connect(self._on_monitor_task_message_updated)
        self.task_monitor.task_completed.connect(self._on_monitor_task_completed)
    
    def _connect_task_signals(self):
        """连接任务管理相关信号"""
        if hasattr(self, 'task_list_widget') and hasattr(self, 'task_creation_widget'):
            # 任务列表信号
            self.task_list_widget.task_edit_requested.connect(self._on_task_edit_requested)
            self.task_list_widget.task_delete_requested.connect(self._on_task_delete_requested)
            self.task_list_widget.task_start_requested.connect(self._on_task_start_requested)
            self.task_list_widget.task_stop_requested.connect(self._on_task_stop_requested)
            
            # 任务创建信号
            self.task_creation_widget.task_created.connect(self._on_task_created)
            self.task_creation_widget.task_creation_failed.connect(self._on_task_creation_failed)
    
    def _on_task_edit_requested(self, task_id: str):
        """处理任务编辑请求"""
        try:
            task = self.task_manager.get_task(task_id)
            if task:
                # 在任务创建组件中加载任务配置进行编辑
                self.task_creation_widget.load_task_for_edit(task)
                logger.info(f"开始编辑任务: {task_id}")
            else:
                QMessageBox.warning(self, "错误", "未找到指定的任务")
        except Exception as e:
            logger.error(f"加载任务编辑失败: {e}")
            QMessageBox.critical(self, "编辑失败", f"加载任务编辑失败：{str(e)}")
    
    def _on_task_delete_requested(self, task_id: str):
        """处理任务删除请求"""
        try:
            success = self.task_manager.delete_task(task_id)
            if success:
                QMessageBox.information(self, "删除成功", "任务已成功删除")
                # 刷新任务列表
                self.task_list_widget.refresh_task_list()
                logger.info(f"任务删除成功: {task_id}")
            else:
                QMessageBox.warning(self, "删除失败", "任务删除失败")
        except Exception as e:
            logger.error(f"任务删除失败: {e}")
            QMessageBox.critical(self, "删除失败", f"任务删除失败：{str(e)}")
    
    def _on_task_start_requested(self, task_id: str):
        """处理任务启动请求"""
        try:
            # 这里应该调用自动化控制器来启动任务
            # 暂时只更新状态
            self.task_manager.update_task(task_id, status=TaskStatus.RUNNING)
            self.task_list_widget.refresh_task_list()
            self.status_label.setText(f"任务 {task_id} 已启动")
            logger.info(f"任务启动: {task_id}")
        except Exception as e:
            logger.error(f"任务启动失败: {e}")
            QMessageBox.critical(self, "启动失败", f"任务启动失败：{str(e)}")
    
    def _on_task_stop_requested(self, task_id: str):
        """处理任务停止请求"""
        try:
            # 这里应该调用自动化控制器来停止任务
            # 暂时只更新状态
            self.task_manager.update_task(task_id, status=TaskStatus.STOPPED)
            self.task_list_widget.refresh_task_list()
            self.status_label.setText(f"任务 {task_id} 已停止")
            logger.info(f"任务停止: {task_id}")
        except Exception as e:
            logger.error(f"任务停止失败: {e}")
            QMessageBox.critical(self, "停止失败", f"任务停止失败：{str(e)}")
    
    def _on_task_created(self, task_id: str):
        """处理任务创建成功"""
        QMessageBox.information(self, "创建成功", f"任务创建成功！\n任务ID: {task_id}")
        # 刷新任务列表
        self.task_list_widget.refresh_task_list()
        # 选择新创建的任务
        self.task_list_widget.select_task(task_id)
        logger.info(f"任务创建成功: {task_id}")
    
    def _on_task_creation_failed(self, error_message: str):
        """处理任务创建失败"""
        QMessageBox.critical(self, "创建失败", f"任务创建失败：{error_message}")
        logger.error(f"任务创建失败: {error_message}")
    
    def _update_status(self):
        """更新状态信息"""
        from datetime import datetime
        
        # 更新时间
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_label.setText(current_time)
        
        # 更新状态文本
        if self.is_automation_running:
            self.status_text.append(f"[{current_time}] 自动化运行中...")
            # 限制状态文本长度
            if self.status_text.document().lineCount() > 50:
                cursor = self.status_text.textCursor()
                cursor.movePosition(cursor.MoveOperation.Start)
                cursor.movePosition(cursor.MoveOperation.Down, cursor.MoveMode.KeepAnchor, 10)
                cursor.removeSelectedText()
    
    def _on_start_automation(self):
        """开始自动化"""
        if self.is_automation_running:
            return
        
        # 创建新任务
        task_id = self.db_manager.create_task(
            user_id="default_user",
            task_name="自动化任务",
            task_type="automation"
        )
        
        self.current_task_id = task_id
        self.is_automation_running = True
        
        # 启动任务监控器
        self.task_monitor.start_monitoring()
        
        # 更新UI状态
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        
        # 发送信号
        self.task_started.emit(task_id)
        
        logger.info(f"开始自动化任务: {task_id}")
    
    def _on_stop_automation(self):
        """停止自动化"""
        if not self.is_automation_running:
            return
        
        # 停止任务监控器
        self.task_monitor.stop_monitoring()
        
        if self.current_task_id:
            # 更新任务状态
            self.db_manager.update_task_status(self.current_task_id, "stopped")
            
            # 发送信号
            self.task_stopped.emit(self.current_task_id)
            
            logger.info(f"停止自动化任务: {self.current_task_id}")
        
        self.is_automation_running = False
        self.current_task_id = None
        
        # 更新UI状态
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
    
    def _on_task_started(self, task_id: str):
        """任务开始处理"""
        self.status_label.setText("运行中")
        self.task_label.setText(f"任务: {task_id[:8]}...")
        self.status_changed.emit("任务已开始")
    
    def _on_task_stopped(self, task_id: str):
        """任务停止处理"""
        self.status_label.setText("就绪")
        self.task_label.setText("无活动任务")
        self.status_changed.emit("任务已停止")
    
    def _on_status_changed(self, message: str):
        """状态变化处理"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.status_text.append(f"[{timestamp}] {message}")
    
    def _on_monitor_task_status_changed(self, task_id: str, status: str):
        """处理任务监控器的状态变化信号"""
        self.status_changed.emit(f"任务 {task_id[:8]}... 状态变更为: {status}")
        # 更新任务列表中的状态显示
        if hasattr(self, 'task_list_widget'):
            from ..automation.automation_controller import TaskStatus
            try:
                task_status = TaskStatus(status)
                self.task_list_widget.update_task_status(task_id, task_status)
            except ValueError:
                logger.warning(f"未知的任务状态: {status}")
                # 刷新整个任务列表作为备选方案
                self.task_list_widget.refresh_task_list()
    
    def _on_monitor_task_progress_updated(self, task_id: str, progress: int, message: str):
        """处理任务进度更新信号"""
        logger.debug(f"任务进度更新: {task_id} - {progress}% - {message}")
        self.status_changed.emit(f"任务 {task_id[:8]}... 进度: {progress}%")
        
        # 更新任务列表中的进度显示
        if hasattr(self, 'task_list_widget'):
            self.task_list_widget.update_task_progress(task_id, progress, message)
    
    def _on_monitor_task_message_updated(self, task_id: str, message: str):
        """处理任务监控器的消息更新信号"""
        self.status_changed.emit(f"任务 {task_id[:8]}...: {message}")
    
    def _on_monitor_task_completed(self, task_id: str, success: bool, message: str):
        """处理任务监控器的任务完成信号"""
        status_msg = "成功" if success else "失败"
        self.status_changed.emit(f"任务 {task_id[:8]}... 执行{status_msg}: {message}")
        
        # 如果是当前运行的任务，更新UI状态
        if task_id == self.current_task_id:
            self.is_automation_running = False
            self.current_task_id = None
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.status_label.setText("就绪")
            self.task_label.setText("无活动任务")
        
        # 刷新任务列表
        if hasattr(self, 'task_list_widget'):
            self.task_list_widget.refresh_task_list()
    
    def _import_config(self):
        """导入配置"""
        QMessageBox.information(self, "提示", "导入配置功能待实现")
    
    def _export_config(self):
        """导出配置"""
        QMessageBox.information(self, "提示", "导出配置功能待实现")
    
    def _open_db_manager(self):
        """打开数据库管理"""
        QMessageBox.information(self, "提示", "数据库管理功能待实现")
    
    def _open_log_manager(self):
        """打开日志管理"""
        QMessageBox.information(self, "提示", "日志管理功能待实现")
    
    def _open_settings(self):
        """打开设置"""
        QMessageBox.information(self, "提示", "设置功能待实现")
    
    def _show_about(self):
        """显示关于对话框"""
        QMessageBox.about(self, "关于", 
            "崩坏星穹铁道自动化助手 v1.0.0\n\n"
            "一个功能完整的游戏自动化工具\n\n"
            "基于 Python + PyQt6 开发")
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        if self.is_automation_running:
            reply = QMessageBox.question(
                self, "确认退出", 
                "自动化任务正在运行，确定要退出吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self._on_stop_automation()
                event.accept()
            else:
                event.ignore()
                return
        
        # 确保任务监控器被停止
        if hasattr(self, 'task_monitor'):
            self.task_monitor.stop_monitoring()
        
        event.accept()
        logger.info("主窗口关闭")