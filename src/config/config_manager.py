# -*- coding: utf-8 -*-
"""
配置管理器 - 负责应用程序配置的加载、保存和管理
"""

import os
import json
from pathlib import Path
from typing import Any, Dict, Optional
from configparser import ConfigParser


class ConfigManager:
    """配置管理器类"""
    
    def __init__(self, config_dir: Optional[Path] = None):
        """初始化配置管理器
        
        Args:
            config_dir: 配置文件目录，默认为项目根目录下的config文件夹
        """
        if config_dir is None:
            project_root = Path(__file__).parent.parent.parent
            config_dir = project_root / "config"
        
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.config_file = self.config_dir / "app_config.ini"
        self.user_config_file = self.config_dir / "user_config.json"
        
        self._config = ConfigParser()
        self._user_config = {}
        
        self._load_default_config()
        self._load_config()
        self._load_user_config()
    
    def _load_default_config(self):
        """加载默认配置"""
        default_config = {
            'game': {
                'resolution': '1920x1080',
                'game_path': '',
                'window_title': '崩坏：星穹铁道',
                'detection_timeout': '30'
            },
            'automation': {
                'click_delay': '1.0',
                'detection_threshold': '0.8',
                'max_retry_count': '3',
                'operation_timeout': '60'
            },
            'security': {
                'random_delay': 'true',
                'safe_mode': 'true',
                'min_random_delay': '0.5',
                'max_random_delay': '2.0'
            },
            'ui': {
                'theme': 'dark',
                'language': 'zh_CN',
                'window_width': '1200',
                'window_height': '800',
                'remember_window_state': 'true'
            },
            'logging': {
                'level': 'INFO',
                'max_file_size': '10MB',
                'backup_count': '5',
                'console_output': 'true'
            }
        }
        
        for section, options in default_config.items():
            self._config.add_section(section)
            for key, value in options.items():
                self._config.set(section, key, value)
    
    def _load_config(self):
        """从文件加载配置"""
        if self.config_file.exists():
            self._config.read(self.config_file, encoding='utf-8')
    
    def _load_user_config(self):
        """加载用户配置"""
        if self.user_config_file.exists():
            try:
                with open(self.user_config_file, 'r', encoding='utf-8') as f:
                    self._user_config = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"加载用户配置失败: {e}")
                self._user_config = {}
    
    def save_config(self) -> bool:
        """保存配置到文件
        
        Returns:
            bool: 保存是否成功
        """
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                self._config.write(f)
            return True
        except IOError as e:
            print(f"保存配置失败: {e}")
            return False
    
    def save_user_config(self) -> bool:
        """保存用户配置到文件
        
        Returns:
            bool: 保存是否成功
        """
        try:
            with open(self.user_config_file, 'w', encoding='utf-8') as f:
                json.dump(self._user_config, f, ensure_ascii=False, indent=2)
            return True
        except IOError as e:
            print(f"保存用户配置失败: {e}")
            return False
    
    def get_setting(self, section: str, key: str, fallback: Any = None) -> Any:
        """获取配置项
        
        Args:
            section: 配置节名
            key: 配置键名
            fallback: 默认值
            
        Returns:
            配置值
        """
        try:
            value = self._config.get(section, key)
            # 尝试转换为合适的类型
            if value.lower() in ('true', 'false'):
                return value.lower() == 'true'
            elif value.isdigit():
                return int(value)
            elif value.replace('.', '').isdigit():
                return float(value)
            return value
        except Exception:
            return fallback
    
    def set_setting(self, section: str, key: str, value: Any) -> bool:
        """设置配置项
        
        Args:
            section: 配置节名
            key: 配置键名
            value: 配置值
            
        Returns:
            bool: 设置是否成功
        """
        try:
            if not self._config.has_section(section):
                self._config.add_section(section)
            
            self._config.set(section, key, str(value))
            return True
        except Exception as e:
            print(f"设置配置项失败: {e}")
            return False
    
    def get_user_setting(self, key: str, fallback: Any = None) -> Any:
        """获取用户配置
        
        Args:
            key: 配置键名
            fallback: 默认值
            
        Returns:
            配置值
        """
        return self._user_config.get(key, fallback)
    
    def set_user_setting(self, key: str, value: Any):
        """设置用户配置
        
        Args:
            key: 配置键名
            value: 配置值
        """
        self._user_config[key] = value
    
    def get_game_config(self) -> Dict[str, Any]:
        """获取游戏相关配置"""
        return {
            'resolution': self.get_setting('game', 'resolution', '1920x1080'),
            'game_path': self.get_setting('game', 'game_path', ''),
            'window_title': self.get_setting('game', 'window_title', '崩坏：星穹铁道'),
            'detection_timeout': self.get_setting('game', 'detection_timeout', 30)
        }
    
    def get_automation_config(self) -> Dict[str, Any]:
        """获取自动化相关配置"""
        return {
            'click_delay': self.get_setting('automation', 'click_delay', 1.0),
            'detection_threshold': self.get_setting('automation', 'detection_threshold', 0.8),
            'max_retry_count': self.get_setting('automation', 'max_retry_count', 3),
            'operation_timeout': self.get_setting('automation', 'operation_timeout', 60)
        }
    
    def get_security_config(self) -> Dict[str, Any]:
        """获取安全相关配置"""
        return {
            'random_delay': self.get_setting('security', 'random_delay', True),
            'safe_mode': self.get_setting('security', 'safe_mode', True),
            'min_random_delay': self.get_setting('security', 'min_random_delay', 0.5),
            'max_random_delay': self.get_setting('security', 'max_random_delay', 2.0)
        }
    
    def get_ui_config(self) -> Dict[str, Any]:
        """获取UI相关配置"""
        return {
            'theme': self.get_setting('ui', 'theme', 'dark'),
            'language': self.get_setting('ui', 'language', 'zh_CN'),
            'window_width': self.get_setting('ui', 'window_width', 1200),
            'window_height': self.get_setting('ui', 'window_height', 800),
            'remember_window_state': self.get_setting('ui', 'remember_window_state', True)
        }