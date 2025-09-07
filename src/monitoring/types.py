"""监控系统类型定义模块.

包含监控系统中使用的共享类型和枚举。
"""

from dataclasses import dataclass, field
from enum import Enum
import time
from typing import Any, Dict


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
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式.
        
        Returns:
            字典格式的健康检查结果
        """
        return {
            'component': self.component,
            'status': self.status.value,
            'message': self.message,
            'timestamp': self.timestamp,
            'details': self.details,
            'duration': self.duration
        }


class AlertSeverity(Enum):
    """告警严重程度枚举."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertStatus(Enum):
    """告警状态枚举."""

    ACTIVE = "active"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"


@dataclass
class Alert:
    """告警数据类."""

    name: str
    severity: AlertSeverity
    message: str
    component: str
    status: AlertStatus = AlertStatus.ACTIVE
    timestamp: float = field(default_factory=time.time)
    resolved_at: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def duration(self) -> float:
        """获取告警持续时间（秒）."""
        if self.status == AlertStatus.RESOLVED and self.resolved_at > 0:
            return self.resolved_at - self.timestamp
        return time.time() - self.timestamp


@dataclass
class AlertRule:
    """告警规则数据类."""

    name: str
    condition: str  # 条件表达式
    severity: AlertSeverity
    message_template: str
    component: str = "system"
    cooldown_seconds: float = 300.0  # 冷却时间（秒）
    enabled: bool = True
    
    def format_message(self, **kwargs) -> str:
        """格式化告警消息.
        
        Args:
            **kwargs: 消息模板参数
            
        Returns:
            格式化后的消息
        """
        try:
            return self.message_template.format(**kwargs)
        except (KeyError, ValueError) as e:
            return f"{self.message_template} (格式化失败: {e})"