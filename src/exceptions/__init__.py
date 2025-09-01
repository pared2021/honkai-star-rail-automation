"""统一异常体系模块

提供整个应用程序的统一异常定义，避免重复定义。
按照分层架构组织异常类型：
- 基础异常：所有自定义异常的基类
- 领域异常：业务逻辑相关的异常
- 应用异常：应用层相关的异常
- 基础设施异常：数据访问、外部服务等异常
"""

from typing import Optional, Any, Dict


# ==================== 基础异常 ====================

class BaseApplicationError(Exception):
    """应用程序基础异常类
    
    所有自定义异常的基类，提供统一的错误处理接口。
    """
    
    def __init__(
        self, 
        message: str, 
        error_code: str = "UNKNOWN_ERROR", 
        original_error: Optional[Exception] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.original_error = original_error
        self.context = context or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "error_code": self.error_code,
            "context": self.context,
            "original_error": str(self.original_error) if self.original_error else None
        }


# ==================== 验证异常 ====================

class ValidationError(BaseApplicationError):
    """数据验证异常"""
    
    def __init__(self, message: str, field: Optional[str] = None, original_error: Optional[Exception] = None):
        context = {"field": field} if field else {}
        super().__init__(message, "VALIDATION_ERROR", original_error, context)
        self.field = field


# ==================== 任务相关异常 ====================

class TaskError(BaseApplicationError):
    """任务相关异常基类"""
    
    def __init__(self, message: str, error_code: str, task_id: Optional[str] = None, original_error: Optional[Exception] = None):
        context = {"task_id": task_id} if task_id else {}
        super().__init__(message, error_code, original_error, context)
        self.task_id = task_id


class TaskNotFoundError(TaskError):
    """任务不存在异常"""
    
    def __init__(self, task_id: str, original_error: Optional[Exception] = None):
        super().__init__(f"Task not found: {task_id}", "TASK_NOT_FOUND", task_id, original_error)


class TaskValidationError(TaskError):
    """任务验证异常"""
    
    def __init__(self, message: str, task_id: Optional[str] = None, original_error: Optional[Exception] = None):
        super().__init__(message, "TASK_VALIDATION_ERROR", task_id, original_error)


class TaskStateError(TaskError):
    """任务状态异常"""
    
    def __init__(self, message: str, task_id: Optional[str] = None, current_state: Optional[str] = None, original_error: Optional[Exception] = None):
        context = {"current_state": current_state} if current_state else {}
        super().__init__(message, "TASK_STATE_ERROR", task_id, original_error)
        if current_state:
            self.context.update(context)


class TaskExecutionError(TaskError):
    """任务执行异常"""
    
    def __init__(self, message: str, task_id: Optional[str] = None, original_error: Optional[Exception] = None):
        super().__init__(message, "TASK_EXECUTION_ERROR", task_id, original_error)


class DuplicateTaskError(TaskError):
    """重复任务异常"""
    
    def __init__(self, message: str, task_name: Optional[str] = None, original_error: Optional[Exception] = None):
        context = {"task_name": task_name} if task_name else {}
        super().__init__(message, "DUPLICATE_TASK", None, original_error)
        self.context.update(context)


# ==================== 权限异常 ====================

class PermissionError(BaseApplicationError):
    """权限异常"""
    
    def __init__(self, message: str, user_id: Optional[str] = None, resource: Optional[str] = None, original_error: Optional[Exception] = None):
        context = {}
        if user_id:
            context["user_id"] = user_id
        if resource:
            context["resource"] = resource
        super().__init__(message, "PERMISSION_ERROR", original_error, context)


class TaskPermissionError(PermissionError):
    """任务权限异常"""
    
    def __init__(self, message: str, task_id: Optional[str] = None, user_id: Optional[str] = None, original_error: Optional[Exception] = None):
        context = {"task_id": task_id} if task_id else {}
        super().__init__(message, user_id, f"task:{task_id}", original_error)
        self.context.update(context)


# ==================== 数据访问异常 ====================

class RepositoryError(BaseApplicationError):
    """数据访问异常基类"""
    
    def __init__(self, message: str, error_code: str = "REPOSITORY_ERROR", original_error: Optional[Exception] = None):
        super().__init__(message, error_code, original_error)


class DatabaseConnectionError(RepositoryError):
    """数据库连接异常"""
    
    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(message, "DATABASE_CONNECTION_ERROR", original_error)


class QueryExecutionError(RepositoryError):
    """查询执行异常"""
    
    def __init__(self, message: str, query: Optional[str] = None, original_error: Optional[Exception] = None):
        context = {"query": query} if query else {}
        super().__init__(message, "QUERY_EXECUTION_ERROR", original_error, context)


# ==================== 服务异常 ====================

class ServiceError(BaseApplicationError):
    """服务异常基类"""
    
    def __init__(self, message: str, error_code: str, service_name: Optional[str] = None, original_error: Optional[Exception] = None):
        context = {"service_name": service_name} if service_name else {}
        super().__init__(message, error_code, original_error, context)
        self.service_name = service_name


class ServiceStartupError(ServiceError):
    """服务启动异常"""
    
    def __init__(self, message: str, service_name: Optional[str] = None, original_error: Optional[Exception] = None):
        super().__init__(message, "SERVICE_STARTUP_ERROR", service_name, original_error)


class ServiceShutdownError(ServiceError):
    """服务关闭异常"""
    
    def __init__(self, message: str, service_name: Optional[str] = None, original_error: Optional[Exception] = None):
        super().__init__(message, "SERVICE_SHUTDOWN_ERROR", service_name, original_error)


class ServiceOperationError(ServiceError):
    """服务操作异常"""
    
    def __init__(self, message: str, service_name: Optional[str] = None, operation: Optional[str] = None, original_error: Optional[Exception] = None):
        context = {"operation": operation} if operation else {}
        super().__init__(message, "SERVICE_OPERATION_ERROR", service_name, original_error, context)


class ServiceTimeoutError(ServiceError):
    """服务超时异常"""
    
    def __init__(self, message: str, service_name: Optional[str] = None, timeout: Optional[float] = None, original_error: Optional[Exception] = None):
        context = {"timeout": timeout} if timeout else {}
        super().__init__(message, "SERVICE_TIMEOUT_ERROR", service_name, original_error, context)


# ==================== 事件异常 ====================

class EventError(BaseApplicationError):
    """事件异常基类"""
    
    def __init__(self, message: str, error_code: str, event_type: Optional[str] = None, original_error: Optional[Exception] = None):
        context = {"event_type": event_type} if event_type else {}
        super().__init__(message, error_code, original_error, context)


class EventPublishError(EventError):
    """事件发布异常"""
    
    def __init__(self, message: str, event_type: Optional[str] = None, original_error: Optional[Exception] = None):
        super().__init__(message, "EVENT_PUBLISH_ERROR", event_type, original_error)


class EventHandlerError(EventError):
    """事件处理异常"""
    
    def __init__(self, message: str, event_type: Optional[str] = None, handler: Optional[str] = None, original_error: Optional[Exception] = None):
        context = {"handler": handler} if handler else {}
        super().__init__(message, "EVENT_HANDLER_ERROR", event_type, original_error, context)


# ==================== 自动化异常 ====================

class AutomationError(BaseApplicationError):
    """自动化异常基类"""
    
    def __init__(self, message: str, error_code: str, automation_id: Optional[str] = None, original_error: Optional[Exception] = None):
        context = {"automation_id": automation_id} if automation_id else {}
        super().__init__(message, error_code, original_error, context)
        self.automation_id = automation_id


class GameDetectionError(AutomationError):
    """游戏检测异常"""
    
    def __init__(self, message: str, automation_id: Optional[str] = None, original_error: Optional[Exception] = None):
        super().__init__(message, "GAME_DETECTION_ERROR", automation_id, original_error)


class AutomationExecutionError(AutomationError):
    """自动化执行异常"""
    
    def __init__(self, message: str, automation_id: Optional[str] = None, action: Optional[str] = None, original_error: Optional[Exception] = None):
        context = {"action": action} if action else {}
        super().__init__(message, "AUTOMATION_EXECUTION_ERROR", automation_id, original_error, context)


# ==================== 同步适配器异常 ====================

class SyncAdapterError(BaseApplicationError):
    """同步适配器异常基类"""
    
    def __init__(self, message: str, error_code: str = "SYNC_ADAPTER_ERROR", original_error: Optional[Exception] = None):
        super().__init__(message, error_code, original_error)


class AsyncTaskError(SyncAdapterError):
    """异步任务异常"""
    
    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(message, "ASYNC_TASK_ERROR", original_error)


class CallbackError(SyncAdapterError):
    """回调异常"""
    
    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(message, "CALLBACK_ERROR", original_error)


# ==================== 导出所有异常类 ====================

__all__ = [
    # 基础异常
    "BaseApplicationError",
    "ValidationError",
    
    # 任务异常
    "TaskError",
    "TaskNotFoundError",
    "TaskValidationError",
    "TaskStateError",
    "TaskExecutionError",
    "DuplicateTaskError",
    
    # 权限异常
    "PermissionError",
    "TaskPermissionError",
    
    # 数据访问异常
    "RepositoryError",
    "DatabaseConnectionError",
    "QueryExecutionError",
    
    # 服务异常
    "ServiceError",
    "ServiceStartupError",
    "ServiceShutdownError",
    "ServiceOperationError",
    "ServiceTimeoutError",
    
    # 事件异常
    "EventError",
    "EventPublishError",
    "EventHandlerError",
    
    # 自动化异常
    "AutomationError",
    "GameDetectionError",
    "AutomationExecutionError",
    
    # 同步适配器异常
    "SyncAdapterError",
    "AsyncTaskError",
    "CallbackError",
]