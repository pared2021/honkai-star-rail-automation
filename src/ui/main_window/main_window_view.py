"""主窗口视图模块.

实现主窗口界面的视图组件。
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
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
    QToolBar
)
from PyQt6.QtGui import QAction, QIcon


class MainWindowView(QMainWindow):
    """主窗口视图类.
    
    提供应用程序的主界面布局和基本组件。
    """
    
    def __init__(self):
        """初始化主窗口视图."""
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        """设置用户界面."""
        self.setWindowTitle("崩坏星穹铁道自动化助手")
        self.setGeometry(100, 100, 1200, 800)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 创建标题标签
        title_label = QLabel("崩坏星穹铁道自动化助手")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
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
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")
        
        # 创建菜单栏
        self.setup_menu_bar()
        
        # 创建工具栏
        self.setup_toolbar()
        
    def setup_tabs(self):
        """设置选项卡."""
        # 主控制面板
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
        
        self.tab_widget.addTab(control_tab, "主控制")
        
        # 设置选项卡
        settings_tab = QWidget()
        settings_layout = QVBoxLayout(settings_tab)
        settings_layout.addWidget(QLabel("设置功能开发中..."))
        self.tab_widget.addTab(settings_tab, "设置")
        
        # 状态监控选项卡
        monitor_tab = QWidget()
        monitor_layout = QVBoxLayout(monitor_tab)
        monitor_layout.addWidget(QLabel("状态监控功能开发中..."))
        self.tab_widget.addTab(monitor_tab, "状态监控")
        
    def setup_menu_bar(self):
        """设置菜单栏."""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件")
        
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助")
        
        about_action = QAction("关于", self)
        help_menu.addAction(about_action)
        
    def setup_toolbar(self):
        """设置工具栏."""
        toolbar = QToolBar()
        self.addToolBar(toolbar)
        
        # 添加工具栏按钮
        start_action = QAction("开始", self)
        toolbar.addAction(start_action)
        
        stop_action = QAction("停止", self)
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
