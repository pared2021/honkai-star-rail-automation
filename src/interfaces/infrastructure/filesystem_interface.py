"""文件系统服务接口

定义文件系统操作的基础设施抽象接口。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Union
from pathlib import Path
from datetime import datetime

from .filesystem_types import FilePermission


class IFileSystemService(ABC):
    """文件系统服务接口
    
    定义文件系统操作的基础设施抽象。
    """
    
    @abstractmethod
    async def exists(self, path: Union[str, Path]) -> bool:
        """检查文件或目录是否存在
        
        Args:
            path: 文件或目录路径
            
        Returns:
            是否存在
        """
        pass
    
    @abstractmethod
    async def is_file(self, path: Union[str, Path]) -> bool:
        """检查是否为文件
        
        Args:
            path: 路径
            
        Returns:
            是否为文件
        """
        pass
    
    @abstractmethod
    async def is_directory(self, path: Union[str, Path]) -> bool:
        """检查是否为目录
        
        Args:
            path: 路径
            
        Returns:
            是否为目录
        """
        pass
    
    @abstractmethod
    async def create_directory(self, path: Union[str, Path], parents: bool = True) -> bool:
        """创建目录
        
        Args:
            path: 目录路径
            parents: 是否创建父目录
            
        Returns:
            是否创建成功
        """
        pass
    
    @abstractmethod
    async def remove_file(self, path: Union[str, Path]) -> bool:
        """删除文件
        
        Args:
            path: 文件路径
            
        Returns:
            是否删除成功
        """
        pass
    
    @abstractmethod
    async def remove_directory(self, path: Union[str, Path], recursive: bool = False) -> bool:
        """删除目录
        
        Args:
            path: 目录路径
            recursive: 是否递归删除
            
        Returns:
            是否删除成功
        """
        pass
    
    @abstractmethod
    async def copy_file(self, src: Union[str, Path], dst: Union[str, Path]) -> bool:
        """复制文件
        
        Args:
            src: 源文件路径
            dst: 目标文件路径
            
        Returns:
            是否复制成功
        """
        pass
    
    @abstractmethod
    async def move_file(self, src: Union[str, Path], dst: Union[str, Path]) -> bool:
        """移动文件
        
        Args:
            src: 源文件路径
            dst: 目标文件路径
            
        Returns:
            是否移动成功
        """
        pass
    
    @abstractmethod
    async def read_text(self, path: Union[str, Path], encoding: str = 'utf-8') -> str:
        """读取文本文件
        
        Args:
            path: 文件路径
            encoding: 编码格式
            
        Returns:
            文件内容
        """
        pass
    
    @abstractmethod
    async def write_text(self, path: Union[str, Path], content: str, encoding: str = 'utf-8') -> bool:
        """写入文本文件
        
        Args:
            path: 文件路径
            content: 文件内容
            encoding: 编码格式
            
        Returns:
            是否写入成功
        """
        pass
    
    @abstractmethod
    async def read_bytes(self, path: Union[str, Path]) -> bytes:
        """读取二进制文件
        
        Args:
            path: 文件路径
            
        Returns:
            文件内容
        """
        pass
    
    @abstractmethod
    async def write_bytes(self, path: Union[str, Path], content: bytes) -> bool:
        """写入二进制文件
        
        Args:
            path: 文件路径
            content: 文件内容
            
        Returns:
            是否写入成功
        """
        pass
    
    @abstractmethod
    async def list_directory(self, path: Union[str, Path]) -> List[Path]:
        """列出目录内容
        
        Args:
            path: 目录路径
            
        Returns:
            目录内容列表
        """
        pass
    
    @abstractmethod
    async def get_file_info(self, path: Union[str, Path]) -> Dict[str, Any]:
        """获取文件信息
        
        Args:
            path: 文件路径
            
        Returns:
            文件信息字典
        """
        pass
    
    @abstractmethod
    async def get_file_size(self, path: Union[str, Path]) -> int:
        """获取文件大小
        
        Args:
            path: 文件路径
            
        Returns:
            文件大小（字节）
        """
        pass
    
    @abstractmethod
    async def get_modification_time(self, path: Union[str, Path]) -> datetime:
        """获取文件修改时间
        
        Args:
            path: 文件路径
            
        Returns:
            修改时间
        """
        pass
    
    @abstractmethod
    async def set_permissions(self, path: Union[str, Path], permissions: FilePermission) -> bool:
        """设置文件权限
        
        Args:
            path: 文件路径
            permissions: 权限设置
            
        Returns:
            是否设置成功
        """
        pass
    
    @abstractmethod
    async def get_permissions(self, path: Union[str, Path]) -> FilePermission:
        """获取文件权限
        
        Args:
            path: 文件路径
            
        Returns:
            文件权限
        """
        pass
    
    @abstractmethod
    async def watch_directory(self, path: Union[str, Path], callback: callable) -> str:
        """监控目录变化
        
        Args:
            path: 目录路径
            callback: 变化回调函数
            
        Returns:
            监控器ID
        """
        pass
    
    @abstractmethod
    async def stop_watching(self, watch_id: str) -> bool:
        """停止监控
        
        Args:
            watch_id: 监控器ID
            
        Returns:
            是否停止成功
        """
        pass
    
    @abstractmethod
    async def find_files(
        self,
        path: Union[str, Path],
        pattern: str,
        recursive: bool = True
    ) -> List[Path]:
        """查找文件
        
        Args:
            path: 搜索路径
            pattern: 文件模式
            recursive: 是否递归搜索
            
        Returns:
            匹配的文件列表
        """
        pass