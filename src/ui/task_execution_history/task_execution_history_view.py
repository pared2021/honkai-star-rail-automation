# -*- coding: utf-8 -*-
"""
任务执行历史View层
负责UI界面的展示和用户交互
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from PyQt6.QtCore import QDate, Qt, pyqtSignal
from PyQt6.QtGui import QBrush, QColor, QFont
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
)
from loguru import logger

from ..common.ui_components import MVPFilterWidget as FilterWidget


class TaskExecutionHistoryView(QDialog, FilterWidget):
    """任务执行历史View"""

    # 用户交互信号
    filter_changed = pyqtSignal(dict)  # 过滤条件变化
    record_selected = pyqtSignal(dict)  # 记录选择
    refresh_requested = pyqtSignal()  # 刷新请求
    export_requested = pyqtSignal(str, str)  # 导出请求(文件路径, 格式)
    cleanup_requested = pyqtSignal(int)  # 清理请求(天数)

    def __init__(self, parent=None):
        """初始化View"""
        QDialog.__init__(self, parent)
        FilterWidget.__init__(self)
        
        # 获取UI服务
        from ...services.ui_service_facade import IUIServiceFacade
        self.ui_service: Optional[IUIServiceFacade] = None
        
        self._setup_ui()
        self._connect_signals()
        
        logger.info("TaskExecutionHistoryView initialized")
    
    def set_ui_service(self, ui_service: IUIServiceFacade):
        """设置UI服务"""
        self.ui_service = ui_service

    def _get_config_value(self, key: str, default_value):
        """从UI服务获取配置值"""
        try:
            if self.ui_service:
                return self.ui_service.get_ui_config(key, default_value)
            return default_value
        except Exception as e:
            logger.warning(f"Failed to get config value for {key}: {e}")
            return default_value

    def _setup_ui(self):
        """设置用户界面"""
        self.setWindowTitle("任务执行历史记录")
        self.setModal(True)
        
        # 从配置获取窗口尺寸
        window_width = self._get_config_value('ui.history_window.width', 1000)
        window_height = self._get_config_value('ui.history_window.height', 700)
        self.resize(window_width, window_height)

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
        left_width = self._get_config_value('ui.history_window.splitter.left_width', 600)
        right_width = self._get_config_value('ui.history_window.splitter.right_width', 400)
        splitter.setSizes([left_width, right_width])

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
        layout.addWidget(self.status_combo)

        # 开始日期
        layout.addWidget(QLabel("开始日期:"))
        self.start_date = QDateEdit()
        default_days_back = self._get_config_value('ui.history_filter.default_days_back', 30)
        self.start_date.setDate(QDate.currentDate().addDays(-default_days_back))
        self.start_date.setCalendarPopup(True)
        layout.addWidget(self.start_date)

        layout.addWidget(QLabel("结束日期:"))
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        layout.addWidget(self.end_date)

        # 搜索框
        layout.addWidget(QLabel("搜索:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("搜索执行ID或错误信息...")
        layout.addWidget(self.search_edit)

        # 只显示失败的执行
        self.show_failed_only = QCheckBox("只显示失败")
        layout.addWidget(self.show_failed_only)

        layout.addStretch()

        # 刷新按钮
        self.refresh_btn = QPushButton("刷新")
        layout.addWidget(self.refresh_btn)

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
        self.execution_table.setColumnWidth(0, self._get_config_value('ui.history_table.column_width.execution_id', 120))
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # 任务名称
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)  # 开始时间
        self.execution_table.setColumnWidth(2, self._get_config_value('ui.history_table.column_width.start_time', 140))
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)  # 结束时间
        self.execution_table.setColumnWidth(3, self._get_config_value('ui.history_table.column_width.end_time', 140))
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)  # 持续时间
        self.execution_table.setColumnWidth(4, self._get_config_value('ui.history_table.column_width.duration', 100))
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)  # 状态
        self.execution_table.setColumnWidth(5, self._get_config_value('ui.history_table.column_width.status', 80))
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)  # 进度
        self.execution_table.setColumnWidth(6, self._get_config_value('ui.history_table.column_width.progress', 80))

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
        self.export_btn = QPushButton("导出历史")
        layout.addWidget(self.export_btn)

        # 清理按钮
        self.cleanup_btn = QPushButton("清理旧记录")
        layout.addWidget(self.cleanup_btn)

        # 关闭按钮
        self.close_btn = QPushButton("关闭")
        layout.addWidget(self.close_btn)

        return layout

    def _connect_signals(self):
        """连接信号与槽"""
        # 过滤条件变化
        self.status_combo.currentTextChanged.connect(self._on_filter_changed)
        self.start_date.dateChanged.connect(self._on_filter_changed)
        self.end_date.dateChanged.connect(self._on_filter_changed)
        self.search_edit.textChanged.connect(self._on_filter_changed)
        self.show_failed_only.toggled.connect(self._on_filter_changed)
        
        # 表格选择变化
        self.execution_table.itemSelectionChanged.connect(self._on_selection_changed)
        
        # 按钮点击
        self.refresh_btn.clicked.connect(self.refresh_requested.emit)
        self.export_btn.clicked.connect(self._on_export_clicked)
        self.cleanup_btn.clicked.connect(self._on_cleanup_clicked)
        self.close_btn.clicked.connect(self.accept)

    def _on_filter_changed(self):
        """过滤条件变化处理"""
        conditions = {
            'status': self.status_combo.currentText(),
            'start_date': self.start_date.date().toPython(),
            'end_date': self.end_date.date().toPython(),
            'search_text': self.search_edit.text(),
            'show_failed_only': self.show_failed_only.isChecked()
        }
        self.filter_changed.emit(conditions)

    def _on_selection_changed(self):
        """表格选择变化处理"""
        current_row = self.execution_table.currentRow()
        if current_row >= 0:
            # 从表格项中获取执行ID，然后发射信号
            execution_id_item = self.execution_table.item(current_row, 0)
            if execution_id_item:
                execution_id = execution_id_item.data(Qt.ItemDataRole.UserRole)
                if execution_id:
                    self.record_selected.emit({'execution_id': execution_id})
                else:
                    self.record_selected.emit({})
            else:
                self.record_selected.emit({})
        else:
            self.record_selected.emit({})

    def _on_export_clicked(self):
        """导出按钮点击处理"""
        # TODO: 显示文件保存对话框
        file_path = "execution_history.csv"  # 临时路径
        format_type = "csv"
        self.export_requested.emit(file_path, format_type)

    def _on_cleanup_clicked(self):
        """清理按钮点击处理"""
        cleanup_days = self._get_config_value('history.cleanup.default_days', 30)
        reply = QMessageBox.question(
            self,
            "确认",
            f"确定要清理{cleanup_days}天前的执行记录吗？此操作不可撤销。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.cleanup_requested.emit(cleanup_days)

    def display_execution_records(self, records: List[Dict[str, Any]]):
        """显示执行记录列表"""
        self.execution_table.setRowCount(len(records))

        for row, record in enumerate(records):
            # 执行ID
            execution_id = record.get("execution_id", "N/A")
            execution_id_item = QTableWidgetItem(
                execution_id[:8] + "..." if len(execution_id) > 8 else execution_id
            )
            # 存储完整的执行ID用于选择
            execution_id_item.setData(Qt.ItemDataRole.UserRole, execution_id)
            self.execution_table.setItem(row, 0, execution_id_item)

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
                color = self._get_config_value('ui.status_colors.completed', [200, 255, 200])
                status_item.setBackground(QBrush(QColor(*color)))
            elif status == "failed":
                color = self._get_config_value('ui.status_colors.failed', [255, 200, 200])
                status_item.setBackground(QBrush(QColor(*color)))
            elif status == "running":
                color = self._get_config_value('ui.status_colors.running', [200, 200, 255])
                status_item.setBackground(QBrush(QColor(*color)))
            elif status == "cancelled":
                color = self._get_config_value('ui.status_colors.cancelled', [255, 255, 200])
                status_item.setBackground(QBrush(QColor(*color)))

            self.execution_table.setItem(row, 5, status_item)

            # 进度
            progress = record.get("progress", 0)
            progress_str = (
                f"{progress:.1f}%"
                if isinstance(progress, (int, float))
                else str(progress)
            )
            self.execution_table.setItem(row, 6, QTableWidgetItem(progress_str))

        logger.debug(f"Displayed {len(records)} execution records")

    def display_execution_details(self, record: Dict[str, Any]):
        """显示执行详情"""
        if not record:
            self.clear_execution_details()
            return

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
        self._update_record_stats(record)
        
        logger.debug(f"Displayed details for execution: {record.get('execution_id', 'N/A')}")

    def _update_record_stats(self, record: Dict[str, Any]):
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

    def clear_execution_details(self):
        """清空执行详情"""
        self.details_text.clear()
        self.stats_label.setText("请选择执行记录查看详情")

    def update_statistics(self, statistics: Dict[str, Any]):
        """更新统计信息显示"""
        # 可以在界面上显示总体统计信息
        logger.debug(f"Statistics updated: {statistics}")

    def set_loading_state(self, loading: bool):
        """设置加载状态"""
        self.refresh_btn.setEnabled(not loading)
        self.export_btn.setEnabled(not loading)
        self.cleanup_btn.setEnabled(not loading)
        
        if loading:
            self.refresh_btn.setText("加载中...")
        else:
            self.refresh_btn.setText("刷新")

    def show_message(self, title: str, message: str, is_error: bool = False):
        """显示消息"""
        if is_error:
            QMessageBox.critical(self, title, message)
        else:
            QMessageBox.information(self, title, message)

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

    def get_filter_conditions(self) -> Dict[str, Any]:
        """获取当前过滤条件"""
        return {
            'status': self.status_combo.currentText(),
            'start_date': self.start_date.date().toPython(),
            'end_date': self.end_date.date().toPython(),
            'search_text': self.search_edit.text(),
            'show_failed_only': self.show_failed_only.isChecked()
        }

    def set_filter_conditions(self, conditions: Dict[str, Any]):
        """设置过滤条件"""
        if 'status' in conditions:
            self.status_combo.setCurrentText(conditions['status'])
        
        if 'start_date' in conditions:
            self.start_date.setDate(QDate.fromString(conditions['start_date'].isoformat(), Qt.DateFormat.ISODate))
        
        if 'end_date' in conditions:
            self.end_date.setDate(QDate.fromString(conditions['end_date'].isoformat(), Qt.DateFormat.ISODate))
        
        if 'search_text' in conditions:
            self.search_edit.setText(conditions['search_text'])
        
        if 'show_failed_only' in conditions:
            self.show_failed_only.setChecked(conditions['show_failed_only'])