"""自动化设置界面模块.

提供自动化设置相关的界面组件。
"""

from .automation_settings_model import AutomationSettingsModel, AutomationSettings, AutomationStatus
from .automation_settings_view import AutomationSettingsView, AutomationControlWidget
from .automation_settings_presenter import AutomationSettingsPresenter

__all__ = [
    'AutomationSettingsModel',
    'AutomationSettings',
    'AutomationStatus',
    'AutomationSettingsView',
    'AutomationControlWidget',
    'AutomationSettingsPresenter'
]
