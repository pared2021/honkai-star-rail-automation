"""任务缓存管理器

专门负责任务相关的缓存操作。
"""

import time
import hashlib
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import OrderedDict
from loguru import logger

from ..interfaces import ICacheManager, IConfigManager
from ..dependency_injection import Injectable, inject

@dataclass
class CacheEntry:
    """缓存条目"""
    value: Any
    created_at: float
    ttl: int
    access_count: int = 0
    last_accessed: float = field(default_factory=time.time)
    
    def is_expired(self) -> bool:
        """检查是否过期"""
        return time.time() - self.created_at > self.ttl
    
    def touch(self):
        """更新访问时间"""
        self.last_accessed = time.time()
        self.access_count += 1

@dataclass
class CacheStats:
    """缓存统计信息"""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    expired_removals: int = 0
    memory_usage: int = 0
    
    @property
    def hit_rate(self) -> float:
        """命中率"""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0

class TaskCacheManager(Injectable, ICacheManager):
    """任务缓存管理器
    
    专门负责任务相关的缓存操作，支持LRU淘汰策略、TTL管理等。
    """
    
    @inject
    def __init__(self, config_manager: IConfigManager):
        self._config_manager = config_manager
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._max_size = config_manager.get('cache.max_size', 1000)
        self._default_ttl = config_manager.get('cache.ttl', 3600)
        self._stats = CacheStats()
        self._cleanup_interval = config_manager.get('cache.cleanup_interval', 300)  # 5分钟清理一次
        self._last_cleanup = time.time()
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取缓存值
        
        Args:
            key: 缓存键
            default: 默认值
            
        Returns:
            缓存值或默认值
        """
        self._cleanup_if_needed()
        
        if key not in self._cache:
            self._stats.misses += 1
            return default
        
        entry = self._cache[key]
        
        # 检查是否过期
        if entry.is_expired():
            del self._cache[key]
            self._stats.expired_removals += 1
            self._stats.misses += 1
            return default
        
        # 更新访问信息
        entry.touch()
        
        # 移到末尾（LRU）
        self._cache.move_to_end(key)
        
        self._stats.hits += 1
        return entry.value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 生存时间（秒），None使用默认值
            
        Returns:
            是否设置成功
        """
        try:
            self._cleanup_if_needed()
            
            if ttl is None:
                ttl = self._default_ttl
            
            # 创建缓存条目
            entry = CacheEntry(
                value=value,
                created_at=time.time(),
                ttl=ttl
            )
            
            # 如果键已存在，更新
            if key in self._cache:
                self._cache[key] = entry
                self._cache.move_to_end(key)
            else:
                # 检查是否需要淘汰
                if len(self._cache) >= self._max_size:
                    self._evict_lru()
                
                self._cache[key] = entry
            
            self._update_memory_usage()
            return True
            
        except Exception as e:
            logger.error(f"设置缓存失败: {key}, 错误: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """删除缓存项
        
        Args:
            key: 缓存键
            
        Returns:
            是否删除成功
        """
        if key in self._cache:
            del self._cache[key]
            self._update_memory_usage()
            return True
        return False
    
    def exists(self, key: str) -> bool:
        """检查缓存项是否存在且未过期
        
        Args:
            key: 缓存键
            
        Returns:
            是否存在
        """
        if key not in self._cache:
            return False
        
        entry = self._cache[key]
        if entry.is_expired():
            del self._cache[key]
            self._stats.expired_removals += 1
            return False
        
        return True
    
    def clear(self) -> bool:
        """清空所有缓存
        
        Returns:
            是否清空成功
        """
        try:
            self._cache.clear()
            self._stats = CacheStats()
            return True
        except Exception as e:
            logger.error(f"清空缓存失败: {e}")
            return False
    
    def get_keys(self, pattern: Optional[str] = None) -> List[str]:
        """获取缓存键列表
        
        Args:
            pattern: 键模式（简单的通配符匹配）
            
        Returns:
            键列表
        """
        self._cleanup_if_needed()
        
        keys = list(self._cache.keys())
        
        if pattern:
            import fnmatch
            keys = [key for key in keys if fnmatch.fnmatch(key, pattern)]
        
        return keys
    
    def get_size(self) -> int:
        """获取缓存大小
        
        Returns:
            缓存项数量
        """
        return len(self._cache)
    
    def get_memory_usage(self) -> int:
        """获取内存使用量（估算）
        
        Returns:
            内存使用量（字节）
        """
        return self._stats.memory_usage
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取缓存统计信息
        
        Returns:
            统计信息字典
        """
        return {
            'size': len(self._cache),
            'max_size': self._max_size,
            'hits': self._stats.hits,
            'misses': self._stats.misses,
            'hit_rate': self._stats.hit_rate,
            'evictions': self._stats.evictions,
            'expired_removals': self._stats.expired_removals,
            'memory_usage': self._stats.memory_usage
        }
    
    def invalidate_pattern(self, pattern: str) -> int:
        """按模式失效缓存
        
        Args:
            pattern: 键模式
            
        Returns:
            失效的缓存项数量
        """
        import fnmatch
        
        keys_to_remove = [
            key for key in self._cache.keys()
            if fnmatch.fnmatch(key, pattern)
        ]
        
        for key in keys_to_remove:
            del self._cache[key]
        
        self._update_memory_usage()
        return len(keys_to_remove)
    
    def set_ttl(self, key: str, ttl: int) -> bool:
        """设置缓存项的TTL
        
        Args:
            key: 缓存键
            ttl: 新的TTL（秒）
            
        Returns:
            是否设置成功
        """
        if key in self._cache:
            entry = self._cache[key]
            entry.ttl = ttl
            entry.created_at = time.time()  # 重置创建时间
            return True
        return False
    
    def get_ttl(self, key: str) -> Optional[int]:
        """获取缓存项的剩余TTL
        
        Args:
            key: 缓存键
            
        Returns:
            剩余TTL（秒），None表示不存在
        """
        if key not in self._cache:
            return None
        
        entry = self._cache[key]
        elapsed = time.time() - entry.created_at
        remaining = entry.ttl - elapsed
        
        return max(0, int(remaining))
    
    # 任务相关的缓存方法
    
    def cache_task(self, task_id: str, task_data: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """缓存任务数据
        
        Args:
            task_id: 任务ID
            task_data: 任务数据
            ttl: 生存时间
            
        Returns:
            是否缓存成功
        """
        key = f"task:{task_id}"
        return self.set(key, task_data, ttl)
    
    def get_cached_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取缓存的任务数据
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务数据或None
        """
        key = f"task:{task_id}"
        return self.get(key)
    
    def invalidate_task(self, task_id: str) -> bool:
        """失效任务缓存
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否失效成功
        """
        key = f"task:{task_id}"
        return self.delete(key)
    
    def cache_query_result(self, query: str, params: Dict[str, Any], 
                          result: Any, ttl: Optional[int] = None) -> bool:
        """缓存查询结果
        
        Args:
            query: 查询语句
            params: 查询参数
            result: 查询结果
            ttl: 生存时间
            
        Returns:
            是否缓存成功
        """
        key = self._generate_query_key(query, params)
        return self.set(key, result, ttl)
    
    def get_cached_query_result(self, query: str, params: Dict[str, Any]) -> Any:
        """获取缓存的查询结果
        
        Args:
            query: 查询语句
            params: 查询参数
            
        Returns:
            查询结果或None
        """
        key = self._generate_query_key(query, params)
        return self.get(key)
    
    def cache_user_tasks(self, user_id: str, tasks: List[Dict[str, Any]], 
                        ttl: Optional[int] = None) -> bool:
        """缓存用户任务列表
        
        Args:
            user_id: 用户ID
            tasks: 任务列表
            ttl: 生存时间
            
        Returns:
            是否缓存成功
        """
        key = f"user_tasks:{user_id}"
        return self.set(key, tasks, ttl)
    
    def get_cached_user_tasks(self, user_id: str) -> Optional[List[Dict[str, Any]]]:
        """获取缓存的用户任务列表
        
        Args:
            user_id: 用户ID
            
        Returns:
            任务列表或None
        """
        key = f"user_tasks:{user_id}"
        return self.get(key)
    
    def invalidate_user_tasks(self, user_id: str) -> bool:
        """失效用户任务缓存
        
        Args:
            user_id: 用户ID
            
        Returns:
            是否失效成功
        """
        key = f"user_tasks:{user_id}"
        return self.delete(key)
    
    def cache_statistics(self, stats_type: str, stats_data: Dict[str, Any], 
                        ttl: Optional[int] = None) -> bool:
        """缓存统计数据
        
        Args:
            stats_type: 统计类型
            stats_data: 统计数据
            ttl: 生存时间
            
        Returns:
            是否缓存成功
        """
        key = f"stats:{stats_type}"
        return self.set(key, stats_data, ttl)
    
    def get_cached_statistics(self, stats_type: str) -> Optional[Dict[str, Any]]:
        """获取缓存的统计数据
        
        Args:
            stats_type: 统计类型
            
        Returns:
            统计数据或None
        """
        key = f"stats:{stats_type}"
        return self.get(key)
    
    # 私有方法
    
    def _generate_query_key(self, query: str, params: Dict[str, Any]) -> str:
        """生成查询缓存键
        
        Args:
            query: 查询语句
            params: 查询参数
            
        Returns:
            缓存键
        """
        # 创建查询和参数的哈希
        content = f"{query}:{sorted(params.items())}"
        hash_value = hashlib.md5(content.encode()).hexdigest()
        return f"query:{hash_value}"
    
    def _evict_lru(self):
        """淘汰最近最少使用的缓存项"""
        if self._cache:
            # OrderedDict的第一个项是最旧的
            key, _ = self._cache.popitem(last=False)
            self._stats.evictions += 1
            logger.debug(f"淘汰缓存项: {key}")
    
    def _cleanup_if_needed(self):
        """如果需要则清理过期缓存"""
        current_time = time.time()
        if current_time - self._last_cleanup > self._cleanup_interval:
            self._cleanup_expired()
            self._last_cleanup = current_time
    
    def _cleanup_expired(self):
        """清理过期缓存"""
        current_time = time.time()
        expired_keys = []
        
        for key, entry in self._cache.items():
            if current_time - entry.created_at > entry.ttl:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self._cache[key]
            self._stats.expired_removals += 1
        
        if expired_keys:
            self._update_memory_usage()
            logger.debug(f"清理了 {len(expired_keys)} 个过期缓存项")
    
    def _update_memory_usage(self):
        """更新内存使用量估算"""
        # 简单的内存使用量估算
        total_size = 0
        for key, entry in self._cache.items():
            # 估算键和值的大小
            key_size = len(key.encode('utf-8'))
            value_size = self._estimate_object_size(entry.value)
            total_size += key_size + value_size + 64  # 额外开销
        
        self._stats.memory_usage = total_size
    
    def _estimate_object_size(self, obj: Any) -> int:
        """估算对象大小
        
        Args:
            obj: 对象
            
        Returns:
            估算的大小（字节）
        """
        import sys
        
        try:
            return sys.getsizeof(obj)
        except:
            # 如果无法获取大小，返回默认值
            return 64
    
    async def dispose(self):
        """清理资源"""
        self.clear()
        logger.info("任务缓存管理器已清理")