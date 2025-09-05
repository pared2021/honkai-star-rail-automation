"""数据库管理器接口

定义数据库管理器的核心接口契约。
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Union
from datetime import datetime


class IDatabaseManager(ABC):
    """数据库管理器接口
    
    定义数据库操作的核心接口。
    """
    
    @abstractmethod
    async def connect(self) -> bool:
        """连接数据库
        
        Returns:
            是否连接成功
        """
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """断开数据库连接
        
        Returns:
            是否断开成功
        """
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """检查是否已连接
        
        Returns:
            是否已连接
        """
        pass
    
    @abstractmethod
    async def execute_query(
        self, 
        query: str, 
        params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """执行查询
        
        Args:
            query: SQL查询语句
            params: 查询参数
            
        Returns:
            查询结果列表
        """
        pass
    
    @abstractmethod
    async def execute_non_query(
        self, 
        query: str, 
        params: Optional[Dict[str, Any]] = None
    ) -> int:
        """执行非查询语句
        
        Args:
            query: SQL语句
            params: 查询参数
            
        Returns:
            影响的行数
        """
        pass
    
    @abstractmethod
    async def execute_scalar(
        self, 
        query: str, 
        params: Optional[Dict[str, Any]] = None
    ) -> Any:
        """执行标量查询
        
        Args:
            query: SQL查询语句
            params: 查询参数
            
        Returns:
            查询结果的第一行第一列值
        """
        pass
    
    @abstractmethod
    async def begin_transaction(self) -> Any:
        """开始事务
        
        Returns:
            事务对象
        """
        pass
    
    @abstractmethod
    async def commit_transaction(self, transaction: Any) -> bool:
        """提交事务
        
        Args:
            transaction: 事务对象
            
        Returns:
            是否提交成功
        """
        pass
    
    @abstractmethod
    async def rollback_transaction(self, transaction: Any) -> bool:
        """回滚事务
        
        Args:
            transaction: 事务对象
            
        Returns:
            是否回滚成功
        """
        pass
    
    @abstractmethod
    async def insert(
        self, 
        table: str, 
        data: Dict[str, Any],
        return_id: bool = False
    ) -> Union[bool, Any]:
        """插入数据
        
        Args:
            table: 表名
            data: 要插入的数据
            return_id: 是否返回插入的ID
            
        Returns:
            如果return_id为True则返回插入的ID，否则返回是否插入成功
        """
        pass
    
    @abstractmethod
    async def update(
        self, 
        table: str, 
        data: Dict[str, Any],
        where: Dict[str, Any]
    ) -> int:
        """更新数据
        
        Args:
            table: 表名
            data: 要更新的数据
            where: 更新条件
            
        Returns:
            影响的行数
        """
        pass
    
    @abstractmethod
    async def delete(self, table: str, where: Dict[str, Any]) -> int:
        """删除数据
        
        Args:
            table: 表名
            where: 删除条件
            
        Returns:
            影响的行数
        """
        pass
    
    @abstractmethod
    async def select(
        self, 
        table: str,
        columns: Optional[List[str]] = None,
        where: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """查询数据
        
        Args:
            table: 表名
            columns: 要查询的列，如果为None则查询所有列
            where: 查询条件
            order_by: 排序条件
            limit: 限制数量
            offset: 偏移量
            
        Returns:
            查询结果列表
        """
        pass
    
    @abstractmethod
    async def select_one(
        self, 
        table: str,
        columns: Optional[List[str]] = None,
        where: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """查询单条数据
        
        Args:
            table: 表名
            columns: 要查询的列，如果为None则查询所有列
            where: 查询条件
            
        Returns:
            查询结果，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    async def count(
        self, 
        table: str,
        where: Optional[Dict[str, Any]] = None
    ) -> int:
        """统计数据数量
        
        Args:
            table: 表名
            where: 统计条件
            
        Returns:
            数据数量
        """
        pass
    
    @abstractmethod
    async def exists(
        self, 
        table: str,
        where: Dict[str, Any]
    ) -> bool:
        """检查数据是否存在
        
        Args:
            table: 表名
            where: 检查条件
            
        Returns:
            是否存在
        """
        pass
    
    @abstractmethod
    async def create_table(self, table_name: str, schema: Dict[str, str]) -> bool:
        """创建表
        
        Args:
            table_name: 表名
            schema: 表结构定义
            
        Returns:
            是否创建成功
        """
        pass
    
    @abstractmethod
    async def drop_table(self, table_name: str) -> bool:
        """删除表
        
        Args:
            table_name: 表名
            
        Returns:
            是否删除成功
        """
        pass
    
    @abstractmethod
    async def table_exists(self, table_name: str) -> bool:
        """检查表是否存在
        
        Args:
            table_name: 表名
            
        Returns:
            是否存在
        """
        pass
    
    @abstractmethod
    async def get_table_schema(self, table_name: str) -> Optional[Dict[str, str]]:
        """获取表结构
        
        Args:
            table_name: 表名
            
        Returns:
            表结构定义，如果表不存在则返回None
        """
        pass
    
    @abstractmethod
    async def backup_database(self, backup_path: str) -> bool:
        """备份数据库
        
        Args:
            backup_path: 备份文件路径
            
        Returns:
            是否备份成功
        """
        pass
    
    @abstractmethod
    async def restore_database(self, backup_path: str) -> bool:
        """恢复数据库
        
        Args:
            backup_path: 备份文件路径
            
        Returns:
            是否恢复成功
        """
        pass
    
    @abstractmethod
    def get_connection_info(self) -> Dict[str, Any]:
        """获取连接信息
        
        Returns:
            连接信息字典
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """健康检查
        
        Returns:
            健康状态信息
        """
        pass