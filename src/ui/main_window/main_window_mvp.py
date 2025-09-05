"""主窗口MVP模块.

实现主窗口界面的MVP架构模式。
"""

from .main_window_view import MainWindowView
from loguru import logger


class MainWindowMVP:
    """主窗口MVP控制器.
    
    整合视图、模型和控制器，提供完整的主窗口功能。
    """
    
    def __init__(self):
        """初始化MVP控制器."""
        self.view = MainWindowView()
        self.setup_connections()
        logger.info("主窗口MVP初始化完成")
        
    def setup_connections(self):
        """设置信号连接."""
        # 连接按钮信号
        self.view.start_button.clicked.connect(self.on_start_automation)
        self.view.stop_button.clicked.connect(self.on_stop_automation)
        
    def show(self):
        """显示主窗口."""
        self.view.show()
        self.view.update_status("应用程序已启动")
        self.view.append_log("欢迎使用崩坏星穹铁道自动化助手！")
        
    def on_start_automation(self):
        """开始自动化处理."""
        logger.info("用户点击开始自动化")
        self.view.update_status("自动化已启动")
        self.view.append_log("自动化功能已启动...")
        
        # TODO: 实现实际的自动化逻辑
        self.view.append_log("注意：自动化功能正在开发中")
        
    def on_stop_automation(self):
        """停止自动化处理."""
        logger.info("用户点击停止自动化")
        self.view.update_status("自动化已停止")
        self.view.append_log("自动化功能已停止")
        
        # TODO: 实现实际的停止逻辑
        
    def close(self):
        """关闭主窗口."""
        self.view.close()
