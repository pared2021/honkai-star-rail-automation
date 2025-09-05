# -*- coding: utf-8 -*-
"""
任务创建MVP组件
将Model、View、Presenter组合成一个完整的组件
"""

from typing import Optional

from PyQt6.QtCore import QObject, pyqtSignal
from loguru import logger

from adapters.task_manager_adapter import TaskManagerAdapter
from models.task_models import TaskConfig
from ui.mvp.base_mvp import BaseMVP
from ui.task_creation.task_creation_model import TaskCreationModel
from ui.task_creation.task_creation_presenter import TaskCreationPresenter
from ui.task_creation.task_creation_view import TaskCreationView
from validators.task_validator import TaskValidator


class TaskCreationMVP(BaseMVP):
    """任务创建MVP组件
    
    将Model、View、Presenter组合成一个完整的任务创建组件
    """
    
    # 业务信号
    task_created = pyqtSignal(str)  # 任务创建成功
    task_updated = pyqtSignal(str)  # 任务更新成功
    task_creation_failed = pyqtSignal(str)  # 任务创建失败
    
    def __init__(
        self,
        task_manager: TaskManagerAdapter,
        task_validator: TaskValidator,
        parent: Optional[QObject] = None
    ):
        """初始化任务创建MVP组件
        
        Args:
            task_manager: 任务管理适配器
            task_validator: 任务验证器
            parent: 父对象
        """
        # 创建组件
        model = TaskCreationModel()
        view = TaskCreationView()
        presenter = TaskCreationPresenter(
            model=model,
            view=view,
            task_manager=task_manager,
            task_validator=task_validator,
            parent=parent
        )
        
        super().__init__(model, view, presenter, parent)
        
        # 保存依赖引用
        self._task_manager = task_manager
        self._task_validator = task_validator
        
        self._connect_business_signals()
        
        logger.info("任务创建MVP组件初始化完成")
    
    def _connect_business_signals(self):
        """连接业务信号"""
        # 转发Presenter的业务信号
        self._presenter.task_created.connect(self.task_created.emit)
        self._presenter.task_updated.connect(self.task_updated.emit)
        self._presenter.task_creation_failed.connect(self.task_creation_failed.emit)
        
        logger.debug("业务信号连接完成")
    
    # 公共接口
    def load_task_for_editing(self, task_config: TaskConfig):
        """加载任务进行编辑
        
        Args:
            task_config: 任务配置
        """
        try:
            self._presenter.load_task_for_editing(task_config)
            logger.info(f"任务加载完成，进入编辑模式: {task_config.id}")
            
        except Exception as e:
            logger.error(f"加载任务进行编辑失败: {e}")
            raise
    
    def clear_editing_mode(self):
        """清除编辑模式"""
        try:
            self._presenter.clear_editing_mode()
            logger.info("编辑模式已清除")
            
        except Exception as e:
            logger.error(f"清除编辑模式失败: {e}")
            raise
    
    def get_current_task_config(self) -> Optional[TaskConfig]:
        """获取当前任务配置
        
        Returns:
            Optional[TaskConfig]: 当前任务配置
        """
        try:
            return self._presenter.get_current_task_config()
            
        except Exception as e:
            logger.error(f"获取当前任务配置失败: {e}")
            return None
    
    def is_form_valid(self) -> bool:
        """检查表单是否有效
        
        Returns:
            bool: 表单是否有效
        """
        try:
            return self._presenter.is_form_valid()
            
        except Exception as e:
            logger.error(f"检查表单有效性失败: {e}")
            return False
    
    def reset_form(self):
        """重置表单"""
        try:
            self._presenter._on_form_reset_requested()
            logger.info("表单重置完成")
            
        except Exception as e:
            logger.error(f"重置表单失败: {e}")
            raise
    
    def show_widget(self):
        """显示组件"""
        self._view.show()
    
    def hide_widget(self):
        """隐藏组件"""
        self._view.hide()
    
    def cleanup(self):
        """清理资源"""
        try:
            # 清理Presenter
            if hasattr(self._presenter, 'cleanup'):
                self._presenter.cleanup()
            
            # 调用父类清理
            super().cleanup()
            
            logger.info("任务创建MVP组件清理完成")
            
        except Exception as e:
            logger.error(f"清理任务创建MVP组件失败: {e}")
    
    # 属性访问器
    @property
    def model(self) -> TaskCreationModel:
        """获取Model"""
        return self._model
    
    @property
    def view(self) -> TaskCreationView:
        """获取View"""
        return self._view
    
    @property
    def presenter(self) -> TaskCreationPresenter:
        """获取Presenter"""
        return self._presenter
    
    @property
    def widget(self) -> TaskCreationView:
        """获取Widget（View的别名）"""
        return self._view