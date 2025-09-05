"""配置管理器模块.

提供配置的统一管理和访问接口。
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional


class ConfigManager:
    """配置管理器类，提供配置的统一管理和访问接口."""

    def __init__(self, config_file: Optional[str] = None):
        """初始化配置管理器.

        Args:
            config_file: 配置文件路径，默认为None
        """
        self._config_file = config_file or "config.json"
        self._config_data: Dict[str, Any] = {}
        self._load_config()

    def _load_config(self) -> None:
        """加载配置文件."""
        config_path = Path(self._config_file)
        if config_path.exists():
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    self._config_data = json.load(f)
            except (json.JSONDecodeError, IOError):
                self._config_data = {}
        else:
            self._config_data = {}

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值.

        Args:
            key: 配置键
            default: 默认值

        Returns:
            配置值或默认值
        """
        return self._config_data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """设置配置值.

        Args:
            key: 配置键
            value: 配置值
        """
        self._config_data[key] = value

    def save(self) -> None:
        """保存配置到文件."""
        config_path = Path(self._config_file)
        config_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(self._config_data, f, indent=2, ensure_ascii=False)
        except IOError:
            pass

    def reload(self) -> None:
        """重新加载配置文件."""
        self._load_config()

    def get_all(self) -> Dict[str, Any]:
        """获取所有配置.

        Returns:
            所有配置的字典
        """
        return self._config_data.copy()
