"""配置管理器接口

定义配置管理的核心接口契约。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List, Union
from pathlib import Path
from enum import Enum


class ConfigFormat(Enum):
    """配置文件格式枚举"""
    JSON = "json"
    YAML = "yaml"
    TOML = "toml"
    INI = "ini"
    ENV = "env"


class ConfigScope(Enum):
    """配置作用域枚举"""
    GLOBAL = "global"
    USER = "user"
    PROJECT = "project"
    RUNTIME = "runtime"


class IConfigManager(ABC):
    """配置管理器接口
    
    定义配置管理的核心接口。
    """
    
    @abstractmethod
    def load_config(
        self, 
        config_path: Union[str, Path],
        format_type: Optional[ConfigFormat] = None,
        scope: ConfigScope = ConfigScope.PROJECT
    ) -> bool:
        """加载配置文件
        
        Args:
            config_path: 配置文件路径
            format_type: 配置文件格式，如果为None则自动检测
            scope: 配置作用域
            
        Returns:
            是否加载成功
        """
        pass
    
    @abstractmethod
    def save_config(
        self, 
        config_path: Union[str, Path],
        format_type: Optional[ConfigFormat] = None,
        scope: ConfigScope = ConfigScope.PROJECT
    ) -> bool:
        """保存配置文件
        
        Args:
            config_path: 配置文件路径
            format_type: 配置文件格式，如果为None则根据文件扩展名确定
            scope: 配置作用域
            
        Returns:
            是否保存成功
        """
        pass
    
    @abstractmethod
    def get(
        self, 
        key: str, 
        default: Any = None,
        scope: Optional[ConfigScope] = None
    ) -> Any:
        """获取配置值
        
        Args:
            key: 配置键，支持点分隔的嵌套键
            default: 默认值
            scope: 配置作用域，如果为None则按优先级查找
            
        Returns:
            配置值
        """
        pass
    
    @abstractmethod
    def set(
        self, 
        key: str, 
        value: Any,
        scope: ConfigScope = ConfigScope.RUNTIME
    ) -> bool:
        """设置配置值
        
        Args:
            key: 配置键，支持点分隔的嵌套键
            value: 配置值
            scope: 配置作用域
            
        Returns:
            是否设置成功
        """
        pass
    
    @abstractmethod
    def delete(
        self, 
        key: str,
        scope: Optional[ConfigScope] = None
    ) -> bool:
        """删除配置项
        
        Args:
            key: 配置键
            scope: 配置作用域，如果为None则从所有作用域删除
            
        Returns:
            是否删除成功
        """
        pass
    
    @abstractmethod
    def exists(
        self, 
        key: str,
        scope: Optional[ConfigScope] = None
    ) -> bool:
        """检查配置项是否存在
        
        Args:
            key: 配置键
            scope: 配置作用域，如果为None则在所有作用域中查找
            
        Returns:
            是否存在
        """
        pass
    
    @abstractmethod
    def get_all(
        self, 
        scope: Optional[ConfigScope] = None
    ) -> Dict[str, Any]:
        """获取所有配置
        
        Args:
            scope: 配置作用域，如果为None则返回合并后的所有配置
            
        Returns:
            配置字典
        """
        pass
    
    @abstractmethod
    def get_section(
        self, 
        section: str,
        scope: Optional[ConfigScope] = None
    ) -> Dict[str, Any]:
        """获取配置段
        
        Args:
            section: 配置段名称
            scope: 配置作用域
            
        Returns:
            配置段字典
        """
        pass
    
    @abstractmethod
    def set_section(
        self, 
        section: str, 
        config: Dict[str, Any],
        scope: ConfigScope = ConfigScope.RUNTIME
    ) -> bool:
        """设置配置段
        
        Args:
            section: 配置段名称
            config: 配置字典
            scope: 配置作用域
            
        Returns:
            是否设置成功
        """
        pass
    
    @abstractmethod
    def merge_config(
        self, 
        config: Dict[str, Any],
        scope: ConfigScope = ConfigScope.RUNTIME
    ) -> bool:
        """合并配置
        
        Args:
            config: 要合并的配置字典
            scope: 配置作用域
            
        Returns:
            是否合并成功
        """
        pass
    
    @abstractmethod
    def clear(
        self, 
        scope: Optional[ConfigScope] = None
    ) -> bool:
        """清空配置
        
        Args:
            scope: 配置作用域，如果为None则清空所有作用域
            
        Returns:
            是否清空成功
        """
        pass
    
    @abstractmethod
    def get_keys(
        self, 
        scope: Optional[ConfigScope] = None
    ) -> List[str]:
        """获取所有配置键
        
        Args:
            scope: 配置作用域
            
        Returns:
            配置键列表
        """
        pass
    
    @abstractmethod
    def get_sections(
        self, 
        scope: Optional[ConfigScope] = None
    ) -> List[str]:
        """获取所有配置段
        
        Args:
            scope: 配置作用域
            
        Returns:
            配置段列表
        """
        pass
    
    @abstractmethod
    def validate_config(
        self, 
        schema: Dict[str, Any],
        scope: Optional[ConfigScope] = None
    ) -> bool:
        """验证配置
        
        Args:
            schema: 配置模式
            scope: 配置作用域
            
        Returns:
            是否验证通过
        """
        pass
    
    @abstractmethod
    def get_validation_errors(
        self, 
        schema: Dict[str, Any],
        scope: Optional[ConfigScope] = None
    ) -> List[str]:
        """获取配置验证错误
        
        Args:
            schema: 配置模式
            scope: 配置作用域
            
        Returns:
            验证错误列表
        """
        pass
    
    @abstractmethod
    def watch_config(
        self, 
        callback: callable,
        key: Optional[str] = None,
        scope: Optional[ConfigScope] = None
    ) -> str:
        """监听配置变化
        
        Args:
            callback: 变化回调函数
            key: 监听的配置键，如果为None则监听所有
            scope: 配置作用域
            
        Returns:
            监听器ID
        """
        pass
    
    @abstractmethod
    def unwatch_config(self, watcher_id: str) -> bool:
        """取消配置监听
        
        Args:
            watcher_id: 监听器ID
            
        Returns:
            是否取消成功
        """
        pass
    
    @abstractmethod
    def reload_config(
        self, 
        scope: Optional[ConfigScope] = None
    ) -> bool:
        """重新加载配置
        
        Args:
            scope: 配置作用域，如果为None则重新加载所有
            
        Returns:
            是否重新加载成功
        """
        pass
    
    @abstractmethod
    def backup_config(
        self, 
        backup_path: Union[str, Path],
        scope: Optional[ConfigScope] = None
    ) -> bool:
        """备份配置
        
        Args:
            backup_path: 备份文件路径
            scope: 配置作用域
            
        Returns:
            是否备份成功
        """
        pass
    
    @abstractmethod
    def restore_config(
        self, 
        backup_path: Union[str, Path],
        scope: ConfigScope = ConfigScope.PROJECT
    ) -> bool:
        """恢复配置
        
        Args:
            backup_path: 备份文件路径
            scope: 配置作用域
            
        Returns:
            是否恢复成功
        """
        pass
    
    @abstractmethod
    def get_config_info(self) -> Dict[str, Any]:
        """获取配置信息
        
        Returns:
            配置信息字典
        """
        pass
    
    @abstractmethod
    def get_scope_priority(self) -> List[ConfigScope]:
        """获取作用域优先级
        
        Returns:
            作用域优先级列表
        """
        pass
    
    @abstractmethod
    def set_scope_priority(self, priority: List[ConfigScope]) -> bool:
        """设置作用域优先级
        
        Args:
            priority: 作用域优先级列表
            
        Returns:
            是否设置成功
        """
        pass