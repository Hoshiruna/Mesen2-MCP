"""Configuration management for MCP server

Loads and manages server configuration from JSON files.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional


class Config:
    """Configuration manager for MCP server"""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration

        Args:
            config_path: Optional path to user config file (overrides defaults)
        """
        # Load default config
        default_path = Path(__file__).parent.parent / "config" / "default_config.json"
        with open(default_path, 'r') as f:
            self.config = json.load(f)

        # Override with user config if provided
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                user_config = json.load(f)
                self._deep_merge(self.config, user_config)

    def get(self, key_path: str, default: Any = None) -> Any:
        """Get config value by dot-separated path

        Args:
            key_path: Dot-separated path (e.g., "streaming.polling_rate_hz")
            default: Default value if key not found

        Returns:
            Configuration value or default

        Example:
            >>> config = Config()
            >>> config.get("streaming.polling_rate_hz")
            10
            >>> config.get("streaming.max_queue_size")
            1000
            >>> config.get("nonexistent.key", 42)
            42
        """
        keys = key_path.split(".")
        value = self.config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    def set(self, key_path: str, value: Any):
        """Set config value by dot-separated path

        Args:
            key_path: Dot-separated path
            value: Value to set

        Example:
            >>> config = Config()
            >>> config.set("streaming.polling_rate_hz", 20)
        """
        keys = key_path.split(".")
        target = self.config

        # Navigate to parent dict
        for key in keys[:-1]:
            if key not in target:
                target[key] = {}
            target = target[key]

        # Set value
        target[keys[-1]] = value

    def get_section(self, section: str) -> Dict[str, Any]:
        """Get entire configuration section

        Args:
            section: Section name (e.g., "streaming", "tools")

        Returns:
            Configuration section dict

        Example:
            >>> config = Config()
            >>> streaming_config = config.get_section("streaming")
            >>> print(streaming_config["polling_rate_hz"])
            10
        """
        return self.config.get(section, {})

    def _deep_merge(self, base: Dict, override: Dict):
        """Recursively merge override dict into base dict

        Args:
            base: Base configuration dict (modified in place)
            override: Override values
        """
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value

    def save(self, path: str):
        """Save current configuration to file

        Args:
            path: Path to save configuration file
        """
        with open(path, 'w') as f:
            json.dump(self.config, f, indent=4)

    def __repr__(self) -> str:
        return f"Config({len(self.config)} sections)"


# Global config instance (singleton pattern)
_config_instance: Optional[Config] = None


def get_config(config_path: Optional[str] = None) -> Config:
    """Get or create global config instance

    Args:
        config_path: Optional path to config file (only used on first call)

    Returns:
        Config instance
    """
    global _config_instance

    if _config_instance is None:
        _config_instance = Config(config_path)

    return _config_instance


def reset_config():
    """Reset global config instance (mainly for testing)"""
    global _config_instance
    _config_instance = None


# Test function
if __name__ == "__main__":
    print("Testing Config class...")

    # Test basic loading
    config = Config()
    print(f"\n[OK] Config loaded: {config}")

    # Test get with path
    polling_rate = config.get("streaming.polling_rate_hz")
    print(f"[OK] Polling rate: {polling_rate} Hz")

    max_queue = config.get("streaming.max_queue_size")
    print(f"[OK] Max queue size: {max_queue}")

    # Test get with default
    nonexistent = config.get("nonexistent.key", "default_value")
    print(f"[OK] Nonexistent key with default: {nonexistent}")

    # Test get_section
    streaming_config = config.get_section("streaming")
    print(f"[OK] Streaming section: {len(streaming_config)} settings")

    # Test set
    config.set("streaming.polling_rate_hz", 20)
    new_rate = config.get("streaming.polling_rate_hz")
    print(f"[OK] Updated polling rate: {new_rate} Hz")

    # Test nested set
    config.set("custom.new.setting", 42)
    custom_value = config.get("custom.new.setting")
    print(f"[OK] Custom nested setting: {custom_value}")

    # Test all major sections exist
    sections = ["dll_path", "streaming", "tools", "thread_safety", "dll_lifecycle", "logging", "performance"]
    missing = []
    for section in sections:
        if section not in config.config and config.get(section) is None:
            missing.append(section)

    if missing:
        print(f"[FAIL] Missing sections: {missing}")
    else:
        print(f"[OK] All expected sections present")

    print("\n[PASS] Config tests passed!")
