# -*- coding: utf-8 -*-
"""
共享GUI组件模块
统一PyQt组件导入，减少重复代码
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


class BaseWidget(QWidget):
    """基础Widget类，提供通用功能"""
    
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


class SettingsWidget(BaseWidget):
    """设置界面基类"""
    
    # 通用信号
    settings_changed = pyqtSignal(str, str, object)  # category, key, value
    
    def __init__(self, config_manager=None, parent=None):
        self.config_manager = config_manager
        super().__init__(parent)
    
    def create_button_layout(self, buttons: list = None) -> QHBoxLayout:
        """创建按钮布局
        
        Args:
            buttons: 按钮配置列表，格式为 [{'text': '按钮文本', 'callback': 回调函数, 'width': 宽度}, ...]
                    如果为None，则创建默认的重置和应用按钮
        
        Returns:
            QHBoxLayout: 按钮布局
        """
        layout = QHBoxLayout()
        layout.addStretch()
        
        if buttons is None:
            # 默认按钮：重置和应用
            buttons = [
                {'text': '重置为默认', 'callback': self._reset_settings, 'width': 100},
                {'text': '应用设置', 'callback': self._apply_settings, 'width': 100}
            ]
        
        # 创建按钮
        for btn_config in buttons:
            button = self.create_button(btn_config['text'], btn_config.get('width', 80))
            if 'callback' in btn_config and btn_config['callback']:
                button.clicked.connect(btn_config['callback'])
            layout.addWidget(button)
            
            # 保存按钮引用（用于后续访问）
            btn_name = btn_config['text'].replace(' ', '_').replace('为', '').replace('设置', '').lower()
            if btn_name == '重置默认':
                btn_name = 'reset_btn'
            elif btn_name == '应用':
                btn_name = 'apply_btn'
            else:
                btn_name = f"{btn_name}_btn"
            setattr(self, btn_name, button)
        
        return layout
    
    def create_standard_button_layout(self) -> QHBoxLayout:
        """创建标准按钮布局（测试、导入、导出、重置、应用）"""
        buttons = [
            {'text': '测试连接', 'callback': self._test_connection, 'width': 100},
            {'text': '导入配置', 'callback': self._import_settings, 'width': 100},
            {'text': '导出配置', 'callback': self._export_settings, 'width': 100},
            {'text': '重置为默认', 'callback': self._reset_settings, 'width': 100},
            {'text': '应用设置', 'callback': self._apply_settings, 'width': 100}
        ]
        return self.create_button_layout(buttons)
    
    def create_simple_button_layout(self) -> QHBoxLayout:
        """创建简单按钮布局（仅重置和应用）"""
        return self.create_button_layout()  # 使用默认配置
    
    def _reset_settings(self):
        """重置设置，子类需要重写"""
        reply = QMessageBox.question(
            self,
            "确认重置",
            "确定要重置所有设置为默认值吗？\n\n此操作不可撤销。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self._do_reset_settings()
    
    def _do_reset_settings(self):
        """执行重置操作，子类需要重写"""
        pass
    
    def _apply_settings(self):
        """应用设置，子类需要重写"""
        pass
    
    def _load_settings(self):
        """加载设置，子类需要重写"""
        pass
    
    def _test_connection(self):
        """测试连接，子类可以重写"""
        QMessageBox.information(self, "测试结果", "测试功能需要在子类中实现")
    
    def _import_settings(self):
        """导入设置，子类可以重写"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "导入配置文件", "", "JSON文件 (*.json);;所有文件 (*.*)"
        )
        if file_path:
            self._do_import_settings(file_path)
    
    def _export_settings(self):
        """导出设置，子类可以重写"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出配置文件", "", "JSON文件 (*.json);;所有文件 (*.*)"
        )
        if file_path:
            self._do_export_settings(file_path)
    
    def _do_import_settings(self, file_path: str):
        """执行导入操作，子类需要重写"""
        QMessageBox.information(self, "导入结果", "导入功能需要在子类中实现")
    
    def _do_export_settings(self, file_path: str):
        """执行导出操作，子类需要重写"""
        QMessageBox.information(self, "导出结果", "导出功能需要在子类中实现")
    
    def _on_setting_changed(self, category: str, key: str, value):
        """设置变更处理"""
        self.settings_changed.emit(category, key, value)


class FilterWidget(BaseWidget):
    """过滤器组件基类"""
    
    filter_changed = pyqtSignal(dict)  # 过滤条件变化信号
    
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
    
    def _on_filter_changed(self):
        """过滤条件变化处理，子类需要重写"""
        pass
    
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


# 导出所有组件
__all__ = [
    # Qt组件导入
    'QCheckBox', 'QComboBox', 'QDateEdit', 'QDateTimeEdit', 'QDoubleSpinBox',
    'QFileDialog', 'QFormLayout', 'QFrame', 'QGridLayout', 'QGroupBox',
    'QHBoxLayout', 'QHeaderView', 'QLabel', 'QLineEdit', 'QListWidget',
    'QListWidgetItem', 'QMainWindow', 'QMenu', 'QMenuBar', 'QMessageBox',
    'QProgressBar', 'QPushButton', 'QScrollArea', 'QSlider', 'QSpinBox',
    'QSplitter', 'QStatusBar', 'QTabWidget', 'QTableWidget', 'QTableWidgetItem',
    'QTextEdit', 'QToolBar', 'QTreeWidget', 'QTreeWidgetItem', 'QVBoxLayout',
    'QWidget',
    
    # Qt Core
    'QDateTime', 'QDate', 'QFileSystemWatcher', 'Qt', 'QThread', 'QTime',
    'QTimer', 'pyqtSignal', 'pyqtSlot',
    
    # Qt Gui
    'QAction', 'QBrush', 'QColor', 'QFont', 'QIcon', 'QPainter', 'QPalette',
    'QPixmap', 'QSyntaxHighlighter', 'QTextCharFormat', 'QTextCursor',
    'QTextDocument',
    
    # 自定义组件
    'BaseWidget', 'SettingsWidget', 'FilterWidget', 'StatusIndicator',
    'MetricsWidget',
]