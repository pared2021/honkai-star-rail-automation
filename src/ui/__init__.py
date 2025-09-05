# -*- coding: utf-8 -*-
"""
UI模块 - 用户界面组件
"""

try:
    from .monitoring_dashboard import MonitoringDashboard
except ImportError:
    from typing import TYPE_CHECKING
    if TYPE_CHECKING:
        from .monitoring_dashboard import MonitoringDashboard
    else:
        MonitoringDashboard = None  # type: ignore

__all__ = ["MonitoringDashboard"]
