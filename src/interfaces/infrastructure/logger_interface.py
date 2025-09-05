"""日志接口

定义日志记录的抽象接口。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from enum import Enum
from datetime import datetime


class LogLevel(Enum):
    """日志级别枚举"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ILogger(ABC):
    """日志接口
    
    定义日志记录的核心功能。
    """
    
    @abstractmethod
    def debug(self, message: str, **kwargs) -> None:
        """记录调试日志
        
        Args:
            message: 日志消息
            **kwargs: 额外参数
        """
        pass
    
    @abstractmethod
    def info(self, message: str, **kwargs) -> None:
        """记录信息日志
        
        Args:
            message: 日志消息
            **kwargs: 额外参数
        """
        pass
    
    @abstractmethod
    def warning(self, message: str, **kwargs) -> None:
        """记录警告日志
        
        Args:
            message: 日志消息
            **kwargs: 额外参数
        """
        pass
    
    @abstractmethod
    def error(self, message: str, exception: Optional[Exception] = None, **kwargs) -> None:
        """记录错误日志
        
        Args:
            message: 日志消息
            exception: 异常对象
            **kwargs: 额外参数
        """
        pass
    
    @abstractmethod
    def critical(self, message: str, exception: Optional[Exception] = None, **kwargs) -> None:
        """记录严重错误日志
        
        Args:
            message: 日志消息
            exception: 异常对象
            **kwargs: 额外参数
        """
        pass
    
    @abstractmethod
    def log(self, level: LogLevel, message: str, **kwargs) -> None:
        """记录指定级别的日志
        
        Args:
            level: 日志级别
            message: 日志消息
            **kwargs: 额外参数
        """
        pass
    
    @abstractmethod
    def set_level(self, level: LogLevel) -> None:
        """设置日志级别
        
        Args:
            level: 日志级别
        """
        pass
    
    @abstractmethod
    def get_level(self) -> LogLevel:
        """获取当前日志级别
        
        Returns:
            当前日志级别
        """
        pass
    
    @abstractmethod
    def add_handler(self, handler_type: str, **config) -> bool:
        """添加日志处理器
        
        Args:
            handler_type: 处理器类型（file, console, rotating等）
            **config: 处理器配置
            
        Returns:
            是否添加成功
        """
        pass
    
    @abstractmethod
    def remove_handler(self, handler_name: str) -> bool:
        """移除日志处理器
        
        Args:
            handler_name: 处理器名称
            
        Returns:
            是否移除成功
        """
        pass
    
    @abstractmethod
    def get_handlers(self) -> List[str]:
        """获取所有处理器名称
        
        Returns:
            处理器名称列表
        """
        pass
    
    @abstractmethod
    def configure(self, config: Dict[str, Any]) -> bool:
        """配置日志器
        
        Args:
            config: 配置字典
            
        Returns:
            是否配置成功
        """
        pass
    
    @abstractmethod
    def get_logs(self, 
                level: Optional[LogLevel] = None,
                start_time: Optional[datetime] = None,
                end_time: Optional[datetime] = None,
                limit: int = 100) -> List[Dict[str, Any]]:
        """获取日志记录
        
        Args:
            level: 日志级别过滤
            start_time: 开始时间
            end_time: 结束时间
            limit: 限制数量
            
        Returns:
            日志记录列表
        """
        pass
    
    @abstractmethod
    def clear_logs(self, 
                  level: Optional[LogLevel] = None,
                  older_than_days: Optional[int] = None) -> int:
        """清理日志
        
        Args:
            level: 日志级别过滤
            older_than_days: 清理多少天前的日志
            
        Returns:
            清理的日志数量
        """
        pass
    
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """获取日志统计信息
        
        Returns:
            统计信息字典
        """
        pass
    
    @abstractmethod
    def rotate_logs(self) -> bool:
        """轮转日志文件
        
        Returns:
            是否轮转成功
        """
        pass
    
    @abstractmethod
    def flush(self) -> None:
        """刷新日志缓冲区"""
        pass
    
    @abstractmethod
    def close(self) -> None:
        """关闭日志器"""
        pass