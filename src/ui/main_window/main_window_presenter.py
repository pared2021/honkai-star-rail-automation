# -*- coding: utf-8 -*-
"""
主窗口展示器 - MVP模式的Presenter层实现
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from PyQt6.QtCore import QObject, QTimer, pyqtSlot
from loguru import logger

from src.ui.mvp.base_presenter import BasePresenter
from src.ui.main_window.main_window_model import MainWindowModel
from src.ui.main_window.main_window_view import MainWindowView
from src.ui.sync_adapter import SyncAdapter
from src.gui.mvp.task_list_mvp import TaskListMVP

# 业务服务导入
from src.application.task_application_service import TaskApplicationService
from src.automation.automation_controller import AutomationController
from src.monitoring.logging_monitoring_service import LoggingMonitoringService
from core.performance_monitor import PerformanceMonitor


class MainWindowPresenter(BasePresenter):
    """
    主窗口展示器 - 负责协调主窗口的Model和View
    
    处理用户交互、业务逻辑调用和界面更新
    """
    
    def __init__(self, 
                 model: MainWindowModel,
                 view: MainWindowView,
                 sync_adapter: SyncAdapter,
                 task_service: TaskApplicationService,
                 automation_controller: AutomationController,
                 monitoring_service: LoggingMonitoringService,
                 performance_monitor: PerformanceMonitor):
        super().__init__(model, view)
        
        # 依赖注入
        self.sync_adapter = sync_adapter
        self.task_service = task_service
        self.automation_controller = automation_controller
        self.monitoring_service = monitoring_service
        self.performance_monitor = performance_monitor
        
        # 初始化TaskListMVP组件
        self.task_list_mvp = TaskListMVP(
            task_service=task_service,
            sync_adapter=sync_adapter
        )
        self.task_list_window = None
        
        # 状态管理
        self.start_time = datetime.now()
        self.automation_running = False
        self.automation_paused = False
        
        # 定时器
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_dashboard)
        self.update_timer.start(1000)  # 每秒更新一次
        
        # 初始化
        self.setup_connections()
        self.initialize_data()
        
        logger.info("主窗口展示器初始化完成")
    
    def _register_action_handlers(self):
        """注册动作处理器"""
        # 注册用户动作处理器
        self.register_action_handler('start_automation', self.handle_start_automation)
        self.register_action_handler('stop_automation', self.handle_stop_automation)
        self.register_action_handler('pause_automation', self.handle_pause_automation)
        self.register_action_handler('settings', self.handle_settings)
        self.register_action_handler('task_management', self.handle_task_management)
        self.register_action_handler('monitoring', self.handle_monitoring)
        self.register_action_handler('about', self.handle_about)
        self.register_action_handler('exit', self.handle_exit)
        
        # 任务操作处理器
        self.register_action_handler('create_task', self.handle_create_task)
        self.register_action_handler('edit_task', self.handle_edit_task)
        self.register_action_handler('delete_task', self.handle_delete_task)
        self.register_action_handler('execute_task', self.handle_execute_task)
        
        # 配置变更处理器
        self.register_action_handler('config_change', self.handle_config_change)
        
        logger.debug("动作处理器注册完成")
    
    def setup_connections(self):
        """设置信号连接"""
        
        # 连接View的用户交互信号
        self.view.start_automation_requested.connect(self.handle_start_automation)
        self.view.stop_automation_requested.connect(self.handle_stop_automation)
        self.view.pause_automation_requested.connect(self.handle_pause_automation)
        self.view.settings_requested.connect(self.handle_settings)
        self.view.task_management_requested.connect(self.handle_task_management)
        self.view.monitoring_requested.connect(self.handle_monitoring)
        self.view.about_requested.connect(self.handle_about)
        self.view.exit_requested.connect(self.handle_exit)
        
        # 任务操作信号
        self.view.create_task_requested.connect(self.handle_create_task)
        self.view.edit_task_requested.connect(self.handle_edit_task)
        self.view.delete_task_requested.connect(self.handle_delete_task)
        self.view.execute_task_requested.connect(self.handle_execute_task)
        
        # 配置变更信号
        self.view.config_changed.connect(self.handle_config_change)
        
        # 连接Model的数据变更信号
        self.model.data_changed.connect(self.on_model_data_changed)
        self.model.validation_failed.connect(self.on_model_validation_failed)
        
        # 连接业务服务信号
        if hasattr(self.automation_controller, 'status_changed'):
            self.automation_controller.status_changed.connect(self.on_automation_status_changed)
        
        if hasattr(self.monitoring_service, 'alert_triggered'):
            self.monitoring_service.alert_triggered.connect(self.on_alert_triggered)
    
    def initialize_data(self):
        """初始化数据"""
        try:
            # 加载初始数据
            self.sync_adapter.run_async_task(self.model.load_data())
            
            # 更新界面
            self.update_view_from_model()
            
            # 启动监控服务
            if hasattr(self.monitoring_service, 'start'):
                self.monitoring_service.start()
            
            logger.info("主窗口数据初始化完成")
            
        except Exception as e:
            logger.error(f"初始化数据失败: {e}")
            self.view.show_error(f"初始化失败: {str(e)}")
    
    def update_view_from_model(self):
        """从Model更新View"""
        try:
            model_data = self.model.get_all_data()
            
            # 构建View需要的数据格式
            view_data = {
                'automation_status': self.get_automation_status(),
                'system_status': model_data.get('system_info', {}).get('health_status', 'unknown'),
                'task_statistics': model_data.get('task_stats', {}),
                'uptime_minutes': self.get_uptime_minutes()
            }
            
            self.view.update_data(view_data)
            
        except Exception as e:
            logger.error(f"更新视图失败: {e}")
    
    def get_automation_status(self) -> str:
        """获取自动化状态"""
        if self.automation_running:
            return "paused" if self.automation_paused else "running"
        return "stopped"
    
    def get_uptime_minutes(self) -> int:
        """获取运行时间（分钟）"""
        uptime = datetime.now() - self.start_time
        return int(uptime.total_seconds() / 60)
    
    def update_dashboard(self):
        """更新仪表板数据"""
        try:
            # 异步获取最新数据
            self.sync_adapter.run_async_task(self._update_dashboard_async())
            
        except Exception as e:
            logger.error(f"更新仪表板失败: {e}")
    
    async def _update_dashboard_async(self):
        """异步更新仪表板数据"""
        try:
            # 刷新Model数据
            await self.model.refresh_data()
            
            # 更新View
            self.update_view_from_model()
            
        except Exception as e:
            logger.error(f"异步更新仪表板失败: {e}")
    
    # === 用户交互处理方法 ===
    
    @pyqtSlot()
    def handle_start_automation(self):
        """处理开始自动化请求"""
        try:
            self.view.show_loading("启动自动化中...")
            
            # 异步启动自动化
            self.sync_adapter.run_async_task(self._start_automation_async())
            
        except Exception as e:
            logger.error(f"启动自动化失败: {e}")
            self.view.show_error(f"启动失败: {str(e)}")
            self.view.hide_loading()
    
    async def _start_automation_async(self):
        """异步启动自动化"""
        try:
            # 检查系统状态
            if not await self.automation_controller.is_ready():
                raise Exception("系统未就绪，无法启动自动化")
            
            # 启动自动化
            await self.automation_controller.start()
            
            # 更新状态
            self.automation_running = True
            self.automation_paused = False
            
            # 更新Model
            self.model.set_data('app_status', 'running')
            
            # 更新View
            self.view.update_automation_status("running")
            self.view.show_status_message("自动化已启动")
            self.view.hide_loading()
            
            logger.info("自动化启动成功")
            
        except Exception as e:
            logger.error(f"启动自动化失败: {e}")
            self.view.show_error(f"启动失败: {str(e)}")
            self.view.hide_loading()
    
    @pyqtSlot()
    def handle_stop_automation(self):
        """处理停止自动化请求"""
        try:
            if not self.view.confirm_action("确认停止", "确定要停止自动化吗？"):
                return
            
            self.view.show_loading("停止自动化中...")
            
            # 异步停止自动化
            self.sync_adapter.run_async_task(self._stop_automation_async())
            
        except Exception as e:
            logger.error(f"停止自动化失败: {e}")
            self.view.show_error(f"停止失败: {str(e)}")
            self.view.hide_loading()
    
    async def _stop_automation_async(self):
        """异步停止自动化"""
        try:
            # 停止自动化
            await self.automation_controller.stop()
            
            # 更新状态
            self.automation_running = False
            self.automation_paused = False
            
            # 更新Model
            self.model.set_data('app_status', 'stopped')
            
            # 更新View
            self.view.update_automation_status("stopped")
            self.view.show_status_message("自动化已停止")
            self.view.hide_loading()
            
            logger.info("自动化停止成功")
            
        except Exception as e:
            logger.error(f"停止自动化失败: {e}")
            self.view.show_error(f"停止失败: {str(e)}")
            self.view.hide_loading()
    
    @pyqtSlot()
    def handle_pause_automation(self):
        """处理暂停自动化请求"""
        try:
            self.view.show_loading("暂停自动化中...")
            
            # 异步暂停自动化
            self.sync_adapter.run_async_task(self._pause_automation_async())
            
        except Exception as e:
            logger.error(f"暂停自动化失败: {e}")
            self.view.show_error(f"暂停失败: {str(e)}")
            self.view.hide_loading()
    
    async def _pause_automation_async(self):
        """异步暂停自动化"""
        try:
            # 暂停自动化
            await self.automation_controller.pause()
            
            # 更新状态
            self.automation_paused = True
            
            # 更新Model
            self.model.set_data('app_status', 'paused')
            
            # 更新View
            self.view.update_automation_status("paused")
            self.view.show_status_message("自动化已暂停")
            self.view.hide_loading()
            
            logger.info("自动化暂停成功")
            
        except Exception as e:
            logger.error(f"暂停自动化失败: {e}")
            self.view.show_error(f"暂停失败: {str(e)}")
            self.view.hide_loading()
    
    @pyqtSlot()
    def handle_settings(self):
        """处理设置请求"""
        try:
            # 这里应该打开设置窗口
            # 暂时显示消息
            self.view.show_info_message("设置", "设置功能正在开发中...")
            
        except Exception as e:
            logger.error(f"打开设置失败: {e}")
            self.view.show_error(f"打开设置失败: {str(e)}")
    
    @pyqtSlot()
    def handle_task_management(self):
        """处理任务管理请求"""
        try:
            # 打开任务管理窗口
            self._show_task_management_window()
            
        except Exception as e:
            logger.error(f"打开任务管理失败: {e}")
            self.view.show_error(f"打开任务管理失败: {str(e)}")
    
    def _show_task_management_window(self):
        """显示任务管理窗口"""
        try:
            if self.task_list_window is None:
                # 创建任务管理窗口
                from PyQt6.QtWidgets import QDialog, QVBoxLayout
                
                self.task_list_window = QDialog(self.view)
                self.task_list_window.setWindowTitle("任务管理")
                self.task_list_window.setMinimumSize(1000, 600)
                
                # 设置布局
                layout = QVBoxLayout()
                
                # 获取TaskListWidget并添加到布局
                task_list_widget = self.task_list_mvp.get_widget()
                layout.addWidget(task_list_widget)
                
                self.task_list_window.setLayout(layout)
                
                # 初始化TaskListMVP
                self.task_list_mvp.initialize()
                
                logger.info("任务管理窗口创建完成")
            
            # 显示窗口
            self.task_list_window.show()
            self.task_list_window.raise_()
            self.task_list_window.activateWindow()
            
            # 刷新任务列表
            self.task_list_mvp.refresh()
            
        except Exception as e:
            logger.error(f"显示任务管理窗口失败: {e}")
            self.view.show_error(f"显示任务管理窗口失败: {str(e)}")
    
    @pyqtSlot()
    def handle_monitoring(self):
        """处理监控请求"""
        try:
            # 这里应该打开监控详情窗口
            # 暂时显示消息
            self.view.show_info_message("监控", "监控详情功能正在开发中...")
            
        except Exception as e:
            logger.error(f"打开监控失败: {e}")
            self.view.show_error(f"打开监控失败: {str(e)}")
    
    @pyqtSlot()
    def handle_about(self):
        """处理关于请求"""
        about_text = """
        星铁自动化助手 v1.0
        
        一个用于《崩坏：星穹铁道》的自动化工具
        
        功能特性：
        • 自动化任务执行
        • 实时系统监控
        • 任务管理
        • 性能优化
        
        开发团队：SOLO Coding
        """
        
        self.view.show_info_message("关于", about_text)
    
    @pyqtSlot()
    def handle_exit(self):
        """处理退出请求"""
        try:
            # 停止定时器
            self.update_timer.stop()
            
            # 如果自动化正在运行，先停止
            if self.automation_running:
                self.sync_adapter.run_async_task(self._stop_automation_async())
            
            # 停止监控服务
            if hasattr(self.monitoring_service, 'stop'):
                self.monitoring_service.stop()
            
            # 清理资源
            self.cleanup()
            
            logger.info("应用程序退出")
            
        except Exception as e:
            logger.error(f"退出应用程序失败: {e}")
    
    # === 任务操作处理方法 ===
    
    @pyqtSlot()
    def handle_create_task(self):
        """处理创建任务请求"""
        try:
            # 这里应该打开任务创建对话框
            self.view.show_info_message("创建任务", "任务创建功能正在开发中...")
            
        except Exception as e:
            logger.error(f"创建任务失败: {e}")
            self.view.show_error(f"创建任务失败: {str(e)}")
    
    @pyqtSlot(int)
    def handle_edit_task(self, task_id: int):
        """处理编辑任务请求"""
        try:
            # 这里应该打开任务编辑对话框
            self.view.show_info_message("编辑任务", f"编辑任务 {task_id} 功能正在开发中...")
            
        except Exception as e:
            logger.error(f"编辑任务失败: {e}")
            self.view.show_error(f"编辑任务失败: {str(e)}")
    
    @pyqtSlot(int)
    def handle_delete_task(self, task_id: int):
        """处理删除任务请求"""
        try:
            if not self.view.confirm_action("确认删除", f"确定要删除任务 {task_id} 吗？"):
                return
            
            # 异步删除任务
            self.sync_adapter.run_async_task(self._delete_task_async(task_id))
            
        except Exception as e:
            logger.error(f"删除任务失败: {e}")
            self.view.show_error(f"删除任务失败: {str(e)}")
    
    async def _delete_task_async(self, task_id: int):
        """异步删除任务"""
        try:
            await self.task_service.delete_task(task_id)
            self.view.show_status_message(f"任务 {task_id} 已删除")
            
            # 刷新任务统计
            await self.model.refresh_task_stats()
            self.update_view_from_model()
            
        except Exception as e:
            logger.error(f"删除任务失败: {e}")
            self.view.show_error(f"删除任务失败: {str(e)}")
    
    @pyqtSlot(int)
    def handle_execute_task(self, task_id: int):
        """处理执行任务请求"""
        try:
            # 异步执行任务
            self.sync_adapter.run_async_task(self._execute_task_async(task_id))
            
        except Exception as e:
            logger.error(f"执行任务失败: {e}")
            self.view.show_error(f"执行任务失败: {str(e)}")
    
    async def _execute_task_async(self, task_id: int):
        """异步执行任务"""
        try:
            await self.task_service.execute_task(task_id)
            self.view.show_status_message(f"任务 {task_id} 开始执行")
            
        except Exception as e:
            logger.error(f"执行任务失败: {e}")
            self.view.show_error(f"执行任务失败: {str(e)}")
    
    # === 配置处理方法 ===
    
    @pyqtSlot(str, object)
    def handle_config_change(self, key: str, value):
        """处理配置变更"""
        try:
            # 更新Model中的配置
            config = self.model.get_data('config', {})
            config[key] = value
            self.model.set_data('config', config)
            
            # 异步保存配置
            self.sync_adapter.run_async_task(self.model.save_data())
            
            logger.info(f"配置已更新: {key} = {value}")
            
        except Exception as e:
            logger.error(f"更新配置失败: {e}")
            self.view.show_error(f"更新配置失败: {str(e)}")
    
    # === 事件处理方法 ===
    
    @pyqtSlot(str, dict)
    def on_model_data_changed(self, key: str, data: dict):
        """处理Model数据变更"""
        try:
            # 根据变更的数据类型更新View
            if key in ['task_stats', 'system_info', 'app_status']:
                self.update_view_from_model()
            
        except Exception as e:
            logger.error(f"处理数据变更失败: {e}")
    
    @pyqtSlot(str, str)
    def on_model_validation_failed(self, field: str, error: str):
        """处理Model验证失败"""
        self.view.show_error(f"数据验证失败 [{field}]: {error}")
    
    @pyqtSlot(str)
    def on_automation_status_changed(self, status: str):
        """处理自动化状态变更"""
        try:
            # 更新内部状态
            if status == "running":
                self.automation_running = True
                self.automation_paused = False
            elif status == "paused":
                self.automation_paused = True
            elif status == "stopped":
                self.automation_running = False
                self.automation_paused = False
            
            # 更新View
            self.view.update_automation_status(status)
            
        except Exception as e:
            logger.error(f"处理自动化状态变更失败: {e}")
    
    @pyqtSlot(str, str, dict)
    def on_alert_triggered(self, level: str, message: str, data: dict):
        """处理告警"""
        try:
            # 记录告警
            logger.warning(f"收到告警 [{level}]: {message}")
            
            # 更新系统状态
            if level in ['critical', 'error']:
                self.model.set_data('system_info', {'health_status': 'critical'})
            elif level == 'warning':
                current_status = self.model.get_data('system_info', {}).get('health_status', 'good')
                if current_status not in ['critical', 'error']:
                    self.model.set_data('system_info', {'health_status': 'fair'})
            
            # 更新View
            self.update_view_from_model()
            
        except Exception as e:
            logger.error(f"处理告警失败: {e}")
    
    def cleanup(self):
        """清理资源"""
        logger.info("清理主窗口资源")
        
        try:
            # 停止定时器
            if hasattr(self, '_dashboard_timer') and self._dashboard_timer:
                self._dashboard_timer.stop()
                self._dashboard_timer = None
            
            # 清理TaskListMVP组件
            if hasattr(self, 'task_list_mvp') and self.task_list_mvp:
                self.task_list_mvp.cleanup()
                self.task_list_mvp = None
            
            # 关闭任务管理窗口
            if hasattr(self, 'task_list_window') and self.task_list_window:
                self.task_list_window.close()
                self.task_list_window = None
            
            # 清理同步适配器
            if self.sync_adapter:
                self.sync_adapter.cleanup()
            
            # 调用父类清理
            self._cleanup()
            
        except Exception as e:
            logger.error(f"清理资源失败: {e}")