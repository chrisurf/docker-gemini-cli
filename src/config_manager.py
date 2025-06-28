#!/usr/bin/env python3
"""
Configuration Manager for Gemini Autonomous Agent
Handles configuration loading and management
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import structlog
import yaml
from pydantic import BaseModel, Field

logger = structlog.get_logger()


class AgentConfig(BaseModel):
    """Agent configuration model"""

    gemini_api_key: str = Field(..., min_length=1)
    gemini_model: str = Field(default="gemini-pro")
    gemini_temperature: float = Field(default=0.7, ge=0.0, le=1.0)
    gemini_max_tokens: int = Field(default=2048, gt=0)
    log_level: str = Field(default="INFO")
    health_check_interval: int = Field(default=30)
    max_concurrent_tasks: int = Field(default=5)


class ConfigManager:
    """Manages application configuration"""

    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or "/app/config/config.yaml"
        self.config = self._load_config()

    def _load_config(self) -> AgentConfig:
        """Load configuration from environment and files"""
        config_data = {}

        # Load from YAML file if exists
        if Path(self.config_file).exists():
            try:
                with open(self.config_file, "r") as f:
                    file_config = yaml.safe_load(f) or {}
                config_data.update(file_config)
            except Exception as e:
                logger.warning("Failed to load config file", error=str(e))

        # Override with environment variables
        env_mapping = {
            "GEMINI_API_KEY": "gemini_api_key",
            "GEMINI_MODEL": "gemini_model",
            "GEMINI_TEMPERATURE": "gemini_temperature",
            "GEMINI_MAX_TOKENS": "gemini_max_tokens",
            "LOG_LEVEL": "log_level",
            "HEALTH_CHECK_INTERVAL": "health_check_interval",
            "MAX_CONCURRENT_TASKS": "max_concurrent_tasks",
        }

        for env_var, config_key in env_mapping.items():
            value = os.getenv(env_var)
            if value:
                # Convert types as needed
                if config_key in ["gemini_temperature"]:
                    value = float(value)
                elif config_key in [
                    "gemini_max_tokens",
                    "health_check_interval",
                    "max_concurrent_tasks",
                ]:
                    value = int(value)

                config_data[config_key] = value

        # Ensure required fields have defaults
        if "gemini_api_key" not in config_data:
            config_data["gemini_api_key"] = os.getenv("GEMINI_API_KEY", "")

        return AgentConfig(**config_data)

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return getattr(self.config, key, default)

    def get_all(self) -> Dict[str, Any]:
        """Get all configuration as dictionary"""
        return self.config.model_dump()

    def reload(self):
        """Reload configuration"""
        self.config = self._load_config()
        logger.info("Configuration reloaded")
