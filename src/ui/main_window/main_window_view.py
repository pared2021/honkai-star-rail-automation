"""主窗口View层

负责主窗口UI界面的展示和用户交互
"""

from typing import Optional, Dict, Any, List
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QTabWidget, QPushButton, QTextEdit, QLabel, QMenuBar, QMenu,
    QToolBar, QStatusBar, QMessageBox, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QIcon, QAction, QFont
import logging

from ...core.interfaces.base_view import BaseView
from ..task_list.task_list_mvp import TaskListMVP
from ..task_creation.task_creation_mvp import TaskCreationMVP
from ..game_settings import GameSettingsMVP as GameSettingsWidget
from ..automation_settings import AutomationSettingsMVP as AutomationSettingsWidget
from ..log_viewer import LogViewerMVP as LogViewerWidget
from ..task_execution_history import TaskExecutionHistoryMVP as TaskExecutionHistoryDialog

logger = logging.getLogger(__name__)


class MainWindowView(QMainWindow, BaseView):
    """主窗口View层
    
    负责主窗口UI界面的展示和用户交互
    """
    
    # 用户交互信号
    start_automation_requested = pyqtSignal()  # 开始自动化请求
    stop_automation_requested = pyqtSignal()  # 停止自动化请求
    tab_changed = pyqtSignal(int)  # 标签页切换 (tab_index)
    window_state_changed = pyqtSignal(dict)  # 窗口状态变化 (state_dict)
    
    # 菜单动作信号
    import_config_requested = pyqtSignal()  # 导入配置请求
    export_config_requested = pyqtSignal()  # 导出配置请求
    show_execution_history_requested = pyqtSignal()  # 显示执行历史请求
    database_management_requested = pyqtSignal()  # 数据库管理请求
    log_management_requested = pyqtSignal()  # 日志管理请求
    settings_requested = pyqtSignal()  # 设置请求
    about_requested = pyqtSignal()  # 关于请求
    
    # 设置变更信号
    game_settings_changed = pyqtSignal(dict)  # 游戏设置变更 (settings_dict)
    automation_settings_changed = pyqtSignal(dict)  # 自动化设置变更 (settings_dict)
    
    # 日志操作信号
    log_exported = pyqtSignal(str)  # 日志导出 (file_path)
    log_cleared = pyqtSignal()  # 日志清空
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        # UI组件
        self.central_widget: Optional[QWidget] = None
        self.main_layout: Optional[QVBoxLayout] = None
        self.main_splitter: Optional[QSplitter] = None
        
        # 左侧控制面板
        self.left_panel: Optional[QWidget] = None
        self.start_button: Optional[QPushButton] = None
        self.stop_button: Optional[QPushButton] = None
        self.status_text: Optional[QTextEdit] = None
        
        # 右侧标签页
        self.tab_widget: Optional[QTabWidget] = None
        self.task_list_mvp: Optional[TaskListMVP] = None
        self.task_creation_mvp: Optional[TaskCreationMVP] = None
        self.game_settings_widget: Optional[GameSettingsWidget] = None
        self.automation_settings_widget: Optional[AutomationSettingsWidget] = None
        self.log_viewer_widget: Optional[LogViewerWidget] = None
        
        # 菜单和工具栏
        self.menu_bar: Optional[QMenuBar] = None
        self.tool_bar: Optional[QToolBar] = None
        self.status_bar: Optional[QStatusBar] = None
        
        # 状态栏标签
        self.status_label: Optional[QLabel] = None
        self.task_info_label: Optional[QLabel] = None
        self.time_label: Optional[QLabel] = None
        
        # 菜单动作
        self.actions: Dict[str, QAction] = {}
        
        # 初始化UI
        self._init_ui()
        self._connect_signals()
        
        logger.debug("MainWindowView 初始化完成")
    
    def _init_ui(self):
        """初始化UI界面"""
        # 设置窗口属性
        self.setWindowTitle("星铁自动化工具")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)
        
        # 设置图标
        try:
            self.setWindowIcon(QIcon("resources/icons/app.ico"))
        except Exception:
            pass  # 图标文件不存在时忽略
        
        # 创建中央部件
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # 创建主布局
        self.main_layout = QVBoxLayout(self.central_widget)
        main_margin = self._get_config_value('ui.main_window.main_layout_margin', 5)
        main_spacing = self._get_config_value('ui.main_window.main_layout_spacing', 5)
        self.main_layout.setContentsMargins(main_margin, main_margin, main_margin, main_margin)
        self.main_layout.setSpacing(main_spacing)
        
        # 创建分割器
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_layout.addWidget(self.main_splitter)
        
        # 创建左右面板
        self._create_left_panel()
        self._create_right_panel()
        
        # 设置分割器比例
        self.main_splitter.setSizes([300, 1100])
        self.main_splitter.setCollapsible(0, False)
        self.main_splitter.setCollapsible(1, False)
        
        # 创建菜单栏
        self._create_menu_bar()
        
        # 创建工具栏
        self._create_tool_bar()
        
        # 创建状态栏
        self._create_status_bar()
    
    def _create_left_panel(self):
        """创建左侧控制面板"""
        self.left_panel = QWidget()
        layout = QVBoxLayout(self.left_panel)
        left_panel_margin = self._get_config_value('ui.main_window.left_panel_margin', 10)
        left_panel_spacing = self._get_config_value('ui.main_window.left_panel_spacing', 10)
        layout.setContentsMargins(left_panel_margin, left_panel_margin, left_panel_margin, left_panel_margin)
        layout.setSpacing(left_panel_spacing)
        
        # 控制按钮
        self.start_button = QPushButton("开始自动化")
        start_button_height = self._get_config_value('ui.main_window.start_button_height', 40)
        self.start_button.setMinimumHeight(start_button_height)
        self.start_button.setStyleSheet("""
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
        
        self.stop_button = QPushButton("停止自动化")
        stop_button_height = self._get_config_value('ui.main_window.stop_button_height', 40)
        self.stop_button.setMinimumHeight(stop_button_height)
        self.stop_button.setEnabled(False)
        self.stop_button.setStyleSheet("""
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
        
        layout.addWidget(self.start_button)
        layout.addWidget(self.stop_button)
        
        # 状态信息
        status_label = QLabel("状态信息:")
        status_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        layout.addWidget(status_label)
        
        self.status_text = QTextEdit()
        status_text_height = self._get_config_value('ui.main_window.status_text_height', 200)
        self.status_text.setMaximumHeight(status_text_height)
        self.status_text.setReadOnly(True)
        self.status_text.setPlainText("就绪")
        layout.addWidget(self.status_text)
        
        layout.addStretch()
        
        self.main_splitter.addWidget(self.left_panel)
    
    def _create_right_panel(self):
        """创建右侧主工作区"""
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.North)
        
        # 创建各个标签页
        self._create_task_tab()
        self._create_game_tab()
        self._create_automation_tab()
        self._create_log_tab()
        
        self.main_splitter.addWidget(self.tab_widget)
    
    def _create_task_tab(self):
        """创建任务管理标签页"""
        task_widget = QWidget()
        layout = QHBoxLayout(task_widget)
        task_tab_margin = self._get_config_value('ui.main_window.task_tab_margin', 5)
        task_tab_spacing = self._get_config_value('ui.main_window.task_tab_spacing', 5)
        layout.setContentsMargins(task_tab_margin, task_tab_margin, task_tab_margin, task_tab_margin)
        layout.setSpacing(task_tab_spacing)
        
        # 创建任务分割器
        task_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 创建任务列表MVP组件
        self.task_list_mvp = TaskListMVP()
        task_splitter.addWidget(self.task_list_mvp.get_view())
        
        # 创建任务创建MVP组件
        self.task_creation_mvp = TaskCreationMVP()
        task_splitter.addWidget(self.task_creation_mvp.get_view())
        
        # 设置分割器比例
        task_splitter.setSizes([800, 400])
        task_splitter.setCollapsible(0, False)
        task_splitter.setCollapsible(1, False)
        
        layout.addWidget(task_splitter)
        
        self.tab_widget.addTab(task_widget, "任务管理")
    
    def _create_game_tab(self):
        """创建游戏设置标签页"""
        self.game_settings_widget = GameSettingsWidget()
        self.tab_widget.addTab(self.game_settings_widget, "游戏设置")
    
    def _create_automation_tab(self):
        """创建自动化配置标签页"""
        self.automation_settings_widget = AutomationSettingsWidget()
        self.tab_widget.addTab(self.automation_settings_widget, "自动化配置")
    
    def _create_log_tab(self):
        """创建日志查看标签页"""
        self.log_viewer_widget = LogViewerWidget()
        self.tab_widget.addTab(self.log_viewer_widget, "执行日志")
    
    def _create_menu_bar(self):
        """创建菜单栏"""
        self.menu_bar = self.menuBar()
        
        # 文件菜单
        file_menu = self.menu_bar.addMenu("文件")
        
        self.actions['import_config'] = QAction("导入配置", self)
        self.actions['export_config'] = QAction("导出配置", self)
        self.actions['exit'] = QAction("退出", self)
        
        file_menu.addAction(self.actions['import_config'])
        file_menu.addAction(self.actions['export_config'])
        file_menu.addSeparator()
        file_menu.addAction(self.actions['exit'])
        
        # 工具菜单
        tools_menu = self.menu_bar.addMenu("工具")
        
        self.actions['execution_history'] = QAction("执行历史", self)
        self.actions['database_management'] = QAction("数据库管理", self)
        self.actions['log_management'] = QAction("日志管理", self)
        self.actions['settings'] = QAction("设置", self)
        
        tools_menu.addAction(self.actions['execution_history'])
        tools_menu.addSeparator()
        tools_menu.addAction(self.actions['database_management'])
        tools_menu.addAction(self.actions['log_management'])
        tools_menu.addSeparator()
        tools_menu.addAction(self.actions['settings'])
        
        # 帮助菜单
        help_menu = self.menu_bar.addMenu("帮助")
        
        self.actions['about'] = QAction("关于", self)
        help_menu.addAction(self.actions['about'])
    
    def _create_tool_bar(self):
        """创建工具栏"""
        self.tool_bar = self.addToolBar("主工具栏")
        self.tool_bar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        
        # 添加工具栏按钮
        self.tool_bar.addAction(self.actions.get('start', self._create_action("开始", "开始自动化")))
        self.tool_bar.addAction(self.actions.get('stop', self._create_action("停止", "停止自动化")))
        self.tool_bar.addSeparator()
        self.tool_bar.addAction(self.actions['settings'])
    
    def _create_action(self, text: str, tooltip: str) -> QAction:
        """创建动作
        
        Args:
            text: 动作文本
            tooltip: 工具提示
        
        Returns:
            创建的动作
        """
        action = QAction(text, self)
        action.setToolTip(tooltip)
        return action
    
    def _create_status_bar(self):
        """创建状态栏"""
        self.status_bar = self.statusBar()
        
        # 状态标签
        self.status_label = QLabel("就绪")
        self.status_bar.addWidget(self.status_label)
        
        # 任务信息标签
        self.task_info_label = QLabel("无任务")
        self.status_bar.addPermanentWidget(self.task_info_label)
        
        # 时间标签
        self.time_label = QLabel("")
        self.status_bar.addPermanentWidget(self.time_label)
    
    def _connect_signals(self):
        """连接信号"""
        # 控制按钮信号
        if self.start_button:
            self.start_button.clicked.connect(self.start_automation_requested.emit)
        if self.stop_button:
            self.stop_button.clicked.connect(self.stop_automation_requested.emit)
        
        # 标签页切换信号
        if self.tab_widget:
            self.tab_widget.currentChanged.connect(self.tab_changed.emit)
        
        # 菜单动作信号
        if 'import_config' in self.actions:
            self.actions['import_config'].triggered.connect(self.import_config_requested.emit)
        if 'export_config' in self.actions:
            self.actions['export_config'].triggered.connect(self.export_config_requested.emit)
        if 'exit' in self.actions:
            self.actions['exit'].triggered.connect(self.close)
        if 'execution_history' in self.actions:
            self.actions['execution_history'].triggered.connect(self.show_execution_history_requested.emit)
        if 'database_management' in self.actions:
            self.actions['database_management'].triggered.connect(self.database_management_requested.emit)
        if 'log_management' in self.actions:
            self.actions['log_management'].triggered.connect(self.log_management_requested.emit)
        if 'settings' in self.actions:
            self.actions['settings'].triggered.connect(self.settings_requested.emit)
        if 'about' in self.actions:
            self.actions['about'].triggered.connect(self.about_requested.emit)
        
        # 设置组件信号
        if self.game_settings_widget:
            self.game_settings_widget.settings_changed.connect(self.game_settings_changed.emit)
        if self.automation_settings_widget:
            self.automation_settings_widget.settings_changed.connect(self.automation_settings_changed.emit)
        if self.log_viewer_widget:
            self.log_viewer_widget.log_exported.connect(self.log_exported.emit)
            self.log_viewer_widget.log_cleared.connect(self.log_cleared.emit)
    
    # 状态更新方法
    def update_automation_status(self, is_running: bool):
        """更新自动化状态
        
        Args:
            is_running: 是否运行中
        """
        if self.start_button:
            self.start_button.setEnabled(not is_running)
        if self.stop_button:
            self.stop_button.setEnabled(is_running)
        
        status_text = "运行中" if is_running else "就绪"
        if self.status_label:
            self.status_label.setText(status_text)
    
    def update_status_message(self, message: str):
        """更新状态消息
        
        Args:
            message: 状态消息
        """
        if self.status_text:
            # 限制状态文本长度
            if len(message) > 1000:
                lines = message.split('\n')
                if len(lines) > 20:
                    message = '\n'.join(lines[-20:])
            
            self.status_text.setPlainText(message)
            # 滚动到底部
            cursor = self.status_text.textCursor()
            cursor.movePosition(cursor.MoveOperation.End)
            self.status_text.setTextCursor(cursor)
        
        if self.status_label:
            # 状态栏显示简短消息
            short_message = message.split('\n')[-1] if '\n' in message else message
            if len(short_message) > 50:
                short_message = short_message[:47] + "..."
            self.status_label.setText(short_message)
    
    def update_current_task(self, task_id: str):
        """更新当前任务显示
        
        Args:
            task_id: 任务ID
        """
        if self.task_info_label:
            if task_id:
                self.task_info_label.setText(f"当前任务: {task_id[:8]}...")
            else:
                self.task_info_label.setText("无任务")
    
    def update_time_display(self, time_text: str):
        """更新时间显示
        
        Args:
            time_text: 时间文本
        """
        if self.time_label:
            self.time_label.setText(time_text)
    
    def set_current_tab(self, tab_index: int):
        """设置当前标签页
        
        Args:
            tab_index: 标签页索引
        """
        if self.tab_widget and 0 <= tab_index < self.tab_widget.count():
            self.tab_widget.setCurrentIndex(tab_index)
    
    def get_current_tab(self) -> int:
        """获取当前标签页索引
        
        Returns:
            当前标签页索引
        """
        return self.tab_widget.currentIndex() if self.tab_widget else 0
    
    # MVP组件访问器
    def get_task_list_mvp(self) -> Optional[TaskListMVP]:
        """获取任务列表MVP组件"""
        return self.task_list_mvp
    
    def get_task_creation_mvp(self) -> Optional[TaskCreationMVP]:
        """获取任务创建MVP组件"""
        return self.task_creation_mvp
    
    def get_game_settings_widget(self) -> Optional[GameSettingsWidget]:
        """获取游戏设置组件"""
        return self.game_settings_widget
    
    def get_automation_settings_widget(self) -> Optional[AutomationSettingsWidget]:
        """获取自动化设置组件"""
        return self.automation_settings_widget
    
    def get_log_viewer_widget(self) -> Optional[LogViewerWidget]:
        """获取日志查看组件"""
        return self.log_viewer_widget
    
    # 对话框显示
    def show_execution_history_dialog(self):
        """显示执行历史对话框"""
        try:
            dialog = TaskExecutionHistoryDialog(self)
            dialog.exec()
        except Exception as e:
            logger.error(f"显示执行历史对话框失败: {e}")
            self.show_error_message("错误", f"无法显示执行历史: {e}")
    
    def show_about_dialog(self):
        """显示关于对话框"""
        QMessageBox.about(self, "关于", 
                         "星铁自动化工具\n\n"
                         "版本: 1.0.0\n"
                         "一个用于崩坏：星穹铁道的自动化工具")
    
    # BaseView接口实现
    def set_loading(self, loading: bool):
        """设置加载状态
        
        Args:
            loading: 是否加载中
        """
        # 可以在这里添加加载指示器
        self.setEnabled(not loading)
    
    def update_data(self, data: Dict[str, Any]):
        """更新数据显示
        
        Args:
            data: 数据字典
        """
        # 根据数据类型更新相应的显示
        if 'automation_status' in data:
            self.update_automation_status(data['automation_status'])
        
        if 'status_message' in data:
            self.update_status_message(data['status_message'])
        
        if 'current_task' in data:
            self.update_current_task(data['current_task'])
        
        if 'time_display' in data:
            self.update_time_display(data['time_display'])
        
        if 'current_tab' in data:
            self.set_current_tab(data['current_tab'])
    
    def set_enabled(self, enabled: bool):
        """设置启用状态
        
        Args:
            enabled: 是否启用
        """
        self.setEnabled(enabled)
    
    def get_user_input(self) -> Dict[str, Any]:
        """获取用户输入
        
        Returns:
            用户输入数据字典
        """
        return {
            'current_tab': self.get_current_tab(),
            'window_geometry': self.geometry(),
            'splitter_sizes': self.main_splitter.sizes() if self.main_splitter else []
        }
    
    def show_message(self, title: str, message: str, message_type: str = "info"):
        """显示消息
        
        Args:
            title: 标题
            message: 消息内容
            message_type: 消息类型 (info, warning, error)
        """
        if message_type == "warning":
            QMessageBox.warning(self, title, message)
        elif message_type == "error":
            QMessageBox.critical(self, title, message)
        else:
            QMessageBox.information(self, title, message)
    
    def show_error_message(self, title: str, message: str):
        """显示错误消息
        
        Args:
            title: 标题
            message: 错误消息
        """
        self.show_message(title, message, "error")
    
    def show_confirmation_dialog(self, title: str, message: str) -> bool:
        """显示确认对话框
        
        Args:
            title: 标题
            message: 消息内容
        
        Returns:
            用户是否确认
        """
        reply = QMessageBox.question(self, title, message,
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                   QMessageBox.StandardButton.No)
        return reply == QMessageBox.StandardButton.Yes
    
    # 窗口状态管理
    def get_window_state(self) -> Dict[str, Any]:
        """获取窗口状态
        
        Returns:
            窗口状态字典
        """
        return {
            'geometry': self.geometry(),
            'splitter_sizes': self.main_splitter.sizes() if self.main_splitter else [],
            'current_tab': self.get_current_tab(),
            'window_state': self.windowState(),
            'is_maximized': self.isMaximized()
        }
    
    def restore_window_state(self, state: Dict[str, Any]):
        """恢复窗口状态
        
        Args:
            state: 窗口状态字典
        """
        try:
            if 'geometry' in state:
                self.setGeometry(state['geometry'])
            
            if 'splitter_sizes' in state and self.main_splitter:
                self.main_splitter.setSizes(state['splitter_sizes'])
            
            if 'current_tab' in state:
                self.set_current_tab(state['current_tab'])
            
            if 'is_maximized' in state and state['is_maximized']:
                self.showMaximized()
                
        except Exception as e:
            logger.warning(f"恢复窗口状态失败: {e}")
    
    # 事件处理
    def closeEvent(self, event):
        """窗口关闭事件
        
        Args:
            event: 关闭事件
        """
        # 发出窗口状态变化信号
        self.window_state_changed.emit(self.get_window_state())
        
        # 调用父类的关闭事件
        super().closeEvent(event)
    
    def resizeEvent(self, event):
        """窗口大小变化事件
        
        Args:
            event: 大小变化事件
        """
        super().resizeEvent(event)
        
        # 发出窗口状态变化信号
        self.window_state_changed.emit(self.get_window_state())
    
    # 清理资源
    def cleanup(self):
        """清理资源"""
        try:
            # 清理MVP组件
            if self.task_list_mvp:
                self.task_list_mvp.cleanup()
            
            if self.task_creation_mvp:
                self.task_creation_mvp.cleanup()
            
            logger.debug("MainWindowView 资源清理完成")
            
        except Exception as e:
            logger.error(f"清理MainWindowView资源失败: {e}")