"""配置仓储接口

定义配置相关的数据访问接口。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from .base_repository_interface import IBaseRepository


class IConfigRepository(IBaseRepository, ABC):
    """配置仓储接口
    
    定义配置相关的数据访问操作。
    """
    
    @abstractmethod
    async def get_config(self, key: str, default: Any = None) -> Any:
        """获取配置值
        
        Args:
            key: 配置键
            default: 默认值
            
        Returns:
            配置值
        """
        pass
    
    @abstractmethod
    async def set_config(self, key: str, value: Any) -> bool:
        """设置配置值
        
        Args:
            key: 配置键
            value: 配置值
            
        Returns:
            是否设置成功
        """
        pass
    
    @abstractmethod
    async def get_config_section(self, section: str) -> Dict[str, Any]:
        """获取配置段
        
        Args:
            section: 配置段名称
            
        Returns:
            配置段字典
        """
        pass
    
    @abstractmethod
    async def set_config_section(self, section: str, config: Dict[str, Any]) -> bool:
        """设置配置段
        
        Args:
            section: 配置段名称
            config: 配置字典
            
        Returns:
            是否设置成功
        """
        pass
    
    @abstractmethod
    async def delete_config(self, key: str) -> bool:
        """删除配置
        
        Args:
            key: 配置键
            
        Returns:
            是否删除成功
        """
        pass
    
    @abstractmethod
    async def get_all_configs(self) -> Dict[str, Any]:
        """获取所有配置
        
        Returns:
            所有配置字典
        """
        pass
    
    @abstractmethod
    async def backup_config(self, backup_name: str) -> bool:
        """备份配置
        
        Args:
            backup_name: 备份名称
            
        Returns:
            是否备份成功
        """
        pass
    
    @abstractmethod
    async def restore_config(self, backup_name: str) -> bool:
        """恢复配置
        
        Args:
            backup_name: 备份名称
            
        Returns:
            是否恢复成功
        """
        pass
    
    @abstractmethod
    async def list_backups(self) -> List[str]:
        """列出所有备份
        
        Returns:
            备份名称列表
        """
        pass
    
    @abstractmethod
    async def validate_config(self, config: Dict[str, Any]) -> bool:
        """验证配置
        
        Args:
            config: 配置字典
            
        Returns:
            是否有效
        """
        pass
    
    @abstractmethod
    async def reset_to_defaults(self) -> bool:
        """重置为默认配置
        
        Returns:
            是否重置成功
        """
        pass