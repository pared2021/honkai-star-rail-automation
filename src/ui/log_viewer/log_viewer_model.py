"""日志查看器Model层

该模块定义了日志查看器的数据模型，负责管理日志数据状态和业务逻辑。
"""

import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
from PyQt6.QtCore import QObject, pyqtSignal, QThread, QTimer
from PyQt6.QtWidgets import QMessageBox

from src.utils.logger import logger
from src.core.interfaces.config_interface import IConfigManager


class LogFileWatcher(QThread):
    """日志文件监控线程"""
    
    new_log_line = pyqtSignal(str)
    
    def __init__(self, log_file_path: str):
        super().__init__()
        self.log_file_path = log_file_path
        self.running = False
        self.last_position = 0
    
    def run(self):
        """运行监控"""
        self.running = True
        
        # 获取初始文件大小
        if os.path.exists(self.log_file_path):
            self.last_position = os.path.getsize(self.log_file_path)
        
        while self.running:
            try:
                if os.path.exists(self.log_file_path):
                    current_size = os.path.getsize(self.log_file_path)
                    
                    if current_size > self.last_position:
                        with open(self.log_file_path, "r", encoding="utf-8") as f:
                            f.seek(self.last_position)
                            new_lines = f.read()
                            
                            for line in new_lines.strip().split("\n"):
                                if line.strip():
                                    self.new_log_line.emit(line)
                        
                        self.last_position = current_size
                
                self.msleep(500)  # 500ms检查一次
                
            except Exception as e:
                logger.error(f"日志文件监控错误: {e}")
                self.msleep(1000)
    
    def stop(self):
        """停止监控"""
        self.running = False
        self.wait()


class LogStatistics:
    """日志统计信息"""
    
    def __init__(self):
        self.reset()
    
    def reset(self):
        """重置统计"""
        self.total_lines = 0
        self.error_count = 0
        self.warning_count = 0
        self.info_count = 0
        self.debug_count = 0
        self.start_time = datetime.now()
        self.last_update = datetime.now()
    
    def update(self, log_line: str):
        """更新统计"""
        self.total_lines += 1
        self.last_update = datetime.now()
        
        line_upper = log_line.upper()
        if "ERROR" in line_upper or "CRITICAL" in line_upper:
            self.error_count += 1
        elif "WARNING" in line_upper or "WARN" in line_upper:
            self.warning_count += 1
        elif "INFO" in line_upper:
            self.info_count += 1
        elif "DEBUG" in line_upper or "TRACE" in line_upper:
            self.debug_count += 1
    
    def get_summary(self) -> Dict[str, Any]:
        """获取统计摘要"""
        duration = self.last_update - self.start_time
        return {
            "total_lines": self.total_lines,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "info_count": self.info_count,
            "debug_count": self.debug_count,
            "duration": str(duration).split(".")[0],  # 去掉微秒
            "start_time": self.start_time.strftime("%H:%M:%S"),
            "last_update": self.last_update.strftime("%H:%M:%S"),
        }


class LogViewerModel(QObject):
    """日志查看器数据模型"""
    
    # 数据变化信号
    log_line_added = pyqtSignal(str)  # 新增日志行
    log_file_changed = pyqtSignal(str)  # 日志文件变化
    statistics_updated = pyqtSignal(dict)  # 统计信息更新
    max_lines_changed = pyqtSignal(int)  # 最大行数变化
    font_size_changed = pyqtSignal(int)  # 字体大小变化
    theme_changed = pyqtSignal(str)  # 主题变化
    auto_scroll_changed = pyqtSignal(bool)  # 自动滚动变化
    realtime_monitoring_changed = pyqtSignal(bool)  # 实时监控变化
    level_filter_changed = pyqtSignal(str)  # 级别过滤变化
    search_filter_changed = pyqtSignal(str)  # 搜索过滤变化
    
    # 状态信号
    log_exported = pyqtSignal(bool, str)  # 日志导出结果
    log_cleared = pyqtSignal(bool, str)  # 日志清空结果
    file_loaded = pyqtSignal(bool, str)  # 文件加载结果
    monitoring_status_changed = pyqtSignal(bool, str)  # 监控状态变化
    
    # 错误信号
    model_error = pyqtSignal(str)  # Model错误
    
    def __init__(self, parent=None, config_manager: IConfigManager = None):
        super().__init__(parent)
        
        # 配置管理器
        if config_manager is None:
            from src.core.dependency_injection import ServiceLocator
            self.config_manager = ServiceLocator.resolve(IConfigManager)
        else:
            self.config_manager = config_manager
        
        # 日志监控
        self.log_watcher: Optional[LogFileWatcher] = None
        self.current_log_file: Optional[str] = None
        
        # 统计信息
        self.statistics = LogStatistics()
        
        # 显示设置
        self._max_lines = 10000
        self._font_size = 9
        self._theme = "默认"
        self._auto_scroll = True
        self._realtime_monitoring = True
        
        # 过滤设置
        self._level_filter = "全部"
        self._search_filter = ""
        
        # 日志内容
        self.log_lines: List[str] = []
        
        # 统计更新定时器
        self.stats_timer = QTimer()
        self.stats_timer.timeout.connect(self._emit_statistics_update)
        self.stats_timer.start(2000)  # 每2秒更新一次统计
        
        logger.info("日志查看器Model初始化完成")
    
    # 属性访问器
    @property
    def max_lines(self) -> int:
        return self._max_lines
    
    @property
    def font_size(self) -> int:
        return self._font_size
    
    @property
    def theme(self) -> str:
        return self._theme
    
    @property
    def auto_scroll(self) -> bool:
        return self._auto_scroll
    
    @property
    def realtime_monitoring(self) -> bool:
        return self._realtime_monitoring
    
    @property
    def level_filter(self) -> str:
        return self._level_filter
    
    @property
    def search_filter(self) -> str:
        return self._search_filter
    
    # 设置方法
    def set_max_lines(self, max_lines: int):
        """设置最大行数"""
        if max_lines != self._max_lines:
            self._max_lines = max_lines
            self.max_lines_changed.emit(max_lines)
            logger.debug(f"最大显示行数已更新为: {max_lines}")
    
    def set_font_size(self, font_size: int):
        """设置字体大小"""
        if font_size != self._font_size:
            self._font_size = font_size
            self.font_size_changed.emit(font_size)
            logger.debug(f"字体大小已更新为: {font_size}")
    
    def set_theme(self, theme: str):
        """设置主题"""
        if theme != self._theme:
            self._theme = theme
            self.theme_changed.emit(theme)
            logger.debug(f"主题已更新为: {theme}")
    
    def set_auto_scroll(self, auto_scroll: bool):
        """设置自动滚动"""
        if auto_scroll != self._auto_scroll:
            self._auto_scroll = auto_scroll
            self.auto_scroll_changed.emit(auto_scroll)
            logger.debug(f"自动滚动已设置为: {auto_scroll}")
    
    def set_realtime_monitoring(self, realtime_monitoring: bool):
        """设置实时监控"""
        if realtime_monitoring != self._realtime_monitoring:
            self._realtime_monitoring = realtime_monitoring
            self.realtime_monitoring_changed.emit(realtime_monitoring)
            
            # 更新监控状态
            if self.log_watcher:
                if realtime_monitoring:
                    if not self.log_watcher.isRunning():
                        self.log_watcher.start()
                    self.monitoring_status_changed.emit(True, "监控中")
                else:
                    if self.log_watcher.isRunning():
                        self.log_watcher.stop()
                    self.monitoring_status_changed.emit(False, "已暂停")
            
            logger.debug(f"实时监控已设置为: {realtime_monitoring}")
    
    def set_level_filter(self, level_filter: str):
        """设置级别过滤"""
        if level_filter != self._level_filter:
            self._level_filter = level_filter
            self.level_filter_changed.emit(level_filter)
            logger.debug(f"级别过滤已设置为: {level_filter}")
    
    def set_search_filter(self, search_filter: str):
        """设置搜索过滤"""
        if search_filter != self._search_filter:
            self._search_filter = search_filter
            self.search_filter_changed.emit(search_filter)
            logger.debug(f"搜索过滤已设置为: {search_filter}")
    
    # 日志文件操作
    def start_monitoring(self, log_file_path: str) -> bool:
        """开始监控日志文件"""
        try:
            # 停止之前的监控
            if self.log_watcher:
                self.log_watcher.stop()
            
            # 创建新的监控线程
            self.log_watcher = LogFileWatcher(log_file_path)
            self.log_watcher.new_log_line.connect(self._on_new_log_line)
            
            if self._realtime_monitoring:
                self.log_watcher.start()
                self.monitoring_status_changed.emit(True, "监控中")
            else:
                self.monitoring_status_changed.emit(False, "已暂停")
            
            self.current_log_file = log_file_path
            self.log_file_changed.emit(log_file_path)
            
            # 加载现有日志内容
            self._load_existing_logs(log_file_path)
            
            logger.info(f"开始监控日志文件: {log_file_path}")
            return True
            
        except Exception as e:
            error_msg = f"启动日志监控失败: {e}"
            logger.error(error_msg)
            self.model_error.emit(error_msg)
            return False
    
    def _load_existing_logs(self, log_file_path: str):
        """加载现有日志内容"""
        try:
            if os.path.exists(log_file_path):
                with open(log_file_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    
                    # 只加载最后的max_lines行
                    if len(lines) > self._max_lines:
                        lines = lines[-self._max_lines:]
                    
                    # 清空现有数据
                    self.log_lines.clear()
                    self.statistics.reset()
                    
                    for line in lines:
                        line = line.strip()
                        if line:
                            self._add_log_line(line, update_stats=True)
                    
                    self.file_loaded.emit(True, f"已加载 {len(self.log_lines)} 行日志")
                    
        except Exception as e:
            error_msg = f"加载日志文件失败: {e}"
            logger.error(error_msg)
            self.file_loaded.emit(False, error_msg)
    
    def _on_new_log_line(self, line: str):
        """处理新日志行"""
        self._add_log_line(line, update_stats=True)
    
    def _add_log_line(self, line: str, update_stats: bool = True):
        """添加日志行"""
        try:
            # 更新统计
            if update_stats:
                self.statistics.update(line)
            
            # 检查行数限制
            if len(self.log_lines) >= self._max_lines:
                # 删除最旧的行
                self.log_lines.pop(0)
            
            # 添加新行
            self.log_lines.append(line)
            self.log_line_added.emit(line)
            
        except Exception as e:
            logger.error(f"添加日志行失败: {e}")
    
    def should_show_line(self, line: str) -> bool:
        """判断是否应该显示该行"""
        # 级别过滤
        if self._level_filter != "全部":
            if self._level_filter.upper() not in line.upper():
                return False
        
        # 搜索过滤
        if self._search_filter.strip():
            if self._search_filter.lower() not in line.lower():
                return False
        
        return True
    
    def get_filtered_logs(self) -> List[str]:
        """获取过滤后的日志"""
        return [line for line in self.log_lines if self.should_show_line(line)]
    
    # 日志操作
    def clear_logs(self) -> bool:
        """清空日志"""
        try:
            self.log_lines.clear()
            self.statistics.reset()
            self.log_cleared.emit(True, "日志已清空")
            logger.info("日志显示已清空")
            return True
            
        except Exception as e:
            error_msg = f"清空日志失败: {e}"
            logger.error(error_msg)
            self.log_cleared.emit(False, error_msg)
            return False
    
    def export_logs(self, file_path: str, content: str) -> bool:
        """导出日志"""
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            
            self.log_exported.emit(True, f"日志已导出到: {file_path}")
            logger.info(f"日志已导出到: {file_path}")
            return True
            
        except Exception as e:
            error_msg = f"导出日志失败: {e}"
            logger.error(error_msg)
            self.log_exported.emit(False, error_msg)
            return False
    
    def add_manual_log(self, message: str, level: str = "INFO"):
        """手动添加日志消息"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_message = f"[{timestamp}] {level.upper()}: {message}"
        self._add_log_line(formatted_message)
    
    def get_log_files(self) -> List[Dict[str, Any]]:
        """获取日志文件列表"""
        try:
            log_files = []
            log_dir = Path("logs")
            
            if log_dir.exists():
                for log_file in log_dir.glob("*.log"):
                    stat = log_file.stat()
                    size_mb = stat.st_size / (1024 * 1024)
                    mod_time = datetime.fromtimestamp(stat.st_mtime)
                    
                    log_files.append({
                        "name": log_file.name,
                        "path": str(log_file),
                        "size": f"{size_mb:.2f} MB",
                        "modified": mod_time.strftime("%Y-%m-%d %H:%M:%S"),
                        "size_bytes": stat.st_size
                    })
            
            return log_files
            
        except Exception as e:
            logger.error(f"获取日志文件列表失败: {e}")
            return []
    
    def auto_detect_log_file(self) -> Optional[str]:
        """自动检测日志文件"""
        try:
            log_dir = Path("logs")
            if log_dir.exists():
                log_files = list(log_dir.glob("*.log"))
                if log_files:
                    # 选择最新的日志文件
                    latest_log = max(log_files, key=lambda f: f.stat().st_mtime)
                    return str(latest_log)
            return None
            
        except Exception as e:
            logger.error(f"自动检测日志文件失败: {e}")
            return None
    
    def _emit_statistics_update(self):
        """发出统计更新信号"""
        stats = self.statistics.get_summary()
        self.statistics_updated.emit(stats)
    
    def get_current_statistics(self) -> Dict[str, Any]:
        """获取当前统计信息"""
        return self.statistics.get_summary()
    
    def cleanup(self):
        """清理资源"""
        try:
            if self.log_watcher:
                self.log_watcher.stop()
            
            if self.stats_timer:
                self.stats_timer.stop()
            
            logger.info("日志查看器Model清理完成")
            
        except Exception as e:
            logger.error(f"清理资源失败: {e}")