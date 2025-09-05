"""配置管理接口

定义配置管理的抽象接口，用于集中化配置管理。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Type, TypeVar
from pathlib import Path

from .configuration_types import (
    ConfigurationSource,
    ConfigurationFormat
)

T = TypeVar('T')


class IConfigurationProvider(ABC):
    """配置提供者接口"""
    
    @abstractmethod
    def load(self) -> Dict[str, Any]:
        """加载配置
        
        Returns:
            配置字典
        """
        pass
    
    @abstractmethod
    def save(self, config: Dict[str, Any]) -> None:
        """保存配置
        
        Args:
            config: 配置字典
        """
        pass
    
    @abstractmethod
    def get_source(self) -> ConfigurationSource:
        """获取配置源类型
        
        Returns:
            配置源类型
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """检查配置源是否可用
        
        Returns:
            是否可用
        """
        pass
    
    @abstractmethod
    def watch_changes(self, callback: callable) -> None:
        """监听配置变化
        
        Args:
            callback: 变化回调函数
        """
        pass
    
    @abstractmethod
    def stop_watching(self) -> None:
        """停止监听配置变化"""
        pass


class IConfigurationManager(ABC):
    """配置管理器接口"""
    
    @abstractmethod
    def add_provider(self, provider: IConfigurationProvider, priority: int = 0) -> None:
        """添加配置提供者
        
        Args:
            provider: 配置提供者
            priority: 优先级（数值越大优先级越高）
        """
        pass
    
    @abstractmethod
    def remove_provider(self, provider: IConfigurationProvider) -> None:
        """移除配置提供者
        
        Args:
            provider: 配置提供者
        """
        pass
    
    @abstractmethod
    def get_value(self, key: str, default: T = None) -> T:
        """获取配置值
        
        Args:
            key: 配置键（支持点分隔的嵌套键）
            default: 默认值
            
        Returns:
            配置值
        """
        pass
    
    @abstractmethod
    def set_value(self, key: str, value: Any) -> None:
        """设置配置值
        
        Args:
            key: 配置键
            value: 配置值
        """
        pass
    
    @abstractmethod
    def has_key(self, key: str) -> bool:
        """检查配置键是否存在
        
        Args:
            key: 配置键
            
        Returns:
            是否存在
        """
        pass
    
    @abstractmethod
    def remove_key(self, key: str) -> bool:
        """移除配置键
        
        Args:
            key: 配置键
            
        Returns:
            是否移除成功
        """
        pass
    
    @abstractmethod
    def get_section(self, section: str) -> Dict[str, Any]:
        """获取配置节
        
        Args:
            section: 节名称
            
        Returns:
            配置节字典
        """
        pass
    
    @abstractmethod
    def get_all_keys(self, prefix: str = "") -> List[str]:
        """获取所有配置键
        
        Args:
            prefix: 键前缀过滤
            
        Returns:
            配置键列表
        """
        pass
    
    @abstractmethod
    def reload(self) -> None:
        """重新加载配置"""
        pass
    
    @abstractmethod
    def save(self) -> None:
        """保存配置"""
        pass
    
    @abstractmethod
    def validate(self, schema: Dict[str, Any]) -> List[str]:
        """验证配置
        
        Args:
            schema: 配置模式
            
        Returns:
            验证错误列表
        """
        pass
    
    @abstractmethod
    def bind_to_object(self, obj: object, section: str = "") -> None:
        """将配置绑定到对象
        
        Args:
            obj: 目标对象
            section: 配置节
        """
        pass
    
    @abstractmethod
    def get_typed_value(self, key: str, value_type: Type[T], default: T = None) -> T:
        """获取类型化配置值
        
        Args:
            key: 配置键
            value_type: 值类型
            default: 默认值
            
        Returns:
            类型化配置值
        """
        pass
    
    @abstractmethod
    def subscribe_to_changes(self, key: str, callback: callable) -> None:
        """订阅配置变化
        
        Args:
            key: 配置键
            callback: 变化回调函数
        """
        pass
    
    @abstractmethod
    def unsubscribe_from_changes(self, key: str, callback: callable) -> None:
        """取消订阅配置变化
        
        Args:
            key: 配置键
            callback: 变化回调函数
        """
        pass
    
    @abstractmethod
    def get_configuration_info(self) -> Dict[str, Any]:
        """获取配置信息
        
        Returns:
            配置信息字典
        """
        pass
    
    @abstractmethod
    def export_configuration(self, format_type: ConfigurationFormat, file_path: Path) -> None:
        """导出配置
        
        Args:
            format_type: 格式类型
            file_path: 文件路径
        """
        pass
    
    @abstractmethod
    def import_configuration(self, format_type: ConfigurationFormat, file_path: Path) -> None:
        """导入配置
        
        Args:
            format_type: 格式类型
            file_path: 文件路径
        """
        pass


class IConfigurationBuilder(ABC):
    """配置构建器接口"""
    
    @abstractmethod
    def add_json_file(self, file_path: Path, optional: bool = False) -> 'IConfigurationBuilder':
        """添加JSON配置文件
        
        Args:
            file_path: 文件路径
            optional: 是否可选
            
        Returns:
            配置构建器
        """
        pass
    
    @abstractmethod
    def add_yaml_file(self, file_path: Path, optional: bool = False) -> 'IConfigurationBuilder':
        """添加YAML配置文件
        
        Args:
            file_path: 文件路径
            optional: 是否可选
            
        Returns:
            配置构建器
        """
        pass
    
    @abstractmethod
    def add_ini_file(self, file_path: Path, optional: bool = False) -> 'IConfigurationBuilder':
        """添加INI配置文件
        
        Args:
            file_path: 文件路径
            optional: 是否可选
            
        Returns:
            配置构建器
        """
        pass
    
    @abstractmethod
    def add_environment_variables(self, prefix: str = "") -> 'IConfigurationBuilder':
        """添加环境变量
        
        Args:
            prefix: 环境变量前缀
            
        Returns:
            配置构建器
        """
        pass
    
    @abstractmethod
    def add_command_line(self, args: List[str]) -> 'IConfigurationBuilder':
        """添加命令行参数
        
        Args:
            args: 命令行参数
            
        Returns:
            配置构建器
        """
        pass
    
    @abstractmethod
    def add_in_memory(self, config: Dict[str, Any]) -> 'IConfigurationBuilder':
        """添加内存配置
        
        Args:
            config: 配置字典
            
        Returns:
            配置构建器
        """
        pass
    
    @abstractmethod
    def add_provider(self, provider: IConfigurationProvider) -> 'IConfigurationBuilder':
        """添加自定义配置提供者
        
        Args:
            provider: 配置提供者
            
        Returns:
            配置构建器
        """
        pass
    
    @abstractmethod
    def build(self) -> IConfigurationManager:
        """构建配置管理器
        
        Returns:
            配置管理器
        """
        pass