# -*- coding: utf-8 -*-
"""
日志管理器 - 负责应用程序日志的配置和管理
"""

from datetime import datetime
import logging
from pathlib import Path
import sys
from typing import Optional

from loguru import logger


class InterceptHandler(logging.Handler):
    """拦截标准库日志并重定向到loguru"""

    def emit(self, record):
        # 获取对应的loguru级别
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # 查找调用者
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def setup_logger(log_dir: Optional[Path] = None, level: str = "INFO") -> logger:
    """设置日志系统

    Args:
        log_dir: 日志文件目录，默认为项目根目录下的logs文件夹
        level: 日志级别

    Returns:
        配置好的logger实例
    """
    if log_dir is None:
        project_root = Path(__file__).parent.parent.parent
        log_dir = project_root / "logs"

    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    # 移除默认处理器
    logger.remove()

    # 控制台输出格式
    console_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )

    # 文件输出格式
    file_format = (
        "{time:YYYY-MM-DD HH:mm:ss} | "
        "{level: <8} | "
        "{name}:{function}:{line} - "
        "{message}"
    )

    # 添加控制台处理器
    logger.add(
        sys.stdout,
        format=console_format,
        level=level,
        colorize=True,
        backtrace=True,
        diagnose=True,
    )

    # 添加文件处理器 - 所有日志
    logger.add(
        log_dir / "app_{time:YYYY-MM-DD}.log",
        format=file_format,
        level="DEBUG",
        rotation="1 day",
        retention="30 days",
        compression="zip",
        encoding="utf-8",
        backtrace=True,
        diagnose=True,
    )

    # 添加错误日志文件处理器
    logger.add(
        log_dir / "error_{time:YYYY-MM-DD}.log",
        format=file_format,
        level="ERROR",
        rotation="1 day",
        retention="90 days",
        compression="zip",
        encoding="utf-8",
        backtrace=True,
        diagnose=True,
    )

    # 添加自动化操作日志文件处理器
    logger.add(
        log_dir / "automation_{time:YYYY-MM-DD}.log",
        format=file_format,
        level="INFO",
        rotation="1 day",
        retention="7 days",
        compression="zip",
        encoding="utf-8",
        filter=lambda record: "automation" in record["extra"],
        backtrace=True,
        diagnose=True,
    )

    # 拦截标准库日志
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    # 设置第三方库日志级别
    for name in ["PyQt6", "urllib3", "requests"]:
        logging.getLogger(name).setLevel(logging.WARNING)

    logger.info("日志系统初始化完成")
    return logger


def get_automation_logger():
    """获取自动化操作专用logger"""
    return logger.bind(automation=True)


def log_function_call(func):
    """函数调用日志装饰器"""

    def wrapper(*args, **kwargs):
        logger.debug(f"调用函数: {func.__name__}, 参数: args={args}, kwargs={kwargs}")
        try:
            result = func(*args, **kwargs)
            logger.debug(f"函数 {func.__name__} 执行成功, 返回值: {result}")
            return result
        except Exception as e:
            logger.error(f"函数 {func.__name__} 执行失败: {e}")
            raise

    return wrapper


def log_automation_action(action_name: str, details: str = ""):
    """记录自动化操作日志

    Args:
        action_name: 操作名称
        details: 操作详情
    """
    automation_logger = get_automation_logger()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    automation_logger.info(f"[{timestamp}] {action_name}: {details}")


def log_game_state(state_info: dict):
    """记录游戏状态日志

    Args:
        state_info: 游戏状态信息字典
    """
    automation_logger = get_automation_logger()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    automation_logger.info(f"[{timestamp}] 游戏状态: {state_info}")


def get_logger(name: str = None):
    """获取logger实例

    Args:
        name: logger名称，可选

    Returns:
        logger实例
    """
    if name:
        return logger.bind(name=name)
    return logger


def log_error_with_context(error: Exception, context: str = ""):
    """记录带上下文的错误日志

    Args:
        error: 异常对象
        context: 错误上下文
    """
    logger.error(f"错误上下文: {context}")
    logger.exception(f"异常详情: {error}")
