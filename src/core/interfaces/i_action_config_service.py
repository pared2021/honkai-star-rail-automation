#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
操作配置服务接口
为操作执行器提供配置管理服务
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class IActionConfigService(ABC):
    """操作配置服务接口"""
    
    @abstractmethod
    def get_click_config(self) -> Dict[str, Any]:
        """获取点击操作默认配置
        
        Returns:
            点击操作配置字典
        """
        pass
    
    @abstractmethod
    def get_key_config(self) -> Dict[str, Any]:
        """获取键盘操作默认配置
        
        Returns:
            键盘操作配置字典
        """
        pass
    
    @abstractmethod
    def get_wait_config(self) -> Dict[str, Any]:
        """获取等待操作默认配置
        
        Returns:
            等待操作配置字典
        """
        pass
    
    @abstractmethod
    def get_loop_config(self) -> Dict[str, Any]:
        """获取循环操作默认配置
        
        Returns:
            循环操作配置字典
        """
        pass
    
    @abstractmethod
    def get_executor_config(self) -> Dict[str, Any]:
        """获取执行器配置
        
        Returns:
            执行器配置字典
        """
        pass
    
    @abstractmethod
    def get_config_value(self, key: str, default_value: Any = None) -> Any:
        """获取指定配置值
        
        Args:
            key: 配置键
            default_value: 默认值
            
        Returns:
            配置值
        """
        pass