# -*- coding: utf-8 -*-
"""
任务创建界面组件
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from PyQt6.QtCore import QDateTime, Qt, QTime, pyqtSignal
from PyQt6.QtGui import QFont, QIcon
from ..common.gui_components import (
    BaseWidget,
    QCheckBox,
    QComboBox,
    QDateTimeEdit,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSlider,
    QSpinBox,
    QSplitter,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from loguru import logger

from adapters.task_manager_adapter import TaskManagerAdapter
from core.enums import ActionType
from core.task_validator import TaskValidator
from models.task_models import Task, TaskConfig, TaskPriority, TaskType, ValidationLevel


class TaskCreationWidget(BaseWidget):
    """任务创建界面组件"""

    # 信号定义
    task_created = pyqtSignal(str)  # 任务创建成功信号，传递任务ID
    task_creation_failed = pyqtSignal(str)  # 任务创建失败信号，传递错误信息

    def __init__(self, task_manager: TaskManagerAdapter, parent=None):
        """初始化任务创建界面

        Args:
            task_manager: 任务管理器实例
            parent: 父组件
        """
        super().__init__(parent)

        self.task_manager = task_manager
        self.validator = TaskValidator()
        self.editing_task_id = None  # 用于跟踪编辑状态

        # 当前编辑的任务配置
        self.current_config: Optional[TaskConfig] = None

        # 初始化UI
        self._setup_ui()
        self._connect_signals()

        logger.info("任务创建界面初始化完成")

    def load_task_for_edit(self, task: Task):
        """加载任务进行编辑

        Args:
            task: 要编辑的任务对象
        """
        try:
            # 设置编辑模式
            self.editing_task_id = task.task_id
            self.create_btn.setText("更新任务")

            # 加载基本信息
            self.name_edit.setText(task.name)
            self.description_edit.setPlainText(task.description or "")

            # 设置类型
            type_index = self.type_combo.findData(task.task_type)
            if type_index >= 0:
                self.type_combo.setCurrentIndex(type_index)

            # 设置优先级
            priority_index = self.priority_combo.findData(task.priority)
            if priority_index >= 0:
                self.priority_combo.setCurrentIndex(priority_index)

            # 加载执行设置（从config字典中获取）
            config = task.config or {}
            self.max_duration_spin.setValue(config.get("max_duration", 300))
            self.retry_count_spin.setValue(config.get("retry_count", 3))
            self.retry_interval_spin.setValue(config.get("retry_interval", 5))
            self.safe_mode_check.setChecked(config.get("safe_mode", True))

            # 加载调度设置
            scheduled_time = config.get("scheduled_time")
            if scheduled_time:
                self.schedule_radio.setChecked(True)
                if isinstance(scheduled_time, str):
                    from datetime import datetime

                    scheduled_time = datetime.fromisoformat(scheduled_time)
                self.schedule_datetime.setDateTime(scheduled_time)
            else:
                self.immediate_radio.setChecked(True)

            repeat_interval = config.get("repeat_interval")
            if repeat_interval:
                self.repeat_check.setChecked(True)
                self.repeat_interval_spin.setValue(repeat_interval)

            # 加载动作序列
            actions = config.get("actions")
            if actions:
                actions_text = "\n".join([str(action) for action in actions])
                self.actions_edit.setPlainText(actions_text)

            # 加载自定义参数
            custom_params = config.get("custom_params")
            if custom_params:
                self.custom_params_edit.setPlainText(str(custom_params))

            # 设置验证级别
            validation_level = config.get("validation_level")
            if validation_level:
                validation_index = self.validation_combo.findData(validation_level)
                if validation_index >= 0:
                    self.validation_combo.setCurrentIndex(validation_index)

            logger.info(f"任务编辑数据加载完成: {task.task_id}")

        except Exception as e:
            logger.error(f"加载任务编辑数据失败: {e}")
            QMessageBox.critical(self, "加载失败", f"加载任务编辑数据失败：{str(e)}")

    def clear_form(self):
        """清空表单"""
        # 重置编辑状态
        self.editing_task_id = None
        self.create_btn.setText("创建任务")

        # 清空基本信息
        self.name_edit.clear()
        self.description_edit.clear()
        self.type_combo.setCurrentIndex(0)
        self.priority_combo.setCurrentIndex(1)  # 默认中等优先级

        # 重置执行设置
        self.max_duration_spin.setValue(300)
        self.retry_count_spin.setValue(3)
        self.retry_interval_spin.setValue(5)
        self.safe_mode_check.setChecked(True)

        # 重置调度设置
        self.immediate_radio.setChecked(True)
        self.repeat_check.setChecked(False)
        self.repeat_interval_spin.setValue(60)

        # 清空动作和参数
        self.actions_edit.clear()
        self.custom_params_edit.clear()

        # 重置验证级别
        self.validation_combo.setCurrentIndex(1)  # 默认基础验证

        logger.info("表单已清空")

    def _setup_ui(self):
        """设置用户界面"""
        # 主布局
        main_layout = self.create_vbox_layout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        self.setLayout(main_layout)

        # 标题
        title_label = QLabel("创建新任务")
        title_label.setFont(QFont("Microsoft YaHei", 16, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)

        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # 滚动内容
        scroll_content = QWidget()
        scroll_layout = self.create_vbox_layout()
        scroll_layout.setSpacing(15)
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

    def _create_basic_info_group(self) -> QGroupBox:
        """创建基本信息组"""
        group = self.create_group_box("基本信息")
        layout = self.create_form_layout()
        group.setLayout(layout)

        # 任务名称
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("请输入任务名称")
        layout.addRow("任务名称*:", self.name_edit)

        # 任务描述
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(80)
        self.description_edit.setPlaceholderText("请输入任务描述（可选）")
        layout.addRow("任务描述:", self.description_edit)

        # 任务类型
        self.type_combo = QComboBox()
        for task_type in TaskType:
            self.type_combo.addItem(task_type.value, task_type)
        layout.addRow("任务类型*:", self.type_combo)

        # 任务优先级
        self.priority_combo = QComboBox()
        for priority in TaskPriority:
            self.priority_combo.addItem(priority.value, priority)
        self.priority_combo.setCurrentText(TaskPriority.MEDIUM.value)
        layout.addRow("优先级:", self.priority_combo)

        return group

    def _create_execution_settings_group(self) -> QGroupBox:
        """创建执行设置组"""
        group = self.create_group_box("执行设置")
        layout = self.create_form_layout()
        group.setLayout(layout)

        # 最大执行时间
        self.max_duration_spin = QSpinBox()
        self.max_duration_spin.setRange(1, 3600)  # 1秒到1小时
        self.max_duration_spin.setValue(300)  # 默认5分钟
        self.max_duration_spin.setSuffix(" 秒")
        layout.addRow("最大执行时间:", self.max_duration_spin)

        # 重试次数
        self.retry_count_spin = QSpinBox()
        self.retry_count_spin.setRange(0, 10)
        self.retry_count_spin.setValue(3)
        layout.addRow("重试次数:", self.retry_count_spin)

        # 重试间隔
        self.retry_interval_spin = QDoubleSpinBox()
        self.retry_interval_spin.setRange(0.1, 60.0)
        self.retry_interval_spin.setValue(1.0)
        self.retry_interval_spin.setSuffix(" 秒")
        self.retry_interval_spin.setDecimals(1)
        layout.addRow("重试间隔:", self.retry_interval_spin)

        # 安全模式
        self.safe_mode_check = QCheckBox("启用安全模式")
        self.safe_mode_check.setChecked(True)
        self.safe_mode_check.setToolTip("安全模式下会进行额外的检查和验证")
        layout.addRow("", self.safe_mode_check)

        return group

    def _create_schedule_settings_group(self) -> QGroupBox:
        """创建调度设置组"""
        group = self.create_group_box("调度设置")
        layout = self.create_form_layout()
        group.setLayout(layout)

        # 立即执行
        self.immediate_check = QCheckBox("立即执行")
        self.immediate_check.setChecked(True)
        self.immediate_check.toggled.connect(self._on_immediate_toggled)
        layout.addRow("", self.immediate_check)

        # 计划执行时间
        self.scheduled_time_edit = QDateTimeEdit()
        self.scheduled_time_edit.setDateTime(
            QDateTime.currentDateTime().addSecs(3600)
        )  # 默认1小时后
        self.scheduled_time_edit.setEnabled(False)
        layout.addRow("计划执行时间:", self.scheduled_time_edit)

        # 重复执行
        self.repeat_check = QCheckBox("重复执行")
        self.repeat_check.toggled.connect(self._on_repeat_toggled)
        layout.addRow("", self.repeat_check)

        # 重复间隔
        self.repeat_interval_spin = QSpinBox()
        self.repeat_interval_spin.setRange(1, 1440)  # 1分钟到24小时
        self.repeat_interval_spin.setValue(60)
        self.repeat_interval_spin.setSuffix(" 分钟")
        self.repeat_interval_spin.setEnabled(False)
        layout.addRow("重复间隔:", self.repeat_interval_spin)

        return group

    def _create_actions_group(self) -> QGroupBox:
        """创建动作序列组"""
        group = self.create_group_box("动作序列")
        layout = self.create_vbox_layout()
        group.setLayout(layout)

        # 动作列表
        self.actions_list = QListWidget()
        self.actions_list.setMaximumHeight(200)
        layout.addWidget(self.actions_list)

        # 动作操作按钮
        action_buttons_layout = self.create_hbox_layout()

        self.add_action_btn = QPushButton("添加动作")
        self.add_action_btn.clicked.connect(self._add_action)
        action_buttons_layout.addWidget(self.add_action_btn)

        self.edit_action_btn = QPushButton("编辑动作")
        self.edit_action_btn.clicked.connect(self._edit_action)
        self.edit_action_btn.setEnabled(False)
        action_buttons_layout.addWidget(self.edit_action_btn)

        self.remove_action_btn = QPushButton("删除动作")
        self.remove_action_btn.clicked.connect(self._remove_action)
        self.remove_action_btn.setEnabled(False)
        action_buttons_layout.addWidget(self.remove_action_btn)

        action_buttons_layout.addStretch()
        layout.addLayout(action_buttons_layout)

        # 连接列表选择信号
        self.actions_list.itemSelectionChanged.connect(
            self._on_action_selection_changed
        )

        return group

    def _create_advanced_settings_group(self) -> QGroupBox:
        """创建高级设置组"""
        group = self.create_group_box("高级设置")
        layout = self.create_form_layout()
        group.setLayout(layout)

        # 自定义参数
        self.custom_params_edit = QTextEdit()
        self.custom_params_edit.setMaximumHeight(100)
        self.custom_params_edit.setPlaceholderText(
            'JSON格式的自定义参数，例如：{"key": "value"}'
        )
        layout.addRow("自定义参数:", self.custom_params_edit)

        # 验证级别
        self.validation_combo = QComboBox()
        for level in ValidationLevel:
            self.validation_combo.addItem(level.value, level)
        self.validation_combo.setCurrentText(ValidationLevel.WARNING.value)
        layout.addRow("验证级别:", self.validation_combo)

        return group

    def _create_button_layout(self) -> QHBoxLayout:
        """创建按钮布局"""
        layout = self.create_hbox_layout()

        # 验证按钮
        self.validate_btn = QPushButton("验证配置")
        self.validate_btn.clicked.connect(self._validate_config)
        layout.addWidget(self.validate_btn)

        layout.addStretch()

        # 重置按钮
        self.reset_btn = QPushButton("重置")
        self.reset_btn.clicked.connect(self._reset_form)
        layout.addWidget(self.reset_btn)

        # 创建按钮
        self.create_btn = QPushButton("创建任务")
        self.create_btn.setStyleSheet(
            """
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
        """
        )
        self.create_btn.clicked.connect(self._create_task)
        layout.addWidget(self.create_btn)

        return layout

    def _connect_signals(self):
        """连接信号和槽"""
        # 表单字段变化时启用创建按钮
        self.name_edit.textChanged.connect(self._on_form_changed)
        self.type_combo.currentTextChanged.connect(self._on_form_changed)

    def _on_immediate_toggled(self, checked: bool):
        """立即执行选项切换"""
        self.scheduled_time_edit.setEnabled(not checked)

    def _on_repeat_toggled(self, checked: bool):
        """重复执行选项切换"""
        self.repeat_interval_spin.setEnabled(checked)

    def _on_action_selection_changed(self):
        """动作列表选择变化"""
        has_selection = bool(self.actions_list.selectedItems())
        self.edit_action_btn.setEnabled(has_selection)
        self.remove_action_btn.setEnabled(has_selection)

    def _on_form_changed(self):
        """表单内容变化"""
        # 检查必填字段
        has_name = bool(self.name_edit.text().strip())
        self.create_btn.setEnabled(has_name)

    def _add_action(self):
        """添加动作"""
        # 这里应该打开动作编辑对话框
        # 暂时添加一个示例动作
        action_text = f"点击动作 - ({len(self.actions_list) + 1})"
        item = QListWidgetItem(action_text)
        item.setData(
            Qt.ItemDataRole.UserRole,
            {"type": ActionType.CLICK, "params": {"x": 100, "y": 100}},
        )
        self.actions_list.addItem(item)

        logger.info(f"添加动作: {action_text}")

    def _edit_action(self):
        """编辑动作"""
        current_item = self.actions_list.currentItem()
        if current_item:
            # 这里应该打开动作编辑对话框
            QMessageBox.information(self, "提示", "动作编辑功能待实现")

    def _remove_action(self):
        """删除动作"""
        current_row = self.actions_list.currentRow()
        if current_row >= 0:
            item = self.actions_list.takeItem(current_row)
            logger.info(f"删除动作: {item.text()}")

    def _validate_config(self):
        """验证配置"""
        try:
            config = self._build_task_config()

            results = self.validator.validate_task_config(config)

            # 检查是否有错误级别的问题
            errors = [r.message for r in results if r.level.value == "error"]
            warnings = [r.message for r in results if r.level.value == "warning"]

            if not errors:
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

        except Exception as e:
            logger.error(f"配置验证失败: {e}")
            QMessageBox.critical(self, "验证错误", f"配置验证时发生错误：{str(e)}")

    def _create_task(self):
        """创建或更新任务"""
        try:
            # 构建任务配置
            config = self._build_task_config()

            # 验证配置
            validation_level = self.validation_combo.currentData()
            results = self.validator.validate_task_config(config)

            # 检查是否有错误级别的问题
            errors = [r.message for r in results if r.level.value == "error"]
            if errors:
                error_msg = "\n".join(errors)
                action = "更新" if self.editing_task_id else "创建"
                QMessageBox.warning(
                    self, f"{action}失败", f"任务配置验证失败：\n{error_msg}"
                )
                return

            if self.editing_task_id:
                # 更新现有任务
                success = self.task_manager.update_task(self.editing_task_id, config)
                if success:
                    # 发送成功信号
                    self.task_created.emit(self.editing_task_id)

                    # 显示成功消息
                    QMessageBox.information(
                        self,
                        "更新成功",
                        f"任务更新成功！\n任务ID: {self.editing_task_id}",
                    )

                    # 清空表单
                    self.clear_form()

                    logger.info(f"任务更新成功: {self.editing_task_id}")
                else:
                    raise Exception("任务更新失败")
            else:
                # 创建新任务
                task_id = self.task_manager.create_task_sync(
                    config=config, user_id="default_user"  # 暂时使用默认用户
                )

                # 发送成功信号
                self.task_created.emit(task_id)

                # 显示成功消息
                QMessageBox.information(
                    self, "创建成功", f"任务创建成功！\n任务ID: {task_id}"
                )

                # 重置表单
                self._reset_form()

                logger.info(f"任务创建成功: {task_id}")

        except Exception as e:
            error_msg = str(e)
            action = "更新" if self.editing_task_id else "创建"
            logger.error(f"任务{action}失败: {error_msg}")

            # 发送失败信号
            self.task_creation_failed.emit(error_msg)

            # 显示错误消息
            QMessageBox.critical(
                self, f"{action}失败", f"任务{action}失败：{error_msg}"
            )

    def _build_task_config(self) -> TaskConfig:
        """构建任务配置"""
        import json

        # 获取基本信息
        name = self.name_edit.text().strip()
        description = self.description_edit.toPlainText().strip()
        task_type = self.type_combo.currentData()
        priority = self.priority_combo.currentData()

        # 获取执行设置
        max_duration = self.max_duration_spin.value()
        retry_count = self.retry_count_spin.value()
        retry_interval = self.retry_interval_spin.value()
        safe_mode = self.safe_mode_check.isChecked()

        # 获取调度设置
        immediate = self.immediate_radio.isChecked()
        scheduled_time = (
            None if immediate else self.schedule_datetime.dateTime().toPython()
        )
        repeat = self.repeat_check.isChecked()
        repeat_interval = self.repeat_interval_spin.value() if repeat else None

        # 获取动作序列
        actions = []
        actions_text = self.actions_edit.toPlainText().strip()
        if actions_text:
            # 简单解析动作文本，每行一个动作
            for line in actions_text.split("\n"):
                line = line.strip()
                if line:
                    actions.append({"type": "custom", "description": line})

        # 获取自定义参数
        custom_params = {}
        custom_params_text = self.custom_params_edit.toPlainText().strip()
        if custom_params_text:
            try:
                custom_params = json.loads(custom_params_text)
            except json.JSONDecodeError:
                raise ValueError("自定义参数格式错误，请使用有效的JSON格式")

        # 构建配置
        config = TaskConfig(
            name=name,
            description=description,
            task_type=task_type,
            priority=priority,
            max_retry_count=retry_count,
            timeout_seconds=max_duration,
            actions=actions,
            custom_params=custom_params,
        )

        # 设置调度配置
        if not immediate and scheduled_time:
            config.schedule_enabled = True
            config.schedule_time = scheduled_time.strftime("%H:%M")

        # 设置重复间隔
        if repeat and repeat_interval:
            config.repeat_interval = repeat_interval

        return config

    def _reset_form(self):
        """重置表单"""
        # 重置基本信息
        self.name_edit.clear()
        self.description_edit.clear()
        self.type_combo.setCurrentIndex(0)
        self.priority_combo.setCurrentText(TaskPriority.MEDIUM.value)

        # 重置执行设置
        self.max_duration_spin.setValue(300)
        self.retry_count_spin.setValue(3)
        self.retry_interval_spin.setValue(1.0)
        self.safe_mode_check.setChecked(True)

        # 重置调度设置
        self.immediate_check.setChecked(True)
        self.scheduled_time_edit.setDateTime(QDateTime.currentDateTime().addSecs(3600))
        self.repeat_check.setChecked(False)
        self.repeat_interval_spin.setValue(60)

        # 重置动作列表
        self.actions_list.clear()

        # 重置高级设置
        self.custom_params_edit.clear()
        self.validation_combo.setCurrentText(ValidationLevel.WARNING.value)

        logger.info("表单已重置")

    def load_task_config(self, config: TaskConfig):
        """加载任务配置到表单

        Args:
            config: 要加载的任务配置
        """
        # 加载基本信息
        self.name_edit.setText(config.name)
        self.description_edit.setPlainText(config.description or "")

        # 设置任务类型
        for i in range(self.type_combo.count()):
            if self.type_combo.itemData(i) == config.task_type:
                self.type_combo.setCurrentIndex(i)
                break

        # 设置优先级
        for i in range(self.priority_combo.count()):
            if self.priority_combo.itemData(i) == config.priority:
                self.priority_combo.setCurrentIndex(i)
                break

        # 加载执行设置
        self.max_duration_spin.setValue(config.timeout_seconds)
        self.retry_count_spin.setValue(config.max_retry_count)
        # retry_interval 和 safe_mode 不是 TaskConfig 的标准属性，使用默认值
        self.retry_interval_spin.setValue(1.0)
        self.safe_mode_check.setChecked(True)

        # 加载调度设置
        if config.schedule_enabled and config.schedule_time:
            self.immediate_check.setChecked(False)
            # 解析 HH:MM 格式的时间
            try:
                hour, minute = map(int, config.schedule_time.split(":"))
                current_date = QDateTime.currentDateTime().date()
                scheduled_datetime = QDateTime(current_date, QTime(hour, minute))
                self.scheduled_time_edit.setDateTime(scheduled_datetime)
            except (ValueError, AttributeError):
                self.immediate_check.setChecked(True)
        else:
            self.immediate_check.setChecked(True)

        # repeat_interval 不是 TaskConfig 的标准属性，使用默认值
        self.repeat_check.setChecked(False)
        self.repeat_interval_spin.setValue(60)

        # 加载动作序列
        self.actions_list.clear()
        for action in config.actions:
            action_text = (
                f"{action.get('type', 'Unknown')} - {action.get('params', {})}"
            )
            item = QListWidgetItem(action_text)
            item.setData(Qt.ItemDataRole.UserRole, action)
            self.actions_list.addItem(item)

        # 加载自定义参数
        if config.custom_params:
            import json

            self.custom_params_edit.setPlainText(
                json.dumps(config.custom_params, indent=2, ensure_ascii=False)
            )

        self.current_config = config
        logger.info(f"已加载任务配置: {config.name}")
