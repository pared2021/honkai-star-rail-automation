#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
操作配置服务实现
为操作执行器提供配置管理服务
"""

from typing import Any, Dict
from ..interfaces.i_action_config_service import IActionConfigService
from ..interfaces.i_config_manager import IConfigManager
from ..enums import ClickType, WaitType, LoopType


class ActionConfigService(IActionConfigService):
    """操作配置服务实现"""
    
    def __init__(self, config_manager: IConfigManager):
        """初始化操作配置服务
        
        Args:
            config_manager: 配置管理器
        """
        self._config_manager = config_manager
        
        # 默认配置
        self._default_configs = {
            'click': {
                'click_type': ClickType.SINGLE,
                'button': 'left',
                'delay_before': 0.1,
                'delay_after': 0.1,
                'count': 1,
                'interval': 0.1,
                'area_radius': 5,
                'randomize': True
            },
            'key': {
                'action_type': 'press',
                'delay_before': 0.1,
                'delay_after': 0.1,
                'hold_duration': 0.05,
                'interval': 0.05
            },
            'wait': {
                'duration': 1.0,
                'min_duration': 0.5,
                'max_duration': 2.0,
                'condition_func': None,
                'timeout': 30.0,
                'check_interval': 0.1
            },
            'loop': {
                'count': 1,
                'condition_func': None,
                'actions': [],
                'max_iterations': 1000,
                'break_on_error': True,
                'delay_between_iterations': 0.1
            },
            'executor': {
                'random_offset_radius': 5,
                'delay_variance': 0.1,
                'pyautogui_failsafe': True,
                'pyautogui_pause': 0.01
            }
        }
    
    def get_click_config(self) -> Dict[str, Any]:
        """获取点击操作默认配置"""
        config = {}
        for key, default_value in self._default_configs['click'].items():
            config_key = f'action_executor.click.{key}'
            config[key] = self._config_manager.get(config_key, default_value)
        return config
    
    def get_key_config(self) -> Dict[str, Any]:
        """获取键盘操作默认配置"""
        config = {}
        for key, default_value in self._default_configs['key'].items():
            config_key = f'action_executor.key.{key}'
            config[key] = self._config_manager.get(config_key, default_value)
        return config
    
    def get_wait_config(self) -> Dict[str, Any]:
        """获取等待操作默认配置"""
        config = {}
        for key, default_value in self._default_configs['wait'].items():
            config_key = f'action_executor.wait.{key}'
            config[key] = self._config_manager.get(config_key, default_value)
        return config
    
    def get_loop_config(self) -> Dict[str, Any]:
        """获取循环操作默认配置"""
        config = {}
        for key, default_value in self._default_configs['loop'].items():
            config_key = f'action_executor.loop.{key}'
            config[key] = self._config_manager.get(config_key, default_value)
        return config
    
    def get_executor_config(self) -> Dict[str, Any]:
        """获取执行器配置"""
        config = {}
        for key, default_value in self._default_configs['executor'].items():
            config_key = f'action_executor.{key}'
            config[key] = self._config_manager.get(config_key, default_value)
        return config
    
    def get_config_value(self, key: str, default_value: Any = None) -> Any:
        """获取指定配置值"""
        return self._config_manager.get(key, default_value)