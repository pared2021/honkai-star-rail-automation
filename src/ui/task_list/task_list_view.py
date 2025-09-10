"""任务列表视图模块.

用于实现任务列表界面的视图组件。
"""

from typing import Optional, List
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableView, QPushButton, 
    QLabel, QComboBox, QLineEdit, QHeaderView, QMenu, QMessageBox,
    QProgressBar, QSplitter, QTextEdit, QGroupBox
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QIcon

from .task_list_model import TaskListModel
from ...core.enhanced_task_executor import TaskExecution, TaskStatus, TaskType, TaskPriority


class TaskListView(QWidget):
    """任务列表视图组件。"""
    
    # 信号定义
    taskSelected = pyqtSignal(str)  # 任务选中信号
    taskStartRequested = pyqtSignal(str)  # 开始任务信号
    taskPauseRequested = pyqtSignal(str)  # 暂停任务信号
    taskStopRequested = pyqtSignal(str)   # 停止任务信号
    taskDeleteRequested = pyqtSignal(str) # 删除任务信号
    taskEditRequested = pyqtSignal(str)   # 编辑任务信号
    createTaskRequested = pyqtSignal()    # 创建任务信号
    
    def __init__(self, parent=None):
        """初始化任务列表视图。"""
        super().__init__(parent)
        self.model = TaskListModel(self)
        self._setup_ui()
        self._connect_signals()
        self._setup_refresh_timer()
        
    def _setup_ui(self):
        """设置用户界面。"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # 标题和工具栏
        self._setup_header(layout)
        
        # 过滤器
        self._setup_filters(layout)
        
        # 主要内容区域
        self._setup_main_content(layout)
        
        # 状态栏
        self._setup_status_bar(layout)
        
    def _setup_header(self, layout):
        """设置标题和工具栏。"""
        header_layout = QHBoxLayout()
        
        # 标题
        title_label = QLabel("任务管理")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # 工具按钮
        self.create_task_btn = QPushButton("创建任务")
        self.create_task_btn.setMinimumSize(100, 30)
        header_layout.addWidget(self.create_task_btn)
        
        self.refresh_btn = QPushButton("刷新")
        self.refresh_btn.setMinimumSize(80, 30)
        header_layout.addWidget(self.refresh_btn)
        
        layout.addLayout(header_layout)
        
    def _setup_filters(self, layout):
        """设置过滤器。"""
        filter_group = QGroupBox("过滤器")
        filter_layout = QHBoxLayout(filter_group)
        
        # 状态过滤
        filter_layout.addWidget(QLabel("状态:"))
        self.status_filter = QComboBox()
        self.status_filter.addItem("全部", None)
        for status in TaskStatus:
            self.status_filter.addItem(status.value, status)
        filter_layout.addWidget(self.status_filter)
        
        # 类型过滤
        filter_layout.addWidget(QLabel("类型:"))
        self.type_filter = QComboBox()
        self.type_filter.addItem("全部", None)
        for task_type in TaskType:
            self.type_filter.addItem(task_type.value, task_type)
        filter_layout.addWidget(self.type_filter)
        
        # 搜索框
        filter_layout.addWidget(QLabel("搜索:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("输入任务名称...")
        filter_layout.addWidget(self.search_edit)
        
        filter_layout.addStretch()
        
        layout.addWidget(filter_group)
        
    def _setup_main_content(self, layout):
        """设置主要内容区域。"""
        splitter = QSplitter(Qt.Vertical)
        
        # 任务列表表格
        self.task_table = QTableView()
        self.task_table.setModel(self.model)
        self.task_table.setSelectionBehavior(QTableView.SelectRows)
        self.task_table.setAlternatingRowColors(True)
        self.task_table.setSortingEnabled(True)
        
        # 设置列宽
        header = self.task_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.resizeSection(0, 200)  # 任务名称
        header.resizeSection(1, 100)  # 类型
        header.resizeSection(2, 80)   # 状态
        header.resizeSection(3, 80)   # 优先级
        header.resizeSection(4, 80)   # 进度
        header.resizeSection(5, 150)  # 创建时间
        
        # 设置右键菜单
        self.task_table.setContextMenuPolicy(Qt.CustomContextMenu)
        
        splitter.addWidget(self.task_table)
        
        # 任务详情面板
        self._setup_detail_panel(splitter)
        
        splitter.setSizes([400, 200])
        layout.addWidget(splitter)
        
    def _setup_detail_panel(self, splitter):
        """设置任务详情面板。"""
        detail_group = QGroupBox("任务详情")
        detail_layout = QVBoxLayout(detail_group)
        
        # 任务信息
        info_layout = QHBoxLayout()
        
        # 基本信息
        basic_info_layout = QVBoxLayout()
        self.task_name_label = QLabel("任务名称: -")
        self.task_type_label = QLabel("任务类型: -")
        self.task_status_label = QLabel("任务状态: -")
        self.task_priority_label = QLabel("优先级: -")
        
        basic_info_layout.addWidget(self.task_name_label)
        basic_info_layout.addWidget(self.task_type_label)
        basic_info_layout.addWidget(self.task_status_label)
        basic_info_layout.addWidget(self.task_priority_label)
        
        info_layout.addLayout(basic_info_layout)
        
        # 进度信息
        progress_layout = QVBoxLayout()
        self.progress_label = QLabel("进度: 0%")
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.execution_time_label = QLabel("执行时间: -")
        
        progress_layout.addWidget(self.progress_label)
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.execution_time_label)
        
        info_layout.addLayout(progress_layout)
        
        detail_layout.addLayout(info_layout)
        
        # 控制按钮
        button_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("开始")
        self.pause_btn = QPushButton("暂停")
        self.stop_btn = QPushButton("停止")
        self.edit_btn = QPushButton("编辑")
        self.delete_btn = QPushButton("删除")
        
        button_layout.addWidget(self.start_btn)
        button_layout.addWidget(self.pause_btn)
        button_layout.addWidget(self.stop_btn)
        button_layout.addWidget(self.edit_btn)
        button_layout.addWidget(self.delete_btn)
        button_layout.addStretch()
        
        detail_layout.addLayout(button_layout)
        
        # 任务描述
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(100)
        self.description_edit.setReadOnly(True)
        detail_layout.addWidget(QLabel("任务描述:"))
        detail_layout.addWidget(self.description_edit)
        
        splitter.addWidget(detail_group)
        
    def _setup_status_bar(self, layout):
        """设置状态栏。"""
        status_layout = QHBoxLayout()
        
        self.total_tasks_label = QLabel("总任务: 0")
        self.running_tasks_label = QLabel("运行中: 0")
        self.completed_tasks_label = QLabel("已完成: 0")
        self.failed_tasks_label = QLabel("失败: 0")
        
        status_layout.addWidget(self.total_tasks_label)
        status_layout.addWidget(QLabel("|"))
        status_layout.addWidget(self.running_tasks_label)
        status_layout.addWidget(QLabel("|"))
        status_layout.addWidget(self.completed_tasks_label)
        status_layout.addWidget(QLabel("|"))
        status_layout.addWidget(self.failed_tasks_label)
        status_layout.addStretch()
        
        layout.addLayout(status_layout)
        
    def _connect_signals(self):
        """连接信号。"""
        # 表格选择
        self.task_table.selectionModel().currentRowChanged.connect(self._on_task_selected)
        
        # 右键菜单
        self.task_table.customContextMenuRequested.connect(self._show_context_menu)
        
        # 按钮点击
        self.create_task_btn.clicked.connect(self.createTaskRequested.emit)
        self.refresh_btn.clicked.connect(self._refresh_tasks)
        self.start_btn.clicked.connect(self._start_selected_task)
        self.pause_btn.clicked.connect(self._pause_selected_task)
        self.stop_btn.clicked.connect(self._stop_selected_task)
        self.edit_btn.clicked.connect(self._edit_selected_task)
        self.delete_btn.clicked.connect(self._delete_selected_task)
        
        # 过滤器
        self.status_filter.currentTextChanged.connect(self._apply_filters)
        self.type_filter.currentTextChanged.connect(self._apply_filters)
        self.search_edit.textChanged.connect(self._apply_filters)
        
        # 模型信号
        self.model.taskUpdated.connect(self._update_status_bar)
        self.model.taskAdded.connect(self._update_status_bar)
        self.model.taskRemoved.connect(self._update_status_bar)
        
    def _setup_refresh_timer(self):
        """设置刷新定时器。"""
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self._update_status_bar)
        self.refresh_timer.start(1000)  # 每秒更新一次
        
    def _on_task_selected(self, current, previous):
        """任务选择事件。"""
        if current.isValid():
            task = self.model.data(current, Qt.UserRole)
            if task:
                self._update_detail_panel(task)
                self.taskSelected.emit(task.task_id)
        else:
            self._clear_detail_panel()
            
    def _update_detail_panel(self, task: TaskExecution):
        """更新详情面板。"""
        self.task_name_label.setText(f"任务名称: {task.task_config.name}")
        self.task_type_label.setText(f"任务类型: {task.task_config.task_type.value}")
        self.task_status_label.setText(f"任务状态: {task.status.value}")
        self.task_priority_label.setText(f"优先级: {task.task_config.priority.value}")
        
        progress = int(task.progress * 100)
        self.progress_label.setText(f"进度: {progress}%")
        self.progress_bar.setValue(progress)
        
        if task.execution_time > 0:
            self.execution_time_label.setText(f"执行时间: {task.execution_time:.2f}s")
        else:
            self.execution_time_label.setText("执行时间: -")
            
        self.description_edit.setText(task.task_config.description)
        
        # 更新按钮状态
        self._update_button_states(task)
        
    def _update_button_states(self, task: TaskExecution):
        """更新按钮状态。"""
        is_running = task.status == TaskStatus.RUNNING
        is_paused = task.status == TaskStatus.PAUSED
        is_completed = task.is_completed
        
        self.start_btn.setEnabled(not is_running and not is_completed)
        self.pause_btn.setEnabled(is_running)
        self.stop_btn.setEnabled(is_running or is_paused)
        self.edit_btn.setEnabled(not is_running)
        self.delete_btn.setEnabled(not is_running)
        
    def _clear_detail_panel(self):
        """清空详情面板。"""
        self.task_name_label.setText("任务名称: -")
        self.task_type_label.setText("任务类型: -")
        self.task_status_label.setText("任务状态: -")
        self.task_priority_label.setText("优先级: -")
        self.progress_label.setText("进度: 0%")
        self.progress_bar.setValue(0)
        self.execution_time_label.setText("执行时间: -")
        self.description_edit.clear()
        
        # 禁用所有按钮
        self.start_btn.setEnabled(False)
        self.pause_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
        self.edit_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)
        
    def _show_context_menu(self, position):
        """显示右键菜单。"""
        index = self.task_table.indexAt(position)
        if not index.isValid():
            return
            
        task = self.model.data(index, Qt.UserRole)
        if not task:
            return
            
        menu = QMenu(self)
        
        # 根据任务状态添加菜单项
        if task.status != TaskStatus.RUNNING and not task.is_completed:
            start_action = menu.addAction("开始任务")
            start_action.triggered.connect(lambda: self.taskStartRequested.emit(task.task_id))
            
        if task.status == TaskStatus.RUNNING:
            pause_action = menu.addAction("暂停任务")
            pause_action.triggered.connect(lambda: self.taskPauseRequested.emit(task.task_id))
            
        if task.status in [TaskStatus.RUNNING, TaskStatus.PAUSED]:
            stop_action = menu.addAction("停止任务")
            stop_action.triggered.connect(lambda: self.taskStopRequested.emit(task.task_id))
            
        if task.status != TaskStatus.RUNNING:
            menu.addSeparator()
            edit_action = menu.addAction("编辑任务")
            edit_action.triggered.connect(lambda: self.taskEditRequested.emit(task.task_id))
            
            delete_action = menu.addAction("删除任务")
            delete_action.triggered.connect(lambda: self._confirm_delete_task(task.task_id))
            
        menu.exec_(self.task_table.mapToGlobal(position))
        
    def _start_selected_task(self):
        """开始选中的任务。"""
        current_index = self.task_table.currentIndex()
        if current_index.isValid():
            task = self.model.data(current_index, Qt.UserRole)
            if task:
                self.taskStartRequested.emit(task.task_id)
                
    def _pause_selected_task(self):
        """暂停选中的任务。"""
        current_index = self.task_table.currentIndex()
        if current_index.isValid():
            task = self.model.data(current_index, Qt.UserRole)
            if task:
                self.taskPauseRequested.emit(task.task_id)
                
    def _stop_selected_task(self):
        """停止选中的任务。"""
        current_index = self.task_table.currentIndex()
        if current_index.isValid():
            task = self.model.data(current_index, Qt.UserRole)
            if task:
                self.taskStopRequested.emit(task.task_id)
                
    def _edit_selected_task(self):
        """编辑选中的任务。"""
        current_index = self.task_table.currentIndex()
        if current_index.isValid():
            task = self.model.data(current_index, Qt.UserRole)
            if task:
                self.taskEditRequested.emit(task.task_id)
                
    def _delete_selected_task(self):
        """删除选中的任务。"""
        current_index = self.task_table.currentIndex()
        if current_index.isValid():
            task = self.model.data(current_index, Qt.UserRole)
            if task:
                self._confirm_delete_task(task.task_id)
                
    def _confirm_delete_task(self, task_id: str):
        """确认删除任务。"""
        reply = QMessageBox.question(
            self, "确认删除", 
            "确定要删除这个任务吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.taskDeleteRequested.emit(task_id)
            
    def _refresh_tasks(self):
        """刷新任务列表。"""
        # 这里可以添加从后端重新加载任务的逻辑
        self._update_status_bar()
        
    def _apply_filters(self):
        """应用过滤器。"""
        # TODO: 实现过滤逻辑
        pass
        
    def _update_status_bar(self):
        """更新状态栏。"""
        all_tasks = self.model.getAllTasks()
        total = len(all_tasks)
        
        running = len([t for t in all_tasks if t.status == TaskStatus.RUNNING])
        completed = len([t for t in all_tasks if t.status == TaskStatus.COMPLETED])
        failed = len([t for t in all_tasks if t.status == TaskStatus.FAILED])
        
        self.total_tasks_label.setText(f"总任务: {total}")
        self.running_tasks_label.setText(f"运行中: {running}")
        self.completed_tasks_label.setText(f"已完成: {completed}")
        self.failed_tasks_label.setText(f"失败: {failed}")
        
    # 公共接口方法
    def addTask(self, task_execution: TaskExecution):
        """添加任务到列表。"""
        self.model.addTask(task_execution)
        
    def updateTask(self, task_execution: TaskExecution):
        """更新任务信息。"""
        self.model.updateTask(task_execution)
        
    def removeTask(self, task_id: str):
        """从列表移除任务。"""
        self.model.removeTask(task_id)
        
    def getSelectedTask(self) -> Optional[TaskExecution]:
        """获取当前选中的任务。"""
        current_index = self.task_table.currentIndex()
        if current_index.isValid():
            return self.model.data(current_index, Qt.UserRole)
        return None
        
    def clearTasks(self):
        """清空任务列表。"""
        self.model.clearTasks()
