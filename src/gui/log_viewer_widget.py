from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
    QLabel, QPushButton, QComboBox, QCheckBox,
    QGroupBox, QSpinBox, QLineEdit, QSplitter,
    QTreeWidget, QTreeWidgetItem, QTabWidget,
    QMessageBox, QFileDialog, QProgressBar,
    QFrame, QScrollArea
)
from PyQt6.QtCore import (
    Qt, pyqtSignal, QTimer, QThread, pyqtSlot,
    QDateTime, QFileSystemWatcher
)
from PyQt6.QtGui import (
    QFont, QTextCursor, QColor, QTextCharFormat,
    QSyntaxHighlighter, QTextDocument, QPalette
)
import os
import re
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from loguru import logger
import threading
from pathlib import Path


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
        self.highlighting_rules.append((r'\bERROR\b|\bCRITICAL\b', error_format))
        
        # 警告级别 - 橙色
        warning_format = QTextCharFormat()
        warning_format.setForeground(QColor(255, 165, 0))  # 橙色
        warning_format.setFontWeight(QFont.Weight.Bold)
        self.highlighting_rules.append((r'\bWARNING\b|\bWARN\b', warning_format))
        
        # 信息级别 - 蓝色
        info_format = QTextCharFormat()
        info_format.setForeground(QColor(38, 139, 210))  # 蓝色
        self.highlighting_rules.append((r'\bINFO\b', info_format))
        
        # 调试级别 - 灰色
        debug_format = QTextCharFormat()
        debug_format.setForeground(QColor(128, 128, 128))  # 灰色
        self.highlighting_rules.append((r'\bDEBUG\b|\bTRACE\b', debug_format))
        
        # 成功信息 - 绿色
        success_format = QTextCharFormat()
        success_format.setForeground(QColor(0, 128, 0))  # 绿色
        success_format.setFontWeight(QFont.Weight.Bold)
        self.highlighting_rules.append((r'成功|完成|SUCCESS|COMPLETE', success_format))
        
        # 时间戳 - 深灰色
        timestamp_format = QTextCharFormat()
        timestamp_format.setForeground(QColor(100, 100, 100))
        self.highlighting_rules.append((r'\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}', timestamp_format))
        
        # 文件路径 - 紫色
        path_format = QTextCharFormat()
        path_format.setForeground(QColor(128, 0, 128))
        self.highlighting_rules.append((r'[A-Za-z]:\\[^\s]+|/[^\s]+', path_format))
        
        # 数字 - 青色
        number_format = QTextCharFormat()
        number_format.setForeground(QColor(0, 128, 128))
        self.highlighting_rules.append((r'\b\d+\.?\d*\b', number_format))
    
    def highlightBlock(self, text: str):
        """高亮文本块"""
        for pattern, format_obj in self.highlighting_rules:
            expression = re.compile(pattern, re.IGNORECASE)
            for match in expression.finditer(text):
                start = match.start()
                length = match.end() - start
                self.setFormat(start, length, format_obj)


class LogFileWatcher(QThread):
    """日志文件监控线程"""
    
    new_log_line = pyqtSignal(str)
    
    def __init__(self, log_file_path: str):
        super().__init__()
        self.log_file_path = log_file_path
        self.running = False
        self.last_position = 0
    
    def run(self):
        """运行监控"""
        self.running = True
        
        # 获取初始文件大小
        if os.path.exists(self.log_file_path):
            self.last_position = os.path.getsize(self.log_file_path)
        
        while self.running:
            try:
                if os.path.exists(self.log_file_path):
                    current_size = os.path.getsize(self.log_file_path)
                    
                    if current_size > self.last_position:
                        with open(self.log_file_path, 'r', encoding='utf-8') as f:
                            f.seek(self.last_position)
                            new_lines = f.read()
                            
                            for line in new_lines.strip().split('\n'):
                                if line.strip():
                                    self.new_log_line.emit(line)
                        
                        self.last_position = current_size
                
                self.msleep(500)  # 500ms检查一次
                
            except Exception as e:
                logger.error(f"日志文件监控错误: {e}")
                self.msleep(1000)
    
    def stop(self):
        """停止监控"""
        self.running = False
        self.wait()


class LogStatistics:
    """日志统计信息"""
    
    def __init__(self):
        self.reset()
    
    def reset(self):
        """重置统计"""
        self.total_lines = 0
        self.error_count = 0
        self.warning_count = 0
        self.info_count = 0
        self.debug_count = 0
        self.start_time = datetime.now()
        self.last_update = datetime.now()
    
    def update(self, log_line: str):
        """更新统计"""
        self.total_lines += 1
        self.last_update = datetime.now()
        
        line_upper = log_line.upper()
        if 'ERROR' in line_upper or 'CRITICAL' in line_upper:
            self.error_count += 1
        elif 'WARNING' in line_upper or 'WARN' in line_upper:
            self.warning_count += 1
        elif 'INFO' in line_upper:
            self.info_count += 1
        elif 'DEBUG' in line_upper or 'TRACE' in line_upper:
            self.debug_count += 1
    
    def get_summary(self) -> Dict[str, Any]:
        """获取统计摘要"""
        duration = self.last_update - self.start_time
        return {
            'total_lines': self.total_lines,
            'error_count': self.error_count,
            'warning_count': self.warning_count,
            'info_count': self.info_count,
            'debug_count': self.debug_count,
            'duration': str(duration).split('.')[0],  # 去掉微秒
            'start_time': self.start_time.strftime('%H:%M:%S'),
            'last_update': self.last_update.strftime('%H:%M:%S')
        }


class LogViewerWidget(QWidget):
    """增强的日志查看器组件"""
    
    # 信号定义
    log_exported = pyqtSignal(str)  # 日志导出完成
    log_cleared = pyqtSignal()  # 日志清空
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.log_watcher = None
        self.statistics = LogStatistics()
        self.max_lines = 10000  # 最大显示行数
        self.auto_scroll = True
        self.current_log_file = None
        
        self._init_ui()
        self._setup_log_monitoring()
        self._start_statistics_timer()
    
    def _init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout(self)
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
        layout = QHBoxLayout()
        
        # 标题
        title_label = QLabel("日志查看器")
        title_label.setFont(QFont("Microsoft YaHei", 14, QFont.Weight.Bold))
        layout.addWidget(title_label)
        
        layout.addStretch()
        
        # 日志级别过滤
        layout.addWidget(QLabel("级别过滤:"))
        self.level_filter_combo = QComboBox()
        self.level_filter_combo.addItems(["全部", "ERROR", "WARNING", "INFO", "DEBUG"])
        self.level_filter_combo.currentTextChanged.connect(self._apply_level_filter)
        layout.addWidget(self.level_filter_combo)
        
        # 搜索框
        layout.addWidget(QLabel("搜索:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("输入关键词搜索...")
        self.search_edit.textChanged.connect(self._apply_search_filter)
        self.search_edit.setMaximumWidth(200)
        layout.addWidget(self.search_edit)
        
        # 实时监控开关
        self.realtime_check = QCheckBox("实时监控")
        self.realtime_check.setChecked(True)
        self.realtime_check.toggled.connect(self._toggle_realtime_monitoring)
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
        self.auto_scroll_check.toggled.connect(self._toggle_auto_scroll)
        button_layout.addWidget(self.auto_scroll_check)
        
        button_layout.addStretch()
        
        self.clear_button = QPushButton("清空日志")
        self.clear_button.clicked.connect(self._clear_logs)
        button_layout.addWidget(self.clear_button)
        
        self.export_button = QPushButton("导出日志")
        self.export_button.clicked.connect(self._export_logs)
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
        self.open_file_button.clicked.connect(self._open_log_file)
        file_button_layout.addWidget(self.open_file_button)
        
        self.refresh_button = QPushButton("刷新")
        self.refresh_button.clicked.connect(self._refresh_logs)
        file_button_layout.addWidget(self.refresh_button)
        
        file_layout.addLayout(file_button_layout)
        
        # 日志文件列表
        self.file_tree = QTreeWidget()
        self.file_tree.setHeaderLabels(["日志文件", "大小", "修改时间"])
        self.file_tree.itemDoubleClicked.connect(self._on_file_selected)
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
        self.max_lines_spin.setValue(self.max_lines)
        self.max_lines_spin.valueChanged.connect(self._update_max_lines)
        max_lines_layout.addWidget(self.max_lines_spin)
        settings_layout.addLayout(max_lines_layout)
        
        # 字体大小设置
        font_size_layout = QHBoxLayout()
        font_size_layout.addWidget(QLabel("字体大小:"))
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 16)
        self.font_size_spin.setValue(9)
        self.font_size_spin.valueChanged.connect(self._update_font_size)
        font_size_layout.addWidget(self.font_size_spin)
        settings_layout.addLayout(font_size_layout)
        
        # 颜色主题
        theme_layout = QHBoxLayout()
        theme_layout.addWidget(QLabel("主题:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["默认", "深色", "高对比度"])
        self.theme_combo.currentTextChanged.connect(self._change_theme)
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
    
    def _setup_log_monitoring(self):
        """设置日志监控"""
        # 默认监控应用日志文件
        log_dir = Path("logs")
        if log_dir.exists():
            log_files = list(log_dir.glob("*.log"))
            if log_files:
                # 选择最新的日志文件
                latest_log = max(log_files, key=lambda f: f.stat().st_mtime)
                self._start_monitoring(str(latest_log))
        
        # 刷新日志文件列表
        self._refresh_file_list()
    
    def _start_monitoring(self, log_file_path: str):
        """开始监控日志文件"""
        try:
            # 停止之前的监控
            if self.log_watcher:
                self.log_watcher.stop()
            
            # 创建新的监控线程
            self.log_watcher = LogFileWatcher(log_file_path)
            self.log_watcher.new_log_line.connect(self._append_log_line)
            
            if self.realtime_check.isChecked():
                self.log_watcher.start()
            
            self.current_log_file = log_file_path
            self.current_file_label.setText(f"当前文件: {os.path.basename(log_file_path)}")
            
            # 加载现有日志内容
            self._load_existing_logs(log_file_path)
            
            logger.info(f"开始监控日志文件: {log_file_path}")
            
        except Exception as e:
            logger.error(f"启动日志监控失败: {e}")
            QMessageBox.warning(self, "监控失败", f"启动日志监控失败：{str(e)}")
    
    def _load_existing_logs(self, log_file_path: str):
        """加载现有日志内容"""
        try:
            if os.path.exists(log_file_path):
                with open(log_file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    
                    # 只加载最后的max_lines行
                    if len(lines) > self.max_lines:
                        lines = lines[-self.max_lines:]
                    
                    self.log_text_edit.clear()
                    self.statistics.reset()
                    
                    for line in lines:
                        line = line.strip()
                        if line:
                            self._append_log_line(line, update_stats=True)
                    
                    self._update_line_count()
                    
        except Exception as e:
            logger.error(f"加载日志文件失败: {e}")
    
    def _start_statistics_timer(self):
        """启动统计更新定时器"""
        self.stats_timer = QTimer()
        self.stats_timer.timeout.connect(self._update_statistics_display)
        self.stats_timer.start(2000)  # 每2秒更新一次统计
    
    @pyqtSlot(str)
    def _append_log_line(self, line: str, update_stats: bool = True):
        """添加日志行"""
        try:
            # 应用过滤器
            if not self._should_show_line(line):
                return
            
            # 更新统计
            if update_stats:
                self.statistics.update(line)
            
            # 检查行数限制
            document = self.log_text_edit.document()
            if document.blockCount() >= self.max_lines:
                # 删除最旧的行
                cursor = QTextCursor(document)
                cursor.movePosition(QTextCursor.MoveOperation.Start)
                cursor.select(QTextCursor.SelectionType.LineUnderCursor)
                cursor.removeSelectedText()
                cursor.deleteChar()  # 删除换行符
            
            # 添加新行
            self.log_text_edit.append(line)
            
            # 自动滚动到底部
            if self.auto_scroll:
                scrollbar = self.log_text_edit.verticalScrollBar()
                scrollbar.setValue(scrollbar.maximum())
            
            self._update_line_count()
            
        except Exception as e:
            logger.error(f"添加日志行失败: {e}")
    
    def _should_show_line(self, line: str) -> bool:
        """判断是否应该显示该行"""
        # 级别过滤
        level_filter = self.level_filter_combo.currentText()
        if level_filter != "全部":
            if level_filter.upper() not in line.upper():
                return False
        
        # 搜索过滤
        search_text = self.search_edit.text().strip()
        if search_text:
            if search_text.lower() not in line.lower():
                return False
        
        return True
    
    def _apply_level_filter(self):
        """应用级别过滤"""
        self._refresh_display()
    
    def _apply_search_filter(self):
        """应用搜索过滤"""
        self._refresh_display()
    
    def _refresh_display(self):
        """刷新显示"""
        if self.current_log_file:
            self._load_existing_logs(self.current_log_file)
    
    def _toggle_realtime_monitoring(self, enabled: bool):
        """切换实时监控"""
        if self.log_watcher:
            if enabled:
                if not self.log_watcher.isRunning():
                    self.log_watcher.start()
                self.monitoring_status_label.setText("● 监控中")
                self.monitoring_status_label.setStyleSheet("color: green;")
            else:
                if self.log_watcher.isRunning():
                    self.log_watcher.stop()
                self.monitoring_status_label.setText("○ 已暂停")
                self.monitoring_status_label.setStyleSheet("color: orange;")
    
    def _toggle_auto_scroll(self, enabled: bool):
        """切换自动滚动"""
        self.auto_scroll = enabled
    
    def _clear_logs(self):
        """清空日志"""
        reply = QMessageBox.question(
            self,
            "确认清空",
            "确定要清空当前显示的日志吗？\n\n此操作不会删除日志文件。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.log_text_edit.clear()
            self.statistics.reset()
            self._update_line_count()
            self._update_statistics_display()
            self.log_cleared.emit()
            logger.info("日志显示已清空")
    
    def _export_logs(self):
        """导出日志"""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "导出日志",
                f"logs_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                "文本文件 (*.txt);;所有文件 (*.*)"
            )
            
            if file_path:
                content = self.log_text_edit.toPlainText()
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                QMessageBox.information(self, "导出成功", f"日志已导出到：\n{file_path}")
                self.log_exported.emit(file_path)
                logger.info(f"日志已导出到: {file_path}")
                
        except Exception as e:
            logger.error(f"导出日志失败: {e}")
            QMessageBox.critical(self, "导出失败", f"导出日志失败：{str(e)}")
    
    def _open_log_file(self):
        """打开日志文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择日志文件",
            "logs",
            "日志文件 (*.log *.txt);;所有文件 (*.*)"
        )
        
        if file_path:
            self._start_monitoring(file_path)
    
    def _refresh_logs(self):
        """刷新日志"""
        if self.current_log_file:
            self._load_existing_logs(self.current_log_file)
        self._refresh_file_list()
    
    def _refresh_file_list(self):
        """刷新文件列表"""
        try:
            self.file_tree.clear()
            
            log_dir = Path("logs")
            if log_dir.exists():
                for log_file in log_dir.glob("*.log"):
                    stat = log_file.stat()
                    size_mb = stat.st_size / (1024 * 1024)
                    mod_time = datetime.fromtimestamp(stat.st_mtime)
                    
                    item = QTreeWidgetItem([
                        log_file.name,
                        f"{size_mb:.2f} MB",
                        mod_time.strftime("%Y-%m-%d %H:%M:%S")
                    ])
                    item.setData(0, Qt.ItemDataRole.UserRole, str(log_file))
                    self.file_tree.addTopLevelItem(item)
            
            # 调整列宽
            for i in range(3):
                self.file_tree.resizeColumnToContents(i)
                
        except Exception as e:
            logger.error(f"刷新文件列表失败: {e}")
    
    def _on_file_selected(self, item: QTreeWidgetItem, column: int):
        """文件选择处理"""
        file_path = item.data(0, Qt.ItemDataRole.UserRole)
        if file_path:
            self._start_monitoring(file_path)
    
    def _update_max_lines(self, value: int):
        """更新最大行数"""
        self.max_lines = value
        logger.debug(f"最大显示行数已更新为: {value}")
    
    def _update_font_size(self, size: int):
        """更新字体大小"""
        font = self.log_text_edit.font()
        font.setPointSize(size)
        self.log_text_edit.setFont(font)
    
    def _change_theme(self, theme: str):
        """更改主题"""
        if theme == "深色":
            self.log_text_edit.setStyleSheet("""
                QTextEdit {
                    background-color: #2b2b2b;
                    color: #ffffff;
                    border: 1px solid #555555;
                }
            """)
        elif theme == "高对比度":
            self.log_text_edit.setStyleSheet("""
                QTextEdit {
                    background-color: #000000;
                    color: #ffffff;
                    border: 2px solid #ffffff;
                }
            """)
        else:  # 默认主题
            self.log_text_edit.setStyleSheet("")
    
    def _update_line_count(self):
        """更新行数显示"""
        line_count = self.log_text_edit.document().blockCount()
        self.line_count_label.setText(f"行数: {line_count}")
    
    def _update_statistics_display(self):
        """更新统计显示"""
        stats = self.statistics.get_summary()
        
        stats_text = f"""总行数: {stats['total_lines']}
错误: {stats['error_count']}
警告: {stats['warning_count']}
信息: {stats['info_count']}
调试: {stats['debug_count']}

运行时长: {stats['duration']}
开始时间: {stats['start_time']}
最后更新: {stats['last_update']}"""
        
        self.stats_label.setText(stats_text)
    
    def add_log_message(self, message: str, level: str = "INFO"):
        """手动添加日志消息"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_message = f"[{timestamp}] {level.upper()}: {message}"
        self._append_log_line(formatted_message)
    
    def get_current_logs(self) -> str:
        """获取当前显示的日志内容"""
        return self.log_text_edit.toPlainText()
    
    def closeEvent(self, event):
        """关闭事件处理"""
        if self.log_watcher:
            self.log_watcher.stop()
        event.accept()