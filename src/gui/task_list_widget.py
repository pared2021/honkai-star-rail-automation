# -*- coding: utf-8 -*-
"""
任务列表显示界面组件
重构为MVP模式的View层实现。
"""

from abc import ABCMeta
from datetime import datetime
from typing import Any, Dict, List, Optional

from PyQt6.QtCore import QDate, Qt, QThread, QTimer, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QAction, QBrush, QColor, QFont, QIcon
from ..common.gui_components import (
    FilterWidget,
    QCheckBox,
    QComboBox,
    QDateEdit,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from loguru import logger

from src.adapters.task_manager_adapter import TaskManagerAdapter
from src.models.task_models import Task, TaskPriority, TaskStatus, TaskType

from .mvp.task_list_view import TaskListView


class QWidgetMeta(type(QWidget), ABCMeta):
    """解决QWidget和ABC元类冲突的元类"""

    pass


class TaskListWidget(FilterWidget, TaskListView, metaclass=QWidgetMeta):
    """任务列表显示界面组件"""

    # 信号定义
    task_selected = pyqtSignal(str)  # 任务选择信号，传递任务ID
    task_edit_requested = pyqtSignal(str)  # 任务编辑请求信号
    task_delete_requested = pyqtSignal(str)  # 任务删除请求信号
    task_start_requested = pyqtSignal(str)  # 任务启动请求信号
    task_stop_requested = pyqtSignal(str)  # 任务停止请求信号
    task_copy_requested = pyqtSignal(str)  # 任务复制请求信号
    refresh_requested = pyqtSignal()  # 刷新请求信号
    filter_changed = pyqtSignal(dict)  # 过滤条件变化信号

    def __init__(
        self, task_manager: TaskManagerAdapter = None, task_monitor=None, parent=None
    ):
        """初始化任务列表界面

        Args:
            task_manager: 任务管理器实例（兼容性保留，MVP模式下可为None）
            task_monitor: 任务监控器实例（可选）
            parent: 父组件
        """
        super().__init__(parent)

        # 兼容性保留
        self.task_manager = task_manager
        self.task_monitor = task_monitor

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
        self.refresh_timer.timeout.connect(self._emit_refresh_requested)
        self.refresh_timer.start(5000)  # 每5秒刷新一次

        # 连接任务监控器信号（如果存在）
        if self.task_monitor:
            self._connect_monitor_signals()

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
        status_label, self.status_filter_combo = self.create_filter_combo(
            "状态", [("全部", None)] + [(status.value, status) for status in TaskStatus]
        )
        filter_layout.addWidget(status_label)
        filter_layout.addWidget(self.status_filter_combo)

        # 类型过滤
        type_label, self.type_filter_combo = self.create_filter_combo(
            "类型", [("全部", None)] + [(task_type.value, task_type) for task_type in TaskType]
        )
        filter_layout.addWidget(type_label)
        filter_layout.addWidget(self.type_filter_combo)

        # 优先级过滤
        priority_label, self.priority_filter_combo = self.create_filter_combo(
            "优先级", [("全部", None)] + [(priority.value, priority) for priority in TaskPriority]
        )
        filter_layout.addWidget(priority_label)
        filter_layout.addWidget(self.priority_filter_combo)

        # 文本搜索
        filter_layout.addWidget(QLabel("搜索:"))
        self.search_edit = self.create_search_edit("输入任务名称或描述")
        filter_layout.addWidget(self.search_edit)

        # 清除过滤按钮
        self.clear_filter_btn = self.create_button("清除过滤")
        self.clear_filter_btn.clicked.connect(self._clear_filters)
        filter_layout.addWidget(self.clear_filter_btn)

        filter_layout.addStretch()
        layout.addWidget(filter_group)

        # 操作按钮组
        action_group = QGroupBox("操作")
        action_layout = QHBoxLayout(action_group)

        # 刷新按钮
        self.refresh_btn = self.create_button("刷新")
        self.refresh_btn.clicked.connect(self.refresh_task_list)
        action_layout.addWidget(self.refresh_btn)

        # 启动任务按钮
        self.start_task_btn = self.create_button("启动任务")
        self.start_task_btn.setEnabled(False)
        self.start_task_btn.clicked.connect(self._start_selected_task)
        action_layout.addWidget(self.start_task_btn)

        # 停止任务按钮
        self.stop_task_btn = self.create_button("停止任务")
        self.stop_task_btn.setEnabled(False)
        self.stop_task_btn.clicked.connect(self._stop_selected_task)
        action_layout.addWidget(self.stop_task_btn)

        # 编辑任务按钮
        self.edit_task_btn = self.create_button("编辑任务")
        self.edit_task_btn.setEnabled(False)
        self.edit_task_btn.clicked.connect(self._edit_selected_task)
        action_layout.addWidget(self.edit_task_btn)

        # 删除任务按钮
        self.delete_task_btn = self.create_button("删除任务")
        self.delete_task_btn.setEnabled(False)
        self.delete_task_btn.setStyleSheet(
            """
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
        """
        )
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
        self.task_table.setHorizontalHeaderLabels(
            ["任务名称", "类型", "优先级", "状态", "创建时间", "最后执行", "进度"]
        )

        # 设置表格属性
        self.task_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.task_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.task_table.setAlternatingRowColors(True)
        self.task_table.setSortingEnabled(True)

        # 设置列宽
        header = self.task_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # 任务名称
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # 类型
        header.setSectionResizeMode(
            2, QHeaderView.ResizeMode.ResizeToContents
        )  # 优先级
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # 状态
        header.setSectionResizeMode(
            4, QHeaderView.ResizeMode.ResizeToContents
        )  # 创建时间
        header.setSectionResizeMode(
            5, QHeaderView.ResizeMode.ResizeToContents
        )  # 最后执行
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
        self.detail_text.setStyleSheet(
            """
            QTextEdit {
                background-color: #f9f9f9;
                border: 1px solid #ddd;
                border-radius: 3px;
                padding: 10px;
                font-family: 'Microsoft YaHei', sans-serif;
                font-size: 12px;
                line-height: 1.4;
            }
        """
        )
        layout.addWidget(self.detail_text)

        # 默认显示提示信息
        self._show_no_selection_message()

        return widget

    def _connect_signals(self):
        """连接信号和槽"""
        pass

    def _connect_monitor_signals(self):
        """连接任务监控器信号"""
        if self.task_monitor:
            # 任务状态变化
            self.task_monitor.task_status_changed.connect(self.update_task_status)

            # 任务进度更新
            self.task_monitor.task_progress_updated.connect(self.update_task_progress)

            # 任务消息更新
            self.task_monitor.task_message_updated.connect(
                self._on_task_message_updated
            )

            # 任务完成
            self.task_monitor.task_completed.connect(self._on_task_completed)

            logger.info("任务监控器信号连接完成")

    def _on_task_message_updated(self, task_id: str, message: str):
        """任务消息更新处理"""
        if self.selected_task_id == task_id:
            # 更新详情显示中的消息
            self._update_task_details_progress(task_id, -1, message)

    def _on_task_completed(self, task_id: str, success: bool, message: str):
        """任务完成处理"""
        # 刷新任务列表以更新状态
        self.refresh_task_list()

        # 如果是当前选中的任务，更新详情
        if self.selected_task_id == task_id:
            self._show_task_details(task_id)

        # 记录任务完成信息
        status_text = "成功" if success else "失败"
        logger.info(f"任务 {task_id} 执行{status_text}: {message}")

    def _on_filter_changed(self):
        """过滤条件变化"""
        # 更新过滤条件
        self.filter_status = self.status_filter_combo.currentData()
        self.filter_type = self.type_filter_combo.currentData()
        self.filter_priority = self.priority_filter_combo.currentData()
        self.filter_text = self.search_edit.text().strip().lower()

        # MVP模式：发射过滤变化信号
        filters = self.get_current_filters()
        self.filter_changed.emit(filters)

        # 兼容性：如果有task_manager，使用传统方式
        if self.task_manager:
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
            if self.filter_type and task.task_type != self.filter_type:
                continue

            # 优先级过滤
            if self.filter_priority and task.priority != self.filter_priority:
                continue

            # 文本搜索
            if self.filter_text:
                search_text = f"{task.name} {task.description or ''}".lower()
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

        # 查看执行历史
        history_action = QAction("查看执行历史", self)
        history_action.triggered.connect(self._show_execution_history)
        menu.addAction(history_action)

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
        if not self.selected_task_id:
            QMessageBox.warning(self, "警告", "请先选择一个任务")
            return

        # MVP模式：发射启动请求信号
        self.task_start_requested.emit(self.selected_task_id)

        # 兼容性：如果有task_manager，使用传统方式
        if self.task_manager:
            try:
                self.task_manager.start_task_sync(self.selected_task_id)
                QMessageBox.information(self, "成功", "任务启动成功")
                self.refresh_task_list()
                logger.info(f"任务启动成功: {self.selected_task_id}")
            except Exception as e:
                logger.error(f"启动任务失败: {e}")
                QMessageBox.critical(self, "启动失败", f"启动任务失败：{str(e)}")

    def _stop_selected_task(self):
        """停止选中的任务"""
        if not self.selected_task_id:
            QMessageBox.warning(self, "警告", "请先选择一个任务")
            return

        # MVP模式：发射停止请求信号
        self.task_stop_requested.emit(self.selected_task_id)

        # 兼容性：如果有task_manager，使用传统方式
        if self.task_manager:
            try:
                self.task_manager.stop_task_sync(self.selected_task_id)
                QMessageBox.information(self, "成功", "任务停止成功")
                self.refresh_task_list()
                logger.info(f"任务停止成功: {self.selected_task_id}")
            except Exception as e:
                logger.error(f"停止任务失败: {e}")
                QMessageBox.critical(self, "停止失败", f"停止任务失败：{str(e)}")

    def _edit_selected_task(self):
        """编辑选中的任务"""
        if not self.selected_task_id:
            QMessageBox.warning(self, "警告", "请先选择一个任务")
            return

        # 发射编辑请求信号
        self.task_edit_requested.emit(self.selected_task_id)

    def _copy_selected_task(self):
        """复制选中的任务"""
        if not self.selected_task_id:
            QMessageBox.warning(self, "警告", "请先选择一个任务")
            return

        # MVP模式：发射复制请求信号
        self.task_copy_requested.emit(self.selected_task_id)

        # 兼容性：如果有task_manager，使用传统方式
        if self.task_manager:
            try:
                selected_task = None
                for task in self.current_tasks:
                    if task.task_id == self.selected_task_id:
                        selected_task = task
                        break

                if not selected_task:
                    QMessageBox.warning(self, "警告", "找不到选中的任务")
                    return

                config = selected_task.config.copy() if selected_task.config else {}
                config["task_name"] = f"{selected_task.name} (副本)"
                config["description"] = selected_task.description
                config["task_type"] = selected_task.task_type
                config["priority"] = selected_task.priority

                new_task_id = self.task_manager.create_task_sync(
                    user_id="default_user", config=config
                )

                QMessageBox.information(
                    self, "成功", f"任务复制成功！新任务ID: {new_task_id}"
                )
                self.refresh_task_list()
                logger.info(f"任务复制成功: {self.selected_task_id} -> {new_task_id}")

            except Exception as e:
                logger.error(f"复制任务失败: {e}")
                QMessageBox.critical(self, "复制失败", f"复制任务失败：{str(e)}")

    def _delete_selected_task(self):
        """删除选中的任务"""
        if not self.selected_task_id:
            QMessageBox.warning(self, "警告", "请先选择一个任务")
            return

        # MVP模式：发射删除请求信号
        self.task_delete_requested.emit(self.selected_task_id)

        # 兼容性：如果有task_manager，使用传统方式
        if self.task_manager:
            reply = QMessageBox.question(
                self,
                "确认删除",
                "确定要删除选中的任务吗？此操作不可撤销。",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )

            if reply == QMessageBox.StandardButton.Yes:
                try:
                    self.task_manager.delete_task_sync(self.selected_task_id)
                    QMessageBox.information(self, "成功", "任务删除成功")
                    self.refresh_task_list()
                    logger.info(f"任务删除成功: {self.selected_task_id}")
                except Exception as e:
                    logger.error(f"删除任务失败: {e}")
                    QMessageBox.critical(self, "删除失败", f"删除任务失败：{str(e)}")

    def _show_execution_history(self):
        """显示选中任务的执行历史"""
        if self.selected_task_id:
            try:
                from .task_execution_history_dialog import TaskExecutionHistoryDialog

                dialog = TaskExecutionHistoryDialog(
                    task_manager=self.task_manager,
                    task_id=self.selected_task_id,
                    parent=self,
                )
                dialog.exec()
            except Exception as e:
                logger.error(f"显示执行历史失败: {e}")
                QMessageBox.critical(self, "错误", f"显示执行历史失败：{str(e)}")

    def _show_task_details(self, task_id: str):
        """显示任务详情"""
        try:
            task = self.task_manager.get_task_sync(task_id)
            if not task:
                self._show_no_selection_message()
                return

            # 构建详情文本
            details = []
            # 使用 task.name 而不是 task.config.task_name
            details.append(f"<h3>{task.name}</h3>")
            details.append(f"<b>任务ID:</b> {task.task_id}")
            details.append(f"<b>类型:</b> {task.task_type.value}")
            details.append(f"<b>优先级:</b> {task.priority.value}")
            details.append(f"<b>状态:</b> {task.status.value}")
            details.append(
                f"<b>创建时间:</b> {task.created_at.strftime('%Y-%m-%d %H:%M:%S')}"
            )

            # Task 模型中没有 started_at 和 completed_at 字段，跳过这些

            if task.description:
                details.append(f"<b>描述:</b><br>{task.description}")

            # 从 config 字典中安全地获取配置信息
            config = task.config or {}

            if config.get("max_duration"):
                details.append(f"<b>最大执行时间:</b> {config['max_duration']} 秒")

            if config.get("retry_count") is not None:
                details.append(f"<b>重试次数:</b> {config['retry_count']}")

            if config.get("retry_interval") is not None:
                details.append(f"<b>重试间隔:</b> {config['retry_interval']} 秒")

            if config.get("safe_mode") is not None:
                details.append(
                    f"<b>安全模式:</b> {'是' if config['safe_mode'] else '否'}"
                )

            if config.get("scheduled_time"):
                # 如果 scheduled_time 是字符串，需要转换为 datetime
                scheduled_time = config["scheduled_time"]
                if isinstance(scheduled_time, str):
                    try:
                        scheduled_time = datetime.fromisoformat(scheduled_time)
                        details.append(
                            f"<b>计划执行时间:</b> {scheduled_time.strftime('%Y-%m-%d %H:%M:%S')}"
                        )
                    except:
                        details.append(f"<b>计划执行时间:</b> {scheduled_time}")
                elif hasattr(scheduled_time, "strftime"):
                    details.append(
                        f"<b>计划执行时间:</b> {scheduled_time.strftime('%Y-%m-%d %H:%M:%S')}"
                    )

            if task.repeat_interval:
                details.append(f"<b>重复间隔:</b> {task.repeat_interval} 秒")

            if config.get("actions"):
                details.append(f"<b>动作数量:</b> {len(config['actions'])}")

            if config.get("custom_params"):
                details.append(
                    f"<b>自定义参数:</b><br><pre>{config['custom_params']}</pre>"
                )

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
            name_item = QTableWidgetItem(task.name)
            name_item.setData(Qt.ItemDataRole.UserRole, task.task_id)
            self.task_table.setItem(row, 0, name_item)

            # 类型
            type_item = QTableWidgetItem(task.task_type.value)
            self.task_table.setItem(row, 1, type_item)

            # 优先级
            priority_item = QTableWidgetItem(task.priority.value)
            # 设置优先级颜色
            if task.priority == TaskPriority.HIGH:
                priority_item.setBackground(QBrush(QColor(255, 200, 200)))
            elif task.priority == TaskPriority.LOW:
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
            last_run = task.last_executed_at or task.created_at
            last_run_item = QTableWidgetItem(last_run.strftime("%m-%d %H:%M"))
            self.task_table.setItem(row, 5, last_run_item)

            # 进度（暂时显示状态）
            progress_item = QTableWidgetItem(
                "100%" if task.status == TaskStatus.COMPLETED else "0%"
            )
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
        """刷新任务列表（兼容性方法）"""
        if self.task_manager:
            # 兼容性：使用传统方式
            try:
                self.current_tasks = self.task_manager.list_tasks_sync(
                    user_id="default_user"
                )
                self._apply_filters()
                logger.debug(f"任务列表已刷新，共 {len(self.current_tasks)} 个任务")
            except Exception as e:
                logger.error(f"刷新任务列表失败: {e}")
                QMessageBox.critical(self, "刷新失败", f"刷新任务列表失败：{str(e)}")
        else:
            # MVP模式：发射刷新请求信号
            self.refresh_requested.emit()

    def _emit_refresh_requested(self):
        """发射刷新请求信号"""
        self.refresh_requested.emit()

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

    # TaskListView接口实现
    def display_tasks(self, tasks: List[Task]):
        """显示任务列表

        Args:
            tasks: 要显示的任务列表
        """
        try:
            self.current_tasks = tasks
            self._apply_filters()
            logger.debug(f"显示任务列表，共 {len(tasks)} 个任务")
        except Exception as e:
            logger.error(f"显示任务列表失败: {e}")

    def show_task_details(self, task: Optional[Task]):
        """显示任务详情

        Args:
            task: 要显示的任务对象，None表示清除显示
        """
        if task:
            self._show_task_details(task.task_id)
        else:
            self._show_no_selection_message()

    def update_statistics(self, stats: Dict[str, int]):
        """更新统计信息

        Args:
            stats: 统计数据字典
        """
        # 这里可以添加统计信息显示逻辑
        # 当前实现中没有专门的统计显示区域，可以在状态栏或其他地方显示
        logger.debug(f"统计信息更新: {stats}")

    def clear_selection(self):
        """清除任务选择"""
        self.task_table.clearSelection()
        self.selected_task_id = None
        self._show_no_selection_message()
        self._update_button_states()

    def set_filter_options(
        self,
        status_options: List[TaskStatus],
        type_options: List[TaskType],
        priority_options: List[TaskPriority],
    ):
        """设置过滤选项

        Args:
            status_options: 状态选项列表
            type_options: 类型选项列表
            priority_options: 优先级选项列表
        """
        try:
            # 更新状态过滤器
            self.status_filter_combo.clear()
            self.status_filter_combo.addItem("全部", None)
            for status in status_options:
                self.status_filter_combo.addItem(status.value, status)

            # 更新类型过滤器
            self.type_filter_combo.clear()
            self.type_filter_combo.addItem("全部", None)
            for task_type in type_options:
                self.type_filter_combo.addItem(task_type.value, task_type)

            # 更新优先级过滤器
            self.priority_filter_combo.clear()
            self.priority_filter_combo.addItem("全部", None)
            for priority in priority_options:
                self.priority_filter_combo.addItem(priority.value, priority)

            logger.debug("过滤选项已更新")

        except Exception as e:
            logger.error(f"设置过滤选项失败: {e}")

    def get_current_filters(self) -> Dict[str, Any]:
        """获取当前过滤条件

        Returns:
            当前过滤条件字典
        """
        filters = {}

        # 状态过滤
        status = self.status_filter_combo.currentData()
        if status:
            filters["status"] = status

        # 类型过滤
        task_type = self.type_filter_combo.currentData()
        if task_type:
            filters["type"] = task_type

        # 优先级过滤
        priority = self.priority_filter_combo.currentData()
        if priority:
            filters["priority"] = priority

        # 搜索文本
        search_text = self.search_edit.text().strip()
        if search_text:
            filters["search_text"] = search_text

        return filters

    def clear_filters(self):
        """清除所有过滤条件"""
        self._clear_filters()
        
    def apply_filters(self, filters: Dict[str, Any]):
        """应用过滤条件"""
        # 设置过滤器状态
        if 'status' in filters:
            for i in range(self.status_filter_combo.count()):
                if self.status_filter_combo.itemData(i) == filters['status']:
                    self.status_filter_combo.setCurrentIndex(i)
                    break
        
        if 'type' in filters:
            for i in range(self.type_filter_combo.count()):
                if self.type_filter_combo.itemData(i) == filters['type']:
                    self.type_filter_combo.setCurrentIndex(i)
                    break
        
        if 'priority' in filters:
            for i in range(self.priority_filter_combo.count()):
                if self.priority_filter_combo.itemData(i) == filters['priority']:
                    self.priority_filter_combo.setCurrentIndex(i)
                    break
        
        if 'search_text' in filters:
            self.search_edit.setText(filters['search_text'])
        
        # 应用过滤
        self._apply_filters()

    def set_loading_state(self, loading: bool):
        """设置加载状态

        Args:
            loading: 是否正在加载
        """
        # 可以在这里添加加载指示器
        self.setEnabled(not loading)
        if loading:
            logger.debug("设置为加载状态")
        else:
            logger.debug("取消加载状态")

    def enable_operations(self, enabled: bool):
        """启用/禁用操作按钮

        Args:
            enabled: 是否启用
        """
        self.start_task_btn.setEnabled(enabled)
        self.stop_task_btn.setEnabled(enabled)
        self.edit_task_btn.setEnabled(enabled)
        self.delete_task_btn.setEnabled(enabled)

    def enable_actions(self, enabled: bool) -> None:
        """启用/禁用操作按钮（TaskListView接口方法）

        Args:
            enabled: 是否启用
        """
        self.enable_operations(enabled)

    def update_button_states(
        self, has_selection: bool, selected_task: Optional[Task] = None
    ):
        """更新按钮状态

        Args:
            has_selection: 是否有选中的任务
            selected_task: 选中的任务对象
        """
        self._update_button_states()

    def show_message(self, message: str, message_type: str = "info"):
        """显示消息

        Args:
            message: 消息内容
            message_type: 消息类型 (info, warning, error, success)
        """
        if message_type == "error":
            QMessageBox.critical(self, "错误", message)
        elif message_type == "warning":
            QMessageBox.warning(self, "警告", message)
        elif message_type == "success":
            QMessageBox.information(self, "成功", message)
        else:
            QMessageBox.information(self, "信息", message)

    def show_error_dialog(self, title: str, message: str):
        """显示错误对话框

        Args:
            title: 对话框标题
            message: 错误消息
        """
        QMessageBox.critical(self, title, message)

    def show_confirmation_dialog(self, title: str, message: str) -> bool:
        """显示确认对话框

        Args:
            title: 对话框标题
            message: 确认消息

        Returns:
            用户是否确认
        """
        reply = QMessageBox.question(
            self,
            title,
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        return reply == QMessageBox.StandardButton.Yes

    def show_context_menu(self, position, task_id: str):
        """显示上下文菜单

        Args:
            position: 菜单位置
            task_id: 任务ID
        """
        self._show_context_menu(position)

    def show_execution_history(self, task_id: str):
        """显示任务执行历史

        Args:
            task_id: 任务ID
        """
        self._show_execution_history()

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

    def _update_task_details_progress(
        self, task_id: str, progress: int, message: str = ""
    ):
        """更新任务详情中的进度信息

        Args:
            task_id: 任务ID
            progress: 进度百分比，-1表示不更新进度
            message: 进度消息
        """
        try:
            # 获取当前详情内容
            current_html = self.detail_text.toHtml()

            # 添加或更新进度信息
            progress_info = ""
            if progress >= 0:
                progress_info = f"<b>执行进度:</b> {progress}%"
            if message:
                if progress_info:
                    progress_info += f"<br><b>当前状态:</b> {message}"
                else:
                    progress_info = f"<b>当前状态:</b> {message}"

            if progress_info:
                # 如果已有进度信息，替换它
                import re

                pattern = r"<b>执行进度:</b>.*?(?=<b>|</div>|$)"
                if re.search(pattern, current_html, re.DOTALL):
                    updated_html = re.sub(
                        pattern, progress_info, current_html, flags=re.DOTALL
                    )
                else:
                    # 在状态信息后添加进度信息
                    status_pattern = r"(<b>状态:</b>.*?)(<br>)"
                    updated_html = re.sub(
                        status_pattern, f"\\1\\2{progress_info}<br>", current_html
                    )

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

    def get_task_progress(self, task_id: str) -> int:
        """获取任务进度

        Args:
            task_id: 任务ID

        Returns:
            进度百分比，如果任务不存在返回-1
        """
        try:
            for row in range(self.task_table.rowCount()):
                item = self.task_table.item(row, 0)
                if item and item.data(Qt.ItemDataRole.UserRole) == task_id:
                    progress_item = self.task_table.item(row, 6)
                    if progress_item:
                        progress_text = progress_item.text().replace("%", "")
                        return int(progress_text)
            return -1
        except Exception as e:
            logger.error(f"获取任务进度失败: {e}")
            return -1
