# -*- coding: utf-8 -*-
"""
配置管理器 - 支持配置的导入、导出、验证和备份
"""

import json
import os
import shutil
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
import jsonschema
from jsonschema import validate, ValidationError

from loguru import logger


class ConfigType(Enum):
    """配置类型"""
    GAME_SETTINGS = "game_settings"
    AUTOMATION_CONFIG = "automation_config"
    UI_PREFERENCES = "ui_preferences"
    TASK_CONFIG = "task_config"
    PERFORMANCE_CONFIG = "performance_config"
    SYSTEM_CONFIG = "system_config"


class ValidationLevel(Enum):
    """验证级别"""
    STRICT = "strict"      # 严格验证，所有字段必须符合规范
    NORMAL = "normal"      # 正常验证，允许部分字段缺失
    LOOSE = "loose"        # 宽松验证，只检查关键字段


@dataclass
class ConfigValidationResult:
    """配置验证结果"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    missing_fields: List[str]
    invalid_values: Dict[str, str]
    suggestions: List[str]


@dataclass
class ConfigBackup:
    """配置备份信息"""
    backup_id: str
    timestamp: datetime
    config_type: ConfigType
    file_path: str
    description: str
    size: int


class ConfigSchema:
    """配置模式定义"""
    
    # 游戏设置模式
    GAME_SETTINGS_SCHEMA = {
        "type": "object",
        "properties": {
            "game_path": {"type": "string", "minLength": 1},
            "game_resolution": {
                "type": "object",
                "properties": {
                    "width": {"type": "integer", "minimum": 800},
                    "height": {"type": "integer", "minimum": 600}
                },
                "required": ["width", "height"]
            },
            "window_mode": {"type": "string", "enum": ["fullscreen", "windowed", "borderless"]},
            "language": {"type": "string", "enum": ["zh_CN", "en_US", "ja_JP"]},
            "auto_start": {"type": "boolean"},
            "close_game_on_exit": {"type": "boolean"}
        },
        "required": ["game_path", "game_resolution", "window_mode"]
    }
    
    # 自动化配置模式
    AUTOMATION_CONFIG_SCHEMA = {
        "type": "object",
        "properties": {
            "click_delay": {"type": "number", "minimum": 0.1, "maximum": 5.0},
            "operation_timeout": {"type": "integer", "minimum": 5, "maximum": 300},
            "retry_count": {"type": "integer", "minimum": 1, "maximum": 10},
            "screenshot_interval": {"type": "number", "minimum": 0.5, "maximum": 10.0},
            "safety_mode": {"type": "boolean"},
            "auto_recovery": {"type": "boolean"},
            "log_level": {"type": "string", "enum": ["DEBUG", "INFO", "WARNING", "ERROR"]},
            "performance_mode": {"type": "string", "enum": ["high", "balanced", "power_save"]}
        },
        "required": ["click_delay", "operation_timeout", "retry_count"]
    }
    
    # UI偏好设置模式
    UI_PREFERENCES_SCHEMA = {
        "type": "object",
        "properties": {
            "theme": {"type": "string", "enum": ["light", "dark", "auto"]},
            "window_size": {
                "type": "object",
                "properties": {
                    "width": {"type": "integer", "minimum": 800},
                    "height": {"type": "integer", "minimum": 600}
                }
            },
            "window_position": {
                "type": "object",
                "properties": {
                    "x": {"type": "integer"},
                    "y": {"type": "integer"}
                }
            },
            "auto_save_interval": {"type": "integer", "minimum": 30, "maximum": 3600},
            "show_notifications": {"type": "boolean"},
            "minimize_to_tray": {"type": "boolean"},
            "language": {"type": "string"}
        }
    }
    
    # 任务配置模式
    TASK_CONFIG_SCHEMA = {
        "type": "object",
        "properties": {
            "max_concurrent_tasks": {"type": "integer", "minimum": 1, "maximum": 10},
            "task_timeout": {"type": "integer", "minimum": 60, "maximum": 3600},
            "auto_schedule": {"type": "boolean"},
            "priority_boost": {"type": "boolean"},
            "failure_retry_count": {"type": "integer", "minimum": 0, "maximum": 5},
            "task_history_limit": {"type": "integer", "minimum": 100, "maximum": 10000}
        }
    }
    
    # 性能配置模式
    PERFORMANCE_CONFIG_SCHEMA = {
        "type": "object",
        "properties": {
            "cpu_limit": {"type": "number", "minimum": 10.0, "maximum": 100.0},
            "memory_limit": {"type": "number", "minimum": 10.0, "maximum": 100.0},
            "image_cache_size": {"type": "integer", "minimum": 10, "maximum": 1000},
            "optimization_level": {"type": "string", "enum": ["none", "basic", "aggressive"]},
            "monitoring_interval": {"type": "number", "minimum": 1.0, "maximum": 60.0}
        }
    }
    
    @classmethod
    def get_schema(cls, config_type: ConfigType) -> Dict[str, Any]:
        """获取指定类型的配置模式"""
        schema_map = {
            ConfigType.GAME_SETTINGS: cls.GAME_SETTINGS_SCHEMA,
            ConfigType.AUTOMATION_CONFIG: cls.AUTOMATION_CONFIG_SCHEMA,
            ConfigType.UI_PREFERENCES: cls.UI_PREFERENCES_SCHEMA,
            ConfigType.TASK_CONFIG: cls.TASK_CONFIG_SCHEMA,
            ConfigType.PERFORMANCE_CONFIG: cls.PERFORMANCE_CONFIG_SCHEMA
        }
        return schema_map.get(config_type, {})


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_dir: str = "config", backup_dir: str = "config/backups"):
        self.config_dir = Path(config_dir)
        self.backup_dir = Path(backup_dir)
        
        # 确保目录存在
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # 配置缓存
        self.config_cache: Dict[ConfigType, Dict[str, Any]] = {}
        
        # 备份记录
        self.backup_records: List[ConfigBackup] = []
        self._load_backup_records()
        
        logger.info(f"配置管理器初始化完成，配置目录: {self.config_dir}")
    
    def export_config(self, config_type: ConfigType, config_data: Dict[str, Any], 
                     file_path: Optional[str] = None, 
                     include_metadata: bool = True) -> str:
        """导出配置到JSON文件"""
        try:
            # 验证配置
            validation_result = self.validate_config(config_type, config_data)
            if not validation_result.is_valid:
                logger.warning(f"配置验证失败，但仍将导出: {validation_result.errors}")
            
            # 确定文件路径
            if file_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                file_path = self.config_dir / f"{config_type.value}_{timestamp}.json"
            else:
                file_path = Path(file_path)
            
            # 准备导出数据
            export_data = {
                "config_type": config_type.value,
                "data": config_data
            }
            
            # 添加元数据
            if include_metadata:
                export_data["metadata"] = {
                    "export_time": datetime.now().isoformat(),
                    "version": "1.0",
                    "application": "星铁自动化助手",
                    "validation_result": {
                        "is_valid": validation_result.is_valid,
                        "error_count": len(validation_result.errors),
                        "warning_count": len(validation_result.warnings)
                    }
                }
            
            # 写入文件
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"配置已导出到: {file_path}")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"导出配置失败: {e}")
            raise
    
    def import_config(self, file_path: str, 
                     validation_level: ValidationLevel = ValidationLevel.NORMAL,
                     auto_backup: bool = True) -> Dict[str, Any]:
        """从JSON文件导入配置"""
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                raise FileNotFoundError(f"配置文件不存在: {file_path}")
            
            # 读取文件
            with open(file_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            # 检查文件格式
            if "config_type" not in import_data or "data" not in import_data:
                raise ValueError("无效的配置文件格式")
            
            config_type_str = import_data["config_type"]
            config_data = import_data["data"]
            
            # 解析配置类型
            try:
                config_type = ConfigType(config_type_str)
            except ValueError:
                raise ValueError(f"不支持的配置类型: {config_type_str}")
            
            # 验证配置
            validation_result = self.validate_config(config_type, config_data, validation_level)
            
            if validation_level == ValidationLevel.STRICT and not validation_result.is_valid:
                raise ValueError(f"配置验证失败: {validation_result.errors}")
            
            # 自动备份当前配置
            if auto_backup:
                current_config = self.get_config(config_type)
                if current_config:
                    self.create_backup(config_type, current_config, "导入前自动备份")
            
            # 缓存配置
            self.config_cache[config_type] = config_data
            
            # 保存到默认位置
            default_path = self.config_dir / f"{config_type.value}.json"
            self.export_config(config_type, config_data, str(default_path), include_metadata=True)
            
            logger.info(f"配置已导入: {config_type.value}")
            
            if validation_result.warnings:
                logger.warning(f"导入时发现警告: {validation_result.warnings}")
            
            return {
                "config_type": config_type.value,
                "data": config_data,
                "validation_result": validation_result,
                "metadata": import_data.get("metadata", {})
            }
            
        except Exception as e:
            logger.error(f"导入配置失败: {e}")
            raise
    
    def validate_config(self, config_type: ConfigType, config_data: Dict[str, Any],
                       validation_level: ValidationLevel = ValidationLevel.NORMAL) -> ConfigValidationResult:
        """验证配置数据"""
        errors = []
        warnings = []
        missing_fields = []
        invalid_values = {}
        suggestions = []
        
        try:
            # 获取配置模式
            schema = ConfigSchema.get_schema(config_type)
            if not schema:
                warnings.append(f"未找到配置类型 {config_type.value} 的验证模式")
                return ConfigValidationResult(
                    is_valid=True, errors=errors, warnings=warnings,
                    missing_fields=missing_fields, invalid_values=invalid_values,
                    suggestions=suggestions
                )
            
            # JSON Schema 验证
            try:
                validate(instance=config_data, schema=schema)
            except ValidationError as e:
                if validation_level == ValidationLevel.STRICT:
                    errors.append(f"模式验证失败: {e.message}")
                else:
                    warnings.append(f"模式验证警告: {e.message}")
            
            # 检查必需字段
            required_fields = schema.get("required", [])
            for field in required_fields:
                if field not in config_data:
                    missing_fields.append(field)
                    if validation_level != ValidationLevel.LOOSE:
                        errors.append(f"缺少必需字段: {field}")
            
            # 特定类型的验证
            self._validate_specific_config(config_type, config_data, errors, warnings, 
                                         invalid_values, suggestions, validation_level)
            
        except Exception as e:
            errors.append(f"验证过程出错: {str(e)}")
        
        is_valid = len(errors) == 0
        
        return ConfigValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            missing_fields=missing_fields,
            invalid_values=invalid_values,
            suggestions=suggestions
        )
    
    def _validate_specific_config(self, config_type: ConfigType, config_data: Dict[str, Any],
                                errors: List[str], warnings: List[str], 
                                invalid_values: Dict[str, str], suggestions: List[str],
                                validation_level: ValidationLevel):
        """特定配置类型的验证逻辑"""
        if config_type == ConfigType.GAME_SETTINGS:
            # 验证游戏路径
            game_path = config_data.get("game_path")
            if game_path and not os.path.exists(game_path):
                invalid_values["game_path"] = "游戏路径不存在"
                if validation_level == ValidationLevel.STRICT:
                    errors.append(f"游戏路径不存在: {game_path}")
                else:
                    warnings.append(f"游戏路径不存在: {game_path}")
                suggestions.append("请检查游戏安装路径是否正确")
        
        elif config_type == ConfigType.AUTOMATION_CONFIG:
            # 验证延迟设置
            click_delay = config_data.get("click_delay")
            if click_delay and click_delay < 0.1:
                invalid_values["click_delay"] = "点击延迟过短可能导致操作失败"
                warnings.append("建议点击延迟不少于0.1秒")
                suggestions.append("适当增加点击延迟可以提高操作成功率")
        
        elif config_type == ConfigType.PERFORMANCE_CONFIG:
            # 验证资源限制
            cpu_limit = config_data.get("cpu_limit")
            memory_limit = config_data.get("memory_limit")
            
            if cpu_limit and cpu_limit > 90:
                warnings.append("CPU限制过高可能影响系统稳定性")
                suggestions.append("建议CPU使用率限制在80%以下")
            
            if memory_limit and memory_limit > 90:
                warnings.append("内存限制过高可能影响系统稳定性")
                suggestions.append("建议内存使用率限制在85%以下")
    
    def create_backup(self, config_type: ConfigType, config_data: Dict[str, Any], 
                     description: str = "") -> str:
        """创建配置备份"""
        try:
            timestamp = datetime.now()
            backup_id = f"{config_type.value}_{timestamp.strftime('%Y%m%d_%H%M%S')}"
            backup_file = self.backup_dir / f"{backup_id}.json"
            
            # 准备备份数据
            backup_data = {
                "backup_id": backup_id,
                "config_type": config_type.value,
                "timestamp": timestamp.isoformat(),
                "description": description,
                "data": config_data
            }
            
            # 写入备份文件
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2)
            
            # 记录备份信息
            backup_info = ConfigBackup(
                backup_id=backup_id,
                timestamp=timestamp,
                config_type=config_type,
                file_path=str(backup_file),
                description=description,
                size=backup_file.stat().st_size
            )
            
            self.backup_records.append(backup_info)
            self._save_backup_records()
            
            logger.info(f"配置备份已创建: {backup_id}")
            return backup_id
            
        except Exception as e:
            logger.error(f"创建配置备份失败: {e}")
            raise
    
    def restore_backup(self, backup_id: str) -> Dict[str, Any]:
        """恢复配置备份"""
        try:
            # 查找备份记录
            backup_info = None
            for backup in self.backup_records:
                if backup.backup_id == backup_id:
                    backup_info = backup
                    break
            
            if not backup_info:
                raise ValueError(f"未找到备份: {backup_id}")
            
            # 读取备份文件
            backup_file = Path(backup_info.file_path)
            if not backup_file.exists():
                raise FileNotFoundError(f"备份文件不存在: {backup_file}")
            
            with open(backup_file, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
            
            config_data = backup_data["data"]
            config_type = ConfigType(backup_data["config_type"])
            
            # 创建当前配置的备份
            current_config = self.get_config(config_type)
            if current_config:
                self.create_backup(config_type, current_config, f"恢复前自动备份 (恢复到 {backup_id})")
            
            # 恢复配置
            self.config_cache[config_type] = config_data
            
            # 保存到默认位置
            default_path = self.config_dir / f"{config_type.value}.json"
            self.export_config(config_type, config_data, str(default_path))
            
            logger.info(f"配置已恢复: {backup_id}")
            return config_data
            
        except Exception as e:
            logger.error(f"恢复配置备份失败: {e}")
            raise
    
    def list_backups(self, config_type: Optional[ConfigType] = None) -> List[Dict[str, Any]]:
        """列出配置备份"""
        backups = self.backup_records
        
        if config_type:
            backups = [b for b in backups if b.config_type == config_type]
        
        return [
            {
                "backup_id": backup.backup_id,
                "config_type": backup.config_type.value,
                "timestamp": backup.timestamp.isoformat(),
                "description": backup.description,
                "size": backup.size,
                "file_path": backup.file_path
            }
            for backup in sorted(backups, key=lambda x: x.timestamp, reverse=True)
        ]
    
    def delete_backup(self, backup_id: str) -> bool:
        """删除配置备份"""
        try:
            # 查找备份记录
            backup_info = None
            for i, backup in enumerate(self.backup_records):
                if backup.backup_id == backup_id:
                    backup_info = backup
                    del self.backup_records[i]
                    break
            
            if not backup_info:
                logger.warning(f"未找到备份记录: {backup_id}")
                return False
            
            # 删除备份文件
            backup_file = Path(backup_info.file_path)
            if backup_file.exists():
                backup_file.unlink()
            
            self._save_backup_records()
            
            logger.info(f"配置备份已删除: {backup_id}")
            return True
            
        except Exception as e:
            logger.error(f"删除配置备份失败: {e}")
            return False
    
    def get_config(self, config_type: ConfigType) -> Optional[Dict[str, Any]]:
        """获取配置"""
        # 先检查缓存
        if config_type in self.config_cache:
            return self.config_cache[config_type]
        
        # 从文件加载
        config_file = self.config_dir / f"{config_type.value}.json"
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    file_data = json.load(f)
                
                config_data = file_data.get("data", file_data)
                self.config_cache[config_type] = config_data
                return config_data
                
            except Exception as e:
                logger.error(f"加载配置文件失败: {e}")
        
        return None
    
    def save_config(self, config_type: ConfigType, config_data: Dict[str, Any],
                   auto_backup: bool = True) -> bool:
        """保存配置"""
        try:
            # 验证配置
            validation_result = self.validate_config(config_type, config_data)
            if not validation_result.is_valid:
                logger.warning(f"配置验证失败，但仍将保存: {validation_result.errors}")
            
            # 自动备份
            if auto_backup:
                current_config = self.get_config(config_type)
                if current_config:
                    self.create_backup(config_type, current_config, "保存前自动备份")
            
            # 更新缓存
            self.config_cache[config_type] = config_data
            
            # 保存到文件
            config_file = self.config_dir / f"{config_type.value}.json"
            self.export_config(config_type, config_data, str(config_file))
            
            logger.info(f"配置已保存: {config_type.value}")
            return True
            
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
            return False
    
    def _load_backup_records(self):
        """加载备份记录"""
        records_file = self.backup_dir / "backup_records.json"
        if records_file.exists():
            try:
                with open(records_file, 'r', encoding='utf-8') as f:
                    records_data = json.load(f)
                
                for record in records_data:
                    backup = ConfigBackup(
                        backup_id=record["backup_id"],
                        timestamp=datetime.fromisoformat(record["timestamp"]),
                        config_type=ConfigType(record["config_type"]),
                        file_path=record["file_path"],
                        description=record["description"],
                        size=record["size"]
                    )
                    self.backup_records.append(backup)
                    
            except Exception as e:
                logger.error(f"加载备份记录失败: {e}")
    
    def _save_backup_records(self):
        """保存备份记录"""
        records_file = self.backup_dir / "backup_records.json"
        try:
            records_data = [
                {
                    "backup_id": backup.backup_id,
                    "timestamp": backup.timestamp.isoformat(),
                    "config_type": backup.config_type.value,
                    "file_path": backup.file_path,
                    "description": backup.description,
                    "size": backup.size
                }
                for backup in self.backup_records
            ]
            
            with open(records_file, 'w', encoding='utf-8') as f:
                json.dump(records_data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"保存备份记录失败: {e}")
    
    def cleanup_old_backups(self, max_backups_per_type: int = 10, max_age_days: int = 30):
        """清理旧备份"""
        try:
            current_time = datetime.now()
            
            # 按配置类型分组
            backups_by_type = {}
            for backup in self.backup_records:
                config_type = backup.config_type
                if config_type not in backups_by_type:
                    backups_by_type[config_type] = []
                backups_by_type[config_type].append(backup)
            
            deleted_count = 0
            
            for config_type, backups in backups_by_type.items():
                # 按时间排序（最新的在前）
                backups.sort(key=lambda x: x.timestamp, reverse=True)
                
                # 删除超过数量限制的备份
                if len(backups) > max_backups_per_type:
                    for backup in backups[max_backups_per_type:]:
                        if self.delete_backup(backup.backup_id):
                            deleted_count += 1
                
                # 删除超过时间限制的备份
                for backup in backups[:max_backups_per_type]:  # 只检查保留的备份
                    age = current_time - backup.timestamp
                    if age.days > max_age_days:
                        if self.delete_backup(backup.backup_id):
                            deleted_count += 1
            
            logger.info(f"清理完成，删除了 {deleted_count} 个旧备份")
            
        except Exception as e:
            logger.error(f"清理旧备份失败: {e}")
    
    def get_setting(self, config_type: ConfigType, key: str, default_value: Any = None) -> Any:
        """获取特定配置项的值"""
        try:
            config_data = self.get_config(config_type)
            if config_data is None:
                return default_value
            
            # 支持嵌套键（如 "section.subsection.key"）
            keys = key.split('.')
            value = config_data
            
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default_value
            
            return value
        except Exception as e:
            logger.error(f"获取配置项失败: {config_type.value}.{key}, 错误: {e}")
            return default_value
    
    def get_ui_config(self) -> Dict[str, Any]:
        """获取UI相关配置
        
        Returns:
            Dict[str, Any]: UI配置字典
        """
        ui_config = self.get_config(ConfigType.UI_PREFERENCES)
        if ui_config is None:
            # 返回默认UI配置
            return {
                'theme': 'dark',
                'language': 'zh_CN',
                'window_width': 1200,
                'window_height': 800,
                'remember_window_state': True,
                'auto_save': True,
                'show_tooltips': True
            }
        return ui_config
    
    def get_log_config(self) -> Dict[str, Any]:
        """获取日志配置
        
        Returns:
            Dict[str, Any]: 日志配置字典
        """
        try:
            log_config = self.get_config(ConfigType.SYSTEM_CONFIG)
            if log_config is None:
                # 返回默认日志配置
                return {
                    'level': 'INFO',
                    'format': '%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s',
                    'file_enabled': True,
                    'console_enabled': True,
                    'max_file_size': '10MB',
                    'backup_count': 5
                }
            return log_config.get('logging', {
                'level': 'INFO',
                'format': '%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s',
                'file_enabled': True,
                'console_enabled': True,
                'max_file_size': '10MB',
                'backup_count': 5
            })
        except Exception as e:
            logger.error(f"获取日志配置失败: {e}")
            return {
                'level': 'INFO',
                'format': '%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s',
                'file_enabled': True,
                'console_enabled': True,
                'max_file_size': '10MB',
                'backup_count': 5
            }
    
    def set_setting(self, config_type: ConfigType, key: str, value: Any, auto_save: bool = True) -> bool:
        """设置特定配置项的值"""
        try:
            config_data = self.get_config(config_type) or {}
            
            # 支持嵌套键（如 "section.subsection.key"）
            keys = key.split('.')
            current = config_data
            
            # 创建嵌套结构
            for k in keys[:-1]:
                if k not in current or not isinstance(current[k], dict):
                    current[k] = {}
                current = current[k]
            
            # 设置值
            current[keys[-1]] = value
            
            # 自动保存
            if auto_save:
                return self.save_config(config_type, config_data)
            else:
                self.config_cache[config_type] = config_data
                return True
                
        except Exception as e:
            logger.error(f"设置配置项失败 {config_type.value}.{key}: {e}")
            return False
    
    def get_config_summary(self) -> Dict[str, Any]:
        """获取配置摘要"""
        summary = {
            "config_types": [],
            "total_backups": len(self.backup_records),
            "backup_size_total": sum(b.size for b in self.backup_records),
            "last_backup_time": None
        }
        
        # 统计各类型配置
        for config_type in ConfigType:
            config_data = self.get_config(config_type)
            type_backups = [b for b in self.backup_records if b.config_type == config_type]
            
            type_info = {
                "type": config_type.value,
                "has_config": config_data is not None,
                "backup_count": len(type_backups),
                "last_backup": (
                    max(type_backups, key=lambda x: x.timestamp).timestamp.isoformat()
                    if type_backups else None
                )
            }
            summary["config_types"].append(type_info)
        
        # 最后备份时间
        if self.backup_records:
            latest_backup = max(self.backup_records, key=lambda x: x.timestamp)
            summary["last_backup_time"] = latest_backup.timestamp.isoformat()
        
        return summary
    
    def get_game_config(self) -> Dict[str, Any]:
        """获取游戏相关配置"""
        return {
            'resolution': self.get_setting(ConfigType.GAME_SETTINGS, 'resolution', '1920x1080'),
            'game_path': self.get_setting(ConfigType.GAME_SETTINGS, 'game_path', ''),
            'window_title': self.get_setting(ConfigType.GAME_SETTINGS, 'window_title', '崩坏：星穹铁道'),
            'detection_timeout': self.get_setting(ConfigType.GAME_SETTINGS, 'detection_timeout', 30)
        }
    
    def get_automation_config(self) -> Dict[str, Any]:
        """获取自动化相关配置"""
        return {
            'click_delay': self.get_setting(ConfigType.AUTOMATION_CONFIG, 'click_delay', 1.0),
            'detection_threshold': self.get_setting(ConfigType.AUTOMATION_CONFIG, 'detection_threshold', 0.8),
            'max_retry_count': self.get_setting(ConfigType.AUTOMATION_CONFIG, 'max_retry_count', 3),
            'operation_timeout': self.get_setting(ConfigType.AUTOMATION_CONFIG, 'operation_timeout', 60)
        }