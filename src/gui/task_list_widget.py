# -*- coding: utf-8 -*-
"""
任务列表显示界面组件
"""

from typing import Optional, List, Dict, Any
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QPushButton, QLabel, QComboBox, QLineEdit, QGroupBox,
    QMessageBox, QMenu, QFrame, QSplitter, QTextEdit, QProgressBar,
    QCheckBox, QDateEdit, QSpinBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QDate, QThread, pyqtSlot
from PyQt6.QtGui import QFont, QColor, QBrush, QAction, QIcon

from loguru import logger
from ..core.task_manager import TaskManager, TaskType, TaskPriority, Task
from ..automation.automation_controller import TaskStatus


class TaskListWidget(QWidget):
    """任务列表显示界面组件"""
    
    # 信号定义
    task_selected = pyqtSignal(str)  # 任务选择信号，传递任务ID
    task_edit_requested = pyqtSignal(str)  # 任务编辑请求信号
    task_delete_requested = pyqtSignal(str)  # 任务删除请求信号
    task_start_requested = pyqtSignal(str)  # 任务启动请求信号
    task_stop_requested = pyqtSignal(str)  # 任务停止请求信号
    
    def __init__(self, task_manager: TaskManager, parent=None):
        """初始化任务列表界面
        
        Args:
            task_manager: 任务管理器实例
            parent: 父组件
        """
        super().__init__(parent)
        
        self.task_manager = task_manager
        
        # 当前任务列表
        self.current_tasks: List[Task] = []
        self.selected_task_id: Optional[str] = None
        
        # 过滤条件
        self.filter_status: Optional[TaskStatus] = None
        self.filter_type: Optional[TaskType] = None
        self.filter_priority: Optional[TaskPriority] = None
        self.filter_text: str = ""
        
        # 初始化UI
        self._init_ui()
        self._connect_signals()
        
        # 自动刷新定时器
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_task_list)
        self.refresh_timer.start(5000)  # 每5秒刷新一次
        
        # 初始加载任务列表
        self.refresh_task_list()
        
        logger.info("任务列表界面初始化完成")
    
    def _init_ui(self):
        """初始化用户界面"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # 标题
        title_label = QLabel("任务列表")
        title_label.setFont(QFont("Microsoft YaHei", 16, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)
        
        # 创建分割器
        splitter = QSplitter(Qt.Orientation.Vertical)
        main_layout.addWidget(splitter)
        
        # 上半部分：过滤和操作区域
        top_widget = self._create_top_widget()
        splitter.addWidget(top_widget)
        
        # 下半部分：任务列表和详情
        bottom_widget = self._create_bottom_widget()
        splitter.addWidget(bottom_widget)
        
        # 设置分割器比例
        splitter.setSizes([150, 500])
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
    
    def _create_top_widget(self) -> QWidget:
        """创建顶部过滤和操作区域"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(10)
        
        # 过滤组
        filter_group = QGroupBox("过滤条件")
        filter_layout = QHBoxLayout(filter_group)
        
        # 状态过滤
        filter_layout.addWidget(QLabel("状态:"))
        self.status_filter_combo = QComboBox()
        self.status_filter_combo.addItem("全部", None)
        for status in TaskStatus:
            self.status_filter_combo.addItem(status.value, status)
        self.status_filter_combo.currentTextChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self.status_filter_combo)
        
        # 类型过滤
        filter_layout.addWidget(QLabel("类型:"))
        self.type_filter_combo = QComboBox()
        self.type_filter_combo.addItem("全部", None)
        for task_type in TaskType:
            self.type_filter_combo.addItem(task_type.value, task_type)
        self.type_filter_combo.currentTextChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self.type_filter_combo)
        
        # 优先级过滤
        filter_layout.addWidget(QLabel("优先级:"))
        self.priority_filter_combo = QComboBox()
        self.priority_filter_combo.addItem("全部", None)
        for priority in TaskPriority:
            self.priority_filter_combo.addItem(priority.value, priority)
        self.priority_filter_combo.currentTextChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self.priority_filter_combo)
        
        # 文本搜索
        filter_layout.addWidget(QLabel("搜索:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("输入任务名称或描述")
        self.search_edit.textChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self.search_edit)
        
        # 清除过滤按钮
        self.clear_filter_btn = QPushButton("清除过滤")
        self.clear_filter_btn.clicked.connect(self._clear_filters)
        filter_layout.addWidget(self.clear_filter_btn)
        
        filter_layout.addStretch()
        layout.addWidget(filter_group)
        
        # 操作按钮组
        action_group = QGroupBox("操作")
        action_layout = QHBoxLayout(action_group)
        
        # 刷新按钮
        self.refresh_btn = QPushButton("刷新")
        self.refresh_btn.clicked.connect(self.refresh_task_list)
        action_layout.addWidget(self.refresh_btn)
        
        # 启动任务按钮
        self.start_task_btn = QPushButton("启动任务")
        self.start_task_btn.setEnabled(False)
        self.start_task_btn.clicked.connect(self._start_selected_task)
        action_layout.addWidget(self.start_task_btn)
        
        # 停止任务按钮
        self.stop_task_btn = QPushButton("停止任务")
        self.stop_task_btn.setEnabled(False)
        self.stop_task_btn.clicked.connect(self._stop_selected_task)
        action_layout.addWidget(self.stop_task_btn)
        
        # 编辑任务按钮
        self.edit_task_btn = QPushButton("编辑任务")
        self.edit_task_btn.setEnabled(False)
        self.edit_task_btn.clicked.connect(self._edit_selected_task)
        action_layout.addWidget(self.edit_task_btn)
        
        # 删除任务按钮
        self.delete_task_btn = QPushButton("删除任务")
        self.delete_task_btn.setEnabled(False)
        self.delete_task_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.delete_task_btn.clicked.connect(self._delete_selected_task)
        action_layout.addWidget(self.delete_task_btn)
        
        action_layout.addStretch()
        layout.addWidget(action_group)
        
        return widget
    
    def _create_bottom_widget(self) -> QWidget:
        """创建底部任务列表和详情区域"""
        # 创建分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧：任务列表
        list_widget = self._create_task_list_widget()
        splitter.addWidget(list_widget)
        
        # 右侧：任务详情
        detail_widget = self._create_task_detail_widget()
        splitter.addWidget(detail_widget)
        
        # 设置分割器比例
        splitter.setSizes([600, 400])
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 0)
        
        return splitter
    
    def _create_task_list_widget(self) -> QWidget:
        """创建任务列表组件"""
        widget = QGroupBox("任务列表")
        layout = QVBoxLayout(widget)
        
        # 任务表格
        self.task_table = QTableWidget()
        self.task_table.setColumnCount(7)
        self.task_table.setHorizontalHeaderLabels([
            "任务名称", "类型", "优先级", "状态", "创建时间", "最后执行", "进度"
        ])
        
        # 设置表格属性
        self.task_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.task_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.task_table.setAlternatingRowColors(True)
        self.task_table.setSortingEnabled(True)
        
        # 设置列宽
        header = self.task_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # 任务名称
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # 类型
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # 优先级
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # 状态
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # 创建时间
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # 最后执行
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)  # 进度
        self.task_table.setColumnWidth(6, 100)
        
        # 连接信号
        self.task_table.itemSelectionChanged.connect(self._on_task_selection_changed)
        self.task_table.itemDoubleClicked.connect(self._on_task_double_clicked)
        
        # 设置右键菜单
        self.task_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.task_table.customContextMenuRequested.connect(self._show_context_menu)
        
        layout.addWidget(self.task_table)
        
        # 统计信息
        self.stats_label = QLabel("总计: 0 个任务")
        self.stats_label.setStyleSheet("color: #666; font-size: 12px;")
        layout.addWidget(self.stats_label)
        
        return widget
    
    def _create_task_detail_widget(self) -> QWidget:
        """创建任务详情组件"""
        widget = QGroupBox("任务详情")
        layout = QVBoxLayout(widget)
        
        # 详情文本区域
        self.detail_text = QTextEdit()
        self.detail_text.setReadOnly(True)
        self.detail_text.setStyleSheet("""
            QTextEdit {
                background-color: #f9f9f9;
                border: 1px solid #ddd;
                border-radius: 3px;
                padding: 10px;
                font-family: 'Microsoft YaHei', sans-serif;
                font-size: 12px;
                line-height: 1.4;
            }
        """)
        layout.addWidget(self.detail_text)
        
        # 默认显示提示信息
        self._show_no_selection_message()
        
        return widget
    
    def _connect_signals(self):
        """连接信号和槽"""
        pass
    
    def _on_filter_changed(self):
        """过滤条件变化"""
        # 更新过滤条件
        self.filter_status = self.status_filter_combo.currentData()
        self.filter_type = self.type_filter_combo.currentData()
        self.filter_priority = self.priority_filter_combo.currentData()
        self.filter_text = self.search_edit.text().strip().lower()
        
        # 应用过滤
        self._apply_filters()
    
    def _clear_filters(self):
        """清除所有过滤条件"""
        self.status_filter_combo.setCurrentIndex(0)
        self.type_filter_combo.setCurrentIndex(0)
        self.priority_filter_combo.setCurrentIndex(0)
        self.search_edit.clear()
        
        # 重置过滤条件
        self.filter_status = None
        self.filter_type = None
        self.filter_priority = None
        self.filter_text = ""
        
        # 刷新列表
        self.refresh_task_list()
    
    def _apply_filters(self):
        """应用过滤条件"""
        filtered_tasks = []
        
        for task in self.current_tasks:
            # 状态过滤
            if self.filter_status and task.status != self.filter_status:
                continue
            
            # 类型过滤
            if self.filter_type and task.config.task_type != self.filter_type:
                continue
            
            # 优先级过滤
            if self.filter_priority and task.config.priority != self.filter_priority:
                continue
            
            # 文本搜索
            if self.filter_text:
                search_text = f"{task.config.name} {task.config.description or ''}".lower()
                if self.filter_text not in search_text:
                    continue
            
            filtered_tasks.append(task)
        
        # 更新表格显示
        self._update_task_table(filtered_tasks)
    
    def _on_task_selection_changed(self):
        """任务选择变化"""
        selected_items = self.task_table.selectedItems()
        
        if selected_items:
            row = selected_items[0].row()
            task_id_item = self.task_table.item(row, 0)
            if task_id_item:
                task_id = task_id_item.data(Qt.ItemDataRole.UserRole)
                self.selected_task_id = task_id
                
                # 更新按钮状态
                self._update_button_states()
                
                # 显示任务详情
                self._show_task_details(task_id)
                
                # 发送选择信号
                self.task_selected.emit(task_id)
        else:
            self.selected_task_id = None
            self._update_button_states()
            self._show_no_selection_message()
    
    def _on_task_double_clicked(self, item):
        """任务双击事件"""
        if self.selected_task_id:
            self.task_edit_requested.emit(self.selected_task_id)
    
    def _show_context_menu(self, position):
        """显示右键菜单"""
        if not self.selected_task_id:
            return
        
        menu = QMenu(self)
        
        # 启动任务
        start_action = QAction("启动任务", self)
        start_action.triggered.connect(self._start_selected_task)
        menu.addAction(start_action)
        
        # 停止任务
        stop_action = QAction("停止任务", self)
        stop_action.triggered.connect(self._stop_selected_task)
        menu.addAction(stop_action)
        
        menu.addSeparator()
        
        # 编辑任务
        edit_action = QAction("编辑任务", self)
        edit_action.triggered.connect(self._edit_selected_task)
        menu.addAction(edit_action)
        
        # 复制任务
        copy_action = QAction("复制任务", self)
        copy_action.triggered.connect(self._copy_selected_task)
        menu.addAction(copy_action)
        
        menu.addSeparator()
        
        # 删除任务
        delete_action = QAction("删除任务", self)
        delete_action.triggered.connect(self._delete_selected_task)
        menu.addAction(delete_action)
        
        # 显示菜单
        menu.exec(self.task_table.mapToGlobal(position))
    
    def _update_button_states(self):
        """更新按钮状态"""
        has_selection = self.selected_task_id is not None
        
        self.start_task_btn.setEnabled(has_selection)
        self.stop_task_btn.setEnabled(has_selection)
        self.edit_task_btn.setEnabled(has_selection)
        self.delete_task_btn.setEnabled(has_selection)
    
    def _start_selected_task(self):
        """启动选中的任务"""
        if self.selected_task_id:
            self.task_start_requested.emit(self.selected_task_id)
    
    def _stop_selected_task(self):
        """停止选中的任务"""
        if self.selected_task_id:
            self.task_stop_requested.emit(self.selected_task_id)
    
    def _edit_selected_task(self):
        """编辑选中的任务"""
        if self.selected_task_id:
            self.task_edit_requested.emit(self.selected_task_id)
    
    def _copy_selected_task(self):
        """复制选中的任务"""
        if self.selected_task_id:
            try:
                task = self.task_manager.get_task(self.selected_task_id)
                if task:
                    # 创建新的任务配置（复制原配置）
                    new_config = task.config
                    new_config.name = f"{task.config.name} (副本)"
                    
                    # 创建新任务
                    new_task_id = self.task_manager.create_task(
                        user_id=task.user_id,
                        config=new_config
                    )
                    
                    QMessageBox.information(self, "复制成功", f"任务复制成功！\n新任务ID: {new_task_id}")
                    
                    # 刷新列表
                    self.refresh_task_list()
                    
                    logger.info(f"任务复制成功: {self.selected_task_id} -> {new_task_id}")
                    
            except Exception as e:
                logger.error(f"任务复制失败: {e}")
                QMessageBox.critical(self, "复制失败", f"任务复制失败：{str(e)}")
    
    def _delete_selected_task(self):
        """删除选中的任务"""
        if self.selected_task_id:
            reply = QMessageBox.question(
                self, "确认删除", 
                "确定要删除选中的任务吗？此操作不可撤销。",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.task_delete_requested.emit(self.selected_task_id)
    
    def _show_task_details(self, task_id: str):
        """显示任务详情"""
        try:
            task = self.task_manager.get_task(task_id)
            if not task:
                self._show_no_selection_message()
                return
            
            # 构建详情文本
            details = []
            details.append(f"<h3>{task.config.name}</h3>")
            details.append(f"<b>任务ID:</b> {task.task_id}")
            details.append(f"<b>类型:</b> {task.config.task_type.value}")
            details.append(f"<b>优先级:</b> {task.config.priority.value}")
            details.append(f"<b>状态:</b> {task.status.value}")
            details.append(f"<b>创建时间:</b> {task.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            
            if task.started_at:
                details.append(f"<b>开始时间:</b> {task.started_at.strftime('%Y-%m-%d %H:%M:%S')}")
            
            if task.completed_at:
                details.append(f"<b>完成时间:</b> {task.completed_at.strftime('%Y-%m-%d %H:%M:%S')}")
            
            if task.config.description:
                details.append(f"<b>描述:</b><br>{task.config.description}")
            
            details.append(f"<b>最大执行时间:</b> {task.config.max_duration} 秒")
            details.append(f"<b>重试次数:</b> {task.config.retry_count}")
            details.append(f"<b>重试间隔:</b> {task.config.retry_interval} 秒")
            details.append(f"<b>安全模式:</b> {'是' if task.config.safe_mode else '否'}")
            
            if task.config.scheduled_time:
                details.append(f"<b>计划执行时间:</b> {task.config.scheduled_time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            if task.config.repeat_interval:
                details.append(f"<b>重复间隔:</b> {task.config.repeat_interval} 分钟")
            
            if task.config.actions:
                details.append(f"<b>动作数量:</b> {len(task.config.actions)}")
            
            if task.config.custom_params:
                details.append(f"<b>自定义参数:</b><br><pre>{task.config.custom_params}</pre>")
            
            # 显示详情
            detail_html = "<br>".join(details)
            self.detail_text.setHtml(detail_html)
            
        except Exception as e:
            logger.error(f"显示任务详情失败: {e}")
            self.detail_text.setPlainText(f"显示任务详情时发生错误：{str(e)}")
    
    def _show_no_selection_message(self):
        """显示无选择提示信息"""
        self.detail_text.setHtml(
            "<div style='text-align: center; color: #666; margin-top: 50px;'>"  
            "<h3>未选择任务</h3>"
            "<p>请从左侧列表中选择一个任务以查看详细信息</p>"
            "</div>"
        )
    
    def _update_task_table(self, tasks: List[Task]):
        """更新任务表格"""
        self.task_table.setRowCount(len(tasks))
        
        for row, task in enumerate(tasks):
            # 任务名称
            name_item = QTableWidgetItem(task.config.name)
            name_item.setData(Qt.ItemDataRole.UserRole, task.task_id)
            self.task_table.setItem(row, 0, name_item)
            
            # 类型
            type_item = QTableWidgetItem(task.config.task_type.value)
            self.task_table.setItem(row, 1, type_item)
            
            # 优先级
            priority_item = QTableWidgetItem(task.config.priority.value)
            # 设置优先级颜色
            if task.config.priority == TaskPriority.HIGH:
                priority_item.setBackground(QBrush(QColor(255, 200, 200)))
            elif task.config.priority == TaskPriority.LOW:
                priority_item.setBackground(QBrush(QColor(200, 255, 200)))
            self.task_table.setItem(row, 2, priority_item)
            
            # 状态
            status_item = QTableWidgetItem(task.status.value)
            # 设置状态颜色
            if task.status == TaskStatus.RUNNING:
                status_item.setBackground(QBrush(QColor(200, 255, 200)))
            elif task.status == TaskStatus.FAILED:
                status_item.setBackground(QBrush(QColor(255, 200, 200)))
            elif task.status == TaskStatus.COMPLETED:
                status_item.setBackground(QBrush(QColor(200, 200, 255)))
            self.task_table.setItem(row, 3, status_item)
            
            # 创建时间
            created_item = QTableWidgetItem(task.created_at.strftime("%m-%d %H:%M"))
            self.task_table.setItem(row, 4, created_item)
            
            # 最后执行时间
            last_run = task.started_at or task.created_at
            last_run_item = QTableWidgetItem(last_run.strftime("%m-%d %H:%M"))
            self.task_table.setItem(row, 5, last_run_item)
            
            # 进度（暂时显示状态）
            progress_item = QTableWidgetItem("100%" if task.status == TaskStatus.COMPLETED else "0%")
            self.task_table.setItem(row, 6, progress_item)
        
        # 更新统计信息
        total_count = len(tasks)
        running_count = len([t for t in tasks if t.status == TaskStatus.RUNNING])
        completed_count = len([t for t in tasks if t.status == TaskStatus.COMPLETED])
        failed_count = len([t for t in tasks if t.status == TaskStatus.FAILED])
        
        stats_text = f"总计: {total_count} 个任务 (运行中: {running_count}, 已完成: {completed_count}, 失败: {failed_count})"
        self.stats_label.setText(stats_text)
    
    @pyqtSlot()
    def refresh_task_list(self):
        """刷新任务列表"""
        try:
            # 获取所有任务
            self.current_tasks = self.task_manager.list_tasks(user_id="default_user")
            
            # 应用过滤
            self._apply_filters()
            
            logger.debug(f"任务列表已刷新，共 {len(self.current_tasks)} 个任务")
            
        except Exception as e:
            logger.error(f"刷新任务列表失败: {e}")
            QMessageBox.critical(self, "刷新失败", f"刷新任务列表失败：{str(e)}")
    
    def select_task(self, task_id: str):
        """选择指定的任务
        
        Args:
            task_id: 要选择的任务ID
        """
        for row in range(self.task_table.rowCount()):
            item = self.task_table.item(row, 0)
            if item and item.data(Qt.ItemDataRole.UserRole) == task_id:
                self.task_table.selectRow(row)
                break
    
    def get_selected_task_id(self) -> Optional[str]:
        """获取当前选中的任务ID
        
        Returns:
            选中的任务ID，如果没有选中则返回None
        """
        return self.selected_task_id
    
    def set_auto_refresh(self, enabled: bool, interval: int = 5000):
        """设置自动刷新
        
        Args:
            enabled: 是否启用自动刷新
            interval: 刷新间隔（毫秒）
        """
        if enabled:
            self.refresh_timer.start(interval)
        else:
            self.refresh_timer.stop()
        
        logger.info(f"自动刷新{'启用' if enabled else '禁用'}，间隔: {interval}ms")
    
    def update_task_progress(self, task_id: str, progress: int, message: str = ""):
        """更新任务进度
        
        Args:
            task_id: 任务ID
            progress: 进度百分比 (0-100)
            message: 进度消息
        """
        try:
            # 查找任务所在行
            for row in range(self.task_table.rowCount()):
                item = self.task_table.item(row, 0)
                if item and item.data(Qt.ItemDataRole.UserRole) == task_id:
                    # 更新进度列
                    progress_item = self.task_table.item(row, 6)
                    if progress_item:
                        progress_item.setText(f"{progress}%")
                        
                        # 设置进度颜色
                        if progress == 100:
                            progress_item.setBackground(QBrush(QColor(200, 255, 200)))
                        elif progress > 0:
                            progress_item.setBackground(QBrush(QColor(255, 255, 200)))
                        else:
                            progress_item.setBackground(QBrush(QColor(255, 255, 255)))
                    
                    # 如果是当前选中的任务，更新详情显示
                    if self.selected_task_id == task_id:
                        self._update_task_details_progress(task_id, progress, message)
                    
                    break
                    
        except Exception as e:
            logger.error(f"更新任务进度失败: {e}")
    
    def _update_task_details_progress(self, task_id: str, progress: int, message: str):
        """更新任务详情中的进度信息
        
        Args:
            task_id: 任务ID
            progress: 进度百分比
            message: 进度消息
        """
        try:
            # 获取当前详情内容
            current_html = self.detail_text.toHtml()
            
            # 添加或更新进度信息
            progress_info = f"<b>执行进度:</b> {progress}%"
            if message:
                progress_info += f"<br><b>当前状态:</b> {message}"
            
            # 如果已有进度信息，替换它
            import re
            pattern = r'<b>执行进度:</b>.*?(?=<b>|</div>|$)'
            if re.search(pattern, current_html, re.DOTALL):
                updated_html = re.sub(pattern, progress_info, current_html, flags=re.DOTALL)
            else:
                # 在状态信息后添加进度信息
                status_pattern = r'(<b>状态:</b>.*?)(<br>)'
                updated_html = re.sub(status_pattern, f'\\1\\2{progress_info}<br>', current_html)
            
            self.detail_text.setHtml(updated_html)
            
        except Exception as e:
            logger.error(f"更新任务详情进度失败: {e}")
    
    def update_task_status(self, task_id: str, status: TaskStatus):
        """更新任务状态
        
        Args:
            task_id: 任务ID
            status: 新状态
        """
        try:
            # 查找任务所在行
            for row in range(self.task_table.rowCount()):
                item = self.task_table.item(row, 0)
                if item and item.data(Qt.ItemDataRole.UserRole) == task_id:
                    # 更新状态列
                    status_item = self.task_table.item(row, 3)
                    if status_item:
                        status_item.setText(status.value)
                        
                        # 设置状态颜色
                        if status == TaskStatus.RUNNING:
                            status_item.setBackground(QBrush(QColor(200, 255, 200)))
                        elif status == TaskStatus.FAILED:
                            status_item.setBackground(QBrush(QColor(255, 200, 200)))
                        elif status == TaskStatus.COMPLETED:
                            status_item.setBackground(QBrush(QColor(200, 200, 255)))
                        else:
                            status_item.setBackground(QBrush(QColor(255, 255, 255)))
                    
                    # 如果是当前选中的任务，刷新详情显示
                    if self.selected_task_id == task_id:
                        self._show_task_details(task_id)
                    
                    break
                    
        except Exception as e:
            logger.error(f"更新任务状态失败: {e}")