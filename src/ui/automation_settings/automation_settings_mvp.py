"""自动化设置MVP组合

该模块定义了自动化设置的MVP组合类，将Model、View和Presenter组合成一个完整的组件。
"""

from typing import Dict, Any, Optional
from PyQt6.QtCore import QObject, pyqtSignal

from src.ui.automation_settings.automation_settings_model import AutomationSettingsModel
from src.ui.automation_settings.automation_settings_view import AutomationSettingsView
from src.ui.automation_settings.automation_settings_presenter import AutomationSettingsPresenter
from src.utils.logger import logger


class AutomationSettingsMVP(QObject):
    """自动化设置MVP组合类
    
    将Model、View和Presenter组合成一个完整的自动化设置组件。
    """
    
    # 业务信号
    settings_changed = pyqtSignal(dict)  # 设置变化
    operation_params_updated = pyqtSignal(dict)  # 操作参数更新
    safety_options_updated = pyqtSignal(dict)  # 安全选项更新
    performance_settings_updated = pyqtSignal(dict)  # 性能设置更新
    task_config_updated = pyqtSignal(dict)  # 任务配置更新
    validation_result = pyqtSignal(bool, str)  # 验证结果
    test_result = pyqtSignal(bool, str)  # 测试结果
    settings_applied = pyqtSignal(bool, str)  # 设置应用结果
    settings_reset = pyqtSignal(bool, str)  # 设置重置结果
    import_result = pyqtSignal(bool, str)  # 导入结果
    export_result = pyqtSignal(bool, str)  # 导出结果
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 初始化MVP组件
        self.model = AutomationSettingsModel()
        self.view = AutomationSettingsView()
        self.presenter = AutomationSettingsPresenter(self.model, self.view)
        
        self.connect_business_signals()
        
        logger.info("自动化设置MVP组合初始化完成")
    
    def connect_business_signals(self):
        """连接业务信号"""
        # 连接Presenter的业务信号
        self.presenter.settings_changed.connect(self.settings_changed.emit)
        self.presenter.validation_result.connect(self.validation_result.emit)
        self.presenter.test_result.connect(self.test_result.emit)
        self.presenter.settings_applied.connect(self.settings_applied.emit)
        self.presenter.settings_reset.connect(self.settings_reset.emit)
        self.presenter.import_result.connect(self.import_result.emit)
        self.presenter.export_result.connect(self.export_result.emit)
        
        # 连接Model的数据变化信号，用于发出更细粒度的更新信号
        self.model.click_delay_changed.connect(self._on_operation_params_changed)
        self.model.key_delay_changed.connect(self._on_operation_params_changed)
        self.model.operation_interval_changed.connect(self._on_operation_params_changed)
        self.model.random_delay_enabled_changed.connect(self._on_operation_params_changed)
        self.model.random_delay_min_changed.connect(self._on_operation_params_changed)
        self.model.random_delay_max_changed.connect(self._on_operation_params_changed)
        self.model.detection_accuracy_changed.connect(self._on_operation_params_changed)
        self.model.retry_count_changed.connect(self._on_operation_params_changed)
        self.model.operation_timeout_changed.connect(self._on_operation_params_changed)
        
        self.model.window_check_changed.connect(self._on_safety_options_changed)
        self.model.scene_check_changed.connect(self._on_safety_options_changed)
        self.model.exception_check_changed.connect(self._on_safety_options_changed)
        self.model.auto_recovery_changed.connect(self._on_safety_options_changed)
        self.model.max_runtime_changed.connect(self._on_safety_options_changed)
        self.model.cpu_limit_changed.connect(self._on_safety_options_changed)
        self.model.memory_limit_changed.connect(self._on_safety_options_changed)
        self.model.emergency_key_changed.connect(self._on_safety_options_changed)
        self.model.mouse_corner_stop_changed.connect(self._on_safety_options_changed)
        
        self.model.performance_mode_changed.connect(self._on_performance_settings_changed)
        self.model.thread_count_changed.connect(self._on_performance_settings_changed)
        self.model.concurrent_tasks_changed.connect(self._on_performance_settings_changed)
        self.model.image_cache_changed.connect(self._on_performance_settings_changed)
        self.model.cache_size_changed.connect(self._on_performance_settings_changed)
        self.model.preload_resources_changed.connect(self._on_performance_settings_changed)
        self.model.smart_wait_changed.connect(self._on_performance_settings_changed)
        self.model.realtime_monitor_changed.connect(self._on_performance_settings_changed)
        self.model.monitor_interval_changed.connect(self._on_performance_settings_changed)
        self.model.performance_warning_changed.connect(self._on_performance_settings_changed)
        
        self.model.schedule_strategy_changed.connect(self._on_task_config_changed)
        self.model.task_interval_changed.connect(self._on_task_config_changed)
        self.model.task_retry_changed.connect(self._on_task_config_changed)
        self.model.task_timeout_action_changed.connect(self._on_task_config_changed)
        self.model.task_priority_changed.connect(self._on_task_config_changed)
        self.model.automation_rules_changed.connect(self._on_task_config_changed)
    
    def _on_operation_params_changed(self):
        """操作参数变化处理"""
        params = {
            "click_delay": self.model.click_delay,
            "key_delay": self.model.key_delay,
            "operation_interval": self.model.operation_interval,
            "random_delay_enabled": self.model.random_delay_enabled,
            "random_delay_min": self.model.random_delay_min,
            "random_delay_max": self.model.random_delay_max,
            "detection_accuracy": self.model.detection_accuracy,
            "retry_count": self.model.retry_count,
            "operation_timeout": self.model.operation_timeout,
        }
        self.operation_params_updated.emit(params)
    
    def _on_safety_options_changed(self):
        """安全选项变化处理"""
        options = {
            "window_check": self.model.window_check,
            "scene_check": self.model.scene_check,
            "exception_check": self.model.exception_check,
            "auto_recovery": self.model.auto_recovery,
            "max_runtime": self.model.max_runtime,
            "cpu_limit": self.model.cpu_limit,
            "memory_limit": self.model.memory_limit,
            "emergency_key": self.model.emergency_key,
            "mouse_corner_stop": self.model.mouse_corner_stop,
        }
        self.safety_options_updated.emit(options)
    
    def _on_performance_settings_changed(self):
        """性能设置变化处理"""
        settings = {
            "performance_mode": self.model.performance_mode,
            "thread_count": self.model.thread_count,
            "concurrent_tasks": self.model.concurrent_tasks,
            "image_cache": self.model.image_cache,
            "cache_size": self.model.cache_size,
            "preload_resources": self.model.preload_resources,
            "smart_wait": self.model.smart_wait,
            "realtime_monitor": self.model.realtime_monitor,
            "monitor_interval": self.model.monitor_interval,
            "performance_warning": self.model.performance_warning,
        }
        self.performance_settings_updated.emit(settings)
    
    def _on_task_config_changed(self):
        """任务配置变化处理"""
        config = {
            "schedule_strategy": self.model.schedule_strategy,
            "task_interval": self.model.task_interval,
            "task_retry": self.model.task_retry,
            "task_timeout_action": self.model.task_timeout_action,
            "task_priorities": self.model.task_priorities.copy(),
            "automation_rules": self.model.automation_rules.copy(),
        }
        self.task_config_updated.emit(config)
    
    # 显示控制
    def show(self):
        """显示组件"""
        self.view.show()
    
    def hide(self):
        """隐藏组件"""
        self.view.hide()
    
    def set_enabled(self, enabled: bool):
        """设置启用状态"""
        self.presenter.set_enabled_state(enabled)
    
    # 数据操作
    def load_settings(self):
        """加载设置"""
        self.presenter.load_settings()
    
    def get_current_settings(self) -> Dict[str, Any]:
        """获取当前设置"""
        return self.presenter.get_current_settings()
    
    def set_click_delay(self, delay: int):
        """设置点击延迟"""
        self.presenter.set_click_delay(delay)
    
    def set_key_delay(self, delay: int):
        """设置按键延迟"""
        self.model.set_key_delay(delay)
    
    def set_operation_interval(self, interval: int):
        """设置操作间隔"""
        self.model.set_operation_interval(interval)
    
    def set_random_delay_enabled(self, enabled: bool):
        """设置随机延迟启用"""
        self.model.set_random_delay_enabled(enabled)
    
    def set_random_delay_range(self, min_delay: int, max_delay: int):
        """设置随机延迟范围"""
        self.model.set_random_delay_min(min_delay)
        self.model.set_random_delay_max(max_delay)
    
    def set_detection_accuracy(self, accuracy: int):
        """设置检测精度"""
        self.model.set_detection_accuracy(accuracy)
    
    def set_retry_count(self, count: int):
        """设置重试次数"""
        self.model.set_retry_count(count)
    
    def set_operation_timeout(self, timeout: int):
        """设置操作超时"""
        self.model.set_operation_timeout(timeout)
    
    def set_window_check(self, enabled: bool):
        """设置窗口检查"""
        self.model.set_window_check(enabled)
    
    def set_scene_check(self, enabled: bool):
        """设置场景检查"""
        self.model.set_scene_check(enabled)
    
    def set_exception_check(self, enabled: bool):
        """设置异常检测"""
        self.model.set_exception_check(enabled)
    
    def set_auto_recovery(self, enabled: bool):
        """设置自动恢复"""
        self.model.set_auto_recovery(enabled)
    
    def set_max_runtime(self, runtime: int):
        """设置最大运行时间"""
        self.model.set_max_runtime(runtime)
    
    def set_cpu_limit(self, limit: int):
        """设置CPU限制"""
        self.model.set_cpu_limit(limit)
    
    def set_memory_limit(self, limit: int):
        """设置内存限制"""
        self.model.set_memory_limit(limit)
    
    def set_emergency_key(self, key: str):
        """设置紧急停止热键"""
        self.model.set_emergency_key(key)
    
    def set_mouse_corner_stop(self, enabled: bool):
        """设置鼠标角落停止"""
        self.model.set_mouse_corner_stop(enabled)
    
    def set_performance_mode(self, mode: str):
        """设置性能模式"""
        self.presenter.set_performance_mode(mode)
    
    def set_thread_count(self, count: int):
        """设置线程数"""
        self.model.set_thread_count(count)
    
    def set_concurrent_tasks(self, count: int):
        """设置并发任务数"""
        self.model.set_concurrent_tasks(count)
    
    def set_image_cache(self, enabled: bool):
        """设置图像缓存"""
        self.model.set_image_cache(enabled)
    
    def set_cache_size(self, size: int):
        """设置缓存大小"""
        self.model.set_cache_size(size)
    
    def set_preload_resources(self, enabled: bool):
        """设置预加载资源"""
        self.model.set_preload_resources(enabled)
    
    def set_smart_wait(self, enabled: bool):
        """设置智能等待"""
        self.model.set_smart_wait(enabled)
    
    def set_realtime_monitor(self, enabled: bool):
        """设置实时监控"""
        self.model.set_realtime_monitor(enabled)
    
    def set_monitor_interval(self, interval: int):
        """设置监控间隔"""
        self.model.set_monitor_interval(interval)
    
    def set_performance_warning(self, enabled: bool):
        """设置性能警告"""
        self.model.set_performance_warning(enabled)
    
    def set_schedule_strategy(self, strategy: str):
        """设置调度策略"""
        self.model.set_schedule_strategy(strategy)
    
    def set_task_interval(self, interval: int):
        """设置任务间隔"""
        self.model.set_task_interval(interval)
    
    def set_task_retry(self, retry: int):
        """设置任务重试"""
        self.model.set_task_retry(retry)
    
    def set_task_timeout_action(self, action: str):
        """设置任务超时处理"""
        self.model.set_task_timeout_action(action)
    
    def set_task_priority(self, task_key: str, priority: str):
        """设置任务优先级"""
        self.model.set_task_priority(task_key, priority)
    
    def set_automation_rules(self, rules: Dict[str, Any]):
        """设置自动化规则"""
        self.model.set_automation_rules(rules)
    
    # 操作方法
    def validate_settings(self) -> tuple[bool, str]:
        """验证设置"""
        return self.presenter.validate_settings()
    
    def reset_to_defaults(self):
        """重置为默认设置"""
        self.presenter.reset_to_defaults()
    
    def apply_settings(self) -> bool:
        """应用设置"""
        return self.presenter.apply_settings()
    
    def test_automation(self) -> bool:
        """测试自动化"""
        return self.presenter.test_automation()
    
    # 获取组件
    def get_widget(self):
        """获取View组件"""
        return self.view
    
    def get_model(self):
        """获取Model组件"""
        return self.model
    
    def get_view(self):
        """获取View组件"""
        return self.view
    
    def get_presenter(self):
        """获取Presenter组件"""
        return self.presenter
    
    def cleanup(self):
        """清理资源"""
        try:
            self.presenter.cleanup()
            logger.info("自动化设置MVP组合清理完成")
        except Exception as e:
            logger.error(f"清理资源失败: {e}")