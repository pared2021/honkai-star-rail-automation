"""自动化设置Presenter

该模块定义了自动化设置的Presenter层，负责协调Model和View，处理用户交互和业务逻辑。
"""

import json
from typing import Dict, Any, Optional
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QMessageBox

from src.ui.automation_settings.automation_settings_model import AutomationSettingsModel
from src.ui.automation_settings.automation_settings_view import AutomationSettingsView
from src.utils.logger import logger


class AutomationSettingsPresenter(QObject):
    """自动化设置Presenter类
    
    负责协调Model和View，处理用户交互和业务逻辑。
    """
    
    # 业务信号
    settings_changed = pyqtSignal(dict)  # 设置变化
    validation_result = pyqtSignal(bool, str)  # 验证结果
    test_result = pyqtSignal(bool, str)  # 测试结果
    settings_applied = pyqtSignal(bool, str)  # 设置应用结果
    settings_reset = pyqtSignal(bool, str)  # 设置重置结果
    import_result = pyqtSignal(bool, str)  # 导入结果
    export_result = pyqtSignal(bool, str)  # 导出结果
    
    def __init__(self, model: AutomationSettingsModel, view: AutomationSettingsView, parent=None):
        super().__init__(parent)
        self.model = model
        self.view = view
        
        self.connect_view_signals()
        self.connect_model_signals()
        self.init_data()
        
        logger.info("自动化设置Presenter初始化完成")
    
    def connect_view_signals(self):
        """连接View信号"""
        # 操作参数信号
        self.view.click_delay_changed.connect(self.model.set_click_delay)
        self.view.key_delay_changed.connect(self.model.set_key_delay)
        self.view.operation_interval_changed.connect(self.model.set_operation_interval)
        self.view.random_delay_enabled_changed.connect(self.model.set_random_delay_enabled)
        self.view.random_delay_min_changed.connect(self.model.set_random_delay_min)
        self.view.random_delay_max_changed.connect(self.model.set_random_delay_max)
        self.view.detection_accuracy_changed.connect(self.model.set_detection_accuracy)
        self.view.retry_count_changed.connect(self.model.set_retry_count)
        self.view.operation_timeout_changed.connect(self.model.set_operation_timeout)
        
        # 安全选项信号
        self.view.window_check_changed.connect(self.model.set_window_check)
        self.view.scene_check_changed.connect(self.model.set_scene_check)
        self.view.exception_check_changed.connect(self.model.set_exception_check)
        self.view.auto_recovery_changed.connect(self.model.set_auto_recovery)
        self.view.max_runtime_changed.connect(self.model.set_max_runtime)
        self.view.cpu_limit_changed.connect(self.model.set_cpu_limit)
        self.view.memory_limit_changed.connect(self.model.set_memory_limit)
        self.view.emergency_key_changed.connect(self.model.set_emergency_key)
        self.view.mouse_corner_stop_changed.connect(self.model.set_mouse_corner_stop)
        
        # 性能设置信号
        self.view.performance_mode_changed.connect(self._on_performance_mode_changed)
        self.view.thread_count_changed.connect(self.model.set_thread_count)
        self.view.concurrent_tasks_changed.connect(self.model.set_concurrent_tasks)
        self.view.image_cache_changed.connect(self.model.set_image_cache)
        self.view.cache_size_changed.connect(self.model.set_cache_size)
        self.view.preload_resources_changed.connect(self.model.set_preload_resources)
        self.view.smart_wait_changed.connect(self.model.set_smart_wait)
        self.view.realtime_monitor_changed.connect(self.model.set_realtime_monitor)
        self.view.monitor_interval_changed.connect(self.model.set_monitor_interval)
        self.view.performance_warning_changed.connect(self.model.set_performance_warning)
        
        # 任务配置信号
        self.view.schedule_strategy_changed.connect(self.model.set_schedule_strategy)
        self.view.task_interval_changed.connect(self.model.set_task_interval)
        self.view.task_retry_changed.connect(self.model.set_task_retry)
        self.view.task_timeout_action_changed.connect(self.model.set_task_timeout_action)
        self.view.task_priority_changed.connect(self.model.set_task_priority)
        self.view.automation_rules_changed.connect(self._on_automation_rules_changed)
        
        # 操作信号
        self.view.test_automation_requested.connect(self._on_test_automation)
        self.view.import_settings_requested.connect(self._on_import_settings)
        self.view.export_settings_requested.connect(self._on_export_settings)
        self.view.reset_settings_requested.connect(self._on_reset_settings)
        self.view.apply_settings_requested.connect(self._on_apply_settings)
        self.view.validate_rules_requested.connect(self._on_validate_rules)
    
    def connect_model_signals(self):
        """连接Model信号"""
        # 数据变化信号
        self.model.click_delay_changed.connect(self.view.update_click_delay)
        self.model.key_delay_changed.connect(self.view.update_key_delay)
        self.model.operation_interval_changed.connect(self.view.update_operation_interval)
        self.model.random_delay_enabled_changed.connect(self.view.update_random_delay_enabled)
        self.model.random_delay_min_changed.connect(self.view.update_random_delay_min)
        self.model.random_delay_max_changed.connect(self.view.update_random_delay_max)
        self.model.detection_accuracy_changed.connect(self.view.update_detection_accuracy)
        self.model.retry_count_changed.connect(self.view.update_retry_count)
        self.model.operation_timeout_changed.connect(self.view.update_operation_timeout)
        
        self.model.window_check_changed.connect(self.view.update_window_check)
        self.model.scene_check_changed.connect(self.view.update_scene_check)
        self.model.exception_check_changed.connect(self.view.update_exception_check)
        self.model.auto_recovery_changed.connect(self.view.update_auto_recovery)
        self.model.max_runtime_changed.connect(self.view.update_max_runtime)
        self.model.cpu_limit_changed.connect(self.view.update_cpu_limit)
        self.model.memory_limit_changed.connect(self.view.update_memory_limit)
        self.model.emergency_key_changed.connect(self.view.update_emergency_key)
        self.model.mouse_corner_stop_changed.connect(self.view.update_mouse_corner_stop)
        
        self.model.performance_mode_changed.connect(self.view.update_performance_mode)
        self.model.thread_count_changed.connect(self.view.update_thread_count)
        self.model.concurrent_tasks_changed.connect(self.view.update_concurrent_tasks)
        self.model.image_cache_changed.connect(self.view.update_image_cache)
        self.model.cache_size_changed.connect(self.view.update_cache_size)
        self.model.preload_resources_changed.connect(self.view.update_preload_resources)
        self.model.smart_wait_changed.connect(self.view.update_smart_wait)
        self.model.realtime_monitor_changed.connect(self.view.update_realtime_monitor)
        self.model.monitor_interval_changed.connect(self.view.update_monitor_interval)
        self.model.performance_warning_changed.connect(self.view.update_performance_warning)
        
        self.model.schedule_strategy_changed.connect(self.view.update_schedule_strategy)
        self.model.task_interval_changed.connect(self.view.update_task_interval)
        self.model.task_retry_changed.connect(self.view.update_task_retry)
        self.model.task_timeout_action_changed.connect(self.view.update_task_timeout_action)
        self.model.task_priority_changed.connect(self.view.update_task_priority)
        self.model.automation_rules_changed.connect(self.view.update_automation_rules)
        
        # 状态信号
        self.model.validation_result.connect(self._on_validation_result)
        self.model.test_result.connect(self._on_test_result)
        
        # 错误信号
        self.model.error_occurred.connect(self._on_model_error)
    
    def init_data(self):
        """初始化数据"""
        try:
            # 加载设置
            self.model.load_settings()
            logger.info("自动化设置数据初始化完成")
        except Exception as e:
            logger.error(f"初始化数据失败: {e}")
            self.view.show_message("错误", f"初始化数据失败: {e}", "error")
    
    def _on_performance_mode_changed(self, mode: str):
        """性能模式变化处理"""
        try:
            self.model.set_performance_mode(mode)
            # 根据性能模式更新相关设置
            self.model.update_performance_settings(mode)
        except Exception as e:
            logger.error(f"性能模式变化处理失败: {e}")
    
    def _on_automation_rules_changed(self, rules_text: str):
        """自动化规则变化处理"""
        try:
            # 尝试解析JSON
            rules = json.loads(rules_text)
            self.model.set_automation_rules(rules)
        except json.JSONDecodeError as e:
            logger.warning(f"自动化规则JSON格式错误: {e}")
            # 不显示错误，让用户继续编辑
        except Exception as e:
            logger.error(f"自动化规则变化处理失败: {e}")
    
    def _on_test_automation(self):
        """测试自动化"""
        try:
            self.view.set_loading_state(True)
            success = self.model.test_automation()
            if success:
                self.view.show_message("测试完成", "自动化测试成功！")
            else:
                self.view.show_message("测试失败", "自动化测试失败，请检查配置。", "warning")
        except Exception as e:
            logger.error(f"测试自动化失败: {e}")
            self.view.show_message("错误", f"测试失败: {e}", "error")
        finally:
            self.view.set_loading_state(False)
    
    def _on_import_settings(self):
        """导入设置"""
        try:
            file_path = self.view.show_file_dialog("open", "JSON files (*.json)")
            if not file_path:
                return
            
            with open(file_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)
            
            # 验证设置格式
            if not isinstance(settings, dict):
                self.view.show_message("错误", "配置文件格式错误", "error")
                return
            
            # 应用设置
            self._apply_imported_settings(settings)
            self.view.show_message("成功", "配置导入成功！")
            self.import_result.emit(True, "配置导入成功")
            
        except json.JSONDecodeError:
            self.view.show_message("错误", "配置文件格式错误", "error")
            self.import_result.emit(False, "配置文件格式错误")
        except Exception as e:
            logger.error(f"导入设置失败: {e}")
            self.view.show_message("错误", f"导入失败: {e}", "error")
            self.import_result.emit(False, f"导入失败: {e}")
    
    def _on_export_settings(self):
        """导出设置"""
        try:
            file_path = self.view.show_file_dialog("save", "JSON files (*.json)")
            if not file_path:
                return
            
            settings = self.model.get_current_settings()
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
            
            self.view.show_message("成功", "配置导出成功！")
            self.export_result.emit(True, "配置导出成功")
            
        except Exception as e:
            logger.error(f"导出设置失败: {e}")
            self.view.show_message("错误", f"导出失败: {e}", "error")
            self.export_result.emit(False, f"导出失败: {e}")
    
    def _on_reset_settings(self):
        """重置设置"""
        try:
            if not self.view.show_confirmation("确认重置", "确定要重置为默认设置吗？这将丢失当前所有配置。"):
                return
            
            self.model.reset_to_defaults()
            self.view.show_message("成功", "设置已重置为默认值！")
            self.settings_reset.emit(True, "设置重置成功")
            
        except Exception as e:
            logger.error(f"重置设置失败: {e}")
            self.view.show_message("错误", f"重置失败: {e}", "error")
            self.settings_reset.emit(False, f"重置失败: {e}")
    
    def _on_apply_settings(self):
        """应用设置"""
        try:
            # 验证设置
            is_valid, error_msg = self.model.validate_settings()
            if not is_valid:
                self.view.show_message("验证失败", error_msg, "warning")
                return
            
            # 应用设置
            success = self.model.apply_settings()
            if success:
                self.view.show_message("成功", "设置应用成功！")
                self.settings_applied.emit(True, "设置应用成功")
            else:
                self.view.show_message("失败", "设置应用失败", "error")
                self.settings_applied.emit(False, "设置应用失败")
                
        except Exception as e:
            logger.error(f"应用设置失败: {e}")
            self.view.show_message("错误", f"应用失败: {e}", "error")
            self.settings_applied.emit(False, f"应用失败: {e}")
    
    def _on_validate_rules(self, rules_text: str):
        """验证自动化规则"""
        try:
            is_valid, error_msg = self.model.validate_automation_rules(rules_text)
            if is_valid:
                self.view.show_message("验证成功", "自动化规则格式正确！")
            else:
                self.view.show_message("验证失败", f"规则验证失败: {error_msg}", "warning")
        except Exception as e:
            logger.error(f"验证规则失败: {e}")
            self.view.show_message("错误", f"验证失败: {e}", "error")
    
    def _on_validation_result(self, is_valid: bool, message: str):
        """处理验证结果"""
        self.validation_result.emit(is_valid, message)
    
    def _on_test_result(self, success: bool, message: str):
        """处理测试结果"""
        self.test_result.emit(success, message)
    
    def _on_model_error(self, error_msg: str):
        """处理Model错误"""
        logger.error(f"Model错误: {error_msg}")
        self.view.show_message("错误", error_msg, "error")
    
    def _apply_imported_settings(self, settings: Dict[str, Any]):
        """应用导入的设置"""
        try:
            # 操作参数
            if "operation_params" in settings:
                params = settings["operation_params"]
                if "click_delay" in params:
                    self.model.set_click_delay(params["click_delay"])
                if "key_delay" in params:
                    self.model.set_key_delay(params["key_delay"])
                if "operation_interval" in params:
                    self.model.set_operation_interval(params["operation_interval"])
                if "random_delay_enabled" in params:
                    self.model.set_random_delay_enabled(params["random_delay_enabled"])
                if "random_delay_min" in params:
                    self.model.set_random_delay_min(params["random_delay_min"])
                if "random_delay_max" in params:
                    self.model.set_random_delay_max(params["random_delay_max"])
                if "detection_accuracy" in params:
                    self.model.set_detection_accuracy(params["detection_accuracy"])
                if "retry_count" in params:
                    self.model.set_retry_count(params["retry_count"])
                if "operation_timeout" in params:
                    self.model.set_operation_timeout(params["operation_timeout"])
            
            # 安全选项
            if "safety_options" in settings:
                safety = settings["safety_options"]
                if "window_check" in safety:
                    self.model.set_window_check(safety["window_check"])
                if "scene_check" in safety:
                    self.model.set_scene_check(safety["scene_check"])
                if "exception_check" in safety:
                    self.model.set_exception_check(safety["exception_check"])
                if "auto_recovery" in safety:
                    self.model.set_auto_recovery(safety["auto_recovery"])
                if "max_runtime" in safety:
                    self.model.set_max_runtime(safety["max_runtime"])
                if "cpu_limit" in safety:
                    self.model.set_cpu_limit(safety["cpu_limit"])
                if "memory_limit" in safety:
                    self.model.set_memory_limit(safety["memory_limit"])
                if "emergency_key" in safety:
                    self.model.set_emergency_key(safety["emergency_key"])
                if "mouse_corner_stop" in safety:
                    self.model.set_mouse_corner_stop(safety["mouse_corner_stop"])
            
            # 性能设置
            if "performance_settings" in settings:
                performance = settings["performance_settings"]
                if "performance_mode" in performance:
                    self.model.set_performance_mode(performance["performance_mode"])
                if "thread_count" in performance:
                    self.model.set_thread_count(performance["thread_count"])
                if "concurrent_tasks" in performance:
                    self.model.set_concurrent_tasks(performance["concurrent_tasks"])
                if "image_cache" in performance:
                    self.model.set_image_cache(performance["image_cache"])
                if "cache_size" in performance:
                    self.model.set_cache_size(performance["cache_size"])
                if "preload_resources" in performance:
                    self.model.set_preload_resources(performance["preload_resources"])
                if "smart_wait" in performance:
                    self.model.set_smart_wait(performance["smart_wait"])
                if "realtime_monitor" in performance:
                    self.model.set_realtime_monitor(performance["realtime_monitor"])
                if "monitor_interval" in performance:
                    self.model.set_monitor_interval(performance["monitor_interval"])
                if "performance_warning" in performance:
                    self.model.set_performance_warning(performance["performance_warning"])
            
            # 任务配置
            if "task_config" in settings:
                task = settings["task_config"]
                if "schedule_strategy" in task:
                    self.model.set_schedule_strategy(task["schedule_strategy"])
                if "task_interval" in task:
                    self.model.set_task_interval(task["task_interval"])
                if "task_retry" in task:
                    self.model.set_task_retry(task["task_retry"])
                if "task_timeout_action" in task:
                    self.model.set_task_timeout_action(task["task_timeout_action"])
                if "task_priorities" in task:
                    for task_key, priority in task["task_priorities"].items():
                        self.model.set_task_priority(task_key, priority)
                if "automation_rules" in task:
                    self.model.set_automation_rules(task["automation_rules"])
                    
        except Exception as e:
            logger.error(f"应用导入设置失败: {e}")
            raise
    
    # 公共接口
    def load_settings(self):
        """加载设置"""
        try:
            self.model.load_settings()
        except Exception as e:
            logger.error(f"加载设置失败: {e}")
            raise
    
    def get_current_settings(self) -> Dict[str, Any]:
        """获取当前设置"""
        return self.model.get_current_settings()
    
    def set_click_delay(self, delay: int):
        """设置点击延迟"""
        self.model.set_click_delay(delay)
    
    def set_performance_mode(self, mode: str):
        """设置性能模式"""
        self.model.set_performance_mode(mode)
        self.model.update_performance_settings(mode)
    
    def validate_settings(self) -> tuple[bool, str]:
        """验证设置"""
        return self.model.validate_settings()
    
    def reset_to_defaults(self):
        """重置为默认设置"""
        self.model.reset_to_defaults()
    
    def apply_settings(self) -> bool:
        """应用设置"""
        return self.model.apply_settings()
    
    def test_automation(self) -> bool:
        """测试自动化"""
        return self.model.test_automation()
    
    def set_enabled_state(self, enabled: bool):
        """设置启用状态"""
        self.view.set_enabled_state(enabled)
    
    def cleanup(self):
        """清理资源"""
        try:
            if hasattr(self.model, 'cleanup'):
                self.model.cleanup()
            if hasattr(self.view, 'cleanup'):
                self.view.cleanup()
            logger.info("自动化设置Presenter清理完成")
        except Exception as e:
            logger.error(f"清理资源失败: {e}")