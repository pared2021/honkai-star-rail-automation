"""配置管理器实现

提供统一的配置管理功能。
"""

import json
import yaml
import configparser
import os
from typing import Any, Dict, List, Optional, Callable, Set
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime
from loguru import logger

from .interfaces.config_interface import IConfigManager, ConfigFormat, ConfigScope
from .dependency_injection import Injectable

@dataclass
class ConfigChangeEvent:
    """配置变更事件"""
    key: str
    old_value: Any
    new_value: Any
    scope: ConfigScope
    timestamp: datetime = field(default_factory=datetime.now)

class ConfigManager(Injectable, IConfigManager):
    """配置管理器实现
    
    提供多格式、多作用域的配置管理功能。
    """
    
    def __init__(self, config_dir: Optional[str] = None):
        # 从环境变量或参数获取配置目录
        default_config_dir = os.getenv('XINGTIE_CONFIG_DIR', 'config')
        self._config_dir = Path(config_dir or default_config_dir)
        self._configs: Dict[ConfigScope, Dict[str, Any]] = {
            scope: {} for scope in ConfigScope
        }
        # 配置作用域优先级可通过环境变量配置
        priority_env = os.getenv('XINGTIE_CONFIG_PRIORITY')
        if priority_env:
            priority_names = priority_env.split(',')
            self._scope_priority = [ConfigScope(name.strip()) for name in priority_names if name.strip() in [s.value for s in ConfigScope]]
        else:
            self._scope_priority = [
                ConfigScope.RUNTIME,
                ConfigScope.USER,
                ConfigScope.PROJECT,
                ConfigScope.SYSTEM,
                ConfigScope.DEFAULT
            ]
        self._change_listeners: List[Callable[[ConfigChangeEvent], None]] = []
        self._validation_rules: Dict[str, Callable[[Any], bool]] = {}
        self._validation_errors: Dict[str, str] = {}
        self._config_info: Dict[ConfigScope, Dict[str, Any]] = {
            scope: {} for scope in ConfigScope
        }
        self._backup_configs: Dict[str, Dict[ConfigScope, Dict[str, Any]]] = {}
        # 缓存TTL可通过环境变量配置
        self._cache_ttl = int(os.getenv('XINGTIE_CONFIG_CACHE_TTL', '300'))  # 默认5分钟缓存
        
        # 确保配置目录存在
        self._config_dir.mkdir(parents=True, exist_ok=True)
        
        # 加载默认配置
        self._load_default_configs()
    
    def load_config(self, file_path: str, scope: ConfigScope = ConfigScope.PROJECT,
                   format_type: ConfigFormat = ConfigFormat.AUTO) -> bool:
        """加载配置文件
        
        Args:
            file_path: 配置文件路径
            scope: 配置作用域
            format_type: 配置格式
            
        Returns:
            是否加载成功
        """
        try:
            path = Path(file_path)
            if not path.exists():
                logger.warning(f"配置文件不存在: {file_path}")
                return False
            
            # 自动检测格式
            if format_type == ConfigFormat.AUTO:
                format_type = self._detect_format(path)
            
            # 读取配置
            config_data = self._read_config_file(path, format_type)
            if config_data is None:
                return False
            
            # 合并到指定作用域
            old_config = self._configs[scope].copy()
            self._configs[scope].update(config_data)
            
            # 记录配置信息
            self._config_info[scope][str(path)] = {
                'file_path': str(path),
                'format': format_type.value,
                'loaded_at': datetime.now(),
                'size': path.stat().st_size
            }
            
            # 通知变更
            self._notify_config_changes(old_config, self._configs[scope], scope)
            
            logger.info(f"配置文件已加载: {file_path} -> {scope.value}")
            return True
            
        except Exception as e:
            logger.error(f"加载配置文件失败: {file_path}, 错误: {e}")
            return False
    
    def save_config(self, file_path: str, scope: ConfigScope = ConfigScope.PROJECT,
                   format_type: ConfigFormat = ConfigFormat.JSON) -> bool:
        """保存配置到文件
        
        Args:
            file_path: 配置文件路径
            scope: 配置作用域
            format_type: 配置格式
            
        Returns:
            是否保存成功
        """
        try:
            path = Path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            config_data = self._configs[scope]
            self._write_config_file(path, config_data, format_type)
            
            # 更新配置信息
            self._config_info[scope][str(path)] = {
                'file_path': str(path),
                'format': format_type.value,
                'saved_at': datetime.now(),
                'size': path.stat().st_size
            }
            
            logger.info(f"配置已保存: {scope.value} -> {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"保存配置失败: {file_path}, 错误: {e}")
            return False
    
    def get(self, key: str, default: Any = None, scope: Optional[ConfigScope] = None) -> Any:
        """获取配置值
        
        Args:
            key: 配置键，支持点号分隔的嵌套键
            default: 默认值
            scope: 指定作用域，None表示按优先级查找
            
        Returns:
            配置值
        """
        if scope:
            return self._get_from_scope(key, scope, default)
        
        # 按优先级查找
        for scope in self._scope_priority:
            value = self._get_from_scope(key, scope, None)
            if value is not None:
                return value
        
        return default
    
    def set(self, key: str, value: Any, scope: ConfigScope = ConfigScope.RUNTIME) -> bool:
        """设置配置值
        
        Args:
            key: 配置键
            value: 配置值
            scope: 配置作用域
            
        Returns:
            是否设置成功
        """
        try:
            # 验证配置
            if not self._validate_config_value(key, value):
                return False
            
            old_value = self._get_from_scope(key, scope, None)
            self._set_in_scope(key, value, scope)
            
            # 通知变更
            change_event = ConfigChangeEvent(
                key=key,
                old_value=old_value,
                new_value=value,
                scope=scope
            )
            self._notify_change_listeners(change_event)
            
            logger.debug(f"配置已设置: {key} = {value} ({scope.value})")
            return True
            
        except Exception as e:
            logger.error(f"设置配置失败: {key}, 错误: {e}")
            return False
    
    def delete(self, key: str, scope: ConfigScope = ConfigScope.RUNTIME) -> bool:
        """删除配置项
        
        Args:
            key: 配置键
            scope: 配置作用域
            
        Returns:
            是否删除成功
        """
        try:
            old_value = self._get_from_scope(key, scope, None)
            if old_value is None:
                return False
            
            self._delete_from_scope(key, scope)
            
            # 通知变更
            change_event = ConfigChangeEvent(
                key=key,
                old_value=old_value,
                new_value=None,
                scope=scope
            )
            self._notify_change_listeners(change_event)
            
            logger.debug(f"配置已删除: {key} ({scope.value})")
            return True
            
        except Exception as e:
            logger.error(f"删除配置失败: {key}, 错误: {e}")
            return False
    
    def exists(self, key: str, scope: Optional[ConfigScope] = None) -> bool:
        """检查配置项是否存在
        
        Args:
            key: 配置键
            scope: 指定作用域，None表示在所有作用域中查找
            
        Returns:
            是否存在
        """
        if scope:
            return self._get_from_scope(key, scope, None) is not None
        
        for scope in self._scope_priority:
            if self._get_from_scope(key, scope, None) is not None:
                return True
        
        return False
    
    def get_all(self, scope: Optional[ConfigScope] = None) -> Dict[str, Any]:
        """获取所有配置
        
        Args:
            scope: 指定作用域，None表示合并所有作用域
            
        Returns:
            配置字典
        """
        if scope:
            return self._configs[scope].copy()
        
        # 合并所有作用域（按优先级）
        merged_config = {}
        for scope in reversed(self._scope_priority):
            merged_config.update(self._configs[scope])
        
        return merged_config
    
    def get_section(self, section: str, scope: Optional[ConfigScope] = None) -> Dict[str, Any]:
        """获取配置段
        
        Args:
            section: 配置段名称
            scope: 指定作用域
            
        Returns:
            配置段字典
        """
        all_config = self.get_all(scope)
        return {k: v for k, v in all_config.items() if k.startswith(f"{section}.")}
    
    def merge_config(self, config: Dict[str, Any], scope: ConfigScope = ConfigScope.RUNTIME) -> bool:
        """合并配置
        
        Args:
            config: 要合并的配置
            scope: 目标作用域
            
        Returns:
            是否合并成功
        """
        try:
            old_config = self._configs[scope].copy()
            
            # 深度合并
            self._deep_merge(self._configs[scope], config)
            
            # 通知变更
            self._notify_config_changes(old_config, self._configs[scope], scope)
            
            logger.debug(f"配置已合并到 {scope.value}")
            return True
            
        except Exception as e:
            logger.error(f"合并配置失败: {e}")
            return False
    
    def clear(self, scope: ConfigScope = ConfigScope.RUNTIME) -> bool:
        """清空配置
        
        Args:
            scope: 配置作用域
            
        Returns:
            是否清空成功
        """
        try:
            old_config = self._configs[scope].copy()
            self._configs[scope].clear()
            
            # 通知变更
            self._notify_config_changes(old_config, {}, scope)
            
            logger.debug(f"配置已清空: {scope.value}")
            return True
            
        except Exception as e:
            logger.error(f"清空配置失败: {e}")
            return False
    
    def get_keys(self, scope: Optional[ConfigScope] = None) -> List[str]:
        """获取所有配置键
        
        Args:
            scope: 指定作用域
            
        Returns:
            配置键列表
        """
        if scope:
            return list(self._configs[scope].keys())
        
        keys = set()
        for scope in ConfigScope:
            keys.update(self._configs[scope].keys())
        
        return list(keys)
    
    def get_sections(self, scope: Optional[ConfigScope] = None) -> List[str]:
        """获取所有配置段
        
        Args:
            scope: 指定作用域
            
        Returns:
            配置段列表
        """
        keys = self.get_keys(scope)
        sections = set()
        
        for key in keys:
            if '.' in key:
                section = key.split('.')[0]
                sections.add(section)
        
        return list(sections)
    
    def add_validation_rule(self, key: str, validator: Callable[[Any], bool]) -> None:
        """添加验证规则
        
        Args:
            key: 配置键
            validator: 验证函数
        """
        self._validation_rules[key] = validator
    
    def remove_validation_rule(self, key: str) -> bool:
        """移除验证规则
        
        Args:
            key: 配置键
            
        Returns:
            是否移除成功
        """
        return self._validation_rules.pop(key, None) is not None
    
    def validate_config(self, config: Optional[Dict[str, Any]] = None, 
                       scope: Optional[ConfigScope] = None) -> bool:
        """验证配置
        
        Args:
            config: 要验证的配置，None表示验证当前配置
            scope: 指定作用域
            
        Returns:
            是否验证通过
        """
        if config is None:
            config = self.get_all(scope)
        
        self._validation_errors.clear()
        is_valid = True
        
        for key, value in config.items():
            if not self._validate_config_value(key, value):
                is_valid = False
        
        return is_valid
    
    def get_validation_errors(self) -> Dict[str, str]:
        """获取验证错误
        
        Returns:
            验证错误字典
        """
        return self._validation_errors.copy()
    
    def add_change_listener(self, listener: Callable[[ConfigChangeEvent], None]) -> None:
        """添加配置变更监听器
        
        Args:
            listener: 监听器函数
        """
        self._change_listeners.append(listener)
    
    def remove_change_listener(self, listener: Callable[[ConfigChangeEvent], None]) -> bool:
        """移除配置变更监听器
        
        Args:
            listener: 监听器函数
            
        Returns:
            是否移除成功
        """
        try:
            self._change_listeners.remove(listener)
            return True
        except ValueError:
            return False
    
    def reload_config(self, scope: Optional[ConfigScope] = None) -> bool:
        """重新加载配置
        
        Args:
            scope: 指定作用域，None表示重新加载所有
            
        Returns:
            是否重新加载成功
        """
        try:
            scopes_to_reload = [scope] if scope else list(ConfigScope)
            
            for scope in scopes_to_reload:
                if scope == ConfigScope.DEFAULT:
                    continue  # 默认配置不需要重新加载
                
                # 重新加载文件配置
                for file_info in self._config_info[scope].values():
                    if 'file_path' in file_info:
                        self.load_config(file_info['file_path'], scope)
            
            logger.info("配置重新加载完成")
            return True
            
        except Exception as e:
            logger.error(f"重新加载配置失败: {e}")
            return False
    
    def backup_config(self, backup_name: str, scope: Optional[ConfigScope] = None) -> bool:
        """备份配置
        
        Args:
            backup_name: 备份名称
            scope: 指定作用域，None表示备份所有
            
        Returns:
            是否备份成功
        """
        try:
            if scope:
                self._backup_configs[backup_name] = {scope: self._configs[scope].copy()}
            else:
                self._backup_configs[backup_name] = {
                    scope: config.copy() for scope, config in self._configs.items()
                }
            
            logger.info(f"配置已备份: {backup_name}")
            return True
            
        except Exception as e:
            logger.error(f"备份配置失败: {e}")
            return False
    
    def restore_config(self, backup_name: str, scope: Optional[ConfigScope] = None) -> bool:
        """恢复配置
        
        Args:
            backup_name: 备份名称
            scope: 指定作用域，None表示恢复所有
            
        Returns:
            是否恢复成功
        """
        try:
            if backup_name not in self._backup_configs:
                logger.warning(f"备份不存在: {backup_name}")
                return False
            
            backup = self._backup_configs[backup_name]
            
            if scope:
                if scope in backup:
                    old_config = self._configs[scope].copy()
                    self._configs[scope] = backup[scope].copy()
                    self._notify_config_changes(old_config, self._configs[scope], scope)
            else:
                for scope, config in backup.items():
                    old_config = self._configs[scope].copy()
                    self._configs[scope] = config.copy()
                    self._notify_config_changes(old_config, self._configs[scope], scope)
            
            logger.info(f"配置已恢复: {backup_name}")
            return True
            
        except Exception as e:
            logger.error(f"恢复配置失败: {e}")
            return False
    
    def get_config_info(self, scope: Optional[ConfigScope] = None) -> Dict[str, Any]:
        """获取配置信息
        
        Args:
            scope: 指定作用域
            
        Returns:
            配置信息字典
        """
        if scope:
            return self._config_info[scope].copy()
        
        return {scope.value: info for scope, info in self._config_info.items()}
    
    def get_scope_priority(self) -> List[ConfigScope]:
        """获取作用域优先级
        
        Returns:
            作用域优先级列表
        """
        return self._scope_priority.copy()
    
    def set_scope_priority(self, priority: List[ConfigScope]) -> bool:
        """设置作用域优先级
        
        Args:
            priority: 作用域优先级列表
            
        Returns:
            是否设置成功
        """
        try:
            # 验证优先级列表
            if set(priority) != set(ConfigScope):
                logger.error("优先级列表必须包含所有作用域")
                return False
            
            self._scope_priority = priority.copy()
            logger.info(f"作用域优先级已更新: {[s.value for s in priority]}")
            return True
            
        except Exception as e:
            logger.error(f"设置作用域优先级失败: {e}")
            return False
    
    # 私有方法
    
    def _load_default_configs(self):
        """加载默认配置"""
        # 尝试从默认配置文件加载
        default_config_path = self._config_dir / "default.json"
        if default_config_path.exists():
            try:
                with open(default_config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                    # 转换为扁平化格式
                    default_config = self._flatten_config(config_data)
                    self._configs[ConfigScope.DEFAULT] = default_config
                    return
            except Exception as e:
                logger.warning(f"加载默认配置文件失败: {e}，使用内置默认配置")
        
        # 如果配置文件不存在，使用内置默认配置
        default_config = self._get_builtin_default_config()
        self._configs[ConfigScope.DEFAULT] = default_config
        
        # 创建默认配置文件
        self._create_default_config_file(default_config_path, self._unflatten_config(default_config))
    
    def _get_builtin_default_config(self) -> Dict[str, Any]:
        """获取内置默认配置
        
        支持从环境变量覆盖默认值
        """
        return {
            'app.name': os.getenv('XINGTIE_APP_NAME', '星铁自动化助手'),
            'app.version': os.getenv('XINGTIE_APP_VERSION', '1.0.0'),
            'app.debug': os.getenv('XINGTIE_APP_DEBUG', 'false').lower() == 'true',
            'app.log_level': os.getenv('XINGTIE_LOG_LEVEL', 'INFO'),
            'database.pool_size': int(os.getenv('XINGTIE_DB_POOL_SIZE', '10')),
            'database.timeout': int(os.getenv('XINGTIE_DB_TIMEOUT', '30')),
            'cache.ttl': int(os.getenv('XINGTIE_CACHE_TTL', '3600')),
            'cache.max_size': int(os.getenv('XINGTIE_CACHE_MAX_SIZE', '1000')),
            'scheduler.max_concurrent_tasks': int(os.getenv('XINGTIE_SCHEDULER_MAX_TASKS', '3')),
            'scheduler.check_interval': float(os.getenv('XINGTIE_SCHEDULER_CHECK_INTERVAL', '1.0')),
            'monitor.check_interval': float(os.getenv('XINGTIE_MONITOR_CHECK_INTERVAL', '5.0')),
            'resource.memory_limit': os.getenv('XINGTIE_RESOURCE_MEMORY_LIMIT', '1GB'),
            'resource.cpu_limit': int(os.getenv('XINGTIE_RESOURCE_CPU_LIMIT', '80')),
            'automation.action_delay': float(os.getenv('XINGTIE_AUTOMATION_ACTION_DELAY', '0.1')),
            'automation.template_threshold': float(os.getenv('XINGTIE_AUTOMATION_TEMPLATE_THRESHOLD', '0.8')),
            'game.window_title': os.getenv('XINGTIE_GAME_WINDOW_TITLE', '崩坏：星穹铁道'),
            'game.process_name': os.getenv('XINGTIE_GAME_PROCESS_NAME', 'StarRail.exe')
        }
    
    def _create_default_config_file(self, config_path: Path, config_data: Dict[str, Any]):
        """创建默认配置文件."""
        try:
            config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            logger.info(f"已创建默认配置文件: {config_path}")
        except Exception as e:
            logger.error(f"创建默认配置文件失败: {e}")
    
    def _flatten_config(self, config_data: Dict[str, Any], prefix: str = '') -> Dict[str, Any]:
        """将嵌套配置转换为扁平化格式."""
        result = {}
        for key, value in config_data.items():
            full_key = f"{prefix}.{key}" if prefix else key
            if isinstance(value, dict):
                result.update(self._flatten_config(value, full_key))
            else:
                result[full_key] = value
        return result
    
    def _unflatten_config(self, flat_config: Dict[str, Any]) -> Dict[str, Any]:
        """将扁平化配置转换为嵌套格式."""
        result = {}
        for key, value in flat_config.items():
            keys = key.split('.')
            current = result
            for k in keys[:-1]:
                if k not in current:
                    current[k] = {}
                current = current[k]
            current[keys[-1]] = value
        return result
    
    def _detect_format(self, path: Path) -> ConfigFormat:
        """检测配置文件格式"""
        suffix = path.suffix.lower()
        if suffix in ['.json']:
            return ConfigFormat.JSON
        elif suffix in ['.yaml', '.yml']:
            return ConfigFormat.YAML
        elif suffix in ['.ini', '.cfg']:
            return ConfigFormat.INI
        else:
            return ConfigFormat.JSON
    
    def _read_config_file(self, path: Path, format_type: ConfigFormat) -> Optional[Dict[str, Any]]:
        """读取配置文件"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                if format_type == ConfigFormat.JSON:
                    return json.load(f)
                elif format_type == ConfigFormat.YAML:
                    return yaml.safe_load(f)
                elif format_type == ConfigFormat.INI:
                    parser = configparser.ConfigParser()
                    parser.read_string(f.read())
                    return {f"{section}.{key}": value 
                           for section in parser.sections() 
                           for key, value in parser[section].items()}
        except Exception as e:
            logger.error(f"读取配置文件失败: {path}, 错误: {e}")
            return None
    
    def _write_config_file(self, path: Path, config: Dict[str, Any], format_type: ConfigFormat):
        """写入配置文件"""
        with open(path, 'w', encoding='utf-8') as f:
            if format_type == ConfigFormat.JSON:
                json.dump(config, f, indent=2, ensure_ascii=False)
            elif format_type == ConfigFormat.YAML:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
            elif format_type == ConfigFormat.INI:
                parser = configparser.ConfigParser()
                for key, value in config.items():
                    if '.' in key:
                        section, option = key.split('.', 1)
                        if section not in parser:
                            parser.add_section(section)
                        parser.set(section, option, str(value))
                parser.write(f)
    
    def _get_from_scope(self, key: str, scope: ConfigScope, default: Any) -> Any:
        """从指定作用域获取配置值"""
        config = self._configs[scope]
        
        # 支持点号分隔的嵌套键
        if '.' in key:
            keys = key.split('.')
            value = config
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default
            return value
        else:
            return config.get(key, default)
    
    def _set_in_scope(self, key: str, value: Any, scope: ConfigScope):
        """在指定作用域设置配置值"""
        config = self._configs[scope]
        
        # 支持点号分隔的嵌套键
        if '.' in key:
            keys = key.split('.')
            current = config
            for k in keys[:-1]:
                if k not in current:
                    current[k] = {}
                current = current[k]
            current[keys[-1]] = value
        else:
            config[key] = value
    
    def _delete_from_scope(self, key: str, scope: ConfigScope):
        """从指定作用域删除配置项"""
        config = self._configs[scope]
        
        # 支持点号分隔的嵌套键
        if '.' in key:
            keys = key.split('.')
            current = config
            for k in keys[:-1]:
                if k not in current:
                    return
                current = current[k]
            if keys[-1] in current:
                del current[keys[-1]]
        else:
            if key in config:
                del config[key]
    
    def _validate_config_value(self, key: str, value: Any) -> bool:
        """验证配置值"""
        if key in self._validation_rules:
            try:
                if not self._validation_rules[key](value):
                    self._validation_errors[key] = f"验证失败: {key} = {value}"
                    return False
            except Exception as e:
                self._validation_errors[key] = f"验证异常: {e}"
                return False
        return True
    
    def _deep_merge(self, target: Dict[str, Any], source: Dict[str, Any]):
        """深度合并字典"""
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._deep_merge(target[key], value)
            else:
                target[key] = value
    
    def _notify_config_changes(self, old_config: Dict[str, Any], 
                              new_config: Dict[str, Any], scope: ConfigScope):
        """通知配置变更"""
        # 找出变更的键
        all_keys = set(old_config.keys()) | set(new_config.keys())
        
        for key in all_keys:
            old_value = old_config.get(key)
            new_value = new_config.get(key)
            
            if old_value != new_value:
                change_event = ConfigChangeEvent(
                    key=key,
                    old_value=old_value,
                    new_value=new_value,
                    scope=scope
                )
                self._notify_change_listeners(change_event)
    
    def _notify_change_listeners(self, change_event: ConfigChangeEvent):
        """通知变更监听器"""
        for listener in self._change_listeners:
            try:
                listener(change_event)
            except Exception as e:
                logger.error(f"配置变更监听器异常: {e}")