"""任务列表View层

该模块定义了任务列表的View层，负责UI界面显示和用户交互。
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QTextEdit, QSplitter, QPushButton, QComboBox, QLineEdit, QLabel,
    QHeaderView, QAbstractItemView, QMenu, QMessageBox, QProgressBar
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QAction, QColor, QFont

from src.models.task_models import Task, TaskStatus, TaskType, TaskPriority
from src.ui.common.ui_components import MVPFilterWidget as FilterWidget
from src.ui.task_execution_history import TaskExecutionHistoryMVP as TaskExecutionHistoryDialog
from src.utils.logger import logger


class TaskListView(QWidget, FilterWidget):
    """任务列表View层
    
    负责任务列表的UI界面显示和用户交互，继承FilterWidget提供过滤功能。
    """
    
    # 用户交互信号
    task_selected = pyqtSignal(str)  # 任务选择，传递任务ID
    task_edit_requested = pyqtSignal(str)  # 编辑任务请求
    task_delete_requested = pyqtSignal(str)  # 删除任务请求
    task_start_requested = pyqtSignal(str)  # 启动任务请求
    task_stop_requested = pyqtSignal(str)  # 停止任务请求
    task_copy_requested = pyqtSignal(str)  # 复制任务请求
    refresh_requested = pyqtSignal()  # 刷新请求
    filter_changed = pyqtSignal(dict)  # 过滤条件变化
    execution_history_requested = pyqtSignal(str)  # 查看执行历史请求
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 初始化UI服务
        self.ui_service: Optional[IUIServiceFacade] = None
        
        # 当前数据
        self._tasks: List[Task] = []
        self._selected_task_id: Optional[str] = None
        self._statistics: Dict[str, int] = {}
        
        # UI组件
        self._task_table: Optional[QTableWidget] = None
        self._task_detail: Optional[QTextEdit] = None
        self._statistics_label: Optional[QLabel] = None
        self._progress_bar: Optional[QProgressBar] = None
        
        # 操作按钮
        self._refresh_btn: Optional[QPushButton] = None
        self._start_btn: Optional[QPushButton] = None
        self._stop_btn: Optional[QPushButton] = None
        self._edit_btn: Optional[QPushButton] = None
        self._delete_btn: Optional[QPushButton] = None
        
        # 过滤组件
        self._status_filter: Optional[QComboBox] = None
        self._type_filter: Optional[QComboBox] = None
        self._priority_filter: Optional[QComboBox] = None
        self._search_input: Optional[QLineEdit] = None
        
        # 初始化UI
        self._init_ui()
        self._connect_signals()
        
        logger.info("任务列表View初始化完成")
    
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
    
    def _init_ui(self):
        """初始化UI界面"""
        layout = QVBoxLayout(self)
        
        # 从配置获取布局参数
        margin = self._get_config_value('ui.task_list.layout.margin', 10)
        spacing = self._get_config_value('ui.task_list.layout.spacing', 10)
        layout.setContentsMargins(margin, margin, margin, margin)
        layout.setSpacing(spacing)
        
        # 标题
        title_label = QLabel("任务列表")
        title_font_size = self._get_config_value('ui.task_list.title.font_size', '18px')
        title_color = self._get_config_value('ui.task_list.title.color', '#2c3e50')
        title_margin_bottom = self._get_config_value('ui.task_list.title.margin_bottom', '10px')
        title_label.setStyleSheet(f"""
            QLabel {{
                font-size: {title_font_size};
                font-weight: bold;
                color: {title_color};
                margin-bottom: {title_margin_bottom};
            }}
        """)
        layout.addWidget(title_label)
        
        # 过滤和操作区域
        filter_layout = self._create_filter_area()
        layout.addLayout(filter_layout)
        
        # 操作按钮区域
        button_layout = self._create_button_area()
        layout.addLayout(button_layout)
        
        # 统计信息
        self._statistics_label = QLabel("总计: 0 | 运行中: 0 | 已完成: 0 | 失败: 0 | 待执行: 0")
        stats_color = self._get_config_value('ui.task_list.stats.color', '#7f8c8d')
        stats_font_size = self._get_config_value('ui.task_list.stats.font_size', '12px')
        stats_padding = self._get_config_value('ui.task_list.stats.padding', '5px')
        stats_bg_color = self._get_config_value('ui.task_list.stats.bg_color', '#ecf0f1')
        stats_border_radius = self._get_config_value('ui.task_list.stats.border_radius', '3px')
        self._statistics_label.setStyleSheet(f"""
            QLabel {{
                color: {stats_color};
                font-size: {stats_font_size};
                padding: {stats_padding};
                background-color: {stats_bg_color};
                border-radius: {stats_border_radius};
            }}
        """)
        layout.addWidget(self._statistics_label)
        
        # 进度条（用于显示加载状态）
        self._progress_bar = QProgressBar()
        self._progress_bar.setVisible(False)
        layout.addWidget(self._progress_bar)
        
        # 主要内容区域（任务列表和详情）
        content_splitter = self._create_content_area()
        layout.addWidget(content_splitter, 1)
    
    def _create_filter_area(self) -> QHBoxLayout:
        """创建过滤区域"""
        layout = QHBoxLayout()
        
        # 状态过滤
        layout.addWidget(QLabel("状态:"))
        self._status_filter = QComboBox()
        self._status_filter.addItem("全部", None)
        for status in TaskStatus:
            self._status_filter.addItem(status.value, status)
        layout.addWidget(self._status_filter)
        
        # 类型过滤
        layout.addWidget(QLabel("类型:"))
        self._type_filter = QComboBox()
        self._type_filter.addItem("全部", None)
        for task_type in TaskType:
            self._type_filter.addItem(task_type.value, task_type)
        layout.addWidget(self._type_filter)
        
        # 优先级过滤
        layout.addWidget(QLabel("优先级:"))
        self._priority_filter = QComboBox()
        self._priority_filter.addItem("全部", None)
        for priority in TaskPriority:
            self._priority_filter.addItem(priority.value, priority)
        layout.addWidget(self._priority_filter)
        
        # 搜索框
        layout.addWidget(QLabel("搜索:"))
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("输入任务名称或描述...")
        layout.addWidget(self._search_input)
        
        # 清除过滤按钮
        clear_btn = QPushButton("清除过滤")
        clear_btn.clicked.connect(self._clear_filters)
        layout.addWidget(clear_btn)
        
        layout.addStretch()
        return layout
    
    def _create_button_area(self) -> QHBoxLayout:
        """创建操作按钮区域"""
        layout = QHBoxLayout()
        
        # 刷新按钮
        self._refresh_btn = QPushButton("刷新")
        refresh_bg_color = self._get_config_value('ui.task_list.refresh_btn.bg_color', '#3498db')
        refresh_hover_color = self._get_config_value('ui.task_list.refresh_btn.hover_color', '#2980b9')
        refresh_pressed_color = self._get_config_value('ui.task_list.refresh_btn.pressed_color', '#21618c')
        refresh_padding = self._get_config_value('ui.task_list.refresh_btn.padding', '8px 16px')
        refresh_border_radius = self._get_config_value('ui.task_list.refresh_btn.border_radius', '4px')
        self._refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {refresh_bg_color};
                color: white;
                border: none;
                padding: {refresh_padding};
                border-radius: {refresh_border_radius};
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {refresh_hover_color};
            }}
            QPushButton:pressed {{
                background-color: {refresh_pressed_color};
            }}
        """)
        layout.addWidget(self._refresh_btn)
        
        # 启动按钮
        self._start_btn = QPushButton("启动任务")
        start_bg_color = self._get_config_value('ui.task_list.start_btn.bg_color', '#27ae60')
        start_hover_color = self._get_config_value('ui.task_list.start_btn.hover_color', '#229954')
        start_pressed_color = self._get_config_value('ui.task_list.start_btn.pressed_color', '#1e8449')
        start_disabled_color = self._get_config_value('ui.task_list.start_btn.disabled_color', '#95a5a6')
        btn_padding = self._get_config_value('ui.task_list.btn.padding', '8px 16px')
        btn_border_radius = self._get_config_value('ui.task_list.btn.border_radius', '4px')
        self._start_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {start_bg_color};
                color: white;
                border: none;
                padding: {btn_padding};
                border-radius: {btn_border_radius};
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {start_hover_color};
            }}
            QPushButton:pressed {{
                background-color: {start_pressed_color};
            }}
            QPushButton:disabled {{
                background-color: {start_disabled_color};
            }}
        """)
        self._start_btn.setEnabled(False)
        layout.addWidget(self._start_btn)
        
        # 停止按钮
        self._stop_btn = QPushButton("停止任务")
        stop_bg_color = self._get_config_value('ui.task_list.stop_btn.bg_color', '#e74c3c')
        stop_hover_color = self._get_config_value('ui.task_list.stop_btn.hover_color', '#c0392b')
        stop_pressed_color = self._get_config_value('ui.task_list.stop_btn.pressed_color', '#a93226')
        self._stop_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {stop_bg_color};
                color: white;
                border: none;
                padding: {btn_padding};
                border-radius: {btn_border_radius};
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {stop_hover_color};
            }}
            QPushButton:pressed {{
                background-color: {stop_pressed_color};
            }}
            QPushButton:disabled {{
                background-color: {start_disabled_color};
            }}
        """)
        self._stop_btn.setEnabled(False)
        layout.addWidget(self._stop_btn)
        
        # 编辑按钮
        self._edit_btn = QPushButton("编辑任务")
        edit_bg_color = self._get_config_value('ui.task_list.edit_btn.bg_color', '#f39c12')
        edit_hover_color = self._get_config_value('ui.task_list.edit_btn.hover_color', '#e67e22')
        edit_pressed_color = self._get_config_value('ui.task_list.edit_btn.pressed_color', '#d35400')
        self._edit_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {edit_bg_color};
                color: white;
                border: none;
                padding: {btn_padding};
                border-radius: {btn_border_radius};
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {edit_hover_color};
            }}
            QPushButton:pressed {{
                background-color: {edit_pressed_color};
            }}
            QPushButton:disabled {{
                background-color: {start_disabled_color};
            }}
        """)
        self._edit_btn.setEnabled(False)
        layout.addWidget(self._edit_btn)
        
        # 删除按钮
        self._delete_btn = QPushButton("删除任务")
        delete_bg_color = self._get_config_value('ui.task_list.delete_btn.bg_color', '#e74c3c')
        delete_hover_color = self._get_config_value('ui.task_list.delete_btn.hover_color', '#c0392b')
        delete_pressed_color = self._get_config_value('ui.task_list.delete_btn.pressed_color', '#a93226')
        self._delete_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {delete_bg_color};
                color: white;
                border: none;
                padding: {btn_padding};
                border-radius: {btn_border_radius};
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {delete_hover_color};
            }}
            QPushButton:pressed {{
                background-color: {delete_pressed_color};
            }}
            QPushButton:disabled {{
                background-color: {start_disabled_color};
            }}
        """)
        self._delete_btn.setEnabled(False)
        layout.addWidget(self._delete_btn)
        
        layout.addStretch()
        return layout
    
    def _create_content_area(self) -> QSplitter:
        """创建主要内容区域"""
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 任务列表
        task_list_widget = self._create_task_list_widget()
        splitter.addWidget(task_list_widget)
        
        # 任务详情
        task_detail_widget = self._create_task_detail_widget()
        splitter.addWidget(task_detail_widget)
        
        # 设置分割比例
        left_width = self._get_config_value('ui.task_list.splitter.left_width', 600)
        right_width = self._get_config_value('ui.task_list.splitter.right_width', 400)
        splitter.setSizes([left_width, right_width])
        
        return splitter
    
    def _create_task_list_widget(self) -> QWidget:
        """创建任务列表组件"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 任务表格
        self._task_table = QTableWidget()
        headers = ["任务名称", "类型", "优先级", "状态", "创建时间", "最后执行", "进度"]
        self._task_table.setColumnCount(len(headers))
        self._task_table.setHorizontalHeaderLabels(headers)
        
        # 设置列宽
        name_width = self._get_config_value('ui.task_list.table.column_width.name', 200)
        type_width = self._get_config_value('ui.task_list.table.column_width.type', 100)
        priority_width = self._get_config_value('ui.task_list.table.column_width.priority', 80)
        status_width = self._get_config_value('ui.task_list.table.column_width.status', 80)
        created_width = self._get_config_value('ui.task_list.table.column_width.created', 150)
        last_exec_width = self._get_config_value('ui.task_list.table.column_width.last_exec', 150)
        progress_width = self._get_config_value('ui.task_list.table.column_width.progress', 100)
        
        self._task_table.setColumnWidth(0, name_width)  # 任务名称
        self._task_table.setColumnWidth(1, type_width)  # 类型
        self._task_table.setColumnWidth(2, priority_width)   # 优先级
        self._task_table.setColumnWidth(3, status_width)   # 状态
        self._task_table.setColumnWidth(4, created_width)  # 创建时间
        self._task_table.setColumnWidth(5, last_exec_width)  # 最后执行
        self._task_table.setColumnWidth(6, progress_width)  # 进度
        
        # 设置表格属性
        header = self._task_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        
        self._task_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._task_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._task_table.setSortingEnabled(True)
        self._task_table.setAlternatingRowColors(True)
        
        # 设置右键菜单
        self._task_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        
        layout.addWidget(self._task_table)
        
        return widget
    
    def _create_task_detail_widget(self) -> QWidget:
        """创建任务详情组件"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 详情标题
        detail_label = QLabel("任务详情")
        detail_font_size = self._get_config_value('ui.task_list.detail.font_size', '14px')
        detail_color = self._get_config_value('ui.task_list.detail.color', '#2c3e50')
        detail_margin_bottom = self._get_config_value('ui.task_list.detail.margin_bottom', '5px')
        detail_label.setStyleSheet(f"""
            QLabel {{
                font-size: {detail_font_size};
                font-weight: bold;
                color: {detail_color};
                margin-bottom: {detail_margin_bottom};
            }}
        """)
        layout.addWidget(detail_label)
        
        # 详情文本
        self._task_detail = QTextEdit()
        self._task_detail.setReadOnly(True)
        detail_border_color = self._get_config_value('ui.task_list.detail_text.border_color', '#bdc3c7')
        detail_border_radius = self._get_config_value('ui.task_list.detail_text.border_radius', '4px')
        detail_text_padding = self._get_config_value('ui.task_list.detail_text.padding', '8px')
        detail_bg_color = self._get_config_value('ui.task_list.detail_text.bg_color', '#f8f9fa')
        detail_font_family = self._get_config_value('ui.task_list.detail_text.font_family', "'Consolas', 'Monaco', monospace")
        detail_text_font_size = self._get_config_value('ui.task_list.detail_text.font_size', '12px')
        self._task_detail.setStyleSheet(f"""
            QTextEdit {{
                border: 1px solid {detail_border_color};
                border-radius: {detail_border_radius};
                padding: {detail_text_padding};
                background-color: {detail_bg_color};
                font-family: {detail_font_family};
                font-size: {detail_text_font_size};
            }}
        """)
        layout.addWidget(self._task_detail)
        
        # 默认显示提示信息
        self._show_no_selection_message()
        
        return widget
    
    def _connect_signals(self):
        """连接信号"""
        # 过滤信号
        self._status_filter.currentIndexChanged.connect(self._on_filter_changed)
        self._type_filter.currentIndexChanged.connect(self._on_filter_changed)
        self._priority_filter.currentIndexChanged.connect(self._on_filter_changed)
        self._search_input.textChanged.connect(self._on_filter_changed)
        
        # 按钮信号
        self._refresh_btn.clicked.connect(self.refresh_requested.emit)
        self._start_btn.clicked.connect(self._on_start_task)
        self._stop_btn.clicked.connect(self._on_stop_task)
        self._edit_btn.clicked.connect(self._on_edit_task)
        self._delete_btn.clicked.connect(self._on_delete_task)
        
        # 表格信号
        self._task_table.itemSelectionChanged.connect(self._on_task_selection_changed)
        self._task_table.itemDoubleClicked.connect(self._on_task_double_clicked)
        self._task_table.customContextMenuRequested.connect(self._show_context_menu)
    
    # 过滤相关方法
    def _on_filter_changed(self):
        """过滤条件变化处理"""
        filters = {
            'status': self._status_filter.currentData(),
            'type': self._type_filter.currentData(),
            'priority': self._priority_filter.currentData(),
            'search_text': self._search_input.text().strip()
        }
        self.filter_changed.emit(filters)
    
    def _clear_filters(self):
        """清除过滤条件"""
        self._status_filter.setCurrentIndex(0)
        self._type_filter.setCurrentIndex(0)
        self._priority_filter.setCurrentIndex(0)
        self._search_input.clear()
    
    # 任务操作方法
    def _on_start_task(self):
        """启动任务"""
        if self._selected_task_id:
            self.task_start_requested.emit(self._selected_task_id)
    
    def _on_stop_task(self):
        """停止任务"""
        if self._selected_task_id:
            self.task_stop_requested.emit(self._selected_task_id)
    
    def _on_edit_task(self):
        """编辑任务"""
        if self._selected_task_id:
            self.task_edit_requested.emit(self._selected_task_id)
    
    def _on_delete_task(self):
        """删除任务"""
        if self._selected_task_id:
            # 显示确认对话框
            reply = QMessageBox.question(
                self, "确认删除",
                "确定要删除选中的任务吗？此操作不可撤销。",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.task_delete_requested.emit(self._selected_task_id)
    
    def _on_copy_task(self):
        """复制任务"""
        if self._selected_task_id:
            self.task_copy_requested.emit(self._selected_task_id)
    
    # 表格事件处理
    def _on_task_selection_changed(self):
        """任务选择变化处理"""
        selected_items = self._task_table.selectedItems()
        if selected_items:
            row = selected_items[0].row()
            task_id_item = self._task_table.item(row, 0)
            if task_id_item:
                task_id = task_id_item.data(Qt.ItemDataRole.UserRole)
                if task_id != self._selected_task_id:
                    self._selected_task_id = task_id
                    self.task_selected.emit(task_id)
                    self._update_button_states()
                    self._show_task_details(task_id)
        else:
            self._selected_task_id = None
            self._update_button_states()
            self._show_no_selection_message()
    
    def _on_task_double_clicked(self, item):
        """任务双击事件处理"""
        if self._selected_task_id:
            self.task_edit_requested.emit(self._selected_task_id)
    
    def _show_context_menu(self, position):
        """显示右键菜单"""
        if not self._selected_task_id:
            return
        
        menu = QMenu(self)
        
        # 启动任务
        start_action = QAction("启动任务", self)
        start_action.triggered.connect(self._on_start_task)
        menu.addAction(start_action)
        
        # 停止任务
        stop_action = QAction("停止任务", self)
        stop_action.triggered.connect(self._on_stop_task)
        menu.addAction(stop_action)
        
        menu.addSeparator()
        
        # 查看执行历史
        history_action = QAction("查看执行历史", self)
        history_action.triggered.connect(lambda: self.execution_history_requested.emit(self._selected_task_id))
        menu.addAction(history_action)
        
        menu.addSeparator()
        
        # 编辑任务
        edit_action = QAction("编辑任务", self)
        edit_action.triggered.connect(self._on_edit_task)
        menu.addAction(edit_action)
        
        # 复制任务
        copy_action = QAction("复制任务", self)
        copy_action.triggered.connect(self._on_copy_task)
        menu.addAction(copy_action)
        
        # 删除任务
        delete_action = QAction("删除任务", self)
        delete_action.triggered.connect(self._on_delete_task)
        menu.addAction(delete_action)
        
        # 显示菜单
        menu.exec(self._task_table.mapToGlobal(position))
    
    def _update_button_states(self):
        """更新按钮状态"""
        has_selection = self._selected_task_id is not None
        
        self._start_btn.setEnabled(has_selection)
        self._stop_btn.setEnabled(has_selection)
        self._edit_btn.setEnabled(has_selection)
        self._delete_btn.setEnabled(has_selection)
    
    # 数据显示方法
    def display_tasks(self, tasks: List[Task]):
        """显示任务列表"""
        try:
            self._tasks = tasks
            self._update_task_table()
            logger.debug(f"显示任务列表，共 {len(tasks)} 个任务")
        except Exception as e:
            logger.error(f"显示任务列表失败: {e}")
    
    def _update_task_table(self):
        """更新任务表格"""
        try:
            self._task_table.setRowCount(len(self._tasks))
            
            for row, task in enumerate(self._tasks):
                # 任务名称
                name_item = QTableWidgetItem(task.name)
                name_item.setData(Qt.ItemDataRole.UserRole, task.task_id)
                self._task_table.setItem(row, 0, name_item)
                
                # 类型
                type_item = QTableWidgetItem(task.task_type.value if task.task_type else "未知")
                self._task_table.setItem(row, 1, type_item)
                
                # 优先级
                priority_item = QTableWidgetItem(task.priority.value if task.priority else "普通")
                self._task_table.setItem(row, 2, priority_item)
                
                # 状态
                status_item = QTableWidgetItem(task.status.value if task.status else "未知")
                self._task_table.setItem(row, 3, status_item)
                
                # 创建时间
                created_time = task.created_at.strftime("%Y-%m-%d %H:%M:%S") if task.created_at else "未知"
                created_item = QTableWidgetItem(created_time)
                self._task_table.setItem(row, 4, created_item)
                
                # 最后执行时间
                last_run = task.last_run_at.strftime("%Y-%m-%d %H:%M:%S") if task.last_run_at else "从未执行"
                last_run_item = QTableWidgetItem(last_run)
                self._task_table.setItem(row, 5, last_run_item)
                
                # 进度
                progress = getattr(task, 'progress', 0)
                progress_item = QTableWidgetItem(f"{progress}%")
                self._task_table.setItem(row, 6, progress_item)
                
                # 设置行颜色
                self._set_row_color(row, task)
            
        except Exception as e:
            logger.error(f"更新任务表格失败: {e}")
    
    def _set_row_color(self, row: int, task: Task):
        """设置行颜色"""
        try:
            color = None
            
            # 根据状态设置颜色
            if task.status == TaskStatus.RUNNING:
                color = QColor(144, 238, 144)  # 浅绿色
            elif task.status == TaskStatus.FAILED:
                color = QColor(255, 182, 193)  # 浅红色
            elif task.status == TaskStatus.COMPLETED:
                color = QColor(173, 216, 230)  # 浅蓝色
            elif task.priority == TaskPriority.HIGH:
                color = QColor(255, 255, 224)  # 浅黄色
            
            if color:
                for col in range(self._task_table.columnCount()):
                    item = self._task_table.item(row, col)
                    if item:
                        item.setBackground(color)
                        
        except Exception as e:
            logger.error(f"设置行颜色失败: {e}")
    
    def _show_task_details(self, task_id: str):
        """显示任务详情"""
        try:
            task = None
            for t in self._tasks:
                if t.task_id == task_id:
                    task = t
                    break
            
            if not task:
                self._show_no_selection_message()
                return
            
            # 格式化任务详情
            details = []
            details.append(f"任务名称: {task.name}")
            details.append(f"任务ID: {task.task_id}")
            details.append(f"类型: {task.task_type.value if task.task_type else '未知'}")
            details.append(f"优先级: {task.priority.value if task.priority else '普通'}")
            details.append(f"状态: {task.status.value if task.status else '未知'}")
            
            if task.created_at:
                details.append(f"创建时间: {task.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            
            if task.description:
                details.append(f"描述: {task.description}")
            
            if hasattr(task, 'max_execution_time') and task.max_execution_time:
                details.append(f"最大执行时间: {task.max_execution_time}秒")
            
            if hasattr(task, 'retry_count'):
                details.append(f"重试次数: {task.retry_count}")
            
            if hasattr(task, 'safe_mode'):
                details.append(f"安全模式: {'是' if task.safe_mode else '否'}")
            
            if task.scheduled_at:
                details.append(f"计划执行时间: {task.scheduled_at.strftime('%Y-%m-%d %H:%M:%S')}")
            
            if hasattr(task, 'repeat_interval') and task.repeat_interval:
                details.append(f"重复间隔: {task.repeat_interval}秒")
            
            if task.config:
                details.append(f"\n配置参数:")
                for key, value in task.config.items():
                    details.append(f"  {key}: {value}")
            
            self._task_detail.setPlainText("\n".join(details))
            
        except Exception as e:
            logger.error(f"显示任务详情失败: {e}")
            self._task_detail.setPlainText(f"显示任务详情时发生错误: {e}")
    
    def _show_no_selection_message(self):
        """显示无选择提示信息"""
        self._task_detail.setPlainText("请选择一个任务以查看详情")
    
    def update_statistics(self, statistics: Dict[str, int]):
        """更新统计信息"""
        try:
            self._statistics = statistics
            text = f"总计: {statistics.get('total', 0)} | "
            text += f"运行中: {statistics.get('running', 0)} | "
            text += f"已完成: {statistics.get('completed', 0)} | "
            text += f"失败: {statistics.get('failed', 0)} | "
            text += f"待执行: {statistics.get('pending', 0)}"
            
            self._statistics_label.setText(text)
            logger.debug(f"统计信息已更新: {statistics}")
        except Exception as e:
            logger.error(f"更新统计信息失败: {e}")
    
    def update_task_progress(self, task_id: str, progress: int, message: str = ""):
        """更新任务进度"""
        try:
            # 更新表格中的进度
            for row in range(self._task_table.rowCount()):
                name_item = self._task_table.item(row, 0)
                if name_item and name_item.data(Qt.ItemDataRole.UserRole) == task_id:
                    progress_item = self._task_table.item(row, 6)
                    if progress_item:
                        progress_item.setText(f"{progress}%")
                    break
            
            # 如果是当前选中的任务，更新详情
            if self._selected_task_id == task_id:
                current_text = self._task_detail.toPlainText()
                if message:
                    updated_text = f"{current_text}\n\n进度更新: {progress}% - {message}"
                else:
                    updated_text = f"{current_text}\n\n进度更新: {progress}%"
                self._task_detail.setPlainText(updated_text)
            
            logger.debug(f"任务进度已更新: {task_id} -> {progress}%")
        except Exception as e:
            logger.error(f"更新任务进度失败: {e}")
    
    def update_task_status(self, task_id: str, status: TaskStatus):
        """更新任务状态"""
        try:
            # 更新表格中的状态
            for row in range(self._task_table.rowCount()):
                name_item = self._task_table.item(row, 0)
                if name_item and name_item.data(Qt.ItemDataRole.UserRole) == task_id:
                    status_item = self._task_table.item(row, 3)
                    if status_item:
                        status_item.setText(status.value)
                    
                    # 更新行颜色
                    task = None
                    for t in self._tasks:
                        if t.task_id == task_id:
                            task = t
                            task.status = status
                            break
                    
                    if task:
                        self._set_row_color(row, task)
                    break
            
            # 如果是当前选中的任务，更新详情
            if self._selected_task_id == task_id:
                self._show_task_details(task_id)
            
            logger.debug(f"任务状态已更新: {task_id} -> {status.value}")
        except Exception as e:
            logger.error(f"更新任务状态失败: {e}")
    
    # 公共接口方法
    def select_task(self, task_id: str):
        """选择指定任务"""
        try:
            for row in range(self._task_table.rowCount()):
                name_item = self._task_table.item(row, 0)
                if name_item and name_item.data(Qt.ItemDataRole.UserRole) == task_id:
                    self._task_table.selectRow(row)
                    break
        except Exception as e:
            logger.error(f"选择任务失败: {e}")
    
    def clear_selection(self):
        """清除选择"""
        self._task_table.clearSelection()
        self._selected_task_id = None
        self._update_button_states()
        self._show_no_selection_message()
    
    def set_loading_state(self, loading: bool):
        """设置加载状态"""
        self._progress_bar.setVisible(loading)
        if loading:
            self._progress_bar.setRange(0, 0)  # 无限进度条
        else:
            self._progress_bar.setRange(0, 100)
    
    def enable_operations(self, enabled: bool):
        """启用/禁用操作"""
        self._refresh_btn.setEnabled(enabled)
        if not enabled:
            self._start_btn.setEnabled(False)
            self._stop_btn.setEnabled(False)
            self._edit_btn.setEnabled(False)
            self._delete_btn.setEnabled(False)
        else:
            self._update_button_states()
    
    def show_message(self, title: str, message: str, msg_type: str = "info"):
        """显示消息对话框"""
        if msg_type == "error":
            QMessageBox.critical(self, title, message)
        elif msg_type == "warning":
            QMessageBox.warning(self, title, message)
        else:
            QMessageBox.information(self, title, message)
    
    def show_execution_history(self, task_id: str):
        """显示执行历史"""
        try:
            dialog = TaskExecutionHistoryDialog(task_id, self)
            dialog.exec()
        except Exception as e:
            logger.error(f"显示执行历史失败: {e}")
            self.show_message("错误", f"显示执行历史失败: {e}", "error")
    
    # FilterWidget接口实现
    def get_current_filters(self) -> Dict[str, Any]:
        """获取当前过滤条件"""
        return {
            'status': self._status_filter.currentData(),
            'type': self._type_filter.currentData(),
            'priority': self._priority_filter.currentData(),
            'search_text': self._search_input.text().strip()
        }
    
    def clear_filters(self):
        """清除过滤条件"""
        self._clear_filters()
    
    def apply_filters(self, filters: Dict[str, Any]):
        """应用过滤条件"""
        try:
            # 设置过滤控件的值
            if 'status' in filters:
                status = filters['status']
                for i in range(self._status_filter.count()):
                    if self._status_filter.itemData(i) == status:
                        self._status_filter.setCurrentIndex(i)
                        break
            
            if 'type' in filters:
                task_type = filters['type']
                for i in range(self._type_filter.count()):
                    if self._type_filter.itemData(i) == task_type:
                        self._type_filter.setCurrentIndex(i)
                        break
            
            if 'priority' in filters:
                priority = filters['priority']
                for i in range(self._priority_filter.count()):
                    if self._priority_filter.itemData(i) == priority:
                        self._priority_filter.setCurrentIndex(i)
                        break
            
            if 'search_text' in filters:
                self._search_input.setText(filters['search_text'])
            
        except Exception as e:
            logger.error(f"应用过滤条件失败: {e}")