"""缓存服务接口

定义缓存操作的基础设施抽象接口。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta


class ICacheService(ABC):
    """缓存服务接口
    
    定义缓存操作的基础设施抽象。
    """
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            缓存值，不存在返回None
        """
        pass
    
    @abstractmethod
    async def set(self, 
                  key: str, 
                  value: Any, 
                  ttl: Optional[Union[int, timedelta]] = None) -> bool:
        """设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒或timedelta对象）
            
        Returns:
            是否设置成功
        """
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """删除缓存
        
        Args:
            key: 缓存键
            
        Returns:
            是否删除成功
        """
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """检查缓存是否存在
        
        Args:
            key: 缓存键
            
        Returns:
            是否存在
        """
        pass
    
    @abstractmethod
    async def expire(self, key: str, ttl: Union[int, timedelta]) -> bool:
        """设置缓存过期时间
        
        Args:
            key: 缓存键
            ttl: 过期时间（秒或timedelta对象）
            
        Returns:
            是否设置成功
        """
        pass
    
    @abstractmethod
    async def ttl(self, key: str) -> Optional[int]:
        """获取缓存剩余过期时间
        
        Args:
            key: 缓存键
            
        Returns:
            剩余秒数，-1表示永不过期，None表示不存在
        """
        pass
    
    @abstractmethod
    async def clear(self, pattern: Optional[str] = None) -> int:
        """清理缓存
        
        Args:
            pattern: 键模式，None表示清理所有
            
        Returns:
            清理的键数量
        """
        pass
    
    @abstractmethod
    async def keys(self, pattern: str = "*") -> List[str]:
        """获取匹配的键列表
        
        Args:
            pattern: 键模式
            
        Returns:
            匹配的键列表
        """
        pass
    
    @abstractmethod
    async def mget(self, keys: List[str]) -> Dict[str, Any]:
        """批量获取缓存值
        
        Args:
            keys: 缓存键列表
            
        Returns:
            键值对字典
        """
        pass
    
    @abstractmethod
    async def mset(self, mapping: Dict[str, Any], ttl: Optional[Union[int, timedelta]] = None) -> bool:
        """批量设置缓存值
        
        Args:
            mapping: 键值对字典
            ttl: 过期时间（秒或timedelta对象）
            
        Returns:
            是否设置成功
        """
        pass
    
    @abstractmethod
    async def increment(self, key: str, delta: Union[int, float] = 1) -> Union[int, float]:
        """递增缓存值
        
        Args:
            key: 缓存键
            delta: 递增量
            
        Returns:
            递增后的值
        """
        pass
    
    @abstractmethod
    async def decrement(self, key: str, delta: Union[int, float] = 1) -> Union[int, float]:
        """递减缓存值
        
        Args:
            key: 缓存键
            delta: 递减量
            
        Returns:
            递减后的值
        """
        pass
    
    @abstractmethod
    async def get_or_set(self, 
                        key: str, 
                        default_factory: callable, 
                        ttl: Optional[Union[int, timedelta]] = None) -> Any:
        """获取缓存值，不存在则设置默认值
        
        Args:
            key: 缓存键
            default_factory: 默认值工厂函数
            ttl: 过期时间（秒或timedelta对象）
            
        Returns:
            缓存值
        """
        pass
    
    @abstractmethod
    async def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息
        
        Returns:
            统计信息字典
        """
        pass
    
    @abstractmethod
    async def flush_all(self) -> bool:
        """清空所有缓存
        
        Returns:
            是否清空成功
        """
        pass
    
    @abstractmethod
    async def ping(self) -> bool:
        """检查缓存服务连接
        
        Returns:
            是否连接正常
        """
        pass