# -*- coding: utf-8 -*-
"""
任务创建Model层
MVP架构中的数据模型层，负责任务创建相关的数据管理
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import json

from loguru import logger

from core.enums import ActionType
from models.task_models import Task, TaskConfig, TaskPriority, TaskType, ValidationLevel
from ui.mvp.base_model import BaseModel


class TaskCreationModel(BaseModel):
    """任务创建数据模型
    
    管理任务创建过程中的数据状态和业务逻辑
    """
    
    def __init__(self):
        super().__init__()
        
        # 当前任务配置数据
        self._task_config: Optional[TaskConfig] = None
        self._editing_task_id: Optional[str] = None
        self._is_editing_mode: bool = False
        
        # 表单数据
        self._form_data: Dict[str, Any] = self._get_default_form_data()
        
        # 动作列表
        self._actions: List[Dict[str, Any]] = []
        
        # 验证结果
        self._validation_results: List[Any] = []
        
        logger.info("任务创建Model初始化完成")
    
    def _get_default_form_data(self) -> Dict[str, Any]:
        """获取默认表单数据"""
        return {
            # 基本信息
            'name': '',
            'description': '',
            'task_type': TaskType.AUTOMATION,
            'priority': TaskPriority.MEDIUM,
            
            # 执行设置
            'max_duration': self._get_config_value('ui.task_creation.default_max_duration', 300),
            'retry_count': self._get_config_value('ui.task_creation.default_retry_count', 3),
            'retry_interval': self._get_config_value('ui.task_creation.default_retry_interval', 1.0),
            'safe_mode': self._get_config_value('ui.task_creation.default_safe_mode', True),
            
            # 调度设置
            'immediate': True,
            'scheduled_time': datetime.now() + timedelta(hours=self._get_config_value('ui.task_creation.default_schedule_hours', 1)),
            'repeat': False,
            'repeat_interval': self._get_config_value('ui.task_creation.default_repeat_interval', 60),
            
            # 高级设置
            'custom_params': {},
            'validation_level': ValidationLevel.WARNING,
        }
    
    @property
    def task_config(self) -> Optional[TaskConfig]:
        """获取当前任务配置"""
        return self._task_config
    
    @property
    def editing_task_id(self) -> Optional[str]:
        """获取编辑中的任务ID"""
        return self._editing_task_id
    
    @property
    def is_editing_mode(self) -> bool:
        """是否为编辑模式"""
        return self._is_editing_mode
    
    @property
    def form_data(self) -> Dict[str, Any]:
        """获取表单数据"""
        return self._form_data.copy()
    
    @property
    def actions(self) -> List[Dict[str, Any]]:
        """获取动作列表"""
        return self._actions.copy()
    
    @property
    def validation_results(self) -> List[Any]:
        """获取验证结果"""
        return self._validation_results.copy()
    
    def set_form_field(self, field: str, value: Any) -> bool:
        """设置表单字段值
        
        Args:
            field: 字段名
            value: 字段值
            
        Returns:
            bool: 是否设置成功
        """
        try:
            if field in self._form_data:
                old_value = self._form_data[field]
                self._form_data[field] = value
                
                # 触发数据变更事件
                self.data_changed.emit('form_field', field, {'old': old_value, 'new': value})
                
                logger.debug(f"表单字段更新: {field} = {value}")
                return True
            else:
                logger.warning(f"未知的表单字段: {field}")
                return False
                
        except Exception as e:
            logger.error(f"设置表单字段失败: {field} = {value}, 错误: {e}")
            return False
    
    def get_form_field(self, field: str, default: Any = None) -> Any:
        """获取表单字段值
        
        Args:
            field: 字段名
            default: 默认值
            
        Returns:
            Any: 字段值
        """
        return self._form_data.get(field, default)
    
    def add_action(self, action: Dict[str, Any]) -> bool:
        """添加动作
        
        Args:
            action: 动作配置
            
        Returns:
            bool: 是否添加成功
        """
        try:
            self._actions.append(action)
            self.data_changed.emit('actions', 'add', action)
            logger.info(f"添加动作: {action}")
            return True
            
        except Exception as e:
            logger.error(f"添加动作失败: {e}")
            return False
    
    def update_action(self, index: int, action: Dict[str, Any]) -> bool:
        """更新动作
        
        Args:
            index: 动作索引
            action: 新的动作配置
            
        Returns:
            bool: 是否更新成功
        """
        try:
            if 0 <= index < len(self._actions):
                old_action = self._actions[index]
                self._actions[index] = action
                self.data_changed.emit('actions', 'update', {'index': index, 'old': old_action, 'new': action})
                logger.info(f"更新动作[{index}]: {action}")
                return True
            else:
                logger.warning(f"动作索引超出范围: {index}")
                return False
                
        except Exception as e:
            logger.error(f"更新动作失败: {e}")
            return False
    
    def remove_action(self, index: int) -> bool:
        """删除动作
        
        Args:
            index: 动作索引
            
        Returns:
            bool: 是否删除成功
        """
        try:
            if 0 <= index < len(self._actions):
                removed_action = self._actions.pop(index)
                self.data_changed.emit('actions', 'remove', {'index': index, 'action': removed_action})
                logger.info(f"删除动作[{index}]: {removed_action}")
                return True
            else:
                logger.warning(f"动作索引超出范围: {index}")
                return False
                
        except Exception as e:
            logger.error(f"删除动作失败: {e}")
            return False
    
    def clear_actions(self):
        """清空动作列表"""
        self._actions.clear()
        self.data_changed.emit('actions', 'clear', None)
        logger.info("动作列表已清空")
    
    def load_task_for_edit(self, task: Task) -> bool:
        """加载任务进行编辑
        
        Args:
            task: 要编辑的任务
            
        Returns:
            bool: 是否加载成功
        """
        try:
            self._editing_task_id = task.task_id
            self._is_editing_mode = True
            
            # 加载基本信息
            self._form_data['name'] = task.name
            self._form_data['description'] = task.description or ''
            self._form_data['task_type'] = task.task_type
            self._form_data['priority'] = task.priority
            
            # 加载配置信息
            config = task.config or {}
            self._form_data['max_duration'] = config.get('max_duration', self._get_config_value('ui.task_creation.default_max_duration', 300))
            self._form_data['retry_count'] = config.get('retry_count', self._get_config_value('ui.task_creation.default_retry_count', 3))
            self._form_data['retry_interval'] = config.get('retry_interval', self._get_config_value('ui.task_creation.default_retry_interval', 1.0))
            self._form_data['safe_mode'] = config.get('safe_mode', True)
            
            # 加载调度设置
            scheduled_time = config.get('scheduled_time')
            if scheduled_time:
                self._form_data['immediate'] = False
                if isinstance(scheduled_time, str):
                    self._form_data['scheduled_time'] = datetime.fromisoformat(scheduled_time)
                else:
                    self._form_data['scheduled_time'] = scheduled_time
            else:
                self._form_data['immediate'] = True
            
            repeat_interval = config.get('repeat_interval')
            if repeat_interval:
                self._form_data['repeat'] = True
                self._form_data['repeat_interval'] = repeat_interval
            else:
                self._form_data['repeat'] = False
            
            # 加载动作序列
            self._actions = config.get('actions', [])
            
            # 加载自定义参数
            self._form_data['custom_params'] = config.get('custom_params', {})
            
            # 加载验证级别
            self._form_data['validation_level'] = config.get('validation_level', ValidationLevel.WARNING)
            
            # 触发数据加载事件
            self.data_changed.emit('task_loaded', task.task_id, task)
            
            logger.info(f"任务编辑数据加载完成: {task.task_id}")
            return True
            
        except Exception as e:
            logger.error(f"加载任务编辑数据失败: {e}")
            return False
    
    def clear_form(self):
        """清空表单"""
        self._editing_task_id = None
        self._is_editing_mode = False
        self._form_data = self._get_default_form_data()
        self._actions.clear()
        self._validation_results.clear()
        
        # 触发数据清空事件
        self.data_changed.emit('form_cleared', None, None)
        
        logger.info("表单已清空")
    
    def build_task_config(self) -> TaskConfig:
        """构建任务配置
        
        Returns:
            TaskConfig: 构建的任务配置
            
        Raises:
            ValueError: 配置数据无效时抛出
        """
        try:
            # 验证必填字段
            name = self._form_data['name'].strip()
            if not name:
                raise ValueError("任务名称不能为空")
            
            # 构建基本配置
            config = TaskConfig(
                name=name,
                description=self._form_data['description'].strip(),
                task_type=self._form_data['task_type'],
                priority=self._form_data['priority'],
                max_retry_count=self._form_data['retry_count'],
                timeout_seconds=self._form_data['max_duration'],
                actions=self._actions.copy(),
                custom_params=self._form_data['custom_params'].copy() if self._form_data['custom_params'] else {},
            )
            
            # 设置调度配置
            if not self._form_data['immediate']:
                config.schedule_enabled = True
                scheduled_time = self._form_data['scheduled_time']
                if isinstance(scheduled_time, datetime):
                    config.schedule_time = scheduled_time.strftime("%H:%M")
            
            # 设置重复间隔
            if self._form_data['repeat']:
                config.repeat_interval = self._form_data['repeat_interval']
            
            self._task_config = config
            logger.info(f"任务配置构建完成: {name}")
            return config
            
        except Exception as e:
            logger.error(f"构建任务配置失败: {e}")
            raise
    
    def set_validation_results(self, results: List[Any]):
        """设置验证结果
        
        Args:
            results: 验证结果列表
        """
        self._validation_results = results.copy()
        self.data_changed.emit('validation_results', None, results)
        logger.debug(f"验证结果已更新: {len(results)} 项")
    
    def has_validation_errors(self) -> bool:
        """检查是否有验证错误
        
        Returns:
            bool: 是否有错误级别的验证问题
        """
        return any(r.level.value == "error" for r in self._validation_results)
    
    def get_validation_errors(self) -> List[str]:
        """获取验证错误信息
        
        Returns:
            List[str]: 错误信息列表
        """
        return [r.message for r in self._validation_results if r.level.value == "error"]
    
    def get_validation_warnings(self) -> List[str]:
        """获取验证警告信息
        
        Returns:
            List[str]: 警告信息列表
        """
        return [r.message for r in self._validation_results if r.level.value == "warning"]
    
    def is_form_valid(self) -> bool:
        """检查表单是否有效
        
        Returns:
            bool: 表单是否有效
        """
        # 检查必填字段
        name = self._form_data.get('name', '').strip()
        if not name:
            return False
        
        # 检查任务类型
        if not isinstance(self._form_data.get('task_type'), TaskType):
            return False
        
        # 检查优先级
        if not isinstance(self._form_data.get('priority'), TaskPriority):
            return False
        
        return True
    
    def get_form_validation_message(self) -> str:
        """获取表单验证消息
        
        Returns:
            str: 验证消息
        """
        if not self._form_data.get('name', '').strip():
            return "请输入任务名称"
        
        if not isinstance(self._form_data.get('task_type'), TaskType):
            return "请选择任务类型"
        
        if not isinstance(self._form_data.get('priority'), TaskPriority):
            return "请选择任务优先级"
        
        return "表单验证通过"