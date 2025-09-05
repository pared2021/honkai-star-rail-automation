"""缓存管理器接口

定义缓存管理器的核心接口契约。
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, Dict, List
from datetime import datetime, timedelta


class ICacheManager(ABC):
    """缓存管理器接口
    
    定义缓存操作的核心接口。
    """
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            缓存值，如果不存在或已过期则返回None
        """
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[timedelta] = None) -> bool:
        """设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 生存时间
            
        Returns:
            是否设置成功
        """
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """删除缓存
        
        Args:
            key: 缓存键
            
        Returns:
            是否删除成功
        """
        pass
    
    @abstractmethod
    def exists(self, key: str) -> bool:
        """检查缓存是否存在
        
        Args:
            key: 缓存键
            
        Returns:
            是否存在
        """
        pass
    
    @abstractmethod
    def clear(self) -> bool:
        """清空所有缓存
        
        Returns:
            是否清空成功
        """
        pass
    
    @abstractmethod
    def clear_expired(self) -> int:
        """清理过期缓存
        
        Returns:
            清理的缓存数量
        """
        pass
    
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息
        
        Returns:
            统计信息字典
        """
        pass
    
    @abstractmethod
    def invalidate_pattern(self, pattern: str) -> int:
        """根据模式失效缓存
        
        Args:
            pattern: 匹配模式
            
        Returns:
            失效的缓存数量
        """
        pass
    
    @abstractmethod
    def invalidate_user_cache(self, user_id: str) -> int:
        """失效用户相关缓存
        
        Args:
            user_id: 用户ID
            
        Returns:
            失效的缓存数量
        """
        pass
    
    @abstractmethod
    def invalidate_task_cache(self, task_id: str) -> int:
        """失效任务相关缓存
        
        Args:
            task_id: 任务ID
            
        Returns:
            失效的缓存数量
        """
        pass
    
    @abstractmethod
    def get_cache_size(self) -> int:
        """获取缓存大小
        
        Returns:
            缓存项数量
        """
        pass
    
    @abstractmethod
    def set_max_size(self, max_size: int) -> None:
        """设置最大缓存大小
        
        Args:
            max_size: 最大缓存项数量
        """
        pass
    
    @abstractmethod
    def get_keys(self, pattern: Optional[str] = None) -> List[str]:
        """获取缓存键列表
        
        Args:
            pattern: 匹配模式，如果为None则返回所有键
            
        Returns:
            缓存键列表
        """
        pass
    
    @abstractmethod
    def get_ttl(self, key: str) -> Optional[timedelta]:
        """获取缓存剩余生存时间
        
        Args:
            key: 缓存键
            
        Returns:
            剩余生存时间，如果不存在或无过期时间则返回None
        """
        pass
    
    @abstractmethod
    def extend_ttl(self, key: str, ttl: timedelta) -> bool:
        """延长缓存生存时间
        
        Args:
            key: 缓存键
            ttl: 新的生存时间
            
        Returns:
            是否延长成功
        """
        pass
    
    @abstractmethod
    def cached_query(self, key: str, query_func: callable, ttl: Optional[timedelta] = None) -> Any:
        """带缓存的查询
        
        Args:
            key: 缓存键
            query_func: 查询函数
            ttl: 生存时间
            
        Returns:
            查询结果
        """
        pass