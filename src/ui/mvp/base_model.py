# -*- coding: utf-8 -*-
"""
MVP模式基础Model类

定义了数据模型的基础接口和通用功能。
"""

import logging
from abc import ABC, ABCMeta, abstractmethod
from typing import Any, Dict, Optional, List
from PyQt6.QtCore import QObject, pyqtSignal

logger = logging.getLogger(__name__)


class QObjectMeta(type(QObject), ABCMeta):
    """解决QObject和ABC元类冲突的元类"""
    pass


class BaseModel(QObject, ABC, metaclass=QObjectMeta):
    """MVP模式基础Model类
    
    提供数据管理的基础功能，包括：
    - 数据变更通知
    - 验证机制
    - 错误处理
    """
    
    # 信号定义
    data_changed = pyqtSignal(str, object)  # field_name, new_value
    validation_failed = pyqtSignal(str, str)  # field_name, error_message
    model_updated = pyqtSignal()  # 模型整体更新
    
    def __init__(self):
        super().__init__()
        self._data: Dict[str, Any] = {}
        self._validators: Dict[str, List[callable]] = {}
        self._dirty_fields: set = set()
        
        logger.debug(f"{self.__class__.__name__} 初始化完成")
    
    def get_data(self, field_name: str, default: Any = None) -> Any:
        """获取字段数据
        
        Args:
            field_name: 字段名
            default: 默认值
            
        Returns:
            字段值
        """
        return self._data.get(field_name, default)
    
    def set_data(self, field_name: str, value: Any, validate: bool = True) -> bool:
        """设置字段数据
        
        Args:
            field_name: 字段名
            value: 新值
            validate: 是否进行验证
            
        Returns:
            是否设置成功
        """
        try:
            # 验证数据
            if validate and not self._validate_field(field_name, value):
                return False
            
            # 检查值是否真的改变了
            old_value = self._data.get(field_name)
            if old_value == value:
                return True
            
            # 设置新值
            self._data[field_name] = value
            self._dirty_fields.add(field_name)
            
            # 发射变更信号
            self.data_changed.emit(field_name, value)
            
            logger.debug(f"字段 {field_name} 已更新: {old_value} -> {value}")
            return True
            
        except Exception as e:
            logger.error(f"设置字段 {field_name} 失败: {e}")
            self.validation_failed.emit(field_name, str(e))
            return False
    
    def get_all_data(self) -> Dict[str, Any]:
        """获取所有数据"""
        return self._data.copy()
    
    def update_data(self, data: Dict[str, Any], validate: bool = True) -> bool:
        """批量更新数据
        
        Args:
            data: 要更新的数据字典
            validate: 是否进行验证
            
        Returns:
            是否全部更新成功
        """
        success = True
        
        for field_name, value in data.items():
            if not self.set_data(field_name, value, validate):
                success = False
        
        if success:
            self.model_updated.emit()
            logger.debug(f"模型数据批量更新完成")
        
        return success
    
    def add_validator(self, field_name: str, validator: callable):
        """添加字段验证器
        
        Args:
            field_name: 字段名
            validator: 验证函数，接受值参数，返回bool或抛出异常
        """
        if field_name not in self._validators:
            self._validators[field_name] = []
        
        self._validators[field_name].append(validator)
        logger.debug(f"为字段 {field_name} 添加验证器")
    
    def _validate_field(self, field_name: str, value: Any) -> bool:
        """验证字段值
        
        Args:
            field_name: 字段名
            value: 要验证的值
            
        Returns:
            是否验证通过
        """
        validators = self._validators.get(field_name, [])
        
        for validator in validators:
            try:
                if not validator(value):
                    error_msg = f"字段 {field_name} 验证失败"
                    logger.warning(error_msg)
                    self.validation_failed.emit(field_name, error_msg)
                    return False
            except Exception as e:
                error_msg = f"字段 {field_name} 验证异常: {e}"
                logger.error(error_msg)
                self.validation_failed.emit(field_name, error_msg)
                return False
        
        return True
    
    def is_dirty(self, field_name: Optional[str] = None) -> bool:
        """检查是否有未保存的更改
        
        Args:
            field_name: 特定字段名，None表示检查整个模型
            
        Returns:
            是否有更改
        """
        if field_name is None:
            return len(self._dirty_fields) > 0
        return field_name in self._dirty_fields
    
    def mark_clean(self, field_name: Optional[str] = None):
        """标记为已保存状态
        
        Args:
            field_name: 特定字段名，None表示标记整个模型
        """
        if field_name is None:
            self._dirty_fields.clear()
            logger.debug("模型已标记为干净状态")
        else:
            self._dirty_fields.discard(field_name)
            logger.debug(f"字段 {field_name} 已标记为干净状态")
    
    def get_dirty_fields(self) -> set:
        """获取所有脏字段"""
        return self._dirty_fields.copy()
    
    @abstractmethod
    def load_data(self) -> bool:
        """加载数据（子类实现）
        
        Returns:
            是否加载成功
        """
        pass
    
    @abstractmethod
    def save_data(self) -> bool:
        """保存数据（子类实现）
        
        Returns:
            是否保存成功
        """
        pass
    
    def reset(self):
        """重置模型状态"""
        self._data.clear()
        self._dirty_fields.clear()
        logger.debug(f"{self.__class__.__name__} 已重置")