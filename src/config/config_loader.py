"""配置加载器模块.

提供配置文件的加载和解析功能，支持多种配置格式。
"""

import json
import yaml
import toml
import configparser
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
import os
from datetime import datetime

from .logger import get_logger


class ConfigFormat(Enum):
    """配置文件格式枚举。"""
    JSON = "json"
    YAML = "yaml"
    TOML = "toml"
    INI = "ini"
    ENV = "env"


@dataclass
class ConfigSource:
    """配置源信息。"""
    path: str
    format: ConfigFormat
    required: bool = True
    encoding: str = "utf-8"
    watch: bool = False
    last_modified: Optional[datetime] = None


@dataclass
class ConfigLoadResult:
    """配置加载结果。"""
    success: bool
    data: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    sources_loaded: List[str] = field(default_factory=list)
    load_time: Optional[datetime] = None


class ConfigLoader:
    """配置加载器。"""

    def __init__(self):
        """初始化配置加载器。"""
        self.logger = get_logger(__name__)
        self._sources: List[ConfigSource] = []
        self._cached_data: Dict[str, Any] = {}
        self._file_watchers: Dict[str, datetime] = {}

    def add_source(self, 
                   path: str, 
                   format: Optional[ConfigFormat] = None,
                   required: bool = True,
                   encoding: str = "utf-8",
                   watch: bool = False) -> None:
        """添加配置源。
        
        Args:
            path: 配置文件路径
            format: 配置格式，如果为None则根据文件扩展名自动检测
            required: 是否必需，如果为True且文件不存在会报错
            encoding: 文件编码
            watch: 是否监控文件变化
        """
        if format is None:
            format = self._detect_format(path)
        
        source = ConfigSource(
            path=path,
            format=format,
            required=required,
            encoding=encoding,
            watch=watch
        )
        
        self._sources.append(source)
        self.logger.info(f"添加配置源: {path} ({format.value})")

    def load_config(self) -> ConfigLoadResult:
        """加载所有配置源。
        
        Returns:
            配置加载结果
        """
        result = ConfigLoadResult(
            success=True,
            load_time=datetime.now()
        )
        
        merged_data = {}
        
        for source in self._sources:
            try:
                self.logger.debug(f"加载配置源: {source.path}")
                
                # 检查文件是否存在
                if not os.path.exists(source.path):
                    if source.required:
                        error_msg = f"必需的配置文件不存在: {source.path}"
                        result.errors.append(error_msg)
                        result.success = False
                        continue
                    else:
                        warning_msg = f"可选配置文件不存在: {source.path}"
                        result.warnings.append(warning_msg)
                        continue
                
                # 加载配置数据
                data = self._load_source(source)
                if data:
                    # 合并配置数据
                    merged_data = self._merge_config(merged_data, data)
                    result.sources_loaded.append(source.path)
                    
                    # 更新文件监控信息
                    if source.watch:
                        stat = os.stat(source.path)
                        source.last_modified = datetime.fromtimestamp(stat.st_mtime)
                        self._file_watchers[source.path] = source.last_modified
                
            except Exception as e:
                error_msg = f"加载配置源失败 {source.path}: {e}"
                result.errors.append(error_msg)
                self.logger.error(error_msg)
                
                if source.required:
                    result.success = False
        
        # 处理环境变量覆盖
        env_overrides = self._load_env_overrides()
        if env_overrides:
            merged_data = self._merge_config(merged_data, env_overrides)
            result.sources_loaded.append("environment_variables")
        
        result.data = merged_data
        self._cached_data = merged_data.copy()
        
        if result.success:
            self.logger.info(f"配置加载成功，共加载 {len(result.sources_loaded)} 个源")
        else:
            self.logger.error(f"配置加载失败，错误数: {len(result.errors)}")
        
        return result

    def reload_if_changed(self) -> Optional[ConfigLoadResult]:
        """如果文件有变化则重新加载配置。
        
        Returns:
            如果有变化则返回加载结果，否则返回None
        """
        changed_files = []
        
        for path, last_modified in self._file_watchers.items():
            if os.path.exists(path):
                stat = os.stat(path)
                current_modified = datetime.fromtimestamp(stat.st_mtime)
                
                if current_modified > last_modified:
                    changed_files.append(path)
        
        if changed_files:
            self.logger.info(f"检测到配置文件变化: {changed_files}")
            return self.load_config()
        
        return None

    def get_cached_data(self) -> Dict[str, Any]:
        """获取缓存的配置数据。
        
        Returns:
            缓存的配置数据
        """
        return self._cached_data.copy()

    def _detect_format(self, path: str) -> ConfigFormat:
        """根据文件扩展名检测配置格式。
        
        Args:
            path: 文件路径
            
        Returns:
            配置格式
        """
        ext = Path(path).suffix.lower()
        
        if ext in [".json"]:
            return ConfigFormat.JSON
        elif ext in [".yaml", ".yml"]:
            return ConfigFormat.YAML
        elif ext in [".toml"]:
            return ConfigFormat.TOML
        elif ext in [".ini", ".cfg", ".conf"]:
            return ConfigFormat.INI
        else:
            # 默认使用JSON格式
            return ConfigFormat.JSON

    def _load_source(self, source: ConfigSource) -> Optional[Dict[str, Any]]:
        """加载单个配置源。
        
        Args:
            source: 配置源
            
        Returns:
            配置数据
        """
        try:
            with open(source.path, 'r', encoding=source.encoding) as f:
                content = f.read()
            
            if source.format == ConfigFormat.JSON:
                return json.loads(content)
            elif source.format == ConfigFormat.YAML:
                return yaml.safe_load(content)
            elif source.format == ConfigFormat.TOML:
                return toml.loads(content)
            elif source.format == ConfigFormat.INI:
                parser = configparser.ConfigParser()
                parser.read_string(content)
                return {section: dict(parser[section]) for section in parser.sections()}
            else:
                raise ValueError(f"不支持的配置格式: {source.format}")
                
        except Exception as e:
            self.logger.error(f"解析配置文件失败 {source.path}: {e}")
            raise

    def _load_env_overrides(self) -> Dict[str, Any]:
        """加载环境变量覆盖。
        
        Returns:
            环境变量配置数据
        """
        env_data = {}
        
        # 查找以XINGTIE_开头的环境变量
        for key, value in os.environ.items():
            if key.startswith("XINGTIE_"):
                # 移除前缀并转换为小写
                config_key = key[8:].lower()
                
                # 尝试转换值类型
                try:
                    # 尝试解析为JSON
                    env_data[config_key] = json.loads(value)
                except json.JSONDecodeError:
                    # 如果不是JSON，则作为字符串处理
                    # 处理布尔值
                    if value.lower() in ['true', 'false']:
                        env_data[config_key] = value.lower() == 'true'
                    # 处理数字
                    elif value.isdigit():
                        env_data[config_key] = int(value)
                    elif value.replace('.', '', 1).isdigit():
                        env_data[config_key] = float(value)
                    else:
                        env_data[config_key] = value
        
        return env_data

    def _merge_config(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """合并配置数据。
        
        Args:
            base: 基础配置
            override: 覆盖配置
            
        Returns:
            合并后的配置
        """
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                # 递归合并字典
                result[key] = self._merge_config(result[key], value)
            else:
                # 直接覆盖
                result[key] = value
        
        return result

    def clear_sources(self) -> None:
        """清除所有配置源。"""
        self._sources.clear()
        self._file_watchers.clear()
        self.logger.info("已清除所有配置源")

    def get_sources(self) -> List[ConfigSource]:
        """获取所有配置源。
        
        Returns:
            配置源列表
        """
        return self._sources.copy()
