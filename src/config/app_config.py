"""应用程序配置模块.

提供应用程序的配置管理功能，包括默认配置、配置验证等。
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum

from .logger import get_logger
from .config_loader import ConfigLoader, ConfigFormat
from .config_manager import ConfigManager
from .database_config import DatabaseConfig, default_config as default_db_config


class LogLevel(Enum):
    """日志级别枚举。"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class UITheme(Enum):
    """UI主题枚举。"""
    LIGHT = "light"
    DARK = "dark"
    AUTO = "auto"


@dataclass
class UIConfig:
    """UI配置。"""
    theme: UITheme = UITheme.AUTO
    window_width: int = 1200
    window_height: int = 800
    window_x: Optional[int] = None
    window_y: Optional[int] = None
    maximized: bool = False
    always_on_top: bool = False
    show_tray_icon: bool = True
    minimize_to_tray: bool = True
    close_to_tray: bool = False
    auto_start: bool = False
    language: str = "zh_CN"
    font_family: str = "Microsoft YaHei"
    font_size: int = 9
    opacity: float = 1.0


@dataclass
class GameConfig:
    """游戏配置。"""
    game_path: Optional[str] = None
    auto_detect_game: bool = True
    detection_interval: int = 5  # 秒
    screenshot_interval: int = 1  # 秒
    action_delay: float = 0.1  # 秒
    retry_count: int = 3
    timeout: int = 30  # 秒
    enable_ocr: bool = True
    ocr_confidence: float = 0.8
    enable_image_match: bool = True
    image_match_threshold: float = 0.9


@dataclass
class AutomationConfig:
    """自动化配置。"""
    enabled: bool = False
    max_concurrent_tasks: int = 3
    task_timeout: int = 300  # 秒
    auto_pause_on_error: bool = True
    auto_resume_after_error: bool = False
    error_retry_count: int = 2
    error_retry_delay: int = 5  # 秒
    enable_safety_checks: bool = True
    safety_check_interval: int = 10  # 秒
    enable_performance_monitor: bool = True
    performance_check_interval: int = 30  # 秒


@dataclass
class LoggingConfig:
    """日志配置。"""
    level: LogLevel = LogLevel.INFO
    enable_file_logging: bool = True
    log_dir: Optional[str] = None
    max_log_files: int = 10
    max_log_size_mb: int = 10
    enable_console_logging: bool = True
    enable_debug_mode: bool = False
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format: str = "%Y-%m-%d %H:%M:%S"


@dataclass
class SecurityConfig:
    """安全配置。"""
    enable_encryption: bool = True
    encryption_key: Optional[str] = None
    enable_backup: bool = True
    backup_interval: int = 24  # 小时
    max_backup_files: int = 7
    backup_dir: Optional[str] = None
    enable_integrity_check: bool = True
    integrity_check_interval: int = 60  # 分钟


@dataclass
class PerformanceConfig:
    """性能配置。"""
    max_memory_usage_mb: int = 512
    max_cpu_usage_percent: int = 50
    enable_resource_monitor: bool = True
    resource_check_interval: int = 30  # 秒
    enable_gc_optimization: bool = True
    gc_threshold: int = 100
    enable_cache: bool = True
    cache_size_mb: int = 64
    cache_ttl: int = 3600  # 秒


@dataclass
class AppConfig:
    """应用程序配置。"""
    # 基本信息
    app_name: str = "星铁助手"
    app_version: str = "1.0.0"
    app_author: str = "XingTie Team"
    app_description: str = "崩坏：星穹铁道自动化助手"
    
    # 配置文件路径
    config_dir: Optional[str] = None
    data_dir: Optional[str] = None
    cache_dir: Optional[str] = None
    temp_dir: Optional[str] = None
    
    # 子配置
    ui: UIConfig = field(default_factory=UIConfig)
    game: GameConfig = field(default_factory=GameConfig)
    automation: AutomationConfig = field(default_factory=AutomationConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    database: DatabaseConfig = field(default_factory=lambda: default_db_config)
    
    # 其他配置
    debug_mode: bool = False
    first_run: bool = True
    last_update_check: Optional[str] = None
    user_agreement_accepted: bool = False
    
    def __post_init__(self):
        """初始化后处理。"""
        # 设置默认目录
        if self.config_dir is None:
            self.config_dir = str(Path.home() / ".xingtie" / "config")
        
        if self.data_dir is None:
            self.data_dir = str(Path.home() / ".xingtie" / "data")
        
        if self.cache_dir is None:
            self.cache_dir = str(Path.home() / ".xingtie" / "cache")
        
        if self.temp_dir is None:
            self.temp_dir = str(Path.home() / ".xingtie" / "temp")
        
        # 设置日志目录
        if self.logging.log_dir is None:
            self.logging.log_dir = str(Path(self.data_dir) / "logs")
        
        # 设置备份目录
        if self.security.backup_dir is None:
            self.security.backup_dir = str(Path(self.data_dir) / "backups")
        
        # 创建必要的目录
        self._create_directories()
    
    def _create_directories(self) -> None:
        """创建必要的目录。"""
        directories = [
            self.config_dir,
            self.data_dir,
            self.cache_dir,
            self.temp_dir,
            self.logging.log_dir,
            self.security.backup_dir
        ]
        
        for directory in directories:
            if directory:
                Path(directory).mkdir(parents=True, exist_ok=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典。
        
        Returns:
            配置字典
        """
        result = {}
        
        # 基本配置
        basic_fields = [
            'app_name', 'app_version', 'app_author', 'app_description',
            'config_dir', 'data_dir', 'cache_dir', 'temp_dir',
            'debug_mode', 'first_run', 'last_update_check', 'user_agreement_accepted'
        ]
        
        for field_name in basic_fields:
            result[field_name] = getattr(self, field_name)
        
        # 子配置
        result['ui'] = self._dataclass_to_dict(self.ui)
        result['game'] = self._dataclass_to_dict(self.game)
        result['automation'] = self._dataclass_to_dict(self.automation)
        result['logging'] = self._dataclass_to_dict(self.logging)
        result['security'] = self._dataclass_to_dict(self.security)
        result['performance'] = self._dataclass_to_dict(self.performance)
        result['database'] = self.database.to_dict()
        
        return result
    
    def _dataclass_to_dict(self, obj: Any) -> Dict[str, Any]:
        """将数据类转换为字典。
        
        Args:
            obj: 数据类对象
            
        Returns:
            字典
        """
        result = {}
        
        for field_name, field_value in obj.__dict__.items():
            if isinstance(field_value, Enum):
                result[field_name] = field_value.value
            else:
                result[field_name] = field_value
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AppConfig':
        """从字典创建配置。
        
        Args:
            data: 配置字典
            
        Returns:
            应用配置实例
        """
        # 创建子配置
        ui_data = data.get('ui', {})
        ui_config = UIConfig(
            theme=UITheme(ui_data.get('theme', UITheme.AUTO.value)),
            window_width=ui_data.get('window_width', 1200),
            window_height=ui_data.get('window_height', 800),
            window_x=ui_data.get('window_x'),
            window_y=ui_data.get('window_y'),
            maximized=ui_data.get('maximized', False),
            always_on_top=ui_data.get('always_on_top', False),
            show_tray_icon=ui_data.get('show_tray_icon', True),
            minimize_to_tray=ui_data.get('minimize_to_tray', True),
            close_to_tray=ui_data.get('close_to_tray', False),
            auto_start=ui_data.get('auto_start', False),
            language=ui_data.get('language', 'zh_CN'),
            font_family=ui_data.get('font_family', 'Microsoft YaHei'),
            font_size=ui_data.get('font_size', 9),
            opacity=ui_data.get('opacity', 1.0)
        )
        
        game_data = data.get('game', {})
        game_config = GameConfig(
            game_path=game_data.get('game_path'),
            auto_detect_game=game_data.get('auto_detect_game', True),
            detection_interval=game_data.get('detection_interval', 5),
            screenshot_interval=game_data.get('screenshot_interval', 1),
            action_delay=game_data.get('action_delay', 0.1),
            retry_count=game_data.get('retry_count', 3),
            timeout=game_data.get('timeout', 30),
            enable_ocr=game_data.get('enable_ocr', True),
            ocr_confidence=game_data.get('ocr_confidence', 0.8),
            enable_image_match=game_data.get('enable_image_match', True),
            image_match_threshold=game_data.get('image_match_threshold', 0.9)
        )
        
        automation_data = data.get('automation', {})
        automation_config = AutomationConfig(
            enabled=automation_data.get('enabled', False),
            max_concurrent_tasks=automation_data.get('max_concurrent_tasks', 3),
            task_timeout=automation_data.get('task_timeout', 300),
            auto_pause_on_error=automation_data.get('auto_pause_on_error', True),
            auto_resume_after_error=automation_data.get('auto_resume_after_error', False),
            error_retry_count=automation_data.get('error_retry_count', 2),
            error_retry_delay=automation_data.get('error_retry_delay', 5),
            enable_safety_checks=automation_data.get('enable_safety_checks', True),
            safety_check_interval=automation_data.get('safety_check_interval', 10),
            enable_performance_monitor=automation_data.get('enable_performance_monitor', True),
            performance_check_interval=automation_data.get('performance_check_interval', 30)
        )
        
        logging_data = data.get('logging', {})
        logging_config = LoggingConfig(
            level=LogLevel(logging_data.get('level', LogLevel.INFO.value)),
            enable_file_logging=logging_data.get('enable_file_logging', True),
            log_dir=logging_data.get('log_dir'),
            max_log_files=logging_data.get('max_log_files', 10),
            max_log_size_mb=logging_data.get('max_log_size_mb', 10),
            enable_console_logging=logging_data.get('enable_console_logging', True),
            enable_debug_mode=logging_data.get('enable_debug_mode', False),
            log_format=logging_data.get('log_format', "%(asctime)s - %(name)s - %(levelname)s - %(message)s"),
            date_format=logging_data.get('date_format', "%Y-%m-%d %H:%M:%S")
        )
        
        security_data = data.get('security', {})
        security_config = SecurityConfig(
            enable_encryption=security_data.get('enable_encryption', True),
            encryption_key=security_data.get('encryption_key'),
            enable_backup=security_data.get('enable_backup', True),
            backup_interval=security_data.get('backup_interval', 24),
            max_backup_files=security_data.get('max_backup_files', 7),
            backup_dir=security_data.get('backup_dir'),
            enable_integrity_check=security_data.get('enable_integrity_check', True),
            integrity_check_interval=security_data.get('integrity_check_interval', 60)
        )
        
        performance_data = data.get('performance', {})
        performance_config = PerformanceConfig(
            max_memory_usage_mb=performance_data.get('max_memory_usage_mb', 512),
            max_cpu_usage_percent=performance_data.get('max_cpu_usage_percent', 50),
            enable_resource_monitor=performance_data.get('enable_resource_monitor', True),
            resource_check_interval=performance_data.get('resource_check_interval', 30),
            enable_gc_optimization=performance_data.get('enable_gc_optimization', True),
            gc_threshold=performance_data.get('gc_threshold', 100),
            enable_cache=performance_data.get('enable_cache', True),
            cache_size_mb=performance_data.get('cache_size_mb', 64),
            cache_ttl=performance_data.get('cache_ttl', 3600)
        )
        
        database_data = data.get('database', {})
        database_config = DatabaseConfig.from_dict(database_data)
        
        # 创建主配置
        return cls(
            app_name=data.get('app_name', '星铁助手'),
            app_version=data.get('app_version', '1.0.0'),
            app_author=data.get('app_author', 'XingTie Team'),
            app_description=data.get('app_description', '崩坏：星穹铁道自动化助手'),
            config_dir=data.get('config_dir'),
            data_dir=data.get('data_dir'),
            cache_dir=data.get('cache_dir'),
            temp_dir=data.get('temp_dir'),
            ui=ui_config,
            game=game_config,
            automation=automation_config,
            logging=logging_config,
            security=security_config,
            performance=performance_config,
            database=database_config,
            debug_mode=data.get('debug_mode', False),
            first_run=data.get('first_run', True),
            last_update_check=data.get('last_update_check'),
            user_agreement_accepted=data.get('user_agreement_accepted', False)
        )
    
    def validate(self) -> List[str]:
        """验证配置。
        
        Returns:
            验证错误列表
        """
        errors = []
        
        # 验证基本配置
        if not self.app_name:
            errors.append("应用名称不能为空")
        
        if not self.app_version:
            errors.append("应用版本不能为空")
        
        # 验证UI配置
        if self.ui.window_width < 800:
            errors.append("窗口宽度不能小于800")
        
        if self.ui.window_height < 600:
            errors.append("窗口高度不能小于600")
        
        if not 0.1 <= self.ui.opacity <= 1.0:
            errors.append("窗口透明度必须在0.1到1.0之间")
        
        # 验证游戏配置
        if self.game.detection_interval < 1:
            errors.append("游戏检测间隔不能小于1秒")
        
        if self.game.screenshot_interval < 0.1:
            errors.append("截图间隔不能小于0.1秒")
        
        if not 0.0 <= self.game.ocr_confidence <= 1.0:
            errors.append("OCR置信度必须在0.0到1.0之间")
        
        if not 0.0 <= self.game.image_match_threshold <= 1.0:
            errors.append("图像匹配阈值必须在0.0到1.0之间")
        
        # 验证自动化配置
        if self.automation.max_concurrent_tasks < 1:
            errors.append("最大并发任务数不能小于1")
        
        if self.automation.task_timeout < 10:
            errors.append("任务超时时间不能小于10秒")
        
        # 验证性能配置
        if self.performance.max_memory_usage_mb < 128:
            errors.append("最大内存使用量不能小于128MB")
        
        if not 1 <= self.performance.max_cpu_usage_percent <= 100:
            errors.append("最大CPU使用率必须在1%到100%之间")
        
        return errors


# 默认配置实例
default_app_config = AppConfig()


class AppConfigManager:
    """应用配置管理器。"""
    
    def __init__(self, config_file: Optional[str] = None):
        """初始化配置管理器。
        
        Args:
            config_file: 配置文件路径
        """
        self.logger = get_logger(__name__)
        self._config: Optional[AppConfig] = None
        self._config_file = config_file or str(Path.home() / ".xingtie" / "config" / "app.json")
        self._config_manager = ConfigManager()
        self._config_loader = ConfigLoader()
    
    def load_config(self) -> AppConfig:
        """加载配置。
        
        Returns:
            应用配置
        """
        try:
            # 添加配置源
            self._config_loader.clear_sources()
            self._config_loader.add_source(
                self._config_file,
                format=ConfigFormat.JSON,
                required=False
            )
            
            # 加载配置
            result = self._config_loader.load_config()
            
            if result.success and result.data:
                self._config = AppConfig.from_dict(result.data)
            else:
                self.logger.warning("使用默认配置")
                self._config = AppConfig()
            
            # 验证配置
            errors = self._config.validate()
            if errors:
                self.logger.warning(f"配置验证失败: {errors}")
                # 使用默认配置
                self._config = AppConfig()
            
            return self._config
            
        except Exception as e:
            self.logger.error(f"加载配置失败: {e}")
            self._config = AppConfig()
            return self._config
    
    def save_config(self, config: Optional[AppConfig] = None) -> bool:
        """保存配置。
        
        Args:
            config: 要保存的配置，如果为None则保存当前配置
            
        Returns:
            是否保存成功
        """
        try:
            if config is None:
                config = self._config
            
            if config is None:
                self.logger.error("没有配置可保存")
                return False
            
            # 验证配置
            errors = config.validate()
            if errors:
                self.logger.error(f"配置验证失败: {errors}")
                return False
            
            # 确保配置目录存在
            config_dir = Path(self._config_file).parent
            config_dir.mkdir(parents=True, exist_ok=True)
            
            # 保存配置
            config_data = config.to_dict()
            self._config_manager.save_config(self._config_file, config_data)
            
            self._config = config
            self.logger.info(f"配置已保存到: {self._config_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"保存配置失败: {e}")
            return False
    
    def get_config(self) -> AppConfig:
        """获取当前配置。
        
        Returns:
            当前配置
        """
        if self._config is None:
            self._config = self.load_config()
        
        return self._config
    
    def update_config(self, **kwargs) -> bool:
        """更新配置。
        
        Args:
            **kwargs: 要更新的配置项
            
        Returns:
            是否更新成功
        """
        try:
            config = self.get_config()
            
            # 更新配置项
            for key, value in kwargs.items():
                if hasattr(config, key):
                    setattr(config, key, value)
                else:
                    self.logger.warning(f"未知的配置项: {key}")
            
            return self.save_config(config)
            
        except Exception as e:
            self.logger.error(f"更新配置失败: {e}")
            return False
    
    def reset_config(self) -> bool:
        """重置为默认配置。
        
        Returns:
            是否重置成功
        """
        try:
            self._config = AppConfig()
            return self.save_config(self._config)
            
        except Exception as e:
            self.logger.error(f"重置配置失败: {e}")
            return False
