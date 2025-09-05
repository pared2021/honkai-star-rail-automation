"""配置管理类型定义

定义配置管理相关的枚举、异常和类型。
"""

from enum import Enum


class ConfigurationSource(Enum):
    """配置源类型"""
    FILE = "file"                    # 文件配置
    ENVIRONMENT = "environment"      # 环境变量
    COMMAND_LINE = "command_line"    # 命令行参数
    DATABASE = "database"            # 数据库配置
    REMOTE = "remote"                # 远程配置
    MEMORY = "memory"                # 内存配置


class ConfigurationFormat(Enum):
    """配置文件格式"""
    JSON = "json"
    YAML = "yaml"
    INI = "ini"
    TOML = "toml"
    XML = "xml"
    PROPERTIES = "properties"


class ConfigurationException(Exception):
    """配置异常"""
    pass


class ConfigurationValidationException(ConfigurationException):
    """配置验证异常"""
    pass


class ConfigurationNotFoundException(ConfigurationException):
    """配置未找到异常"""