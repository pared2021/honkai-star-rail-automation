"""日志模块.

提供统一的日志记录功能。
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime
import os


def get_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """获取日志记录器。
    
    Args:
        name: 日志记录器名称
        level: 日志级别，如果为None则使用环境变量或默认级别
        
    Returns:
        配置好的日志记录器
    """
    logger = logging.getLogger(name)
    
    # 如果已经配置过，直接返回
    if logger.handlers:
        return logger
    
    # 设置日志级别
    if level is None:
        level = os.getenv('XINGTIE_LOG_LEVEL', 'INFO')
    
    logger.setLevel(getattr(logging, level.upper()))
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    
    # 创建格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    
    # 添加处理器
    logger.addHandler(console_handler)
    
    # 创建文件处理器（如果指定了日志目录）
    log_dir = os.getenv('XINGTIE_LOG_DIR')
    if log_dir:
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
        
        # 创建日志文件名
        log_file = log_path / f"xingtie_{datetime.now().strftime('%Y%m%d')}.log"
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
    
    return logger


def setup_logging(level: str = 'INFO', log_dir: Optional[str] = None) -> None:
    """设置全局日志配置。
    
    Args:
        level: 日志级别
        log_dir: 日志目录，如果为None则不写入文件
    """
    # 设置环境变量
    os.environ['XINGTIE_LOG_LEVEL'] = level
    if log_dir:
        os.environ['XINGTIE_LOG_DIR'] = log_dir
    
    # 配置根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # 清除现有处理器
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 重新配置
    get_logger('xingtie')