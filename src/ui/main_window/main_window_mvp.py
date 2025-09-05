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
        
        try:
            # 获取监控系统
            from src.monitoring import get_monitoring_system
            monitoring_system = get_monitoring_system()
            
            if monitoring_system:
                monitoring_system.start()
                self.view.append_log("自动化监控系统已启动")
            
            # 更新监控界面状态
            if hasattr(self.view, 'monitoring_widget'):
                self.view.monitoring_widget.add_log("自动化处理已开始")
                
            self.view.append_log("自动化处理已启动")
            
        except Exception as e:
            self.view.append_log(f"启动自动化处理时出错: {str(e)}")
            logger.error(f"启动自动化处理失败: {str(e)}")
        
    def on_stop_automation(self):
        """停止自动化处理."""
        logger.info("用户点击停止自动化")
        self.view.update_status("自动化已停止")
        self.view.append_log("自动化功能已停止")
        
        try:
            # 获取监控系统
            from src.monitoring import get_monitoring_system
            monitoring_system = get_monitoring_system()
            
            if monitoring_system:
                monitoring_system.stop()
                self.view.append_log("自动化监控系统已停止")
            
            # 更新监控界面状态
            if hasattr(self.view, 'monitoring_widget'):
                self.view.monitoring_widget.add_log("自动化处理已停止")
                
            self.view.append_log("自动化处理已停止")
            
        except Exception as e:
            self.view.append_log(f"停止自动化处理时出错: {str(e)}")
            logger.error(f"停止自动化处理失败: {str(e)}")
        
    def close(self):
        """关闭主窗口."""
        self.view.close()
