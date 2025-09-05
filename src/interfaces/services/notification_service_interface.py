"""通知服务接口

定义通知管理的业务逻辑接口。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from enum import Enum


class NotificationType(Enum):
    """通知类型枚举"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"


class NotificationPriority(Enum):
    """通知优先级枚举"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class INotificationService(ABC):
    """通知服务接口
    
    定义通知管理的业务操作。
    """
    
    @abstractmethod
    async def send_notification(
        self,
        title: str,
        message: str,
        notification_type: NotificationType = NotificationType.INFO,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        data: Optional[Dict[str, Any]] = None
    ) -> str:
        """发送通知
        
        Args:
            title: 通知标题
            message: 通知消息
            notification_type: 通知类型
            priority: 通知优先级
            data: 附加数据
            
        Returns:
            通知ID
        """
        pass
    
    @abstractmethod
    async def send_system_notification(
        self,
        title: str,
        message: str,
        icon_path: Optional[str] = None
    ) -> bool:
        """发送系统通知
        
        Args:
            title: 通知标题
            message: 通知消息
            icon_path: 图标路径
            
        Returns:
            是否发送成功
        """
        pass
    
    @abstractmethod
    async def send_email_notification(
        self,
        to_email: str,
        subject: str,
        body: str,
        is_html: bool = False
    ) -> bool:
        """发送邮件通知
        
        Args:
            to_email: 收件人邮箱
            subject: 邮件主题
            body: 邮件内容
            is_html: 是否为HTML格式
            
        Returns:
            是否发送成功
        """
        pass
    
    @abstractmethod
    async def get_notification(self, notification_id: str) -> Optional[Dict[str, Any]]:
        """获取通知
        
        Args:
            notification_id: 通知ID
            
        Returns:
            通知信息
        """
        pass
    
    @abstractmethod
    async def get_notifications(
        self,
        limit: int = 50,
        offset: int = 0,
        notification_type: Optional[NotificationType] = None,
        priority: Optional[NotificationPriority] = None,
        unread_only: bool = False
    ) -> List[Dict[str, Any]]:
        """获取通知列表
        
        Args:
            limit: 限制数量
            offset: 偏移量
            notification_type: 通知类型过滤
            priority: 优先级过滤
            unread_only: 仅未读通知
            
        Returns:
            通知列表
        """
        pass
    
    @abstractmethod
    async def mark_as_read(self, notification_id: str) -> bool:
        """标记为已读
        
        Args:
            notification_id: 通知ID
            
        Returns:
            是否标记成功
        """
        pass
    
    @abstractmethod
    async def mark_all_as_read(self) -> bool:
        """标记所有为已读
        
        Returns:
            是否标记成功
        """
        pass
    
    @abstractmethod
    async def delete_notification(self, notification_id: str) -> bool:
        """删除通知
        
        Args:
            notification_id: 通知ID
            
        Returns:
            是否删除成功
        """
        pass
    
    @abstractmethod
    async def clear_notifications(
        self,
        notification_type: Optional[NotificationType] = None,
        older_than_days: Optional[int] = None
    ) -> int:
        """清理通知
        
        Args:
            notification_type: 通知类型过滤
            older_than_days: 清理多少天前的通知
            
        Returns:
            清理的通知数量
        """
        pass
    
    @abstractmethod
    async def get_unread_count(self) -> int:
        """获取未读通知数量
        
        Returns:
            未读通知数量
        """
        pass
    
    @abstractmethod
    async def subscribe_to_notifications(self, callback: callable) -> bool:
        """订阅通知
        
        Args:
            callback: 回调函数
            
        Returns:
            是否订阅成功
        """
        pass
    
    @abstractmethod
    async def unsubscribe_from_notifications(self, callback: callable) -> bool:
        """取消订阅通知
        
        Args:
            callback: 回调函数
            
        Returns:
            是否取消订阅成功
        """
        pass
    
    @abstractmethod
    async def configure_notification_settings(self, settings: Dict[str, Any]) -> bool:
        """配置通知设置
        
        Args:
            settings: 通知设置
            
        Returns:
            是否配置成功
        """
        pass
    
    @abstractmethod
    async def get_notification_settings(self) -> Dict[str, Any]:
        """获取通知设置
        
        Returns:
            通知设置
        """
        pass