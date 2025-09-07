"""
Configuration management for Naim integration.

:copyright: (c) 2025 by Meir Miyara.
:license: Mozilla Public License Version 2.0, see LICENSE for more details.
"""

import json
import logging
import os
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

_LOG = logging.getLogger(__name__)


@dataclass
class NaimDeviceConfig:
    """Configuration for a single Naim device."""
    
    id: str
    name: str
    address: str
    port: int = 80
    enabled: bool = True
    standby_monitoring: bool = True


@dataclass
class NaimConfig:
    """Global Naim integration configuration."""
    
    devices: Dict[str, NaimDeviceConfig] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NaimConfig":
        """Create config from dictionary."""
        devices = {}
        for device_id, device_data in data.get("devices", {}).items():
            devices[device_id] = NaimDeviceConfig(
                id=device_id,
                name=device_data.get("name", ""),
                address=device_data.get("address", ""),
                port=device_data.get("port", 80),
                enabled=device_data.get("enabled", True),
                standby_monitoring=device_data.get("standby_monitoring", True)
            )
        
        return cls(devices=devices)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "devices": {
                device_id: {
                    "name": device.name,
                    "address": device.address,
                    "port": device.port,
                    "enabled": device.enabled,
                    "standby_monitoring": device.standby_monitoring
                }
                for device_id, device in self.devices.items()
            }
        }


class Configuration:
    """Manages configuration file operations."""
    
    def __init__(self):
        """Initialize configuration manager."""
        # Use environment variable or default to current directory
        config_dir = os.environ.get("UC_CONFIG_HOME", os.getcwd())
        self._config_path = os.path.join(config_dir, "config.json")
        self._config:"""
Configuration management for Naim integration.

:copyright: (c) 2025 by Meir Miyara.
:license: Mozilla Public License Version 2.0, see LICENSE for more details.
"""

import json
import logging
import os
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

_LOG = logging.getLogger(__name__)


@dataclass
class NaimDeviceConfig:
    """Configuration for a single Naim device."""
    
    id: str
    name: str
    address: str
    port: int = 80
    enabled: bool = True
    standby_monitoring: bool = True


@dataclass
class NaimConfig:
    """Global Naim integration configuration."""
    
    devices: Dict[str, NaimDeviceConfig] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NaimConfig":
        """Create config from dictionary."""
        devices = {}
        for device_id, device_data in data.get("devices", {}).items():
            devices[device_id] = NaimDeviceConfig(
                id=device_id,
                name=device_data.get("name", ""),
                address=device_data.get("address", ""),
                port=device_data.get("port", 80),
                enabled=device_data.get("enabled", True),
                standby_monitoring=device_data.get("standby_monitoring", True)
            )
        
        return cls(devices=devices)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "devices": {
                device_id: {
                    "name": device.name,
                    "address": device.address,
                    "port": device.port,
                    "enabled": device.enabled,
                    "standby_monitoring": device.standby_monitoring
                }
                for device_id, device in self.devices.items()
            }
        }


class Configuration:
    """Manages configuration file operations."""
    
    def __init__(self):
        """Initialize configuration manager."""
        # Use environment variable or default to current directory
        config_dir = os.environ.get("UC_CONFIG_HOME", os.getcwd())
        self._config_path = os.path.join(config_dir, "config.json")
        self._config: Optional[NaimConfig] = None
    
    @property
    def config(self) -> NaimConfig:
        """Get current configuration."""
        if self._config is None:
            self.load()
        return self._config
    
    def load(self) -> None:
        """Load configuration from file."""
        try:
            if os.path.exists(self._config_path):
                with open(self._config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self._config = NaimConfig.from_dict(data)
                _LOG.info("Configuration loaded from %s", self._config_path)
            else:
                _LOG.info("No configuration file found, using defaults")
                self._config = NaimConfig()
        except Exception as e:
            _LOG.error("Error loading configuration: %s", e)
            self._config = NaimConfig()
    
    def save(self) -> None:
        """Save configuration to file."""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self._config_path), exist_ok=True)
            
            with open(self._config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config.to_dict(), f, indent=2)
            _LOG.info("Configuration saved to %s", self._config_path)
        except Exception as e:
            _LOG.error("Error saving configuration: %s", e)
    
    def add_device(self, device_config: NaimDeviceConfig) -> None:
        """Add a device to configuration."""
        self._config.devices[device_config.id] = device_config
        self.save()
    
    def remove_device(self, device_id: str) -> None:
        """Remove a device from configuration."""
        if device_id in self._config.devices:
            del self._config.devices[device_id]
            self.save()
    
    def update_device(self, device_config: NaimDeviceConfig) -> None:
        """Update device configuration."""
        self._config.devices[device_config.id] = device_config
        self.save()