"""核心配置管理器模块。.

提供核心系统的配置管理功能。
"""

from dataclasses import asdict, dataclass, field
from enum import Enum
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional


class ConfigType(Enum):
    """配置类型枚举。."""

    GAME = "game"
    UI = "ui"
    DETECTION = "detection"
    AUTOMATION = "automation"
    LOGGING = "logging"
    SYSTEM = "system"


@dataclass
class GameConfig:
    """游戏配置。."""

    window_title: str = "崩坏：星穹铁道"
    process_name: str = "StarRail.exe"
    screenshot_interval: float = 0.1
    detection_timeout: float = 10.0
    template_threshold: float = 0.8
    max_retries: int = 3


@dataclass
class UIConfig:
    """UI配置。."""

    template_dir: str = "templates"
    screenshot_dir: str = "screenshots"
    result_dir: str = "results"
    visualization_enabled: bool = True
    save_failed_detections: bool = True


@dataclass
class DetectionConfig:
    """检测配置."""

    confidence_threshold: float = 0.8
    template_matching_method: str = "TM_CCOEFF_NORMED"
    scale_factors: list = field(default_factory=lambda: [0.8, 0.9, 1.0, 1.1, 1.2])
    max_scale_iterations: int = 5
    roi_enabled: bool = False
    roi_coordinates: tuple = (0, 0, 0, 0)
    multi_scale_enabled: bool = True
    edge_detection_enabled: bool = False
    noise_reduction_enabled: bool = True


@dataclass
class AutomationConfig:
    """自动化配置。."""

    action_delay: float = 0.5
    click_delay: float = 0.1
    key_delay: float = 0.05
    scroll_delay: float = 0.2
    max_action_retries: int = 3
    safe_mode_enabled: bool = True


@dataclass
class LoggingConfig:
    """日志配置。."""

    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_enabled: bool = True
    console_enabled: bool = True
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5


@dataclass
class SystemConfig:
    """系统配置。."""

    work_dir: str = "."
    temp_dir: str = "temp"
    cache_enabled: bool = True
    cache_size: int = 100
    performance_mode: bool = False
    debug_mode: bool = False


class ConfigManager:
    """配置管理器。."""

    def __init__(self, config_file: str = "config.json"):
        """初始化配置管理器."""
        self.config_file = Path(config_file)
        self.logger = logging.getLogger(__name__)

        # 默认配置
        self._configs = {
            ConfigType.GAME: GameConfig(),
            ConfigType.UI: UIConfig(),
            ConfigType.DETECTION: DetectionConfig(),
            ConfigType.AUTOMATION: AutomationConfig(),
            ConfigType.LOGGING: LoggingConfig(),
            ConfigType.SYSTEM: SystemConfig(),
        }

        # 加载配置文件
        self.load_config()

    def get_config(self, config_type: ConfigType) -> Any:
        """获取指定类型的配置。."""
        return self._configs.get(config_type)

    def get_game_config(self) -> GameConfig:
        """获取游戏配置。."""
        config = self._configs[ConfigType.GAME]
        return config  # type: ignore

    def get_ui_config(self) -> UIConfig:
        """获取UI配置。."""
        config = self._configs[ConfigType.UI]
        return config  # type: ignore

    def get_detection_config(self) -> DetectionConfig:
        """获取检测配置。."""
        config = self._configs[ConfigType.DETECTION]
        return config  # type: ignore

    def get_automation_config(self) -> AutomationConfig:
        """获取自动化配置。."""
        config = self._configs[ConfigType.AUTOMATION]
        return config  # type: ignore

    def get_logging_config(self) -> LoggingConfig:
        """获取日志配置。."""
        config = self._configs[ConfigType.LOGGING]
        return config  # type: ignore

    def get_system_config(self) -> SystemConfig:
        """获取系统配置。."""
        config = self._configs[ConfigType.SYSTEM]
        return config  # type: ignore

    def set_config(self, config_type: ConfigType, config: Any) -> None:
        """设置指定类型的配置。."""
        self._configs[config_type] = config
        self.logger.debug(f"配置已更新: {config_type.value}")

    def update_config(self, config_type: ConfigType, **kwargs) -> None:
        """更新指定类型配置的部分字段。."""
        config = self._configs.get(config_type)
        if config:
            for key, value in kwargs.items():
                if hasattr(config, key):
                    setattr(config, key, value)
                    self.logger.debug(
                        f"配置字段已更新: {config_type.value}.{key} = {value}"
                    )
                else:
                    self.logger.warning(f"配置字段不存在: {config_type.value}.{key}")

    def load_config(self, config_file: Optional[str] = None) -> bool:
        """从文件加载配置。."""
        if config_file:
            self.config_file = Path(config_file)

        if not self.config_file.exists():
            self.logger.info(f"配置文件不存在，使用默认配置: {self.config_file}")
            return False

        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # 更新配置
            for config_type_str, config_data in data.items():
                try:
                    config_type = ConfigType(config_type_str)
                    current_config = self._configs[config_type]

                    # 更新配置对象的字段
                    for key, value in config_data.items():
                        if hasattr(current_config, key):
                            setattr(current_config, key, value)
                        else:
                            self.logger.warning(
                                f"未知配置字段: {config_type_str}.{key}"
                            )

                except ValueError:
                    self.logger.warning(f"未知配置类型: {config_type_str}")
                except Exception as e:
                    self.logger.error(f"加载配置失败 {config_type_str}: {e}")

            self.logger.info(f"配置加载成功: {self.config_file}")
            return True

        except Exception as e:
            self.logger.error(f"加载配置文件失败: {e}")
            return False

    def save_config(self, config_file: Optional[str] = None) -> bool:
        """保存配置到文件。."""
        if config_file:
            self.config_file = Path(config_file)

        try:
            # 确保目录存在
            self.config_file.parent.mkdir(parents=True, exist_ok=True)

            # 转换配置为字典
            data = {}
            for config_type, config_obj in self._configs.items():
                data[config_type.value] = asdict(config_obj)  # type: ignore

            # 保存到文件
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            self.logger.info(f"配置保存成功: {self.config_file}")
            return True

        except Exception as e:
            self.logger.error(f"保存配置文件失败: {e}")
            return False

    def get_value(self, config_type: ConfigType, key: str, default: Any = None) -> Any:
        """获取配置值。."""
        config = self._configs.get(config_type)
        if config and hasattr(config, key):
            return getattr(config, key)
        return default

    def set_value(self, config_type: ConfigType, key: str, value: Any) -> bool:
        """设置配置值。."""
        config = self._configs.get(config_type)
        if config and hasattr(config, key):
            setattr(config, key, value)
            self.logger.debug(f"配置值已设置: {config_type.value}.{key} = {value}")
            return True
        return False

    def reset_config(self, config_type: Optional[ConfigType] = None) -> None:
        """重置配置为默认值。."""
        if config_type is None:
            # 重置所有配置
            self._configs = {
                ConfigType.GAME: GameConfig(),
                ConfigType.UI: UIConfig(),
                ConfigType.DETECTION: DetectionConfig(),
                ConfigType.AUTOMATION: AutomationConfig(),
                ConfigType.LOGGING: LoggingConfig(),
                ConfigType.SYSTEM: SystemConfig(),
            }
            self.logger.info("所有配置已重置为默认值")
            return

        # 重置指定类型的配置
        config_classes = {
            ConfigType.GAME: GameConfig,
            ConfigType.UI: UIConfig,
            ConfigType.DETECTION: DetectionConfig,
            ConfigType.AUTOMATION: AutomationConfig,
            ConfigType.LOGGING: LoggingConfig,
            ConfigType.SYSTEM: SystemConfig,
        }

        if config_type in config_classes:
            self._configs[config_type] = config_classes[config_type]()
            self.logger.info(f"配置已重置: {config_type.value}")
        else:
            self.logger.warning(f"未知配置类型: {config_type}")

    def validate_config(self) -> Dict[str, list]:
        """验证配置的有效性。."""
        errors = {}

        # 验证游戏配置
        game_config = self.get_game_config()
        game_errors = []
        if game_config.screenshot_interval <= 0:
            game_errors.append("screenshot_interval必须大于0")
        if game_config.detection_timeout <= 0:
            game_errors.append("detection_timeout必须大于0")
        if not (0 < game_config.template_threshold <= 1):
            game_errors.append("template_threshold必须在0到1之间")
        if game_errors:
            errors[ConfigType.GAME.value] = game_errors

        # 验证检测配置
        detection_config = self.get_detection_config()
        detection_errors = []
        if not detection_config.scale_factors:
            detection_errors.append("scale_factors不能为空")
        if any(factor <= 0 for factor in detection_config.scale_factors):
            detection_errors.append("scale_factors中的值必须大于0")
        if detection_errors:
            errors[ConfigType.DETECTION.value] = detection_errors

        # 验证自动化配置
        automation_config = self.get_automation_config()
        automation_errors = []
        if automation_config.action_delay < 0:
            automation_errors.append("action_delay不能为负数")
        if automation_config.click_delay < 0:
            automation_errors.append("click_delay不能为负数")
        if automation_errors:
            errors[ConfigType.AUTOMATION.value] = automation_errors

        return errors

    def __str__(self) -> str:
        """字符串表示。."""
        return (
            f"ConfigManager(file={self.config_file}, " f"configs={len(self._configs)})"
        )

    def __repr__(self) -> str:
        """详细字符串表示。."""
        return self.__str__()
