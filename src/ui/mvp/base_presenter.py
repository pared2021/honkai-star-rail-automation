# -*- coding: utf-8 -*-
"""
MVP模式基础Presenter类

定义了展示器的基础接口和通用功能。
"""

import logging
from abc import ABC, ABCMeta, abstractmethod
from typing import Any, Dict, Optional, List, Callable
from PyQt6.QtCore import QObject, pyqtSignal, QTimer

from .base_model import BaseModel
from .base_view import BaseView
from ..sync_adapter import get_sync_adapter

logger = logging.getLogger(__name__)


class QObjectMeta(type(QObject), ABCMeta):
    """解决QObject和ABC元类冲突的元类"""
    pass


class BasePresenter(QObject, ABC, metaclass=QObjectMeta):
    """MVP模式基础Presenter类
    
    负责协调Model和View之间的交互，包括：
    - 处理用户交互
    - 更新视图显示
    - 管理业务逻辑
    - 异步操作处理
    """
    
    def __init__(self, model: BaseModel, view: BaseView):
        super().__init__()
        self._model = model
        self._view = view
        self._sync_adapter = get_sync_adapter()
        self._action_handlers: Dict[str, Callable] = {}
        self._is_initialized = False
        
        logger.debug(f"{self.__class__.__name__} 初始化开始")
    
    def initialize(self):
        """初始化Presenter
        
        设置Model和View之间的连接
        """
        if self._is_initialized:
            return
        
        try:
            # 连接Model信号
            self._connect_model_signals()
            
            # 连接View信号
            self._connect_view_signals()
            
            # 注册动作处理器
            self._register_action_handlers()
            
            # 初始化View
            self._view.initialize()
            
            # 加载初始数据
            self._load_initial_data()
            
            self._is_initialized = True
            logger.debug(f"{self.__class__.__name__} 初始化完成")
            
        except Exception as e:
            logger.error(f"{self.__class__.__name__} 初始化失败: {e}")
            raise
    
    def _connect_model_signals(self):
        """连接Model信号"""
        self._model.data_changed.connect(self._on_model_data_changed)
        self._model.validation_failed.connect(self._on_model_validation_failed)
        self._model.model_updated.connect(self._on_model_updated)
        
        logger.debug("Model信号已连接")
    
    def _connect_view_signals(self):
        """连接View信号"""
        self._view.user_action.connect(self._on_user_action)
        self._view.view_ready.connect(self._on_view_ready)
        self._view.view_closing.connect(self._on_view_closing)
        self._view.validation_error.connect(self._on_view_validation_error)
        
        logger.debug("View信号已连接")
    
    @abstractmethod
    def _register_action_handlers(self):
        """注册动作处理器（子类实现）"""
        pass
    
    def register_action_handler(self, action_name: str, handler: Callable):
        """注册动作处理器
        
        Args:
            action_name: 动作名称
            handler: 处理函数
        """
        self._action_handlers[action_name] = handler
        logger.debug(f"注册动作处理器: {action_name}")
    
    def _on_user_action(self, action_name: str, data: Any):
        """处理用户动作
        
        Args:
            action_name: 动作名称
            data: 相关数据
        """
        logger.debug(f"处理用户动作: {action_name}")
        
        handler = self._action_handlers.get(action_name)
        if handler:
            try:
                handler(data)
            except Exception as e:
                logger.error(f"动作处理器执行失败: {action_name}, 错误: {e}")
                self._view.show_error(f"操作失败: {str(e)}")
        else:
            logger.warning(f"未找到动作处理器: {action_name}")
    
    def _on_model_data_changed(self, field_name: str, value: Any):
        """处理Model数据变更
        
        Args:
            field_name: 字段名
            value: 新值
        """
        logger.debug(f"Model数据变更: {field_name} = {value}")
        self._view.update_display(field_name, value)
    
    def _on_model_validation_failed(self, field_name: str, error_message: str):
        """处理Model验证失败
        
        Args:
            field_name: 字段名
            error_message: 错误消息
        """
        logger.warning(f"Model验证失败: {field_name} - {error_message}")
        self._view.show_error(error_message, "验证失败")
    
    def _on_model_updated(self):
        """处理Model整体更新"""
        logger.debug("Model整体更新")
        self._view.update_multiple_displays(self._model.get_all_data())
    
    def _on_view_ready(self):
        """处理View准备就绪"""
        logger.debug("View准备就绪")
        self._on_view_initialized()
    
    def _on_view_closing(self):
        """处理View关闭"""
        logger.debug("View即将关闭")
        self._cleanup()
    
    def _on_view_validation_error(self, field_name: str, error_message: str):
        """处理View验证错误
        
        Args:
            field_name: 字段名
            error_message: 错误消息
        """
        logger.warning(f"View验证错误: {field_name} - {error_message}")
        self._view.show_error(error_message, "输入错误")
    
    def _load_initial_data(self):
        """加载初始数据"""
        try:
            self._view.set_loading(True)
            
            # 异步加载数据
            self._sync_adapter.run_async(
                self._load_data_async(),
                callback=self._on_data_loaded,
                error_callback=self._on_data_load_failed
            )
            
        except Exception as e:
            logger.error(f"加载初始数据失败: {e}")
            self._view.set_loading(False)
            self._view.show_error(f"加载数据失败: {str(e)}")
    
    async def _load_data_async(self) -> bool:
        """异步加载数据（子类可重写）
        
        Returns:
            是否加载成功
        """
        return await self._model.load_data()
    
    def _on_data_loaded(self, success: bool):
        """数据加载完成回调
        
        Args:
            success: 是否加载成功
        """
        self._view.set_loading(False)
        
        if success:
            logger.info("数据加载成功")
            self._view.update_multiple_displays(self._model.get_all_data())
        else:
            logger.error("数据加载失败")
            self._view.show_error("数据加载失败")
    
    def _on_data_load_failed(self, error: Exception):
        """数据加载失败回调
        
        Args:
            error: 错误信息
        """
        self._view.set_loading(False)
        logger.error(f"数据加载异常: {error}")
        self._view.show_error(f"数据加载失败: {str(error)}")
    
    def save_data(self):
        """保存数据"""
        try:
            self._view.set_loading(True)
            
            # 异步保存数据
            self._sync_adapter.run_async(
                self._save_data_async(),
                callback=self._on_data_saved,
                error_callback=self._on_data_save_failed
            )
            
        except Exception as e:
            logger.error(f"保存数据失败: {e}")
            self._view.set_loading(False)
            self._view.show_error(f"保存数据失败: {str(e)}")
    
    async def _save_data_async(self) -> bool:
        """异步保存数据（子类可重写）
        
        Returns:
            是否保存成功
        """
        return await self._model.save_data()
    
    def _on_data_saved(self, success: bool):
        """数据保存完成回调
        
        Args:
            success: 是否保存成功
        """
        self._view.set_loading(False)
        
        if success:
            logger.info("数据保存成功")
            self._model.mark_clean()
            self._view.show_info("保存成功")
        else:
            logger.error("数据保存失败")
            self._view.show_error("数据保存失败")
    
    def _on_data_save_failed(self, error: Exception):
        """数据保存失败回调
        
        Args:
            error: 错误信息
        """
        self._view.set_loading(False)
        logger.error(f"数据保存异常: {error}")
        self._view.show_error(f"数据保存失败: {str(error)}")
    
    def _on_view_initialized(self):
        """View初始化完成后的处理（子类可重写）"""
        pass
    
    def _cleanup(self):
        """清理资源（子类可重写）"""
        logger.debug(f"{self.__class__.__name__} 清理资源")
    
    @property
    def model(self) -> BaseModel:
        """获取Model"""
        return self._model
    
    @property
    def view(self) -> BaseView:
        """获取View"""
        return self._view
    
    @property
    def is_initialized(self) -> bool:
        """是否已初始化"""
        return self._is_initialized