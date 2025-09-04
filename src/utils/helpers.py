# -*- coding: utf-8 -*-
"""辅助工具函数 - 提供通用的工具函数."""

from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
from typing import Any, Dict, List, Optional, Tuple, Union

from loguru import logger


def get_project_root() -> Path:
    """获取项目根目录.

    Returns:
        Path: 项目根目录路径
    """
    current_file = Path(__file__)
    # 从当前文件向上查找，直到找到包含main.py的目录
    for parent in current_file.parents:
        if (parent / "main.py").exists():
            return parent

    # 如果没找到，返回当前文件的上三级目录
    return current_file.parent.parent.parent


def ensure_directory(path: Union[str, Path]) -> Path:
    """确保目录存在，如果不存在则创建.

    Args:
        path: 目录路径

    Returns:
        Path: 目录路径对象
    """
    path_obj = Path(path)
    path_obj.mkdir(parents=True, exist_ok=True)
    return path_obj


def safe_json_load(file_path: Union[str, Path], default: Any = None) -> Any:
    """安全地加载JSON文件.

    Args:
        file_path: JSON文件路径
        default: 加载失败时的默认值

    Returns:
        Any: JSON数据或默认值
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, Exception) as e:
        logger.warning(f"加载JSON文件失败 {file_path}: {e}")
        return default


def safe_json_save(data: Any, file_path: Union[str, Path], indent: int = 2) -> bool:
    """安全地保存JSON文件.

    Args:
        data: 要保存的数据
        file_path: JSON文件路径
        indent: 缩进空格数

    Returns:
        bool: 是否保存成功
    """
    try:
        # 确保目录存在
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=indent)
        return True
    except Exception as e:
        logger.error(f"保存JSON文件失败 {file_path}: {e}")
        return False


def get_file_hash(file_path: Union[str, Path], algorithm: str = "md5") -> Optional[str]:
    """计算文件哈希值.

    Args:
        file_path: 文件路径
        algorithm: 哈希算法 ('md5', 'sha1', 'sha256')

    Returns:
        str: 文件哈希值，失败返回None
    """
    try:
        hash_obj = hashlib.new(algorithm)
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()
    except Exception as e:
        logger.error(f"计算文件哈希失败 {file_path}: {e}")
        return None


def format_file_size(size_bytes: int) -> str:
    """格式化文件大小.

    Args:
        size_bytes: 字节数

    Returns:
        str: 格式化的文件大小
    """
    if size_bytes == 0:
        return "0 B"

    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1

    return f"{size_bytes:.1f} {size_names[i]}"


def format_duration(seconds: float) -> str:
    """格式化时间间隔.

    Args:
        seconds: 秒数

    Returns:
        str: 格式化的时间间隔
    """
    if seconds < 60:
        return f"{seconds:.1f}秒"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}分钟"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}小时"


def get_system_info() -> Dict[str, Any]:
    """获取系统信息.

    Returns:
        Dict: 系统信息
    """
    try:
        import psutil

        # 基本系统信息
        info = {
            "platform": platform.platform(),
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "python_executable": sys.executable,
        }

        # 内存信息
        memory = psutil.virtual_memory()
        info["memory"] = {
            "total": memory.total,
            "available": memory.available,
            "percent": memory.percent,
            "used": memory.used,
            "free": memory.free,
        }

        # CPU信息
        info["cpu"] = {
            "count": psutil.cpu_count(),
            "count_logical": psutil.cpu_count(logical=True),
            "percent": psutil.cpu_percent(interval=1),
        }

        # 磁盘信息
        disk = psutil.disk_usage("/")
        info["disk"] = {
            "total": disk.total,
            "used": disk.used,
            "free": disk.free,
            "percent": (disk.used / disk.total) * 100,
        }

        return info

    except ImportError:
        # 如果psutil不可用，返回基本信息
        return {
            "platform": platform.platform(),
            "system": platform.system(),
            "python_version": platform.python_version(),
        }
    except Exception as e:
        logger.error(f"获取系统信息失败: {e}")
        return {}


def is_admin() -> bool:
    """检查是否以管理员权限运行.

    Returns:
        bool: 是否为管理员权限
    """
    try:
        if platform.system() == "Windows":
            import ctypes

            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        else:
            return os.geteuid() == 0
    except Exception:
        return False


def run_command(
    command: Union[str, List[str]],
    cwd: Optional[Union[str, Path]] = None,
    timeout: Optional[float] = None,
    capture_output: bool = True,
) -> Tuple[int, str, str]:
    """运行系统命令.

    Args:
        command: 要执行的命令
        cwd: 工作目录
        timeout: 超时时间（秒）
        capture_output: 是否捕获输出

    Returns:
        Tuple[int, str, str]: (返回码, 标准输出, 标准错误)
    """
    try:
        if isinstance(command, str):
            shell = True
        else:
            shell = False

        result = subprocess.run(
            command,
            cwd=cwd,
            timeout=timeout,
            capture_output=capture_output,
            text=True,
            shell=shell,
        )

        return result.returncode, result.stdout or "", result.stderr or ""

    except subprocess.TimeoutExpired:
        logger.error(f"命令执行超时: {command}")
        return -1, "", "命令执行超时"
    except Exception as e:
        logger.error(f"命令执行失败 {command}: {e}")
        return -1, "", str(e)


def find_process_by_name(process_name: str) -> List[Dict[str, Any]]:
    """根据进程名查找进程.

    Args:
        process_name: 进程名

    Returns:
        List[Dict]: 进程信息列表
    """
    try:
        import psutil

        processes = []
        for proc in psutil.process_iter(["pid", "name", "exe", "cmdline"]):
            try:
                if process_name.lower() in proc.info["name"].lower():
                    processes.append(
                        {
                            "pid": proc.info["pid"],
                            "name": proc.info["name"],
                            "exe": proc.info["exe"],
                            "cmdline": proc.info["cmdline"],
                        }
                    )
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        return processes

    except ImportError:
        logger.warning("psutil模块未安装，无法查找进程")
        return []
    except Exception as e:
        logger.error(f"查找进程失败: {e}")
        return []


def kill_process_by_name(process_name: str) -> int:
    """根据进程名终止进程.

    Args:
        process_name: 进程名

    Returns:
        int: 终止的进程数量
    """
    try:
        import psutil

        killed_count = 0
        for proc in psutil.process_iter(["pid", "name"]):
            try:
                if process_name.lower() in proc.info["name"].lower():
                    proc.terminate()
                    killed_count += 1
                    logger.info(
                        f"终止进程: {proc.info['name']} (PID: {proc.info['pid']})"
                    )
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        return killed_count

    except ImportError:
        logger.warning("psutil模块未安装，无法终止进程")
        return 0
    except Exception as e:
        logger.error(f"终止进程失败: {e}")
        return 0


def validate_config(
    config: Dict[str, Any], schema: Dict[str, Any]
) -> Tuple[bool, List[str]]:
    """验证配置是否符合模式.

    Args:
        config: 要验证的配置
        schema: 配置模式

    Returns:
        Tuple[bool, List[str]]: (是否有效, 错误信息列表)
    """
    try:
        validator = ConfigValidator()
        errors = validator.validate(config, schema)
        return len(errors) == 0, errors
    except Exception as e:
        logger.error(f"配置验证失败: {e}")
        return False, [f"验证过程出错: {e}"]


class ConfigValidator:
    """配置验证器类."""

    def __init__(self):
        """初始化配置验证器."""
        self.errors = []

    def validate(self, config: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
        """验证配置.

        Args:
            config: 要验证的配置
            schema: 配置模式

        Returns:
            List[str]: 错误信息列表
        """
        self.errors = []
        self._validate_section(config, schema, "")
        return self.errors

    def _validate_value(self, value: Any, expected_type: str, path: str) -> None:
        """验证单个值的类型."""
        type_validators = {
            "string": lambda v: isinstance(v, str),
            "integer": lambda v: isinstance(v, int),
            "float": lambda v: isinstance(v, (int, float)),
            "boolean": lambda v: isinstance(v, bool),
            "list": lambda v: isinstance(v, list),
            "dict": lambda v: isinstance(v, dict),
        }

        validator = type_validators.get(expected_type)
        if validator and not validator(value):
            self.errors.append(f"{path}: 期望{expected_type}类型，实际为 {type(value).__name__}")

    def _validate_section(
        self, config_section: Dict[str, Any],
        schema_section: Dict[str, Any], path_prefix: str
    ) -> None:
        """验证配置段."""
        for key, expected_type in schema_section.items():
            current_path = f"{path_prefix}.{key}" if path_prefix else key

            if key not in config_section:
                self.errors.append(f"{current_path}: 缺少必需的配置项")
                continue

            if isinstance(expected_type, dict):
                self._validate_nested_dict(config_section[key], expected_type, current_path)
            else:
                self._validate_value(config_section[key], expected_type, current_path)

    def _validate_nested_dict(
        self, value: Any, expected_type: Dict[str, Any],
        current_path: str
    ) -> None:
        """验证嵌套字典."""
        if not isinstance(value, dict):
            self.errors.append(
                f"{current_path}: 期望字典类型，实际为 {type(value).__name__}"
            )
        else:
            self._validate_section(value, expected_type, current_path)


def create_backup(
    source_path: Union[str, Path],
    backup_dir: Optional[Union[str, Path]] = None,
    max_backups: int = 5,
) -> Optional[Path]:
    """创建文件或目录的备份.

    Args:
        source_path: 源文件或目录路径
        backup_dir: 备份目录，None表示在源文件同级目录
        max_backups: 最大备份数量

    Returns:
        Path: 备份文件路径，失败返回None
    """
    try:
        source_path = Path(source_path)

        if not source_path.exists():
            logger.error(f"源路径不存在: {source_path}")
            return None

        # 确定备份目录
        if backup_dir is None:
            backup_dir = source_path.parent / "backups"
        else:
            backup_dir = Path(backup_dir)

        ensure_directory(backup_dir)

        # 生成备份文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{source_path.name}_{timestamp}"
        backup_path = backup_dir / backup_name

        # 执行备份
        if source_path.is_file():
            import shutil

            shutil.copy2(source_path, backup_path)
        else:
            import shutil

            shutil.copytree(source_path, backup_path)

        logger.info(f"创建备份: {backup_path}")

        # 清理旧备份
        _cleanup_old_backups(backup_dir, source_path.name, max_backups)

        return backup_path

    except Exception as e:
        logger.error(f"创建备份失败: {e}")
        return None


def _cleanup_old_backups(backup_dir: Path, original_name: str, max_backups: int):
    """清理旧备份文件.

    Args:
        backup_dir: 备份目录
        original_name: 原始文件名
        max_backups: 最大备份数量
    """
    try:
        # 查找相关备份文件
        backup_files = []
        for backup_file in backup_dir.iterdir():
            if backup_file.name.startswith(original_name + "_"):
                backup_files.append(backup_file)

        # 按修改时间排序
        backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

        # 删除多余的备份
        for old_backup in backup_files[max_backups:]:
            try:
                if old_backup.is_file():
                    old_backup.unlink()
                else:
                    import shutil

                    shutil.rmtree(old_backup)
                logger.debug(f"删除旧备份: {old_backup}")
            except Exception as e:
                logger.warning(f"删除旧备份失败 {old_backup}: {e}")

    except Exception as e:
        logger.error(f"清理旧备份失败: {e}")


def retry_on_exception(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: Tuple = (Exception,),
):
    """重试装饰器.

    Args:
        max_retries: 最大重试次数
        delay: 初始延迟时间（秒）
        backoff_factor: 延迟倍增因子
        exceptions: 需要重试的异常类型
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(
                            f"函数 {func.__name__} 第{attempt + 1}次执行失败，{current_delay}秒后重试: {e}"
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff_factor
                    else:
                        logger.error(
                            f"函数 {func.__name__} 重试{max_retries}次后仍然失败: {e}"
                        )

            raise last_exception

        return wrapper

    return decorator
