"""自动化设置View

该模块定义了自动化设置的View层，负责UI界面的展示和用户交互。
"""

import json
from typing import Dict, Any, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QGroupBox,
    QLabel, QSpinBox, QSlider, QCheckBox, QComboBox, QPushButton,
    QTextEdit, QLineEdit, QFileDialog, QMessageBox, QProgressBar
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from src.ui.common.base_widget import BaseWidget
from src.utils.logger import logger


class AutomationSettingsView(BaseWidget):
    """自动化设置View类
    
    负责UI界面的展示和用户交互。
    """
    
    # 操作参数信号
    click_delay_changed = pyqtSignal(int)
    key_delay_changed = pyqtSignal(int)
    operation_interval_changed = pyqtSignal(int)
    random_delay_enabled_changed = pyqtSignal(bool)
    random_delay_min_changed = pyqtSignal(int)
    random_delay_max_changed = pyqtSignal(int)
    detection_accuracy_changed = pyqtSignal(int)
    retry_count_changed = pyqtSignal(int)
    operation_timeout_changed = pyqtSignal(int)
    
    # 安全选项信号
    window_check_changed = pyqtSignal(bool)
    scene_check_changed = pyqtSignal(bool)
    exception_check_changed = pyqtSignal(bool)
    auto_recovery_changed = pyqtSignal(bool)
    max_runtime_changed = pyqtSignal(int)
    cpu_limit_changed = pyqtSignal(int)
    memory_limit_changed = pyqtSignal(int)
    emergency_key_changed = pyqtSignal(str)
    mouse_corner_stop_changed = pyqtSignal(bool)
    
    # 性能设置信号
    performance_mode_changed = pyqtSignal(str)
    thread_count_changed = pyqtSignal(int)
    concurrent_tasks_changed = pyqtSignal(int)
    image_cache_changed = pyqtSignal(bool)
    cache_size_changed = pyqtSignal(int)
    preload_resources_changed = pyqtSignal(bool)
    smart_wait_changed = pyqtSignal(bool)
    realtime_monitor_changed = pyqtSignal(bool)
    monitor_interval_changed = pyqtSignal(int)
    performance_warning_changed = pyqtSignal(bool)
    
    # 任务配置信号
    schedule_strategy_changed = pyqtSignal(str)
    task_interval_changed = pyqtSignal(int)
    task_retry_changed = pyqtSignal(int)
    task_timeout_action_changed = pyqtSignal(str)
    task_priority_changed = pyqtSignal(str, str)  # task_key, priority
    automation_rules_changed = pyqtSignal(str)  # JSON string
    
    # 操作信号
    test_automation_requested = pyqtSignal()
    import_settings_requested = pyqtSignal()
    export_settings_requested = pyqtSignal()
    reset_settings_requested = pyqtSignal()
    apply_settings_requested = pyqtSignal()
    validate_rules_requested = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("自动化设置")
        self.init_ui()
        self.connect_signals()
        logger.info("自动化设置View初始化完成")
    
    def init_ui(self):
        """初始化UI界面"""
        layout = QVBoxLayout(self)
        
        # 标题
        title_label = QLabel("自动化设置")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # 选项卡
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # 创建各个选项卡
        self.create_operation_tab()
        self.create_safety_tab()
        self.create_performance_tab()
        self.create_task_tab()
        
        # 按钮布局
        self.create_button_layout(layout)
    
    def create_operation_tab(self):
        """创建操作参数选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 基础操作参数组
        basic_group = QGroupBox("基础操作参数")
        basic_layout = QVBoxLayout(basic_group)
        
        # 点击延迟
        click_layout = QHBoxLayout()
        click_layout.addWidget(QLabel("点击延迟 (ms):"))
        self.click_delay_spin = QSpinBox()
        click_delay_min = self._get_config_value('ui.automation_settings.click_delay_min', 50)
        click_delay_max = self._get_config_value('ui.automation_settings.click_delay_max', 2000)
        click_delay_default = self._get_config_value('ui.automation_settings.click_delay_default', 200)
        self.click_delay_spin.setRange(click_delay_min, click_delay_max)
        self.click_delay_spin.setValue(click_delay_default)
        click_layout.addWidget(self.click_delay_spin)
        click_layout.addStretch()
        basic_layout.addLayout(click_layout)
        
        # 按键延迟
        key_layout = QHBoxLayout()
        key_layout.addWidget(QLabel("按键延迟 (ms):"))
        self.key_delay_spin = QSpinBox()
        key_delay_min = self._get_config_value('ui.automation_settings.key_delay_min', 50)
        key_delay_max = self._get_config_value('ui.automation_settings.key_delay_max', 2000)
        key_delay_default = self._get_config_value('ui.automation_settings.key_delay_default', 100)
        self.key_delay_spin.setRange(key_delay_min, key_delay_max)
        self.key_delay_spin.setValue(key_delay_default)
        key_layout.addWidget(self.key_delay_spin)
        key_layout.addStretch()
        basic_layout.addLayout(key_layout)
        
        # 操作间隔
        interval_layout = QHBoxLayout()
        interval_layout.addWidget(QLabel("操作间隔 (ms):"))
        self.operation_interval_spin = QSpinBox()
        operation_interval_min = self._get_config_value('ui.automation_settings.operation_interval_min', 100)
        operation_interval_max = self._get_config_value('ui.automation_settings.operation_interval_max', 5000)
        operation_interval_default = self._get_config_value('ui.automation_settings.operation_interval_default', 500)
        self.operation_interval_spin.setRange(operation_interval_min, operation_interval_max)
        self.operation_interval_spin.setValue(operation_interval_default)
        interval_layout.addWidget(self.operation_interval_spin)
        interval_layout.addStretch()
        basic_layout.addLayout(interval_layout)
        
        layout.addWidget(basic_group)
        
        # 随机延迟组
        random_group = QGroupBox("随机延迟")
        random_layout = QVBoxLayout(random_group)
        
        # 启用随机延迟
        self.random_delay_check = QCheckBox("启用随机延迟")
        self.random_delay_check.setChecked(True)
        random_layout.addWidget(self.random_delay_check)
        
        # 随机延迟范围
        range_layout = QHBoxLayout()
        range_layout.addWidget(QLabel("延迟范围:"))
        self.random_delay_min_spin = QSpinBox()
        random_delay_min_range = self._get_config_value('ui.automation_settings.random_delay_min_range', [10, 1000])
        random_delay_min_default = self._get_config_value('ui.automation_settings.random_delay_min_default', 50)
        self.random_delay_min_spin.setRange(random_delay_min_range[0], random_delay_min_range[1])
        self.random_delay_min_spin.setValue(random_delay_min_default)
        range_layout.addWidget(self.random_delay_min_spin)
        range_layout.addWidget(QLabel("~"))
        self.random_delay_max_spin = QSpinBox()
        random_delay_max_range = self._get_config_value('ui.automation_settings.random_delay_max_range', [10, 1000])
        random_delay_max_default = self._get_config_value('ui.automation_settings.random_delay_max_default', 200)
        self.random_delay_max_spin.setRange(random_delay_max_range[0], random_delay_max_range[1])
        self.random_delay_max_spin.setValue(random_delay_max_default)
        range_layout.addWidget(self.random_delay_max_spin)
        range_layout.addWidget(QLabel("ms"))
        range_layout.addStretch()
        random_layout.addLayout(range_layout)
        
        layout.addWidget(random_group)
        
        # 检测参数组
        detection_group = QGroupBox("检测参数")
        detection_layout = QVBoxLayout(detection_group)
        
        # 检测精度
        accuracy_layout = QHBoxLayout()
        accuracy_layout.addWidget(QLabel("检测精度:"))
        self.detection_accuracy_slider = QSlider(Qt.Orientation.Horizontal)
        detection_accuracy_min = self._get_config_value('ui.automation_settings.detection_accuracy_min', 50)
        detection_accuracy_max = self._get_config_value('ui.automation_settings.detection_accuracy_max', 100)
        detection_accuracy_default = self._get_config_value('ui.automation_settings.detection_accuracy_default', 85)
        self.detection_accuracy_slider.setRange(detection_accuracy_min, detection_accuracy_max)
        self.detection_accuracy_slider.setValue(detection_accuracy_default)
        accuracy_layout.addWidget(self.detection_accuracy_slider)
        self.accuracy_label = QLabel("85%")
        accuracy_layout.addWidget(self.accuracy_label)
        detection_layout.addLayout(accuracy_layout)
        
        # 重试次数
        retry_layout = QHBoxLayout()
        retry_layout.addWidget(QLabel("重试次数:"))
        self.retry_count_spin = QSpinBox()
        retry_count_min = self._get_config_value('ui.automation_settings.retry_count_min', 1)
        retry_count_max = self._get_config_value('ui.automation_settings.retry_count_max', 10)
        retry_count_default = self._get_config_value('ui.automation_settings.retry_count_default', 3)
        self.retry_count_spin.setRange(retry_count_min, retry_count_max)
        self.retry_count_spin.setValue(retry_count_default)
        retry_layout.addWidget(self.retry_count_spin)
        retry_layout.addStretch()
        detection_layout.addLayout(retry_layout)
        
        # 操作超时
        timeout_layout = QHBoxLayout()
        timeout_layout.addWidget(QLabel("操作超时 (s):"))
        self.operation_timeout_spin = QSpinBox()
        operation_timeout_min = self._get_config_value('ui.automation_settings.operation_timeout_min', 5)
        operation_timeout_max = self._get_config_value('ui.automation_settings.operation_timeout_max', 300)
        operation_timeout_default = self._get_config_value('ui.automation_settings.operation_timeout_default', 30)
        self.operation_timeout_spin.setRange(operation_timeout_min, operation_timeout_max)
        self.operation_timeout_spin.setValue(operation_timeout_default)
        timeout_layout.addWidget(self.operation_timeout_spin)
        timeout_layout.addStretch()
        detection_layout.addLayout(timeout_layout)
        
        layout.addWidget(detection_group)
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "操作参数")
    
    def create_safety_tab(self):
        """创建安全选项选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 安全检查组
        safety_group = QGroupBox("安全检查")
        safety_layout = QVBoxLayout(safety_group)
        
        self.window_check = QCheckBox("游戏窗口检查")
        self.window_check.setChecked(True)
        safety_layout.addWidget(self.window_check)
        
        self.scene_check = QCheckBox("场景验证")
        self.scene_check.setChecked(True)
        safety_layout.addWidget(self.scene_check)
        
        self.exception_check = QCheckBox("异常检测")
        self.exception_check.setChecked(True)
        safety_layout.addWidget(self.exception_check)
        
        self.auto_recovery_check = QCheckBox("自动恢复")
        self.auto_recovery_check.setChecked(True)
        safety_layout.addWidget(self.auto_recovery_check)
        
        layout.addWidget(safety_group)
        
        # 运行限制组
        limit_group = QGroupBox("运行限制")
        limit_layout = QVBoxLayout(limit_group)
        
        # 最大运行时间
        runtime_layout = QHBoxLayout()
        runtime_layout.addWidget(QLabel("最大运行时间 (分钟):"))
        self.max_runtime_spin = QSpinBox()
        max_runtime_min = self._get_config_value('ui.automation_settings.max_runtime_min', 10)
        max_runtime_max = self._get_config_value('ui.automation_settings.max_runtime_max', 1440)
        max_runtime_default = self._get_config_value('ui.automation_settings.max_runtime_default', 120)
        self.max_runtime_spin.setRange(max_runtime_min, max_runtime_max)
        self.max_runtime_spin.setValue(max_runtime_default)
        runtime_layout.addWidget(self.max_runtime_spin)
        runtime_layout.addStretch()
        limit_layout.addLayout(runtime_layout)
        
        # CPU使用限制
        cpu_layout = QHBoxLayout()
        cpu_layout.addWidget(QLabel("CPU使用限制:"))
        self.cpu_limit_slider = QSlider(Qt.Orientation.Horizontal)
        cpu_limit_min = self._get_config_value('ui.automation_settings.cpu_limit_min', 10)
        cpu_limit_max = self._get_config_value('ui.automation_settings.cpu_limit_max', 100)
        cpu_limit_default = self._get_config_value('ui.automation_settings.cpu_limit_default', 50)
        self.cpu_limit_slider.setRange(cpu_limit_min, cpu_limit_max)
        self.cpu_limit_slider.setValue(cpu_limit_default)
        cpu_layout.addWidget(self.cpu_limit_slider)
        self.cpu_label = QLabel("50%")
        cpu_layout.addWidget(self.cpu_label)
        limit_layout.addLayout(cpu_layout)
        
        # 内存使用限制
        memory_layout = QHBoxLayout()
        memory_layout.addWidget(QLabel("内存使用限制 (MB):"))
        self.memory_limit_spin = QSpinBox()
        memory_limit_min = self._get_config_value('ui.automation_settings.memory_limit_min', 128)
        memory_limit_max = self._get_config_value('ui.automation_settings.memory_limit_max', 2048)
        memory_limit_default = self._get_config_value('ui.automation_settings.memory_limit_default', 512)
        self.memory_limit_spin.setRange(memory_limit_min, memory_limit_max)
        self.memory_limit_spin.setValue(memory_limit_default)
        memory_layout.addWidget(self.memory_limit_spin)
        memory_layout.addStretch()
        limit_layout.addLayout(memory_layout)
        
        layout.addWidget(limit_group)
        
        # 紧急停止组
        emergency_group = QGroupBox("紧急停止")
        emergency_layout = QVBoxLayout(emergency_group)
        
        # 紧急停止热键
        key_layout = QHBoxLayout()
        key_layout.addWidget(QLabel("紧急停止热键:"))
        self.emergency_key_edit = QLineEdit()
        emergency_key_default = self._get_config_value('ui.automation_settings.emergency_key_default', 'F12')
        self.emergency_key_edit.setText(emergency_key_default)
        key_layout.addWidget(self.emergency_key_edit)
        key_layout.addStretch()
        emergency_layout.addLayout(key_layout)
        
        # 鼠标移至屏幕角落停止
        self.mouse_corner_stop_check = QCheckBox("鼠标移至屏幕角落停止")
        emergency_layout.addWidget(self.mouse_corner_stop_check)
        
        layout.addWidget(emergency_group)
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "安全选项")
    
    def create_performance_tab(self):
        """创建性能设置选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 性能模式组
        mode_group = QGroupBox("性能模式")
        mode_layout = QVBoxLayout(mode_group)
        
        self.performance_mode_combo = QComboBox()
        self.performance_mode_combo.addItems(["节能模式", "平衡模式", "高性能模式", "自定义模式"])
        performance_mode_default = self._get_config_value('ui.automation_settings.performance_mode_default', '平衡模式')
        self.performance_mode_combo.setCurrentText(performance_mode_default)
        mode_layout.addWidget(self.performance_mode_combo)
        
        # 工作线程数
        thread_layout = QHBoxLayout()
        thread_layout.addWidget(QLabel("工作线程数:"))
        self.thread_count_spin = QSpinBox()
        thread_count_min = self._get_config_value('ui.automation_settings.thread_count_min', 1)
        thread_count_max = self._get_config_value('ui.automation_settings.thread_count_max', 8)
        thread_count_default = self._get_config_value('ui.automation_settings.thread_count_default', 2)
        self.thread_count_spin.setRange(thread_count_min, thread_count_max)
        self.thread_count_spin.setValue(thread_count_default)
        thread_layout.addWidget(self.thread_count_spin)
        thread_layout.addStretch()
        mode_layout.addLayout(thread_layout)
        
        # 并发任务数
        concurrent_layout = QHBoxLayout()
        concurrent_layout.addWidget(QLabel("并发任务数:"))
        self.concurrent_tasks_spin = QSpinBox()
        concurrent_tasks_min = self._get_config_value('ui.automation_settings.concurrent_tasks_min', 1)
        concurrent_tasks_max = self._get_config_value('ui.automation_settings.concurrent_tasks_max', 5)
        concurrent_tasks_default = self._get_config_value('ui.automation_settings.concurrent_tasks_default', 1)
        self.concurrent_tasks_spin.setRange(concurrent_tasks_min, concurrent_tasks_max)
        self.concurrent_tasks_spin.setValue(concurrent_tasks_default)
        concurrent_layout.addWidget(self.concurrent_tasks_spin)
        concurrent_layout.addStretch()
        mode_layout.addLayout(concurrent_layout)
        
        layout.addWidget(mode_group)
        
        # 优化设置组
        optimization_group = QGroupBox("优化设置")
        optimization_layout = QVBoxLayout(optimization_group)
        
        self.image_cache_check = QCheckBox("图像缓存")
        self.image_cache_check.setChecked(True)
        optimization_layout.addWidget(self.image_cache_check)
        
        # 缓存大小
        cache_layout = QHBoxLayout()
        cache_layout.addWidget(QLabel("缓存大小 (MB):"))
        self.cache_size_spin = QSpinBox()
        cache_size_min = self._get_config_value('ui.automation_settings.cache_size_min', 50)
        cache_size_max = self._get_config_value('ui.automation_settings.cache_size_max', 500)
        cache_size_default = self._get_config_value('ui.automation_settings.cache_size_default', 100)
        self.cache_size_spin.setRange(cache_size_min, cache_size_max)
        self.cache_size_spin.setValue(cache_size_default)
        cache_layout.addWidget(self.cache_size_spin)
        cache_layout.addStretch()
        optimization_layout.addLayout(cache_layout)
        
        self.preload_resources_check = QCheckBox("预加载资源")
        optimization_layout.addWidget(self.preload_resources_check)
        
        self.smart_wait_check = QCheckBox("智能等待优化")
        self.smart_wait_check.setChecked(True)
        optimization_layout.addWidget(self.smart_wait_check)
        
        layout.addWidget(optimization_group)
        
        # 性能监控组
        monitor_group = QGroupBox("性能监控")
        monitor_layout = QVBoxLayout(monitor_group)
        
        self.realtime_monitor_check = QCheckBox("实时性能监控")
        self.realtime_monitor_check.setChecked(True)
        monitor_layout.addWidget(self.realtime_monitor_check)
        
        # 监控间隔
        interval_layout = QHBoxLayout()
        interval_layout.addWidget(QLabel("监控间隔 (秒):"))
        self.monitor_interval_spin = QSpinBox()
        monitor_interval_min = self._get_config_value('ui.automation_settings.monitor_interval_min', 1)
        monitor_interval_max = self._get_config_value('ui.automation_settings.monitor_interval_max', 60)
        monitor_interval_default = self._get_config_value('ui.automation_settings.monitor_interval_default', 5)
        self.monitor_interval_spin.setRange(monitor_interval_min, monitor_interval_max)
        self.monitor_interval_spin.setValue(monitor_interval_default)
        interval_layout.addWidget(self.monitor_interval_spin)
        interval_layout.addStretch()
        monitor_layout.addLayout(interval_layout)
        
        self.performance_warning_check = QCheckBox("性能异常警告")
        self.performance_warning_check.setChecked(True)
        monitor_layout.addWidget(self.performance_warning_check)
        
        layout.addWidget(monitor_group)
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "性能设置")
    
    def create_task_tab(self):
        """创建任务配置选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 任务调度组
        schedule_group = QGroupBox("任务调度")
        schedule_layout = QVBoxLayout(schedule_group)
        
        # 调度策略
        strategy_layout = QHBoxLayout()
        strategy_layout.addWidget(QLabel("调度策略:"))
        self.schedule_strategy_combo = QComboBox()
        self.schedule_strategy_combo.addItems(["智能调度", "顺序执行", "优先级调度", "负载均衡"])
        schedule_strategy_default = self._get_config_value('ui.automation_settings.schedule_strategy_default', '智能调度')
        self.schedule_strategy_combo.setCurrentText(schedule_strategy_default)
        strategy_layout.addWidget(self.schedule_strategy_combo)
        strategy_layout.addStretch()
        schedule_layout.addLayout(strategy_layout)
        
        # 任务间隔
        task_interval_layout = QHBoxLayout()
        task_interval_layout.addWidget(QLabel("任务间隔 (秒):"))
        self.task_interval_spin = QSpinBox()
        task_interval_min = self._get_config_value('ui.automation_settings.task_interval_min', 1)
        task_interval_max = self._get_config_value('ui.automation_settings.task_interval_max', 300)
        task_interval_default = self._get_config_value('ui.automation_settings.task_interval_default', 10)
        self.task_interval_spin.setRange(task_interval_min, task_interval_max)
        self.task_interval_spin.setValue(task_interval_default)
        task_interval_layout.addWidget(self.task_interval_spin)
        task_interval_layout.addStretch()
        schedule_layout.addLayout(task_interval_layout)
        
        # 失败重试次数
        retry_layout = QHBoxLayout()
        retry_layout.addWidget(QLabel("失败重试次数:"))
        self.task_retry_spin = QSpinBox()
        task_retry_min = self._get_config_value('ui.automation_settings.task_retry_min', 0)
        task_retry_max = self._get_config_value('ui.automation_settings.task_retry_max', 10)
        task_retry_default = self._get_config_value('ui.automation_settings.task_retry_default', 2)
        self.task_retry_spin.setRange(task_retry_min, task_retry_max)
        self.task_retry_spin.setValue(task_retry_default)
        retry_layout.addWidget(self.task_retry_spin)
        retry_layout.addStretch()
        schedule_layout.addLayout(retry_layout)
        
        # 超时处理
        timeout_action_layout = QHBoxLayout()
        timeout_action_layout.addWidget(QLabel("超时处理:"))
        self.task_timeout_action_combo = QComboBox()
        self.task_timeout_action_combo.addItems(["重试任务", "跳过任务", "停止执行", "用户确认"])
        task_timeout_action_default = self._get_config_value('ui.automation_settings.task_timeout_action_default', '重试任务')
        self.task_timeout_action_combo.setCurrentText(task_timeout_action_default)
        timeout_action_layout.addWidget(self.task_timeout_action_combo)
        timeout_action_layout.addStretch()
        schedule_layout.addLayout(timeout_action_layout)
        
        layout.addWidget(schedule_group)
        
        # 任务优先级组
        priority_group = QGroupBox("任务优先级")
        priority_layout = QVBoxLayout(priority_group)
        
        # 创建任务优先级控件字典
        self.task_priority_combos = {}
        task_types = [
            ("daily_missions", "每日任务"),
            ("stamina_consumption", "体力消耗"),
            ("resource_collection", "资源收集"),
            ("battle_tasks", "战斗任务"),
            ("exploration", "探索任务")
        ]
        
        for task_key, task_name in task_types:
            task_layout = QHBoxLayout()
            task_layout.addWidget(QLabel(f"{task_name}:"))
            combo = QComboBox()
            combo.addItems(["低", "中", "高", "紧急"])
            combo.setCurrentText("中")
            combo.setProperty("task_key", task_key)
            self.task_priority_combos[task_key] = combo
            task_layout.addWidget(combo)
            task_layout.addStretch()
            priority_layout.addLayout(task_layout)
        
        layout.addWidget(priority_group)
        
        # 自动化规则组
        rules_group = QGroupBox("自动化规则")
        rules_layout = QVBoxLayout(rules_group)
        
        self.automation_rules_edit = QTextEdit()
        self.automation_rules_edit.setMaximumHeight(150)
        default_rules = {
            "daily_reset_time": "04:00",
            "auto_start_tasks": ["daily_missions", "stamina_consumption"],
            "conditions": {"stamina_threshold": 160, "skip_on_weekend": False},
        }
        self.automation_rules_edit.setPlainText(json.dumps(default_rules, indent=2, ensure_ascii=False))
        rules_layout.addWidget(self.automation_rules_edit)
        
        # 验证规则按钮
        self.validate_rules_btn = QPushButton("验证规则")
        rules_layout.addWidget(self.validate_rules_btn)
        
        layout.addWidget(rules_group)
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "任务配置")
    
    def create_button_layout(self, parent_layout):
        """创建按钮布局"""
        button_layout = QHBoxLayout()
        
        self.test_btn = QPushButton("测试自动化")
        self.import_btn = QPushButton("导入配置")
        self.export_btn = QPushButton("导出配置")
        self.reset_btn = QPushButton("重置为默认")
        self.apply_btn = QPushButton("应用设置")
        
        button_layout.addWidget(self.test_btn)
        button_layout.addWidget(self.import_btn)
        button_layout.addWidget(self.export_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.reset_btn)
        button_layout.addWidget(self.apply_btn)
        
        parent_layout.addLayout(button_layout)
    
    def connect_signals(self):
        """连接信号与槽"""
        # 操作参数信号
        self.click_delay_spin.valueChanged.connect(self.click_delay_changed.emit)
        self.key_delay_spin.valueChanged.connect(self.key_delay_changed.emit)
        self.operation_interval_spin.valueChanged.connect(self.operation_interval_changed.emit)
        self.random_delay_check.toggled.connect(self.random_delay_enabled_changed.emit)
        self.random_delay_min_spin.valueChanged.connect(self.random_delay_min_changed.emit)
        self.random_delay_max_spin.valueChanged.connect(self.random_delay_max_changed.emit)
        self.detection_accuracy_slider.valueChanged.connect(self._on_accuracy_changed)
        self.retry_count_spin.valueChanged.connect(self.retry_count_changed.emit)
        self.operation_timeout_spin.valueChanged.connect(self.operation_timeout_changed.emit)
        
        # 安全选项信号
        self.window_check.toggled.connect(self.window_check_changed.emit)
        self.scene_check.toggled.connect(self.scene_check_changed.emit)
        self.exception_check.toggled.connect(self.exception_check_changed.emit)
        self.auto_recovery_check.toggled.connect(self.auto_recovery_changed.emit)
        self.max_runtime_spin.valueChanged.connect(self.max_runtime_changed.emit)
        self.cpu_limit_slider.valueChanged.connect(self._on_cpu_limit_changed)
        self.memory_limit_spin.valueChanged.connect(self.memory_limit_changed.emit)
        self.emergency_key_edit.textChanged.connect(self.emergency_key_changed.emit)
        self.mouse_corner_stop_check.toggled.connect(self.mouse_corner_stop_changed.emit)
        
        # 性能设置信号
        self.performance_mode_combo.currentTextChanged.connect(self.performance_mode_changed.emit)
        self.thread_count_spin.valueChanged.connect(self.thread_count_changed.emit)
        self.concurrent_tasks_spin.valueChanged.connect(self.concurrent_tasks_changed.emit)
        self.image_cache_check.toggled.connect(self.image_cache_changed.emit)
        self.cache_size_spin.valueChanged.connect(self.cache_size_changed.emit)
        self.preload_resources_check.toggled.connect(self.preload_resources_changed.emit)
        self.smart_wait_check.toggled.connect(self.smart_wait_changed.emit)
        self.realtime_monitor_check.toggled.connect(self.realtime_monitor_changed.emit)
        self.monitor_interval_spin.valueChanged.connect(self.monitor_interval_changed.emit)
        self.performance_warning_check.toggled.connect(self.performance_warning_changed.emit)
        
        # 任务配置信号
        self.schedule_strategy_combo.currentTextChanged.connect(self.schedule_strategy_changed.emit)
        self.task_interval_spin.valueChanged.connect(self.task_interval_changed.emit)
        self.task_retry_spin.valueChanged.connect(self.task_retry_changed.emit)
        self.task_timeout_action_combo.currentTextChanged.connect(self.task_timeout_action_changed.emit)
        
        # 任务优先级信号
        for task_key, combo in self.task_priority_combos.items():
            combo.currentTextChanged.connect(
                lambda priority, key=task_key: self.task_priority_changed.emit(key, priority)
            )
        
        # 自动化规则信号
        self.automation_rules_edit.textChanged.connect(
            lambda: self.automation_rules_changed.emit(self.automation_rules_edit.toPlainText())
        )
        
        # 按钮信号
        self.test_btn.clicked.connect(self.test_automation_requested.emit)
        self.import_btn.clicked.connect(self.import_settings_requested.emit)
        self.export_btn.clicked.connect(self.export_settings_requested.emit)
        self.reset_btn.clicked.connect(self.reset_settings_requested.emit)
        self.apply_btn.clicked.connect(self.apply_settings_requested.emit)
        self.validate_rules_btn.clicked.connect(
            lambda: self.validate_rules_requested.emit(self.automation_rules_edit.toPlainText())
        )
    
    def _on_accuracy_changed(self, value: int):
        """检测精度变化处理"""
        self.accuracy_label.setText(f"{value}%")
        self.detection_accuracy_changed.emit(value)
    
    def _on_cpu_limit_changed(self, value: int):
        """CPU限制变化处理"""
        self.cpu_label.setText(f"{value}%")
        self.cpu_limit_changed.emit(value)
    
    # 数据更新方法
    def update_click_delay(self, value: int):
        """更新点击延迟"""
        self.click_delay_spin.setValue(value)
    
    def update_key_delay(self, value: int):
        """更新按键延迟"""
        self.key_delay_spin.setValue(value)
    
    def update_operation_interval(self, value: int):
        """更新操作间隔"""
        self.operation_interval_spin.setValue(value)
    
    def update_random_delay_enabled(self, enabled: bool):
        """更新随机延迟启用状态"""
        self.random_delay_check.setChecked(enabled)
    
    def update_random_delay_min(self, value: int):
        """更新随机延迟最小值"""
        self.random_delay_min_spin.setValue(value)
    
    def update_random_delay_max(self, value: int):
        """更新随机延迟最大值"""
        self.random_delay_max_spin.setValue(value)
    
    def update_detection_accuracy(self, value: int):
        """更新检测精度"""
        self.detection_accuracy_slider.setValue(value)
        self.accuracy_label.setText(f"{value}%")
    
    def update_retry_count(self, value: int):
        """更新重试次数"""
        self.retry_count_spin.setValue(value)
    
    def update_operation_timeout(self, value: int):
        """更新操作超时"""
        self.operation_timeout_spin.setValue(value)
    
    def update_window_check(self, enabled: bool):
        """更新窗口检查"""
        self.window_check.setChecked(enabled)
    
    def update_scene_check(self, enabled: bool):
        """更新场景检查"""
        self.scene_check.setChecked(enabled)
    
    def update_exception_check(self, enabled: bool):
        """更新异常检测"""
        self.exception_check.setChecked(enabled)
    
    def update_auto_recovery(self, enabled: bool):
        """更新自动恢复"""
        self.auto_recovery_check.setChecked(enabled)
    
    def update_max_runtime(self, value: int):
        """更新最大运行时间"""
        self.max_runtime_spin.setValue(value)
    
    def update_cpu_limit(self, value: int):
        """更新CPU限制"""
        self.cpu_limit_slider.setValue(value)
        self.cpu_label.setText(f"{value}%")
    
    def update_memory_limit(self, value: int):
        """更新内存限制"""
        self.memory_limit_spin.setValue(value)
    
    def update_emergency_key(self, key: str):
        """更新紧急停止热键"""
        self.emergency_key_edit.setText(key)
    
    def update_mouse_corner_stop(self, enabled: bool):
        """更新鼠标角落停止"""
        self.mouse_corner_stop_check.setChecked(enabled)
    
    def update_performance_mode(self, mode: str):
        """更新性能模式"""
        self.performance_mode_combo.setCurrentText(mode)
    
    def update_thread_count(self, value: int):
        """更新线程数"""
        self.thread_count_spin.setValue(value)
    
    def update_concurrent_tasks(self, value: int):
        """更新并发任务数"""
        self.concurrent_tasks_spin.setValue(value)
    
    def update_image_cache(self, enabled: bool):
        """更新图像缓存"""
        self.image_cache_check.setChecked(enabled)
    
    def update_cache_size(self, value: int):
        """更新缓存大小"""
        self.cache_size_spin.setValue(value)
    
    def update_preload_resources(self, enabled: bool):
        """更新预加载资源"""
        self.preload_resources_check.setChecked(enabled)
    
    def update_smart_wait(self, enabled: bool):
        """更新智能等待"""
        self.smart_wait_check.setChecked(enabled)
    
    def update_realtime_monitor(self, enabled: bool):
        """更新实时监控"""
        self.realtime_monitor_check.setChecked(enabled)
    
    def update_monitor_interval(self, value: int):
        """更新监控间隔"""
        self.monitor_interval_spin.setValue(value)
    
    def update_performance_warning(self, enabled: bool):
        """更新性能警告"""
        self.performance_warning_check.setChecked(enabled)
    
    def update_schedule_strategy(self, strategy: str):
        """更新调度策略"""
        self.schedule_strategy_combo.setCurrentText(strategy)
    
    def update_task_interval(self, value: int):
        """更新任务间隔"""
        self.task_interval_spin.setValue(value)
    
    def update_task_retry(self, value: int):
        """更新任务重试"""
        self.task_retry_spin.setValue(value)
    
    def update_task_timeout_action(self, action: str):
        """更新任务超时处理"""
        self.task_timeout_action_combo.setCurrentText(action)
    
    def update_task_priority(self, task_key: str, priority: str):
        """更新任务优先级"""
        if task_key in self.task_priority_combos:
            self.task_priority_combos[task_key].setCurrentText(priority)
    
    def update_automation_rules(self, rules: Dict[str, Any]):
        """更新自动化规则"""
        rules_text = json.dumps(rules, indent=2, ensure_ascii=False)
        self.automation_rules_edit.setPlainText(rules_text)
    
    # 对话框方法
    def show_file_dialog(self, mode: str, file_filter: str = "JSON files (*.json)") -> Optional[str]:
        """显示文件对话框"""
        if mode == "open":
            file_path, _ = QFileDialog.getOpenFileName(self, "选择配置文件", "", file_filter)
        else:
            file_path, _ = QFileDialog.getSaveFileName(self, "保存配置文件", "", file_filter)
        return file_path if file_path else None
    
    def show_message(self, title: str, message: str, msg_type: str = "info"):
        """显示消息对话框"""
        if msg_type == "info":
            QMessageBox.information(self, title, message)
        elif msg_type == "warning":
            QMessageBox.warning(self, title, message)
        elif msg_type == "error":
            QMessageBox.critical(self, title, message)
    
    def show_confirmation(self, title: str, message: str) -> bool:
        """显示确认对话框"""
        reply = QMessageBox.question(
            self, title, message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        return reply == QMessageBox.StandardButton.Yes
    
    # 状态控制方法
    def set_loading_state(self, loading: bool):
        """设置加载状态"""
        self.setEnabled(not loading)
    
    def set_enabled_state(self, enabled: bool):
        """设置启用状态"""
        self.setEnabled(enabled)
    
    # 获取当前界面值
    def get_current_values(self) -> Dict[str, Any]:
        """获取当前界面值"""
        # 获取任务优先级
        task_priorities = {}
        for task_key, combo in self.task_priority_combos.items():
            task_priorities[task_key] = combo.currentText()
        
        # 获取自动化规则
        try:
            automation_rules = json.loads(self.automation_rules_edit.toPlainText())
        except json.JSONDecodeError:
            automation_rules = {}
        
        return {
            # 操作参数
            "click_delay": self.click_delay_spin.value(),
            "key_delay": self.key_delay_spin.value(),
            "operation_interval": self.operation_interval_spin.value(),
            "random_delay_enabled": self.random_delay_check.isChecked(),
            "random_delay_min": self.random_delay_min_spin.value(),
            "random_delay_max": self.random_delay_max_spin.value(),
            "detection_accuracy": self.detection_accuracy_slider.value(),
            "retry_count": self.retry_count_spin.value(),
            "operation_timeout": self.operation_timeout_spin.value(),
            # 安全选项
            "window_check": self.window_check.isChecked(),
            "scene_check": self.scene_check.isChecked(),
            "exception_check": self.exception_check.isChecked(),
            "auto_recovery": self.auto_recovery_check.isChecked(),
            "max_runtime": self.max_runtime_spin.value(),
            "cpu_limit": self.cpu_limit_slider.value(),
            "memory_limit": self.memory_limit_spin.value(),
            "emergency_key": self.emergency_key_edit.text(),
            "mouse_corner_stop": self.mouse_corner_stop_check.isChecked(),
            # 性能设置
            "performance_mode": self.performance_mode_combo.currentText(),
            "thread_count": self.thread_count_spin.value(),
            "concurrent_tasks": self.concurrent_tasks_spin.value(),
            "image_cache": self.image_cache_check.isChecked(),
            "cache_size": self.cache_size_spin.value(),
            "preload_resources": self.preload_resources_check.isChecked(),
            "smart_wait": self.smart_wait_check.isChecked(),
            "realtime_monitor": self.realtime_monitor_check.isChecked(),
            "monitor_interval": self.monitor_interval_spin.value(),
            "performance_warning": self.performance_warning_check.isChecked(),
            # 任务配置
            "schedule_strategy": self.schedule_strategy_combo.currentText(),
            "task_interval": self.task_interval_spin.value(),
            "task_retry": self.task_retry_spin.value(),
            "task_timeout_action": self.task_timeout_action_combo.currentText(),
            "task_priorities": task_priorities,
            "automation_rules": automation_rules,
        }
    
    def cleanup(self):
        """清理资源"""
        try:
            logger.info("自动化设置View清理完成")
        except Exception as e:
            logger.error(f"清理资源失败: {e}")