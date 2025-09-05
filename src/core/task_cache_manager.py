# -*- coding: utf-8 -*-
"""
任务缓存管理器 - 负责任务数据的缓存管理
"""

import hashlib
import json
import time
from typing import Any, Dict, List, Optional

from ..utils.logger import get_logger

logger = get_logger(__name__)


class TaskCacheManager:
    """任务缓存管理器 - 专门负责任务数据的缓存操作"""

    def __init__(self, config_manager=None, cache_ttl: int = None, max_cache_size: int = None):
        """初始化任务缓存管理器

        Args:
            config_manager: 配置管理器
            cache_ttl: 缓存生存时间（秒），默认从配置获取
            max_cache_size: 最大缓存条目数，默认从配置获取
        """
        self.config_manager = config_manager
        self._cache = {}  # 缓存存储
        self._cache_timestamps = {}  # 缓存时间戳
        self._cache_ttl = cache_ttl or self._get_config_value('task_cache.cache_ttl', 300)
        self._max_cache_size = max_cache_size or self._get_config_value('task_cache.max_cache_size', 1000)
        self._cache_hits = 0
        self._cache_misses = 0
    
    def _get_config_value(self, key: str, default_value):
        """获取配置值"""
        if self.config_manager:
            return self.config_manager.get(key, default_value)
        return default_value

    def _get_cache_key(self, operation: str, **kwargs) -> str:
        """生成缓存键

        Args:
            operation: 操作类型
            **kwargs: 参数

        Returns:
            str: 缓存键
        """
        # 创建一个包含操作和参数的字典
        cache_data = {"operation": operation, **kwargs}
        
        # 将字典转换为JSON字符串并排序键以确保一致性
        cache_string = json.dumps(cache_data, sort_keys=True, ensure_ascii=False)
        
        # 生成MD5哈希作为缓存键
        return hashlib.md5(cache_string.encode('utf-8')).hexdigest()

    def _is_cache_valid(self, cache_key: str) -> bool:
        """检查缓存是否有效

        Args:
            cache_key: 缓存键

        Returns:
            bool: 缓存是否有效
        """
        if cache_key not in self._cache_timestamps:
            return False
        
        cache_time = self._cache_timestamps[cache_key]
        current_time = time.time()
        
        return (current_time - cache_time) < self._cache_ttl

    def _cleanup_expired_cache(self):
        """清理过期的缓存条目"""
        current_time = time.time()
        expired_keys = []
        
        for cache_key, cache_time in self._cache_timestamps.items():
            if (current_time - cache_time) >= self._cache_ttl:
                expired_keys.append(cache_key)
        
        for key in expired_keys:
            self._cache.pop(key, None)
            self._cache_timestamps.pop(key, None)
        
        if expired_keys:
            logger.debug(f"清理了 {len(expired_keys)} 个过期缓存条目")

    def _enforce_cache_size_limit(self):
        """强制执行缓存大小限制"""
        if len(self._cache) <= self._max_cache_size:
            return
        
        # 按时间戳排序，移除最旧的条目
        sorted_items = sorted(
            self._cache_timestamps.items(), 
            key=lambda x: x[1]
        )
        
        # 计算需要移除的条目数
        items_to_remove = len(self._cache) - self._max_cache_size
        
        for i in range(items_to_remove):
            cache_key = sorted_items[i][0]
            self._cache.pop(cache_key, None)
            self._cache_timestamps.pop(cache_key, None)
        
        logger.debug(f"移除了 {items_to_remove} 个最旧的缓存条目以满足大小限制")

    def get_cached_data(self, operation: str, **kwargs) -> Optional[Any]:
        """获取缓存数据

        Args:
            operation: 操作类型
            **kwargs: 参数

        Returns:
            Optional[Any]: 缓存的数据，如果不存在或已过期返回None
        """
        cache_key = self._get_cache_key(operation, **kwargs)
        
        # 检查缓存是否存在且有效
        if cache_key in self._cache and self._is_cache_valid(cache_key):
            self._cache_hits += 1
            logger.debug(f"缓存命中: {operation}")
            return self._cache[cache_key]
        
        self._cache_misses += 1
        logger.debug(f"缓存未命中: {operation}")
        return None

    def set_cached_data(self, data: Any, operation: str, **kwargs):
        """设置缓存数据

        Args:
            data: 要缓存的数据
            operation: 操作类型
            **kwargs: 参数
        """
        cache_key = self._get_cache_key(operation, **kwargs)
        current_time = time.time()
        
        # 清理过期缓存
        self._cleanup_expired_cache()
        
        # 设置缓存
        self._cache[cache_key] = data
        self._cache_timestamps[cache_key] = current_time
        
        # 强制执行大小限制
        self._enforce_cache_size_limit()
        
        logger.debug(f"缓存已设置: {operation}")

    def invalidate_cache(self, operation: str = None, **kwargs):
        """使缓存失效

        Args:
            operation: 操作类型，如果为None则清空所有缓存
            **kwargs: 参数
        """
        if operation is None:
            # 清空所有缓存
            cleared_count = len(self._cache)
            self._cache.clear()
            self._cache_timestamps.clear()
            logger.info(f"已清空所有缓存，共清理 {cleared_count} 个条目")
        else:
            # 清空特定操作的缓存
            cache_key = self._get_cache_key(operation, **kwargs)
            if cache_key in self._cache:
                self._cache.pop(cache_key)
                self._cache_timestamps.pop(cache_key)
                logger.debug(f"已清理缓存: {operation}")

    def invalidate_task_cache(self, task_id: str):
        """使特定任务相关的所有缓存失效

        Args:
            task_id: 任务ID
        """
        keys_to_remove = []
        
        for cache_key in self._cache.keys():
            # 检查缓存键是否包含任务ID
            try:
                # 尝试从缓存键重构原始参数
                for key, timestamp in self._cache_timestamps.items():
                    if key == cache_key:
                        # 这里可以添加更复杂的逻辑来检查缓存是否与特定任务相关
                        # 简单起见，我们检查任务ID是否在缓存键中
                        if task_id in str(self._cache.get(cache_key, "")):
                            keys_to_remove.append(cache_key)
                        break
            except Exception:
                continue
        
        for key in keys_to_remove:
            self._cache.pop(key, None)
            self._cache_timestamps.pop(key, None)
        
        if keys_to_remove:
            logger.debug(f"已清理任务 {task_id} 相关的 {len(keys_to_remove)} 个缓存条目")

    def invalidate_user_cache(self, user_id: str):
        """使特定用户相关的所有缓存失效

        Args:
            user_id: 用户ID
        """
        keys_to_remove = []
        
        for cache_key in self._cache.keys():
            # 检查缓存键是否包含用户ID
            try:
                if user_id in str(self._cache.get(cache_key, "")):
                    keys_to_remove.append(cache_key)
            except Exception:
                continue
        
        for key in keys_to_remove:
            self._cache.pop(key, None)
            self._cache_timestamps.pop(key, None)
        
        if keys_to_remove:
            logger.debug(f"已清理用户 {user_id} 相关的 {len(keys_to_remove)} 个缓存条目")

    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息

        Returns:
            Dict[str, Any]: 缓存统计信息
        """
        total_requests = self._cache_hits + self._cache_misses
        hit_rate = (self._cache_hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "cache_size": len(self._cache),
            "max_cache_size": self._max_cache_size,
            "cache_ttl": self._cache_ttl,
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses,
            "hit_rate": round(hit_rate, 2),
            "total_requests": total_requests,
        }

    def reset_stats(self):
        """重置缓存统计信息"""
        self._cache_hits = 0
        self._cache_misses = 0
        logger.info("缓存统计信息已重置")

    def configure_cache(self, cache_ttl: int = None, max_cache_size: int = None):
        """配置缓存参数

        Args:
            cache_ttl: 缓存生存时间（秒）
            max_cache_size: 最大缓存条目数
        """
        if cache_ttl is not None:
            self._cache_ttl = cache_ttl
            logger.info(f"缓存TTL已更新为 {cache_ttl} 秒")
        
        if max_cache_size is not None:
            old_size = self._max_cache_size
            self._max_cache_size = max_cache_size
            
            # 如果新的大小限制更小，立即强制执行
            if max_cache_size < old_size:
                self._enforce_cache_size_limit()
            
            logger.info(f"最大缓存大小已更新为 {max_cache_size}")

    async def cached_query(self, query_func, operation: str, use_cache: bool = True, **kwargs):
        """执行带缓存的查询

        Args:
            query_func: 查询函数
            operation: 操作类型
            use_cache: 是否使用缓存
            **kwargs: 查询参数

        Returns:
            查询结果
        """
        if not use_cache:
            # 不使用缓存，直接执行查询
            if asyncio.iscoroutinefunction(query_func):
                return await query_func(**kwargs)
            else:
                return query_func(**kwargs)
        
        # 尝试从缓存获取数据
        cached_result = self.get_cached_data(operation, **kwargs)
        if cached_result is not None:
            return cached_result
        
        # 缓存未命中，执行查询
        if asyncio.iscoroutinefunction(query_func):
            result = await query_func(**kwargs)
        else:
            result = query_func(**kwargs)
        
        # 将结果存入缓存
        self.set_cached_data(result, operation, **kwargs)
        
        return result