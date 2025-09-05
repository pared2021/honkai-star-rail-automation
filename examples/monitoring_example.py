# -*- coding: utf-8 -*-
"""
监控系统使用示例

本示例展示如何在实际项目中集成和使用监控系统的各种功能。
"""

from datetime import datetime, timedelta
import os
import sys
import threading
import time

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# 导入其他系统组件（模拟）
from src.core.event_bus import EventBus
from src.data.database_manager import DatabaseManager

# 导入监控系统组件
from src.monitoring import (
    AlertChannel,
    AlertSeverity,
    ComponentType,
    ConfigType,
    HealthStatus,
    LogLevel,
    MonitoringEventType,
    get_monitoring_system,
    initialize_monitoring_system,
)


class MonitoringExampleApp:
    """监控系统示例应用"""

    def __init__(self):
        """初始化示例应用"""
        self.event_bus = EventBus()
        self.db_manager = DatabaseManager()
        self.monitoring_system = None
        self.is_running = False

        # 模拟应用组件
        self.task_processor = TaskProcessor()
        self.game_detector = GameDetector()
        self.automation_controller = AutomationController()

    def setup_monitoring(self):
        """设置监控系统"""
        print("🔧 设置监控系统...")

        # 初始化监控系统
        self.monitoring_system = initialize_monitoring_system(
            event_bus=self.event_bus,
            db_manager=self.db_manager,
            config_directory="./config",
        )

        if not self.monitoring_system:
            print("❌ 监控系统初始化失败")
            return False

        # 启动监控系统
        if not self.monitoring_system.start():
            print("❌ 监控系统启动失败")
            return False

        print("✅ 监控系统启动成功")

        # 配置自定义告警规则
        self._setup_custom_alerts()

        # 配置健康检查
        self._setup_health_checks()

        # 设置事件监听
        self._setup_event_listeners()

        return True

    def _setup_custom_alerts(self):
        """设置自定义告警规则"""
        print("📋 配置告警规则...")

        alert_manager = self.monitoring_system.alert_manager

        # CPU使用率告警
        alert_manager.add_rule(
            name="high_cpu_usage",
            condition="cpu_usage > 80",
            severity=AlertSeverity.WARNING,
            message="CPU使用率过高: {cpu_usage}%",
            channels=[AlertChannel.DESKTOP, AlertChannel.LOG],
        )

        # 内存使用率告警
        alert_manager.add_rule(
            name="high_memory_usage",
            condition="memory_usage > 85",
            severity=AlertSeverity.CRITICAL,
            message="内存使用率过高: {memory_usage}%",
            channels=[AlertChannel.DESKTOP, AlertChannel.LOG, AlertChannel.EMAIL],
        )

        # 任务失败率告警
        alert_manager.add_rule(
            name="high_task_failure_rate",
            condition="task_failure_rate > 0.1",
            severity=AlertSeverity.WARNING,
            message="任务失败率过高: {task_failure_rate:.2%}",
            channels=[AlertChannel.LOG],
        )

        # 错误日志频率告警
        alert_manager.add_rule(
            name="high_error_rate",
            condition="error_count_per_minute > 10",
            severity=AlertSeverity.CRITICAL,
            message="错误日志频率过高: {error_count_per_minute}/分钟",
            channels=[AlertChannel.DESKTOP, AlertChannel.LOG],
        )

        print("✅ 告警规则配置完成")

    def _setup_health_checks(self):
        """设置健康检查"""
        print("🏥 配置健康检查...")

        health_checker = self.monitoring_system.health_checker

        # 添加自定义健康检查
        from src.monitoring.health_checker import BaseHealthCheck

        class TaskProcessorHealthCheck(BaseHealthCheck):
            def __init__(self, task_processor):
                super().__init__(
                    name="task_processor",
                    component_type=ComponentType.SERVICE,
                    check_interval=30,
                )
                self.task_processor = task_processor

            def _perform_check(self):
                try:
                    # 检查任务处理器状态
                    if not self.task_processor.is_running:
                        return HealthStatus.CRITICAL, "任务处理器未运行"

                    # 检查任务队列长度
                    queue_length = self.task_processor.get_queue_length()
                    if queue_length > 100:
                        return HealthStatus.WARNING, f"任务队列过长: {queue_length}"

                    # 检查最近的任务处理时间
                    last_processed = self.task_processor.get_last_processed_time()
                    if (
                        last_processed
                        and (datetime.now() - last_processed).seconds > 300
                    ):
                        return HealthStatus.WARNING, "任务处理器长时间无活动"

                    return HealthStatus.HEALTHY, "任务处理器运行正常"

                except Exception as e:
                    return HealthStatus.CRITICAL, f"健康检查失败: {str(e)}"

        # 添加自定义健康检查
        health_checker.add_check(TaskProcessorHealthCheck(self.task_processor))

        print("✅ 健康检查配置完成")

    def _setup_event_listeners(self):
        """设置事件监听"""
        print("👂 设置事件监听...")

        # 监听任务相关事件
        self.event_bus.subscribe("task_started", self._on_task_started)
        self.event_bus.subscribe("task_completed", self._on_task_completed)
        self.event_bus.subscribe("task_failed", self._on_task_failed)

        # 监听游戏检测事件
        self.event_bus.subscribe("game_detected", self._on_game_detected)
        self.event_bus.subscribe("game_lost", self._on_game_lost)

        # 监听自动化事件
        self.event_bus.subscribe("automation_started", self._on_automation_started)
        self.event_bus.subscribe("automation_stopped", self._on_automation_stopped)
        self.event_bus.subscribe("automation_error", self._on_automation_error)

        # 监听系统事件
        self.event_bus.subscribe("system_error", self._on_system_error)
        self.event_bus.subscribe("performance_warning", self._on_performance_warning)

        print("✅ 事件监听设置完成")

    def _on_task_started(self, event_data):
        """任务开始事件处理"""
        task_id = event_data.get("task_id")
        task_name = event_data.get("task_name", "Unknown")

        # 记录日志
        self.monitoring_system.logging_service.add_log(
            level=LogLevel.INFO,
            message=f"任务开始: {task_name} (ID: {task_id})",
            source="task_manager",
            details={"task_id": task_id, "task_name": task_name},
        )

        # 记录事件
        self.monitoring_system.logging_service.add_event(
            event_type=MonitoringEventType.TASK_STARTED,
            message=f"任务 {task_name} 开始执行",
            source="task_manager",
            details=event_data,
        )

    def _on_task_completed(self, event_data):
        """任务完成事件处理"""
        task_id = event_data.get("task_id")
        task_name = event_data.get("task_name", "Unknown")
        duration = event_data.get("duration", 0)

        # 记录日志
        self.monitoring_system.logging_service.add_log(
            level=LogLevel.INFO,
            message=f"任务完成: {task_name} (耗时: {duration:.2f}秒)",
            source="task_manager",
            details=event_data,
        )

        # 记录事件
        self.monitoring_system.logging_service.add_event(
            event_type=MonitoringEventType.TASK_COMPLETED,
            message=f"任务 {task_name} 执行完成",
            source="task_manager",
            details=event_data,
        )

        # 更新性能指标
        self.monitoring_system.logging_service.add_metrics(
            {"task_completion_time": duration, "completed_tasks_count": 1}
        )

    def _on_task_failed(self, event_data):
        """任务失败事件处理"""
        task_id = event_data.get("task_id")
        task_name = event_data.get("task_name", "Unknown")
        error = event_data.get("error", "Unknown error")

        # 记录错误日志
        self.monitoring_system.logging_service.add_log(
            level=LogLevel.ERROR,
            message=f"任务失败: {task_name} - {error}",
            source="task_manager",
            details=event_data,
        )

        # 记录事件
        self.monitoring_system.logging_service.add_event(
            event_type=MonitoringEventType.TASK_FAILED,
            message=f"任务 {task_name} 执行失败",
            source="task_manager",
            details=event_data,
        )

        # 更新失败计数
        self.monitoring_system.alert_manager.update_metrics({"failed_tasks_count": 1})

    def _on_game_detected(self, event_data):
        """游戏检测事件处理"""
        game_name = event_data.get("game_name", "Unknown")

        self.monitoring_system.logging_service.add_log(
            level=LogLevel.INFO,
            message=f"检测到游戏: {game_name}",
            source="game_detector",
            details=event_data,
        )

        self.monitoring_system.logging_service.add_event(
            event_type=MonitoringEventType.GAME_DETECTED,
            message=f"游戏 {game_name} 已检测到",
            source="game_detector",
            details=event_data,
        )

    def _on_game_lost(self, event_data):
        """游戏丢失事件处理"""
        game_name = event_data.get("game_name", "Unknown")

        self.monitoring_system.logging_service.add_log(
            level=LogLevel.WARNING,
            message=f"游戏丢失: {game_name}",
            source="game_detector",
            details=event_data,
        )

        self.monitoring_system.logging_service.add_event(
            event_type=MonitoringEventType.GAME_LOST,
            message=f"游戏 {game_name} 连接丢失",
            source="game_detector",
            details=event_data,
        )

    def _on_automation_started(self, event_data):
        """自动化开始事件处理"""
        automation_type = event_data.get("type", "Unknown")

        self.monitoring_system.logging_service.add_log(
            level=LogLevel.INFO,
            message=f"自动化开始: {automation_type}",
            source="automation_controller",
            details=event_data,
        )

    def _on_automation_stopped(self, event_data):
        """自动化停止事件处理"""
        automation_type = event_data.get("type", "Unknown")

        self.monitoring_system.logging_service.add_log(
            level=LogLevel.INFO,
            message=f"自动化停止: {automation_type}",
            source="automation_controller",
            details=event_data,
        )

    def _on_automation_error(self, event_data):
        """自动化错误事件处理"""
        automation_type = event_data.get("type", "Unknown")
        error = event_data.get("error", "Unknown error")

        self.monitoring_system.logging_service.add_log(
            level=LogLevel.ERROR,
            message=f"自动化错误: {automation_type} - {error}",
            source="automation_controller",
            details=event_data,
        )

        self.monitoring_system.logging_service.add_event(
            event_type=MonitoringEventType.AUTOMATION_ERROR,
            message=f"自动化 {automation_type} 发生错误",
            source="automation_controller",
            details=event_data,
        )

    def _on_system_error(self, event_data):
        """系统错误事件处理"""
        error_type = event_data.get("type", "Unknown")
        error_message = event_data.get("message", "Unknown error")

        self.monitoring_system.logging_service.add_log(
            level=LogLevel.ERROR,
            message=f"系统错误: {error_type} - {error_message}",
            source="system",
            details=event_data,
        )

        self.monitoring_system.logging_service.add_event(
            event_type=MonitoringEventType.SYSTEM_ERROR,
            message=f"系统发生错误: {error_type}",
            source="system",
            details=event_data,
        )

    def _on_performance_warning(self, event_data):
        """性能警告事件处理"""
        metric = event_data.get("metric", "Unknown")
        value = event_data.get("value", 0)
        threshold = event_data.get("threshold", 0)

        self.monitoring_system.logging_service.add_log(
            level=LogLevel.WARNING,
            message=f"性能警告: {metric} = {value} (阈值: {threshold})",
            source="performance_monitor",
            details=event_data,
        )

        self.monitoring_system.logging_service.add_event(
            event_type=MonitoringEventType.PERFORMANCE_WARNING,
            message=f"性能指标 {metric} 超出阈值",
            source="performance_monitor",
            details=event_data,
        )

    def run_simulation(self):
        """运行模拟场景"""
        print("🎮 开始运行模拟场景...")

        self.is_running = True

        # 启动模拟组件
        self.task_processor.start()
        self.game_detector.start()
        self.automation_controller.start()

        try:
            # 模拟各种场景
            self._simulate_normal_operations()
            self._simulate_high_load()
            self._simulate_error_conditions()
            self._simulate_performance_issues()

        except KeyboardInterrupt:
            print("\n⏹️ 用户中断模拟")

        finally:
            self._cleanup()

    def _simulate_normal_operations(self):
        """模拟正常操作"""
        print("📊 模拟正常操作...")

        for i in range(10):
            # 模拟任务执行
            task_id = f"task_{i}"
            task_name = f"示例任务 {i}"

            # 发送任务开始事件
            self.event_bus.emit(
                "task_started",
                {
                    "task_id": task_id,
                    "task_name": task_name,
                    "timestamp": datetime.now().isoformat(),
                },
            )

            # 模拟任务执行时间
            execution_time = 1 + (i % 3)  # 1-3秒
            time.sleep(execution_time)

            # 发送任务完成事件
            self.event_bus.emit(
                "task_completed",
                {
                    "task_id": task_id,
                    "task_name": task_name,
                    "duration": execution_time,
                    "timestamp": datetime.now().isoformat(),
                },
            )

            # 模拟游戏检测
            if i % 3 == 0:
                self.event_bus.emit(
                    "game_detected",
                    {
                        "game_name": "TestGame",
                        "window_title": "Test Game Window",
                        "timestamp": datetime.now().isoformat(),
                    },
                )

            time.sleep(0.5)

        print("✅ 正常操作模拟完成")

    def _simulate_high_load(self):
        """模拟高负载"""
        print("🔥 模拟高负载场景...")

        # 模拟高CPU和内存使用率
        self.monitoring_system.alert_manager.update_metrics(
            {"cpu_usage": 85.0, "memory_usage": 90.0, "disk_usage": 75.0}
        )

        # 模拟大量并发任务
        def simulate_concurrent_tasks():
            for i in range(20):
                task_id = f"concurrent_task_{i}"
                self.event_bus.emit(
                    "task_started",
                    {
                        "task_id": task_id,
                        "task_name": f"并发任务 {i}",
                        "timestamp": datetime.now().isoformat(),
                    },
                )
                time.sleep(0.1)

        # 启动多个线程模拟并发
        threads = []
        for i in range(3):
            thread = threading.Thread(target=simulate_concurrent_tasks)
            threads.append(thread)
            thread.start()

        # 等待线程完成
        for thread in threads:
            thread.join()

        time.sleep(2)
        print("✅ 高负载模拟完成")

    def _simulate_error_conditions(self):
        """模拟错误条件"""
        print("❌ 模拟错误条件...")

        # 模拟任务失败
        for i in range(5):
            task_id = f"failed_task_{i}"
            task_name = f"失败任务 {i}"

            self.event_bus.emit(
                "task_started",
                {
                    "task_id": task_id,
                    "task_name": task_name,
                    "timestamp": datetime.now().isoformat(),
                },
            )

            time.sleep(0.5)

            self.event_bus.emit(
                "task_failed",
                {
                    "task_id": task_id,
                    "task_name": task_name,
                    "error": f"模拟错误 {i}",
                    "error_type": "simulation_error",
                    "timestamp": datetime.now().isoformat(),
                },
            )

            time.sleep(0.2)

        # 模拟系统错误
        self.event_bus.emit(
            "system_error",
            {
                "type": "database_connection",
                "message": "数据库连接失败",
                "severity": "high",
                "timestamp": datetime.now().isoformat(),
            },
        )

        # 模拟自动化错误
        self.event_bus.emit(
            "automation_error",
            {
                "type": "image_recognition",
                "error": "图像识别失败",
                "timestamp": datetime.now().isoformat(),
            },
        )

        # 模拟游戏丢失
        self.event_bus.emit(
            "game_lost",
            {
                "game_name": "TestGame",
                "reason": "window_closed",
                "timestamp": datetime.now().isoformat(),
            },
        )

        time.sleep(2)
        print("✅ 错误条件模拟完成")

    def _simulate_performance_issues(self):
        """模拟性能问题"""
        print("⚠️ 模拟性能问题...")

        # 模拟性能警告
        self.event_bus.emit(
            "performance_warning",
            {
                "metric": "response_time",
                "value": 5.2,
                "threshold": 3.0,
                "unit": "seconds",
                "timestamp": datetime.now().isoformat(),
            },
        )

        self.event_bus.emit(
            "performance_warning",
            {
                "metric": "memory_usage",
                "value": 88.5,
                "threshold": 85.0,
                "unit": "percent",
                "timestamp": datetime.now().isoformat(),
            },
        )

        # 更新性能指标
        self.monitoring_system.alert_manager.update_metrics(
            {
                "response_time": 5.2,
                "error_count_per_minute": 15,
                "task_failure_rate": 0.15,
            }
        )

        time.sleep(3)
        print("✅ 性能问题模拟完成")

    def _cleanup(self):
        """清理资源"""
        print("🧹 清理资源...")

        self.is_running = False

        # 停止模拟组件
        self.task_processor.stop()
        self.game_detector.stop()
        self.automation_controller.stop()

        # 显示监控摘要
        self._show_monitoring_summary()

        # 导出监控数据
        self._export_monitoring_data()

        # 停止监控系统
        if self.monitoring_system:
            self.monitoring_system.stop()

        print("✅ 清理完成")

    def _show_monitoring_summary(self):
        """显示监控摘要"""
        print("\n📈 监控摘要:")
        print("=" * 50)

        # 系统状态
        status = self.monitoring_system.get_status()
        print(f"系统运行状态: {'✅ 运行中' if status['is_running'] else '❌ 已停止'}")

        # 组件状态
        components = status.get("components", {})
        for component, info in components.items():
            running = info.get("running", False)
            print(f"{component}: {'✅ 运行中' if running else '❌ 已停止'}")

        # 健康状态
        health_summary = self.monitoring_system.get_health_summary()
        overall_health = health_summary.get("overall_status", "unknown")
        print(f"整体健康状态: {overall_health}")

        # 告警摘要
        alert_summary = self.monitoring_system.get_alert_summary()
        active_alerts = alert_summary.get("active_alerts", [])
        print(f"活动告警数量: {len(active_alerts)}")

        if active_alerts:
            print("活动告警:")
            for alert in active_alerts[:5]:  # 显示前5个
                print(f"  - {alert['severity']}: {alert['message']}")

        # 性能指标
        performance = self.monitoring_system.get_performance_metrics()
        system_metrics = performance.get("system_metrics", {})
        if system_metrics:
            print("系统指标:")
            for metric, value in system_metrics.items():
                print(f"  - {metric}: {value}")

        print("=" * 50)

    def _export_monitoring_data(self):
        """导出监控数据"""
        export_file = (
            f"monitoring_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )

        if self.monitoring_system.export_monitoring_data(export_file):
            print(f"📁 监控数据已导出到: {export_file}")
        else:
            print("❌ 监控数据导出失败")


# 模拟应用组件
class TaskProcessor:
    """模拟任务处理器"""

    def __init__(self):
        self.is_running = False
        self.queue_length = 0
        self.last_processed_time = None

    def start(self):
        self.is_running = True
        self.last_processed_time = datetime.now()
        print("📋 任务处理器已启动")

    def stop(self):
        self.is_running = False
        print("📋 任务处理器已停止")

    def get_queue_length(self):
        return self.queue_length

    def get_last_processed_time(self):
        return self.last_processed_time


class GameDetector:
    """模拟游戏检测器"""

    def __init__(self):
        self.is_running = False

    def start(self):
        self.is_running = True
        print("🎮 游戏检测器已启动")

    def stop(self):
        self.is_running = False
        print("🎮 游戏检测器已停止")


class AutomationController:
    """模拟自动化控制器"""

    def __init__(self):
        self.is_running = False

    def start(self):
        self.is_running = True
        print("🤖 自动化控制器已启动")

    def stop(self):
        self.is_running = False
        print("🤖 自动化控制器已停止")


def main():
    """主函数"""
    print("🚀 监控系统示例应用启动")
    print("=" * 50)

    # 创建示例应用
    app = MonitoringExampleApp()

    try:
        # 设置监控系统
        if not app.setup_monitoring():
            print("❌ 监控系统设置失败，退出")
            return

        print("\n🎯 监控系统设置完成，开始模拟...")
        print("按 Ctrl+C 可以随时停止模拟\n")

        # 运行模拟
        app.run_simulation()

    except Exception as e:
        print(f"❌ 应用运行出错: {e}")
        import traceback

        traceback.print_exc()

    finally:
        print("\n👋 示例应用结束")


if __name__ == "__main__":
    main()
