# -*- coding: utf-8 -*-
"""
MVP模式基础View类

定义了视图组件的基础接口和通用功能。
"""

import logging
from abc import ABC, ABCMeta, abstractmethod
from typing import Any, Dict, Optional, List, Callable
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QMessageBox
from PyQt6.QtCore import pyqtSignal, QTimer
from PyQt6.QtGui import QFont

logger = logging.getLogger(__name__)


class QWidgetMeta(type(QWidget), ABCMeta):
    """解决QWidget和ABC元类冲突的元类"""
    pass


class BaseView(QWidget, ABC, metaclass=QWidgetMeta):
    """MVP模式基础View类
    
    提供视图管理的基础功能，包括：
    - 用户交互事件
    - 数据显示更新
    - 状态管理
    """
    
    # 信号定义
    user_action = pyqtSignal(str, object)  # action_name, data
    view_ready = pyqtSignal()  # 视图准备就绪
    view_closing = pyqtSignal()  # 视图即将关闭
    validation_error = pyqtSignal(str, str)  # field_name, error_message
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._is_initialized = False
        self._event_handlers: Dict[str, Callable] = {}
        self._validation_rules: Dict[str, list] = {}
        
        logger.debug(f"{self.__class__.__name__} 初始化开始")
    
    def initialize(self):
        """初始化视图
        
        在Presenter设置完成后调用
        """
        if self._is_initialized:
            return
        
        try:
            self.setup_ui()
            self.connect_signals()
            self.setup_validation()
            
            self._is_initialized = True
            self.view_ready.emit()
            
            logger.debug(f"{self.__class__.__name__} 初始化完成")
            
        except Exception as e:
            logger.error(f"{self.__class__.__name__} 初始化失败: {e}")
            raise
    
    @abstractmethod
    def setup_ui(self):
        """设置用户界面（子类实现）"""
        pass
    
    @abstractmethod
    def connect_signals(self):
        """连接信号槽（子类实现）"""
        pass
    
    def setup_validation(self):
        """设置验证规则（子类可重写）"""
        pass
    
    def register_event_handler(self, action_name: str, handler: Callable):
        """注册事件处理器
        
        Args:
            action_name: 动作名称
            handler: 处理函数
        """
        self._event_handlers[action_name] = handler
        logger.debug(f"注册事件处理器: {action_name}")
    
    def emit_user_action(self, action_name: str, data: Any = None):
        """发射用户动作信号
        
        Args:
            action_name: 动作名称
            data: 相关数据
        """
        logger.debug(f"用户动作: {action_name}")
        
        # 先尝试本地处理器
        handler = self._event_handlers.get(action_name)
        if handler:
            try:
                handler(data)
            except Exception as e:
                logger.error(f"本地事件处理器执行失败: {e}")
        
        # 发射信号给Presenter
        self.user_action.emit(action_name, data)
    
    def update_display(self, field_name: str, value: Any):
        """更新显示内容
        
        Args:
            field_name: 字段名
            value: 新值
        """
        try:
            self._update_field_display(field_name, value)
            logger.debug(f"更新显示: {field_name} = {value}")
        except Exception as e:
            logger.error(f"更新显示失败: {field_name}, 错误: {e}")
    
    def update_multiple_displays(self, data: Dict[str, Any]):
        """批量更新显示内容
        
        Args:
            data: 要更新的数据字典
        """
        for field_name, value in data.items():
            self.update_display(field_name, value)
    
    @abstractmethod
    def _update_field_display(self, field_name: str, value: Any):
        """更新特定字段的显示（子类实现）
        
        Args:
            field_name: 字段名
            value: 新值
        """
        pass
    
    def show_error(self, message: str, title: str = "错误"):
        """显示错误信息
        
        Args:
            message: 错误消息
            title: 错误标题
        """
        logger.warning(f"显示错误: {title} - {message}")
        self._show_error_dialog(message, title)
    
    def show_info(self, message: str, title: str = "信息"):
        """显示信息
        
        Args:
            message: 信息内容
            title: 信息标题
        """
        logger.info(f"显示信息: {title} - {message}")
        self._show_info_dialog(message, title)
    
    def show_warning(self, message: str, title: str = "警告"):
        """显示警告信息
        
        Args:
            message: 警告消息
            title: 警告标题
        """
        logger.warning(f"显示警告: {title} - {message}")
        self._show_warning_dialog(message, title)
    
    def _show_error_dialog(self, message: str, title: str):
        """显示错误对话框（子类可重写）"""
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.critical(self, title, message)
    
    def _show_info_dialog(self, message: str, title: str):
        """显示信息对话框（子类可重写）"""
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(self, title, message)
    
    def _show_warning_dialog(self, message: str, title: str):
        """显示警告对话框（子类可重写）"""
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.warning(self, title, message)
    
    def set_enabled(self, enabled: bool):
        """设置视图启用状态
        
        Args:
            enabled: 是否启用
        """
        self.setEnabled(enabled)
        logger.debug(f"视图启用状态: {enabled}")
    
    def set_loading(self, loading: bool):
        """设置加载状态
        
        Args:
            loading: 是否正在加载
        """
        self._set_loading_state(loading)
        logger.debug(f"视图加载状态: {loading}")
    
    def _set_loading_state(self, loading: bool):
        """设置加载状态的具体实现（子类可重写）
        
        Args:
            loading: 是否正在加载
        """
        # 默认实现：禁用/启用整个视图
        self.setEnabled(not loading)
    
    def validate_input(self, field_name: str, value: Any) -> bool:
        """验证输入
        
        Args:
            field_name: 字段名
            value: 输入值
            
        Returns:
            是否验证通过
        """
        rules = self._validation_rules.get(field_name, [])
        
        for rule in rules:
            try:
                if not rule(value):
                    error_msg = f"字段 {field_name} 验证失败"
                    self.validation_error.emit(field_name, error_msg)
                    return False
            except Exception as e:
                error_msg = f"字段 {field_name} 验证异常: {e}"
                self.validation_error.emit(field_name, error_msg)
                return False
        
        return True
    
    def add_validation_rule(self, field_name: str, rule: Callable[[Any], bool]):
        """添加验证规则
        
        Args:
            field_name: 字段名
            rule: 验证规则函数
        """
        if field_name not in self._validation_rules:
            self._validation_rules[field_name] = []
        
        self._validation_rules[field_name].append(rule)
        logger.debug(f"为字段 {field_name} 添加验证规则")
    
    def closeEvent(self, event):
        """关闭事件处理"""
        logger.debug(f"{self.__class__.__name__} 即将关闭")
        self.view_closing.emit()
        super().closeEvent(event)
    
    @property
    def is_initialized(self) -> bool:
        """是否已初始化"""
        return self._is_initialized