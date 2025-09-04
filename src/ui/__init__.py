# -*- coding: utf-8 -*-
"""
UI模块 - 用户界面组件
"""

try:
    from .monitoring_dashboard import MonitoringDashboard
except ImportError:
    MonitoringDashboard = None

__all__ = ["MonitoringDashboard"]
