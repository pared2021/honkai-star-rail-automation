"""日志查看器视图模块.

实现日志查看器界面的视图组件。
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QComboBox,
    QPushButton, QLabel, QLineEdit, QCheckBox, QSplitter,
    QGroupBox, QScrollArea, QFrame, QSpinBox, QDateTimeEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QMenu, QAction, QFileDialog, QMessageBox, QProgressBar
)
from PyQt5.QtCore import Qt, pyqtSignal, QDateTime, QTimer
from PyQt5.QtGui import QFont, QTextCursor, QColor, QPalette
from typing import Dict, List, Any, Optional
import json
from datetime import datetime


class LogFilterWidget(QWidget):
    """日志过滤器组件."""
    
    filter_changed = pyqtSignal(dict)  # 过滤条件变化
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.connect_signals()
        
    def setup_ui(self):
        """设置UI."""
        layout = QVBoxLayout(self)
        
        # 过滤器组
        filter_group = QGroupBox("日志过滤")
        filter_layout = QVBoxLayout(filter_group)
        
        # 第一行：级别和来源
        row1_layout = QHBoxLayout()
        
        # 日志级别
        row1_layout.addWidget(QLabel("级别:"))
        self.level_combo = QComboBox()
        self.level_combo.addItems(["全部", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        row1_layout.addWidget(self.level_combo)
        
        # 日志来源
        row1_layout.addWidget(QLabel("来源:"))
        self.source_combo = QComboBox()
        self.source_combo.addItems(["全部", "TaskExecutor", "GameOperator", "UI", "System"])
        row1_layout.addWidget(self.source_combo)
        
        row1_layout.addStretch()
        filter_layout.addLayout(row1_layout)
        
        # 第二行：时间范围
        row2_layout = QHBoxLayout()
        
        # 开始时间
        row2_layout.addWidget(QLabel("开始时间:"))
        self.start_time = QDateTimeEdit()
        self.start_time.setDateTime(QDateTime.currentDateTime().addDays(-1))
        self.start_time.setCalendarPopup(True)
        row2_layout.addWidget(self.start_time)
        
        # 结束时间
        row2_layout.addWidget(QLabel("结束时间:"))
        self.end_time = QDateTimeEdit()
        self.end_time.setDateTime(QDateTime.currentDateTime())
        self.end_time.setCalendarPopup(True)
        row2_layout.addWidget(self.end_time)
        
        row2_layout.addStretch()
        filter_layout.addLayout(row2_layout)
        
        # 第三行：关键词搜索
        row3_layout = QHBoxLayout()
        
        row3_layout.addWidget(QLabel("关键词:"))
        self.keyword_edit = QLineEdit()
        self.keyword_edit.setPlaceholderText("输入搜索关键词...")
        row3_layout.addWidget(self.keyword_edit)
        
        # 区分大小写
        self.case_sensitive_cb = QCheckBox("区分大小写")
        row3_layout.addWidget(self.case_sensitive_cb)
        
        # 正则表达式
        self.regex_cb = QCheckBox("正则表达式")
        row3_layout.addWidget(self.regex_cb)
        
        filter_layout.addLayout(row3_layout)
        
        # 第四行：控制按钮
        row4_layout = QHBoxLayout()
        
        self.apply_filter_btn = QPushButton("应用过滤")
        self.clear_filter_btn = QPushButton("清除过滤")
        self.auto_refresh_cb = QCheckBox("自动刷新")
        
        row4_layout.addWidget(self.apply_filter_btn)
        row4_layout.addWidget(self.clear_filter_btn)
        row4_layout.addWidget(self.auto_refresh_cb)
        row4_layout.addStretch()
        
        filter_layout.addLayout(row4_layout)
        
        layout.addWidget(filter_group)
        
    def connect_signals(self):
        """连接信号."""
        self.apply_filter_btn.clicked.connect(self.apply_filter)
        self.clear_filter_btn.clicked.connect(self.clear_filter)
        self.keyword_edit.returnPressed.connect(self.apply_filter)
        
        # 自动应用过滤
        self.level_combo.currentTextChanged.connect(self.on_filter_changed)
        self.source_combo.currentTextChanged.connect(self.on_filter_changed)
        
    def apply_filter(self):
        """应用过滤器."""
        filter_data = self.get_filter_data()
        self.filter_changed.emit(filter_data)
        
    def clear_filter(self):
        """清除过滤器."""
        self.level_combo.setCurrentText("全部")
        self.source_combo.setCurrentText("全部")
        self.keyword_edit.clear()
        self.case_sensitive_cb.setChecked(False)
        self.regex_cb.setChecked(False)
        self.start_time.setDateTime(QDateTime.currentDateTime().addDays(-1))
        self.end_time.setDateTime(QDateTime.currentDateTime())
        self.apply_filter()
        
    def on_filter_changed(self):
        """过滤条件变化时自动应用."""
        if self.auto_refresh_cb.isChecked():
            self.apply_filter()
            
    def get_filter_data(self) -> Dict[str, Any]:
        """获取过滤条件."""
        return {
            'level': self.level_combo.currentText(),
            'source': self.source_combo.currentText(),
            'start_time': self.start_time.dateTime().toPyDateTime(),
            'end_time': self.end_time.dateTime().toPyDateTime(),
            'keyword': self.keyword_edit.text(),
            'case_sensitive': self.case_sensitive_cb.isChecked(),
            'regex': self.regex_cb.isChecked(),
            'auto_refresh': self.auto_refresh_cb.isChecked()
        }
        
    def set_filter_data(self, filter_data: Dict[str, Any]):
        """设置过滤条件."""
        if 'level' in filter_data:
            self.level_combo.setCurrentText(filter_data['level'])
        if 'source' in filter_data:
            self.source_combo.setCurrentText(filter_data['source'])
        if 'start_time' in filter_data:
            self.start_time.setDateTime(filter_data['start_time'])
        if 'end_time' in filter_data:
            self.end_time.setDateTime(filter_data['end_time'])
        if 'keyword' in filter_data:
            self.keyword_edit.setText(filter_data['keyword'])
        if 'case_sensitive' in filter_data:
            self.case_sensitive_cb.setChecked(filter_data['case_sensitive'])
        if 'regex' in filter_data:
            self.regex_cb.setChecked(filter_data['regex'])
        if 'auto_refresh' in filter_data:
            self.auto_refresh_cb.setChecked(filter_data['auto_refresh'])


class LogDisplayWidget(QWidget):
    """日志显示组件."""
    
    log_selected = pyqtSignal(dict)  # 日志选中
    export_requested = pyqtSignal(list)  # 导出请求
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logs = []
        self.filtered_logs = []
        self.setup_ui()
        self.connect_signals()
        
    def setup_ui(self):
        """设置UI."""
        layout = QVBoxLayout(self)
        
        # 工具栏
        toolbar_layout = QHBoxLayout()
        
        # 显示模式
        toolbar_layout.addWidget(QLabel("显示模式:"))
        self.display_mode_combo = QComboBox()
        self.display_mode_combo.addItems(["表格", "文本"])
        toolbar_layout.addWidget(self.display_mode_combo)
        
        # 最大显示行数
        toolbar_layout.addWidget(QLabel("最大行数:"))
        self.max_lines_spin = QSpinBox()
        self.max_lines_spin.setRange(100, 10000)
        self.max_lines_spin.setValue(1000)
        toolbar_layout.addWidget(self.max_lines_spin)
        
        # 控制按钮
        self.clear_btn = QPushButton("清空")
        self.export_btn = QPushButton("导出")
        self.refresh_btn = QPushButton("刷新")
        
        toolbar_layout.addWidget(self.clear_btn)
        toolbar_layout.addWidget(self.export_btn)
        toolbar_layout.addWidget(self.refresh_btn)
        toolbar_layout.addStretch()
        
        layout.addLayout(toolbar_layout)
        
        # 日志显示区域
        self.display_stack = QWidget()
        display_layout = QVBoxLayout(self.display_stack)
        
        # 表格视图
        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(5)
        self.table_widget.setHorizontalHeaderLabels(["时间", "级别", "来源", "消息", "详情"])
        
        # 设置表格属性
        header = self.table_widget.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        
        self.table_widget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_widget.setAlternatingRowColors(True)
        
        # 文本视图
        self.text_widget = QTextEdit()
        self.text_widget.setReadOnly(True)
        self.text_widget.setFont(QFont("Consolas", 9))
        
        display_layout.addWidget(self.table_widget)
        display_layout.addWidget(self.text_widget)
        
        layout.addWidget(self.display_stack)
        
        # 状态栏
        status_layout = QHBoxLayout()
        
        self.status_label = QLabel("就绪")
        self.log_count_label = QLabel("日志数: 0")
        
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        status_layout.addWidget(self.log_count_label)
        
        layout.addLayout(status_layout)
        
        # 初始显示模式
        self.switch_display_mode("表格")
        
    def connect_signals(self):
        """连接信号."""
        self.display_mode_combo.currentTextChanged.connect(self.switch_display_mode)
        self.clear_btn.clicked.connect(self.clear_logs)
        self.export_btn.clicked.connect(self.export_logs)
        self.refresh_btn.clicked.connect(self.refresh_display)
        self.table_widget.itemSelectionChanged.connect(self.on_table_selection_changed)
        
    def switch_display_mode(self, mode: str):
        """切换显示模式."""
        if mode == "表格":
            self.table_widget.show()
            self.text_widget.hide()
        else:
            self.table_widget.hide()
            self.text_widget.show()
            
    def add_log(self, log_data: Dict[str, Any]):
        """添加日志."""
        self.logs.append(log_data)
        
        # 限制日志数量
        max_lines = self.max_lines_spin.value()
        if len(self.logs) > max_lines:
            self.logs = self.logs[-max_lines:]
            
        self.refresh_display()
        
    def add_logs(self, logs: List[Dict[str, Any]]):
        """批量添加日志."""
        self.logs.extend(logs)
        
        # 限制日志数量
        max_lines = self.max_lines_spin.value()
        if len(self.logs) > max_lines:
            self.logs = self.logs[-max_lines:]
            
        self.refresh_display()
        
    def set_logs(self, logs: List[Dict[str, Any]]):
        """设置日志列表."""
        self.logs = logs.copy()
        self.refresh_display()
        
    def filter_logs(self, filter_data: Dict[str, Any]):
        """过滤日志."""
        self.filtered_logs = []
        
        for log in self.logs:
            if self.match_filter(log, filter_data):
                self.filtered_logs.append(log)
                
        self.refresh_display()
        
    def match_filter(self, log: Dict[str, Any], filter_data: Dict[str, Any]) -> bool:
        """检查日志是否匹配过滤条件."""
        # 级别过滤
        if filter_data.get('level', '全部') != '全部':
            if log.get('level', '') != filter_data['level']:
                return False
                
        # 来源过滤
        if filter_data.get('source', '全部') != '全部':
            if log.get('source', '') != filter_data['source']:
                return False
                
        # 时间过滤
        log_time = log.get('timestamp')
        if log_time:
            if isinstance(log_time, str):
                try:
                    log_time = datetime.fromisoformat(log_time)
                except:
                    pass
                    
            if isinstance(log_time, datetime):
                start_time = filter_data.get('start_time')
                end_time = filter_data.get('end_time')
                
                if start_time and log_time < start_time:
                    return False
                if end_time and log_time > end_time:
                    return False
                    
        # 关键词过滤
        keyword = filter_data.get('keyword', '').strip()
        if keyword:
            message = log.get('message', '')
            case_sensitive = filter_data.get('case_sensitive', False)
            is_regex = filter_data.get('regex', False)
            
            if not case_sensitive:
                keyword = keyword.lower()
                message = message.lower()
                
            if is_regex:
                import re
                try:
                    if not re.search(keyword, message):
                        return False
                except re.error:
                    return False
            else:
                if keyword not in message:
                    return False
                    
        return True
        
    def refresh_display(self):
        """刷新显示."""
        display_logs = self.filtered_logs if self.filtered_logs else self.logs
        
        if self.display_mode_combo.currentText() == "表格":
            self.refresh_table_display(display_logs)
        else:
            self.refresh_text_display(display_logs)
            
        # 更新状态
        self.log_count_label.setText(f"日志数: {len(display_logs)}")
        
    def refresh_table_display(self, logs: List[Dict[str, Any]]):
        """刷新表格显示."""
        self.table_widget.setRowCount(len(logs))
        
        for row, log in enumerate(logs):
            # 时间
            timestamp = log.get('timestamp', '')
            if isinstance(timestamp, datetime):
                timestamp = timestamp.strftime('%Y-%m-%d %H:%M:%S')
            self.table_widget.setItem(row, 0, QTableWidgetItem(str(timestamp)))
            
            # 级别
            level = log.get('level', '')
            level_item = QTableWidgetItem(level)
            
            # 设置级别颜色
            if level == 'ERROR':
                level_item.setBackground(QColor(255, 200, 200))
            elif level == 'WARNING':
                level_item.setBackground(QColor(255, 255, 200))
            elif level == 'DEBUG':
                level_item.setBackground(QColor(200, 200, 255))
                
            self.table_widget.setItem(row, 1, level_item)
            
            # 来源
            self.table_widget.setItem(row, 2, QTableWidgetItem(log.get('source', '')))
            
            # 消息
            self.table_widget.setItem(row, 3, QTableWidgetItem(log.get('message', '')))
            
            # 详情
            details = log.get('details', '')
            if isinstance(details, dict):
                details = json.dumps(details, ensure_ascii=False, indent=2)
            self.table_widget.setItem(row, 4, QTableWidgetItem(str(details)))
            
        # 滚动到底部
        if logs:
            self.table_widget.scrollToBottom()
            
    def refresh_text_display(self, logs: List[Dict[str, Any]]):
        """刷新文本显示."""
        self.text_widget.clear()
        
        for log in logs:
            timestamp = log.get('timestamp', '')
            if isinstance(timestamp, datetime):
                timestamp = timestamp.strftime('%Y-%m-%d %H:%M:%S')
                
            level = log.get('level', '')
            source = log.get('source', '')
            message = log.get('message', '')
            
            log_line = f"[{timestamp}] [{level}] [{source}] {message}"
            
            # 设置颜色
            cursor = self.text_widget.textCursor()
            cursor.movePosition(QTextCursor.End)
            
            if level == 'ERROR':
                self.text_widget.setTextColor(QColor(255, 0, 0))
            elif level == 'WARNING':
                self.text_widget.setTextColor(QColor(255, 165, 0))
            elif level == 'DEBUG':
                self.text_widget.setTextColor(QColor(128, 128, 128))
            else:
                self.text_widget.setTextColor(QColor(0, 0, 0))
                
            self.text_widget.append(log_line)
            
        # 滚动到底部
        if logs:
            self.text_widget.moveCursor(QTextCursor.End)
            
    def clear_logs(self):
        """清空日志."""
        self.logs.clear()
        self.filtered_logs.clear()
        self.refresh_display()
        
    def export_logs(self):
        """导出日志."""
        display_logs = self.filtered_logs if self.filtered_logs else self.logs
        if display_logs:
            self.export_requested.emit(display_logs)
        else:
            QMessageBox.information(self, "提示", "没有可导出的日志")
            
    def on_table_selection_changed(self):
        """表格选择变化."""
        current_row = self.table_widget.currentRow()
        if current_row >= 0:
            display_logs = self.filtered_logs if self.filtered_logs else self.logs
            if current_row < len(display_logs):
                self.log_selected.emit(display_logs[current_row])
                
    def get_selected_log(self) -> Optional[Dict[str, Any]]:
        """获取选中的日志."""
        current_row = self.table_widget.currentRow()
        if current_row >= 0:
            display_logs = self.filtered_logs if self.filtered_logs else self.logs
            if current_row < len(display_logs):
                return display_logs[current_row]
        return None


class LogDetailWidget(QWidget):
    """日志详情组件."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """设置UI."""
        layout = QVBoxLayout(self)
        
        # 详情组
        detail_group = QGroupBox("日志详情")
        detail_layout = QVBoxLayout(detail_group)
        
        # 详情文本
        self.detail_text = QTextEdit()
        self.detail_text.setReadOnly(True)
        self.detail_text.setFont(QFont("Consolas", 9))
        detail_layout.addWidget(self.detail_text)
        
        layout.addWidget(detail_group)
        
    def show_log_detail(self, log_data: Dict[str, Any]):
        """显示日志详情."""
        detail_text = ""
        
        # 基本信息
        detail_text += "=== 基本信息 ===\n"
        detail_text += f"时间: {log_data.get('timestamp', '')}\n"
        detail_text += f"级别: {log_data.get('level', '')}\n"
        detail_text += f"来源: {log_data.get('source', '')}\n"
        detail_text += f"消息: {log_data.get('message', '')}\n\n"
        
        # 详细信息
        details = log_data.get('details')
        if details:
            detail_text += "=== 详细信息 ===\n"
            if isinstance(details, dict):
                detail_text += json.dumps(details, ensure_ascii=False, indent=2)
            else:
                detail_text += str(details)
            detail_text += "\n\n"
            
        # 堆栈信息
        stack_trace = log_data.get('stack_trace')
        if stack_trace:
            detail_text += "=== 堆栈信息 ===\n"
            detail_text += str(stack_trace)
            detail_text += "\n\n"
            
        # 上下文信息
        context = log_data.get('context')
        if context:
            detail_text += "=== 上下文信息 ===\n"
            if isinstance(context, dict):
                detail_text += json.dumps(context, ensure_ascii=False, indent=2)
            else:
                detail_text += str(context)
                
        self.detail_text.setPlainText(detail_text)
        
    def clear_detail(self):
        """清空详情."""
        self.detail_text.clear()


class LogViewerView(QWidget):
    """日志查看器主视图."""
    
    # 信号定义
    filter_changed = pyqtSignal(dict)
    log_selected = pyqtSignal(dict)
    export_requested = pyqtSignal(list)
    refresh_requested = pyqtSignal()
    clear_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.connect_signals()
        
        # 自动刷新定时器
        self.auto_refresh_timer = QTimer()
        self.auto_refresh_timer.timeout.connect(self.on_auto_refresh)
        
    def setup_ui(self):
        """设置UI."""
        layout = QVBoxLayout(self)
        
        # 创建分割器
        main_splitter = QSplitter(Qt.Vertical)
        
        # 过滤器组件
        self.filter_widget = LogFilterWidget()
        main_splitter.addWidget(self.filter_widget)
        
        # 内容分割器
        content_splitter = QSplitter(Qt.Horizontal)
        
        # 日志显示组件
        self.display_widget = LogDisplayWidget()
        content_splitter.addWidget(self.display_widget)
        
        # 详情组件
        self.detail_widget = LogDetailWidget()
        content_splitter.addWidget(self.detail_widget)
        
        # 设置分割器比例
        content_splitter.setSizes([700, 300])
        
        main_splitter.addWidget(content_splitter)
        main_splitter.setSizes([150, 600])
        
        layout.addWidget(main_splitter)
        
    def connect_signals(self):
        """连接信号."""
        # 过滤器信号
        self.filter_widget.filter_changed.connect(self.on_filter_changed)
        
        # 显示组件信号
        self.display_widget.log_selected.connect(self.on_log_selected)
        self.display_widget.export_requested.connect(self.export_requested.emit)
        
        # 刷新按钮
        self.display_widget.refresh_btn.clicked.connect(self.refresh_requested.emit)
        self.display_widget.clear_btn.clicked.connect(self.clear_requested.emit)
        
    def on_filter_changed(self, filter_data: Dict[str, Any]):
        """处理过滤条件变化."""
        # 应用过滤
        self.display_widget.filter_logs(filter_data)
        
        # 设置自动刷新
        if filter_data.get('auto_refresh', False):
            self.auto_refresh_timer.start(5000)  # 5秒刷新一次
        else:
            self.auto_refresh_timer.stop()
            
        self.filter_changed.emit(filter_data)
        
    def on_log_selected(self, log_data: Dict[str, Any]):
        """处理日志选择."""
        self.detail_widget.show_log_detail(log_data)
        self.log_selected.emit(log_data)
        
    def on_auto_refresh(self):
        """自动刷新."""
        self.refresh_requested.emit()
        
    def add_log(self, log_data: Dict[str, Any]):
        """添加日志."""
        self.display_widget.add_log(log_data)
        
    def add_logs(self, logs: List[Dict[str, Any]]):
        """批量添加日志."""
        self.display_widget.add_logs(logs)
        
    def set_logs(self, logs: List[Dict[str, Any]]):
        """设置日志列表."""
        self.display_widget.set_logs(logs)
        
    def clear_logs(self):
        """清空日志."""
        self.display_widget.clear_logs()
        self.detail_widget.clear_detail()
        
    def get_filter_data(self) -> Dict[str, Any]:
        """获取过滤条件."""
        return self.filter_widget.get_filter_data()
        
    def set_filter_data(self, filter_data: Dict[str, Any]):
        """设置过滤条件."""
        self.filter_widget.set_filter_data(filter_data)
        
    def get_selected_log(self) -> Optional[Dict[str, Any]]:
        """获取选中的日志."""
        return self.display_widget.get_selected_log()
        
    def update_status(self, message: str):
        """更新状态."""
        self.display_widget.status_label.setText(message)
        
    def cleanup(self):
        """清理资源."""
        self.auto_refresh_timer.stop()
