"""健康检查器模块.

提供系统健康状态检查功能。
"""

from dataclasses import dataclass, field
from enum import Enum
import logging
import threading
import time
from typing import Any, Callable, Dict, Optional, Union


class HealthStatus(Enum):
    """健康状态枚举."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    """健康检查结果数据类."""

    component: str
    status: HealthStatus
    message: str
    timestamp: float = field(default_factory=time.time)
    details: Dict[str, Any] = field(default_factory=dict)
    duration: float = 0.0


class HealthChecker:
    """健康检查器.

    负责检查系统各组件的健康状态。
    """

    def __init__(self, check_interval: float = 30.0):
        """初始化健康检查器.

        Args:
            check_interval: 检查间隔（秒）
        """
        self._check_interval = check_interval
        self._checks: Dict[str, Callable[[], HealthCheckResult]] = {}
        self._results: Dict[str, HealthCheckResult] = {}
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.RLock()
        self._logger = logging.getLogger(__name__)
        self._overall_status = HealthStatus.UNKNOWN

    def add_check(self, name: str, check_func: Callable[[], HealthCheckResult]) -> None:
        """添加健康检查.

        Args:
            name: 检查名称
            check_func: 检查函数
        """
        with self._lock:
            self._checks[name] = check_func

        self._logger.info(f"Health check added: {name}")

    def remove_check(self, name: str) -> bool:
        """移除健康检查.

        Args:
            name: 检查名称

        Returns:
            是否成功移除
        """
        with self._lock:
            if name in self._checks:
                del self._checks[name]
                if name in self._results:
                    del self._results[name]
                self._logger.info(f"Health check removed: {name}")
                return True

        return False

    def check_health(
        self, component: Optional[str] = None
    ) -> Union[HealthCheckResult, Dict[str, HealthCheckResult]]:
        """执行健康检查.

        Args:
            component: 指定组件名称，None表示检查所有组件

        Returns:
            健康检查结果
        """
        if component is not None:
            # 检查指定组件
            if component not in self._checks:
                return HealthCheckResult(
                    component=component,
                    status=HealthStatus.UNKNOWN,
                    message=f"Component '{component}' not found",
                )

            start_time = time.time()
            try:
                check_func = self._checks[component]
                result = check_func()
                result.duration = time.time() - start_time

                with self._lock:
                    self._results[component] = result

                self._logger.debug(
                    f"Health check completed for {component}: {result.status}"
                )
                return result
            except Exception as e:
                duration = time.time() - start_time
                result = HealthCheckResult(
                    component=component,
                    status=HealthStatus.UNHEALTHY,
                    message=f"Health check failed: {str(e)}",
                    duration=duration,
                )

                with self._lock:
                    self._results[component] = result

                self._logger.error(f"Health check failed for {component}: {e}")
                return result
        else:
            # 检查所有组件
            results: Dict[str, HealthCheckResult] = {}

            with self._lock:
                checks = self._checks.copy()

            for name in checks:
                single_result = self.check_health(name)
                if isinstance(single_result, HealthCheckResult):
                    results[name] = single_result

            # 更新整体状态
            self._update_overall_status(results)

            return results

    def get_status(
        self, component: Optional[str] = None
    ) -> Union[HealthStatus, Dict[str, HealthStatus]]:
        """获取健康状态.

        Args:
            component: 指定组件名称，None表示获取所有组件状态

        Returns:
            健康状态
        """
        if component is not None:
            with self._lock:
                result = self._results.get(component)
                return result.status if result else HealthStatus.UNKNOWN
        else:
            with self._lock:
                return {name: result.status for name, result in self._results.items()}

    def get_overall_status(self) -> HealthStatus:
        """获取整体健康状态.

        Returns:
            整体健康状态
        """
        with self._lock:
            return self._overall_status

    def get_results(
        self, component: Optional[str] = None
    ) -> Union[Optional[HealthCheckResult], Dict[str, HealthCheckResult]]:
        """获取健康检查结果.

        Args:
            component: 指定组件名称，None表示获取所有结果

        Returns:
            健康检查结果
        """
        with self._lock:
            if component is not None:
                return self._results.get(component)
            else:
                return self._results.copy()

    def start(self) -> None:
        """开始监控."""
        self.start_monitoring()

    def stop(self) -> None:
        """停止监控."""
        self.stop_monitoring()

    def start_monitoring(self) -> None:
        """开始监控."""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self._thread.start()

        self._logger.info("Health monitoring started")

    def stop_monitoring(self) -> None:
        """停止监控."""
        if not self._running:
            return

        self._running = False

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5.0)

        self._logger.info("Health monitoring stopped")

    def _monitoring_loop(self) -> None:
        """监控循环."""
        while self._running:
            try:
                self.check_health()
                time.sleep(self._check_interval)
            except Exception as e:
                self._logger.error(f"Error in health monitoring loop: {e}")
                time.sleep(1.0)  # 短暂休息后继续

    def _update_overall_status(self, results: Dict[str, HealthCheckResult]) -> None:
        """更新整体状态.

        Args:
            results: 检查结果字典
        """
        if not results:
            self._overall_status = HealthStatus.UNKNOWN
            return

        statuses = [result.status for result in results.values()]

        # 如果有任何组件不健康，整体状态为不健康
        if HealthStatus.UNHEALTHY in statuses:
            self._overall_status = HealthStatus.UNHEALTHY
        # 如果有任何组件降级，整体状态为降级
        elif HealthStatus.DEGRADED in statuses:
            self._overall_status = HealthStatus.DEGRADED
        # 如果所有组件都健康，整体状态为健康
        elif all(status == HealthStatus.HEALTHY for status in statuses):
            self._overall_status = HealthStatus.HEALTHY
        # 其他情况为未知
        else:
            self._overall_status = HealthStatus.UNKNOWN

    def create_basic_checks(self) -> None:
        """创建基本的健康检查."""
        # CPU 使用率检查
        def cpu_check() -> HealthCheckResult:
            try:
                import psutil

                cpu_percent = psutil.cpu_percent(interval=1)

                if cpu_percent > 90:
                    status = HealthStatus.UNHEALTHY
                    message = f"High CPU usage: {cpu_percent}%"
                elif cpu_percent > 70:
                    status = HealthStatus.DEGRADED
                    message = f"Moderate CPU usage: {cpu_percent}%"
                else:
                    status = HealthStatus.HEALTHY
                    message = f"Normal CPU usage: {cpu_percent}%"

                return HealthCheckResult(
                    component="cpu",
                    status=status,
                    message=message,
                    details={"cpu_percent": cpu_percent},
                )
            except ImportError:
                return HealthCheckResult(
                    component="cpu",
                    status=HealthStatus.UNKNOWN,
                    message="psutil not available for CPU monitoring",
                )
            except Exception as e:
                return HealthCheckResult(
                    component="cpu",
                    status=HealthStatus.UNHEALTHY,
                    message=f"CPU check failed: {str(e)}",
                )

        # 内存使用率检查
        def memory_check() -> HealthCheckResult:
            try:
                import psutil

                memory = psutil.virtual_memory()

                if memory.percent > 90:
                    status = HealthStatus.UNHEALTHY
                    message = f"High memory usage: {memory.percent}%"
                elif memory.percent > 80:
                    status = HealthStatus.DEGRADED
                    message = f"Moderate memory usage: {memory.percent}%"
                else:
                    status = HealthStatus.HEALTHY
                    message = f"Normal memory usage: {memory.percent}%"

                return HealthCheckResult(
                    component="memory",
                    status=status,
                    message=message,
                    details={
                        "percent": memory.percent,
                        "available": memory.available,
                        "total": memory.total,
                    },
                )
            except ImportError:
                return HealthCheckResult(
                    component="memory",
                    status=HealthStatus.UNKNOWN,
                    message="psutil not available for memory monitoring",
                )
            except Exception as e:
                return HealthCheckResult(
                    component="memory",
                    status=HealthStatus.UNHEALTHY,
                    message=f"Memory check failed: {str(e)}",
                )

        # 磁盘使用率检查
        def disk_check() -> HealthCheckResult:
            try:
                import psutil

                disk = psutil.disk_usage("/")
                percent = (disk.used / disk.total) * 100

                if percent > 90:
                    status = HealthStatus.UNHEALTHY
                    message = f"High disk usage: {percent:.1f}%"
                elif percent > 80:
                    status = HealthStatus.DEGRADED
                    message = f"Moderate disk usage: {percent:.1f}%"
                else:
                    status = HealthStatus.HEALTHY
                    message = f"Normal disk usage: {percent:.1f}%"

                return HealthCheckResult(
                    component="disk",
                    status=status,
                    message=message,
                    details={
                        "percent": percent,
                        "free": disk.free,
                        "total": disk.total,
                    },
                )
            except ImportError:
                return HealthCheckResult(
                    component="disk",
                    status=HealthStatus.UNKNOWN,
                    message="psutil not available for disk monitoring",
                )
            except Exception as e:
                return HealthCheckResult(
                    component="disk",
                    status=HealthStatus.UNHEALTHY,
                    message=f"Disk check failed: {str(e)}",
                )

        self.add_check("cpu", cpu_check)
        self.add_check("memory", memory_check)
        self.add_check("disk", disk_check)
