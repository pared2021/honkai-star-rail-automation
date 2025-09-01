# -*- coding: utf-8 -*-
"""
错误处理中间件 - 统一错误拦截、处理和恢复
"""

import asyncio
import traceback
from typing import Any, Callable, Dict, List, Optional, Type, Union
from functools import wraps
from datetime import datetime
import logging

from core.events import EventBus
from application.error_handling_service import ErrorHandlingService, ErrorContext, ErrorSeverity
from config.error_recovery_strategies import error_recovery_config, ErrorCategory
from utils.logger import get_logger


class ErrorHandlingMiddleware:
    """错误处理中间件"""
    
    def __init__(self, 
                 error_service: ErrorHandlingService,
                 event_bus: EventBus,
                 logger: Optional[logging.Logger] = None):
        self.error_service = error_service
        self.event_bus = event_bus
        self.logger = logger or get_logger(self.__class__.__name__)
        
        # 错误拦截器
        self.interceptors: List[Callable] = []
        
        # 错误过滤器
        self.filters: Dict[str, Callable] = {}
        
        # 错误转换器
        self.transformers: Dict[Type[Exception], Callable] = {}
        
        # 全局错误处理器
        self.global_handlers: List[Callable] = []
        
        # 错误统计
        self.error_stats = {
            'total_errors': 0,
            'handled_errors': 0,
            'unhandled_errors': 0,
            'by_category': {},
            'by_severity': {},
            'last_reset': datetime.now()
        }
        
        self._setup_default_handlers()
    
    def _setup_default_handlers(self):
        """设置默认错误处理器"""
        
        # 添加默认拦截器
        self.add_interceptor(self._log_error_interceptor)
        self.add_interceptor(self._stats_interceptor)
        
        # 添加默认转换器
        self.add_transformer(ConnectionError, self._network_error_transformer)
        self.add_transformer(TimeoutError, self._timeout_error_transformer)
        self.add_transformer(MemoryError, self._memory_error_transformer)
        self.add_transformer(PermissionError, self._permission_error_transformer)
        self.add_transformer(FileNotFoundError, self._file_error_transformer)
        
        # 添加默认全局处理器
        self.add_global_handler(self._emergency_handler)
    
    def add_interceptor(self, interceptor: Callable):
        """添加错误拦截器"""
        if interceptor not in self.interceptors:
            self.interceptors.append(interceptor)
    
    def remove_interceptor(self, interceptor: Callable):
        """移除错误拦截器"""
        if interceptor in self.interceptors:
            self.interceptors.remove(interceptor)
    
    def add_filter(self, name: str, filter_func: Callable):
        """添加错误过滤器"""
        self.filters[name] = filter_func
    
    def remove_filter(self, name: str):
        """移除错误过滤器"""
        self.filters.pop(name, None)
    
    def add_transformer(self, exception_type: Type[Exception], transformer: Callable):
        """添加错误转换器"""
        self.transformers[exception_type] = transformer
    
    def remove_transformer(self, exception_type: Type[Exception]):
        """移除错误转换器"""
        self.transformers.pop(exception_type, None)
    
    def add_global_handler(self, handler: Callable):
        """添加全局错误处理器"""
        if handler not in self.global_handlers:
            self.global_handlers.append(handler)
    
    def remove_global_handler(self, handler: Callable):
        """移除全局错误处理器"""
        if handler in self.global_handlers:
            self.global_handlers.remove(handler)
    
    def handle_error(self, 
                    error: Exception, 
                    context: Optional[Dict[str, Any]] = None,
                    source: Optional[str] = None) -> bool:
        """处理错误
        
        Args:
            error: 异常对象
            context: 错误上下文
            source: 错误源
            
        Returns:
            bool: 是否成功处理
        """
        try:
            self.error_stats['total_errors'] += 1
            
            # 创建错误上下文
            error_context = self._create_error_context(error, context, source)
            
            # 执行拦截器
            for interceptor in self.interceptors:
                try:
                    interceptor(error, error_context)
                except Exception as e:
                    self.logger.error(f"错误拦截器执行失败: {e}")
            
            # 应用过滤器
            if not self._apply_filters(error, error_context):
                self.logger.debug(f"错误被过滤器过滤: {error}")
                return True
            
            # 转换错误
            transformed_error = self._transform_error(error)
            if transformed_error != error:
                error = transformed_error
                error_context = self._create_error_context(error, context, source)
            
            # 使用错误处理服务处理
            result = self.error_service.handle_error(error, error_context)
            
            if result.handled:
                self.error_stats['handled_errors'] += 1
                
                # 发送错误处理成功事件
                self.event_bus.emit('error_handled', {
                    'error': error,
                    'context': error_context,
                    'result': result,
                    'timestamp': datetime.now()
                })
                
                return True
            else:
                # 尝试全局处理器
                for handler in self.global_handlers:
                    try:
                        if handler(error, error_context):
                            self.error_stats['handled_errors'] += 1
                            return True
                    except Exception as e:
                        self.logger.error(f"全局错误处理器执行失败: {e}")
                
                self.error_stats['unhandled_errors'] += 1
                
                # 发送未处理错误事件
                self.event_bus.emit('error_unhandled', {
                    'error': error,
                    'context': error_context,
                    'timestamp': datetime.now()
                })
                
                return False
        
        except Exception as e:
            self.logger.error(f"错误处理中间件内部错误: {e}")
            self.logger.error(traceback.format_exc())
            return False
    
    def _create_error_context(self, 
                             error: Exception, 
                             context: Optional[Dict[str, Any]], 
                             source: Optional[str]) -> ErrorContext:
        """创建错误上下文"""
        
        # 获取错误策略
        error_type = type(error).__name__
        strategy = error_recovery_config.get_strategy(error_type)
        
        # 确定错误严重程度
        severity = ErrorSeverity.MEDIUM
        if strategy:
            severity = strategy.severity
        elif isinstance(error, (MemoryError, SystemError)):
            severity = ErrorSeverity.CRITICAL
        elif isinstance(error, (ConnectionError, TimeoutError)):
            severity = ErrorSeverity.HIGH
        elif isinstance(error, (ValueError, TypeError)):
            severity = ErrorSeverity.LOW
        
        # 构建上下文数据
        context_data = {
            'error_type': error_type,
            'error_message': str(error),
            'traceback': traceback.format_exc(),
            'source': source or 'unknown',
            'timestamp': datetime.now(),
            'strategy': strategy
        }
        
        if context:
            context_data.update(context)
        
        return ErrorContext(
            error_id=f"{error_type}_{datetime.now().timestamp()}",
            error_type=error_type,
            severity=severity,
            context=context_data,
            timestamp=datetime.now()
        )
    
    def _apply_filters(self, error: Exception, context: ErrorContext) -> bool:
        """应用错误过滤器"""
        for name, filter_func in self.filters.items():
            try:
                if not filter_func(error, context):
                    return False
            except Exception as e:
                self.logger.error(f"错误过滤器 {name} 执行失败: {e}")
        return True
    
    def _transform_error(self, error: Exception) -> Exception:
        """转换错误"""
        error_type = type(error)
        if error_type in self.transformers:
            try:
                return self.transformers[error_type](error)
            except Exception as e:
                self.logger.error(f"错误转换器执行失败: {e}")
        return error
    
    # 默认拦截器
    def _log_error_interceptor(self, error: Exception, context: ErrorContext):
        """日志记录拦截器"""
        severity_map = {
            ErrorSeverity.LOW: logging.WARNING,
            ErrorSeverity.MEDIUM: logging.ERROR,
            ErrorSeverity.HIGH: logging.ERROR,
            ErrorSeverity.CRITICAL: logging.CRITICAL
        }
        
        log_level = severity_map.get(context.severity, logging.ERROR)
        self.logger.log(log_level, f"错误处理: {context.error_type} - {error}")
        
        if context.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            self.logger.error(f"错误详情: {context.context}")
    
    def _stats_interceptor(self, error: Exception, context: ErrorContext):
        """统计拦截器"""
        error_type = context.error_type
        severity = context.severity.value
        
        # 按类型统计
        if 'by_type' not in self.error_stats:
            self.error_stats['by_type'] = {}
        self.error_stats['by_type'][error_type] = self.error_stats['by_type'].get(error_type, 0) + 1
        
        # 按严重程度统计
        self.error_stats['by_severity'][severity] = self.error_stats['by_severity'].get(severity, 0) + 1
        
        # 按分类统计
        strategy = context.context.get('strategy')
        if strategy:
            category = strategy.category.value
            self.error_stats['by_category'][category] = self.error_stats['by_category'].get(category, 0) + 1
    
    # 默认转换器
    def _network_error_transformer(self, error: ConnectionError) -> Exception:
        """网络错误转换器"""
        if "timeout" in str(error).lower():
            return TimeoutError(f"网络超时: {error}")
        return error
    
    def _timeout_error_transformer(self, error: TimeoutError) -> Exception:
        """超时错误转换器"""
        return error
    
    def _memory_error_transformer(self, error: MemoryError) -> Exception:
        """内存错误转换器"""
        return error
    
    def _permission_error_transformer(self, error: PermissionError) -> Exception:
        """权限错误转换器"""
        return error
    
    def _file_error_transformer(self, error: FileNotFoundError) -> Exception:
        """文件错误转换器"""
        return error
    
    # 默认全局处理器
    def _emergency_handler(self, error: Exception, context: ErrorContext) -> bool:
        """紧急处理器 - 最后的处理手段"""
        if context.severity == ErrorSeverity.CRITICAL:
            self.logger.critical(f"紧急处理严重错误: {error}")
            
            # 发送紧急告警
            self.event_bus.emit('emergency_alert', {
                'error': error,
                'context': context,
                'timestamp': datetime.now(),
                'message': '系统遇到严重错误，需要立即处理'
            })
            
            return True
        
        return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取错误统计信息"""
        return self.error_stats.copy()
    
    def reset_statistics(self):
        """重置错误统计"""
        self.error_stats = {
            'total_errors': 0,
            'handled_errors': 0,
            'unhandled_errors': 0,
            'by_category': {},
            'by_severity': {},
            'by_type': {},
            'last_reset': datetime.now()
        }
    
    def get_health_status(self) -> Dict[str, Any]:
        """获取健康状态"""
        total = self.error_stats['total_errors']
        handled = self.error_stats['handled_errors']
        
        success_rate = (handled / total * 100) if total > 0 else 100
        
        status = 'healthy'
        if success_rate < 50:
            status = 'critical'
        elif success_rate < 80:
            status = 'warning'
        elif success_rate < 95:
            status = 'degraded'
        
        return {
            'status': status,
            'success_rate': success_rate,
            'total_errors': total,
            'handled_errors': handled,
            'unhandled_errors': self.error_stats['unhandled_errors'],
            'last_reset': self.error_stats['last_reset']
        }


def error_handler(middleware: ErrorHandlingMiddleware, 
                 source: Optional[str] = None,
                 context: Optional[Dict[str, Any]] = None):
    """错误处理装饰器"""
    
    def decorator(func):
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    handled = middleware.handle_error(e, context, source or func.__name__)
                    if not handled:
                        raise
                    return None
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    handled = middleware.handle_error(e, context, source or func.__name__)
                    if not handled:
                        raise
                    return None
            return sync_wrapper
    
    return decorator


def safe_execute(middleware: ErrorHandlingMiddleware,
                func: Callable,
                *args,
                source: Optional[str] = None,
                context: Optional[Dict[str, Any]] = None,
                **kwargs) -> Any:
    """安全执行函数"""
    try:
        if asyncio.iscoroutinefunction(func):
            return asyncio.create_task(func(*args, **kwargs))
        else:
            return func(*args, **kwargs)
    except Exception as e:
        handled = middleware.handle_error(e, context, source or func.__name__)
        if not handled:
            raise
        return None


class ErrorHandlingContext:
    """错误处理上下文管理器"""
    
    def __init__(self, 
                 middleware: ErrorHandlingMiddleware,
                 source: Optional[str] = None,
                 context: Optional[Dict[str, Any]] = None,
                 reraise: bool = False):
        self.middleware = middleware
        self.source = source
        self.context = context
        self.reraise = reraise
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            handled = self.middleware.handle_error(exc_val, self.context, self.source)
            if handled and not self.reraise:
                return True  # 抑制异常
        return False


# 全局错误处理中间件实例
_global_middleware: Optional[ErrorHandlingMiddleware] = None


def get_global_middleware() -> Optional[ErrorHandlingMiddleware]:
    """获取全局错误处理中间件"""
    return _global_middleware


def set_global_middleware(middleware: ErrorHandlingMiddleware):
    """设置全局错误处理中间件"""
    global _global_middleware
    _global_middleware = middleware


def handle_global_error(error: Exception, 
                       context: Optional[Dict[str, Any]] = None,
                       source: Optional[str] = None) -> bool:
    """使用全局中间件处理错误"""
    if _global_middleware:
        return _global_middleware.handle_error(error, context, source)
    return False