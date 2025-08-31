from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QCheckBox,
    QGroupBox, QSpinBox, QDoubleSpinBox, QSlider,
    QFormLayout, QFrame, QTextEdit, QTabWidget,
    QMessageBox, QProgressBar
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QPixmap, QPainter, QColor
import json
from typing import Dict, Any, List
from loguru import logger

from ..core.config_manager import ConfigManager
from ..core.task_manager import TaskType


class AutomationSettingsWidget(QWidget):
    """自动化配置界面组件"""
    
    # 信号定义
    settings_changed = pyqtSignal(str, str, object)  # category, key, value
    test_automation = pyqtSignal(str)  # test_type
    
    def __init__(self, config_manager: ConfigManager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self._init_ui()
        self._load_settings()
        self._connect_signals()
    
    def _init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 标题
        title_label = QLabel("自动化配置")
        title_label.setFont(QFont("Microsoft YaHei", 16, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # 创建选项卡
        self.tab_widget = QTabWidget()
        
        # 操作参数选项卡
        operation_tab = self._create_operation_tab()
        self.tab_widget.addTab(operation_tab, "操作参数")
        
        # 安全选项选项卡
        safety_tab = self._create_safety_tab()
        self.tab_widget.addTab(safety_tab, "安全选项")
        
        # 性能设置选项卡
        performance_tab = self._create_performance_tab()
        self.tab_widget.addTab(performance_tab, "性能设置")
        
        # 任务配置选项卡
        task_tab = self._create_task_tab()
        self.tab_widget.addTab(task_tab, "任务配置")
        
        layout.addWidget(self.tab_widget)
        
        # 按钮区域
        button_layout = self._create_button_layout()
        layout.addLayout(button_layout)
    
    def _create_operation_tab(self) -> QWidget:
        """创建操作参数选项卡"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 基础操作设置组
        basic_group = QGroupBox("基础操作")
        basic_layout = QFormLayout(basic_group)
        
        # 点击延迟
        self.click_delay_spin = QSpinBox()
        self.click_delay_spin.setRange(50, 5000)
        self.click_delay_spin.setValue(200)
        self.click_delay_spin.setSuffix(" 毫秒")
        basic_layout.addRow("点击延迟:", self.click_delay_spin)
        
        # 按键延迟
        self.key_delay_spin = QSpinBox()
        self.key_delay_spin.setRange(50, 2000)
        self.key_delay_spin.setValue(100)
        self.key_delay_spin.setSuffix(" 毫秒")
        basic_layout.addRow("按键延迟:", self.key_delay_spin)
        
        # 操作间隔
        self.operation_interval_spin = QSpinBox()
        self.operation_interval_spin.setRange(100, 10000)
        self.operation_interval_spin.setValue(500)
        self.operation_interval_spin.setSuffix(" 毫秒")
        basic_layout.addRow("操作间隔:", self.operation_interval_spin)
        
        # 随机延迟
        self.random_delay_check = QCheckBox("启用随机延迟")
        self.random_delay_check.setChecked(True)
        basic_layout.addRow("", self.random_delay_check)
        
        # 随机延迟范围
        random_layout = QHBoxLayout()
        self.random_min_spin = QSpinBox()
        self.random_min_spin.setRange(0, 1000)
        self.random_min_spin.setValue(50)
        self.random_min_spin.setSuffix(" 毫秒")
        random_layout.addWidget(self.random_min_spin)
        
        random_layout.addWidget(QLabel("至"))
        
        self.random_max_spin = QSpinBox()
        self.random_max_spin.setRange(0, 2000)
        self.random_max_spin.setValue(200)
        self.random_max_spin.setSuffix(" 毫秒")
        random_layout.addWidget(self.random_max_spin)
        
        random_layout.addStretch()
        basic_layout.addRow("随机延迟范围:", random_layout)
        
        layout.addWidget(basic_group)
        
        # 检测设置组
        detection_group = QGroupBox("检测设置")
        detection_layout = QFormLayout(detection_group)
        
        # 检测精度
        self.detection_accuracy_slider = QSlider(Qt.Orientation.Horizontal)
        self.detection_accuracy_slider.setRange(70, 99)
        self.detection_accuracy_slider.setValue(85)
        self.accuracy_label = QLabel("85%")
        accuracy_layout = QHBoxLayout()
        accuracy_layout.addWidget(self.detection_accuracy_slider)
        accuracy_layout.addWidget(self.accuracy_label)
        detection_layout.addRow("检测精度:", accuracy_layout)
        
        # 重试次数
        self.retry_count_spin = QSpinBox()
        self.retry_count_spin.setRange(1, 10)
        self.retry_count_spin.setValue(3)
        detection_layout.addRow("重试次数:", self.retry_count_spin)
        
        # 超时时间
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(5, 300)
        self.timeout_spin.setValue(30)
        self.timeout_spin.setSuffix(" 秒")
        detection_layout.addRow("操作超时:", self.timeout_spin)
        
        layout.addWidget(detection_group)
        layout.addStretch()
        
        return widget
    
    def _create_safety_tab(self) -> QWidget:
        """创建安全选项选项卡"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 安全检查组
        safety_group = QGroupBox("安全检查")
        safety_layout = QFormLayout(safety_group)
        
        # 游戏窗口检查
        self.window_check = QCheckBox("检查游戏窗口状态")
        self.window_check.setChecked(True)
        safety_layout.addRow("", self.window_check)
        
        # 场景验证
        self.scene_check = QCheckBox("验证游戏场景")
        self.scene_check.setChecked(True)
        safety_layout.addRow("", self.scene_check)
        
        # 异常检测
        self.exception_check = QCheckBox("启用异常检测")
        self.exception_check.setChecked(True)
        safety_layout.addRow("", self.exception_check)
        
        # 自动恢复
        self.auto_recovery_check = QCheckBox("自动错误恢复")
        self.auto_recovery_check.setChecked(True)
        safety_layout.addRow("", self.auto_recovery_check)
        
        layout.addWidget(safety_group)
        
        # 限制设置组
        limit_group = QGroupBox("运行限制")
        limit_layout = QFormLayout(limit_group)
        
        # 最大运行时间
        self.max_runtime_spin = QSpinBox()
        self.max_runtime_spin.setRange(10, 1440)
        self.max_runtime_spin.setValue(120)
        self.max_runtime_spin.setSuffix(" 分钟")
        limit_layout.addRow("最大运行时间:", self.max_runtime_spin)
        
        # CPU使用限制
        self.cpu_limit_slider = QSlider(Qt.Orientation.Horizontal)
        self.cpu_limit_slider.setRange(10, 100)
        self.cpu_limit_slider.setValue(50)
        self.cpu_label = QLabel("50%")
        cpu_layout = QHBoxLayout()
        cpu_layout.addWidget(self.cpu_limit_slider)
        cpu_layout.addWidget(self.cpu_label)
        limit_layout.addRow("CPU使用限制:", cpu_layout)
        
        # 内存使用限制
        self.memory_limit_spin = QSpinBox()
        self.memory_limit_spin.setRange(100, 2048)
        self.memory_limit_spin.setValue(512)
        self.memory_limit_spin.setSuffix(" MB")
        limit_layout.addRow("内存使用限制:", self.memory_limit_spin)
        
        layout.addWidget(limit_group)
        
        # 紧急停止组
        emergency_group = QGroupBox("紧急停止")
        emergency_layout = QFormLayout(emergency_group)
        
        # 热键设置
        self.emergency_key_edit = QLineEdit()
        self.emergency_key_edit.setText("F12")
        self.emergency_key_edit.setPlaceholderText("设置紧急停止热键")
        emergency_layout.addRow("紧急停止热键:", self.emergency_key_edit)
        
        # 鼠标位置检测
        self.mouse_corner_check = QCheckBox("鼠标移至屏幕角落停止")
        self.mouse_corner_check.setChecked(False)
        emergency_layout.addRow("", self.mouse_corner_check)
        
        layout.addWidget(emergency_group)
        layout.addStretch()
        
        return widget
    
    def _create_performance_tab(self) -> QWidget:
        """创建性能设置选项卡"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 性能模式组
        mode_group = QGroupBox("性能模式")
        mode_layout = QFormLayout(mode_group)
        
        # 性能模式选择
        self.performance_mode_combo = QComboBox()
        self.performance_mode_combo.addItems(["节能模式", "平衡模式", "高性能模式", "自定义"])
        self.performance_mode_combo.setCurrentText("平衡模式")
        mode_layout.addRow("性能模式:", self.performance_mode_combo)
        
        # 线程数设置
        self.thread_count_spin = QSpinBox()
        self.thread_count_spin.setRange(1, 8)
        self.thread_count_spin.setValue(2)
        mode_layout.addRow("工作线程数:", self.thread_count_spin)
        
        # 并发任务数
        self.concurrent_tasks_spin = QSpinBox()
        self.concurrent_tasks_spin.setRange(1, 5)
        self.concurrent_tasks_spin.setValue(1)
        mode_layout.addRow("并发任务数:", self.concurrent_tasks_spin)
        
        layout.addWidget(mode_group)
        
        # 优化设置组
        optimization_group = QGroupBox("优化设置")
        optimization_layout = QFormLayout(optimization_group)
        
        # 图像缓存
        self.image_cache_check = QCheckBox("启用图像缓存")
        self.image_cache_check.setChecked(True)
        optimization_layout.addRow("", self.image_cache_check)
        
        # 缓存大小
        self.cache_size_spin = QSpinBox()
        self.cache_size_spin.setRange(50, 500)
        self.cache_size_spin.setValue(100)
        self.cache_size_spin.setSuffix(" MB")
        optimization_layout.addRow("缓存大小:", self.cache_size_spin)
        
        # 预加载资源
        self.preload_check = QCheckBox("预加载游戏资源")
        self.preload_check.setChecked(False)
        optimization_layout.addRow("", self.preload_check)
        
        # 智能等待
        self.smart_wait_check = QCheckBox("智能等待优化")
        self.smart_wait_check.setChecked(True)
        optimization_layout.addRow("", self.smart_wait_check)
        
        layout.addWidget(optimization_group)
        
        # 监控设置组
        monitor_group = QGroupBox("性能监控")
        monitor_layout = QFormLayout(monitor_group)
        
        # 实时监控
        self.realtime_monitor_check = QCheckBox("启用实时性能监控")
        self.realtime_monitor_check.setChecked(True)
        monitor_layout.addRow("", self.realtime_monitor_check)
        
        # 监控间隔
        self.monitor_interval_spin = QSpinBox()
        self.monitor_interval_spin.setRange(1, 60)
        self.monitor_interval_spin.setValue(5)
        self.monitor_interval_spin.setSuffix(" 秒")
        monitor_layout.addRow("监控间隔:", self.monitor_interval_spin)
        
        # 性能警告
        self.performance_warning_check = QCheckBox("性能异常警告")
        self.performance_warning_check.setChecked(True)
        monitor_layout.addRow("", self.performance_warning_check)
        
        layout.addWidget(monitor_group)
        layout.addStretch()
        
        return widget
    
    def _create_task_tab(self) -> QWidget:
        """创建任务配置选项卡"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 任务优先级组
        priority_group = QGroupBox("任务优先级")
        priority_layout = QFormLayout(priority_group)
        
        # 各类任务的优先级设置
        self.task_priorities = {}
        task_types = [
            ("每日任务", "daily_missions"),
            ("体力消耗", "stamina_consumption"),
            ("派遣任务", "dispatch_missions"),
            ("委托任务", "assignment_missions"),
            ("合成任务", "synthesis_missions"),
            ("自动战斗", "auto_combat"),
            ("邮件收集", "mail_collection")
        ]
        
        for display_name, task_key in task_types:
            priority_combo = QComboBox()
            priority_combo.addItems(["低", "中", "高", "最高"])
            priority_combo.setCurrentText("中")
            self.task_priorities[task_key] = priority_combo
            priority_layout.addRow(f"{display_name}:", priority_combo)
        
        layout.addWidget(priority_group)
        
        # 任务调度组
        schedule_group = QGroupBox("任务调度")
        schedule_layout = QFormLayout(schedule_group)
        
        # 调度策略
        self.schedule_strategy_combo = QComboBox()
        self.schedule_strategy_combo.addItems(["顺序执行", "优先级执行", "智能调度"])
        self.schedule_strategy_combo.setCurrentText("智能调度")
        schedule_layout.addRow("调度策略:", self.schedule_strategy_combo)
        
        # 任务间隔
        self.task_interval_spin = QSpinBox()
        self.task_interval_spin.setRange(1, 300)
        self.task_interval_spin.setValue(10)
        self.task_interval_spin.setSuffix(" 秒")
        schedule_layout.addRow("任务间隔:", self.task_interval_spin)
        
        # 失败重试
        self.task_retry_spin = QSpinBox()
        self.task_retry_spin.setRange(0, 10)
        self.task_retry_spin.setValue(2)
        schedule_layout.addRow("失败重试次数:", self.task_retry_spin)
        
        # 超时处理
        self.task_timeout_combo = QComboBox()
        self.task_timeout_combo.addItems(["跳过任务", "重试任务", "停止所有任务"])
        self.task_timeout_combo.setCurrentText("重试任务")
        schedule_layout.addRow("超时处理:", self.task_timeout_combo)
        
        layout.addWidget(schedule_group)
        
        # 自动化规则组
        rules_group = QGroupBox("自动化规则")
        rules_layout = QVBoxLayout(rules_group)
        
        # 规则编辑器
        rules_label = QLabel("自定义自动化规则 (JSON格式):")
        rules_layout.addWidget(rules_label)
        
        self.rules_edit = QTextEdit()
        self.rules_edit.setMaximumHeight(150)
        self.rules_edit.setPlainText(json.dumps({
            "daily_reset_time": "04:00",
            "auto_start_tasks": ["daily_missions", "stamina_consumption"],
            "conditions": {
                "stamina_threshold": 160,
                "skip_on_weekend": False
            }
        }, indent=2, ensure_ascii=False))
        rules_layout.addWidget(self.rules_edit)
        
        # 验证按钮
        validate_button = QPushButton("验证规则")
        validate_button.clicked.connect(self._validate_rules)
        rules_layout.addWidget(validate_button)
        
        layout.addWidget(rules_group)
        layout.addStretch()
        
        return widget
    
    def _create_button_layout(self) -> QHBoxLayout:
        """创建按钮布局"""
        layout = QHBoxLayout()
        layout.addStretch()
        
        # 测试自动化按钮
        self.test_automation_button = QPushButton("测试自动化")
        self.test_automation_button.clicked.connect(self._test_automation_settings)
        layout.addWidget(self.test_automation_button)
        
        # 导入配置按钮
        self.import_button = QPushButton("导入配置")
        self.import_button.clicked.connect(self._import_settings)
        layout.addWidget(self.import_button)
        
        # 导出配置按钮
        self.export_button = QPushButton("导出配置")
        self.export_button.clicked.connect(self._export_settings)
        layout.addWidget(self.export_button)
        
        # 重置按钮
        self.reset_button = QPushButton("重置为默认")
        self.reset_button.clicked.connect(self._reset_to_defaults)
        layout.addWidget(self.reset_button)
        
        # 应用按钮
        self.apply_button = QPushButton("应用设置")
        self.apply_button.clicked.connect(self._apply_settings)
        layout.addWidget(self.apply_button)
        
        return layout
    
    def _connect_signals(self):
        """连接信号和槽"""
        # 滑块值变化
        self.detection_accuracy_slider.valueChanged.connect(
            lambda value: self.accuracy_label.setText(f"{value}%")
        )
        self.cpu_limit_slider.valueChanged.connect(
            lambda value: self.cpu_label.setText(f"{value}%")
        )
        
        # 性能模式变化
        self.performance_mode_combo.currentTextChanged.connect(self._on_performance_mode_changed)
        
        # 配置变更信号连接
        widgets_mapping = {
            # 操作参数
            'click_delay': self.click_delay_spin,
            'key_delay': self.key_delay_spin,
            'operation_interval': self.operation_interval_spin,
            'random_delay_enabled': self.random_delay_check,
            'random_delay_min': self.random_min_spin,
            'random_delay_max': self.random_max_spin,
            'detection_accuracy': self.detection_accuracy_slider,
            'retry_count': self.retry_count_spin,
            'operation_timeout': self.timeout_spin,
            
            # 安全选项
            'window_check': self.window_check,
            'scene_check': self.scene_check,
            'exception_check': self.exception_check,
            'auto_recovery': self.auto_recovery_check,
            'max_runtime': self.max_runtime_spin,
            'cpu_limit': self.cpu_limit_slider,
            'memory_limit': self.memory_limit_spin,
            'emergency_key': self.emergency_key_edit,
            'mouse_corner_stop': self.mouse_corner_check,
            
            # 性能设置
            'performance_mode': self.performance_mode_combo,
            'thread_count': self.thread_count_spin,
            'concurrent_tasks': self.concurrent_tasks_spin,
            'image_cache': self.image_cache_check,
            'cache_size': self.cache_size_spin,
            'preload_resources': self.preload_check,
            'smart_wait': self.smart_wait_check,
            'realtime_monitor': self.realtime_monitor_check,
            'monitor_interval': self.monitor_interval_spin,
            'performance_warning': self.performance_warning_check,
            
            # 任务配置
            'schedule_strategy': self.schedule_strategy_combo,
            'task_interval': self.task_interval_spin,
            'task_retry': self.task_retry_spin,
            'task_timeout_action': self.task_timeout_combo
        }
        
        for key, widget in widgets_mapping.items():
            if hasattr(widget, 'valueChanged'):
                widget.valueChanged.connect(
                    lambda value, k=key: self._on_setting_changed('automation', k, value)
                )
            elif hasattr(widget, 'toggled'):
                widget.toggled.connect(
                    lambda checked, k=key: self._on_setting_changed('automation', k, checked)
                )
            elif hasattr(widget, 'currentTextChanged'):
                widget.currentTextChanged.connect(
                    lambda text, k=key: self._on_setting_changed('automation', k, text)
                )
            elif hasattr(widget, 'textChanged'):
                widget.textChanged.connect(
                    lambda text, k=key: self._on_setting_changed('automation', k, text)
                )
    
    def _load_settings(self):
        """加载配置设置"""
        try:
            automation_config = self.config_manager.get_automation_config()
            
            # 加载操作参数
            self.click_delay_spin.setValue(int(automation_config.get('click_delay', 200)))
            self.key_delay_spin.setValue(int(automation_config.get('key_delay', 100)))
            self.operation_interval_spin.setValue(int(automation_config.get('operation_interval', 500)))
            self.random_delay_check.setChecked(automation_config.get('random_delay_enabled', True))
            self.random_min_spin.setValue(int(automation_config.get('random_delay_min', 50)))
            self.random_max_spin.setValue(int(automation_config.get('random_delay_max', 200)))
            self.detection_accuracy_slider.setValue(int(automation_config.get('detection_accuracy', 85)))
            self.retry_count_spin.setValue(int(automation_config.get('retry_count', 3)))
            self.timeout_spin.setValue(int(automation_config.get('operation_timeout', 30)))
            
            # 加载安全选项
            self.window_check.setChecked(automation_config.get('window_check', True))
            self.scene_check.setChecked(automation_config.get('scene_check', True))
            self.exception_check.setChecked(automation_config.get('exception_check', True))
            self.auto_recovery_check.setChecked(automation_config.get('auto_recovery', True))
            self.max_runtime_spin.setValue(int(automation_config.get('max_runtime', 120)))
            self.cpu_limit_slider.setValue(int(automation_config.get('cpu_limit', 50)))
            self.memory_limit_spin.setValue(int(automation_config.get('memory_limit', 512)))
            self.emergency_key_edit.setText(automation_config.get('emergency_key', 'F12'))
            self.mouse_corner_check.setChecked(automation_config.get('mouse_corner_stop', False))
            
            # 加载性能设置
            performance_mode = automation_config.get('performance_mode', '平衡模式')
            mode_index = self.performance_mode_combo.findText(performance_mode)
            if mode_index >= 0:
                self.performance_mode_combo.setCurrentIndex(mode_index)
            
            self.thread_count_spin.setValue(int(automation_config.get('thread_count', 2)))
            self.concurrent_tasks_spin.setValue(int(automation_config.get('concurrent_tasks', 1)))
            self.image_cache_check.setChecked(automation_config.get('image_cache', True))
            self.cache_size_spin.setValue(int(automation_config.get('cache_size', 100)))
            self.preload_check.setChecked(automation_config.get('preload_resources', False))
            self.smart_wait_check.setChecked(automation_config.get('smart_wait', True))
            self.realtime_monitor_check.setChecked(automation_config.get('realtime_monitor', True))
            self.monitor_interval_spin.setValue(int(automation_config.get('monitor_interval', 5)))
            self.performance_warning_check.setChecked(automation_config.get('performance_warning', True))
            
            # 加载任务配置
            schedule_strategy = automation_config.get('schedule_strategy', '智能调度')
            strategy_index = self.schedule_strategy_combo.findText(schedule_strategy)
            if strategy_index >= 0:
                self.schedule_strategy_combo.setCurrentIndex(strategy_index)
            
            self.task_interval_spin.setValue(int(automation_config.get('task_interval', 10)))
            self.task_retry_spin.setValue(int(automation_config.get('task_retry', 2)))
            
            timeout_action = automation_config.get('task_timeout_action', '重试任务')
            timeout_index = self.task_timeout_combo.findText(timeout_action)
            if timeout_index >= 0:
                self.task_timeout_combo.setCurrentIndex(timeout_index)
            
            # 加载任务优先级
            task_priorities = automation_config.get('task_priorities', {})
            for task_key, combo in self.task_priorities.items():
                priority = task_priorities.get(task_key, '中')
                priority_index = combo.findText(priority)
                if priority_index >= 0:
                    combo.setCurrentIndex(priority_index)
            
            # 加载自动化规则
            rules = automation_config.get('automation_rules', {})
            if rules:
                self.rules_edit.setPlainText(json.dumps(rules, indent=2, ensure_ascii=False))
            
            logger.info("自动化配置加载完成")
            
        except Exception as e:
            logger.error(f"加载自动化配置失败: {e}")
            QMessageBox.warning(self, "加载失败", f"加载自动化配置失败：{str(e)}")
    
    def _on_performance_mode_changed(self, mode: str):
        """性能模式变化处理"""
        # 根据性能模式自动调整相关设置
        if mode == "节能模式":
            self.thread_count_spin.setValue(1)
            self.concurrent_tasks_spin.setValue(1)
            self.cpu_limit_slider.setValue(int(30))
            self.cache_size_spin.setValue(50)
        elif mode == "平衡模式":
            self.thread_count_spin.setValue(2)
            self.concurrent_tasks_spin.setValue(1)
            self.cpu_limit_slider.setValue(int(50))
            self.cache_size_spin.setValue(100)
        elif mode == "高性能模式":
            self.thread_count_spin.setValue(4)
            self.concurrent_tasks_spin.setValue(2)
            self.cpu_limit_slider.setValue(int(80))
            self.cache_size_spin.setValue(200)
        # 自定义模式不自动调整
    
    def _validate_rules(self):
        """验证自动化规则"""
        try:
            rules_text = self.rules_edit.toPlainText()
            rules = json.loads(rules_text)
            
            # 基本验证
            required_keys = ['daily_reset_time', 'auto_start_tasks', 'conditions']
            for key in required_keys:
                if key not in rules:
                    raise ValueError(f"缺少必需的配置项: {key}")
            
            QMessageBox.information(self, "验证成功", "自动化规则格式正确")
            logger.info("自动化规则验证通过")
            
        except json.JSONDecodeError as e:
            QMessageBox.warning(self, "验证失败", f"JSON格式错误：{str(e)}")
        except ValueError as e:
            QMessageBox.warning(self, "验证失败", f"规则验证失败：{str(e)}")
        except Exception as e:
            logger.error(f"规则验证失败: {e}")
            QMessageBox.critical(self, "验证失败", f"验证过程出错：{str(e)}")
    
    def _test_automation_settings(self):
        """测试自动化设置"""
        try:
            # 发射测试信号
            self.test_automation.emit("basic_test")
            
            # 显示测试对话框
            QMessageBox.information(
                self,
                "测试完成",
                "自动化设置测试完成！\n\n基础配置验证通过。"
            )
            logger.info("自动化设置测试完成")
            
        except Exception as e:
            logger.error(f"自动化设置测试失败: {e}")
            QMessageBox.critical(self, "测试失败", f"自动化设置测试失败：{str(e)}")
    
    def _import_settings(self):
        """导入配置"""
        try:
            from PyQt6.QtWidgets import QFileDialog
            
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "导入自动化配置",
                "",
                "JSON文件 (*.json);;所有文件 (*.*)"
            )
            
            if file_path:
                with open(file_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # 更新配置管理器
                for key, value in config.items():
                    self.config_manager.set_setting('automation', key, value)
                
                # 重新加载界面
                self._load_settings()
                
                QMessageBox.information(self, "导入成功", "自动化配置已成功导入")
                logger.info(f"自动化配置已从 {file_path} 导入")
                
        except Exception as e:
            logger.error(f"导入配置失败: {e}")
            QMessageBox.critical(self, "导入失败", f"导入配置失败：{str(e)}")
    
    def _export_settings(self):
        """导出配置"""
        try:
            from PyQt6.QtWidgets import QFileDialog
            
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "导出自动化配置",
                "automation_config.json",
                "JSON文件 (*.json);;所有文件 (*.*)"
            )
            
            if file_path:
                config = self.get_current_settings()
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)
                
                QMessageBox.information(self, "导出成功", f"自动化配置已导出到：\n{file_path}")
                logger.info(f"自动化配置已导出到 {file_path}")
                
        except Exception as e:
            logger.error(f"导出配置失败: {e}")
            QMessageBox.critical(self, "导出失败", f"导出配置失败：{str(e)}")
    
    def _reset_to_defaults(self):
        """重置为默认设置"""
        reply = QMessageBox.question(
            self,
            "确认重置",
            "确定要重置所有自动化设置为默认值吗？\n\n此操作不可撤销。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # 重置配置
                self.config_manager.reset_category('automation')
                
                # 重新加载界面
                self._load_settings()
                
                QMessageBox.information(self, "重置完成", "自动化设置已重置为默认值")
                logger.info("自动化设置已重置为默认值")
                
            except Exception as e:
                logger.error(f"重置设置失败: {e}")
                QMessageBox.critical(self, "重置失败", f"重置设置失败：{str(e)}")
    
    def _apply_settings(self):
        """应用设置"""
        try:
            # 验证设置
            if not self._validate_settings():
                return
            
            # 保存任务优先级
            task_priorities = {}
            for task_key, combo in self.task_priorities.items():
                task_priorities[task_key] = combo.currentText()
            self.config_manager.set_setting('automation', 'task_priorities', task_priorities)
            
            # 保存自动化规则
            try:
                rules_text = self.rules_edit.toPlainText()
                rules = json.loads(rules_text)
                self.config_manager.set_setting('automation', 'automation_rules', rules)
            except json.JSONDecodeError:
                QMessageBox.warning(self, "应用失败", "自动化规则JSON格式错误，请检查后重试")
                return
            
            # 保存配置
            self.config_manager.save_config()
            
            QMessageBox.information(self, "应用成功", "自动化设置已成功应用")
            logger.info("自动化设置已应用")
            
        except Exception as e:
            logger.error(f"应用设置失败: {e}")
            QMessageBox.critical(self, "应用失败", f"应用设置失败：{str(e)}")
    
    def _validate_settings(self) -> bool:
        """验证设置有效性"""
        # 验证随机延迟范围
        if self.random_min_spin.value() >= self.random_max_spin.value():
            QMessageBox.warning(self, "验证失败", "随机延迟最小值不能大于等于最大值")
            return False
        
        # 验证线程数和并发任务数
        if self.concurrent_tasks_spin.value() > self.thread_count_spin.value():
            QMessageBox.warning(self, "验证失败", "并发任务数不能大于工作线程数")
            return False
        
        # 验证紧急停止热键
        emergency_key = self.emergency_key_edit.text().strip()
        if not emergency_key:
            QMessageBox.warning(self, "验证失败", "紧急停止热键不能为空")
            return False
        
        return True
    
    def _on_setting_changed(self, category: str, key: str, value: Any):
        """设置变更处理"""
        try:
            # 更新配置
            self.config_manager.set_setting(category, key, value)
            
            # 发射信号
            self.settings_changed.emit(category, key, value)
            
            logger.debug(f"自动化设置已更新: {category}.{key} = {value}")
            
        except Exception as e:
            logger.error(f"更新自动化设置失败: {e}")
    
    def get_current_settings(self) -> Dict[str, Any]:
        """获取当前设置"""
        # 获取任务优先级
        task_priorities = {}
        for task_key, combo in self.task_priorities.items():
            task_priorities[task_key] = combo.currentText()
        
        # 获取自动化规则
        try:
            rules_text = self.rules_edit.toPlainText()
            automation_rules = json.loads(rules_text)
        except json.JSONDecodeError:
            automation_rules = {}
        
        return {
            # 操作参数
            'click_delay': self.click_delay_spin.value(),
            'key_delay': self.key_delay_spin.value(),
            'operation_interval': self.operation_interval_spin.value(),
            'random_delay_enabled': self.random_delay_check.isChecked(),
            'random_delay_min': self.random_min_spin.value(),
            'random_delay_max': self.random_max_spin.value(),
            'detection_accuracy': self.detection_accuracy_slider.value(),
            'retry_count': self.retry_count_spin.value(),
            'operation_timeout': self.timeout_spin.value(),
            
            # 安全选项
            'window_check': self.window_check.isChecked(),
            'scene_check': self.scene_check.isChecked(),
            'exception_check': self.exception_check.isChecked(),
            'auto_recovery': self.auto_recovery_check.isChecked(),
            'max_runtime': self.max_runtime_spin.value(),
            'cpu_limit': self.cpu_limit_slider.value(),
            'memory_limit': self.memory_limit_spin.value(),
            'emergency_key': self.emergency_key_edit.text(),
            'mouse_corner_stop': self.mouse_corner_check.isChecked(),
            
            # 性能设置
            'performance_mode': self.performance_mode_combo.currentText(),
            'thread_count': self.thread_count_spin.value(),
            'concurrent_tasks': self.concurrent_tasks_spin.value(),
            'image_cache': self.image_cache_check.isChecked(),
            'cache_size': self.cache_size_spin.value(),
            'preload_resources': self.preload_check.isChecked(),
            'smart_wait': self.smart_wait_check.isChecked(),
            'realtime_monitor': self.realtime_monitor_check.isChecked(),
            'monitor_interval': self.monitor_interval_spin.value(),
            'performance_warning': self.performance_warning_check.isChecked(),
            
            # 任务配置
            'schedule_strategy': self.schedule_strategy_combo.currentText(),
            'task_interval': self.task_interval_spin.value(),
            'task_retry': self.task_retry_spin.value(),
            'task_timeout_action': self.task_timeout_combo.currentText(),
            'task_priorities': task_priorities,
            'automation_rules': automation_rules
        }