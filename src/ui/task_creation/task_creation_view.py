# -*- coding: utf-8 -*-
"""
任务创建View层
MVP架构中的视图层，负责UI界面展示和用户交互
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from PyQt6.QtCore import QDateTime, Qt, QTime, pyqtSignal
from PyQt6.QtGui import QFont
from loguru import logger

from models.task_models import TaskPriority, TaskType, ValidationLevel
from ui.common.ui_components import (
    BaseUIWidget,
    QCheckBox,
    QComboBox,
    QDateTimeEdit,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    LoadingWidget,
)
from ui.mvp.base_view import BaseView


class TaskCreationView(BaseView):
    """任务创建视图层
    
    负责任务创建界面的展示和用户交互
    """
    
    # 用户交互信号
    form_field_changed = pyqtSignal(str, object)  # 表单字段变化
    action_add_requested = pyqtSignal()  # 添加动作请求
    action_edit_requested = pyqtSignal(int)  # 编辑动作请求
    action_remove_requested = pyqtSignal(int)  # 删除动作请求
    validation_requested = pyqtSignal()  # 验证请求
    task_create_requested = pyqtSignal()  # 创建任务请求
    form_reset_requested = pyqtSignal()  # 重置表单请求
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # UI组件引用
        self._form_widgets = {}
        self._action_buttons = {}
        
        # 加载状态
        self._loading_widget = None
        
        self._setup_ui()
        self._connect_internal_signals()
        
        logger.info("任务创建View初始化完成")
    
    def _setup_ui(self):
        """设置用户界面"""
        # 主布局
        main_layout = self.create_vbox_layout()
        margin = self._get_config_value('ui.task_creation.layout_margin', 10)
        spacing = self._get_config_value('ui.task_creation.layout_spacing', 10)
        main_layout.setContentsMargins(margin, margin, margin, margin)
        main_layout.setSpacing(spacing)
        self.setLayout(main_layout)
        
        # 标题
        title_font_size = self._get_config_value('ui.task_creation.title_font_size', 16)
        self._title_label = self.create_title_label("创建新任务", title_font_size)
        main_layout.addWidget(self._title_label)
        
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # 滚动内容
        scroll_content = QWidget()
        scroll_layout = self.create_vbox_layout()
        scroll_spacing = self._get_config_value('ui.task_creation.scroll_spacing', 15)
        scroll_layout.setSpacing(scroll_spacing)
        scroll_content.setLayout(scroll_layout)
        
        # 基本信息组
        basic_group = self._create_basic_info_group()
        scroll_layout.addWidget(basic_group)
        
        # 执行设置组
        execution_group = self._create_execution_settings_group()
        scroll_layout.addWidget(execution_group)
        
        # 调度设置组
        schedule_group = self._create_schedule_settings_group()
        scroll_layout.addWidget(schedule_group)
        
        # 动作序列组
        actions_group = self._create_actions_group()
        scroll_layout.addWidget(actions_group)
        
        # 高级设置组
        advanced_group = self._create_advanced_settings_group()
        scroll_layout.addWidget(advanced_group)
        
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)
        
        # 按钮区域
        button_layout = self._create_button_layout()
        main_layout.addLayout(button_layout)
        
        # 加载指示器
        self._loading_widget = LoadingWidget("处理中...")
        self._loading_widget.hide()
        main_layout.addWidget(self._loading_widget)
    
    def _create_basic_info_group(self) -> QGroupBox:
        """创建基本信息组"""
        group = self.create_group_box("基本信息")
        layout = self.create_form_layout()
        group.setLayout(layout)
        
        # 任务名称
        self._form_widgets['name'] = QLineEdit()
        self._form_widgets['name'].setPlaceholderText("请输入任务名称")
        layout.addRow("任务名称*:", self._form_widgets['name'])
        
        # 任务描述
        self._form_widgets['description'] = QTextEdit()
        desc_height = self._get_config_value('ui.task_creation.description_height', 80)
        self._form_widgets['description'].setMaximumHeight(desc_height)
        self._form_widgets['description'].setPlaceholderText("请输入任务描述（可选）")
        layout.addRow("任务描述:", self._form_widgets['description'])
        
        # 任务类型
        self._form_widgets['task_type'] = QComboBox()
        for task_type in TaskType:
            self._form_widgets['task_type'].addItem(task_type.value, task_type)
        layout.addRow("任务类型*:", self._form_widgets['task_type'])
        
        # 任务优先级
        self._form_widgets['priority'] = QComboBox()
        for priority in TaskPriority:
            self._form_widgets['priority'].addItem(priority.value, priority)
        self._form_widgets['priority'].setCurrentText(TaskPriority.MEDIUM.value)
        layout.addRow("优先级:", self._form_widgets['priority'])
        
        return group
    
    def _create_execution_settings_group(self) -> QGroupBox:
        """创建执行设置组"""
        group = self.create_group_box("执行设置")
        layout = self.create_form_layout()
        group.setLayout(layout)
        
        # 最大执行时间
        self._form_widgets['max_duration'] = QSpinBox()
        duration_min = self._get_config_value('ui.task_creation.duration_range_min', 1)
        duration_max = self._get_config_value('ui.task_creation.duration_range_max', 3600)
        duration_default = self._get_config_value('ui.task_creation.default_max_duration', 300)
        self._form_widgets['max_duration'].setRange(duration_min, duration_max)
        self._form_widgets['max_duration'].setValue(duration_default)
        self._form_widgets['max_duration'].setSuffix(" 秒")
        layout.addRow("最大执行时间:", self._form_widgets['max_duration'])
        
        # 重试次数
        self._form_widgets['retry_count'] = QSpinBox()
        retry_min = self._get_config_value('ui.task_creation.retry_range_min', 0)
        retry_max = self._get_config_value('ui.task_creation.retry_range_max', 10)
        retry_default = self._get_config_value('ui.task_creation.default_retry_count', 3)
        self._form_widgets['retry_count'].setRange(retry_min, retry_max)
        self._form_widgets['retry_count'].setValue(retry_default)
        layout.addRow("重试次数:", self._form_widgets['retry_count'])
        
        # 重试间隔
        self._form_widgets['retry_interval'] = QDoubleSpinBox()
        interval_min = self._get_config_value('ui.task_creation.retry_interval_min', 0.1)
        interval_max = self._get_config_value('ui.task_creation.retry_interval_max', 60.0)
        interval_default = self._get_config_value('ui.task_creation.default_retry_interval', 1.0)
        interval_decimals = self._get_config_value('ui.task_creation.retry_interval_decimals', 1)
        self._form_widgets['retry_interval'].setRange(interval_min, interval_max)
        self._form_widgets['retry_interval'].setValue(interval_default)
        self._form_widgets['retry_interval'].setSuffix(" 秒")
        self._form_widgets['retry_interval'].setDecimals(interval_decimals)
        layout.addRow("重试间隔:", self._form_widgets['retry_interval'])
        
        # 安全模式
        self._form_widgets['safe_mode'] = QCheckBox("启用安全模式")
        self._form_widgets['safe_mode'].setChecked(True)
        self._form_widgets['safe_mode'].setToolTip("安全模式下会进行额外的检查和验证")
        layout.addRow("", self._form_widgets['safe_mode'])
        
        return group
    
    def _create_schedule_settings_group(self) -> QGroupBox:
        """创建调度设置组"""
        group = self.create_group_box("调度设置")
        layout = self.create_form_layout()
        group.setLayout(layout)
        
        # 立即执行
        self._form_widgets['immediate'] = QCheckBox("立即执行")
        self._form_widgets['immediate'].setChecked(True)
        layout.addRow("", self._form_widgets['immediate'])
        
        # 计划执行时间
        self._form_widgets['scheduled_time'] = QDateTimeEdit()
        default_schedule_hours = self._get_config_value('ui.task_creation.default_schedule_hours', 1)
        self._form_widgets['scheduled_time'].setDateTime(
            QDateTime.currentDateTime().addSecs(default_schedule_hours * 3600)
        )
        self._form_widgets['scheduled_time'].setEnabled(False)
        layout.addRow("计划执行时间:", self._form_widgets['scheduled_time'])
        
        # 重复执行
        self._form_widgets['repeat'] = QCheckBox("重复执行")
        layout.addRow("", self._form_widgets['repeat'])
        
        # 重复间隔
        self._form_widgets['repeat_interval'] = QSpinBox()
        repeat_min = self._get_config_value('ui.task_creation.repeat_interval_min', 1)
        repeat_max = self._get_config_value('ui.task_creation.repeat_interval_max', 1440)
        repeat_default = self._get_config_value('ui.task_creation.repeat_interval_default', 60)
        self._form_widgets['repeat_interval'].setRange(repeat_min, repeat_max)
        self._form_widgets['repeat_interval'].setValue(repeat_default)
        self._form_widgets['repeat_interval'].setSuffix(" 分钟")
        self._form_widgets['repeat_interval'].setEnabled(False)
        layout.addRow("重复间隔:", self._form_widgets['repeat_interval'])
        
        return group
    
    def _create_actions_group(self) -> QGroupBox:
        """创建动作序列组"""
        group = self.create_group_box("动作序列")
        layout = self.create_vbox_layout()
        group.setLayout(layout)
        
        # 动作列表
        self._form_widgets['actions_list'] = QListWidget()
        actions_list_height = self._get_config_value('ui.task_creation.actions_list_height', 200)
        self._form_widgets['actions_list'].setMaximumHeight(actions_list_height)
        layout.addWidget(self._form_widgets['actions_list'])
        
        # 动作操作按钮
        action_buttons_layout = self.create_hbox_layout()
        
        self._action_buttons['add'] = self.create_button("添加动作")
        action_buttons_layout.addWidget(self._action_buttons['add'])
        
        self._action_buttons['edit'] = self.create_button("编辑动作")
        self._action_buttons['edit'].setEnabled(False)
        action_buttons_layout.addWidget(self._action_buttons['edit'])
        
        self._action_buttons['remove'] = self.create_button("删除动作")
        self._action_buttons['remove'].setEnabled(False)
        action_buttons_layout.addWidget(self._action_buttons['remove'])
        
        action_buttons_layout.addStretch()
        layout.addLayout(action_buttons_layout)
        
        return group
    
    def _create_advanced_settings_group(self) -> QGroupBox:
        """创建高级设置组"""
        group = self.create_group_box("高级设置")
        layout = self.create_form_layout()
        group.setLayout(layout)
        
        # 自定义参数
        self._form_widgets['custom_params'] = QTextEdit()
        custom_params_height = self._get_config_value('ui.task_creation.custom_params_height', 100)
        self._form_widgets['custom_params'].setMaximumHeight(custom_params_height)
        self._form_widgets['custom_params'].setPlaceholderText(
            'JSON格式的自定义参数，例如：{"key": "value"}'
        )
        layout.addRow("自定义参数:", self._form_widgets['custom_params'])
        
        # 验证级别
        self._form_widgets['validation_level'] = QComboBox()
        for level in ValidationLevel:
            self._form_widgets['validation_level'].addItem(level.value, level)
        self._form_widgets['validation_level'].setCurrentText(ValidationLevel.WARNING.value)
        layout.addRow("验证级别:", self._form_widgets['validation_level'])
        
        return group
    
    def _create_button_layout(self) -> QHBoxLayout:
        """创建按钮布局"""
        layout = self.create_hbox_layout()
        
        # 验证按钮
        self._validate_btn = self.create_button("验证配置")
        layout.addWidget(self._validate_btn)
        
        layout.addStretch()
        
        # 重置按钮
        self._reset_btn = self.create_button("重置")
        layout.addWidget(self._reset_btn)
        
        # 创建按钮
        self._create_btn = self.create_button("创建任务")
        self._create_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        layout.addWidget(self._create_btn)
        
        return layout
    
    def _connect_internal_signals(self):
        """连接内部信号"""
        # 表单字段变化信号
        self._form_widgets['name'].textChanged.connect(
            lambda text: self.form_field_changed.emit('name', text)
        )
        self._form_widgets['description'].textChanged.connect(
            lambda: self.form_field_changed.emit('description', self._form_widgets['description'].toPlainText())
        )
        self._form_widgets['task_type'].currentTextChanged.connect(
            lambda: self.form_field_changed.emit('task_type', self._form_widgets['task_type'].currentData())
        )
        self._form_widgets['priority'].currentTextChanged.connect(
            lambda: self.form_field_changed.emit('priority', self._form_widgets['priority'].currentData())
        )
        
        # 执行设置变化
        self._form_widgets['max_duration'].valueChanged.connect(
            lambda value: self.form_field_changed.emit('max_duration', value)
        )
        self._form_widgets['retry_count'].valueChanged.connect(
            lambda value: self.form_field_changed.emit('retry_count', value)
        )
        self._form_widgets['retry_interval'].valueChanged.connect(
            lambda value: self.form_field_changed.emit('retry_interval', value)
        )
        self._form_widgets['safe_mode'].toggled.connect(
            lambda checked: self.form_field_changed.emit('safe_mode', checked)
        )
        
        # 调度设置变化
        self._form_widgets['immediate'].toggled.connect(self._on_immediate_toggled)
        self._form_widgets['immediate'].toggled.connect(
            lambda checked: self.form_field_changed.emit('immediate', checked)
        )
        self._form_widgets['scheduled_time'].dateTimeChanged.connect(
            lambda dt: self.form_field_changed.emit('scheduled_time', dt.toPython())
        )
        self._form_widgets['repeat'].toggled.connect(self._on_repeat_toggled)
        self._form_widgets['repeat'].toggled.connect(
            lambda checked: self.form_field_changed.emit('repeat', checked)
        )
        self._form_widgets['repeat_interval'].valueChanged.connect(
            lambda value: self.form_field_changed.emit('repeat_interval', value)
        )
        
        # 高级设置变化
        self._form_widgets['custom_params'].textChanged.connect(
            lambda: self.form_field_changed.emit('custom_params', self._form_widgets['custom_params'].toPlainText())
        )
        self._form_widgets['validation_level'].currentTextChanged.connect(
            lambda: self.form_field_changed.emit('validation_level', self._form_widgets['validation_level'].currentData())
        )
        
        # 动作操作按钮
        self._action_buttons['add'].clicked.connect(self.action_add_requested.emit)
        self._action_buttons['edit'].clicked.connect(
            lambda: self.action_edit_requested.emit(self._form_widgets['actions_list'].currentRow())
        )
        self._action_buttons['remove'].clicked.connect(
            lambda: self.action_remove_requested.emit(self._form_widgets['actions_list'].currentRow())
        )
        
        # 动作列表选择变化
        self._form_widgets['actions_list'].itemSelectionChanged.connect(
            self._on_action_selection_changed
        )
        
        # 主要操作按钮
        self._validate_btn.clicked.connect(self.validation_requested.emit)
        self._reset_btn.clicked.connect(self.form_reset_requested.emit)
        self._create_btn.clicked.connect(self.task_create_requested.emit)
    
    def _on_immediate_toggled(self, checked: bool):
        """立即执行选项切换"""
        self._form_widgets['scheduled_time'].setEnabled(not checked)
    
    def _on_repeat_toggled(self, checked: bool):
        """重复执行选项切换"""
        self._form_widgets['repeat_interval'].setEnabled(checked)
    
    def _on_action_selection_changed(self):
        """动作列表选择变化"""
        has_selection = bool(self._form_widgets['actions_list'].selectedItems())
        self._action_buttons['edit'].setEnabled(has_selection)
        self._action_buttons['remove'].setEnabled(has_selection)
    
    def set_form_field_value(self, field: str, value: Any):
        """设置表单字段值
        
        Args:
            field: 字段名
            value: 字段值
        """
        try:
            widget = self._form_widgets.get(field)
            if not widget:
                logger.warning(f"未找到表单字段: {field}")
                return
            
            # 根据字段类型设置值
            if field == 'name':
                widget.setText(str(value))
            elif field == 'description':
                widget.setPlainText(str(value))
            elif field in ['task_type', 'priority', 'validation_level']:
                for i in range(widget.count()):
                    if widget.itemData(i) == value:
                        widget.setCurrentIndex(i)
                        break
            elif field in ['max_duration', 'retry_count', 'repeat_interval']:
                widget.setValue(int(value))
            elif field == 'retry_interval':
                widget.setValue(float(value))
            elif field in ['safe_mode', 'immediate', 'repeat']:
                widget.setChecked(bool(value))
            elif field == 'scheduled_time':
                if isinstance(value, datetime):
                    widget.setDateTime(QDateTime(value))
            elif field == 'custom_params':
                if isinstance(value, dict):
                    import json
                    widget.setPlainText(json.dumps(value, indent=2, ensure_ascii=False))
                else:
                    widget.setPlainText(str(value))
            
            logger.debug(f"设置表单字段值: {field} = {value}")
            
        except Exception as e:
            logger.error(f"设置表单字段值失败: {field} = {value}, 错误: {e}")
    
    def get_form_field_value(self, field: str) -> Any:
        """获取表单字段值
        
        Args:
            field: 字段名
            
        Returns:
            Any: 字段值
        """
        try:
            widget = self._form_widgets.get(field)
            if not widget:
                logger.warning(f"未找到表单字段: {field}")
                return None
            
            # 根据字段类型获取值
            if field == 'name':
                return widget.text()
            elif field == 'description':
                return widget.toPlainText()
            elif field in ['task_type', 'priority', 'validation_level']:
                return widget.currentData()
            elif field in ['max_duration', 'retry_count', 'repeat_interval']:
                return widget.value()
            elif field == 'retry_interval':
                return widget.value()
            elif field in ['safe_mode', 'immediate', 'repeat']:
                return widget.isChecked()
            elif field == 'scheduled_time':
                return widget.dateTime().toPython()
            elif field == 'custom_params':
                text = widget.toPlainText().strip()
                if text:
                    try:
                        import json
                        return json.loads(text)
                    except json.JSONDecodeError:
                        return text
                return {}
            
            return None
            
        except Exception as e:
            logger.error(f"获取表单字段值失败: {field}, 错误: {e}")
            return None
    
    def clear_form(self):
        """清空表单"""
        try:
            # 清空基本信息
            self._form_widgets['name'].clear()
            self._form_widgets['description'].clear()
            self._form_widgets['task_type'].setCurrentIndex(0)
            self._form_widgets['priority'].setCurrentText(TaskPriority.MEDIUM.value)
            
            # 重置执行设置
            self._form_widgets['max_duration'].setValue(300)
            self._form_widgets['retry_count'].setValue(3)
            self._form_widgets['retry_interval'].setValue(1.0)
            self._form_widgets['safe_mode'].setChecked(True)
            
            # 重置调度设置
            self._form_widgets['immediate'].setChecked(True)
            self._form_widgets['scheduled_time'].setDateTime(QDateTime.currentDateTime().addSecs(3600))
            self._form_widgets['repeat'].setChecked(False)
            self._form_widgets['repeat_interval'].setValue(60)
            
            # 清空动作列表
            self._form_widgets['actions_list'].clear()
            
            # 重置高级设置
            self._form_widgets['custom_params'].clear()
            self._form_widgets['validation_level'].setCurrentText(ValidationLevel.WARNING.value)
            
            # 重置按钮状态
            self._create_btn.setText("创建任务")
            self._create_btn.setEnabled(False)
            
            logger.info("表单已清空")
            
        except Exception as e:
            logger.error(f"清空表单失败: {e}")
    
    def set_editing_mode(self, editing: bool, task_id: Optional[str] = None):
        """设置编辑模式
        
        Args:
            editing: 是否为编辑模式
            task_id: 编辑的任务ID
        """
        if editing:
            self._title_label.setText(f"编辑任务 - {task_id or ''}")
            self._create_btn.setText("更新任务")
        else:
            self._title_label.setText("创建新任务")
            self._create_btn.setText("创建任务")
    
    def update_actions_list(self, actions: List[Dict[str, Any]]):
        """更新动作列表
        
        Args:
            actions: 动作列表
        """
        try:
            self._form_widgets['actions_list'].clear()
            
            for i, action in enumerate(actions):
                action_text = f"{i+1}. {action.get('type', 'Unknown')} - {action.get('description', '')}"
                item = QListWidgetItem(action_text)
                item.setData(Qt.ItemDataRole.UserRole, action)
                self._form_widgets['actions_list'].addItem(item)
            
            logger.debug(f"动作列表已更新: {len(actions)} 项")
            
        except Exception as e:
            logger.error(f"更新动作列表失败: {e}")
    
    def set_create_button_enabled(self, enabled: bool):
        """设置创建按钮启用状态
        
        Args:
            enabled: 是否启用
        """
        self._create_btn.setEnabled(enabled)
    
    def show_validation_result(self, success: bool, errors: List[str], warnings: List[str]):
        """显示验证结果
        
        Args:
            success: 验证是否成功
            errors: 错误信息列表
            warnings: 警告信息列表
        """
        if success:
            if warnings:
                warning_msg = "\n".join(warnings)
                QMessageBox.information(
                    self, "验证成功", f"任务配置验证通过！\n\n警告：\n{warning_msg}"
                )
            else:
                QMessageBox.information(self, "验证成功", "任务配置验证通过！")
        else:
            error_msg = "\n".join(errors)
            if warnings:
                warning_msg = "\n".join(warnings)
                QMessageBox.warning(
                    self,
                    "验证失败",
                    f"任务配置验证失败：\n{error_msg}\n\n警告：\n{warning_msg}",
                )
            else:
                QMessageBox.warning(
                    self, "验证失败", f"任务配置验证失败：\n{error_msg}"
                )
    
    def show_success_message(self, title: str, message: str):
        """显示成功消息
        
        Args:
            title: 标题
            message: 消息内容
        """
        QMessageBox.information(self, title, message)
    
    def show_error_message(self, title: str, message: str):
        """显示错误消息
        
        Args:
            title: 标题
            message: 消息内容
        """
        QMessageBox.critical(self, title, message)
    
    # BaseView接口实现
    def show_loading(self, message: str = "处理中..."):
        """显示加载状态"""
        self._loading_widget.set_text(message)
        self._loading_widget.start_loading()
    
    def hide_loading(self):
        """隐藏加载状态"""
        self._loading_widget.stop_loading()
    
    def show_error(self, message: str):
        """显示错误信息"""
        self.show_error_message("错误", message)
    
    def update_data(self, data: Dict[str, Any]):
        """更新界面数据
        
        Args:
            data: 数据字典
        """
        for field, value in data.items():
            if field == 'actions':
                self.update_actions_list(value)
            else:
                self.set_form_field_value(field, value)
    
    def set_enabled(self, enabled: bool):
        """设置界面启用状态
        
        Args:
            enabled: 是否启用
        """
        self.setEnabled(enabled)
    
    def get_user_input(self) -> Dict[str, Any]:
        """获取用户输入
        
        Returns:
            Dict[str, Any]: 用户输入数据
        """
        data = {}
        for field in self._form_widgets.keys():
            if field != 'actions_list':  # 动作列表单独处理
                data[field] = self.get_form_field_value(field)
        return data