"""日志查看器数据模型模块.

定义日志查看器界面的数据模型。
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from PyQt5.QtCore import QObject, pyqtSignal
import json
import os
import logging
from pathlib import Path
import threading
from queue import Queue, Empty
import time


@dataclass
class LogEntry:
    """日志条目数据类."""
    timestamp: datetime
    level: str
    source: str
    message: str
    details: Optional[Dict[str, Any]] = None
    stack_trace: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    thread_id: Optional[str] = None
    process_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典."""
        return {
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'level': self.level,
            'source': self.source,
            'message': self.message,
            'details': self.details,
            'stack_trace': self.stack_trace,
            'context': self.context,
            'thread_id': self.thread_id,
            'process_id': self.process_id
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LogEntry':
        """从字典创建."""
        timestamp = data.get('timestamp')
        if isinstance(timestamp, str):
            try:
                timestamp = datetime.fromisoformat(timestamp)
            except:
                timestamp = datetime.now()
        elif not isinstance(timestamp, datetime):
            timestamp = datetime.now()
            
        return cls(
            timestamp=timestamp,
            level=data.get('level', 'INFO'),
            source=data.get('source', 'Unknown'),
            message=data.get('message', ''),
            details=data.get('details'),
            stack_trace=data.get('stack_trace'),
            context=data.get('context'),
            thread_id=data.get('thread_id'),
            process_id=data.get('process_id')
        )


@dataclass
class LogFilter:
    """日志过滤器数据类."""
    level: str = '全部'
    source: str = '全部'
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    keyword: str = ''
    case_sensitive: bool = False
    regex: bool = False
    auto_refresh: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典."""
        return {
            'level': self.level,
            'source': self.source,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'keyword': self.keyword,
            'case_sensitive': self.case_sensitive,
            'regex': self.regex,
            'auto_refresh': self.auto_refresh
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LogFilter':
        """从字典创建."""
        start_time = data.get('start_time')
        if isinstance(start_time, str):
            try:
                start_time = datetime.fromisoformat(start_time)
            except:
                start_time = None
                
        end_time = data.get('end_time')
        if isinstance(end_time, str):
            try:
                end_time = datetime.fromisoformat(end_time)
            except:
                end_time = None
                
        return cls(
            level=data.get('level', '全部'),
            source=data.get('source', '全部'),
            start_time=start_time,
            end_time=end_time,
            keyword=data.get('keyword', ''),
            case_sensitive=data.get('case_sensitive', False),
            regex=data.get('regex', False),
            auto_refresh=data.get('auto_refresh', False)
        )


@dataclass
class LogStatistics:
    """日志统计数据类."""
    total_count: int = 0
    debug_count: int = 0
    info_count: int = 0
    warning_count: int = 0
    error_count: int = 0
    critical_count: int = 0
    source_counts: Dict[str, int] = field(default_factory=dict)
    time_range: Optional[tuple] = None
    
    def update_from_logs(self, logs: List[LogEntry]):
        """从日志列表更新统计."""
        self.total_count = len(logs)
        self.debug_count = 0
        self.info_count = 0
        self.warning_count = 0
        self.error_count = 0
        self.critical_count = 0
        self.source_counts.clear()
        
        if not logs:
            self.time_range = None
            return
            
        timestamps = [log.timestamp for log in logs if log.timestamp]
        if timestamps:
            self.time_range = (min(timestamps), max(timestamps))
            
        for log in logs:
            # 统计级别
            level = log.level.upper()
            if level == 'DEBUG':
                self.debug_count += 1
            elif level == 'INFO':
                self.info_count += 1
            elif level == 'WARNING':
                self.warning_count += 1
            elif level == 'ERROR':
                self.error_count += 1
            elif level == 'CRITICAL':
                self.critical_count += 1
                
            # 统计来源
            source = log.source
            self.source_counts[source] = self.source_counts.get(source, 0) + 1
            
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典."""
        return {
            'total_count': self.total_count,
            'debug_count': self.debug_count,
            'info_count': self.info_count,
            'warning_count': self.warning_count,
            'error_count': self.error_count,
            'critical_count': self.critical_count,
            'source_counts': self.source_counts,
            'time_range': [
                self.time_range[0].isoformat(),
                self.time_range[1].isoformat()
            ] if self.time_range else None
        }


class LogStorage:
    """日志存储管理器."""
    
    def __init__(self, storage_dir: str = "logs"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        self.max_files = 10
        
    def save_logs(self, logs: List[LogEntry], filename: Optional[str] = None) -> str:
        """保存日志到文件."""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"logs_{timestamp}.json"
            
        filepath = self.storage_dir / filename
        
        log_data = [log.to_dict() for log in logs]
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, ensure_ascii=False, indent=2)
            
        return str(filepath)
        
    def load_logs(self, filename: str) -> List[LogEntry]:
        """从文件加载日志."""
        filepath = self.storage_dir / filename
        
        if not filepath.exists():
            return []
            
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                log_data = json.load(f)
                
            return [LogEntry.from_dict(data) for data in log_data]
        except Exception as e:
            logging.error(f"加载日志文件失败: {e}")
            return []
            
    def get_log_files(self) -> List[str]:
        """获取日志文件列表."""
        files = []
        for file in self.storage_dir.glob("*.json"):
            files.append(file.name)
        return sorted(files, reverse=True)
        
    def cleanup_old_files(self):
        """清理旧的日志文件."""
        files = [(f, f.stat().st_mtime) for f in self.storage_dir.glob("*.json")]
        files.sort(key=lambda x: x[1], reverse=True)
        
        # 删除超过最大数量的文件
        for file, _ in files[self.max_files:]:
            try:
                file.unlink()
            except Exception as e:
                logging.error(f"删除日志文件失败: {e}")
                
    def export_logs(self, logs: List[LogEntry], format_type: str = 'json') -> str:
        """导出日志."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if format_type == 'json':
            filename = f"export_{timestamp}.json"
            return self.save_logs(logs, filename)
        elif format_type == 'txt':
            filename = f"export_{timestamp}.txt"
            filepath = self.storage_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                for log in logs:
                    timestamp_str = log.timestamp.strftime('%Y-%m-%d %H:%M:%S') if log.timestamp else ''
                    f.write(f"[{timestamp_str}] [{log.level}] [{log.source}] {log.message}\n")
                    
            return str(filepath)
        elif format_type == 'csv':
            import csv
            filename = f"export_{timestamp}.csv"
            filepath = self.storage_dir / filename
            
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['时间', '级别', '来源', '消息', '详情'])
                
                for log in logs:
                    timestamp_str = log.timestamp.strftime('%Y-%m-%d %H:%M:%S') if log.timestamp else ''
                    details_str = json.dumps(log.details, ensure_ascii=False) if log.details else ''
                    writer.writerow([timestamp_str, log.level, log.source, log.message, details_str])
                    
            return str(filepath)
        else:
            raise ValueError(f"不支持的导出格式: {format_type}")


class LogCollector:
    """日志收集器."""
    
    def __init__(self):
        self.handlers: List[Callable[[LogEntry], None]] = []
        self.log_queue = Queue()
        self.running = False
        self.worker_thread = None
        
    def add_handler(self, handler: Callable[[LogEntry], None]):
        """添加日志处理器."""
        self.handlers.append(handler)
        
    def remove_handler(self, handler: Callable[[LogEntry], None]):
        """移除日志处理器."""
        if handler in self.handlers:
            self.handlers.remove(handler)
            
    def start(self):
        """启动收集器."""
        if self.running:
            return
            
        self.running = True
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
        
    def stop(self):
        """停止收集器."""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=1.0)
            
    def collect_log(self, log_entry: LogEntry):
        """收集日志."""
        if self.running:
            try:
                self.log_queue.put_nowait(log_entry)
            except:
                pass  # 队列满时忽略
                
    def _worker_loop(self):
        """工作线程循环."""
        while self.running:
            try:
                log_entry = self.log_queue.get(timeout=0.1)
                for handler in self.handlers:
                    try:
                        handler(log_entry)
                    except Exception as e:
                        # 避免处理器错误影响其他处理器
                        pass
            except Empty:
                continue
            except Exception:
                break


class LogViewerModel(QObject):
    """日志查看器数据模型."""
    
    # 信号定义
    logs_changed = pyqtSignal(list)  # 日志列表变化
    log_added = pyqtSignal(dict)  # 新增日志
    filter_applied = pyqtSignal(list)  # 过滤应用
    statistics_updated = pyqtSignal(dict)  # 统计更新
    export_completed = pyqtSignal(str)  # 导出完成
    error_occurred = pyqtSignal(str)  # 错误发生
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logs: List[LogEntry] = []
        self.filtered_logs: List[LogEntry] = []
        self.current_filter = LogFilter()
        self.statistics = LogStatistics()
        self.storage = LogStorage()
        self.collector = LogCollector()
        
        # 设置日志收集器
        self.collector.add_handler(self._handle_collected_log)
        self.collector.start()
        
        # 最大日志数量
        self.max_logs = 10000
        
    def add_log(self, log_data: Dict[str, Any]):
        """添加日志."""
        try:
            log_entry = LogEntry.from_dict(log_data)
            self.logs.append(log_entry)
            
            # 限制日志数量
            if len(self.logs) > self.max_logs:
                self.logs = self.logs[-self.max_logs:]
                
            # 应用当前过滤器
            self.apply_filter(self.current_filter)
            
            # 更新统计
            self.update_statistics()
            
            # 发送信号
            self.log_added.emit(log_data)
            
        except Exception as e:
            self.error_occurred.emit(f"添加日志失败: {str(e)}")
            
    def add_logs(self, logs_data: List[Dict[str, Any]]):
        """批量添加日志."""
        try:
            new_logs = [LogEntry.from_dict(data) for data in logs_data]
            self.logs.extend(new_logs)
            
            # 限制日志数量
            if len(self.logs) > self.max_logs:
                self.logs = self.logs[-self.max_logs:]
                
            # 应用当前过滤器
            self.apply_filter(self.current_filter)
            
            # 更新统计
            self.update_statistics()
            
            # 发送信号
            self.logs_changed.emit([log.to_dict() for log in self.filtered_logs])
            
        except Exception as e:
            self.error_occurred.emit(f"批量添加日志失败: {str(e)}")
            
    def set_logs(self, logs_data: List[Dict[str, Any]]):
        """设置日志列表."""
        try:
            self.logs = [LogEntry.from_dict(data) for data in logs_data]
            
            # 应用当前过滤器
            self.apply_filter(self.current_filter)
            
            # 更新统计
            self.update_statistics()
            
            # 发送信号
            self.logs_changed.emit([log.to_dict() for log in self.filtered_logs])
            
        except Exception as e:
            self.error_occurred.emit(f"设置日志列表失败: {str(e)}")
            
    def apply_filter(self, filter_data: Dict[str, Any]):
        """应用过滤器."""
        try:
            self.current_filter = LogFilter.from_dict(filter_data)
            self.filtered_logs = []
            
            for log in self.logs:
                if self._match_filter(log, self.current_filter):
                    self.filtered_logs.append(log)
                    
            # 发送信号
            self.filter_applied.emit([log.to_dict() for log in self.filtered_logs])
            
        except Exception as e:
            self.error_occurred.emit(f"应用过滤器失败: {str(e)}")
            
    def _match_filter(self, log: LogEntry, filter_obj: LogFilter) -> bool:
        """检查日志是否匹配过滤条件."""
        # 级别过滤
        if filter_obj.level != '全部' and log.level != filter_obj.level:
            return False
            
        # 来源过滤
        if filter_obj.source != '全部' and log.source != filter_obj.source:
            return False
            
        # 时间过滤
        if filter_obj.start_time and log.timestamp < filter_obj.start_time:
            return False
        if filter_obj.end_time and log.timestamp > filter_obj.end_time:
            return False
            
        # 关键词过滤
        if filter_obj.keyword.strip():
            message = log.message
            keyword = filter_obj.keyword
            
            if not filter_obj.case_sensitive:
                message = message.lower()
                keyword = keyword.lower()
                
            if filter_obj.regex:
                import re
                try:
                    if not re.search(keyword, message):
                        return False
                except re.error:
                    return False
            else:
                if keyword not in message:
                    return False
                    
        return True
        
    def clear_logs(self):
        """清空日志."""
        self.logs.clear()
        self.filtered_logs.clear()
        self.update_statistics()
        self.logs_changed.emit([])
        
    def get_logs(self) -> List[Dict[str, Any]]:
        """获取当前显示的日志."""
        return [log.to_dict() for log in self.filtered_logs]
        
    def get_all_logs(self) -> List[Dict[str, Any]]:
        """获取所有日志."""
        return [log.to_dict() for log in self.logs]
        
    def update_statistics(self):
        """更新统计信息."""
        self.statistics.update_from_logs(self.logs)
        self.statistics_updated.emit(self.statistics.to_dict())
        
    def export_logs(self, format_type: str = 'json', filtered_only: bool = True):
        """导出日志."""
        try:
            logs_to_export = self.filtered_logs if filtered_only else self.logs
            filepath = self.storage.export_logs(logs_to_export, format_type)
            self.export_completed.emit(filepath)
        except Exception as e:
            self.error_occurred.emit(f"导出日志失败: {str(e)}")
            
    def save_logs(self, filename: Optional[str] = None):
        """保存日志到文件."""
        try:
            filepath = self.storage.save_logs(self.logs, filename)
            self.export_completed.emit(filepath)
        except Exception as e:
            self.error_occurred.emit(f"保存日志失败: {str(e)}")
            
    def load_logs(self, filename: str):
        """从文件加载日志."""
        try:
            loaded_logs = self.storage.load_logs(filename)
            self.logs = loaded_logs
            self.apply_filter(self.current_filter.to_dict())
            self.update_statistics()
        except Exception as e:
            self.error_occurred.emit(f"加载日志失败: {str(e)}")
            
    def get_log_files(self) -> List[str]:
        """获取日志文件列表."""
        return self.storage.get_log_files()
        
    def _handle_collected_log(self, log_entry: LogEntry):
        """处理收集到的日志."""
        self.add_log(log_entry.to_dict())
        
    def collect_log(self, log_data: Dict[str, Any]):
        """收集日志（外部接口）."""
        log_entry = LogEntry.from_dict(log_data)
        self.collector.collect_log(log_entry)
        
    def set_max_logs(self, max_logs: int):
        """设置最大日志数量."""
        self.max_logs = max_logs
        if len(self.logs) > max_logs:
            self.logs = self.logs[-max_logs:]
            self.apply_filter(self.current_filter.to_dict())
            
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息."""
        return self.statistics.to_dict()
        
    def cleanup(self):
        """清理资源."""
        self.collector.stop()
        self.storage.cleanup_old_files()
