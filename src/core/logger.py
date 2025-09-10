"""核心日志模块.

提供核心系统的日志功能。
"""

import logging
import sys
from pathlib import Path
from loguru import logger


def setup_logger(log_level: str = "INFO") -> logging.Logger:
    """设置日志系统.
    
    Args:
        log_level: 日志级别，默认为INFO
        
    Returns:
        配置好的logger实例
    """
    # 创建logs目录
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # 移除默认的loguru处理器
    logger.remove()
    
    # 添加控制台输出
    logger.add(
        sys.stderr,
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )
    
    # 添加文件输出
    logger.add(
        log_dir / "app.log",
        level=log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="10 MB",
        retention="7 days",
        compression="zip"
    )
    
    # 添加错误日志文件
    logger.add(
        log_dir / "error.log",
        level="ERROR",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="10 MB",
        retention="30 days",
        compression="zip"
    )
    
    return logger


def get_logger(name: str = None):
    """获取logger实例。
    
    Args:
        name: logger名称
        
    Returns:
        logger实例
    """
    if name:
        return logger.bind(name=name)
    return logger
