# -*- coding: utf-8 -*-
"""
任务创建Presenter层
MVP架构中的展示层，负责协调Model和View，处理业务逻辑
"""

import json
from typing import Any, Dict, List, Optional

from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from loguru import logger

from adapters.task_manager_adapter import TaskManagerAdapter
from models.task_models import TaskConfig, TaskPriority, TaskType, ValidationLevel
from ui.mvp.base_presenter import BasePresenter
from ui.task_creation.task_creation_model import TaskCreationModel
from ui.task_creation.task_creation_view import TaskCreationView
from validators.task_validator import TaskValidator


class TaskCreationPresenter(BasePresenter):
    """任务创建展示层
    
    负责协调Model和View，处理用户交互和业务逻辑
    """
    
    # 业务信号
    task_created = pyqtSignal(str)  # 任务创建成功
    task_updated = pyqtSignal(str)  # 任务更新成功
    task_creation_failed = pyqtSignal(str)  # 任务创建失败
    
    def __init__(
        self,
        model: TaskCreationModel,
        view: TaskCreationView,
        task_manager: TaskManagerAdapter,
        task_validator: TaskValidator,
        parent: Optional[QObject] = None
    ):
        super().__init__(model, view, parent)
        
        # 依赖注入
        self._task_manager = task_manager
        self._task_validator = task_validator
        
        # 状态管理
        self._is_processing = False
        self._validation_timer = QTimer()
        self._validation_timer.setSingleShot(True)
        self._validation_timer.timeout.connect(self._perform_validation)
        
        self._connect_signals()
        self._initialize_data()
        
        logger.info("任务创建Presenter初始化完成")
    
    def _connect_signals(self):
        """连接信号"""
        # View -> Presenter 信号
        self._view.form_field_changed.connect(self._on_form_field_changed)
        self._view.action_add_requested.connect(self._on_action_add_requested)
        self._view.action_edit_requested.connect(self._on_action_edit_requested)
        self._view.action_remove_requested.connect(self._on_action_remove_requested)
        self._view.validation_requested.connect(self._on_validation_requested)
        self._view.task_create_requested.connect(self._on_task_create_requested)
        self._view.form_reset_requested.connect(self._on_form_reset_requested)
        
        # Model -> Presenter 信号
        self._model.data_changed.connect(self._on_model_data_changed)
        self._model.validation_changed.connect(self._on_validation_changed)
        
        # 外部依赖信号
        self._task_manager.task_created.connect(self._on_task_created_success)
        self._task_manager.task_updated.connect(self._on_task_updated_success)
        self._task_manager.task_operation_failed.connect(self._on_task_operation_failed)
        
        logger.debug("信号连接完成")
    
    def _initialize_data(self):
        """初始化数据"""
        try:
            # 初始化表单默认值
            self._model.reset_form()
            
            # 同步到View
            self._sync_model_to_view()
            
            logger.info("数据初始化完成")
            
        except Exception as e:
            logger.error(f"数据初始化失败: {e}")
            self._view.show_error(f"初始化失败: {e}")
    
    def _sync_model_to_view(self):
        """同步Model数据到View"""
        try:
            # 获取表单数据
            form_data = self._model.get_form_data()
            
            # 更新View
            self._view.update_data(form_data)
            
            # 更新动作列表
            actions = self._model.get_actions()
            self._view.update_actions_list(actions)
            
            # 更新编辑模式
            is_editing = self._model.is_editing_mode()
            task_id = self._model.get_editing_task_id()
            self._view.set_editing_mode(is_editing, task_id)
            
            # 更新按钮状态
            is_valid = self._model.is_form_valid()
            self._view.set_create_button_enabled(is_valid)
            
            logger.debug("Model数据已同步到View")
            
        except Exception as e:
            logger.error(f"同步Model到View失败: {e}")
    
    def _sync_view_to_model(self):
        """同步View数据到Model"""
        try:
            # 获取View数据
            form_data = self._view.get_user_input()
            
            # 更新Model
            for field, value in form_data.items():
                self._model.set_form_field(field, value)
            
            logger.debug("View数据已同步到Model")
            
        except Exception as e:
            logger.error(f"同步View到Model失败: {e}")
    
    def _on_form_field_changed(self, field: str, value: Any):
        """处理表单字段变化
        
        Args:
            field: 字段名
            value: 字段值
        """
        try:
            # 更新Model
            self._model.set_form_field(field, value)
            
            # 延迟验证（避免频繁验证）
            self._validation_timer.stop()
            self._validation_timer.start(500)  # 500ms后验证
            
            logger.debug(f"表单字段变化: {field} = {value}")
            
        except Exception as e:
            logger.error(f"处理表单字段变化失败: {field} = {value}, 错误: {e}")
    
    def _on_action_add_requested(self):
        """处理添加动作请求"""
        try:
            # TODO: 打开动作编辑对话框
            # 这里暂时添加一个示例动作
            action = {
                'type': 'click',
                'description': '点击操作',
                'target': '',
                'params': {}
            }
            
            self._model.add_action(action)
            
            logger.info("添加动作请求处理完成")
            
        except Exception as e:
            logger.error(f"处理添加动作请求失败: {e}")
            self._view.show_error(f"添加动作失败: {e}")
    
    def _on_action_edit_requested(self, index: int):
        """处理编辑动作请求
        
        Args:
            index: 动作索引
        """
        try:
            if index < 0:
                return
            
            actions = self._model.get_actions()
            if index >= len(actions):
                logger.warning(f"动作索引超出范围: {index}")
                return
            
            # TODO: 打开动作编辑对话框
            # 这里暂时修改动作描述
            action = actions[index].copy()
            action['description'] = f"已编辑 - {action.get('description', '')}" 
            
            self._model.update_action(index, action)
            
            logger.info(f"编辑动作请求处理完成: {index}")
            
        except Exception as e:
            logger.error(f"处理编辑动作请求失败: {index}, 错误: {e}")
            self._view.show_error(f"编辑动作失败: {e}")
    
    def _on_action_remove_requested(self, index: int):
        """处理删除动作请求
        
        Args:
            index: 动作索引
        """
        try:
            if index < 0:
                return
            
            self._model.remove_action(index)
            
            logger.info(f"删除动作请求处理完成: {index}")
            
        except Exception as e:
            logger.error(f"处理删除动作请求失败: {index}, 错误: {e}")
            self._view.show_error(f"删除动作失败: {e}")
    
    def _on_validation_requested(self):
        """处理验证请求"""
        try:
            self._perform_validation(show_result=True)
            
        except Exception as e:
            logger.error(f"处理验证请求失败: {e}")
            self._view.show_error(f"验证失败: {e}")
    
    def _perform_validation(self, show_result: bool = False):
        """执行验证
        
        Args:
            show_result: 是否显示验证结果
        """
        try:
            # 构建任务配置
            task_config = self._model.build_task_config()
            if not task_config:
                if show_result:
                    self._view.show_error_message("验证失败", "无法构建任务配置")
                return
            
            # 执行验证
            validation_result = self._task_validator.validate_task_config(task_config)
            
            # 更新Model验证结果
            self._model.set_validation_result(validation_result)
            
            # 显示验证结果
            if show_result:
                self._view.show_validation_result(
                    validation_result.is_valid,
                    validation_result.errors,
                    validation_result.warnings
                )
            
            logger.debug(f"验证完成: 有效={validation_result.is_valid}")
            
        except Exception as e:
            logger.error(f"执行验证失败: {e}")
            if show_result:
                self._view.show_error_message("验证失败", str(e))
    
    def _on_task_create_requested(self):
        """处理任务创建请求"""
        if self._is_processing:
            logger.warning("任务创建正在进行中，忽略重复请求")
            return
        
        try:
            self._is_processing = True
            self._view.show_loading("创建任务中...")
            
            # 构建任务配置
            task_config = self._model.build_task_config()
            if not task_config:
                self._view.show_error_message("创建失败", "无法构建任务配置")
                return
            
            # 验证任务配置
            validation_result = self._task_validator.validate_task_config(task_config)
            if not validation_result.is_valid:
                error_msg = "\n".join(validation_result.errors)
                self._view.show_error_message("创建失败", f"任务配置验证失败：\n{error_msg}")
                return
            
            # 创建或更新任务
            if self._model.is_editing_mode():
                task_id = self._model.get_editing_task_id()
                self._task_manager.update_task_async(task_id, task_config)
            else:
                self._task_manager.create_task_async(task_config)
            
            logger.info("任务创建请求已提交")
            
        except Exception as e:
            logger.error(f"处理任务创建请求失败: {e}")
            self._view.show_error_message("创建失败", str(e))
        finally:
            if self._is_processing:
                self._is_processing = False
                self._view.hide_loading()
    
    def _on_form_reset_requested(self):
        """处理表单重置请求"""
        try:
            self._model.reset_form()
            self._sync_model_to_view()
            
            logger.info("表单重置完成")
            
        except Exception as e:
            logger.error(f"处理表单重置请求失败: {e}")
            self._view.show_error(f"重置失败: {e}")
    
    def _on_model_data_changed(self, field: str, value: Any):
        """处理Model数据变化
        
        Args:
            field: 字段名
            value: 字段值
        """
        try:
            # 同步特定字段到View
            if field == 'actions':
                self._view.update_actions_list(value)
            else:
                self._view.set_form_field_value(field, value)
            
            logger.debug(f"Model数据变化已同步到View: {field}")
            
        except Exception as e:
            logger.error(f"处理Model数据变化失败: {field} = {value}, 错误: {e}")
    
    def _on_validation_changed(self, is_valid: bool, errors: List[str], warnings: List[str]):
        """处理验证结果变化
        
        Args:
            is_valid: 是否有效
            errors: 错误列表
            warnings: 警告列表
        """
        try:
            # 更新创建按钮状态
            self._view.set_create_button_enabled(is_valid)
            
            logger.debug(f"验证结果变化: 有效={is_valid}, 错误={len(errors)}, 警告={len(warnings)}")
            
        except Exception as e:
            logger.error(f"处理验证结果变化失败: {e}")
    
    def _on_task_created_success(self, task_id: str):
        """处理任务创建成功
        
        Args:
            task_id: 任务ID
        """
        try:
            self._is_processing = False
            self._view.hide_loading()
            
            self._view.show_success_message("创建成功", f"任务创建成功！\n任务ID: {task_id}")
            
            # 重置表单
            self._model.reset_form()
            self._sync_model_to_view()
            
            # 发射业务信号
            self.task_created.emit(task_id)
            
            logger.info(f"任务创建成功: {task_id}")
            
        except Exception as e:
            logger.error(f"处理任务创建成功失败: {e}")
    
    def _on_task_updated_success(self, task_id: str):
        """处理任务更新成功
        
        Args:
            task_id: 任务ID
        """
        try:
            self._is_processing = False
            self._view.hide_loading()
            
            self._view.show_success_message("更新成功", f"任务更新成功！\n任务ID: {task_id}")
            
            # 发射业务信号
            self.task_updated.emit(task_id)
            
            logger.info(f"任务更新成功: {task_id}")
            
        except Exception as e:
            logger.error(f"处理任务更新成功失败: {e}")
    
    def _on_task_operation_failed(self, error_message: str):
        """处理任务操作失败
        
        Args:
            error_message: 错误消息
        """
        try:
            self._is_processing = False
            self._view.hide_loading()
            
            self._view.show_error_message("操作失败", error_message)
            
            # 发射业务信号
            self.task_creation_failed.emit(error_message)
            
            logger.error(f"任务操作失败: {error_message}")
            
        except Exception as e:
            logger.error(f"处理任务操作失败失败: {e}")
    
    # 公共接口
    def load_task_for_editing(self, task_config: TaskConfig):
        """加载任务进行编辑
        
        Args:
            task_config: 任务配置
        """
        try:
            self._model.load_task_for_editing(task_config)
            self._sync_model_to_view()
            
            logger.info(f"任务加载完成，进入编辑模式: {task_config.id}")
            
        except Exception as e:
            logger.error(f"加载任务进行编辑失败: {e}")
            self._view.show_error(f"加载任务失败: {e}")
    
    def clear_editing_mode(self):
        """清除编辑模式"""
        try:
            self._model.clear_editing_mode()
            self._sync_model_to_view()
            
            logger.info("编辑模式已清除")
            
        except Exception as e:
            logger.error(f"清除编辑模式失败: {e}")
    
    def get_current_task_config(self) -> Optional[TaskConfig]:
        """获取当前任务配置
        
        Returns:
            Optional[TaskConfig]: 当前任务配置
        """
        try:
            return self._model.build_task_config()
            
        except Exception as e:
            logger.error(f"获取当前任务配置失败: {e}")
            return None
    
    def is_form_valid(self) -> bool:
        """检查表单是否有效
        
        Returns:
            bool: 表单是否有效
        """
        return self._model.is_form_valid()
    
    def cleanup(self):
        """清理资源"""
        try:
            # 停止定时器
            if self._validation_timer.isActive():
                self._validation_timer.stop()
            
            # 断开信号连接
            self._disconnect_signals()
            
            logger.info("任务创建Presenter清理完成")
            
        except Exception as e:
            logger.error(f"清理任务创建Presenter失败: {e}")
    
    def _disconnect_signals(self):
        """断开信号连接"""
        try:
            # 断开View信号
            self._view.form_field_changed.disconnect()
            self._view.action_add_requested.disconnect()
            self._view.action_edit_requested.disconnect()
            self._view.action_remove_requested.disconnect()
            self._view.validation_requested.disconnect()
            self._view.task_create_requested.disconnect()
            self._view.form_reset_requested.disconnect()
            
            # 断开Model信号
            self._model.data_changed.disconnect()
            self._model.validation_changed.disconnect()
            
            # 断开外部依赖信号
            self._task_manager.task_created.disconnect(self._on_task_created_success)
            self._task_manager.task_updated.disconnect(self._on_task_updated_success)
            self._task_manager.task_operation_failed.disconnect(self._on_task_operation_failed)
            
            logger.debug("信号断开完成")
            
        except Exception as e:
            logger.error(f"断开信号失败: {e}")