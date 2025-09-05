"""服务层模块

提供UI层和核心层之间的解耦服务。
"""

from .application_service import ApplicationService
from .ui_service_facade import UIServiceFacade

__all__ = [
    'ApplicationService',
    'UIServiceFacade'
]