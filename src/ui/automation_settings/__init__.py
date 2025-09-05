"""自动化设置模块

该模块提供自动化设置的MVP架构组件，包括Model、View、Presenter和MVP组合类。
"""

from .automation_settings_model import AutomationSettingsModel
from .automation_settings_view import AutomationSettingsView
from .automation_settings_presenter import AutomationSettingsPresenter
from .automation_settings_mvp import AutomationSettingsMVP

__all__ = [
    'AutomationSettingsModel',
    'AutomationSettingsView', 
    'AutomationSettingsPresenter',
    'AutomationSettingsMVP'
]