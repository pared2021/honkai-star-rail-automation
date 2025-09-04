# -*- coding: utf-8 -*-
"""
统一枚举定义模块
包含项目中所有通用的枚举类型定义
"""

from enum import Enum


class ActionType(Enum):
    """统一的动作类型枚举

    整合了所有模块中的动作类型定义
    """

    # 基础动作类型
    CLICK = "click"
    DOUBLE_CLICK = "double_click"
    RIGHT_CLICK = "right_click"
    KEY_PRESS = "key_press"
    KEY_COMBINATION = "key_combination"
    WAIT = "wait"
    SCREENSHOT = "screenshot"

    # 高级动作类型
    SCROLL = "scroll"
    DRAG = "drag"
    TEXT_INPUT = "text_input"
    TYPE_TEXT = "type_text"

    # 条件动作类型
    WAIT_FOR_TEMPLATE = "wait_for_template"
    LOOP = "loop"

    # 自定义动作类型
    CUSTOM = "custom"


class ActionStatus(Enum):
    """动作执行状态枚举"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ClickType(Enum):
    """点击类型枚举"""

    SINGLE = "single"  # 单次点击
    DOUBLE = "double"  # 双击
    RIGHT = "right"  # 右键点击
    AREA = "area"  # 区域点击
    CONTINUOUS = "continuous"  # 连续点击


class WaitType(Enum):
    """等待类型枚举"""

    FIXED = "fixed"  # 固定等待
    CONDITION = "condition"  # 条件等待
    RANDOM = "random"  # 随机等待


class LoopType(Enum):
    """循环类型枚举"""

    COUNT = "count"  # 次数循环
    CONDITION = "condition"  # 条件循环
    INFINITE = "infinite"  # 无限循环


class TaskStatus(Enum):
    """任务状态枚举"""

    PENDING = "pending"
    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"
    CANCELLED = "cancelled"


class TaskType(Enum):
    """任务类型枚举（仅包含任务类型，不包含动作类型）"""

    DAILY_MISSION = "daily_mission"  # 日常任务
    DAILY_MISSIONS = "daily_missions"  # 日常任务（复数形式）
    DAILY_STAMINA = "daily_stamina"  # 日常体力消耗
    WEEKLY_MISSION = "weekly_mission"  # 周常任务
    MATERIAL_FARMING = "material_farming"  # 材料刷取
    CUSTOM_SEQUENCE = "custom_sequence"  # 自定义序列
    EXPLORATION = "exploration"  # 探索任务
    COMBAT_TRAINING = "combat_training"  # 战斗训练
    COMBAT_AUTO = "combat_auto"  # 自动战斗
    MAIL_COLLECTION = "mail_collection"  # 邮件收集
    CUSTOM = "custom"  # 自定义任务


class TaskPriority(Enum):
    """任务优先级枚举"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"
