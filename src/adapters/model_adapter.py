# -*- coding: utf-8 -*-
"""
数据模型适配器

本模块提供数据模型之间的转换功能，用于兼容旧代码和实现渐进式迁移。
支持从dataclass、字典等格式转换为统一的Pydantic模型。
"""

from typing import Dict, Any, Union, Optional
from dataclasses import is_dataclass, asdict
from src.models.task_models import TaskConfig, Task, TaskType, TaskStatus, TaskPriority
import logging

logger = logging.getLogger(__name__)


class ModelAdapter:
    """数据模型适配器，用于兼容旧代码"""
    
    @staticmethod
    def dataclass_to_pydantic(dataclass_obj, target_class=None):
        """将dataclass对象转换为Pydantic模型"""
        if target_class is None:
            target_class = TaskConfig
        
        try:
            if is_dataclass(dataclass_obj):
                data = asdict(dataclass_obj)
            elif hasattr(dataclass_obj, '__dict__'):
                data = dataclass_obj.__dict__.copy()
            else:
                # 假设已经是字典格式
                data = dataclass_obj
            
            # 处理枚举类型转换
            data = ModelAdapter._normalize_enum_values(data)
            
            if target_class == TaskConfig:
                return TaskConfig.from_dict(data)
            elif target_class == Task:
                return ModelAdapter.dict_to_task(data)
            else:
                raise ValueError(f"Unsupported target class: {target_class}")
        except Exception as e:
            logger.error(f"Failed to convert dataclass to {target_class.__name__}: {e}")
            raise ValueError(f"Cannot convert dataclass to {target_class.__name__}: {e}")
    
    @staticmethod
    def dict_to_model(data: Dict[str, Any], target_class):
        """将字典转换为指定的模型类"""
        if target_class == TaskConfig:
            return ModelAdapter.dict_to_task_config(data)
        elif target_class == Task:
            return ModelAdapter.dict_to_task(data)
        else:
            raise ValueError(f"Unsupported target class: {target_class}")
    
    @staticmethod
    def batch_convert(obj_list: list, target_class):
        """批量转换对象列表"""
        converted_list = []
        for obj in obj_list:
            try:
                if isinstance(obj, dict):
                    converted = ModelAdapter.dict_to_model(obj, target_class)
                elif is_dataclass(obj) or hasattr(obj, '__dict__'):
                    converted = ModelAdapter.dataclass_to_pydantic(obj, target_class)
                else:
                    raise ValueError(f"Cannot convert {type(obj)} to {target_class.__name__}")
                converted_list.append(converted)
            except Exception as e:
                logger.warning(f"Failed to convert object in batch: {e}")
                raise
        return converted_list
    

    
    @staticmethod
    def dict_to_task_config(data: Dict[str, Any]) -> TaskConfig:
        """将字典转换为TaskConfig"""
        try:
            # 处理枚举类型转换
            normalized_data = ModelAdapter._normalize_enum_values(data.copy())
            return TaskConfig.from_dict(normalized_data)
        except Exception as e:
            logger.error(f"Failed to convert dict to TaskConfig: {e}")
            raise ValueError(f"Cannot convert dict to TaskConfig: {e}")
    
    @staticmethod
    def dict_to_task(data: Dict[str, Any]) -> Task:
        """将字典转换为Task"""
        try:
            # 处理嵌套的config字段
            normalized_data = data.copy()
            
            if 'config' in normalized_data and isinstance(normalized_data['config'], dict):
                normalized_data['config'] = ModelAdapter.dict_to_task_config(normalized_data['config'])
            
            # 处理枚举类型转换
            normalized_data = ModelAdapter._normalize_enum_values(normalized_data)
            
            return Task.from_dict(normalized_data)
        except Exception as e:
            logger.error(f"Failed to convert dict to Task: {e}")
            raise ValueError(f"Cannot convert dict to Task: {e}")
    
    @staticmethod
    def ensure_task_config(obj: Union[TaskConfig, Dict[str, Any], Any]) -> TaskConfig:
        """确保对象是TaskConfig类型"""
        if isinstance(obj, TaskConfig):
            return obj
        elif isinstance(obj, dict):
            return ModelAdapter.dict_to_task_config(obj)
        elif is_dataclass(obj) or hasattr(obj, '__dict__'):
            return ModelAdapter.dataclass_to_pydantic(obj)
        else:
            raise ValueError(f"Cannot convert {type(obj)} to TaskConfig")
    
    @staticmethod
    def ensure_task(obj: Union[Task, Dict[str, Any], Any]) -> Task:
        """确保对象是Task类型"""
        if isinstance(obj, Task):
            return obj
        elif isinstance(obj, dict):
            return ModelAdapter.dict_to_task(obj)
        elif is_dataclass(obj) or hasattr(obj, '__dict__'):
            # 对于dataclass Task对象的转换
            if is_dataclass(obj):
                data = asdict(obj)
            else:
                data = obj.__dict__.copy()
            return ModelAdapter.dict_to_task(data)
        else:
            raise ValueError(f"Cannot convert {type(obj)} to Task")
    
    @staticmethod
    def _normalize_enum_values(data: Dict[str, Any]) -> Dict[str, Any]:
        """标准化枚举值"""
        normalized = data.copy()
        
        # 处理task_type - 确保转换为字符串值
        if 'task_type' in normalized:
            task_type = normalized['task_type']
            if hasattr(task_type, 'value'):
                # 如果是枚举对象，取其值
                normalized['task_type'] = task_type.value
            elif isinstance(task_type, str):
                # 尝试通过枚举名称或值查找
                found = False
                for enum_item in TaskType:
                    if task_type == enum_item.value or task_type.upper() == enum_item.name:
                        normalized['task_type'] = enum_item.value
                        found = True
                        break
                if not found:
                    raise ValueError(f"Invalid task_type: {task_type}")
        
        # 处理priority - 确保转换为整数值
        if 'priority' in normalized:
            priority = normalized['priority']
            if hasattr(priority, 'value'):
                # 如果是枚举对象，取其值
                normalized['priority'] = priority.value
            elif isinstance(priority, str):
                priority_map = {
                    'low': 1,
                    'medium': 2,
                    'high': 3,
                    'urgent': 4
                }
                normalized['priority'] = priority_map.get(priority.lower(), 2)
            elif isinstance(priority, int):
                # 验证是否为有效的优先级值
                valid_values = [e.value for e in TaskPriority]
                if priority not in valid_values:
                    normalized['priority'] = 2  # 默认为medium
        
        # 处理status - 确保转换为字符串值
        if 'status' in normalized:
            status = normalized['status']
            if hasattr(status, 'value'):
                # 如果是枚举对象，取其值
                normalized['status'] = status.value
            elif isinstance(status, str):
                # 验证是否为有效的枚举值
                valid_values = [e.value for e in TaskStatus]
                if status not in valid_values:
                    normalized['status'] = 'pending'  # 默认状态
        
        return normalized
    
    @staticmethod
    def convert_legacy_task_list(task_list: list) -> list:
        """转换旧格式的任务列表"""
        converted_tasks = []
        for task_data in task_list:
            try:
                task = ModelAdapter.ensure_task(task_data)
                converted_tasks.append(task)
            except Exception as e:
                logger.warning(f"Failed to convert task: {e}, skipping...")
                continue
        return converted_tasks
    
    @staticmethod
    def validate_conversion(original_data: Dict[str, Any], converted_obj: Union[TaskConfig, Task]) -> bool:
        """验证转换是否正确"""
        try:
            # 将转换后的对象转回字典进行比较
            converted_dict = converted_obj.to_dict()
            
            # 检查关键字段是否一致
            key_fields = ['name', 'task_type'] if isinstance(converted_obj, TaskConfig) else ['task_id', 'user_id']
            
            for field in key_fields:
                if field in original_data:
                    original_value = original_data[field]
                    converted_value = converted_dict.get(field)
                    
                    # 处理枚举类型的比较
                    if hasattr(original_value, 'value'):
                        original_value = original_value.value
                    if hasattr(converted_value, 'value'):
                        converted_value = converted_value.value
                    
                    if original_value != converted_value:
                        logger.warning(f"Field {field} mismatch: {original_value} != {converted_value}")
                        return False
            
            return True
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return False


# 便利函数
def safe_convert_to_task_config(obj: Any) -> Optional[TaskConfig]:
    """安全地转换为TaskConfig，失败时返回None"""
    try:
        return ModelAdapter.ensure_task_config(obj)
    except Exception as e:
        logger.warning(f"Failed to convert to TaskConfig: {e}")
        return None


def safe_convert_to_task(obj: Any) -> Optional[Task]:
    """安全地转换为Task，失败时返回None"""
    try:
        return ModelAdapter.ensure_task(obj)
    except Exception as e:
        logger.warning(f"Failed to convert to Task: {e}")
        return None


def batch_convert_tasks(task_list: list) -> tuple[list, list]:
    """批量转换任务列表，返回(成功列表, 失败列表)"""
    success_list = []
    failed_list = []
    
    for i, task_data in enumerate(task_list):
        converted_task = safe_convert_to_task(task_data)
        if converted_task:
            success_list.append(converted_task)
        else:
            failed_list.append((i, task_data))
    
    return success_list, failed_list