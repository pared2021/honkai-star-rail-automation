"""主窗口视图模块.

实现主窗口界面的视图组件。
"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTabWidget,
    QTextEdit,
    QStatusBar,
    QMenuBar,
    QToolBar,
    QAction
)
from PyQt5.QtGui import QIcon


class MainWindowView:
    """主窗口视图类.
    
    提供应用程序的主界面布局和基本组件。
    """
    
    def __init__(self):
        """初始化主窗口视图."""
        # 延迟所有UI创建，等待QApplication创建
        self._window = None
        self._ui_setup_done = False
        
    def ensure_ui_setup(self):
        """确保UI已设置."""
        if not self._ui_setup_done:
            self._window = QMainWindow()
            self.setup_ui()
            self._ui_setup_done = True
            
    def get_window(self):
        """获取主窗口实例."""
        self.ensure_ui_setup()
        return self._window
        
    def setup_ui(self):
        """设置用户界面."""
        self._window.setWindowTitle("崩坏星穹铁道自动化助手")
        self._window.setGeometry(100, 100, 1200, 800)
        
        # 创建中央部件
        central_widget = QWidget()
        self._window.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 创建标题标签
        title_label = QLabel("崩坏星穹铁道自动化助手")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #2c3e50;
                margin: 20px;
            }
        """)
        main_layout.addWidget(title_label)
        
        # 创建选项卡控件
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # 添加基本选项卡
        self.setup_tabs()
        
        # 创建状态栏
        self.status_bar = QStatusBar()
        self._window.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")
        
        # 创建菜单栏
        self.setup_menu_bar()
        
        # 创建工具栏
        self.setup_toolbar()
        
    def setup_tabs(self):
        """设置选项卡."""
        # 主控制面板
        control_tab = self._create_control_tab()
        self.tab_widget.addTab(control_tab, "主控制")
        
        # 任务管理选项卡
        try:
            from ..task_list.task_list_view import TaskListView
            self.task_list_widget = TaskListView(self._window)
            self.tab_widget.addTab(self.task_list_widget, "任务管理")
        except Exception as e:
            # 如果导入失败，创建占位符
            self.tab_widget.addTab(self._create_placeholder_widget(f"任务管理界面加载失败: {str(e)}"), "任务管理")
        
        # 任务创建选项卡
        try:
            from ..task_creation.task_creation_view import TaskCreationView
            self.task_creation_widget = TaskCreationView(self._window)
            self.tab_widget.addTab(self.task_creation_widget, "创建任务")
        except Exception as e:
            # 如果导入失败，创建占位符
            self.tab_widget.addTab(self._create_placeholder_widget(f"任务创建界面加载失败: {str(e)}"), "创建任务")
        
        # 进度监控选项卡
        try:
            from ..task_progress.task_progress_view import TaskProgressView
            self.task_progress_widget = TaskProgressView(self._window)
            self.tab_widget.addTab(self.task_progress_widget, "进度监控")
        except Exception as e:
            # 如果导入失败，创建占位符
            self.tab_widget.addTab(self._create_placeholder_widget(f"进度监控界面加载失败: {str(e)}"), "进度监控")
        
        # 日志查看器选项卡
        try:
            from ..log_viewer.log_viewer_view import LogViewerView
            self.log_viewer_widget = LogViewerView(self._window)
            self.tab_widget.addTab(self.log_viewer_widget, "日志查看")
        except Exception as e:
            # 如果导入失败，创建占位符
            self.tab_widget.addTab(self._create_placeholder_widget(f"日志查看界面加载失败: {str(e)}"), "日志查看")
        
    def setup_menu_bar(self):
        """设置菜单栏."""
        menubar = self._window.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件")
        
        exit_action = QAction("退出", self._window)
        exit_action.triggered.connect(self._window.close)
        file_menu.addAction(exit_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助")
        
        about_action = QAction("关于", self._window)
        help_menu.addAction(about_action)
        
    def setup_toolbar(self):
        """设置工具栏."""
        toolbar = QToolBar()
        self._window.addToolBar(toolbar)
        
        # 添加工具栏按钮
        start_action = QAction("开始", self._window)
        toolbar.addAction(start_action)
        
        stop_action = QAction("停止", self._window)
        toolbar.addAction(stop_action)
        
    def update_status(self, message: str):
        """更新状态栏消息.
        
        Args:
            message: 要显示的状态消息
        """
        self.status_bar.showMessage(message)
        
    def append_log(self, message: str):
        """添加日志消息.
        
        Args:
            message: 要添加的日志消息
        """
        self.log_display.append(message)
    
    def _create_placeholder_widget(self, message: str) -> QWidget:
        """创建占位符组件.
        
        Args:
            message: 要显示的错误消息
            
        Returns:
            QWidget: 占位符组件
        """
        placeholder = QWidget()
        layout = QVBoxLayout(placeholder)
        layout.addWidget(QLabel(message))
        return placeholder
    
    def _create_control_tab(self) -> QWidget:
        """创建主控制面板.
        
        Returns:
            QWidget: 控制面板组件
        """
        control_tab = QWidget()
        control_layout = QVBoxLayout(control_tab)
        
        # 添加控制按钮
        button_layout = QHBoxLayout()
        
        self.start_button = QPushButton("开始自动化")
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #2ecc71;
            }
        """)
        button_layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton("停止自动化")
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        button_layout.addWidget(self.stop_button)
        
        control_layout.addLayout(button_layout)
        
        # 添加日志显示区域
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setPlaceholderText("日志信息将在这里显示...")
        control_layout.addWidget(self.log_display)
        
        return control_tab
