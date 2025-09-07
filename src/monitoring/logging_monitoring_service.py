"""日志监控服务模块.

提供日志的监控和分析服务，包括日志收集、分析、告警等功能。
"""

import os
import re
import time
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable, Pattern
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
from collections import defaultdict, deque
import logging
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler

from ..config.logger import get_logger
from .alert_manager import AlertManager, AlertLevel, Alert
from .metrics_collector import MetricsCollector


class LogLevel(Enum):
    """日志级别枚举。"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogEventType(Enum):
    """日志事件类型。"""
    ERROR_SPIKE = "error_spike"  # 错误激增
    PERFORMANCE_ISSUE = "performance_issue"  # 性能问题
    SECURITY_ALERT = "security_alert"  # 安全告警
    SYSTEM_ANOMALY = "system_anomaly"  # 系统异常
    CUSTOM_PATTERN = "custom_pattern"  # 自定义模式


@dataclass
class LogEntry:
    """日志条目。"""
    timestamp: datetime
    level: LogLevel
    logger_name: str
    message: str
    module: Optional[str] = None
    function: Optional[str] = None
    line_number: Optional[int] = None
    thread_id: Optional[int] = None
    process_id: Optional[int] = None
    extra_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LogPattern:
    """日志模式。"""
    name: str
    pattern: Pattern[str]
    event_type: LogEventType
    alert_level: AlertLevel
    description: str
    threshold: int = 1  # 触发阈值
    time_window: int = 60  # 时间窗口（秒）
    enabled: bool = True


@dataclass
class LogStatistics:
    """日志统计信息。"""
    total_count: int = 0
    debug_count: int = 0
    info_count: int = 0
    warning_count: int = 0
    error_count: int = 0
    critical_count: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error_rate: float = 0.0
    warning_rate: float = 0.0
    top_errors: List[Dict[str, Any]] = field(default_factory=list)
    top_loggers: List[Dict[str, Any]] = field(default_factory=list)


class LogMonitoringHandler(logging.Handler):
    """日志监控处理器。"""
    
    def __init__(self, monitoring_service: 'LoggingMonitoringService'):
        """初始化处理器。
        
        Args:
            monitoring_service: 日志监控服务实例
        """
        super().__init__()
        self.monitoring_service = monitoring_service
    
    def emit(self, record: logging.LogRecord) -> None:
        """处理日志记录。
        
        Args:
            record: 日志记录
        """
        try:
            # 转换为LogEntry
            log_entry = LogEntry(
                timestamp=datetime.fromtimestamp(record.created),
                level=LogLevel(record.levelname),
                logger_name=record.name,
                message=record.getMessage(),
                module=record.module if hasattr(record, 'module') else None,
                function=record.funcName if hasattr(record, 'funcName') else None,
                line_number=record.lineno if hasattr(record, 'lineno') else None,
                thread_id=record.thread if hasattr(record, 'thread') else None,
                process_id=record.process if hasattr(record, 'process') else None
            )
            
            # 添加到监控服务
            self.monitoring_service.add_log_entry(log_entry)
            
        except Exception:
            # 避免日志处理器本身出错影响应用
            pass


class LoggingMonitoringService:
    """日志监控服务。"""
    
    def __init__(self, 
                 alert_manager: Optional[AlertManager] = None,
                 metrics_collector: Optional[MetricsCollector] = None,
                 max_entries: int = 10000,
                 cleanup_interval: int = 300):
        """初始化日志监控服务。
        
        Args:
            alert_manager: 告警管理器
            metrics_collector: 指标收集器
            max_entries: 最大日志条目数
            cleanup_interval: 清理间隔（秒）
        """
        self.logger = get_logger(__name__)
        self.alert_manager = alert_manager or AlertManager()
        self.metrics_collector = metrics_collector or MetricsCollector()
        self.max_entries = max_entries
        self.cleanup_interval = cleanup_interval
        
        # 日志存储
        self._log_entries: deque[LogEntry] = deque(maxlen=max_entries)
        self._log_patterns: List[LogPattern] = []
        self._pattern_matches: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        
        # 统计信息
        self._statistics = LogStatistics()
        self._level_counts = defaultdict(int)
        self._logger_counts = defaultdict(int)
        self._error_counts = defaultdict(int)
        
        # 线程控制
        self._running = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._cleanup_thread: Optional[threading.Thread] = None
        self._lock = threading.RLock()
        
        # 初始化默认模式
        self._init_default_patterns()
        
        # 创建监控处理器
        self._handler = LogMonitoringHandler(self)
    
    def _init_default_patterns(self) -> None:
        """初始化默认日志模式。"""
        default_patterns = [
            LogPattern(
                name="错误激增",
                pattern=re.compile(r"ERROR|CRITICAL", re.IGNORECASE),
                event_type=LogEventType.ERROR_SPIKE,
                alert_level=AlertLevel.HIGH,
                description="检测到错误日志激增",
                threshold=10,
                time_window=60
            ),
            LogPattern(
                name="性能问题",
                pattern=re.compile(r"timeout|slow|performance|latency", re.IGNORECASE),
                event_type=LogEventType.PERFORMANCE_ISSUE,
                alert_level=AlertLevel.MEDIUM,
                description="检测到性能相关问题",
                threshold=5,
                time_window=120
            ),
            LogPattern(
                name="安全告警",
                pattern=re.compile(r"security|unauthorized|forbidden|attack", re.IGNORECASE),
                event_type=LogEventType.SECURITY_ALERT,
                alert_level=AlertLevel.CRITICAL,
                description="检测到安全相关告警",
                threshold=1,
                time_window=60
            ),
            LogPattern(
                name="系统异常",
                pattern=re.compile(r"exception|traceback|stack trace", re.IGNORECASE),
                event_type=LogEventType.SYSTEM_ANOMALY,
                alert_level=AlertLevel.HIGH,
                description="检测到系统异常",
                threshold=3,
                time_window=60
            )
        ]
        
        self._log_patterns.extend(default_patterns)
    
    def start(self) -> None:
        """启动监控服务。"""
        if self._running:
            return
        
        self._running = True
        
        # 启动监控线程
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            name="LogMonitoringThread",
            daemon=True
        )
        self._monitor_thread.start()
        
        # 启动清理线程
        self._cleanup_thread = threading.Thread(
            target=self._cleanup_loop,
            name="LogCleanupThread",
            daemon=True
        )
        self._cleanup_thread.start()
        
        # 注册到根日志记录器
        root_logger = logging.getLogger()
        root_logger.addHandler(self._handler)
        
        self.logger.info("日志监控服务已启动")
    
    def stop(self) -> None:
        """停止监控服务。"""
        if not self._running:
            return
        
        self._running = False
        
        # 从根日志记录器移除处理器
        root_logger = logging.getLogger()
        root_logger.removeHandler(self._handler)
        
        # 等待线程结束
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=5)
        
        if self._cleanup_thread and self._cleanup_thread.is_alive():
            self._cleanup_thread.join(timeout=5)
        
        self.logger.info("日志监控服务已停止")
    
    def add_log_entry(self, entry: LogEntry) -> None:
        """添加日志条目。
        
        Args:
            entry: 日志条目
        """
        with self._lock:
            # 添加到存储
            self._log_entries.append(entry)
            
            # 更新统计
            self._update_statistics(entry)
            
            # 检查模式匹配
            self._check_patterns(entry)
            
            # 更新指标
            self._update_metrics(entry)
    
    def _update_statistics(self, entry: LogEntry) -> None:
        """更新统计信息。
        
        Args:
            entry: 日志条目
        """
        # 更新总计数
        self._statistics.total_count += 1
        
        # 更新级别计数
        level_attr = f"{entry.level.value.lower()}_count"
        if hasattr(self._statistics, level_attr):
            setattr(self._statistics, level_attr, getattr(self._statistics, level_attr) + 1)
        
        self._level_counts[entry.level.value] += 1
        self._logger_counts[entry.logger_name] += 1
        
        # 记录错误信息
        if entry.level in [LogLevel.ERROR, LogLevel.CRITICAL]:
            self._error_counts[entry.message] += 1
        
        # 更新时间范围
        if self._statistics.start_time is None:
            self._statistics.start_time = entry.timestamp
        self._statistics.end_time = entry.timestamp
        
        # 计算错误率
        if self._statistics.total_count > 0:
            error_total = self._statistics.error_count + self._statistics.critical_count
            self._statistics.error_rate = error_total / self._statistics.total_count
            self._statistics.warning_rate = self._statistics.warning_count / self._statistics.total_count
    
    def _check_patterns(self, entry: LogEntry) -> None:
        """检查日志模式匹配。
        
        Args:
            entry: 日志条目
        """
        for pattern in self._log_patterns:
            if not pattern.enabled:
                continue
            
            if pattern.pattern.search(entry.message):
                # 记录匹配
                matches = self._pattern_matches[pattern.name]
                matches.append(entry.timestamp)
                
                # 检查是否触发告警
                self._check_pattern_threshold(pattern, matches)
    
    def _check_pattern_threshold(self, pattern: LogPattern, matches: deque) -> None:
        """检查模式阈值。
        
        Args:
            pattern: 日志模式
            matches: 匹配时间列表
        """
        now = datetime.now()
        window_start = now - timedelta(seconds=pattern.time_window)
        
        # 计算时间窗口内的匹配数
        recent_matches = [t for t in matches if t >= window_start]
        
        if len(recent_matches) >= pattern.threshold:
            # 触发告警
            alert = Alert(
                id=f"log_pattern_{pattern.name}_{int(now.timestamp())}",
                title=f"日志模式告警: {pattern.name}",
                message=f"{pattern.description}，在{pattern.time_window}秒内检测到{len(recent_matches)}次匹配",
                level=pattern.alert_level,
                source="LoggingMonitoringService",
                timestamp=now,
                data={
                    "pattern_name": pattern.name,
                    "match_count": len(recent_matches),
                    "time_window": pattern.time_window,
                    "threshold": pattern.threshold,
                    "event_type": pattern.event_type.value
                }
            )
            
            self.alert_manager.add_alert(alert)
    
    def _update_metrics(self, entry: LogEntry) -> None:
        """更新指标。
        
        Args:
            entry: 日志条目
        """
        # 记录日志级别指标
        self.metrics_collector.increment_counter(
            f"log_entries_total",
            tags={"level": entry.level.value, "logger": entry.logger_name}
        )
        
        # 记录错误指标
        if entry.level in [LogLevel.ERROR, LogLevel.CRITICAL]:
            self.metrics_collector.increment_counter(
                "log_errors_total",
                tags={"level": entry.level.value, "logger": entry.logger_name}
            )
    
    def _monitor_loop(self) -> None:
        """监控循环。"""
        while self._running:
            try:
                # 更新统计信息
                self._update_top_statistics()
                
                # 检查系统健康状态
                self._check_system_health()
                
                time.sleep(10)  # 每10秒检查一次
                
            except Exception as e:
                self.logger.error(f"监控循环出错: {e}")
                time.sleep(5)
    
    def _cleanup_loop(self) -> None:
        """清理循环。"""
        while self._running:
            try:
                # 清理过期的模式匹配记录
                self._cleanup_pattern_matches()
                
                time.sleep(self.cleanup_interval)
                
            except Exception as e:
                self.logger.error(f"清理循环出错: {e}")
                time.sleep(60)
    
    def _update_top_statistics(self) -> None:
        """更新Top统计信息。"""
        with self._lock:
            # 更新Top错误
            top_errors = sorted(
                self._error_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
            
            self._statistics.top_errors = [
                {"message": msg, "count": count}
                for msg, count in top_errors
            ]
            
            # 更新Top日志记录器
            top_loggers = sorted(
                self._logger_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
            
            self._statistics.top_loggers = [
                {"logger": logger, "count": count}
                for logger, count in top_loggers
            ]
    
    def _check_system_health(self) -> None:
        """检查系统健康状态。"""
        # 检查错误率
        if self._statistics.error_rate > 0.1:  # 错误率超过10%
            alert = Alert(
                id=f"high_error_rate_{int(time.time())}",
                title="高错误率告警",
                message=f"当前错误率为 {self._statistics.error_rate:.2%}，超过阈值",
                level=AlertLevel.HIGH,
                source="LoggingMonitoringService",
                timestamp=datetime.now(),
                data={"error_rate": self._statistics.error_rate}
            )
            
            self.alert_manager.add_alert(alert)
    
    def _cleanup_pattern_matches(self) -> None:
        """清理过期的模式匹配记录。"""
        now = datetime.now()
        
        for pattern_name, matches in self._pattern_matches.items():
            # 找到对应的模式
            pattern = next((p for p in self._log_patterns if p.name == pattern_name), None)
            if not pattern:
                continue
            
            # 清理过期记录
            cutoff_time = now - timedelta(seconds=pattern.time_window * 2)
            while matches and matches[0] < cutoff_time:
                matches.popleft()
    
    def add_pattern(self, pattern: LogPattern) -> None:
        """添加日志模式。
        
        Args:
            pattern: 日志模式
        """
        with self._lock:
            self._log_patterns.append(pattern)
            self.logger.info(f"已添加日志模式: {pattern.name}")
    
    def remove_pattern(self, pattern_name: str) -> bool:
        """移除日志模式。
        
        Args:
            pattern_name: 模式名称
            
        Returns:
            是否移除成功
        """
        with self._lock:
            for i, pattern in enumerate(self._log_patterns):
                if pattern.name == pattern_name:
                    del self._log_patterns[i]
                    # 清理相关匹配记录
                    if pattern_name in self._pattern_matches:
                        del self._pattern_matches[pattern_name]
                    self.logger.info(f"已移除日志模式: {pattern_name}")
                    return True
            return False
    
    def get_patterns(self) -> List[LogPattern]:
        """获取所有日志模式。
        
        Returns:
            日志模式列表
        """
        with self._lock:
            return self._log_patterns.copy()
    
    def get_statistics(self) -> LogStatistics:
        """获取统计信息。
        
        Returns:
            统计信息
        """
        with self._lock:
            return self._statistics
    
    def get_recent_logs(self, 
                       count: int = 100,
                       level_filter: Optional[LogLevel] = None,
                       logger_filter: Optional[str] = None) -> List[LogEntry]:
        """获取最近的日志。
        
        Args:
            count: 返回数量
            level_filter: 级别过滤
            logger_filter: 日志记录器过滤
            
        Returns:
            日志条目列表
        """
        with self._lock:
            logs = list(self._log_entries)
            
            # 应用过滤器
            if level_filter:
                logs = [log for log in logs if log.level == level_filter]
            
            if logger_filter:
                logs = [log for log in logs if logger_filter in log.logger_name]
            
            # 返回最近的日志
            return logs[-count:] if count < len(logs) else logs
    
    def search_logs(self, 
                   query: str,
                   start_time: Optional[datetime] = None,
                   end_time: Optional[datetime] = None,
                   level_filter: Optional[LogLevel] = None) -> List[LogEntry]:
        """搜索日志。
        
        Args:
            query: 搜索查询
            start_time: 开始时间
            end_time: 结束时间
            level_filter: 级别过滤
            
        Returns:
            匹配的日志条目列表
        """
        with self._lock:
            results = []
            pattern = re.compile(query, re.IGNORECASE)
            
            for log in self._log_entries:
                # 时间过滤
                if start_time and log.timestamp < start_time:
                    continue
                if end_time and log.timestamp > end_time:
                    continue
                
                # 级别过滤
                if level_filter and log.level != level_filter:
                    continue
                
                # 内容匹配
                if pattern.search(log.message) or pattern.search(log.logger_name):
                    results.append(log)
            
            return results
    
    def export_logs(self, 
                   file_path: str,
                   start_time: Optional[datetime] = None,
                   end_time: Optional[datetime] = None,
                   format: str = "json") -> bool:
        """导出日志。
        
        Args:
            file_path: 文件路径
            start_time: 开始时间
            end_time: 结束时间
            format: 导出格式（json/csv/txt）
            
        Returns:
            是否导出成功
        """
        try:
            logs = []
            
            with self._lock:
                for log in self._log_entries:
                    if start_time and log.timestamp < start_time:
                        continue
                    if end_time and log.timestamp > end_time:
                        continue
                    logs.append(log)
            
            # 根据格式导出
            if format.lower() == "json":
                import json
                data = [
                    {
                        "timestamp": log.timestamp.isoformat(),
                        "level": log.level.value,
                        "logger": log.logger_name,
                        "message": log.message,
                        "module": log.module,
                        "function": log.function,
                        "line_number": log.line_number
                    }
                    for log in logs
                ]
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            
            elif format.lower() == "csv":
                import csv
                with open(file_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(["Timestamp", "Level", "Logger", "Message", "Module", "Function", "Line"])
                    
                    for log in logs:
                        writer.writerow([
                            log.timestamp.isoformat(),
                            log.level.value,
                            log.logger_name,
                            log.message,
                            log.module or "",
                            log.function or "",
                            log.line_number or ""
                        ])
            
            elif format.lower() == "txt":
                with open(file_path, 'w', encoding='utf-8') as f:
                    for log in logs:
                        f.write(f"[{log.timestamp.isoformat()}] {log.level.value} {log.logger_name}: {log.message}\n")
            
            else:
                raise ValueError(f"不支持的导出格式: {format}")
            
            self.logger.info(f"已导出 {len(logs)} 条日志到: {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"导出日志失败: {e}")
            return False
