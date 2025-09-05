# -*- coding: utf-8 -*-
"""
共享UI组件模块
统一PyQt组件导入，减少重复代码
重构为MVP架构兼容的组件库
"""

from typing import Any, Dict, List, Optional, Union

from PyQt6.QtCore import (
    QDateTime,
    QDate,
    QFileSystemWatcher,
    Qt,
    QThread,
    QTime,
    QTimer,
    pyqtSignal,
    pyqtSlot,
)
from PyQt6.QtGui import (
    QAction,
    QBrush,
    QColor,
    QFont,
    QIcon,
    QPainter,
    QPalette,
    QPixmap,
    QSyntaxHighlighter,
    QTextCharFormat,
    QTextCursor,
    QTextDocument,
)
from PyQt6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDateTimeEdit,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMenuBar,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QSizePolicy,
    QSlider,
    QSpacerItem,
    QSpinBox,
    QSplitter,
    QStackedWidget,
    QStatusBar,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QToolBar,
    QToolButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)


class BaseUIWidget(QWidget):
    """基础UI Widget类，提供通用功能
    
    为MVP架构设计的基础组件类
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self):
        """设置UI界面，子类需要重写"""
        pass
    
    def _connect_signals(self):
        """连接信号槽，子类需要重写"""
        pass
    
    def create_title_label(self, text: str, font_size: int = 16) -> QLabel:
        """创建标题标签"""
        label = QLabel(text)
        label.setFont(QFont("Microsoft YaHei", font_size, QFont.Weight.Bold))
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return label
    
    def create_group_box(self, title: str) -> QGroupBox:
        """创建分组框"""
        return QGroupBox(title)
    
    def create_button(self, text: str, width: Optional[int] = None) -> QPushButton:
        """创建按钮"""
        button = QPushButton(text)
        if width:
            button.setFixedWidth(width)
        return button
    
    def create_form_layout(self) -> QFormLayout:
        """创建表单布局"""
        return QFormLayout()
    
    def create_hbox_layout(self) -> QHBoxLayout:
        """创建水平布局"""
        return QHBoxLayout()
    
    def create_vbox_layout(self) -> QVBoxLayout:
        """创建垂直布局"""
        return QVBoxLayout()
    
    def create_grid_layout(self) -> QGridLayout:
        """创建网格布局"""
        return QGridLayout()


class MVPSettingsWidget(BaseUIWidget):
    """MVP架构的设置界面基类
    
    为MVP模式设计的设置组件基类
    """
    
    # 通用信号
    settings_changed = pyqtSignal(str, str, object)  # category, key, value
    reset_requested = pyqtSignal()  # 重置请求
    apply_requested = pyqtSignal()  # 应用请求
    test_requested = pyqtSignal()  # 测试请求
    import_requested = pyqtSignal(str)  # 导入请求
    export_requested = pyqtSignal(str)  # 导出请求
    
    def __init__(self, parent=None):
        super().__init__(parent)
    
    def create_button_layout(self, buttons: list = None) -> QHBoxLayout:
        """创建按钮布局
        
        Args:
            buttons: 按钮配置列表，格式为 [{'text': '按钮文本', 'signal': 信号名称, 'width': 宽度}, ...]
                    如果为None，则创建默认的重置和应用按钮
        
        Returns:
            QHBoxLayout: 按钮布局
        """
        layout = QHBoxLayout()
        layout.addStretch()
        
        if buttons is None:
            # 默认按钮：重置和应用
            buttons = [
                {'text': '重置为默认', 'signal': 'reset_requested', 'width': 100},
                {'text': '应用设置', 'signal': 'apply_requested', 'width': 100}
            ]
        
        # 创建按钮
        for btn_config in buttons:
            button = self.create_button(btn_config['text'], btn_config.get('width', 80))
            
            # 连接信号
            signal_name = btn_config.get('signal')
            if signal_name and hasattr(self, signal_name):
                signal = getattr(self, signal_name)
                if signal_name in ['import_requested', 'export_requested']:
                    # 文件操作信号需要特殊处理
                    if signal_name == 'import_requested':
                        button.clicked.connect(self._handle_import_request)
                    else:
                        button.clicked.connect(self._handle_export_request)
                else:
                    button.clicked.connect(signal.emit)
            
            layout.addWidget(button)
            
            # 保存按钮引用（用于后续访问）
            btn_name = btn_config['text'].replace(' ', '_').replace('为', '').replace('设置', '').lower()
            if btn_name == '重置默认':
                btn_name = 'reset_btn'
            elif btn_name == '应用':
                btn_name = 'apply_btn'
            elif btn_name == '测试连接':
                btn_name = 'test_btn'
            elif btn_name == '导入配置':
                btn_name = 'import_btn'
            elif btn_name == '导出配置':
                btn_name = 'export_btn'
            else:
                btn_name = f"{btn_name}_btn"
            setattr(self, btn_name, button)
        
        return layout
    
    def create_standard_button_layout(self) -> QHBoxLayout:
        """创建标准按钮布局（测试、导入、导出、重置、应用）"""
        buttons = [
            {'text': '测试连接', 'signal': 'test_requested', 'width': 100},
            {'text': '导入配置', 'signal': 'import_requested', 'width': 100},
            {'text': '导出配置', 'signal': 'export_requested', 'width': 100},
            {'text': '重置为默认', 'signal': 'reset_requested', 'width': 100},
            {'text': '应用设置', 'signal': 'apply_requested', 'width': 100}
        ]
        return self.create_button_layout(buttons)
    
    def create_simple_button_layout(self) -> QHBoxLayout:
        """创建简单按钮布局（仅重置和应用）"""
        return self.create_button_layout()  # 使用默认配置
    
    def _handle_import_request(self):
        """处理导入请求"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "导入配置文件", "", "JSON文件 (*.json);;所有文件 (*.*)"
        )
        if file_path:
            self.import_requested.emit(file_path)
    
    def _handle_export_request(self):
        """处理导出请求"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出配置文件", "", "JSON文件 (*.json);;所有文件 (*.*)"
        )
        if file_path:
            self.export_requested.emit(file_path)
    
    def show_reset_confirmation(self) -> bool:
        """显示重置确认对话框
        
        Returns:
            bool: 用户是否确认重置
        """
        reply = QMessageBox.question(
            self,
            "确认重置",
            "确定要重置所有设置为默认值吗？\n\n此操作不可撤销。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        return reply == QMessageBox.StandardButton.Yes
    
    def show_success_message(self, title: str, message: str):
        """显示成功消息"""
        QMessageBox.information(self, title, message)
    
    def show_error_message(self, title: str, message: str):
        """显示错误消息"""
        QMessageBox.critical(self, title, message)
    
    def show_warning_message(self, title: str, message: str):
        """显示警告消息"""
        QMessageBox.warning(self, title, message)


class MVPFilterWidget(BaseUIWidget):
    """MVP架构的过滤器组件基类
    
    为MVP模式设计的过滤组件基类
    """
    
    filter_changed = pyqtSignal(dict)  # 过滤条件变化信号
    clear_requested = pyqtSignal()  # 清除过滤请求
    
    def __init__(self, parent=None):
        super().__init__(parent)
    
    def create_filter_combo(self, label_text: str, items: List[tuple]) -> tuple:
        """创建过滤下拉框
        
        Args:
            label_text: 标签文本
            items: 选项列表，格式为[(显示文本, 值), ...]
            
        Returns:
            (QLabel, QComboBox)
        """
        label = QLabel(f"{label_text}:")
        combo = QComboBox()
        
        for text, value in items:
            combo.addItem(text, value)
        
        combo.currentTextChanged.connect(self._on_filter_changed)
        return label, combo
    
    def create_search_edit(self, placeholder: str = "搜索...") -> QLineEdit:
        """创建搜索输入框"""
        edit = QLineEdit()
        edit.setPlaceholderText(placeholder)
        edit.textChanged.connect(self._on_filter_changed)
        return edit
    
    def create_clear_button(self) -> QPushButton:
        """创建清除过滤按钮"""
        button = self.create_button("清除过滤")
        button.clicked.connect(self.clear_requested.emit)
        return button
    
    def _on_filter_changed(self):
        """过滤条件变化处理，子类需要重写"""
        pass
    
    def get_filter_data(self) -> dict:
        """获取当前过滤条件，子类需要重写
        
        Returns:
            dict: 过滤条件字典
        """
        return {}
    
    def clear_filters(self):
        """清除所有过滤条件，子类需要重写"""
        pass


class StatusIndicator(QLabel):
    """状态指示器组件"""
    
    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self.setStyleSheet("""
            QLabel {
                padding: 5px;
                border: 1px solid #ccc;
                border-radius: 3px;
                background-color: #f0f0f0;
            }
        """)
    
    def set_status(self, status: str, color: str = "black"):
        """设置状态
        
        Args:
            status: 状态文本
            color: 文本颜色
        """
        self.setText(status)
        self.setStyleSheet(f"""
            QLabel {{
                padding: 5px;
                border: 1px solid #ccc;
                border-radius: 3px;
                background-color: #f0f0f0;
                color: {color};
            }}
        """)
    
    def set_good_status(self, text: str = "正常"):
        """设置良好状态"""
        self.set_status(text, "green")
    
    def set_warning_status(self, text: str = "警告"):
        """设置警告状态"""
        self.set_status(text, "orange")
    
    def set_error_status(self, text: str = "错误"):
        """设置错误状态"""
        self.set_status(text, "red")


class MetricsWidget(QLabel):
    """指标显示组件"""
    
    def __init__(self, label: str, value: Union[str, int] = "", parent=None):
        super().__init__(parent)
        self.label = label
        self.update_value(value)
        self.setStyleSheet("""
            QLabel {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 5px;
                background-color: #fafafa;
                font-weight: bold;
            }
        """)
    
    def update_value(self, value: Union[str, int]):
        """更新指标值"""
        self.setText(f"{self.label}: {value}")
    
    def set_highlight(self, highlight: bool = True):
        """设置高亮显示"""
        if highlight:
            self.setStyleSheet("""
                QLabel {
                    padding: 8px;
                    border: 2px solid #007acc;
                    border-radius: 5px;
                    background-color: #e6f3ff;
                    font-weight: bold;
                    color: #007acc;
                }
            """)
        else:
            self.setStyleSheet("""
                QLabel {
                    padding: 8px;
                    border: 1px solid #ddd;
                    border-radius: 5px;
                    background-color: #fafafa;
                    font-weight: bold;
                }
            """)


class LoadingWidget(QWidget):
    """加载指示器组件"""
    
    def __init__(self, text: str = "加载中...", parent=None):
        super().__init__(parent)
        self.setup_ui(text)
    
    def setup_ui(self, text: str):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # 无限进度条
        layout.addWidget(self.progress_bar)
        
        # 文本标签
        self.text_label = QLabel(text)
        self.text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.text_label)
    
    def set_text(self, text: str):
        """设置加载文本"""
        self.text_label.setText(text)
    
    def start_loading(self):
        """开始加载动画"""
        self.progress_bar.setRange(0, 0)
        self.show()
    
    def stop_loading(self):
        """停止加载动画"""
        self.progress_bar.setRange(0, 1)
        self.progress_bar.setValue(1)
        self.hide()


# 导出所有组件
__all__ = [
    # Qt组件导入
    'QCheckBox', 'QComboBox', 'QDateEdit', 'QDateTimeEdit', 'QDoubleSpinBox',
    'QFileDialog', 'QFormLayout', 'QFrame', 'QGridLayout', 'QGroupBox',
    'QHBoxLayout', 'QHeaderView', 'QLabel', 'QLineEdit', 'QListWidget',
    'QListWidgetItem', 'QMainWindow', 'QMenu', 'QMenuBar', 'QMessageBox',
    'QProgressBar', 'QPushButton', 'QRadioButton', 'QScrollArea', 'QSizePolicy',
    'QSlider', 'QSpacerItem', 'QSpinBox', 'QSplitter', 'QStackedWidget',
    'QStatusBar', 'QTabWidget', 'QTableWidget', 'QTableWidgetItem',
    'QTextEdit', 'QToolBar', 'QToolButton', 'QTreeWidget', 'QTreeWidgetItem',
    'QVBoxLayout', 'QWidget', 'QButtonGroup',
    
    # Qt Core
    'QDateTime', 'QDate', 'QFileSystemWatcher', 'Qt', 'QThread', 'QTime',
    'QTimer', 'pyqtSignal', 'pyqtSlot',
    
    # Qt Gui
    'QAction', 'QBrush', 'QColor', 'QFont', 'QIcon', 'QPainter', 'QPalette',
    'QPixmap', 'QSyntaxHighlighter', 'QTextCharFormat', 'QTextCursor',
    'QTextDocument',
    
    # MVP架构组件
    'BaseUIWidget', 'MVPSettingsWidget', 'MVPFilterWidget',
    
    # 通用UI组件
    'StatusIndicator', 'MetricsWidget', 'LoadingWidget',
]