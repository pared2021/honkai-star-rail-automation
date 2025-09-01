#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务列表MVP模式集成模块

将TaskListWidget(View)、TaskListPresenter和相关服务层连接起来，
实现完整的MVP架构模式。

作者: Assistant
日期: 2024-01-XX
"""

import logging
from typing import Optional
from PyQt6.QtCore import QObject

from ..task_list_widget import TaskListWidget
from .task_list_presenter import TaskListPresenter
from ...adapters.sync_adapter import SyncAdapter
from ...application.task_application_service import TaskApplicationService

logger = logging.getLogger(__name__)


class TaskListMVP(QObject):
    """任务列表MVP模式集成类
    
    负责将View、Presenter和Service层连接起来，
    实现完整的MVP架构模式。
    """
    
    def __init__(self, 
                 task_service: TaskApplicationService,
                 sync_adapter: SyncAdapter,
                 parent=None):
        """初始化MVP集成
        
        Args:
            task_service: 任务应用服务
            sync_adapter: 同步适配器
            parent: 父对象
        """
        super().__init__(parent)
        
        # 保存服务层引用
        self.task_service = task_service
        self.sync_adapter = sync_adapter
        
        # 创建View层（不传入task_manager，使用MVP模式）
        self.view = TaskListWidget(task_manager=None, parent=parent)
        
        # 创建Presenter层
        self.presenter = TaskListPresenter(
            view=self.view,
            task_service=task_service,
            sync_adapter=sync_adapter
        )
        
        logger.info("任务列表MVP模式初始化完成")
    
    def get_widget(self) -> TaskListWidget:
        """获取Widget实例
        
        Returns:
            TaskListWidget实例
        """
        return self.view
    
    def get_presenter(self) -> TaskListPresenter:
        """获取Presenter实例
        
        Returns:
            TaskListPresenter实例
        """
        return self.presenter
    
    def initialize(self):
        """初始化MVP组件
        
        启动Presenter并加载初始数据
        """
        try:
            # 初始化Presenter
            self.presenter.initialize()
            
            # 刷新任务列表
            self.presenter.refresh_tasks()
            
            logger.info("任务列表MVP组件初始化成功")
            
        except Exception as e:
            logger.error(f"任务列表MVP组件初始化失败: {e}")
            raise
    
    def cleanup(self):
        """清理资源
        
        在组件销毁时调用，清理相关资源
        """
        try:
            if self.presenter:
                self.presenter.cleanup()
            
            logger.info("任务列表MVP组件清理完成")
            
        except Exception as e:
            logger.error(f"任务列表MVP组件清理失败: {e}")
    
    def refresh(self):
        """刷新任务列表
        
        外部调用接口，用于刷新任务数据
        """
        if self.presenter:
            self.presenter.refresh_tasks()
    
    def select_task(self, task_id: str):
        """选择指定任务
        
        Args:
            task_id: 任务ID
        """
        if self.presenter:
            self.presenter.select_task(task_id)
    
    def set_auto_refresh(self, enabled: bool, interval: int = 5000):
        """设置自动刷新
        
        Args:
            enabled: 是否启用自动刷新
            interval: 刷新间隔（毫秒）
        """
        if self.presenter:
            self.presenter.set_auto_refresh(enabled, interval)