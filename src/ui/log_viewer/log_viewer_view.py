"""日志查看器View层

该模块定义了日志查看器的视图层，负责UI界面的展示和用户交互。
"""

import re
from datetime import datetime
from typing import Dict, Any, List, Optional
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import (
    QColor, QFont, QSyntaxHighlighter, QTextCharFormat, 
    QTextCursor, QTextDocument
)
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
    QComboBox, QLineEdit, QCheckBox, QPushButton, QSpinBox,
    QSplitter, QGroupBox, QTreeWidget, QTreeWidgetItem,
    QFileDialog, QMessageBox, QProgressBar
)

from src.ui.common.ui_components import MVPFilterWidget as FilterWidget
from src.utils.logger import logger


class LogHighlighter(QSyntaxHighlighter):
    """日志语法高亮器"""
    
    def __init__(self, parent: QTextDocument):
        super().__init__(parent)
        self._setup_highlighting_rules()
    
    def _setup_highlighting_rules(self):
        """设置高亮规则"""
        self.highlighting_rules = []
        
        # 错误级别 - 红色
        error_format = QTextCharFormat()
        error_format.setForeground(QColor(220, 50, 47))  # 红色
        error_format.setFontWeight(QFont.Weight.Bold)
        self.highlighting_rules.append((r"\bERROR\b|\bCRITICAL\b", error_format))
        
        # 警告级别 - 橙色
        warning_format = QTextCharFormat()
        warning_format.setForeground(QColor(255, 165, 0))  # 橙色
        warning_format.setFontWeight(QFont.Weight.Bold)
        self.highlighting_rules.append((r"\bWARNING\b|\bWARN\b", warning_format))
        
        # 信息级别 - 蓝色
        info_format = QTextCharFormat()
        info_format.setForeground(QColor(38, 139, 210))  # 蓝色
        self.highlighting_rules.append((r"\bINFO\b", info_format))
        
        # 调试级别 - 灰色
        debug_format = QTextCharFormat()
        debug_format.setForeground(QColor(128, 128, 128))  # 灰色
        self.highlighting_rules.append((r"\bDEBUG\b|\bTRACE\b", debug_format))
        
        # 成功信息 - 绿色
        success_format = QTextCharFormat()
        success_format.setForeground(QColor(0, 128, 0))  # 绿色
        success_format.setFontWeight(QFont.Weight.Bold)
        self.highlighting_rules.append((r"成功|完成|SUCCESS|COMPLETE", success_format))
        
        # 时间戳 - 深灰色
        timestamp_format = QTextCharFormat()
        timestamp_format.setForeground(QColor(100, 100, 100))
        self.highlighting_rules.append(
            (r"\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}", timestamp_format)
        )
        
        # 文件路径 - 紫色
        path_format = QTextCharFormat()
        path_format.setForeground(QColor(128, 0, 128))
        self.highlighting_rules.append((r"[A-Za-z]:\\[^\s]+|/[^\s]+", path_format))
        
        # 数字 - 青色
        number_format = QTextCharFormat()
        number_format.setForeground(QColor(0, 128, 128))
        self.highlighting_rules.append((r"\b\d+\.?\d*\b", number_format))
    
    def highlightBlock(self, text: str):
        """高亮文本块"""
        for pattern, format_obj in self.highlighting_rules:
            expression = re.compile(pattern, re.IGNORECASE)
            for match in expression.finditer(text):
                start = match.start()
                length = match.end() - start
                self.setFormat(start, length, format_obj)


class LogViewerView(FilterWidget):
    """日志查看器视图层"""
    
    # 用户交互信号
    level_filter_changed = pyqtSignal(str)  # 级别过滤变化
    search_filter_changed = pyqtSignal(str)  # 搜索过滤变化
    realtime_monitoring_toggled = pyqtSignal(bool)  # 实时监控切换
    auto_scroll_toggled = pyqtSignal(bool)  # 自动滚动切换
    max_lines_changed = pyqtSignal(int)  # 最大行数变化
    font_size_changed = pyqtSignal(int)  # 字体大小变化
    theme_changed = pyqtSignal(str)  # 主题变化
    
    # 操作请求信号
    clear_logs_requested = pyqtSignal()  # 清空日志请求
    export_logs_requested = pyqtSignal(str)  # 导出日志请求
    open_file_requested = pyqtSignal(str)  # 打开文件请求
    refresh_requested = pyqtSignal()  # 刷新请求
    file_selected = pyqtSignal(str)  # 文件选择
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # UI组件
        self.log_text_edit: Optional[QTextEdit] = None
        self.level_filter_combo: Optional[QComboBox] = None
        self.search_edit: Optional[QLineEdit] = None
        self.realtime_check: Optional[QCheckBox] = None
        self.auto_scroll_check: Optional[QCheckBox] = None
        self.max_lines_spin: Optional[QSpinBox] = None
        self.font_size_spin: Optional[QSpinBox] = None
        self.theme_combo: Optional[QComboBox] = None
        self.stats_label: Optional[QLabel] = None
        self.current_file_label: Optional[QLabel] = None
        self.file_tree: Optional[QTreeWidget] = None
        self.status_label: Optional[QLabel] = None
        self.line_count_label: Optional[QLabel] = None
        self.monitoring_status_label: Optional[QLabel] = None
        self.clear_button: Optional[QPushButton] = None
        self.export_button: Optional[QPushButton] = None
        self.open_file_button: Optional[QPushButton] = None
        self.refresh_button: Optional[QPushButton] = None
        
        # 语法高亮器
        self.highlighter: Optional[LogHighlighter] = None
        
        # 状态
        self.loading = False
        
        self._init_ui()
        self._connect_signals()
        
        logger.info("日志查看器View初始化完成")
    
    def _init_ui(self):
        """初始化用户界面"""
        layout = self.create_vbox_layout()
        self.setLayout(layout)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # 标题和控制区域
        header_layout = self._create_header_layout()
        layout.addLayout(header_layout)
        
        # 主要内容区域
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧：日志显示区域
        log_widget = self._create_log_display_widget()
        main_splitter.addWidget(log_widget)
        
        # 右侧：统计和控制面板
        control_widget = self._create_control_panel()
        main_splitter.addWidget(control_widget)
        
        # 设置分割比例
        main_splitter.setSizes([700, 300])
        layout.addWidget(main_splitter)
        
        # 状态栏
        status_layout = self._create_status_layout()
        layout.addLayout(status_layout)
    
    def _create_header_layout(self) -> QHBoxLayout:
        """创建头部布局"""
        layout = self.create_hbox_layout()
        
        # 标题
        title_label = QLabel("日志查看器")
        title_label.setFont(QFont("Microsoft YaHei", 14, QFont.Weight.Bold))
        layout.addWidget(title_label)
        
        layout.addStretch()
        
        # 日志级别过滤
        level_label, self.level_filter_combo = self.create_filter_combo(
            "级别过滤", [("全部", "all"), ("ERROR", "error"), ("WARNING", "warning"), 
                        ("INFO", "info"), ("DEBUG", "debug")]
        )
        layout.addWidget(level_label)
        layout.addWidget(self.level_filter_combo)
        
        # 搜索框
        layout.addWidget(QLabel("搜索:"))
        self.search_edit = self.create_search_edit("输入关键词搜索...")
        self.search_edit.setMaximumWidth(200)
        layout.addWidget(self.search_edit)
        
        # 实时监控开关
        self.realtime_check = QCheckBox("实时监控")
        self.realtime_check.setChecked(True)
        layout.addWidget(self.realtime_check)
        
        return layout
    
    def _create_log_display_widget(self) -> QWidget:
        """创建日志显示组件"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 日志文本显示区域
        self.log_text_edit = QTextEdit()
        self.log_text_edit.setFont(QFont("Consolas", 9))
        self.log_text_edit.setReadOnly(True)
        self.log_text_edit.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        
        # 设置语法高亮
        self.highlighter = LogHighlighter(self.log_text_edit.document())
        
        layout.addWidget(self.log_text_edit)
        
        # 日志控制按钮
        button_layout = QHBoxLayout()
        
        self.auto_scroll_check = QCheckBox("自动滚动")
        self.auto_scroll_check.setChecked(True)
        button_layout.addWidget(self.auto_scroll_check)
        
        button_layout.addStretch()
        
        self.clear_button = self.create_button("清空日志")
        button_layout.addWidget(self.clear_button)
        
        self.export_button = self.create_button("导出日志")
        button_layout.addWidget(self.export_button)
        
        layout.addLayout(button_layout)
        
        return widget
    
    def _create_control_panel(self) -> QWidget:
        """创建控制面板"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 统计信息组
        stats_group = QGroupBox("统计信息")
        stats_layout = QVBoxLayout(stats_group)
        
        self.stats_label = QLabel("暂无统计数据")
        self.stats_label.setFont(QFont("Consolas", 8))
        self.stats_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.stats_label.setWordWrap(True)
        stats_layout.addWidget(self.stats_label)
        
        layout.addWidget(stats_group)
        
        # 日志文件管理组
        file_group = QGroupBox("文件管理")
        file_layout = QVBoxLayout(file_group)
        
        # 当前日志文件
        self.current_file_label = QLabel("当前文件: 无")
        self.current_file_label.setWordWrap(True)
        file_layout.addWidget(self.current_file_label)
        
        # 文件操作按钮
        file_button_layout = QHBoxLayout()
        
        self.open_file_button = QPushButton("打开文件")
        file_button_layout.addWidget(self.open_file_button)
        
        self.refresh_button = QPushButton("刷新")
        file_button_layout.addWidget(self.refresh_button)
        
        file_layout.addLayout(file_button_layout)
        
        # 日志文件列表
        self.file_tree = QTreeWidget()
        self.file_tree.setHeaderLabels(["日志文件", "大小", "修改时间"])
        file_layout.addWidget(self.file_tree)
        
        layout.addWidget(file_group)
        
        # 设置组
        settings_group = QGroupBox("显示设置")
        settings_layout = QVBoxLayout(settings_group)
        
        # 最大行数设置
        max_lines_layout = QHBoxLayout()
        max_lines_layout.addWidget(QLabel("最大行数:"))
        self.max_lines_spin = QSpinBox()
        self.max_lines_spin.setRange(1000, 100000)
        self.max_lines_spin.setValue(10000)
        max_lines_layout.addWidget(self.max_lines_spin)
        settings_layout.addLayout(max_lines_layout)
        
        # 字体大小设置
        font_size_layout = QHBoxLayout()
        font_size_layout.addWidget(QLabel("字体大小:"))
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 16)
        self.font_size_spin.setValue(9)
        font_size_layout.addWidget(self.font_size_spin)
        settings_layout.addLayout(font_size_layout)
        
        # 颜色主题
        theme_layout = QHBoxLayout()
        theme_layout.addWidget(QLabel("主题:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["默认", "深色", "高对比度"])
        theme_layout.addWidget(self.theme_combo)
        settings_layout.addLayout(theme_layout)
        
        layout.addWidget(settings_group)
        
        layout.addStretch()
        
        return widget
    
    def _create_status_layout(self) -> QHBoxLayout:
        """创建状态栏布局"""
        layout = QHBoxLayout()
        
        self.status_label = QLabel("就绪")
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        
        self.line_count_label = QLabel("行数: 0")
        layout.addWidget(self.line_count_label)
        
        self.monitoring_status_label = QLabel("● 监控中")
        self.monitoring_status_label.setStyleSheet("color: green;")
        layout.addWidget(self.monitoring_status_label)
        
        return layout
    
    def _connect_signals(self):
        """连接信号与槽"""
        # 过滤器信号
        self.level_filter_combo.currentTextChanged.connect(self.level_filter_changed.emit)
        self.search_edit.textChanged.connect(self.search_filter_changed.emit)
        
        # 控制信号
        self.realtime_check.toggled.connect(self.realtime_monitoring_toggled.emit)
        self.auto_scroll_check.toggled.connect(self.auto_scroll_toggled.emit)
        
        # 设置信号
        self.max_lines_spin.valueChanged.connect(self.max_lines_changed.emit)
        self.font_size_spin.valueChanged.connect(self.font_size_changed.emit)
        self.theme_combo.currentTextChanged.connect(self.theme_changed.emit)
        
        # 按钮信号
        self.clear_button.clicked.connect(self._on_clear_logs_clicked)
        self.export_button.clicked.connect(self._on_export_logs_clicked)
        self.open_file_button.clicked.connect(self._on_open_file_clicked)
        self.refresh_button.clicked.connect(self.refresh_requested.emit)
        
        # 文件树信号
        self.file_tree.itemDoubleClicked.connect(self._on_file_tree_item_clicked)
    
    def _on_clear_logs_clicked(self):
        """清空日志按钮点击处理"""
        reply = QMessageBox.question(
            self,
            "确认清空",
            "确定要清空当前显示的日志吗？\n\n此操作不会删除日志文件。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.clear_logs_requested.emit()
    
    def _on_export_logs_clicked(self):
        """导出日志按钮点击处理"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "导出日志",
            f"logs_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "文本文件 (*.txt);;所有文件 (*.*)",
        )
        
        if file_path:
            self.export_logs_requested.emit(file_path)
    
    def _on_open_file_clicked(self):
        """打开文件按钮点击处理"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择日志文件", "logs", "日志文件 (*.log *.txt);;所有文件 (*.*)"
        )
        
        if file_path:
            self.open_file_requested.emit(file_path)
    
    def _on_file_tree_item_clicked(self, item: QTreeWidgetItem, column: int):
        """文件树项目点击处理"""
        file_path = item.data(0, Qt.ItemDataRole.UserRole)
        if file_path:
            self.file_selected.emit(file_path)
    
    # 数据更新方法
    def append_log_line(self, line: str):
        """添加日志行"""
        try:
            # 检查行数限制
            document = self.log_text_edit.document()
            max_lines = self.max_lines_spin.value()
            
            if document.blockCount() >= max_lines:
                # 删除最旧的行
                cursor = QTextCursor(document)
                cursor.movePosition(QTextCursor.MoveOperation.Start)
                cursor.select(QTextCursor.SelectionType.LineUnderCursor)
                cursor.removeSelectedText()
                cursor.deleteChar()  # 删除换行符
            
            # 添加新行
            self.log_text_edit.append(line)
            
            # 自动滚动到底部
            if self.auto_scroll_check.isChecked():
                scrollbar = self.log_text_edit.verticalScrollBar()
                scrollbar.setValue(scrollbar.maximum())
            
            # 更新行数显示
            self._update_line_count()
            
        except Exception as e:
            logger.error(f"添加日志行失败: {e}")
    
    def clear_log_display(self):
        """清空日志显示"""
        self.log_text_edit.clear()
        self._update_line_count()
    
    def set_log_content(self, content: str):
        """设置日志内容"""
        self.log_text_edit.setPlainText(content)
        self._update_line_count()
    
    def get_log_content(self) -> str:
        """获取日志内容"""
        return self.log_text_edit.toPlainText()
    
    def update_statistics(self, stats: Dict[str, Any]):
        """更新统计信息"""
        stats_text = f"""总行数: {stats['total_lines']}
错误: {stats['error_count']}
警告: {stats['warning_count']}
信息: {stats['info_count']}
调试: {stats['debug_count']}

运行时长: {stats['duration']}
开始时间: {stats['start_time']}
最后更新: {stats['last_update']}"""
        
        self.stats_label.setText(stats_text)
    
    def update_current_file(self, file_path: str):
        """更新当前文件显示"""
        import os
        file_name = os.path.basename(file_path) if file_path else "无"
        self.current_file_label.setText(f"当前文件: {file_name}")
    
    def update_file_list(self, files: List[Dict[str, Any]]):
        """更新文件列表"""
        try:
            self.file_tree.clear()
            
            for file_info in files:
                item = QTreeWidgetItem([
                    file_info["name"],
                    file_info["size"],
                    file_info["modified"]
                ])
                item.setData(0, Qt.ItemDataRole.UserRole, file_info["path"])
                self.file_tree.addTopLevelItem(item)
            
            # 调整列宽
            for i in range(3):
                self.file_tree.resizeColumnToContents(i)
                
        except Exception as e:
            logger.error(f"更新文件列表失败: {e}")
    
    def update_monitoring_status(self, is_monitoring: bool, status_text: str):
        """更新监控状态"""
        if is_monitoring:
            self.monitoring_status_label.setText(f"● {status_text}")
            self.monitoring_status_label.setStyleSheet("color: green;")
        else:
            self.monitoring_status_label.setText(f"○ {status_text}")
            self.monitoring_status_label.setStyleSheet("color: orange;")
    
    def update_theme(self, theme: str):
        """更新主题"""
        if theme == "深色":
            self.log_text_edit.setStyleSheet(
                """
                QTextEdit {
                    background-color: #2b2b2b;
                    color: #ffffff;
                    border: 1px solid #555555;
                }
            """
            )
        elif theme == "高对比度":
            self.log_text_edit.setStyleSheet(
                """
                QTextEdit {
                    background-color: #000000;
                    color: #ffffff;
                    border: 2px solid #ffffff;
                }
            """
            )
        else:  # 默认主题
            self.log_text_edit.setStyleSheet("")
    
    def update_font_size(self, size: int):
        """更新字体大小"""
        font = self.log_text_edit.font()
        font.setPointSize(size)
        self.log_text_edit.setFont(font)
    
    def _update_line_count(self):
        """更新行数显示"""
        line_count = self.log_text_edit.document().blockCount()
        self.line_count_label.setText(f"行数: {line_count}")
    
    # 状态控制
    def set_loading_state(self, loading: bool):
        """设置加载状态"""
        self.loading = loading
        
        # 禁用/启用相关控件
        self.open_file_button.setEnabled(not loading)
        self.refresh_button.setEnabled(not loading)
        self.clear_button.setEnabled(not loading)
        self.export_button.setEnabled(not loading)
        
        if loading:
            self.status_label.setText("加载中...")
        else:
            self.status_label.setText("就绪")
    
    def set_enabled_state(self, enabled: bool):
        """设置启用状态"""
        self.setEnabled(enabled)
    
    # 消息显示
    def show_message(self, title: str, message: str, msg_type: str = "info"):
        """显示消息"""
        if msg_type == "error":
            QMessageBox.critical(self, title, message)
        elif msg_type == "warning":
            QMessageBox.warning(self, title, message)
        else:
            QMessageBox.information(self, title, message)
    
    def show_confirmation(self, title: str, message: str) -> bool:
        """显示确认对话框"""
        reply = QMessageBox.question(
            self, title, message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        return reply == QMessageBox.StandardButton.Yes
    
    # 获取当前设置
    def get_current_level_filter(self) -> str:
        """获取当前级别过滤"""
        return self.level_filter_combo.currentText()
    
    def get_current_search_filter(self) -> str:
        """获取当前搜索过滤"""
        return self.search_edit.text()
    
    def get_current_max_lines(self) -> int:
        """获取当前最大行数"""
        return self.max_lines_spin.value()
    
    def get_current_font_size(self) -> int:
        """获取当前字体大小"""
        return self.font_size_spin.value()
    
    def get_current_theme(self) -> str:
        """获取当前主题"""
        return self.theme_combo.currentText()
    
    def is_auto_scroll_enabled(self) -> bool:
        """是否启用自动滚动"""
        return self.auto_scroll_check.isChecked()
    
    def is_realtime_monitoring_enabled(self) -> bool:
        """是否启用实时监控"""
        return self.realtime_check.isChecked()
    
    # 设置控件值
    def set_level_filter(self, level: str):
        """设置级别过滤"""
        index = self.level_filter_combo.findText(level)
        if index >= 0:
            self.level_filter_combo.setCurrentIndex(index)
    
    def set_search_filter(self, text: str):
        """设置搜索过滤"""
        self.search_edit.setText(text)
    
    def set_max_lines(self, max_lines: int):
        """设置最大行数"""
        self.max_lines_spin.setValue(max_lines)
    
    def set_font_size(self, size: int):
        """设置字体大小"""
        self.font_size_spin.setValue(size)
    
    def set_theme(self, theme: str):
        """设置主题"""
        index = self.theme_combo.findText(theme)
        if index >= 0:
            self.theme_combo.setCurrentIndex(index)
    
    def set_auto_scroll(self, enabled: bool):
        """设置自动滚动"""
        self.auto_scroll_check.setChecked(enabled)
    
    def set_realtime_monitoring(self, enabled: bool):
        """设置实时监控"""
        self.realtime_check.setChecked(enabled)
    
    def cleanup(self):
        """清理资源"""
        try:
            logger.info("日志查看器View清理完成")
        except Exception as e:
            logger.error(f"清理资源失败: {e}")