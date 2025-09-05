"""服务层接口

定义应用服务层的抽象接口。
"""

from .task_service_interface import ITaskService
from .automation_service_interface import IAutomationService
from .config_service_interface import IConfigService
from .notification_service_interface import INotificationService
from .monitoring_service_interface import IMonitoringService

__all__ = [
    'ITaskService',
    'IAutomationService',
    'IConfigService',
    'INotificationService',
    'IMonitoringService'
]