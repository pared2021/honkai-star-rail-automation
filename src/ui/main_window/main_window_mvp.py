"""主窗口MVP模块.

实现主窗口界面的MVP架构模式。
"""

from .main_window_view import MainWindowView
from loguru import logger
from ...automation.automation_controller import AutomationController
from ...core.game_detector import GameDetector
from ...core.task_manager import TaskManager
from ...monitoring import get_monitoring_system, initialize_monitoring_system
from PyQt5.QtCore import QTimer
import asyncio
import threading


class MainWindowMVP:
    """主窗口MVP控制器.
    
    整合视图、模型和控制器，提供完整的主窗口功能。
    """
    
    def __init__(self):
        """初始化MVP控制器."""
        self.view = MainWindowView()
        
        # 初始化监控系统
        self.monitoring_system = initialize_monitoring_system()
        
        # 初始化核心组件
        self.automation_controller = AutomationController()
        self.game_detector = GameDetector()
        self.task_manager = TaskManager()
        
        # 初始化UI组件的Presenter
        self.init_ui_presenters()
        
        # 启动监控系统
        if self.monitoring_system:
            self.monitoring_system.start()
            # 添加基本的健康检查
            self.monitoring_system.health_checker.create_basic_checks()
            # 添加游戏检测器健康检查
            self.monitoring_system.health_checker.add_check(
                "game_detector", 
                self._check_game_detector_health
            )
            # 添加任务管理器健康检查
            self.monitoring_system.health_checker.add_check(
                "task_manager", 
                self._check_task_manager_health
            )
        
        # 自动化状态
        self.is_automation_running = False
        
        # 设置定时器用于状态更新
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(1000)  # 每秒更新一次
        
        # 启动监控系统
        try:
            self.monitoring_system.start()
            logger.info("监控系统已启动")
        except Exception as e:
            logger.error(f"启动监控系统失败: {str(e)}")
        
        self.setup_connections()
        logger.info("主窗口MVP初始化完成")
        
    def init_ui_presenters(self):
        """初始化UI组件的Presenter."""
        try:
            # 初始化任务列表Presenter
            if hasattr(self.view, 'task_list_widget'):
                from ..task_list import TaskListPresenter
                from ...core.enhanced_task_executor import EnhancedTaskExecutor
                task_executor = EnhancedTaskExecutor()
                self.task_list_presenter = TaskListPresenter(
                    view=self.view.task_list_widget,
                    task_executor=task_executor
                )
                logger.info("任务列表Presenter初始化完成")
            
            # 初始化任务进度Presenter
            if hasattr(self.view, 'task_progress_widget'):
                from ..task_progress import TaskProgressPresenter
                self.task_progress_presenter = TaskProgressPresenter(
                    view=self.view.task_progress_widget
                )
                logger.info("任务进度Presenter初始化完成")
            
            # 初始化日志查看器Presenter
            if hasattr(self.view, 'log_viewer_widget'):
                from ..log_viewer import LogViewerPresenter
                self.log_viewer_presenter = LogViewerPresenter(
                    view=self.view.log_viewer_widget
                )
                logger.info("日志查看器Presenter初始化完成")
                
        except Exception as e:
            logger.error(f"初始化UI Presenter失败: {str(e)}")
        
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
        if self.is_automation_running:
            self.view.append_log("自动化已在运行中")
            return
            
        logger.info("用户点击开始自动化")
        self.view.update_status("正在启动自动化...")
        self.view.append_log("开始启动自动化功能...")
        
        try:
            # 检查游戏状态
            self.view.append_log("正在检测游戏窗口...")
            game_status = self.game_detector.get_game_status()
            
            if game_status.get('is_running', False):
                self.view.append_log(f"检测到游戏窗口: {game_status.get('window_title', '未知')}")
            else:
                self.view.append_log("警告: 未检测到游戏窗口，自动化功能可能无法正常工作")
            
            # 启动任务管理器
            self.task_manager.start_concurrent_manager()
            self.view.append_log("任务管理器已启动")
            
            # 记录监控指标
            if self.monitoring_system:
                self.monitoring_system.metrics_collector.record_counter("automation_starts", 1)
                self.monitoring_system.metrics_collector.record_gauge("automation_status", 1)
            
            # 启动自动化控制器
            self.automation_controller.start()
            self.view.append_log("自动化控制器已启动")
            
            # 添加基本自动化任务
            basic_tasks = self.automation_controller.get_available_tasks()
            if basic_tasks:
                self.view.append_log(f"可用任务: {', '.join(basic_tasks)}")
                
                # 记录任务创建指标
                if self.monitoring_system:
                    self.monitoring_system.metrics_collector.record_counter("tasks_created", len(basic_tasks))
            
            # 获取监控系统
            from ...monitoring import get_monitoring_system
            monitoring_system = get_monitoring_system()
            
            if monitoring_system:
                monitoring_system.start()
                self.view.append_log("监控系统已启动")
            
            # 更新监控界面状态
            if hasattr(self.view, 'monitoring_widget'):
                self.view.monitoring_widget.add_log("自动化处理已开始")
            
            # 通知UI组件自动化已启动
            self.notify_ui_automation_started()
            
            self.is_automation_running = True
            self.view.update_status("自动化已启动")
            self.view.append_log("✅ 自动化功能启动成功")
            
        except Exception as e:
            self.view.append_log(f"❌ 启动自动化处理时出错: {str(e)}")
            logger.error(f"启动自动化处理失败: {str(e)}")
            self.view.update_status("自动化启动失败")
        
    def on_stop_automation(self):
        """停止自动化处理."""
        if not self.is_automation_running:
            self.view.append_log("自动化未在运行")
            return
            
        logger.info("用户点击停止自动化")
        self.view.update_status("正在停止自动化...")
        self.view.append_log("开始停止自动化功能...")
        
        try:
            # 停止自动化控制器
            self.automation_controller.stop()
            self.view.append_log("自动化控制器已停止")
            
            # 停止任务管理器
            self.task_manager.stop_concurrent_manager()
            self.view.append_log("任务管理器已停止")
            
            # 记录监控指标
            if self.monitoring_system:
                self.monitoring_system.metrics_collector.record_counter("automation_stops", 1)
                self.monitoring_system.metrics_collector.record_gauge("automation_status", 0)
            
            # 获取监控系统
            from ...monitoring import get_monitoring_system
            monitoring_system = get_monitoring_system()
            
            if monitoring_system:
                monitoring_system.stop()
                self.view.append_log("监控系统已停止")
            
            # 更新监控界面状态
            if hasattr(self.view, 'monitoring_widget'):
                self.view.monitoring_widget.add_log("自动化处理已停止")
            
            # 通知UI组件自动化已停止
            self.notify_ui_automation_stopped()
            
            self.is_automation_running = False
            self.view.update_status("自动化已停止")
            self.view.append_log("✅ 自动化功能停止成功")
            
        except Exception as e:
            self.view.append_log(f"❌ 停止自动化处理时出错: {str(e)}")
            logger.error(f"停止自动化处理失败: {str(e)}")
            self.view.update_status("自动化停止失败")
        
    def update_status(self):
        """定期更新状态信息."""
        try:
            # 更新游戏检测状态
            game_status = self.game_detector.get_game_status()
            
            # 更新任务统计
            if self.is_automation_running:
                task_stats = self.task_manager.get_task_statistics()
                concurrent_status = self.task_manager.get_concurrent_status()
                
                # 更新监控界面
                if hasattr(self.view, 'monitoring_widget'):
                    status_info = {
                        'game_running': game_status.get('game_running', False),
                        'automation_running': self.is_automation_running,
                        'active_tasks': concurrent_status.get('active_tasks', 0),
                        'completed_tasks': task_stats.get('completed', 0),
                        'failed_tasks': task_stats.get('failed', 0)
                    }
                    self.view.monitoring_widget.update_status(status_info)
            
            # 更新任务列表和进度显示
            if hasattr(self, 'task_list_presenter'):
                self.task_list_presenter.refresh_task_list()
            
            if hasattr(self, 'task_progress_presenter'):
                self.task_progress_presenter.update_progress()
                    
        except Exception as e:
            logger.error(f"状态更新失败: {str(e)}")
    
    def notify_ui_automation_started(self):
        """通知UI组件自动化已启动."""
        try:
            # 通知任务列表组件
            if hasattr(self, 'task_list_presenter'):
                self.task_list_presenter.on_automation_started()
            
            # 通知任务进度组件
            if hasattr(self, 'task_progress_presenter'):
                self.task_progress_presenter.on_automation_started()
            
            # 通知日志查看器组件
            if hasattr(self, 'log_viewer_presenter'):
                self.log_viewer_presenter.add_log("自动化系统已启动", "INFO")
                
        except Exception as e:
            logger.error(f"通知UI组件自动化启动失败: {str(e)}")
    
    def notify_ui_automation_stopped(self):
        """通知UI组件自动化已停止."""
        try:
            # 通知任务列表组件
            if hasattr(self, 'task_list_presenter'):
                self.task_list_presenter.on_automation_stopped()
            
            # 通知任务进度组件
            if hasattr(self, 'task_progress_presenter'):
                self.task_progress_presenter.on_automation_stopped()
            
            # 通知日志查看器组件
            if hasattr(self, 'log_viewer_presenter'):
                self.log_viewer_presenter.add_log("自动化系统已停止", "INFO")
                
        except Exception as e:
            logger.error(f"通知UI组件自动化停止失败: {str(e)}")
    
    def _check_game_detector_health(self):
        """检查游戏检测器健康状态."""
        from ...monitoring.health_checker import HealthCheckResult, HealthStatus
        
        try:
            if not self.game_detector:
                return HealthCheckResult(
                    component="game_detector",
                    status=HealthStatus.UNHEALTHY,
                    message="游戏检测器未初始化"
                )
            
            # 检查游戏状态
            game_status = self.game_detector.get_game_status()
            
            if game_status and game_status.get('overall_status') in ['running', 'ready']:
                return HealthCheckResult(
                    component="game_detector",
                    status=HealthStatus.HEALTHY,
                    message="游戏检测器正常运行",
                    details=game_status
                )
            else:
                return HealthCheckResult(
                    component="game_detector",
                    status=HealthStatus.DEGRADED,
                    message="游戏未检测到或检测器状态异常",
                    details=game_status or {}
                )
        except Exception as e:
            return HealthCheckResult(
                component="game_detector",
                status=HealthStatus.UNHEALTHY,
                message=f"游戏检测器检查失败: {str(e)}"
            )
    
    def _check_task_manager_health(self):
        """检查任务管理器健康状态."""
        from ...monitoring.health_checker import HealthCheckResult, HealthStatus
        
        try:
            if not self.task_manager:
                return HealthCheckResult(
                    component="task_manager",
                    status=HealthStatus.UNHEALTHY,
                    message="任务管理器未初始化"
                )
            
            # 检查任务管理器状态
            task_count = len(self.task_manager.get_all_tasks())
            
            return HealthCheckResult(
                component="task_manager",
                status=HealthStatus.HEALTHY,
                message=f"任务管理器正常运行，当前任务数: {task_count}",
                details={"task_count": task_count}
            )
        except Exception as e:
            return HealthCheckResult(
                component="task_manager",
                status=HealthStatus.UNHEALTHY,
                message=f"任务管理器检查失败: {str(e)}"
            )
    
    def close(self):
        """关闭主窗口."""
        try:
            # 停止定时器
            if hasattr(self, 'status_timer'):
                self.status_timer.stop()
            
            # 如果自动化正在运行，先停止
            if self.is_automation_running:
                self.on_stop_automation()
            
            # 清理UI组件Presenter
            self.cleanup_ui_presenters()
            
            # 清理资源
            if hasattr(self, 'task_manager'):
                self.task_manager.stop_concurrent_manager()
            
            # 停止监控系统
            if hasattr(self, 'monitoring_system') and self.monitoring_system:
                try:
                    self.monitoring_system.stop()
                    logger.info("监控系统已停止")
                except Exception as e:
                    logger.error(f"停止监控系统时出错: {str(e)}")
                
            logger.info("主窗口关闭，资源已清理")
            
        except Exception as e:
            logger.error(f"关闭窗口时出错: {str(e)}")
        finally:
            self.view.close()
    
    def cleanup_ui_presenters(self):
        """清理UI组件的Presenter."""
        try:
            # 清理任务列表Presenter
            if hasattr(self, 'task_list_presenter'):
                self.task_list_presenter.cleanup()
                logger.info("任务列表Presenter已清理")
            
            # 清理任务进度Presenter
            if hasattr(self, 'task_progress_presenter'):
                self.task_progress_presenter.cleanup()
                logger.info("任务进度Presenter已清理")
            
            # 清理日志查看器Presenter
            if hasattr(self, 'log_viewer_presenter'):
                self.log_viewer_presenter.cleanup()
                logger.info("日志查看器Presenter已清理")
                
        except Exception as e:
            logger.error(f"清理UI Presenter失败: {str(e)}")
