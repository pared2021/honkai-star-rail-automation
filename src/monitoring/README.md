# 监控系统 (Monitoring System)

## 概述

监控系统是星铁助手的核心组件之一，提供全面的系统监控、日志记录、告警管理、健康检查和性能优化功能。该系统采用模块化设计，支持实时监控、自动告警、数据可视化和智能优化。

## 核心功能

### 🔍 实时监控
- **系统指标监控**: CPU、内存、磁盘使用率
- **应用性能监控**: 响应时间、吞吐量、错误率
- **任务执行监控**: 任务状态、执行时间、成功率
- **游戏检测监控**: 游戏状态、窗口检测、自动化操作

### 📊 日志管理
- **多级别日志**: DEBUG、INFO、WARNING、ERROR、CRITICAL
- **结构化日志**: JSON格式，支持字段搜索和过滤
- **日志轮转**: 自动压缩和清理历史日志
- **实时日志流**: 支持实时日志查看和监控

### 🚨 智能告警
- **规则引擎**: 灵活的告警规则配置
- **多通道通知**: 桌面通知、邮件、Webhook、短信
- **告警聚合**: 防止告警风暴，智能分组
- **告警抑制**: 避免重复告警，支持冷却时间

### 🏥 健康检查
- **组件健康**: 数据库、文件系统、进程状态
- **自动恢复**: 检测到问题时自动尝试恢复
- **健康报告**: 生成详细的健康状态报告
- **预防性维护**: 提前发现潜在问题

### 📈 性能优化
- **自动优化**: 根据系统负载自动调整参数
- **缓存管理**: 智能缓存策略和清理
- **资源监控**: 内存泄漏检测和资源优化
- **性能分析**: 生成性能报告和优化建议

### 🎛️ 可视化仪表板
- **实时图表**: CPU、内存、网络等指标的实时图表
- **告警面板**: 活动告警的可视化展示
- **日志查看器**: 实时日志流和历史日志查询
- **事件时间线**: 系统事件的时间线视图

## 架构设计

```
监控系统架构
├── LoggingMonitoringService (日志监控服务)
│   ├── 日志收集和存储
│   ├── 事件记录和管理
│   └── 指标数据收集
├── AlertManager (告警管理器)
│   ├── 告警规则引擎
│   ├── 通知发送器
│   └── 告警生命周期管理
├── HealthChecker (健康检查器)
│   ├── 组件健康检查
│   ├── 自动恢复机制
│   └── 健康报告生成
├── PerformanceMonitor (性能监控器)
│   ├── 系统指标收集
│   ├── 性能分析
│   └── 自动优化
├── MonitoringDashboard (监控仪表板)
│   ├── 实时数据展示
│   ├── 图表和可视化
│   └── 用户交互界面
└── MonitoringConfigManager (配置管理器)
    ├── 配置加载和保存
    ├── 配置验证
    └── 动态配置更新
```

## 快速开始

### 1. 基本使用

```python
from src.monitoring import initialize_monitoring_system, get_monitoring_system
from src.core.event_bus import EventBus
from src.data.database_manager import DatabaseManager

# 初始化依赖组件
event_bus = EventBus()
db_manager = DatabaseManager()

# 初始化监控系统
monitoring_system = initialize_monitoring_system(
    event_bus=event_bus,
    db_manager=db_manager,
    config_directory="./config"
)

# 启动监控系统
if monitoring_system.start():
    print("监控系统启动成功")
else:
    print("监控系统启动失败")

# 获取全局监控系统实例
monitoring = get_monitoring_system()
```

### 2. 日志记录

```python
from src.monitoring import LogLevel

# 记录不同级别的日志
monitoring.logging_service.add_log(
    level=LogLevel.INFO,
    message="任务开始执行",
    source="task_manager",
    details={'task_id': 'task_001', 'task_name': '示例任务'}
)

monitoring.logging_service.add_log(
    level=LogLevel.ERROR,
    message="任务执行失败",
    source="task_manager",
    details={'task_id': 'task_001', 'error': '网络连接超时'}
)
```

### 3. 事件记录

```python
from src.monitoring import MonitoringEventType

# 记录系统事件
monitoring.logging_service.add_event(
    event_type=MonitoringEventType.TASK_STARTED,
    message="任务开始执行",
    source="task_manager",
    details={'task_id': 'task_001'}
)

monitoring.logging_service.add_event(
    event_type=MonitoringEventType.GAME_DETECTED,
    message="检测到游戏窗口",
    source="game_detector",
    details={'game_name': '崩坏：星穹铁道'}
)
```

### 4. 自定义告警规则

```python
from src.monitoring import AlertSeverity, AlertChannel

# 添加CPU使用率告警
monitoring.alert_manager.add_rule(
    name="high_cpu_usage",
    condition="cpu_usage > 80",
    severity=AlertSeverity.WARNING,
    message="CPU使用率过高: {cpu_usage}%",
    channels=[AlertChannel.DESKTOP, AlertChannel.LOG]
)

# 添加任务失败率告警
monitoring.alert_manager.add_rule(
    name="high_task_failure_rate",
    condition="task_failure_rate > 0.1",
    severity=AlertSeverity.CRITICAL,
    message="任务失败率过高: {task_failure_rate:.2%}",
    channels=[AlertChannel.EMAIL, AlertChannel.DESKTOP]
)
```

### 5. 健康检查

```python
from src.monitoring import ComponentType, HealthStatus
from src.monitoring.health_checker import BaseHealthCheck

# 自定义健康检查
class CustomServiceHealthCheck(BaseHealthCheck):
    def __init__(self, service):
        super().__init__(
            name="custom_service",
            component_type=ComponentType.SERVICE,
            check_interval=30
        )
        self.service = service
    
    def _perform_check(self):
        try:
            if self.service.is_running():
                return HealthStatus.HEALTHY, "服务运行正常"
            else:
                return HealthStatus.CRITICAL, "服务未运行"
        except Exception as e:
            return HealthStatus.CRITICAL, f"检查失败: {str(e)}"

# 添加健康检查
monitoring.health_checker.add_check(CustomServiceHealthCheck(my_service))
```

### 6. 性能指标

```python
# 更新性能指标
monitoring.logging_service.add_metrics({
    'response_time': 1.5,
    'request_count': 100,
    'error_count': 2,
    'cache_hit_rate': 0.85
})

# 获取当前性能指标
metrics = monitoring.get_performance_metrics()
print(f"当前CPU使用率: {metrics['system_metrics']['cpu_usage']}%")
print(f"当前内存使用率: {metrics['system_metrics']['memory_usage']}%")
```

### 7. 显示监控仪表板

```python
# 显示监控仪表板
monitoring.show_dashboard()

# 隐藏监控仪表板
monitoring.hide_dashboard()
```

## 配置说明

监控系统支持通过JSON配置文件进行详细配置。配置文件位于 `config/monitoring_config.json`。

### 主要配置项

#### 日志配置
```json
{
  "logging": {
    "level": "INFO",
    "max_file_size": 10485760,
    "max_files": 10,
    "log_directory": "./logs",
    "console_output": true,
    "file_output": true
  }
}
```

#### 告警配置
```json
{
  "alerting": {
    "enabled": true,
    "evaluation_interval": 10,
    "max_alerts": 1000,
    "enable_grouping": true,
    "grouping_window": 300
  }
}
```

#### 性能监控配置
```json
{
  "performance": {
    "enabled": true,
    "monitoring_interval": 5,
    "enable_auto_optimization": true,
    "thresholds": {
      "cpu_warning": 70.0,
      "cpu_critical": 85.0,
      "memory_warning": 75.0,
      "memory_critical": 90.0
    }
  }
}
```

#### 健康检查配置
```json
{
  "health_check": {
    "enabled": true,
    "check_interval": 30,
    "timeout": 10,
    "max_failures": 3,
    "enable_auto_recovery": true
  }
}
```

## API 参考

### MonitoringSystem

主要的监控系统类，提供统一的接口。

#### 方法

- `start() -> bool`: 启动监控系统
- `stop() -> bool`: 停止监控系统
- `restart() -> bool`: 重启监控系统
- `get_status() -> Dict`: 获取系统状态
- `get_health_summary() -> Dict`: 获取健康状态摘要
- `get_alert_summary() -> Dict`: 获取告警摘要
- `get_performance_metrics() -> Dict`: 获取性能指标
- `export_monitoring_data(filename: str) -> bool`: 导出监控数据
- `show_dashboard()`: 显示监控仪表板
- `hide_dashboard()`: 隐藏监控仪表板

### LoggingMonitoringService

日志和监控服务。

#### 方法

- `add_log(level, message, source, details)`: 添加日志
- `add_event(event_type, message, source, details)`: 添加事件
- `add_metrics(metrics)`: 添加指标数据
- `get_logs(start_time, end_time, level, source)`: 获取日志
- `get_events(start_time, end_time, event_type, source)`: 获取事件
- `get_metrics(start_time, end_time, metric_names)`: 获取指标

### AlertManager

告警管理器。

#### 方法

- `add_rule(name, condition, severity, message, channels)`: 添加告警规则
- `remove_rule(name)`: 移除告警规则
- `update_rule(name, **kwargs)`: 更新告警规则
- `get_active_alerts()`: 获取活动告警
- `acknowledge_alert(alert_id, user)`: 确认告警
- `resolve_alert(alert_id, user, resolution)`: 解决告警

### HealthChecker

健康检查器。

#### 方法

- `add_check(health_check)`: 添加健康检查
- `remove_check(name)`: 移除健康检查
- `run_check(name)`: 运行指定检查
- `get_health_status()`: 获取整体健康状态
- `get_check_results(name)`: 获取检查结果
- `get_health_summary()`: 获取健康摘要

## 最佳实践

### 1. 日志记录

- 使用合适的日志级别
- 提供详细的上下文信息
- 避免记录敏感信息
- 使用结构化日志格式

```python
# 好的日志记录示例
monitoring.logging_service.add_log(
    level=LogLevel.INFO,
    message="用户登录成功",
    source="auth_service",
    details={
        'user_id': user.id,
        'username': user.username,
        'ip_address': request.remote_addr,
        'user_agent': request.user_agent.string
    }
)

# 避免记录敏感信息
# 错误示例：不要记录密码、令牌等敏感信息
```

### 2. 告警配置

- 设置合理的阈值
- 避免告警风暴
- 使用告警分组和抑制
- 定期审查告警规则

```python
# 设置合理的告警规则
monitoring.alert_manager.add_rule(
    name="database_connection_failure",
    condition="database_connection_errors > 5",
    severity=AlertSeverity.CRITICAL,
    message="数据库连接失败次数过多",
    channels=[AlertChannel.EMAIL, AlertChannel.DESKTOP],
    cooldown=300  # 5分钟冷却时间
)
```

### 3. 性能监控

- 监控关键性能指标
- 设置合理的性能阈值
- 启用自动优化功能
- 定期分析性能趋势

```python
# 监控关键业务指标
monitoring.logging_service.add_metrics({
    'task_execution_time': execution_time,
    'task_success_rate': success_rate,
    'user_active_count': active_users,
    'api_response_time': response_time
})
```

### 4. 健康检查

- 检查关键组件
- 设置合适的检查间隔
- 实现自动恢复机制
- 监控检查结果趋势

```python
# 实现自定义健康检查
class DatabaseHealthCheck(BaseHealthCheck):
    def _perform_check(self):
        try:
            # 执行数据库连接测试
            result = self.db.execute("SELECT 1")
            if result:
                return HealthStatus.HEALTHY, "数据库连接正常"
            else:
                return HealthStatus.CRITICAL, "数据库查询失败"
        except Exception as e:
            return HealthStatus.CRITICAL, f"数据库连接失败: {str(e)}"
```

## 故障排除

### 常见问题

#### 1. 监控系统启动失败

**问题**: 监控系统无法启动

**解决方案**:
- 检查配置文件是否正确
- 确认依赖组件已正确初始化
- 查看日志文件中的错误信息
- 检查文件权限和目录是否存在

#### 2. 告警不工作

**问题**: 告警规则不触发或通知不发送

**解决方案**:
- 检查告警规则配置是否正确
- 确认指标数据是否正常更新
- 检查通知渠道配置
- 查看告警管理器的日志

#### 3. 性能监控数据不准确

**问题**: 性能指标显示异常或不更新

**解决方案**:
- 检查性能监控器是否正常运行
- 确认系统资源监控权限
- 检查监控间隔配置
- 重启性能监控组件

#### 4. 健康检查失败

**问题**: 健康检查持续失败

**解决方案**:
- 检查被检查组件的实际状态
- 确认健康检查配置正确
- 检查网络连接和权限
- 调整检查超时时间

### 调试模式

启用调试模式可以获得更详细的日志信息：

```python
# 在配置文件中启用调试模式
{
  "system": {
    "debug_mode": true,
    "enable_profiling": true
  }
}
```

### 日志分析

监控系统的日志文件位于 `logs/` 目录下：

- `monitoring.log`: 主要监控日志
- `alerts.log`: 告警相关日志
- `health_check.log`: 健康检查日志
- `performance.log`: 性能监控日志

## 扩展开发

### 自定义监控组件

```python
from src.monitoring.base import BaseMonitoringComponent

class CustomMonitoringComponent(BaseMonitoringComponent):
    def __init__(self, config):
        super().__init__("custom_component", config)
    
    def start(self):
        # 启动逻辑
        pass
    
    def stop(self):
        # 停止逻辑
        pass
    
    def get_status(self):
        # 返回组件状态
        return {'running': self.is_running}
```

### 自定义告警通道

```python
from src.monitoring.alert_manager import BaseNotificationChannel

class CustomNotificationChannel(BaseNotificationChannel):
    def __init__(self, config):
        super().__init__("custom_channel", config)
    
    def send_notification(self, alert, template):
        # 实现自定义通知发送逻辑
        pass
```

### 自定义健康检查

```python
from src.monitoring.health_checker import BaseHealthCheck

class CustomHealthCheck(BaseHealthCheck):
    def __init__(self, name, config):
        super().__init__(name, ComponentType.SERVICE, config.get('interval', 30))
        self.config = config
    
    def _perform_check(self):
        # 实现自定义健康检查逻辑
        try:
            # 执行检查
            if check_passed:
                return HealthStatus.HEALTHY, "检查通过"
            else:
                return HealthStatus.WARNING, "检查警告"
        except Exception as e:
            return HealthStatus.CRITICAL, f"检查失败: {str(e)}"
```

## 版本历史

### v1.0.0 (当前版本)
- 初始版本发布
- 基础监控功能
- 日志记录和事件管理
- 告警系统
- 健康检查
- 性能监控
- 可视化仪表板

## 许可证

本监控系统遵循项目的整体许可证。

## 贡献

欢迎提交问题报告和功能请求。在提交代码之前，请确保：

1. 代码符合项目的编码规范
2. 添加了适当的测试用例
3. 更新了相关文档
4. 通过了所有测试

## 支持

如果您在使用监控系统时遇到问题，请：

1. 查看本文档的故障排除部分
2. 检查项目的 Issues 页面
3. 提交新的 Issue 并提供详细信息

---

*最后更新: 2024年1月*