# -*- coding: utf-8 -*-
"""
监控配置管理器 - 管理监控系统的各种配置参数
"""

import json
import os
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum

from src.core.logger import get_logger

logger = get_logger(__name__)


class ConfigScope(Enum):
    """配置范围"""
    GLOBAL = "global"
    USER = "user"
    SESSION = "session"
    TEMPORARY = "temporary"


class ConfigType(Enum):
    """配置类型"""
    LOGGING = "logging"
    MONITORING = "monitoring"
    ALERTING = "alerting"
    PERFORMANCE = "performance"
    HEALTH_CHECK = "health_check"
    NOTIFICATION = "notification"
    DASHBOARD = "dashboard"
    SYSTEM = "system"


@dataclass
class LoggingConfig:
    """日志配置"""
    log_level: str = "INFO"
    log_format: str = "{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}"
    log_rotation: str = "10 MB"
    log_retention: str = "30 days"
    log_compression: bool = True
    console_output: bool = True
    file_output: bool = True
    max_log_files: int = 10
    log_directory: str = "./logs"
    separate_error_log: bool = True
    automation_log_enabled: bool = True
    performance_log_enabled: bool = True
    debug_mode: bool = False


@dataclass
class MonitoringConfig:
    """监控配置"""
    enabled: bool = True
    monitoring_interval_seconds: int = 30
    metrics_retention_hours: int = 24
    max_metrics_history: int = 1000
    auto_cleanup_enabled: bool = True
    cleanup_interval_hours: int = 6
    performance_monitoring_enabled: bool = True
    task_monitoring_enabled: bool = True
    system_monitoring_enabled: bool = True
    real_time_updates: bool = True
    export_enabled: bool = True
    export_format: str = "json"
    export_directory: str = "./exports"


@dataclass
class AlertingConfig:
    """告警配置"""
    enabled: bool = True
    alert_cooldown_minutes: int = 5
    max_alerts_per_hour: int = 20
    email_notifications: bool = False
    desktop_notifications: bool = True
    webhook_notifications: bool = False
    sms_notifications: bool = False
    alert_severity_threshold: str = "WARNING"
    auto_resolve_enabled: bool = True
    auto_resolve_timeout_minutes: int = 30
    escalation_enabled: bool = False
    escalation_timeout_minutes: int = 60
    notification_retry_count: int = 3
    notification_retry_delay_seconds: int = 30


@dataclass
class PerformanceConfig:
    """性能配置"""
    monitoring_enabled: bool = True
    optimization_enabled: bool = True
    auto_optimization: bool = False
    cpu_threshold_warning: float = 80.0
    cpu_threshold_critical: float = 95.0
    memory_threshold_warning: float = 85.0
    memory_threshold_critical: float = 95.0
    disk_threshold_warning: float = 90.0
    disk_threshold_critical: float = 95.0
    response_time_threshold_ms: float = 1000.0
    cache_enabled: bool = True
    cache_size_mb: int = 100
    image_optimization_enabled: bool = True
    template_caching_enabled: bool = True
    performance_profiling: bool = False


@dataclass
class HealthCheckConfig:
    """健康检查配置"""
    enabled: bool = True
    check_interval_seconds: int = 60
    timeout_seconds: int = 30
    retry_count: int = 3
    retry_delay_seconds: int = 5
    database_check_enabled: bool = True
    filesystem_check_enabled: bool = True
    system_resource_check_enabled: bool = True
    process_check_enabled: bool = False
    service_check_enabled: bool = False
    network_check_enabled: bool = False
    custom_checks_enabled: bool = True
    parallel_execution: bool = True
    max_concurrent_checks: int = 5
    history_retention_days: int = 7


@dataclass
class NotificationConfig:
    """通知配置"""
    enabled: bool = True
    email_enabled: bool = False
    email_smtp_server: str = ""
    email_smtp_port: int = 587
    email_username: str = ""
    email_password: str = ""
    email_from: str = ""
    email_to: List[str] = field(default_factory=list)
    desktop_enabled: bool = True
    desktop_duration_seconds: int = 5
    webhook_enabled: bool = False
    webhook_url: str = ""
    webhook_timeout_seconds: int = 10
    sms_enabled: bool = False
    sms_api_key: str = ""
    sms_phone_numbers: List[str] = field(default_factory=list)
    notification_queue_size: int = 100
    batch_notifications: bool = False
    batch_size: int = 10
    batch_timeout_seconds: int = 60


@dataclass
class DashboardConfig:
    """仪表板配置"""
    enabled: bool = True
    auto_refresh_enabled: bool = True
    refresh_interval_seconds: int = 30
    max_chart_points: int = 100
    chart_animation_enabled: bool = True
    theme: str = "light"  # light, dark, auto
    show_grid: bool = True
    show_legend: bool = True
    compact_mode: bool = False
    custom_widgets_enabled: bool = True
    export_charts_enabled: bool = True
    real_time_charts: bool = True
    historical_data_enabled: bool = True
    alert_overlay_enabled: bool = True


@dataclass
class SystemConfig:
    """系统配置"""
    debug_mode: bool = False
    development_mode: bool = False
    max_threads: int = 10
    thread_pool_size: int = 5
    memory_limit_mb: int = 512
    temp_directory: str = "./temp"
    backup_enabled: bool = True
    backup_interval_hours: int = 24
    backup_retention_days: int = 7
    auto_update_enabled: bool = False
    telemetry_enabled: bool = False
    crash_reporting_enabled: bool = True
    performance_profiling_enabled: bool = False
    resource_monitoring_enabled: bool = True


@dataclass
class MonitoringSystemConfig:
    """监控系统完整配置"""
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    alerting: AlertingConfig = field(default_factory=AlertingConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    health_check: HealthCheckConfig = field(default_factory=HealthCheckConfig)
    notification: NotificationConfig = field(default_factory=NotificationConfig)
    dashboard: DashboardConfig = field(default_factory=DashboardConfig)
    system: SystemConfig = field(default_factory=SystemConfig)
    version: str = "1.0.0"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())


class MonitoringConfigManager:
    """监控配置管理器"""
    
    def __init__(self, config_directory: str = "./config"):
        self.config_directory = Path(config_directory)
        self.config_directory.mkdir(parents=True, exist_ok=True)
        
        # 配置文件路径
        self.global_config_file = self.config_directory / "monitoring_config.json"
        self.user_config_file = self.config_directory / "user_monitoring_config.json"
        self.session_config_file = self.config_directory / "session_monitoring_config.json"
        
        # 当前配置
        self.current_config: MonitoringSystemConfig = MonitoringSystemConfig()
        
        # 配置变更回调
        self.config_change_callbacks: List[callable] = []
        
        # 加载配置
        self._load_configurations()
        
        logger.info(f"监控配置管理器初始化完成，配置目录: {self.config_directory}")
    
    def load_config(self, scope: ConfigScope = ConfigScope.GLOBAL) -> MonitoringSystemConfig:
        """加载指定范围的配置"""
        config_file = self._get_config_file(scope)
        
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                # 创建配置对象
                config = self._dict_to_config(config_data)
                logger.info(f"加载配置成功: {scope.value}")
                return config
                
            except Exception as e:
                logger.error(f"加载配置失败 {scope.value}: {e}")
                return MonitoringSystemConfig()
        else:
            logger.info(f"配置文件不存在: {config_file}，使用默认配置")
            return MonitoringSystemConfig()
    
    def save_config(self, config: MonitoringSystemConfig = None, 
                   scope: ConfigScope = ConfigScope.GLOBAL) -> bool:
        """保存配置到指定范围"""
        if config is None:
            config = self.current_config
        
        config_file = self._get_config_file(scope)
        
        try:
            # 更新时间戳
            config.updated_at = datetime.now().isoformat()
            
            # 转换为字典
            config_data = self._config_to_dict(config)
            
            # 保存到文件
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"保存配置成功: {scope.value}")
            return True
            
        except Exception as e:
            logger.error(f"保存配置失败 {scope.value}: {e}")
            return False
    
    def get_config(self, config_type: ConfigType = None) -> Union[MonitoringSystemConfig, Any]:
        """获取配置"""
        if config_type is None:
            return self.current_config
        
        config_map = {
            ConfigType.LOGGING: self.current_config.logging,
            ConfigType.MONITORING: self.current_config.monitoring,
            ConfigType.ALERTING: self.current_config.alerting,
            ConfigType.PERFORMANCE: self.current_config.performance,
            ConfigType.HEALTH_CHECK: self.current_config.health_check,
            ConfigType.NOTIFICATION: self.current_config.notification,
            ConfigType.DASHBOARD: self.current_config.dashboard,
            ConfigType.SYSTEM: self.current_config.system
        }
        
        return config_map.get(config_type, self.current_config)
    
    def update_config(self, config_type: ConfigType, config_data: Dict[str, Any]) -> bool:
        """更新指定类型的配置"""
        try:
            config_map = {
                ConfigType.LOGGING: self.current_config.logging,
                ConfigType.MONITORING: self.current_config.monitoring,
                ConfigType.ALERTING: self.current_config.alerting,
                ConfigType.PERFORMANCE: self.current_config.performance,
                ConfigType.HEALTH_CHECK: self.current_config.health_check,
                ConfigType.NOTIFICATION: self.current_config.notification,
                ConfigType.DASHBOARD: self.current_config.dashboard,
                ConfigType.SYSTEM: self.current_config.system
            }
            
            target_config = config_map.get(config_type)
            if target_config is None:
                logger.error(f"未知的配置类型: {config_type}")
                return False
            
            # 更新配置字段
            for key, value in config_data.items():
                if hasattr(target_config, key):
                    setattr(target_config, key, value)
                else:
                    logger.warning(f"配置字段不存在: {config_type.value}.{key}")
            
            # 更新时间戳
            self.current_config.updated_at = datetime.now().isoformat()
            
            # 触发配置变更回调
            self._trigger_config_change_callbacks(config_type, config_data)
            
            logger.info(f"更新配置成功: {config_type.value}")
            return True
            
        except Exception as e:
            logger.error(f"更新配置失败 {config_type.value}: {e}")
            return False
    
    def reset_config(self, config_type: ConfigType = None) -> bool:
        """重置配置为默认值"""
        try:
            if config_type is None:
                # 重置所有配置
                self.current_config = MonitoringSystemConfig()
                logger.info("重置所有配置为默认值")
            else:
                # 重置指定类型配置
                default_configs = {
                    ConfigType.LOGGING: LoggingConfig(),
                    ConfigType.MONITORING: MonitoringConfig(),
                    ConfigType.ALERTING: AlertingConfig(),
                    ConfigType.PERFORMANCE: PerformanceConfig(),
                    ConfigType.HEALTH_CHECK: HealthCheckConfig(),
                    ConfigType.NOTIFICATION: NotificationConfig(),
                    ConfigType.DASHBOARD: DashboardConfig(),
                    ConfigType.SYSTEM: SystemConfig()
                }
                
                default_config = default_configs.get(config_type)
                if default_config is None:
                    logger.error(f"未知的配置类型: {config_type}")
                    return False
                
                setattr(self.current_config, config_type.value, default_config)
                logger.info(f"重置配置为默认值: {config_type.value}")
            
            # 更新时间戳
            self.current_config.updated_at = datetime.now().isoformat()
            
            # 触发配置变更回调
            self._trigger_config_change_callbacks(config_type, {})
            
            return True
            
        except Exception as e:
            logger.error(f"重置配置失败: {e}")
            return False
    
    def validate_config(self, config: MonitoringSystemConfig = None) -> Dict[str, List[str]]:
        """验证配置有效性"""
        if config is None:
            config = self.current_config
        
        validation_errors = {}
        
        # 验证日志配置
        logging_errors = []
        if config.logging.log_level not in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
            logging_errors.append("无效的日志级别")
        if config.logging.max_log_files <= 0:
            logging_errors.append("最大日志文件数必须大于0")
        if logging_errors:
            validation_errors['logging'] = logging_errors
        
        # 验证监控配置
        monitoring_errors = []
        if config.monitoring.monitoring_interval_seconds <= 0:
            monitoring_errors.append("监控间隔必须大于0")
        if config.monitoring.max_metrics_history <= 0:
            monitoring_errors.append("指标历史记录数必须大于0")
        if monitoring_errors:
            validation_errors['monitoring'] = monitoring_errors
        
        # 验证告警配置
        alerting_errors = []
        if config.alerting.alert_cooldown_minutes < 0:
            alerting_errors.append("告警冷却时间不能为负数")
        if config.alerting.max_alerts_per_hour <= 0:
            alerting_errors.append("每小时最大告警数必须大于0")
        if alerting_errors:
            validation_errors['alerting'] = alerting_errors
        
        # 验证性能配置
        performance_errors = []
        if not (0 <= config.performance.cpu_threshold_warning <= 100):
            performance_errors.append("CPU警告阈值必须在0-100之间")
        if not (0 <= config.performance.memory_threshold_warning <= 100):
            performance_errors.append("内存警告阈值必须在0-100之间")
        if config.performance.cache_size_mb <= 0:
            performance_errors.append("缓存大小必须大于0")
        if performance_errors:
            validation_errors['performance'] = performance_errors
        
        # 验证健康检查配置
        health_check_errors = []
        if config.health_check.check_interval_seconds <= 0:
            health_check_errors.append("健康检查间隔必须大于0")
        if config.health_check.timeout_seconds <= 0:
            health_check_errors.append("健康检查超时时间必须大于0")
        if config.health_check.retry_count < 0:
            health_check_errors.append("重试次数不能为负数")
        if health_check_errors:
            validation_errors['health_check'] = health_check_errors
        
        # 验证通知配置
        notification_errors = []
        if config.notification.email_enabled and not config.notification.email_smtp_server:
            notification_errors.append("启用邮件通知时必须配置SMTP服务器")
        if config.notification.webhook_enabled and not config.notification.webhook_url:
            notification_errors.append("启用Webhook通知时必须配置URL")
        if notification_errors:
            validation_errors['notification'] = notification_errors
        
        # 验证仪表板配置
        dashboard_errors = []
        if config.dashboard.refresh_interval_seconds <= 0:
            dashboard_errors.append("刷新间隔必须大于0")
        if config.dashboard.max_chart_points <= 0:
            dashboard_errors.append("图表最大点数必须大于0")
        if dashboard_errors:
            validation_errors['dashboard'] = dashboard_errors
        
        # 验证系统配置
        system_errors = []
        if config.system.max_threads <= 0:
            system_errors.append("最大线程数必须大于0")
        if config.system.memory_limit_mb <= 0:
            system_errors.append("内存限制必须大于0")
        if system_errors:
            validation_errors['system'] = system_errors
        
        return validation_errors
    
    def export_config(self, file_path: str, config_types: List[ConfigType] = None) -> bool:
        """导出配置到文件"""
        try:
            export_data = {}
            
            if config_types is None:
                # 导出所有配置
                export_data = self._config_to_dict(self.current_config)
            else:
                # 导出指定类型配置
                for config_type in config_types:
                    config_obj = self.get_config(config_type)
                    if config_obj:
                        export_data[config_type.value] = asdict(config_obj)
            
            # 添加元数据
            export_data['_metadata'] = {
                'export_time': datetime.now().isoformat(),
                'version': self.current_config.version,
                'exported_types': [ct.value for ct in config_types] if config_types else 'all'
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"导出配置成功: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"导出配置失败: {e}")
            return False
    
    def import_config(self, file_path: str, merge: bool = True) -> bool:
        """从文件导入配置"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            # 移除元数据
            if '_metadata' in import_data:
                metadata = import_data.pop('_metadata')
                logger.info(f"导入配置元数据: {metadata}")
            
            if merge:
                # 合并配置
                for config_type_str, config_data in import_data.items():
                    try:
                        config_type = ConfigType(config_type_str)
                        self.update_config(config_type, config_data)
                    except ValueError:
                        logger.warning(f"跳过未知配置类型: {config_type_str}")
            else:
                # 替换配置
                imported_config = self._dict_to_config(import_data)
                self.current_config = imported_config
            
            logger.info(f"导入配置成功: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"导入配置失败: {e}")
            return False
    
    def add_config_change_callback(self, callback: callable):
        """添加配置变更回调"""
        if callback not in self.config_change_callbacks:
            self.config_change_callbacks.append(callback)
    
    def remove_config_change_callback(self, callback: callable):
        """移除配置变更回调"""
        if callback in self.config_change_callbacks:
            self.config_change_callbacks.remove(callback)
    
    def get_config_summary(self) -> Dict[str, Any]:
        """获取配置摘要"""
        return {
            'version': self.current_config.version,
            'created_at': self.current_config.created_at,
            'updated_at': self.current_config.updated_at,
            'logging_enabled': self.current_config.logging.file_output,
            'monitoring_enabled': self.current_config.monitoring.enabled,
            'alerting_enabled': self.current_config.alerting.enabled,
            'performance_monitoring': self.current_config.performance.monitoring_enabled,
            'health_checks_enabled': self.current_config.health_check.enabled,
            'notifications_enabled': self.current_config.notification.enabled,
            'dashboard_enabled': self.current_config.dashboard.enabled,
            'debug_mode': self.current_config.system.debug_mode
        }
    
    def _load_configurations(self):
        """加载所有配置"""
        # 加载全局配置
        global_config = self.load_config(ConfigScope.GLOBAL)
        
        # 加载用户配置并合并
        user_config = self.load_config(ConfigScope.USER)
        merged_config = self._merge_configs(global_config, user_config)
        
        # 加载会话配置并合并
        session_config = self.load_config(ConfigScope.SESSION)
        final_config = self._merge_configs(merged_config, session_config)
        
        self.current_config = final_config
        
        # 验证配置
        validation_errors = self.validate_config()
        if validation_errors:
            logger.warning(f"配置验证发现问题: {validation_errors}")
    
    def _merge_configs(self, base_config: MonitoringSystemConfig, 
                      override_config: MonitoringSystemConfig) -> MonitoringSystemConfig:
        """合并配置"""
        # 将配置转换为字典进行合并
        base_dict = self._config_to_dict(base_config)
        override_dict = self._config_to_dict(override_config)
        
        # 深度合并字典
        merged_dict = self._deep_merge_dict(base_dict, override_dict)
        
        # 转换回配置对象
        return self._dict_to_config(merged_dict)
    
    def _deep_merge_dict(self, base: Dict, override: Dict) -> Dict:
        """深度合并字典"""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge_dict(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _config_to_dict(self, config: MonitoringSystemConfig) -> Dict[str, Any]:
        """配置对象转字典"""
        return asdict(config)
    
    def _dict_to_config(self, config_dict: Dict[str, Any]) -> MonitoringSystemConfig:
        """字典转配置对象"""
        try:
            # 创建各个子配置对象
            logging_config = LoggingConfig(**config_dict.get('logging', {}))
            monitoring_config = MonitoringConfig(**config_dict.get('monitoring', {}))
            alerting_config = AlertingConfig(**config_dict.get('alerting', {}))
            performance_config = PerformanceConfig(**config_dict.get('performance', {}))
            health_check_config = HealthCheckConfig(**config_dict.get('health_check', {}))
            notification_config = NotificationConfig(**config_dict.get('notification', {}))
            dashboard_config = DashboardConfig(**config_dict.get('dashboard', {}))
            system_config = SystemConfig(**config_dict.get('system', {}))
            
            # 创建主配置对象
            return MonitoringSystemConfig(
                logging=logging_config,
                monitoring=monitoring_config,
                alerting=alerting_config,
                performance=performance_config,
                health_check=health_check_config,
                notification=notification_config,
                dashboard=dashboard_config,
                system=system_config,
                version=config_dict.get('version', '1.0.0'),
                created_at=config_dict.get('created_at', datetime.now().isoformat()),
                updated_at=config_dict.get('updated_at', datetime.now().isoformat())
            )
            
        except Exception as e:
            logger.error(f"字典转配置对象失败: {e}")
            return MonitoringSystemConfig()
    
    def _get_config_file(self, scope: ConfigScope) -> Path:
        """获取配置文件路径"""
        file_map = {
            ConfigScope.GLOBAL: self.global_config_file,
            ConfigScope.USER: self.user_config_file,
            ConfigScope.SESSION: self.session_config_file,
            ConfigScope.TEMPORARY: self.config_directory / "temp_monitoring_config.json"
        }
        return file_map.get(scope, self.global_config_file)
    
    def _trigger_config_change_callbacks(self, config_type: ConfigType, config_data: Dict[str, Any]):
        """触发配置变更回调"""
        for callback in self.config_change_callbacks:
            try:
                callback(config_type, config_data)
            except Exception as e:
                logger.error(f"配置变更回调执行失败: {e}")


# 全局配置管理器实例
_config_manager_instance: Optional[MonitoringConfigManager] = None


def get_config_manager() -> Optional[MonitoringConfigManager]:
    """获取全局配置管理器实例"""
    return _config_manager_instance


def set_config_manager(config_manager: MonitoringConfigManager):
    """设置全局配置管理器实例"""
    global _config_manager_instance
    _config_manager_instance = config_manager


def get_monitoring_config(config_type: ConfigType = None) -> Union[MonitoringSystemConfig, Any]:
    """获取监控配置的便捷函数"""
    config_manager = get_config_manager()
    if config_manager:
        return config_manager.get_config(config_type)
    else:
        # 返回默认配置
        if config_type is None:
            return MonitoringSystemConfig()
        
        default_configs = {
            ConfigType.LOGGING: LoggingConfig(),
            ConfigType.MONITORING: MonitoringConfig(),
            ConfigType.ALERTING: AlertingConfig(),
            ConfigType.PERFORMANCE: PerformanceConfig(),
            ConfigType.HEALTH_CHECK: HealthCheckConfig(),
            ConfigType.NOTIFICATION: NotificationConfig(),
            ConfigType.DASHBOARD: DashboardConfig(),
            ConfigType.SYSTEM: SystemConfig()
        }
        
        return default_configs.get(config_type, MonitoringSystemConfig())