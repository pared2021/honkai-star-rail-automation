# -*- coding: utf-8 -*-
"""
监控系统模块 - 提供完整的日志记录、性能监控、健康检查和告警功能
"""

from typing import Any, Dict, Optional

from loguru import logger

from src.core.config_manager import (
    AlertingConfig,
    ConfigManager as MonitoringConfigManager,
    ConfigType,
    DashboardConfig,
    HealthCheckConfig as ConfigHealthCheckConfig,
    LoggingConfig,
    MonitoringConfig,
    MonitoringSystemConfig,
    NotificationConfig,
    PerformanceConfig,
    SystemConfig,
)
from src.monitoring.alert_manager import (
    Alert,
    AlertChannel,
    AlertManager,
    AlertRule,
    AlertSeverity,
    AlertStatus,
    NotificationConfig as AlertNotificationConfig,
)
from src.monitoring.health_checker import (
    BaseHealthCheck,
    ComponentType,
    DatabaseHealthCheck,
    FileSystemHealthCheck,
    HealthCheckConfig,
    HealthChecker,
    HealthCheckResult,
    HealthStatus,
    ProcessHealthCheck,
    ServiceHealthCheck,
    SystemResourceHealthCheck,
)

# 导入核心组件
from src.monitoring.logging_monitoring_service import (
    LogEntry,
    LoggingMonitoringService,
    LogLevel,
    MonitoringEvent,
    MonitoringEventType,
    SystemMetrics,
)

# 导入UI组件
try:
    from src.ui import MonitoringDashboard
except ImportError:
    MonitoringDashboard = None
    logger.warning("监控仪表板UI组件导入失败，可能缺少PyQt6依赖")


class MonitoringSystem:
    """监控系统主类 - 整合所有监控功能"""

    def __init__(
        self, event_bus=None, db_manager=None, config_directory: str = "./config"
    ):
        """
        初始化监控系统

        Args:
            event_bus: 事件总线实例
            db_manager: 数据库管理器实例
            config_directory: 配置文件目录
        """
        self.event_bus = event_bus
        self.db_manager = db_manager

        # 初始化配置管理器
        self.config_manager = MonitoringConfigManager()

        # 获取监控配置
        self.config = self.config_manager.get_monitoring_config()

        # 初始化核心组件
        self.logging_service: Optional[LoggingMonitoringService] = None
        self.alert_manager: Optional[AlertManager] = None
        self.health_checker: Optional[HealthChecker] = None
        self.dashboard: Optional[MonitoringDashboard] = None

        # 运行状态
        self.is_running = False

        logger.info("监控系统初始化完成")

    def initialize(self) -> bool:
        """初始化所有监控组件"""
        try:
            # 初始化日志监控服务
            if self.config.monitoring.enabled:
                from src.core.performance_monitor import PerformanceMonitor
                from src.monitoring.task_monitor import TaskMonitor

                # 创建性能监控器和任务监控器
                performance_monitor = PerformanceMonitor()
                task_monitor = TaskMonitor(
                    db_manager=self.db_manager,
                    automation_controller=None,  # 暂时设为None，后续可以注入
                )

                self.logging_service = LoggingMonitoringService(
                    performance_monitor=performance_monitor,
                    task_monitor=task_monitor,
                    log_directory="logs",
                )
                logger.info("日志监控服务初始化完成")

            # 初始化告警管理器
            if self.config.alerting.enabled:
                self.alert_manager = AlertManager(event_bus=self.event_bus)
                logger.info("告警管理器初始化完成")

            # 初始化健康检查器
            if self.config.health_check.enabled:
                self.health_checker = HealthChecker(
                    event_bus=self.event_bus, db_manager=self.db_manager
                )
                logger.info("健康检查器初始化完成")

            # 初始化仪表板（如果可用）
            if self.config.dashboard.enabled and MonitoringDashboard:
                try:
                    self.dashboard = MonitoringDashboard(
                        logging_service=self.logging_service,
                        alert_manager=self.alert_manager,
                        health_checker=self.health_checker,
                    )
                    logger.info("监控仪表板初始化完成")
                except Exception as e:
                    logger.warning(f"监控仪表板初始化失败: {e}")

            # 设置组件间的连接
            self._setup_component_connections()

            logger.info("监控系统所有组件初始化完成")
            return True

        except Exception as e:
            logger.error(f"监控系统初始化失败: {e}")
            return False

    def start(self) -> bool:
        """启动监控系统"""
        if self.is_running:
            logger.warning("监控系统已在运行中")
            return True

        try:
            # 启动日志监控服务
            if self.logging_service:
                self.logging_service.start()
                logger.info("日志监控服务已启动")

            # 启动告警管理器
            if self.alert_manager:
                self.alert_manager.start()
                logger.info("告警管理器已启动")

            # 启动健康检查器
            if self.health_checker:
                self.health_checker.start()
                logger.info("健康检查器已启动")

            self.is_running = True
            logger.info("监控系统启动完成")

            # 发送系统启动事件
            if self.event_bus:
                self.event_bus.emit(
                    "monitoring_system_started",
                    {
                        "timestamp": self._get_current_timestamp(),
                        "components": self._get_active_components(),
                    },
                )

            return True

        except Exception as e:
            logger.error(f"监控系统启动失败: {e}")
            return False

    def stop(self) -> bool:
        """停止监控系统"""
        if not self.is_running:
            logger.warning("监控系统未在运行")
            return True

        try:
            # 停止健康检查器
            if self.health_checker:
                self.health_checker.stop()
                logger.info("健康检查器已停止")

            # 停止告警管理器
            if self.alert_manager:
                self.alert_manager.stop()
                logger.info("告警管理器已停止")

            # 停止日志监控服务
            if self.logging_service:
                self.logging_service.stop()
                logger.info("日志监控服务已停止")

            self.is_running = False
            logger.info("监控系统停止完成")

            # 发送系统停止事件
            if self.event_bus:
                self.event_bus.emit(
                    "monitoring_system_stopped",
                    {"timestamp": self._get_current_timestamp()},
                )

            return True

        except Exception as e:
            logger.error(f"监控系统停止失败: {e}")
            return False

    def restart(self) -> bool:
        """重启监控系统"""
        logger.info("重启监控系统")

        if not self.stop():
            return False

        # 重新加载配置
        self.config = self.config_manager.get_monitoring_config()

        return self.start()

    def get_status(self) -> Dict[str, Any]:
        """获取监控系统状态"""
        status = {
            "is_running": self.is_running,
            "components": {},
            "configuration": {"monitoring": self.config},
            "statistics": {},
        }

        # 日志监控服务状态
        if self.logging_service:
            status["components"]["logging_service"] = {
                "running": self.logging_service.is_running,
                "log_entries_count": len(self.logging_service.log_entries),
                "events_count": len(self.logging_service.monitoring_events),
                "metrics_count": len(self.logging_service.system_metrics_history),
            }

        # 告警管理器状态
        if self.alert_manager:
            alert_stats = self.alert_manager.get_statistics()
            status["components"]["alert_manager"] = {
                "running": getattr(self.alert_manager, "running", False),
                "active_alerts": alert_stats.get("active_alerts", 0),
                "total_alerts": alert_stats.get("total_alerts", 0),
                "rules_count": alert_stats.get("rules_count", 0),
            }

        # 健康检查器状态
        if self.health_checker:
            health_stats = self.health_checker.get_statistics()
            status["components"]["health_checker"] = {
                "running": getattr(self.health_checker, "running", False),
                "overall_health": self.health_checker.get_overall_health_status().value,
                "healthy_components": health_stats.get("healthy_components", 0),
                "warning_components": health_stats.get("warning_components", 0),
                "critical_components": health_stats.get("critical_components", 0),
            }

        # 仪表板状态
        if self.dashboard:
            status["components"]["dashboard"] = {
                "available": True,
                "visible": (
                    self.dashboard.isVisible()
                    if hasattr(self.dashboard, "isVisible")
                    else False
                ),
            }

        return status

    def get_health_summary(self) -> Dict[str, Any]:
        """获取系统健康状态摘要"""
        if self.health_checker:
            return self.health_checker.get_health_summary()
        else:
            return {"overall_status": "unknown", "components": {}, "statistics": {}}

    def get_alert_summary(self) -> Dict[str, Any]:
        """获取告警状态摘要"""
        if self.alert_manager:
            return {
                "statistics": self.alert_manager.get_statistics(),
                "active_alerts": [
                    alert.to_dict() for alert in self.alert_manager.get_active_alerts()
                ],
                "recent_alerts": [
                    alert.to_dict() for alert in self.alert_manager.get_alerts(limit=10)
                ],
            }
        else:
            return {"statistics": {}, "active_alerts": [], "recent_alerts": []}

    def get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        if self.logging_service:
            return self.logging_service.get_dashboard_data()
        else:
            return {"system_metrics": {}, "log_statistics": {}, "event_statistics": {}}

    def export_monitoring_data(
        self, file_path: str, include_config: bool = True
    ) -> bool:
        """导出监控数据"""
        try:
            export_data = {
                "export_timestamp": self._get_current_timestamp(),
                "system_status": self.get_status(),
                "health_summary": self.get_health_summary(),
                "alert_summary": self.get_alert_summary(),
                "performance_metrics": self.get_performance_metrics(),
            }

            if include_config:
                export_data["configuration"] = {"monitoring": self.config}

            import json

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

            logger.info(f"监控数据导出成功: {file_path}")
            return True

        except Exception as e:
            logger.error(f"监控数据导出失败: {e}")
            return False

    def show_dashboard(self):
        """显示监控仪表板"""
        if self.dashboard:
            self.dashboard.show()
            logger.info("监控仪表板已显示")
        else:
            logger.warning("监控仪表板不可用")

    def hide_dashboard(self):
        """隐藏监控仪表板"""
        if self.dashboard:
            self.dashboard.hide()
            logger.info("监控仪表板已隐藏")

    def update_config(
        self, config_type: ConfigType, config_data: Dict[str, Any]
    ) -> bool:
        """更新配置"""
        success = self.config_manager.update_monitoring_config(config_data)
        if success:
            # 重新加载配置
            self.config = self.config_manager.get_monitoring_config()

            # 通知组件配置已更新
            self._notify_config_change(config_type, config_data)

            logger.info(f"配置更新成功: {config_type.value}")

        return success

    def _setup_component_connections(self):
        """设置组件间的连接"""
        # 连接告警管理器和日志服务
        if self.alert_manager and self.logging_service:
            # 设置告警管理器的日志服务引用
            self.alert_manager.logging_service = self.logging_service

        # 连接健康检查器和告警管理器
        if self.health_checker and self.alert_manager:
            # 健康状态变化时触发告警检查
            self.health_checker.health_status_changed.connect(
                lambda component, old_status, new_status: self._handle_health_status_change(
                    component, old_status, new_status
                )
            )

        # 配置变更回调已在统一的ConfigManager中处理

        logger.debug("组件连接设置完成")

    def _handle_health_status_change(
        self, component: str, old_status: str, new_status: str
    ):
        """处理健康状态变化"""
        if self.alert_manager:
            # 根据健康状态变化创建相应的告警
            if new_status == "critical":
                self.alert_manager.create_alert(
                    rule_name=f"health_check_{component}",
                    message=f"组件 {component} 健康状态变为严重",
                    severity=AlertSeverity.CRITICAL,
                    details={
                        "component": component,
                        "old_status": old_status,
                        "new_status": new_status,
                    },
                )
            elif new_status == "warning":
                self.alert_manager.create_alert(
                    rule_name=f"health_check_{component}",
                    message=f"组件 {component} 健康状态变为警告",
                    severity=AlertSeverity.WARNING,
                    details={
                        "component": component,
                        "old_status": old_status,
                        "new_status": new_status,
                    },
                )

    def _notify_config_change(
        self, config_type: ConfigType, config_data: Dict[str, Any]
    ):
        """通知组件配置变更"""
        # 根据配置类型通知相应组件
        if config_type == ConfigType.ALERTING and self.alert_manager:
            # 重新加载告警配置
            pass  # 告警管理器可以实现配置重载方法

        elif config_type == ConfigType.HEALTH_CHECK and self.health_checker:
            # 重新加载健康检查配置
            pass  # 健康检查器可以实现配置重载方法

        elif config_type == ConfigType.MONITORING and self.logging_service:
            # 重新加载监控配置
            pass  # 日志服务可以实现配置重载方法

    def _on_config_changed(self, config_type: ConfigType, config_data: Dict[str, Any]):
        """配置变更回调"""
        logger.info(f"配置已变更: {config_type.value}")

        # 发送配置变更事件
        if self.event_bus:
            self.event_bus.emit(
                "monitoring_config_changed",
                {
                    "config_type": config_type.value,
                    "config_data": config_data,
                    "timestamp": self._get_current_timestamp(),
                },
            )

    def _get_active_components(self) -> list:
        """获取活动组件列表"""
        components = []

        if self.logging_service:
            components.append("logging_service")
        if self.alert_manager:
            components.append("alert_manager")
        if self.health_checker:
            components.append("health_checker")
        if self.dashboard:
            components.append("dashboard")

        return components

    def _get_current_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime

        return datetime.now().isoformat()


# 全局监控系统实例
_monitoring_system_instance: Optional[MonitoringSystem] = None


def get_monitoring_system() -> Optional[MonitoringSystem]:
    """获取全局监控系统实例"""
    return _monitoring_system_instance


def set_monitoring_system(monitoring_system: MonitoringSystem):
    """设置全局监控系统实例"""
    global _monitoring_system_instance
    _monitoring_system_instance = monitoring_system


def initialize_monitoring_system(
    event_bus=None, db_manager=None, config_directory: str = "./config"
) -> MonitoringSystem:
    """初始化监控系统的便捷函数"""
    monitoring_system = MonitoringSystem(
        event_bus=event_bus, db_manager=db_manager, config_directory=config_directory
    )

    if monitoring_system.initialize():
        set_monitoring_system(monitoring_system)
        logger.info("监控系统初始化并设置为全局实例")
        return monitoring_system
    else:
        logger.error("监控系统初始化失败")
        return None


# 导出主要类和函数
__all__ = [
    # 主要类
    "MonitoringSystem",
    # 日志监控
    "LoggingMonitoringService",
    "LogLevel",
    "MonitoringEventType",
    "LogEntry",
    "MonitoringEvent",
    "SystemMetrics",
    # 告警管理
    "AlertManager",
    "AlertSeverity",
    "AlertStatus",
    "AlertChannel",
    "AlertRule",
    "Alert",
    "AlertNotificationConfig",
    # 健康检查
    "HealthChecker",
    "HealthStatus",
    "ComponentType",
    "HealthCheckResult",
    "HealthCheckConfig",
    "BaseHealthCheck",
    "DatabaseHealthCheck",
    "SystemResourceHealthCheck",
    "FileSystemHealthCheck",
    "ProcessHealthCheck",
    "ServiceHealthCheck",
    # 配置管理
    "MonitoringConfigManager",
    "ConfigType",
    "LoggingConfig",
    "MonitoringConfig",
    "AlertingConfig",
    "PerformanceConfig",
    "ConfigHealthCheckConfig",
    "NotificationConfig",
    "DashboardConfig",
    "SystemConfig",
    "MonitoringSystemConfig",
    # UI组件
    "MonitoringDashboard",
    # 全局函数
    "get_monitoring_system",
    "set_monitoring_system",
    "initialize_monitoring_system",
]
