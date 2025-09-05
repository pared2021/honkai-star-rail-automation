"""自动化设置Model

该模块定义了自动化设置的Model层，负责管理自动化设置的数据状态和业务逻辑。
"""

import json
from typing import Dict, Any, Optional
from PyQt6.QtCore import QObject, pyqtSignal

from ...services.ui_service_facade import IUIServiceFacade
from src.utils.logger import logger


class AutomationSettingsModel(QObject):
    """自动化设置Model类
    
    负责管理自动化设置的数据状态和业务逻辑。
    """
    
    # 操作参数信号
    click_delay_changed = pyqtSignal(int)  # 点击延迟变化
    key_delay_changed = pyqtSignal(int)  # 按键延迟变化
    operation_interval_changed = pyqtSignal(int)  # 操作间隔变化
    random_delay_enabled_changed = pyqtSignal(bool)  # 随机延迟启用状态变化
    random_delay_min_changed = pyqtSignal(int)  # 随机延迟最小值变化
    random_delay_max_changed = pyqtSignal(int)  # 随机延迟最大值变化
    detection_accuracy_changed = pyqtSignal(int)  # 检测精度变化
    retry_count_changed = pyqtSignal(int)  # 重试次数变化
    operation_timeout_changed = pyqtSignal(int)  # 操作超时变化
    
    # 安全选项信号
    window_check_changed = pyqtSignal(bool)  # 窗口检查变化
    scene_check_changed = pyqtSignal(bool)  # 场景检查变化
    exception_check_changed = pyqtSignal(bool)  # 异常检测变化
    auto_recovery_changed = pyqtSignal(bool)  # 自动恢复变化
    max_runtime_changed = pyqtSignal(int)  # 最大运行时间变化
    cpu_limit_changed = pyqtSignal(int)  # CPU限制变化
    memory_limit_changed = pyqtSignal(int)  # 内存限制变化
    emergency_key_changed = pyqtSignal(str)  # 紧急停止热键变化
    mouse_corner_stop_changed = pyqtSignal(bool)  # 鼠标角落停止变化
    
    # 性能设置信号
    performance_mode_changed = pyqtSignal(str)  # 性能模式变化
    thread_count_changed = pyqtSignal(int)  # 线程数变化
    concurrent_tasks_changed = pyqtSignal(int)  # 并发任务数变化
    image_cache_changed = pyqtSignal(bool)  # 图像缓存变化
    cache_size_changed = pyqtSignal(int)  # 缓存大小变化
    preload_resources_changed = pyqtSignal(bool)  # 预加载资源变化
    smart_wait_changed = pyqtSignal(bool)  # 智能等待变化
    realtime_monitor_changed = pyqtSignal(bool)  # 实时监控变化
    monitor_interval_changed = pyqtSignal(int)  # 监控间隔变化
    performance_warning_changed = pyqtSignal(bool)  # 性能警告变化
    
    # 任务配置信号
    schedule_strategy_changed = pyqtSignal(str)  # 调度策略变化
    task_interval_changed = pyqtSignal(int)  # 任务间隔变化
    task_retry_changed = pyqtSignal(int)  # 任务重试变化
    task_timeout_action_changed = pyqtSignal(str)  # 任务超时处理变化
    task_priorities_changed = pyqtSignal(dict)  # 任务优先级变化
    automation_rules_changed = pyqtSignal(dict)  # 自动化规则变化
    
    # 状态信号
    settings_validated = pyqtSignal(bool, str)  # 设置验证结果
    automation_tested = pyqtSignal(bool, str)  # 自动化测试结果
    
    # 错误信号
    model_error = pyqtSignal(str)  # Model错误
    
    def __init__(self, ui_service: IUIServiceFacade, parent=None):
        super().__init__(parent)
        self.ui_service = ui_service
        
        # 操作参数
        self._click_delay = 200
        self._key_delay = 100
        self._operation_interval = 500
        self._random_delay_enabled = True
        self._random_delay_min = 50
        self._random_delay_max = 200
        self._detection_accuracy = 85
        self._retry_count = 3
        self._operation_timeout = 30
        
        # 安全选项
        self._window_check = True
        self._scene_check = True
        self._exception_check = True
        self._auto_recovery = True
        self._max_runtime = 120
        self._cpu_limit = 50
        self._memory_limit = 512
        self._emergency_key = "F12"
        self._mouse_corner_stop = False
        
        # 性能设置
        self._performance_mode = "平衡模式"
        self._thread_count = 2
        self._concurrent_tasks = 1
        self._image_cache = True
        self._cache_size = 100
        self._preload_resources = False
        self._smart_wait = True
        self._realtime_monitor = True
        self._monitor_interval = 5
        self._performance_warning = True
        
        # 任务配置
        self._schedule_strategy = "智能调度"
        self._task_interval = 10
        self._task_retry = 2
        self._task_timeout_action = "重试任务"
        self._task_priorities = {}
        self._automation_rules = {}
        
        logger.info("自动化设置Model初始化完成")
    
    # 操作参数属性
    @property
    def click_delay(self) -> int:
        return self._click_delay
    
    @click_delay.setter
    def click_delay(self, value: int):
        if self._click_delay != value:
            self._click_delay = value
            self.click_delay_changed.emit(value)
    
    @property
    def key_delay(self) -> int:
        return self._key_delay
    
    @key_delay.setter
    def key_delay(self, value: int):
        if self._key_delay != value:
            self._key_delay = value
            self.key_delay_changed.emit(value)
    
    @property
    def operation_interval(self) -> int:
        return self._operation_interval
    
    @operation_interval.setter
    def operation_interval(self, value: int):
        if self._operation_interval != value:
            self._operation_interval = value
            self.operation_interval_changed.emit(value)
    
    @property
    def random_delay_enabled(self) -> bool:
        return self._random_delay_enabled
    
    @random_delay_enabled.setter
    def random_delay_enabled(self, value: bool):
        if self._random_delay_enabled != value:
            self._random_delay_enabled = value
            self.random_delay_enabled_changed.emit(value)
    
    @property
    def random_delay_min(self) -> int:
        return self._random_delay_min
    
    @random_delay_min.setter
    def random_delay_min(self, value: int):
        if self._random_delay_min != value:
            self._random_delay_min = value
            self.random_delay_min_changed.emit(value)
    
    @property
    def random_delay_max(self) -> int:
        return self._random_delay_max
    
    @random_delay_max.setter
    def random_delay_max(self, value: int):
        if self._random_delay_max != value:
            self._random_delay_max = value
            self.random_delay_max_changed.emit(value)
    
    @property
    def detection_accuracy(self) -> int:
        return self._detection_accuracy
    
    @detection_accuracy.setter
    def detection_accuracy(self, value: int):
        if self._detection_accuracy != value:
            self._detection_accuracy = value
            self.detection_accuracy_changed.emit(value)
    
    @property
    def retry_count(self) -> int:
        return self._retry_count
    
    @retry_count.setter
    def retry_count(self, value: int):
        if self._retry_count != value:
            self._retry_count = value
            self.retry_count_changed.emit(value)
    
    @property
    def operation_timeout(self) -> int:
        return self._operation_timeout
    
    @operation_timeout.setter
    def operation_timeout(self, value: int):
        if self._operation_timeout != value:
            self._operation_timeout = value
            self.operation_timeout_changed.emit(value)
    
    # 安全选项属性
    @property
    def window_check(self) -> bool:
        return self._window_check
    
    @window_check.setter
    def window_check(self, value: bool):
        if self._window_check != value:
            self._window_check = value
            self.window_check_changed.emit(value)
    
    @property
    def scene_check(self) -> bool:
        return self._scene_check
    
    @scene_check.setter
    def scene_check(self, value: bool):
        if self._scene_check != value:
            self._scene_check = value
            self.scene_check_changed.emit(value)
    
    @property
    def exception_check(self) -> bool:
        return self._exception_check
    
    @exception_check.setter
    def exception_check(self, value: bool):
        if self._exception_check != value:
            self._exception_check = value
            self.exception_check_changed.emit(value)
    
    @property
    def auto_recovery(self) -> bool:
        return self._auto_recovery
    
    @auto_recovery.setter
    def auto_recovery(self, value: bool):
        if self._auto_recovery != value:
            self._auto_recovery = value
            self.auto_recovery_changed.emit(value)
    
    @property
    def max_runtime(self) -> int:
        return self._max_runtime
    
    @max_runtime.setter
    def max_runtime(self, value: int):
        if self._max_runtime != value:
            self._max_runtime = value
            self.max_runtime_changed.emit(value)
    
    @property
    def cpu_limit(self) -> int:
        return self._cpu_limit
    
    @cpu_limit.setter
    def cpu_limit(self, value: int):
        if self._cpu_limit != value:
            self._cpu_limit = value
            self.cpu_limit_changed.emit(value)
    
    @property
    def memory_limit(self) -> int:
        return self._memory_limit
    
    @memory_limit.setter
    def memory_limit(self, value: int):
        if self._memory_limit != value:
            self._memory_limit = value
            self.memory_limit_changed.emit(value)
    
    @property
    def emergency_key(self) -> str:
        return self._emergency_key
    
    @emergency_key.setter
    def emergency_key(self, value: str):
        if self._emergency_key != value:
            self._emergency_key = value
            self.emergency_key_changed.emit(value)
    
    @property
    def mouse_corner_stop(self) -> bool:
        return self._mouse_corner_stop
    
    @mouse_corner_stop.setter
    def mouse_corner_stop(self, value: bool):
        if self._mouse_corner_stop != value:
            self._mouse_corner_stop = value
            self.mouse_corner_stop_changed.emit(value)
    
    # 性能设置属性
    @property
    def performance_mode(self) -> str:
        return self._performance_mode
    
    @performance_mode.setter
    def performance_mode(self, value: str):
        if self._performance_mode != value:
            self._performance_mode = value
            self.performance_mode_changed.emit(value)
    
    @property
    def thread_count(self) -> int:
        return self._thread_count
    
    @thread_count.setter
    def thread_count(self, value: int):
        if self._thread_count != value:
            self._thread_count = value
            self.thread_count_changed.emit(value)
    
    @property
    def concurrent_tasks(self) -> int:
        return self._concurrent_tasks
    
    @concurrent_tasks.setter
    def concurrent_tasks(self, value: int):
        if self._concurrent_tasks != value:
            self._concurrent_tasks = value
            self.concurrent_tasks_changed.emit(value)
    
    @property
    def image_cache(self) -> bool:
        return self._image_cache
    
    @image_cache.setter
    def image_cache(self, value: bool):
        if self._image_cache != value:
            self._image_cache = value
            self.image_cache_changed.emit(value)
    
    @property
    def cache_size(self) -> int:
        return self._cache_size
    
    @cache_size.setter
    def cache_size(self, value: int):
        if self._cache_size != value:
            self._cache_size = value
            self.cache_size_changed.emit(value)
    
    @property
    def preload_resources(self) -> bool:
        return self._preload_resources
    
    @preload_resources.setter
    def preload_resources(self, value: bool):
        if self._preload_resources != value:
            self._preload_resources = value
            self.preload_resources_changed.emit(value)
    
    @property
    def smart_wait(self) -> bool:
        return self._smart_wait
    
    @smart_wait.setter
    def smart_wait(self, value: bool):
        if self._smart_wait != value:
            self._smart_wait = value
            self.smart_wait_changed.emit(value)
    
    @property
    def realtime_monitor(self) -> bool:
        return self._realtime_monitor
    
    @realtime_monitor.setter
    def realtime_monitor(self, value: bool):
        if self._realtime_monitor != value:
            self._realtime_monitor = value
            self.realtime_monitor_changed.emit(value)
    
    @property
    def monitor_interval(self) -> int:
        return self._monitor_interval
    
    @monitor_interval.setter
    def monitor_interval(self, value: int):
        if self._monitor_interval != value:
            self._monitor_interval = value
            self.monitor_interval_changed.emit(value)
    
    @property
    def performance_warning(self) -> bool:
        return self._performance_warning
    
    @performance_warning.setter
    def performance_warning(self, value: bool):
        if self._performance_warning != value:
            self._performance_warning = value
            self.performance_warning_changed.emit(value)
    
    # 任务配置属性
    @property
    def schedule_strategy(self) -> str:
        return self._schedule_strategy
    
    @schedule_strategy.setter
    def schedule_strategy(self, value: str):
        if self._schedule_strategy != value:
            self._schedule_strategy = value
            self.schedule_strategy_changed.emit(value)
    
    @property
    def task_interval(self) -> int:
        return self._task_interval
    
    @task_interval.setter
    def task_interval(self, value: int):
        if self._task_interval != value:
            self._task_interval = value
            self.task_interval_changed.emit(value)
    
    @property
    def task_retry(self) -> int:
        return self._task_retry
    
    @task_retry.setter
    def task_retry(self, value: int):
        if self._task_retry != value:
            self._task_retry = value
            self.task_retry_changed.emit(value)
    
    @property
    def task_timeout_action(self) -> str:
        return self._task_timeout_action
    
    @task_timeout_action.setter
    def task_timeout_action(self, value: str):
        if self._task_timeout_action != value:
            self._task_timeout_action = value
            self.task_timeout_action_changed.emit(value)
    
    @property
    def task_priorities(self) -> Dict[str, str]:
        return self._task_priorities.copy()
    
    @task_priorities.setter
    def task_priorities(self, value: Dict[str, str]):
        if self._task_priorities != value:
            self._task_priorities = value.copy()
            self.task_priorities_changed.emit(self._task_priorities)
    
    @property
    def automation_rules(self) -> Dict[str, Any]:
        return self._automation_rules.copy()
    
    @automation_rules.setter
    def automation_rules(self, value: Dict[str, Any]):
        if self._automation_rules != value:
            self._automation_rules = value.copy()
            self.automation_rules_changed.emit(self._automation_rules)
    
    # 业务方法
    def load_settings(self):
        """从配置管理器加载设置"""
        try:
            automation_config = self.ui_service.get_automation_config()
            
            # 加载操作参数
            self.click_delay = automation_config.get("click_delay", 200)
            self.key_delay = automation_config.get("key_delay", 100)
            self.operation_interval = automation_config.get("operation_interval", 500)
            self.random_delay_enabled = automation_config.get("random_delay_enabled", True)
            self.random_delay_min = automation_config.get("random_delay_min", 50)
            self.random_delay_max = automation_config.get("random_delay_max", 200)
            self.detection_accuracy = automation_config.get("detection_accuracy", 85)
            self.retry_count = automation_config.get("retry_count", 3)
            self.operation_timeout = automation_config.get("operation_timeout", 30)
            
            # 加载安全选项
            self.window_check = automation_config.get("window_check", True)
            self.scene_check = automation_config.get("scene_check", True)
            self.exception_check = automation_config.get("exception_check", True)
            self.auto_recovery = automation_config.get("auto_recovery", True)
            self.max_runtime = automation_config.get("max_runtime", 120)
            self.cpu_limit = automation_config.get("cpu_limit", 50)
            self.memory_limit = automation_config.get("memory_limit", 512)
            self.emergency_key = automation_config.get("emergency_key", "F12")
            self.mouse_corner_stop = automation_config.get("mouse_corner_stop", False)
            
            # 加载性能设置
            self.performance_mode = automation_config.get("performance_mode", "平衡模式")
            self.thread_count = automation_config.get("thread_count", 2)
            self.concurrent_tasks = automation_config.get("concurrent_tasks", 1)
            self.image_cache = automation_config.get("image_cache", True)
            self.cache_size = automation_config.get("cache_size", 100)
            self.preload_resources = automation_config.get("preload_resources", False)
            self.smart_wait = automation_config.get("smart_wait", True)
            self.realtime_monitor = automation_config.get("realtime_monitor", True)
            self.monitor_interval = automation_config.get("monitor_interval", 5)
            self.performance_warning = automation_config.get("performance_warning", True)
            
            # 加载任务配置
            self.schedule_strategy = automation_config.get("schedule_strategy", "智能调度")
            self.task_interval = automation_config.get("task_interval", 10)
            self.task_retry = automation_config.get("task_retry", 2)
            self.task_timeout_action = automation_config.get("task_timeout_action", "重试任务")
            self.task_priorities = automation_config.get("task_priorities", {})
            self.automation_rules = automation_config.get("automation_rules", {})
            
            logger.info("自动化设置加载完成")
            
        except Exception as e:
            error_msg = f"加载自动化设置失败: {e}"
            logger.error(error_msg)
            self.model_error.emit(error_msg)
    
    def validate_settings(self) -> tuple[bool, str]:
        """验证设置有效性"""
        try:
            # 验证随机延迟范围
            if self.random_delay_min >= self.random_delay_max:
                return False, "随机延迟最小值不能大于等于最大值"
            
            # 验证线程数和并发任务数
            if self.concurrent_tasks > self.thread_count:
                return False, "并发任务数不能大于工作线程数"
            
            # 验证紧急停止热键
            if not self.emergency_key.strip():
                return False, "紧急停止热键不能为空"
            
            # 验证自动化规则
            if self.automation_rules:
                required_keys = ["daily_reset_time", "auto_start_tasks", "conditions"]
                for key in required_keys:
                    if key not in self.automation_rules:
                        return False, f"自动化规则缺少必需的配置项: {key}"
            
            self.settings_validated.emit(True, "设置验证通过")
            return True, "设置验证通过"
            
        except Exception as e:
            error_msg = f"设置验证失败: {e}"
            logger.error(error_msg)
            self.settings_validated.emit(False, error_msg)
            return False, error_msg
    
    def reset_to_defaults(self):
        """重置为默认设置"""
        try:
            # 重置操作参数
            self.click_delay = 200
            self.key_delay = 100
            self.operation_interval = 500
            self.random_delay_enabled = True
            self.random_delay_min = 50
            self.random_delay_max = 200
            self.detection_accuracy = 85
            self.retry_count = 3
            self.operation_timeout = 30
            
            # 重置安全选项
            self.window_check = True
            self.scene_check = True
            self.exception_check = True
            self.auto_recovery = True
            self.max_runtime = 120
            self.cpu_limit = 50
            self.memory_limit = 512
            self.emergency_key = "F12"
            self.mouse_corner_stop = False
            
            # 重置性能设置
            self.performance_mode = "平衡模式"
            self.thread_count = 2
            self.concurrent_tasks = 1
            self.image_cache = True
            self.cache_size = 100
            self.preload_resources = False
            self.smart_wait = True
            self.realtime_monitor = True
            self.monitor_interval = 5
            self.performance_warning = True
            
            # 重置任务配置
            self.schedule_strategy = "智能调度"
            self.task_interval = 10
            self.task_retry = 2
            self.task_timeout_action = "重试任务"
            self.task_priorities = {}
            self.automation_rules = {
                "daily_reset_time": "04:00",
                "auto_start_tasks": ["daily_missions", "stamina_consumption"],
                "conditions": {"stamina_threshold": 160, "skip_on_weekend": False},
            }
            
            logger.info("自动化设置已重置为默认值")
            
        except Exception as e:
            error_msg = f"重置设置失败: {e}"
            logger.error(error_msg)
            self.model_error.emit(error_msg)
    
    def apply_settings(self) -> bool:
        """应用设置到配置管理器"""
        try:
            # 验证设置
            is_valid, error_msg = self.validate_settings()
            if not is_valid:
                return False
            
            # 保存到配置管理器
            settings = self.get_current_settings()
            self.ui_service.save_automation_config(settings)
            
            logger.info("自动化设置已应用")
            return True
            
        except Exception as e:
            error_msg = f"应用设置失败: {e}"
            logger.error(error_msg)
            self.model_error.emit(error_msg)
            return False
    
    def test_automation(self) -> bool:
        """测试自动化设置"""
        try:
            # 基础配置验证
            is_valid, error_msg = self.validate_settings()
            if not is_valid:
                self.automation_tested.emit(False, error_msg)
                return False
            
            # 模拟测试过程
            test_msg = "自动化设置测试完成！\n\n基础配置验证通过。"
            self.automation_tested.emit(True, test_msg)
            
            logger.info("自动化设置测试完成")
            return True
            
        except Exception as e:
            error_msg = f"自动化设置测试失败: {e}"
            logger.error(error_msg)
            self.automation_tested.emit(False, error_msg)
            return False
    
    def validate_automation_rules(self, rules_text: str) -> tuple[bool, str]:
        """验证自动化规则"""
        try:
            rules = json.loads(rules_text)
            
            # 基本验证
            required_keys = ["daily_reset_time", "auto_start_tasks", "conditions"]
            for key in required_keys:
                if key not in rules:
                    return False, f"缺少必需的配置项: {key}"
            
            return True, "自动化规则格式正确"
            
        except json.JSONDecodeError as e:
            return False, f"JSON格式错误：{str(e)}"
        except Exception as e:
            return False, f"规则验证失败：{str(e)}"
    
    def set_task_priority(self, task_key: str, priority: str):
        """设置任务优先级"""
        priorities = self.task_priorities
        priorities[task_key] = priority
        self.task_priorities = priorities
    
    def get_task_priority(self, task_key: str) -> str:
        """获取任务优先级"""
        return self.task_priorities.get(task_key, "中")
    
    def update_performance_mode_settings(self, mode: str):
        """根据性能模式更新相关设置"""
        if mode == "节能模式":
            self.thread_count = 1
            self.concurrent_tasks = 1
            self.cpu_limit = 30
            self.cache_size = 50
        elif mode == "平衡模式":
            self.thread_count = 2
            self.concurrent_tasks = 1
            self.cpu_limit = 50
            self.cache_size = 100
        elif mode == "高性能模式":
            self.thread_count = 4
            self.concurrent_tasks = 2
            self.cpu_limit = 80
            self.cache_size = 200
        # 自定义模式不自动调整
    
    def get_current_settings(self) -> Dict[str, Any]:
        """获取当前所有设置"""
        return {
            # 操作参数
            "click_delay": self.click_delay,
            "key_delay": self.key_delay,
            "operation_interval": self.operation_interval,
            "random_delay_enabled": self.random_delay_enabled,
            "random_delay_min": self.random_delay_min,
            "random_delay_max": self.random_delay_max,
            "detection_accuracy": self.detection_accuracy,
            "retry_count": self.retry_count,
            "operation_timeout": self.operation_timeout,
            # 安全选项
            "window_check": self.window_check,
            "scene_check": self.scene_check,
            "exception_check": self.exception_check,
            "auto_recovery": self.auto_recovery,
            "max_runtime": self.max_runtime,
            "cpu_limit": self.cpu_limit,
            "memory_limit": self.memory_limit,
            "emergency_key": self.emergency_key,
            "mouse_corner_stop": self.mouse_corner_stop,
            # 性能设置
            "performance_mode": self.performance_mode,
            "thread_count": self.thread_count,
            "concurrent_tasks": self.concurrent_tasks,
            "image_cache": self.image_cache,
            "cache_size": self.cache_size,
            "preload_resources": self.preload_resources,
            "smart_wait": self.smart_wait,
            "realtime_monitor": self.realtime_monitor,
            "monitor_interval": self.monitor_interval,
            "performance_warning": self.performance_warning,
            # 任务配置
            "schedule_strategy": self.schedule_strategy,
            "task_interval": self.task_interval,
            "task_retry": self.task_retry,
            "task_timeout_action": self.task_timeout_action,
            "task_priorities": self.task_priorities,
            "automation_rules": self.automation_rules,
        }
    
    def cleanup(self):
        """清理资源"""
        try:
            logger.info("自动化设置Model清理完成")
        except Exception as e:
            logger.error(f"清理资源失败: {e}")