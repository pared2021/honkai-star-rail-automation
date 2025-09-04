"""服务层模块

提供应用服务的统一入口。
"""

from .automation_application_service import (
    AutomationApplicationService,
    AutomationError,
    ElementMatch,
    ElementNotFoundError,
    OperationTimeoutError,
    WindowInfo,
    WindowNotFoundError,
)

__all__ = [
    # 自动化服务
    "AutomationApplicationService",
    "AutomationError",
    "WindowNotFoundError",
    "ElementNotFoundError",
    "OperationTimeoutError",
    "WindowInfo",
    "ElementMatch",
]
