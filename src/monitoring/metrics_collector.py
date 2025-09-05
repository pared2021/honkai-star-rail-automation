"""指标收集器模块.

提供系统指标的收集和管理功能。
"""

from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
import logging
import threading
import time
from typing import Any, Callable, Dict, List, Optional, Union


class MetricType(Enum):
    """指标类型枚举."""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"
    TIMER = "timer"


@dataclass
class Metric:
    """指标数据类."""

    name: str
    value: Union[int, float]
    metric_type: MetricType
    timestamp: float = field(default_factory=time.time)
    labels: Dict[str, str] = field(default_factory=dict)
    unit: Optional[str] = None
    description: Optional[str] = None


class MetricsCollector:
    """指标收集器.

    负责收集、存储和管理系统指标。
    """

    def __init__(self, max_metrics: int = 10000):
        """初始化指标收集器.

        Args:
            max_metrics: 最大指标数量
        """
        self._metrics: Dict[str, List[Metric]] = defaultdict(list)
        self._counters: Dict[str, float] = defaultdict(float)
        self._gauges: Dict[str, float] = defaultdict(float)
        self._histograms: Dict[str, List[float]] = defaultdict(list)
        self._timers: Dict[str, List[float]] = defaultdict(list)
        self._max_metrics = max_metrics
        self._lock = threading.RLock()
        self._logger = logging.getLogger(__name__)
        self._collectors: Dict[str, Callable[[], Dict[str, Any]]] = {}

    def record_counter(
        self, name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None
    ) -> None:
        """记录计数器指标.

        Args:
            name: 指标名称
            value: 增量值
            labels: 标签
        """
        with self._lock:
            key = self._make_key(name, labels)
            self._counters[key] += value

            metric = Metric(
                name=name,
                value=self._counters[key],
                metric_type=MetricType.COUNTER,
                labels=labels or {},
            )

            self._add_metric(name, metric)

    def set_gauge(
        self, name: str, value: float, labels: Optional[Dict[str, str]] = None
    ) -> None:
        """设置仪表盘指标.

        Args:
            name: 指标名称
            value: 指标值
            labels: 标签
        """
        with self._lock:
            key = self._make_key(name, labels)
            self._gauges[key] = value

            metric = Metric(
                name=name,
                value=value,
                metric_type=MetricType.GAUGE,
                labels=labels or {},
            )

            self._add_metric(name, metric)

    def record_histogram(
        self, name: str, value: float, labels: Optional[Dict[str, str]] = None
    ) -> None:
        """记录直方图指标.

        Args:
            name: 指标名称
            value: 观测值
            labels: 标签
        """
        with self._lock:
            key = self._make_key(name, labels)
            self._histograms[key].append(value)

            # 保持最近的1000个值
            if len(self._histograms[key]) > 1000:
                self._histograms[key] = self._histograms[key][-1000:]

            metric = Metric(
                name=name,
                value=value,
                metric_type=MetricType.HISTOGRAM,
                labels=labels or {},
            )

            self._add_metric(name, metric)

    def record_timer(
        self, name: str, duration: float, labels: Optional[Dict[str, str]] = None
    ) -> None:
        """记录计时器指标.

        Args:
            name: 指标名称
            duration: 持续时间（秒）
            labels: 标签
        """
        with self._lock:
            key = self._make_key(name, labels)
            self._timers[key].append(duration)

            # 保持最近的1000个值
            if len(self._timers[key]) > 1000:
                self._timers[key] = self._timers[key][-1000:]

            metric = Metric(
                name=name,
                value=duration,
                metric_type=MetricType.TIMER,
                labels=labels or {},
                unit="seconds",
            )

            self._add_metric(name, metric)

    def timer(
        self, name: str, labels: Optional[Dict[str, str]] = None
    ) -> "TimerContext":
        """创建计时器上下文管理器.

        Args:
            name: 指标名称
            labels: 标签

        Returns:
            计时器上下文管理器
        """
        return TimerContext(self, name, labels)

    def collect_metrics(
        self, metric_name: Optional[str] = None
    ) -> Dict[str, List[Metric]]:
        """收集指标.

        Args:
            metric_name: 指定指标名称，None表示收集所有指标

        Returns:
            指标字典
        """
        # 运行自定义收集器
        self._run_collectors()

        with self._lock:
            if metric_name is not None:
                return {metric_name: self._metrics.get(metric_name, [])}
            else:
                return {name: metrics.copy() for name, metrics in self._metrics.items()}

    def get_counter(self, name: str, labels: Optional[Dict[str, str]] = None) -> float:
        """获取计数器值.

        Args:
            name: 指标名称
            labels: 标签

        Returns:
            计数器值
        """
        with self._lock:
            key = self._make_key(name, labels)
            return self._counters.get(key, 0.0)

    def get_gauge(
        self, name: str, labels: Optional[Dict[str, str]] = None
    ) -> Optional[float]:
        """获取仪表盘值.

        Args:
            name: 指标名称
            labels: 标签

        Returns:
            仪表盘值
        """
        with self._lock:
            key = self._make_key(name, labels)
            return self._gauges.get(key)

    def get_histogram_stats(
        self, name: str, labels: Optional[Dict[str, str]] = None
    ) -> Optional[Dict[str, float]]:
        """获取直方图统计信息.

        Args:
            name: 指标名称
            labels: 标签

        Returns:
            统计信息字典
        """
        with self._lock:
            key = self._make_key(name, labels)
            values = self._histograms.get(key, [])

            if not values:
                return None

            values_sorted = sorted(values)
            count = len(values)

            return {
                "count": count,
                "sum": sum(values),
                "min": min(values),
                "max": max(values),
                "mean": sum(values) / count,
                "p50": values_sorted[int(count * 0.5)],
                "p90": values_sorted[int(count * 0.9)],
                "p95": values_sorted[int(count * 0.95)],
                "p99": values_sorted[int(count * 0.99)],
            }

    def get_timer_stats(
        self, name: str, labels: Optional[Dict[str, str]] = None
    ) -> Optional[Dict[str, float]]:
        """获取计时器统计信息.

        Args:
            name: 指标名称
            labels: 标签

        Returns:
            统计信息字典
        """
        with self._lock:
            key = self._make_key(name, labels)
            values = self._timers.get(key, [])

            if not values:
                return None

            values_sorted = sorted(values)
            count = len(values)

            return {
                "count": count,
                "sum": sum(values),
                "min": min(values),
                "max": max(values),
                "mean": sum(values) / count,
                "p50": values_sorted[int(count * 0.5)],
                "p90": values_sorted[int(count * 0.9)],
                "p95": values_sorted[int(count * 0.95)],
                "p99": values_sorted[int(count * 0.99)],
            }

    def register_collector(
        self, name: str, collector_func: Callable[[], Dict[str, Any]]
    ) -> None:
        """注册自定义指标收集器.

        Args:
            name: 收集器名称
            collector_func: 收集器函数，应返回指标字典
        """
        with self._lock:
            self._collectors[name] = collector_func

        self._logger.info(f"Metrics collector registered: {name}")

    def unregister_collector(self, name: str) -> bool:
        """注销自定义指标收集器.

        Args:
            name: 收集器名称

        Returns:
            是否成功注销
        """
        with self._lock:
            if name in self._collectors:
                del self._collectors[name]
                self._logger.info(f"Metrics collector unregistered: {name}")
                return True

        return False

    def get_all_metrics(self) -> Dict[str, Any]:
        """获取所有指标的汇总信息.

        Returns:
            指标汇总字典
        """
        with self._lock:
            result: Dict[str, Any] = {
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
                "histograms": {},
                "timers": {},
                "timestamp": time.time(),
            }

            # 添加直方图统计
            for key, values in self._histograms.items():
                if values:
                    result["histograms"][key] = self._calculate_stats(values)

            # 添加计时器统计
            for key, values in self._timers.items():
                if values:
                    result["timers"][key] = self._calculate_stats(values)

            return result

    def start(self) -> None:
        """开始指标收集."""
        self._logger.info("Metrics collection started")

    def stop(self) -> None:
        """停止指标收集."""
        self._logger.info("Metrics collection stopped")

    def reset_metrics(self, metric_name: Optional[str] = None) -> None:
        """重置指标.

        Args:
            metric_name: 指定指标名称，None表示重置所有指标
        """
        with self._lock:
            if metric_name is not None:
                # 重置特定指标
                if metric_name in self._metrics:
                    del self._metrics[metric_name]

                # 重置相关的计数器、仪表盘等
                keys_to_remove = [
                    key for key in self._counters.keys() if key.startswith(metric_name)
                ]
                for key in keys_to_remove:
                    del self._counters[key]

                keys_to_remove = [
                    key for key in self._gauges.keys() if key.startswith(metric_name)
                ]
                for key in keys_to_remove:
                    del self._gauges[key]

                keys_to_remove = [
                    key
                    for key in self._histograms.keys()
                    if key.startswith(metric_name)
                ]
                for key in keys_to_remove:
                    del self._histograms[key]

                keys_to_remove = [
                    key for key in self._timers.keys() if key.startswith(metric_name)
                ]
                for key in keys_to_remove:
                    del self._timers[key]
            else:
                # 重置所有指标
                self._metrics.clear()
                self._counters.clear()
                self._gauges.clear()
                self._histograms.clear()
                self._timers.clear()

        self._logger.info(f"Metrics reset: {metric_name or 'all'}")

    def _make_key(self, name: str, labels: Optional[Dict[str, str]]) -> str:
        """创建指标键.

        Args:
            name: 指标名称
            labels: 标签

        Returns:
            指标键
        """
        if not labels:
            return name

        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"

    def _add_metric(self, name: str, metric: Metric) -> None:
        """添加指标到历史记录.

        Args:
            name: 指标名称
            metric: 指标对象
        """
        self._metrics[name].append(metric)

        # 保持最近的指标数量限制
        if len(self._metrics[name]) > self._max_metrics:
            self._metrics[name] = self._metrics[name][-self._max_metrics :]

    def _run_collectors(self) -> None:
        """运行自定义收集器."""
        for name, collector_func in self._collectors.items():
            try:
                metrics_data = collector_func()

                # 处理收集到的指标数据
                for metric_name, value in metrics_data.items():
                    if isinstance(value, (int, float)):
                        self.set_gauge(f"{name}.{metric_name}", float(value))
                    elif isinstance(value, dict) and "value" in value:
                        metric_type = value.get("type", "gauge")
                        metric_value = float(value["value"])
                        labels = value.get("labels", {})

                        if metric_type == "counter":
                            self.record_counter(
                                f"{name}.{metric_name}", metric_value, labels
                            )
                        elif metric_type == "gauge":
                            self.set_gauge(
                                f"{name}.{metric_name}", metric_value, labels
                            )
                        elif metric_type == "histogram":
                            self.record_histogram(
                                f"{name}.{metric_name}", metric_value, labels
                            )
                        elif metric_type == "timer":
                            self.record_timer(
                                f"{name}.{metric_name}", metric_value, labels
                            )

            except Exception as e:
                self._logger.error(f"Error running collector {name}: {e}")

    def _calculate_stats(self, values: List[float]) -> Dict[str, float]:
        """计算统计信息.

        Args:
            values: 数值列表

        Returns:
            统计信息字典
        """
        if not values:
            return {}

        values_sorted = sorted(values)
        count = len(values)

        return {
            "count": count,
            "sum": sum(values),
            "min": min(values),
            "max": max(values),
            "mean": sum(values) / count,
            "p50": values_sorted[int(count * 0.5)],
            "p90": values_sorted[int(count * 0.9)],
            "p95": values_sorted[int(count * 0.95)],
            "p99": values_sorted[int(count * 0.99)],
        }


class TimerContext:
    """计时器上下文管理器."""

    def __init__(
        self,
        collector: MetricsCollector,
        name: str,
        labels: Optional[Dict[str, str]] = None,
    ):
        """初始化计时器上下文.

        Args:
            collector: 指标收集器
            name: 指标名称
            labels: 标签
        """
        self._collector = collector
        self._name = name
        self._labels = labels
        self._start_time: Optional[float] = None

    def __enter__(self) -> "TimerContext":
        """进入上下文."""
        self._start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """退出上下文."""
        if self._start_time is not None:
            duration = time.time() - self._start_time
            self._collector.record_timer(self._name, duration, self._labels)
