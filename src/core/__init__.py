# -*- coding: utf-8 -*-
"""
核心模块包
"""

# 注释掉相对导入以避免导入错误
# 当作为包使用时，这些导入会在需要时进行
# from .task_manager import TaskConfig, TaskManager
# from .action_executor import (
#     ActionExecutor, ActionResult, ActionType, ClickType, WaitType, LoopType,
#     ClickAction, KeyAction, WaitAction, LoopAction
# )
# from .game_operations import GameOperations, TaskType, OperationResult
# from .game_detector import GameDetector, SceneType, UIElement
# from .config_manager import ConfigManager

__all__ = [
    'TaskConfig', 'TaskManager',
    'ActionExecutor', 'ActionResult', 'ActionType', 'ClickType', 'WaitType', 'LoopType',
    'ClickAction', 'KeyAction', 'WaitAction', 'LoopAction',
    'GameOperations', 'TaskType', 'OperationResult',
    'GameDetector', 'SceneType', 'UIElement',
    'ConfigManager'
]