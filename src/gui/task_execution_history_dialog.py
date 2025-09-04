# -*- coding: utf-8 -*-
"""
任务执行历史记录对话框
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from PyQt6.QtCore import QDate, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QBrush, QColor, QFont, QIcon
from PyQt6.QtWidgets import QDialog

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
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
)
from loguru import logger

from adapters.task_manager_adapter import TaskManagerAdapter


class TaskExecutionHistoryDialog(QDialog, FilterWidget):
    """任务执行历史记录对话框"""

    def __init__(
        self, task_manager: TaskManagerAdapter, task_id: str = None, parent=None
    ):
        """初始化对话框

        Args:
            task_manager: 任务管理器实例
            task_id: 特定任务ID（可选，如果提供则只显示该任务的历史）
            parent: 父组件
        """
        QDialog.__init__(self, parent)
        FilterWidget.__init__(self)
        self.task_manager = task_manager
        self.task_id = task_id
        self.execution_records = []

        self._setup_ui()
        self._load_execution_history()

    def _setup_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("任务执行历史记录")
        self.setModal(True)
        self.resize(1000, 700)

        # 主布局
        main_layout = self.create_vbox_layout()
        self.setLayout(main_layout)

        # 筛选区域
        filter_group = self._create_filter_group()
        main_layout.addWidget(filter_group)

        # 分割器
        splitter = self.create_splitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)

        # 左侧：执行记录列表
        left_frame = self._create_execution_list_frame()
        splitter.addWidget(left_frame)

        # 右侧：执行详情
        right_frame = self._create_execution_details_frame()
        splitter.addWidget(right_frame)

        # 设置分割器比例
        splitter.setSizes([600, 400])

        # 底部按钮
        button_layout = self._create_button_layout()
        main_layout.addLayout(button_layout)

    def _create_filter_group(self) -> QGroupBox:
        """创建筛选区域"""
        group = self.create_group_box("筛选条件")
        layout = self.create_hbox_layout()
        group.setLayout(layout)

        # 状态筛选
        layout.addWidget(QLabel("状态:"))
        self.status_combo = QComboBox()
        self.status_combo.addItems(["全部", "成功", "失败", "运行中", "已取消"])
        self.status_combo.currentTextChanged.connect(self._apply_filters)
        layout.addWidget(self.status_combo)

        # 日期范围
        layout.addWidget(QLabel("开始日期:"))
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addDays(-30))
        self.start_date.setCalendarPopup(True)
        self.start_date.dateChanged.connect(self._apply_filters)
        layout.addWidget(self.start_date)

        layout.addWidget(QLabel("结束日期:"))
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        self.end_date.dateChanged.connect(self._apply_filters)
        layout.addWidget(self.end_date)

        # 搜索框
        layout.addWidget(QLabel("搜索:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("搜索执行ID或错误信息...")
        self.search_edit.textChanged.connect(self._apply_filters)
        layout.addWidget(self.search_edit)

        # 只显示失败的执行
        self.show_failed_only = QCheckBox("只显示失败")
        self.show_failed_only.toggled.connect(self._apply_filters)
        layout.addWidget(self.show_failed_only)

        layout.addStretch()

        # 刷新按钮
        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(self._load_execution_history)
        layout.addWidget(refresh_btn)

        return group

    def _create_execution_list_frame(self) -> QFrame:
        """创建执行记录列表框架"""
        frame = QFrame()
        layout = self.create_vbox_layout()
        frame.setLayout(layout)

        # 标题
        title_label = QLabel("执行记录列表")
        title_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        layout.addWidget(title_label)

        # 执行记录表格
        self.execution_table = QTableWidget()
        self.execution_table.setColumnCount(7)
        self.execution_table.setHorizontalHeaderLabels(
            ["执行ID", "任务名称", "开始时间", "结束时间", "持续时间", "状态", "进度"]
        )

        # 设置表格属性
        self.execution_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.execution_table.setAlternatingRowColors(True)
        self.execution_table.setSortingEnabled(True)

        # 设置列宽
        header = self.execution_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)  # 执行ID
        self.execution_table.setColumnWidth(0, 120)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # 任务名称
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)  # 开始时间
        self.execution_table.setColumnWidth(2, 140)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)  # 结束时间
        self.execution_table.setColumnWidth(3, 140)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)  # 持续时间
        self.execution_table.setColumnWidth(4, 100)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)  # 状态
        self.execution_table.setColumnWidth(5, 80)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)  # 进度
        self.execution_table.setColumnWidth(6, 80)

        # 连接信号
        self.execution_table.itemSelectionChanged.connect(
            self._on_execution_selection_changed
        )

        layout.addWidget(self.execution_table)

        return frame

    def _create_execution_details_frame(self) -> QFrame:
        """创建执行详情框架"""
        frame = QFrame()
        layout = self.create_vbox_layout()
        frame.setLayout(layout)

        # 标题
        title_label = QLabel("执行详情")
        title_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        layout.addWidget(title_label)

        # 详情文本区域
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setFont(QFont("Consolas", 9))
        layout.addWidget(self.details_text)

        # 统计信息
        stats_group = QGroupBox("统计信息")
        stats_layout = QVBoxLayout(stats_group)

        self.stats_label = QLabel("请选择执行记录查看详情")
        self.stats_label.setWordWrap(True)
        stats_layout.addWidget(self.stats_label)

        layout.addWidget(stats_group)

        return frame

    def _create_button_layout(self) -> QHBoxLayout:
        """创建底部按钮布局"""
        layout = self.create_hbox_layout()
        layout.addStretch()

        # 导出按钮
        export_btn = QPushButton("导出历史")
        export_btn.clicked.connect(self._export_history)
        layout.addWidget(export_btn)

        # 清理按钮
        cleanup_btn = QPushButton("清理旧记录")
        cleanup_btn.clicked.connect(self._cleanup_old_records)
        layout.addWidget(cleanup_btn)

        # 关闭按钮
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

        return layout

    def _load_execution_history(self):
        """加载执行历史记录"""
        try:
            if self.task_id:
                # 加载特定任务的执行历史
                self.execution_records = self.task_manager.get_task_executions(
                    self.task_id
                )
            else:
                # 加载所有任务的执行历史
                # 这里需要在TaskManager中添加获取所有执行记录的方法
                self.execution_records = self._get_all_executions()

            self._populate_execution_table()

        except Exception as e:
            logger.error(f"加载执行历史失败: {e}")
            QMessageBox.critical(self, "错误", f"加载执行历史失败: {str(e)}")

    def _get_all_executions(self) -> List[Dict[str, Any]]:
        """获取所有任务的执行记录"""
        # 这是一个临时实现，实际应该在TaskManager中添加相应方法
        all_executions = []
        try:
            # 获取所有任务
            tasks = self.task_manager.list_tasks_sync()
            for task in tasks:
                executions = self.task_manager.get_task_executions(task.task_id)
                all_executions.extend(executions)
        except Exception as e:
            logger.error(f"获取所有执行记录失败: {e}")

        return all_executions

    def _populate_execution_table(self):
        """填充执行记录表格"""
        self.execution_table.setRowCount(len(self.execution_records))

        for row, record in enumerate(self.execution_records):
            # 执行ID
            execution_id = record.get("execution_id", "N/A")
            self.execution_table.setItem(
                row,
                0,
                QTableWidgetItem(
                    execution_id[:8] + "..." if len(execution_id) > 8 else execution_id
                ),
            )

            # 任务名称
            task_name = record.get("task_name", "Unknown")
            self.execution_table.setItem(row, 1, QTableWidgetItem(task_name))

            # 开始时间
            start_time = record.get("start_time")
            start_time_str = (
                start_time.strftime("%Y-%m-%d %H:%M:%S") if start_time else "N/A"
            )
            self.execution_table.setItem(row, 2, QTableWidgetItem(start_time_str))

            # 结束时间
            end_time = record.get("end_time")
            end_time_str = end_time.strftime("%Y-%m-%d %H:%M:%S") if end_time else "N/A"
            self.execution_table.setItem(row, 3, QTableWidgetItem(end_time_str))

            # 持续时间
            duration = self._calculate_duration(start_time, end_time)
            self.execution_table.setItem(row, 4, QTableWidgetItem(duration))

            # 状态
            status = record.get("status", "Unknown")
            status_item = QTableWidgetItem(status)

            # 根据状态设置颜色
            if status == "completed":
                status_item.setBackground(QBrush(QColor(200, 255, 200)))  # 浅绿色
            elif status == "failed":
                status_item.setBackground(QBrush(QColor(255, 200, 200)))  # 浅红色
            elif status == "running":
                status_item.setBackground(QBrush(QColor(200, 200, 255)))  # 浅蓝色
            elif status == "cancelled":
                status_item.setBackground(QBrush(QColor(255, 255, 200)))  # 浅黄色

            self.execution_table.setItem(row, 5, status_item)

            # 进度
            progress = record.get("progress", 0)
            progress_str = (
                f"{progress:.1f}%"
                if isinstance(progress, (int, float))
                else str(progress)
            )
            self.execution_table.setItem(row, 6, QTableWidgetItem(progress_str))

    def _calculate_duration(self, start_time, end_time) -> str:
        """计算执行持续时间"""
        if not start_time:
            return "N/A"

        if not end_time:
            # 如果没有结束时间，计算到现在的时间
            end_time = datetime.now()

        try:
            duration = end_time - start_time
            total_seconds = int(duration.total_seconds())

            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60

            if hours > 0:
                return f"{hours}h {minutes}m {seconds}s"
            elif minutes > 0:
                return f"{minutes}m {seconds}s"
            else:
                return f"{seconds}s"

        except Exception:
            return "N/A"

    def _on_execution_selection_changed(self):
        """执行记录选择变化事件"""
        current_row = self.execution_table.currentRow()
        if current_row >= 0 and current_row < len(self.execution_records):
            record = self.execution_records[current_row]
            self._show_execution_details(record)
        else:
            self._clear_execution_details()

    def _show_execution_details(self, record: Dict[str, Any]):
        """显示执行详情"""
        details = []
        details.append(f"<h3>执行详情</h3>")
        details.append(f"<b>执行ID:</b> {record.get('execution_id', 'N/A')}")
        details.append(f"<b>任务ID:</b> {record.get('task_id', 'N/A')}")
        details.append(f"<b>任务名称:</b> {record.get('task_name', 'N/A')}")
        details.append(f"<b>状态:</b> {record.get('status', 'N/A')}")
        details.append(f"<b>进度:</b> {record.get('progress', 0)}%")

        # 时间信息
        start_time = record.get("start_time")
        if start_time:
            details.append(
                f"<b>开始时间:</b> {start_time.strftime('%Y-%m-%d %H:%M:%S')}"
            )

        end_time = record.get("end_time")
        if end_time:
            details.append(f"<b>结束时间:</b> {end_time.strftime('%Y-%m-%d %H:%M:%S')}")

        duration = self._calculate_duration(start_time, end_time)
        details.append(f"<b>持续时间:</b> {duration}")

        # 执行结果
        result = record.get("result")
        if result:
            details.append(f"<b>执行结果:</b> {result}")

        # 错误信息
        error_message = record.get("error_message")
        if error_message:
            details.append(
                f"<b>错误信息:</b> <span style='color: red;'>{error_message}</span>"
            )

        # 执行日志
        execution_log = record.get("execution_log")
        if execution_log:
            details.append(f"<b>执行日志:</b>")
            details.append(
                f"<pre style='background-color: #f5f5f5; padding: 10px; border-radius: 5px;'>{execution_log}</pre>"
            )

        self.details_text.setHtml("<br>".join(details))

        # 更新统计信息
        self._update_stats_for_record(record)

    def _update_stats_for_record(self, record: Dict[str, Any]):
        """更新选中记录的统计信息"""
        stats = []

        # 基本统计
        actions_completed = record.get("actions_completed", 0)
        actions_failed = record.get("actions_failed", 0)
        total_actions = actions_completed + actions_failed

        stats.append(f"总动作数: {total_actions}")
        stats.append(f"成功动作: {actions_completed}")
        stats.append(f"失败动作: {actions_failed}")

        if total_actions > 0:
            success_rate = (actions_completed / total_actions) * 100
            stats.append(f"成功率: {success_rate:.1f}%")

        # 性能统计
        avg_action_time = record.get("avg_action_time")
        if avg_action_time:
            stats.append(f"平均动作时间: {avg_action_time:.2f}s")

        # 资源使用
        memory_usage = record.get("memory_usage")
        if memory_usage:
            stats.append(f"内存使用: {memory_usage}MB")

        cpu_usage = record.get("cpu_usage")
        if cpu_usage:
            stats.append(f"CPU使用: {cpu_usage}%")

        self.stats_label.setText("\n".join(stats))

    def _clear_execution_details(self):
        """清空执行详情"""
        self.details_text.clear()
        self.stats_label.setText("请选择执行记录查看详情")

    def _apply_filters(self):
        """应用筛选条件"""
        # 这里实现筛选逻辑
        # 根据状态、日期范围、搜索关键词等筛选执行记录
        pass

    def _export_history(self):
        """导出执行历史"""
        try:
            # 实现导出功能
            QMessageBox.information(self, "提示", "导出功能正在开发中...")
        except Exception as e:
            logger.error(f"导出历史失败: {e}")
            QMessageBox.critical(self, "错误", f"导出失败: {str(e)}")

    def _cleanup_old_records(self):
        """清理旧记录"""
        try:
            # 实现清理功能
            reply = QMessageBox.question(
                self,
                "确认",
                "确定要清理30天前的执行记录吗？此操作不可撤销。",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )

            if reply == QMessageBox.StandardButton.Yes:
                # 这里实现清理逻辑
                QMessageBox.information(self, "提示", "清理功能正在开发中...")

        except Exception as e:
            logger.error(f"清理旧记录失败: {e}")
            QMessageBox.critical(self, "错误", f"清理失败: {str(e)}")
