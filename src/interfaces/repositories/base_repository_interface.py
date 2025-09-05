"""基础仓储接口

定义通用的数据访问接口。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TypeVar, Generic

T = TypeVar('T')


class IBaseRepository(ABC, Generic[T]):
    """基础仓储接口
    
    定义通用的CRUD操作接口。
    """
    
    @abstractmethod
    async def create(self, entity: T) -> T:
        """创建实体
        
        Args:
            entity: 要创建的实体
            
        Returns:
            创建后的实体
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, entity_id: str) -> Optional[T]:
        """根据ID获取实体
        
        Args:
            entity_id: 实体ID
            
        Returns:
            实体对象，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    async def update(self, entity: T) -> T:
        """更新实体
        
        Args:
            entity: 要更新的实体
            
        Returns:
            更新后的实体
        """
        pass
    
    @abstractmethod
    async def delete(self, entity_id: str) -> bool:
        """删除实体
        
        Args:
            entity_id: 实体ID
            
        Returns:
            是否删除成功
        """
        pass
    
    @abstractmethod
    async def find_all(self, filters: Optional[Dict[str, Any]] = None) -> List[T]:
        """查找所有实体
        
        Args:
            filters: 过滤条件
            
        Returns:
            实体列表
        """
        pass
    
    @abstractmethod
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """统计实体数量
        
        Args:
            filters: 过滤条件
            
        Returns:
            实体数量
        """
        pass
    
    @abstractmethod
    async def exists(self, entity_id: str) -> bool:
        """检查实体是否存在
        
        Args:
            entity_id: 实体ID
            
        Returns:
            是否存在
        """
        pass