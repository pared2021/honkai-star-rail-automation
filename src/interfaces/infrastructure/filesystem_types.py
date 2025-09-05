"""文件系统类型定义

定义文件系统相关的枚举和类型。
"""

from enum import Enum


class FileType(Enum):
    """文件类型枚举"""
    FILE = "file"
    DIRECTORY = "directory"
    SYMLINK = "symlink"
    UNKNOWN = "unknown"


class FilePermission(Enum):
    """文件权限枚举"""
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    READ_WRITE = "read_write"
    FULL = "full"