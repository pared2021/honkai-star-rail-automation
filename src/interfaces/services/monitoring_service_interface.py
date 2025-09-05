"""监控服务接口

定义系统监控和性能管理的业务逻辑接口。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from datetime import datetime
from enum import Enum


class MetricType(Enum):
    """指标类型枚举"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


class AlertLevel(Enum):
    """告警级别枚举"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class IMonitoringService(ABC):
    """监控服务接口
    
    定义系统监控和性能管理的业务操作。
    """
    
    @abstractmethod
    async def record_metric(
        self,
        name: str,
        value: float,
        metric_type: MetricType = MetricType.GAUGE,
        tags: Optional[Dict[str, str]] = None,
        timestamp: Optional[datetime] = None
    ) -> bool:
        """记录指标
        
        Args:
            name: 指标名称
            value: 指标值
            metric_type: 指标类型
            tags: 标签
            timestamp: 时间戳
            
        Returns:
            是否记录成功
        """
        pass
    
    @abstractmethod
    async def increment_counter(
        self,
        name: str,
        value: float = 1.0,
        tags: Optional[Dict[str, str]] = None
    ) -> bool:
        """递增计数器
        
        Args:
            name: 计数器名称
            value: 递增值
            tags: 标签
            
        Returns:
            是否递增成功
        """
        pass
    
    @abstractmethod
    async def set_gauge(
        self,
        name: str,
        value: float,
        tags: Optional[Dict[str, str]] = None
    ) -> bool:
        """设置仪表盘值
        
        Args:
            name: 仪表盘名称
            value: 值
            tags: 标签
            
        Returns:
            是否设置成功
        """
        pass
    
    @abstractmethod
    async def record_timer(
        self,
        name: str,
        duration: float,
        tags: Optional[Dict[str, str]] = None
    ) -> bool:
        """记录计时器
        
        Args:
            name: 计时器名称
            duration: 持续时间（秒）
            tags: 标签
            
        Returns:
            是否记录成功
        """
        pass
    
    @abstractmethod
    async def get_metrics(
        self,
        name_pattern: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        tags: Optional[Dict[str, str]] = None
    ) -> List[Dict[str, Any]]:
        """获取指标数据
        
        Args:
            name_pattern: 指标名称模式
            start_time: 开始时间
            end_time: 结束时间
            tags: 标签过滤
            
        Returns:
            指标数据列表
        """
        pass
    
    @abstractmethod
    async def get_system_metrics(self) -> Dict[str, Any]:
        """获取系统指标
        
        Returns:
            系统指标字典
        """
        pass
    
    @abstractmethod
    async def get_application_metrics(self) -> Dict[str, Any]:
        """获取应用指标
        
        Returns:
            应用指标字典
        """
        pass
    
    @abstractmethod
    async def create_alert_rule(
        self,
        name: str,
        condition: str,
        level: AlertLevel,
        message: str,
        enabled: bool = True
    ) -> str:
        """创建告警规则
        
        Args:
            name: 规则名称
            condition: 告警条件
            level: 告警级别
            message: 告警消息
            enabled: 是否启用
            
        Returns:
            规则ID
        """
        pass
    
    @abstractmethod
    async def update_alert_rule(
        self,
        rule_id: str,
        name: Optional[str] = None,
        condition: Optional[str] = None,
        level: Optional[AlertLevel] = None,
        message: Optional[str] = None,
        enabled: Optional[bool] = None
    ) -> bool:
        """更新告警规则
        
        Args:
            rule_id: 规则ID
            name: 规则名称
            condition: 告警条件
            level: 告警级别
            message: 告警消息
            enabled: 是否启用
            
        Returns:
            是否更新成功
        """
        pass
    
    @abstractmethod
    async def delete_alert_rule(self, rule_id: str) -> bool:
        """删除告警规则
        
        Args:
            rule_id: 规则ID
            
        Returns:
            是否删除成功
        """
        pass
    
    @abstractmethod
    async def get_alert_rules(self) -> List[Dict[str, Any]]:
        """获取告警规则列表
        
        Returns:
            告警规则列表
        """
        pass
    
    @abstractmethod
    async def get_active_alerts(self) -> List[Dict[str, Any]]:
        """获取活跃告警
        
        Returns:
            活跃告警列表
        """
        pass
    
    @abstractmethod
    async def acknowledge_alert(self, alert_id: str) -> bool:
        """确认告警
        
        Args:
            alert_id: 告警ID
            
        Returns:
            是否确认成功
        """
        pass
    
    @abstractmethod
    async def start_monitoring(self) -> bool:
        """开始监控
        
        Returns:
            是否启动成功
        """
        pass
    
    @abstractmethod
    async def stop_monitoring(self) -> bool:
        """停止监控
        
        Returns:
            是否停止成功
        """
        pass
    
    @abstractmethod
    async def get_monitoring_status(self) -> Dict[str, Any]:
        """获取监控状态
        
        Returns:
            监控状态信息
        """
        pass
    
    @abstractmethod
    async def configure_monitoring(
        self,
        config: Dict[str, Any]
    ) -> bool:
        """配置监控
        
        Args:
            config: 监控配置
            
        Returns:
            是否配置成功
        """
        pass
    
    @abstractmethod
    async def export_metrics(
        self,
        format_type: str = "json",
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> str:
        """导出指标数据
        
        Args:
            format_type: 导出格式
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            导出文件路径
        """
        pass