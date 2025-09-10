"""任务创建视图模块.

实现任务创建界面的视图组件。
"""

from typing import Optional, Dict, Any
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QTextEdit, QComboBox, QSpinBox,
    QPushButton, QGroupBox, QCheckBox, QDateTimeEdit,
    QSlider, QTabWidget, QScrollArea, QFrame,
    QMessageBox, QFileDialog, QProgressBar
)
from PyQt5.QtCore import Qt, pyqtSignal, QDateTime
from PyQt5.QtGui import QFont, QIcon

from ...core.enhanced_task_executor import (
    TaskType, TaskPriority, TaskConfig, TaskStatus
)


class TaskCreationView(QWidget):
    """任务创建视图。"""
    
    # 信号定义
    taskCreated = pyqtSignal(object)  # TaskConfig
    taskUpdated = pyqtSignal(object)  # TaskConfig
    cancelled = pyqtSignal()
    
    def __init__(self, parent=None):
        """初始化任务创建视图。
        
        Args:
            parent: 父组件
        """
        super().__init__(parent)
        self.current_task_config = None
        self.is_edit_mode = False
        
        self._setup_ui()
        self._connect_signals()
        
    def _setup_ui(self):
        """设置用户界面。"""
        self.setWindowTitle("创建任务")
        self.setMinimumSize(600, 500)
        
        # 主布局
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        
        # 标题
        self.title_label = QLabel("创建新任务")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        self.title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.title_label)
        
        # 滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # 基本信息组
        basic_group = self._create_basic_info_group()
        scroll_layout.addWidget(basic_group)
        
        # 任务配置组
        config_group = self._create_task_config_group()
        scroll_layout.addWidget(config_group)
        
        # 高级设置组
        advanced_group = self._create_advanced_settings_group()
        scroll_layout.addWidget(advanced_group)
        
        scroll_area.setWidget(scroll_widget)
        main_layout.addWidget(scroll_area)
        
        # 按钮组
        button_layout = self._create_button_layout()
        main_layout.addLayout(button_layout)
        
    def _create_basic_info_group(self) -> QGroupBox:
        """创建基本信息组。
        
        Returns:
            QGroupBox: 基本信息组件
        """
        group = QGroupBox("基本信息")
        layout = QFormLayout()
        
        # 任务名称
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("请输入任务名称")
        layout.addRow("任务名称*:", self.name_edit)
        
        # 任务描述
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("请输入任务描述")
        self.description_edit.setMaximumHeight(80)
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
        
        group.setLayout(layout)
        return group
        
    def _create_task_config_group(self) -> QGroupBox:
        """创建任务配置组。
        
        Returns:
            QGroupBox: 任务配置组件
        """
        group = QGroupBox("任务配置")
        layout = QFormLayout()
        
        # 重试次数
        self.retry_count_spin = QSpinBox()
        self.retry_count_spin.setRange(0, 10)
        self.retry_count_spin.setValue(3)
        layout.addRow("重试次数:", self.retry_count_spin)
        
        # 超时时间（秒）
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(1, 3600)
        self.timeout_spin.setValue(300)
        self.timeout_spin.setSuffix(" 秒")
        layout.addRow("超时时间:", self.timeout_spin)
        
        # 依赖任务
        self.dependencies_edit = QLineEdit()
        self.dependencies_edit.setPlaceholderText("任务ID，多个用逗号分隔")
        layout.addRow("依赖任务:", self.dependencies_edit)
        
        # 任务参数
        self.parameters_edit = QTextEdit()
        self.parameters_edit.setPlaceholderText("JSON格式的任务参数")
        self.parameters_edit.setMaximumHeight(100)
        layout.addRow("任务参数:", self.parameters_edit)
        
        group.setLayout(layout)
        return group
        
    def _create_advanced_settings_group(self) -> QGroupBox:
        """创建高级设置组。
        
        Returns:
            QGroupBox: 高级设置组件
        """
        group = QGroupBox("高级设置")
        layout = QFormLayout()
        
        # 计划执行时间
        self.scheduled_time_edit = QDateTimeEdit()
        self.scheduled_time_edit.setDateTime(QDateTime.currentDateTime())
        self.scheduled_time_edit.setCalendarPopup(True)
        layout.addRow("计划执行时间:", self.scheduled_time_edit)
        
        # 是否启用
        self.enabled_checkbox = QCheckBox()
        self.enabled_checkbox.setChecked(True)
        layout.addRow("启用任务:", self.enabled_checkbox)
        
        # 是否自动重试
        self.auto_retry_checkbox = QCheckBox()
        self.auto_retry_checkbox.setChecked(True)
        layout.addRow("自动重试:", self.auto_retry_checkbox)
        
        # 最大并发数
        self.max_concurrent_spin = QSpinBox()
        self.max_concurrent_spin.setRange(1, 10)
        self.max_concurrent_spin.setValue(1)
        layout.addRow("最大并发数:", self.max_concurrent_spin)
        
        # 任务标签
        self.tags_edit = QLineEdit()
        self.tags_edit.setPlaceholderText("标签，多个用逗号分隔")
        layout.addRow("任务标签:", self.tags_edit)
        
        group.setLayout(layout)
        return group
        
    def _create_button_layout(self) -> QHBoxLayout:
        """创建按钮布局。
        
        Returns:
            QHBoxLayout: 按钮布局
        """
        layout = QHBoxLayout()
        
        # 左侧按钮
        self.reset_button = QPushButton("重置")
        self.load_template_button = QPushButton("加载模板")
        self.save_template_button = QPushButton("保存模板")
        
        layout.addWidget(self.reset_button)
        layout.addWidget(self.load_template_button)
        layout.addWidget(self.save_template_button)
        layout.addStretch()
        
        # 右侧按钮
        self.cancel_button = QPushButton("取消")
        self.save_button = QPushButton("保存")
        self.create_button = QPushButton("创建")
        
        self.cancel_button.setMinimumWidth(80)
        self.save_button.setMinimumWidth(80)
        self.create_button.setMinimumWidth(80)
        
        layout.addWidget(self.cancel_button)
        layout.addWidget(self.save_button)
        layout.addWidget(self.create_button)
        
        return layout
        
    def _connect_signals(self):
        """连接信号槽。"""
        self.reset_button.clicked.connect(self._reset_form)
        self.load_template_button.clicked.connect(self._load_template)
        self.save_template_button.clicked.connect(self._save_template)
        self.cancel_button.clicked.connect(self.cancelled.emit)
        self.save_button.clicked.connect(self._save_task)
        self.create_button.clicked.connect(self._create_task)
        
        # 表单验证
        self.name_edit.textChanged.connect(self._validate_form)
        self.type_combo.currentTextChanged.connect(self._validate_form)
        
    def _validate_form(self):
        """验证表单。"""
        is_valid = bool(self.name_edit.text().strip())
        
        self.save_button.setEnabled(is_valid)
        self.create_button.setEnabled(is_valid)
        
    def _reset_form(self):
        """重置表单。"""
        self.name_edit.clear()
        self.description_edit.clear()
        self.type_combo.setCurrentIndex(0)
        self.priority_combo.setCurrentText(TaskPriority.MEDIUM.value)
        self.retry_count_spin.setValue(3)
        self.timeout_spin.setValue(300)
        self.dependencies_edit.clear()
        self.parameters_edit.clear()
        self.scheduled_time_edit.setDateTime(QDateTime.currentDateTime())
        self.enabled_checkbox.setChecked(True)
        self.auto_retry_checkbox.setChecked(True)
        self.max_concurrent_spin.setValue(1)
        self.tags_edit.clear()
        
    def _load_template(self):
        """加载任务模板。"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "加载任务模板", "", "JSON文件 (*.json)"
        )
        
        if file_path:
            try:
                import json
                with open(file_path, 'r', encoding='utf-8') as f:
                    template = json.load(f)
                    
                self._load_from_dict(template)
                QMessageBox.information(self, "成功", "模板加载成功")
                
            except Exception as e:
                QMessageBox.warning(self, "错误", f"加载模板失败: {e}")
                
    def _save_template(self):
        """保存任务模板。"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存任务模板", "", "JSON文件 (*.json)"
        )
        
        if file_path:
            try:
                import json
                template = self._get_form_data()
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(template, f, ensure_ascii=False, indent=2)
                    
                QMessageBox.information(self, "成功", "模板保存成功")
                
            except Exception as e:
                QMessageBox.warning(self, "错误", f"保存模板失败: {e}")
                
    def _save_task(self):
        """保存任务。"""
        if not self._validate_required_fields():
            return
            
        try:
            task_config = self._create_task_config()
            
            if self.is_edit_mode:
                self.taskUpdated.emit(task_config)
            else:
                # 保存为草稿
                pass
                
            QMessageBox.information(self, "成功", "任务保存成功")
            
        except Exception as e:
            QMessageBox.warning(self, "错误", f"保存任务失败: {e}")
            
    def _create_task(self):
        """创建任务。"""
        if not self._validate_required_fields():
            return
            
        try:
            task_config = self._create_task_config()
            self.taskCreated.emit(task_config)
            
            QMessageBox.information(self, "成功", "任务创建成功")
            self._reset_form()
            
        except Exception as e:
            QMessageBox.warning(self, "错误", f"创建任务失败: {e}")
            
    def _validate_required_fields(self) -> bool:
        """验证必填字段。
        
        Returns:
            bool: 是否验证通过
        """
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "验证失败", "请输入任务名称")
            self.name_edit.setFocus()
            return False
            
        return True
        
    def _create_task_config(self) -> TaskConfig:
        """创建任务配置。
        
        Returns:
            TaskConfig: 任务配置对象
        """
        import json
        
        # 解析依赖任务
        dependencies = []
        if self.dependencies_edit.text().strip():
            dependencies = [dep.strip() for dep in self.dependencies_edit.text().split(',')]
            
        # 解析任务参数
        parameters = {}
        if self.parameters_edit.toPlainText().strip():
            try:
                parameters = json.loads(self.parameters_edit.toPlainText())
            except json.JSONDecodeError:
                raise ValueError("任务参数格式错误，请使用有效的JSON格式")
                
        # 解析标签
        tags = []
        if self.tags_edit.text().strip():
            tags = [tag.strip() for tag in self.tags_edit.text().split(',')]
            
        task_config = TaskConfig(
            task_id=self.current_task_config.task_id if self.current_task_config else None,
            name=self.name_edit.text().strip(),
            description=self.description_edit.toPlainText().strip(),
            task_type=self.type_combo.currentData(),
            priority=self.priority_combo.currentData(),
            retry_count=self.retry_count_spin.value(),
            timeout=self.timeout_spin.value(),
            dependencies=dependencies,
            parameters=parameters,
            scheduled_time=self.scheduled_time_edit.dateTime().toPyDateTime(),
            enabled=self.enabled_checkbox.isChecked(),
            auto_retry=self.auto_retry_checkbox.isChecked(),
            max_concurrent=self.max_concurrent_spin.value(),
            tags=tags
        )
        
        return task_config
        
    def _get_form_data(self) -> Dict[str, Any]:
        """获取表单数据。
        
        Returns:
            Dict[str, Any]: 表单数据字典
        """
        import json
        
        # 解析依赖任务
        dependencies = []
        if self.dependencies_edit.text().strip():
            dependencies = [dep.strip() for dep in self.dependencies_edit.text().split(',')]
            
        # 解析任务参数
        parameters = {}
        if self.parameters_edit.toPlainText().strip():
            try:
                parameters = json.loads(self.parameters_edit.toPlainText())
            except json.JSONDecodeError:
                parameters = {}
                
        # 解析标签
        tags = []
        if self.tags_edit.text().strip():
            tags = [tag.strip() for tag in self.tags_edit.text().split(',')]
            
        return {
            'name': self.name_edit.text().strip(),
            'description': self.description_edit.toPlainText().strip(),
            'task_type': self.type_combo.currentData().value if self.type_combo.currentData() else '',
            'priority': self.priority_combo.currentData().value if self.priority_combo.currentData() else '',
            'retry_count': self.retry_count_spin.value(),
            'timeout': self.timeout_spin.value(),
            'dependencies': dependencies,
            'parameters': parameters,
            'scheduled_time': self.scheduled_time_edit.dateTime().toString(),
            'enabled': self.enabled_checkbox.isChecked(),
            'auto_retry': self.auto_retry_checkbox.isChecked(),
            'max_concurrent': self.max_concurrent_spin.value(),
            'tags': tags
        }
        
    def _load_from_dict(self, data: Dict[str, Any]):
        """从字典加载数据。
        
        Args:
            data: 数据字典
        """
        self.name_edit.setText(data.get('name', ''))
        self.description_edit.setPlainText(data.get('description', ''))
        
        # 设置任务类型
        task_type_value = data.get('task_type', '')
        for i in range(self.type_combo.count()):
            if self.type_combo.itemData(i).value == task_type_value:
                self.type_combo.setCurrentIndex(i)
                break
                
        # 设置优先级
        priority_value = data.get('priority', '')
        for i in range(self.priority_combo.count()):
            if self.priority_combo.itemData(i).value == priority_value:
                self.priority_combo.setCurrentIndex(i)
                break
                
        self.retry_count_spin.setValue(data.get('retry_count', 3))
        self.timeout_spin.setValue(data.get('timeout', 300))
        
        dependencies = data.get('dependencies', [])
        self.dependencies_edit.setText(', '.join(dependencies))
        
        parameters = data.get('parameters', {})
        if parameters:
            import json
            self.parameters_edit.setPlainText(json.dumps(parameters, ensure_ascii=False, indent=2))
            
        scheduled_time = data.get('scheduled_time', '')
        if scheduled_time:
            self.scheduled_time_edit.setDateTime(QDateTime.fromString(scheduled_time))
            
        self.enabled_checkbox.setChecked(data.get('enabled', True))
        self.auto_retry_checkbox.setChecked(data.get('auto_retry', True))
        self.max_concurrent_spin.setValue(data.get('max_concurrent', 1))
        
        tags = data.get('tags', [])
        self.tags_edit.setText(', '.join(tags))
        
    def set_edit_mode(self, task_config: TaskConfig):
        """设置编辑模式。
        
        Args:
            task_config: 要编辑的任务配置
        """
        self.is_edit_mode = True
        self.current_task_config = task_config
        
        self.title_label.setText("编辑任务")
        self.setWindowTitle("编辑任务")
        self.create_button.setText("更新")
        
        # 加载任务数据
        self._load_task_config(task_config)
        
    def set_create_mode(self):
        """设置创建模式。"""
        self.is_edit_mode = False
        self.current_task_config = None
        
        self.title_label.setText("创建新任务")
        self.setWindowTitle("创建任务")
        self.create_button.setText("创建")
        
        self._reset_form()
        
    def _load_task_config(self, task_config: TaskConfig):
        """加载任务配置。
        
        Args:
            task_config: 任务配置
        """
        self.name_edit.setText(task_config.name or '')
        self.description_edit.setPlainText(task_config.description or '')
        
        # 设置任务类型
        for i in range(self.type_combo.count()):
            if self.type_combo.itemData(i) == task_config.task_type:
                self.type_combo.setCurrentIndex(i)
                break
                
        # 设置优先级
        for i in range(self.priority_combo.count()):
            if self.priority_combo.itemData(i) == task_config.priority:
                self.priority_combo.setCurrentIndex(i)
                break
                
        self.retry_count_spin.setValue(task_config.retry_count or 3)
        self.timeout_spin.setValue(task_config.timeout or 300)
        
        if task_config.dependencies:
            self.dependencies_edit.setText(', '.join(task_config.dependencies))
            
        if task_config.parameters:
            import json
            self.parameters_edit.setPlainText(
                json.dumps(task_config.parameters, ensure_ascii=False, indent=2)
            )
            
        if task_config.scheduled_time:
            self.scheduled_time_edit.setDateTime(
                QDateTime.fromSecsSinceEpoch(int(task_config.scheduled_time.timestamp()))
            )
            
        self.enabled_checkbox.setChecked(getattr(task_config, 'enabled', True))
        self.auto_retry_checkbox.setChecked(getattr(task_config, 'auto_retry', True))
        self.max_concurrent_spin.setValue(getattr(task_config, 'max_concurrent', 1))
        
        if hasattr(task_config, 'tags') and task_config.tags:
            self.tags_edit.setText(', '.join(task_config.tags))
            
    def get_task_config(self) -> Optional[TaskConfig]:
        """获取当前的任务配置。
        
        Returns:
            Optional[TaskConfig]: 任务配置对象
        """
        if not self._validate_required_fields():
            return None
            
        try:
            return self._create_task_config()
        except Exception as e:
            QMessageBox.warning(self, "错误", f"获取任务配置失败: {e}")
            return None
