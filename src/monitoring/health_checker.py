# -*- coding: utf-8 -*-
"""
系统健康检查器 - 定期检查系统各组件的健康状态
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
import sqlite3
import threading
import time
from typing import Any, Callable, Dict, List, Optional

from PyQt6.QtCore import QObject, QTimer, pyqtSignal
import psutil

from src.core.logger import get_logger

logger = get_logger(__name__)

from src.database.db_manager import DatabaseManager
from src.monitoring.logging_monitoring_service import LoggingMonitoringService
from src.services.event_bus import EventBus


class HealthStatus(Enum):
    """健康状态"""

    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"
    OFFLINE = "offline"


class ComponentType(Enum):
    """组件类型"""

    DATABASE = "database"
    FILESYSTEM = "filesystem"
    MEMORY = "memory"
    CPU = "cpu"
    DISK = "disk"
    NETWORK = "network"
    SERVICE = "service"
    PROCESS = "process"
    APPLICATION = "application"


@dataclass
class HealthCheckResult:
    """健康检查结果"""

    component_name: str
    component_type: ComponentType
    status: HealthStatus
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, float] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    check_duration_ms: float = 0.0
    error: Optional[str] = None


@dataclass
class HealthCheckConfig:
    """健康检查配置"""

    name: str
    component_type: ComponentType
    check_interval_seconds: int = 60
    timeout_seconds: int = 30
    enabled: bool = True
    warning_threshold: Optional[float] = None
    critical_threshold: Optional[float] = None
    retry_count: int = 3
    retry_delay_seconds: int = 5
    tags: Dict[str, str] = field(default_factory=dict)


class BaseHealthCheck:
    """健康检查基类"""

    def __init__(self, config: HealthCheckConfig):
        self.config = config
        self.last_result: Optional[HealthCheckResult] = None
        self.consecutive_failures = 0

    def check(self) -> HealthCheckResult:
        """执行健康检查"""
        start_time = time.time()

        try:
            result = self._perform_check()
            result.check_duration_ms = (time.time() - start_time) * 1000

            # 重置失败计数
            if result.status != HealthStatus.CRITICAL:
                self.consecutive_failures = 0
            else:
                self.consecutive_failures += 1

            self.last_result = result
            return result

        except Exception as e:
            self.consecutive_failures += 1
            duration_ms = (time.time() - start_time) * 1000

            result = HealthCheckResult(
                component_name=self.config.name,
                component_type=self.config.component_type,
                status=HealthStatus.CRITICAL,
                message=f"健康检查失败: {str(e)}",
                check_duration_ms=duration_ms,
                error=str(e),
            )

            self.last_result = result
            return result

    def _perform_check(self) -> HealthCheckResult:
        """执行具体的健康检查逻辑（子类实现）"""
        raise NotImplementedError

    def get_status_from_value(self, value: float, metric_name: str) -> HealthStatus:
        """根据数值和阈值确定状态"""
        if (
            self.config.critical_threshold is not None
            and value >= self.config.critical_threshold
        ):
            return HealthStatus.CRITICAL
        elif (
            self.config.warning_threshold is not None
            and value >= self.config.warning_threshold
        ):
            return HealthStatus.WARNING
        else:
            return HealthStatus.HEALTHY


class DatabaseHealthCheck(BaseHealthCheck):
    """数据库健康检查"""

    def __init__(self, config: HealthCheckConfig, db_manager: DatabaseManager):
        super().__init__(config)
        self.db_manager = db_manager

    def _perform_check(self) -> HealthCheckResult:
        """检查数据库连接和性能"""
        start_time = time.time()

        try:
            # 测试连接
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()

                # 执行简单查询测试
                cursor.execute("SELECT 1")
                result = cursor.fetchone()

                if result[0] != 1:
                    raise Exception("数据库查询结果异常")

                # 检查数据库大小
                cursor.execute("PRAGMA page_count")
                page_count = cursor.fetchone()[0]

                cursor.execute("PRAGMA page_size")
                page_size = cursor.fetchone()[0]

                db_size_mb = (page_count * page_size) / (1024 * 1024)

                # 检查连接数（SQLite不适用，但保留接口）
                connection_count = 1

                query_time_ms = (time.time() - start_time) * 1000

                # 确定状态
                status = HealthStatus.HEALTHY
                message = "数据库运行正常"

                if query_time_ms > 1000:  # 查询时间超过1秒
                    status = HealthStatus.WARNING
                    message = "数据库响应较慢"

                if query_time_ms > 5000:  # 查询时间超过5秒
                    status = HealthStatus.CRITICAL
                    message = "数据库响应严重超时"

                return HealthCheckResult(
                    component_name=self.config.name,
                    component_type=self.config.component_type,
                    status=status,
                    message=message,
                    details={
                        "database_size_mb": db_size_mb,
                        "connection_count": connection_count,
                        "query_time_ms": query_time_ms,
                    },
                    metrics={
                        "db_size_mb": db_size_mb,
                        "query_time_ms": query_time_ms,
                        "connection_count": connection_count,
                    },
                )

        except Exception as e:
            return HealthCheckResult(
                component_name=self.config.name,
                component_type=self.config.component_type,
                status=HealthStatus.CRITICAL,
                message=f"数据库连接失败: {str(e)}",
                error=str(e),
            )


class SystemResourceHealthCheck(BaseHealthCheck):
    """系统资源健康检查"""

    def _perform_check(self) -> HealthCheckResult:
        """检查系统资源使用情况"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)

            # 内存使用情况
            memory = psutil.virtual_memory()
            memory_percent = memory.percent

            # 磁盘使用情况
            disk = psutil.disk_usage("/")
            disk_percent = (disk.used / disk.total) * 100

            # 确定整体状态
            status = HealthStatus.HEALTHY
            messages = []

            if cpu_percent > 90:
                status = HealthStatus.CRITICAL
                messages.append(f"CPU使用率过高: {cpu_percent:.1f}%")
            elif cpu_percent > 80:
                status = max(status, HealthStatus.WARNING)
                messages.append(f"CPU使用率较高: {cpu_percent:.1f}%")

            if memory_percent > 95:
                status = HealthStatus.CRITICAL
                messages.append(f"内存使用率过高: {memory_percent:.1f}%")
            elif memory_percent > 85:
                status = max(status, HealthStatus.WARNING)
                messages.append(f"内存使用率较高: {memory_percent:.1f}%")

            if disk_percent > 95:
                status = HealthStatus.CRITICAL
                messages.append(f"磁盘使用率过高: {disk_percent:.1f}%")
            elif disk_percent > 90:
                status = max(status, HealthStatus.WARNING)
                messages.append(f"磁盘使用率较高: {disk_percent:.1f}%")

            message = "; ".join(messages) if messages else "系统资源使用正常"

            return HealthCheckResult(
                component_name=self.config.name,
                component_type=self.config.component_type,
                status=status,
                message=message,
                details={
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory_percent,
                    "memory_total_gb": memory.total / (1024**3),
                    "memory_available_gb": memory.available / (1024**3),
                    "disk_percent": disk_percent,
                    "disk_total_gb": disk.total / (1024**3),
                    "disk_free_gb": disk.free / (1024**3),
                },
                metrics={
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory_percent,
                    "disk_percent": disk_percent,
                },
            )

        except Exception as e:
            return HealthCheckResult(
                component_name=self.config.name,
                component_type=self.config.component_type,
                status=HealthStatus.CRITICAL,
                message=f"系统资源检查失败: {str(e)}",
                error=str(e),
            )


class FileSystemHealthCheck(BaseHealthCheck):
    """文件系统健康检查"""

    def __init__(self, config: HealthCheckConfig, paths_to_check: List[str]):
        super().__init__(config)
        self.paths_to_check = paths_to_check

    def _perform_check(self) -> HealthCheckResult:
        """检查文件系统可访问性"""
        try:
            issues = []
            accessible_paths = 0
            total_paths = len(self.paths_to_check)

            for path_str in self.paths_to_check:
                path = Path(path_str)

                try:
                    if path.exists():
                        # 检查读写权限
                        if path.is_dir():
                            # 尝试在目录中创建临时文件
                            test_file = path / f".health_check_{int(time.time())}"
                            try:
                                test_file.write_text("health check")
                                test_file.unlink()
                                accessible_paths += 1
                            except Exception:
                                issues.append(f"目录 {path} 无写入权限")
                        else:
                            # 检查文件可读性
                            try:
                                path.read_text()
                                accessible_paths += 1
                            except Exception:
                                issues.append(f"文件 {path} 无法读取")
                    else:
                        issues.append(f"路径 {path} 不存在")

                except Exception as e:
                    issues.append(f"检查路径 {path} 时出错: {str(e)}")

            # 确定状态
            accessibility_rate = (
                accessible_paths / total_paths if total_paths > 0 else 0
            )

            if accessibility_rate == 1.0:
                status = HealthStatus.HEALTHY
                message = "所有文件系统路径正常"
            elif accessibility_rate >= 0.8:
                status = HealthStatus.WARNING
                message = f"部分文件系统路径异常: {'; '.join(issues[:3])}"
            else:
                status = HealthStatus.CRITICAL
                message = f"多个文件系统路径异常: {'; '.join(issues[:3])}"

            return HealthCheckResult(
                component_name=self.config.name,
                component_type=self.config.component_type,
                status=status,
                message=message,
                details={
                    "total_paths": total_paths,
                    "accessible_paths": accessible_paths,
                    "accessibility_rate": accessibility_rate,
                    "issues": issues,
                },
                metrics={"accessibility_rate": accessibility_rate * 100},
            )

        except Exception as e:
            return HealthCheckResult(
                component_name=self.config.name,
                component_type=self.config.component_type,
                status=HealthStatus.CRITICAL,
                message=f"文件系统检查失败: {str(e)}",
                error=str(e),
            )


class ProcessHealthCheck(BaseHealthCheck):
    """进程健康检查"""

    def __init__(self, config: HealthCheckConfig, process_names: List[str]):
        super().__init__(config)
        self.process_names = process_names

    def _perform_check(self) -> HealthCheckResult:
        """检查指定进程是否运行"""
        try:
            running_processes = []
            missing_processes = []
            process_info = {}

            # 获取所有进程
            all_processes = {
                p.info["name"]: p
                for p in psutil.process_iter(
                    ["name", "pid", "cpu_percent", "memory_percent"]
                )
            }

            for process_name in self.process_names:
                if process_name in all_processes:
                    proc = all_processes[process_name]
                    running_processes.append(process_name)

                    try:
                        # 获取进程详细信息
                        with proc.oneshot():
                            process_info[process_name] = {
                                "pid": proc.pid,
                                "cpu_percent": proc.cpu_percent(),
                                "memory_percent": proc.memory_percent(),
                                "status": proc.status(),
                                "create_time": proc.create_time(),
                            }
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        process_info[process_name] = {"status": "unknown"}
                else:
                    missing_processes.append(process_name)

            # 确定状态
            running_rate = (
                len(running_processes) / len(self.process_names)
                if self.process_names
                else 1.0
            )

            if running_rate == 1.0:
                status = HealthStatus.HEALTHY
                message = "所有监控进程正在运行"
            elif running_rate >= 0.5:
                status = HealthStatus.WARNING
                message = f"部分进程未运行: {', '.join(missing_processes)}"
            else:
                status = HealthStatus.CRITICAL
                message = f"多个进程未运行: {', '.join(missing_processes)}"

            return HealthCheckResult(
                component_name=self.config.name,
                component_type=self.config.component_type,
                status=status,
                message=message,
                details={
                    "total_processes": len(self.process_names),
                    "running_processes": running_processes,
                    "missing_processes": missing_processes,
                    "process_info": process_info,
                },
                metrics={"running_rate": running_rate * 100},
            )

        except Exception as e:
            return HealthCheckResult(
                component_name=self.config.name,
                component_type=self.config.component_type,
                status=HealthStatus.CRITICAL,
                message=f"进程检查失败: {str(e)}",
                error=str(e),
            )


class ServiceHealthCheck(BaseHealthCheck):
    """服务健康检查"""

    def __init__(
        self,
        config: HealthCheckConfig,
        service_checker: Callable[[], bool],
        service_name: str = "Unknown Service",
    ):
        super().__init__(config)
        self.service_checker = service_checker
        self.service_name = service_name

    def _perform_check(self) -> HealthCheckResult:
        """检查服务状态"""
        try:
            start_time = time.time()
            is_healthy = self.service_checker()
            response_time_ms = (time.time() - start_time) * 1000

            if is_healthy:
                status = HealthStatus.HEALTHY
                message = f"{self.service_name} 服务运行正常"
            else:
                status = HealthStatus.CRITICAL
                message = f"{self.service_name} 服务异常"

            return HealthCheckResult(
                component_name=self.config.name,
                component_type=self.config.component_type,
                status=status,
                message=message,
                details={
                    "service_name": self.service_name,
                    "response_time_ms": response_time_ms,
                },
                metrics={
                    "response_time_ms": response_time_ms,
                    "is_healthy": 1.0 if is_healthy else 0.0,
                },
            )

        except Exception as e:
            return HealthCheckResult(
                component_name=self.config.name,
                component_type=self.config.component_type,
                status=HealthStatus.CRITICAL,
                message=f"{self.service_name} 服务检查失败: {str(e)}",
                error=str(e),
            )


class HealthChecker(QObject):
    """系统健康检查器"""

    # 信号定义
    health_check_completed = pyqtSignal(dict)  # 健康检查完成
    health_status_changed = pyqtSignal(str, str, str)  # 组件, 旧状态, 新状态
    overall_health_changed = pyqtSignal(str)  # 整体健康状态变化

    def __init__(self, event_bus: EventBus, db_manager: DatabaseManager = None):
        super().__init__()

        self.event_bus = event_bus
        self.db_manager = db_manager

        # 健康检查器列表
        self.health_checks: Dict[str, BaseHealthCheck] = {}

        # 检查结果历史
        self.check_results: Dict[str, List[HealthCheckResult]] = {}
        self.max_history_size = 100

        # 状态管理
        self.running = False
        self.check_threads: Dict[str, threading.Thread] = {}
        self.check_timers: Dict[str, QTimer] = {}

        # 整体健康状态
        self.overall_health_status = HealthStatus.UNKNOWN

        # 统计信息
        self.stats = {
            "total_checks": 0,
            "healthy_components": 0,
            "warning_components": 0,
            "critical_components": 0,
            "offline_components": 0,
            "last_check_time": None,
        }

        # 设置默认健康检查
        self._setup_default_checks()

        logger.info("健康检查器初始化完成")

    def start(self):
        """启动健康检查器"""
        if not self.running:
            self.running = True

            # 启动所有健康检查
            for name, health_check in self.health_checks.items():
                if health_check.config.enabled:
                    self._start_health_check(name, health_check)

            logger.info("健康检查器已启动")

    def stop(self):
        """停止健康检查器"""
        self.running = False

        # 停止所有定时器
        for timer in self.check_timers.values():
            timer.stop()

        # 等待所有检查线程完成
        for thread in self.check_threads.values():
            if thread.is_alive():
                thread.join(timeout=5)

        self.check_timers.clear()
        self.check_threads.clear()

        logger.info("健康检查器已停止")

    def add_health_check(self, name: str, health_check: BaseHealthCheck):
        """添加健康检查"""
        self.health_checks[name] = health_check
        self.check_results[name] = []

        if self.running and health_check.config.enabled:
            self._start_health_check(name, health_check)

        logger.info(f"添加健康检查: {name}")

    def remove_health_check(self, name: str):
        """移除健康检查"""
        if name in self.health_checks:
            # 停止定时器
            if name in self.check_timers:
                self.check_timers[name].stop()
                del self.check_timers[name]

            # 等待线程完成
            if name in self.check_threads and self.check_threads[name].is_alive():
                self.check_threads[name].join(timeout=5)
                del self.check_threads[name]

            # 移除检查器和结果
            del self.health_checks[name]
            if name in self.check_results:
                del self.check_results[name]

            logger.info(f"移除健康检查: {name}")

    def get_health_check(self, name: str) -> Optional[BaseHealthCheck]:
        """获取健康检查器"""
        return self.health_checks.get(name)

    def get_all_health_checks(self) -> Dict[str, BaseHealthCheck]:
        """获取所有健康检查器"""
        return self.health_checks.copy()

    def get_latest_result(self, name: str) -> Optional[HealthCheckResult]:
        """获取最新的检查结果"""
        results = self.check_results.get(name, [])
        return results[-1] if results else None

    def get_results_history(
        self, name: str, limit: int = None
    ) -> List[HealthCheckResult]:
        """获取检查结果历史"""
        results = self.check_results.get(name, [])
        if limit:
            return results[-limit:]
        return results.copy()

    def get_overall_health_status(self) -> HealthStatus:
        """获取整体健康状态"""
        return self.overall_health_status

    def get_health_summary(self) -> Dict[str, Any]:
        """获取健康状态摘要"""
        summary = {
            "overall_status": self.overall_health_status.value,
            "components": {},
            "statistics": self.stats.copy(),
        }

        for name, health_check in self.health_checks.items():
            latest_result = self.get_latest_result(name)
            if latest_result:
                summary["components"][name] = {
                    "status": latest_result.status.value,
                    "message": latest_result.message,
                    "last_check": latest_result.timestamp.isoformat(),
                    "check_duration_ms": latest_result.check_duration_ms,
                    "component_type": latest_result.component_type.value,
                    "metrics": latest_result.metrics,
                }
            else:
                summary["components"][name] = {
                    "status": HealthStatus.UNKNOWN.value,
                    "message": "尚未检查",
                    "component_type": health_check.config.component_type.value,
                }

        return summary

    def run_immediate_check(self, name: str = None) -> Dict[str, HealthCheckResult]:
        """立即运行健康检查"""
        results = {}

        if name:
            # 检查指定组件
            if name in self.health_checks:
                result = self.health_checks[name].check()
                self._process_check_result(name, result)
                results[name] = result
        else:
            # 检查所有组件
            for check_name, health_check in self.health_checks.items():
                if health_check.config.enabled:
                    result = health_check.check()
                    self._process_check_result(check_name, result)
                    results[check_name] = result

        return results

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.stats.copy()

    def _setup_default_checks(self):
        """设置默认健康检查"""
        # 系统资源检查
        system_config = HealthCheckConfig(
            name="system_resources",
            component_type=ComponentType.CPU,
            check_interval_seconds=30,
            warning_threshold=80.0,
            critical_threshold=95.0,
        )
        self.add_health_check(
            "system_resources", SystemResourceHealthCheck(system_config)
        )

        # 数据库检查（如果有数据库管理器）
        if self.db_manager:
            db_config = HealthCheckConfig(
                name="database",
                component_type=ComponentType.DATABASE,
                check_interval_seconds=60,
                timeout_seconds=10,
            )
            self.add_health_check(
                "database", DatabaseHealthCheck(db_config, self.db_manager)
            )

        # 文件系统检查
        important_paths = [
            "./",  # 当前目录
            "./logs",  # 日志目录
            "./data",  # 数据目录
            "./config",  # 配置目录
        ]

        fs_config = HealthCheckConfig(
            name="filesystem",
            component_type=ComponentType.FILESYSTEM,
            check_interval_seconds=120,
        )
        self.add_health_check(
            "filesystem", FileSystemHealthCheck(fs_config, important_paths)
        )

    def _start_health_check(self, name: str, health_check: BaseHealthCheck):
        """启动单个健康检查"""
        # 创建定时器
        timer = QTimer()
        timer.timeout.connect(lambda: self._run_check_async(name))
        timer.start(health_check.config.check_interval_seconds * 1000)

        self.check_timers[name] = timer

        # 立即执行一次检查
        self._run_check_async(name)

        logger.debug(
            f"启动健康检查: {name}, 间隔: {health_check.config.check_interval_seconds}秒"
        )

    def _run_check_async(self, name: str):
        """异步运行健康检查"""
        if name not in self.health_checks:
            return

        # 如果已有线程在运行，跳过此次检查
        if name in self.check_threads and self.check_threads[name].is_alive():
            logger.debug(f"跳过健康检查 {name}，上次检查仍在进行中")
            return

        # 创建新线程执行检查
        thread = threading.Thread(
            target=self._run_check_sync, args=(name,), daemon=True
        )
        thread.start()
        self.check_threads[name] = thread

    def _run_check_sync(self, name: str):
        """同步运行健康检查"""
        try:
            health_check = self.health_checks[name]
            result = health_check.check()
            self._process_check_result(name, result)

        except Exception as e:
            logger.error(f"健康检查 {name} 执行失败: {e}")

            # 创建错误结果
            error_result = HealthCheckResult(
                component_name=name,
                component_type=self.health_checks[name].config.component_type,
                status=HealthStatus.CRITICAL,
                message=f"健康检查执行失败: {str(e)}",
                error=str(e),
            )
            self._process_check_result(name, error_result)

    def _process_check_result(self, name: str, result: HealthCheckResult):
        """处理检查结果"""
        # 获取之前的状态
        previous_result = self.get_latest_result(name)
        previous_status = (
            previous_result.status if previous_result else HealthStatus.UNKNOWN
        )

        # 保存结果
        if name not in self.check_results:
            self.check_results[name] = []

        self.check_results[name].append(result)

        # 限制历史记录大小
        if len(self.check_results[name]) > self.max_history_size:
            self.check_results[name] = self.check_results[name][
                -self.max_history_size :
            ]

        # 更新统计信息
        self._update_statistics()

        # 检查状态变化
        if result.status != previous_status:
            self.health_status_changed.emit(
                name, previous_status.value, result.status.value
            )

            # 发送事件
            self.event_bus.emit(
                "health_status_changed",
                {
                    "component": name,
                    "previous_status": previous_status.value,
                    "current_status": result.status.value,
                    "message": result.message,
                    "timestamp": result.timestamp.isoformat(),
                },
            )

            logger.info(
                f"组件 {name} 健康状态变化: {previous_status.value} -> {result.status.value}"
            )

        # 更新整体健康状态
        self._update_overall_health_status()

        # 发射信号
        self.health_check_completed.emit(
            {
                "component": name,
                "status": result.status.value,
                "message": result.message,
                "timestamp": result.timestamp.isoformat(),
                "check_duration_ms": result.check_duration_ms,
                "metrics": result.metrics,
            }
        )

        # 记录日志
        if result.status == HealthStatus.CRITICAL:
            logger.error(f"健康检查 {name} 严重异常: {result.message}")
        elif result.status == HealthStatus.WARNING:
            logger.warning(f"健康检查 {name} 警告: {result.message}")
        else:
            logger.debug(f"健康检查 {name} 完成: {result.message}")

    def _update_statistics(self):
        """更新统计信息"""
        self.stats["total_checks"] = sum(
            len(results) for results in self.check_results.values()
        )
        self.stats["last_check_time"] = datetime.now().isoformat()

        # 统计当前状态
        status_counts = {
            HealthStatus.HEALTHY: 0,
            HealthStatus.WARNING: 0,
            HealthStatus.CRITICAL: 0,
            HealthStatus.OFFLINE: 0,
        }

        for name in self.health_checks:
            latest_result = self.get_latest_result(name)
            if latest_result:
                status_counts[latest_result.status] = (
                    status_counts.get(latest_result.status, 0) + 1
                )

        self.stats["healthy_components"] = status_counts[HealthStatus.HEALTHY]
        self.stats["warning_components"] = status_counts[HealthStatus.WARNING]
        self.stats["critical_components"] = status_counts[HealthStatus.CRITICAL]
        self.stats["offline_components"] = status_counts[HealthStatus.OFFLINE]

    def _update_overall_health_status(self):
        """更新整体健康状态"""
        previous_overall_status = self.overall_health_status

        # 收集所有组件的当前状态
        component_statuses = []
        for name in self.health_checks:
            latest_result = self.get_latest_result(name)
            if latest_result:
                component_statuses.append(latest_result.status)

        if not component_statuses:
            new_overall_status = HealthStatus.UNKNOWN
        elif any(status == HealthStatus.CRITICAL for status in component_statuses):
            new_overall_status = HealthStatus.CRITICAL
        elif any(status == HealthStatus.WARNING for status in component_statuses):
            new_overall_status = HealthStatus.WARNING
        elif any(status == HealthStatus.OFFLINE for status in component_statuses):
            new_overall_status = HealthStatus.WARNING  # 离线组件视为警告
        else:
            new_overall_status = HealthStatus.HEALTHY

        self.overall_health_status = new_overall_status

        # 检查整体状态变化
        if new_overall_status != previous_overall_status:
            self.overall_health_changed.emit(new_overall_status.value)

            # 发送事件
            self.event_bus.emit(
                "overall_health_changed",
                {
                    "previous_status": previous_overall_status.value,
                    "current_status": new_overall_status.value,
                    "timestamp": datetime.now().isoformat(),
                },
            )

            logger.info(
                f"整体健康状态变化: {previous_overall_status.value} -> {new_overall_status.value}"
            )


# 全局健康检查器实例
_health_checker_instance: Optional[HealthChecker] = None


def get_health_checker() -> Optional[HealthChecker]:
    """获取全局健康检查器实例"""
    return _health_checker_instance


def set_health_checker(health_checker: HealthChecker):
    """设置全局健康检查器实例"""
    global _health_checker_instance
    _health_checker_instance = health_checker
