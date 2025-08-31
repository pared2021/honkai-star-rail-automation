# -*- coding: utf-8 -*-
"""
性能监控和优化系统 - 监控CPU、内存使用，优化图像识别速度
"""

import time
import threading
import psutil
import gc
from typing import Dict, List, Optional, Callable, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
import json
import cv2
import numpy as np

from loguru import logger


class PerformanceLevel(Enum):
    """性能等级"""
    EXCELLENT = "excellent"  # 优秀
    GOOD = "good"           # 良好
    FAIR = "fair"           # 一般
    POOR = "poor"           # 较差
    CRITICAL = "critical"   # 严重


class OptimizationStrategy(Enum):
    """优化策略"""
    REDUCE_IMAGE_SIZE = "reduce_image_size"
    LOWER_DETECTION_FREQUENCY = "lower_detection_frequency"
    ENABLE_CACHING = "enable_caching"
    REDUCE_TEMPLATE_COUNT = "reduce_template_count"
    OPTIMIZE_MEMORY = "optimize_memory"
    ADJUST_THREAD_COUNT = "adjust_thread_count"
    DISABLE_NON_ESSENTIAL = "disable_non_essential"


@dataclass
class PerformanceMetrics:
    """性能指标"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    gpu_percent: Optional[float] = None
    gpu_memory_used_mb: Optional[float] = None
    fps: Optional[float] = None
    response_time_ms: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp.isoformat(),
            'cpu_percent': self.cpu_percent,
            'memory_percent': self.memory_percent,
            'memory_used_mb': self.memory_used_mb,
            'memory_available_mb': self.memory_available_mb,
            'gpu_percent': self.gpu_percent,
            'gpu_memory_used_mb': self.gpu_memory_used_mb,
            'fps': self.fps,
            'response_time_ms': self.response_time_ms
        }


@dataclass
class ImageProcessingMetrics:
    """图像处理性能指标"""
    template_match_time: float = 0.0
    image_resize_time: float = 0.0
    screenshot_time: float = 0.0
    total_processing_time: float = 0.0
    templates_processed: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    
    def get_cache_hit_rate(self) -> float:
        total = self.cache_hits + self.cache_misses
        return self.cache_hits / total if total > 0 else 0.0


@dataclass
class PerformanceThresholds:
    """性能阈值配置"""
    cpu_warning: float = 70.0
    cpu_critical: float = 85.0
    memory_warning: float = 75.0
    memory_critical: float = 90.0
    response_time_warning: float = 1000.0  # ms
    response_time_critical: float = 3000.0  # ms
    fps_warning: float = 10.0
    fps_critical: float = 5.0


class ImageCache:
    """图像缓存系统"""
    
    def __init__(self, max_size: int = 100):
        self.cache: Dict[str, Tuple[np.ndarray, float]] = {}
        self.max_size = max_size
        self.access_times: Dict[str, float] = {}
        self.hits = 0
        self.misses = 0
    
    def get(self, key: str) -> Optional[np.ndarray]:
        """获取缓存的图像"""
        if key in self.cache:
            self.hits += 1
            self.access_times[key] = time.time()
            return self.cache[key][0]
        else:
            self.misses += 1
            return None
    
    def put(self, key: str, image: np.ndarray):
        """存储图像到缓存"""
        current_time = time.time()
        
        # 如果缓存已满，移除最久未访问的项
        if len(self.cache) >= self.max_size:
            oldest_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
            del self.cache[oldest_key]
            del self.access_times[oldest_key]
        
        self.cache[key] = (image.copy(), current_time)
        self.access_times[key] = current_time
    
    def clear(self):
        """清空缓存"""
        self.cache.clear()
        self.access_times.clear()
        self.hits = 0
        self.misses = 0
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        total = self.hits + self.misses
        hit_rate = self.hits / total if total > 0 else 0.0
        
        return {
            'size': len(self.cache),
            'max_size': self.max_size,
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': hit_rate
        }


class PerformanceOptimizer:
    """性能优化器"""
    
    def __init__(self):
        self.image_cache = ImageCache()
        self.optimization_enabled = True
        self.current_image_scale = 1.0
        self.detection_interval = 0.1  # 秒
        self.max_templates_per_detection = 10
        
    def optimize_image_processing(self, image: np.ndarray, 
                                 performance_level: PerformanceLevel) -> np.ndarray:
        """根据性能等级优化图像处理"""
        if not self.optimization_enabled:
            return image
        
        # 根据性能等级调整图像大小
        if performance_level in [PerformanceLevel.POOR, PerformanceLevel.CRITICAL]:
            scale = 0.5 if performance_level == PerformanceLevel.CRITICAL else 0.7
            if scale != self.current_image_scale:
                self.current_image_scale = scale
                height, width = image.shape[:2]
                new_height, new_width = int(height * scale), int(width * scale)
                image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_LINEAR)
                logger.info(f"图像缩放至 {scale:.1f}x 以提升性能")
        
        return image
    
    def should_skip_detection(self, performance_level: PerformanceLevel) -> bool:
        """根据性能等级决定是否跳过检测"""
        if performance_level == PerformanceLevel.CRITICAL:
            # 严重性能问题时，降低检测频率
            return time.time() % (self.detection_interval * 3) != 0
        elif performance_level == PerformanceLevel.POOR:
            # 性能较差时，适当降低检测频率
            return time.time() % (self.detection_interval * 2) != 0
        
        return False
    
    def optimize_template_matching(self, templates: List[str], 
                                  performance_level: PerformanceLevel) -> List[str]:
        """优化模板匹配"""
        if performance_level in [PerformanceLevel.POOR, PerformanceLevel.CRITICAL]:
            # 限制同时处理的模板数量
            max_templates = self.max_templates_per_detection // 2 if performance_level == PerformanceLevel.CRITICAL else self.max_templates_per_detection
            return templates[:max_templates]
        
        return templates
    
    def cleanup_memory(self):
        """清理内存"""
        self.image_cache.clear()
        gc.collect()
        logger.info("执行内存清理")


class PerformanceMonitor:
    """性能监控系统"""
    
    def __init__(self, monitoring_interval: float = 1.0, history_size: int = 300):
        self.monitoring_interval = monitoring_interval
        self.history_size = history_size
        
        # 性能数据
        self.metrics_history: deque = deque(maxlen=history_size)
        self.image_metrics = ImageProcessingMetrics()
        
        # 配置
        self.thresholds = PerformanceThresholds()
        self.optimizer = PerformanceOptimizer()
        
        # 监控状态
        self.monitoring_active = False
        self.monitor_thread: Optional[threading.Thread] = None
        
        # 回调函数
        self.performance_warning_callback: Optional[Callable] = None
        self.performance_critical_callback: Optional[Callable] = None
        self.optimization_applied_callback: Optional[Callable] = None
        
        # 进程信息
        self.process = psutil.Process()
        
        logger.info("性能监控系统初始化完成")
    
    def start_monitoring(self):
        """开始性能监控"""
        if self.monitoring_active:
            logger.warning("性能监控已在运行")
            return
        
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("性能监控已启动")
    
    def stop_monitoring(self):
        """停止性能监控"""
        self.monitoring_active = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5)
        logger.info("性能监控已停止")
    
    def _monitoring_loop(self):
        """监控循环"""
        while self.monitoring_active:
            try:
                metrics = self._collect_metrics()
                self.metrics_history.append(metrics)
                
                # 分析性能等级
                performance_level = self._analyze_performance(metrics)
                
                # 触发回调
                if performance_level == PerformanceLevel.CRITICAL:
                    if self.performance_critical_callback:
                        self.performance_critical_callback(metrics, performance_level)
                elif performance_level in [PerformanceLevel.POOR, PerformanceLevel.FAIR]:
                    if self.performance_warning_callback:
                        self.performance_warning_callback(metrics, performance_level)
                
                # 自动优化
                self._apply_auto_optimization(performance_level)
                
                time.sleep(self.monitoring_interval)
                
            except Exception as e:
                logger.error(f"性能监控循环出错: {e}")
                time.sleep(self.monitoring_interval)
    
    def _collect_metrics(self) -> PerformanceMetrics:
        """收集性能指标"""
        # CPU和内存使用率
        cpu_percent = self.process.cpu_percent()
        memory_info = self.process.memory_info()
        memory_percent = self.process.memory_percent()
        
        # 系统内存信息
        system_memory = psutil.virtual_memory()
        memory_used_mb = memory_info.rss / 1024 / 1024
        memory_available_mb = system_memory.available / 1024 / 1024
        
        # GPU信息（如果可用）
        gpu_percent = None
        gpu_memory_used_mb = None
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            if gpus:
                gpu = gpus[0]
                gpu_percent = gpu.load * 100
                gpu_memory_used_mb = gpu.memoryUsed
        except ImportError:
            pass
        
        return PerformanceMetrics(
            timestamp=datetime.now(),
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            memory_used_mb=memory_used_mb,
            memory_available_mb=memory_available_mb,
            gpu_percent=gpu_percent,
            gpu_memory_used_mb=gpu_memory_used_mb
        )
    
    def _analyze_performance(self, metrics: PerformanceMetrics) -> PerformanceLevel:
        """分析性能等级"""
        # 检查关键指标
        critical_conditions = [
            metrics.cpu_percent > self.thresholds.cpu_critical,
            metrics.memory_percent > self.thresholds.memory_critical
        ]
        
        warning_conditions = [
            metrics.cpu_percent > self.thresholds.cpu_warning,
            metrics.memory_percent > self.thresholds.memory_warning
        ]
        
        if any(critical_conditions):
            return PerformanceLevel.CRITICAL
        elif any(warning_conditions):
            return PerformanceLevel.POOR
        elif metrics.cpu_percent > 50 or metrics.memory_percent > 50:
            return PerformanceLevel.FAIR
        elif metrics.cpu_percent > 30 or metrics.memory_percent > 30:
            return PerformanceLevel.GOOD
        else:
            return PerformanceLevel.EXCELLENT
    
    def _apply_auto_optimization(self, performance_level: PerformanceLevel):
        """应用自动优化"""
        if performance_level in [PerformanceLevel.POOR, PerformanceLevel.CRITICAL]:
            strategies_applied = []
            
            # 内存优化
            if performance_level == PerformanceLevel.CRITICAL:
                self.optimizer.cleanup_memory()
                strategies_applied.append(OptimizationStrategy.OPTIMIZE_MEMORY)
            
            # 图像处理优化
            if performance_level in [PerformanceLevel.POOR, PerformanceLevel.CRITICAL]:
                # 这些优化会在实际图像处理时应用
                strategies_applied.extend([
                    OptimizationStrategy.REDUCE_IMAGE_SIZE,
                    OptimizationStrategy.LOWER_DETECTION_FREQUENCY
                ])
            
            if strategies_applied and self.optimization_applied_callback:
                self.optimization_applied_callback(strategies_applied, performance_level)
    
    def record_image_processing_time(self, operation: str, duration: float):
        """记录图像处理时间"""
        if operation == "template_match":
            self.image_metrics.template_match_time += duration
        elif operation == "image_resize":
            self.image_metrics.image_resize_time += duration
        elif operation == "screenshot":
            self.image_metrics.screenshot_time += duration
        
        self.image_metrics.total_processing_time += duration
    
    def record_template_processing(self, count: int):
        """记录模板处理数量"""
        self.image_metrics.templates_processed += count
    
    def record_cache_hit(self):
        """记录缓存命中"""
        self.image_metrics.cache_hits += 1
    
    def record_cache_miss(self):
        """记录缓存未命中"""
        self.image_metrics.cache_misses += 1
    
    def get_current_metrics(self) -> Optional[PerformanceMetrics]:
        """获取当前性能指标"""
        if self.metrics_history:
            return self.metrics_history[-1]
        return None
    
    def get_performance_summary(self, minutes: int = 5) -> Dict[str, Any]:
        """获取性能摘要"""
        if not self.metrics_history:
            return {}
        
        # 获取指定时间范围内的数据
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        recent_metrics = [m for m in self.metrics_history if m.timestamp >= cutoff_time]
        
        if not recent_metrics:
            recent_metrics = list(self.metrics_history)[-10:]  # 至少取最近10个数据点
        
        # 计算统计信息
        cpu_values = [m.cpu_percent for m in recent_metrics]
        memory_values = [m.memory_percent for m in recent_metrics]
        
        summary = {
            "time_range_minutes": minutes,
            "data_points": len(recent_metrics),
            "cpu": {
                "current": cpu_values[-1] if cpu_values else 0,
                "average": sum(cpu_values) / len(cpu_values) if cpu_values else 0,
                "max": max(cpu_values) if cpu_values else 0,
                "min": min(cpu_values) if cpu_values else 0
            },
            "memory": {
                "current": memory_values[-1] if memory_values else 0,
                "average": sum(memory_values) / len(memory_values) if memory_values else 0,
                "max": max(memory_values) if memory_values else 0,
                "min": min(memory_values) if memory_values else 0
            },
            "image_processing": {
                "total_time": self.image_metrics.total_processing_time,
                "templates_processed": self.image_metrics.templates_processed,
                "cache_hit_rate": self.image_metrics.get_cache_hit_rate(),
                "average_template_time": (
                    self.image_metrics.template_match_time / self.image_metrics.templates_processed
                    if self.image_metrics.templates_processed > 0 else 0
                )
            },
            "cache_stats": self.optimizer.image_cache.get_stats()
        }
        
        # 当前性能等级
        if recent_metrics:
            current_level = self._analyze_performance(recent_metrics[-1])
            summary["current_performance_level"] = current_level.value
        
        return summary
    
    def get_optimization_recommendations(self) -> List[Dict[str, Any]]:
        """获取优化建议"""
        recommendations = []
        current_metrics = self.get_current_metrics()
        
        if not current_metrics:
            return recommendations
        
        # CPU优化建议
        if current_metrics.cpu_percent > self.thresholds.cpu_warning:
            recommendations.append({
                "type": "cpu",
                "level": "warning" if current_metrics.cpu_percent < self.thresholds.cpu_critical else "critical",
                "message": f"CPU使用率过高 ({current_metrics.cpu_percent:.1f}%)",
                "suggestions": [
                    "降低图像检测频率",
                    "减少同时处理的模板数量",
                    "启用图像缓存",
                    "关闭非必要功能"
                ]
            })
        
        # 内存优化建议
        if current_metrics.memory_percent > self.thresholds.memory_warning:
            recommendations.append({
                "type": "memory",
                "level": "warning" if current_metrics.memory_percent < self.thresholds.memory_critical else "critical",
                "message": f"内存使用率过高 ({current_metrics.memory_percent:.1f}%)",
                "suggestions": [
                    "清理图像缓存",
                    "减小图像处理尺寸",
                    "执行垃圾回收",
                    "重启应用程序"
                ]
            })
        
        # 图像处理优化建议
        cache_hit_rate = self.image_metrics.get_cache_hit_rate()
        if cache_hit_rate < 0.5 and self.image_metrics.templates_processed > 100:
            recommendations.append({
                "type": "image_processing",
                "level": "info",
                "message": f"图像缓存命中率较低 ({cache_hit_rate:.1%})",
                "suggestions": [
                    "增加缓存大小",
                    "优化模板匹配策略",
                    "减少重复的图像处理操作"
                ]
            })
        
        return recommendations
    
    def export_performance_data(self, filepath: str, hours: int = 1):
        """导出性能数据"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        export_data = [
            metrics.to_dict() for metrics in self.metrics_history 
            if metrics.timestamp >= cutoff_time
        ]
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump({
                "export_time": datetime.now().isoformat(),
                "time_range_hours": hours,
                "data_count": len(export_data),
                "metrics": export_data,
                "summary": self.get_performance_summary(hours * 60)
            }, f, indent=2, ensure_ascii=False)
        
        logger.info(f"性能数据已导出到: {filepath}")
    
    def set_callbacks(self, warning_callback: Optional[Callable] = None,
                     critical_callback: Optional[Callable] = None,
                     optimization_callback: Optional[Callable] = None):
        """设置回调函数"""
        self.performance_warning_callback = warning_callback
        self.performance_critical_callback = critical_callback
        self.optimization_applied_callback = optimization_callback
    
    def update_thresholds(self, **kwargs):
        """更新性能阈值"""
        for key, value in kwargs.items():
            if hasattr(self.thresholds, key):
                setattr(self.thresholds, key, value)
                logger.info(f"性能阈值已更新: {key} = {value}")
    
    def reset_image_metrics(self):
        """重置图像处理指标"""
        self.image_metrics = ImageProcessingMetrics()
        self.optimizer.image_cache.clear()
        logger.info("图像处理指标已重置")