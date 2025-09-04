"""核心模块

包含任务执行引擎、事件系统等核心组件。
"""

from .error_handling import (
    DatabaseRecoveryHandler,
    ErrorCategory,
    ErrorClassifier,
    ErrorContext,
    ErrorHandler,
    ErrorRecoveryHandler,
    ErrorSeverity,
    ExponentialBackoffStrategy,
    FixedDelayStrategy,
    LinearBackoffStrategy,
    NetworkRecoveryHandler,
    RetryStrategy,
    with_error_handling,
)
from .events import (
    ActionExecutedEvent,
    AutomationEvent,
    Event,
    EventBus,
    EventHandler,
    LoggingEventHandler,
    MetricsEventHandler,
    ScreenshotTakenEvent,
    TaskCreatedEvent,
    TaskEvent,
    TaskExecutionCompletedEvent,
    TaskExecutionStartedEvent,
    TaskStatusChangedEvent,
    WindowDetectedEvent,
)
from .sync_adapter import (
    AsyncCallback,
    AsyncToSyncAdapter,
    CallbackData,
    CallbackManager,
    CallbackType,
    EventBridge,
    SyncCallback,
    SyncToAsyncAdapter,
    async_sync,
    default_event_bridge,
    sync_async,
)
from .task_executor import (
    ExecutorStatus,
    RetryPolicy,
    TaskExecutionContext,
    TaskExecutor,
)

__all__ = [
    # 任务执行引擎
    "TaskExecutor",
    "ExecutorStatus",
    "TaskExecutionContext",
    "RetryPolicy",
    # 事件系统
    "Event",
    "TaskEvent",
    "TaskCreatedEvent",
    "TaskStatusChangedEvent",
    "TaskExecutionStartedEvent",
    "TaskExecutionCompletedEvent",
    "AutomationEvent",
    "WindowDetectedEvent",
    "ActionExecutedEvent",
    "ScreenshotTakenEvent",
    "EventHandler",
    "EventBus",
    "LoggingEventHandler",
    "MetricsEventHandler",
    # 错误处理
    "ErrorSeverity",
    "ErrorCategory",
    "ErrorContext",
    "ErrorClassifier",
    "RetryStrategy",
    "ExponentialBackoffStrategy",
    "LinearBackoffStrategy",
    "FixedDelayStrategy",
    "ErrorRecoveryHandler",
    "DatabaseRecoveryHandler",
    "NetworkRecoveryHandler",
    "ErrorHandler",
    "with_error_handling",
    # 同步适配器
    "CallbackType",
    "CallbackData",
    "AsyncCallback",
    "SyncCallback",
    "CallbackManager",
    "AsyncToSyncAdapter",
    "SyncToAsyncAdapter",
    "EventBridge",
    "default_event_bridge",
    "sync_async",
    "async_sync",
]
