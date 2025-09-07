"""
Setup flow for Naim integration.

:copyright: (c) 2025 by Meir Miyara.
:license: Mozilla Public License Version 2.0, see LICENSE for more details.
"""

import asyncio
import logging
from enum import IntEnum
from typing import Any, Dict

import ucapi
from ucapi import AbortDriverSetup, DriverSetupRequest, RequestUserInput, SetupComplete, SetupDriver

from uc_intg_naim.config import Configuration, NaimDeviceConfig
from uc_intg_naim.client import NaimClient

_LOG = logging.getLogger(__name__)


class SetupSteps(IntEnum):
    """Setup flow steps."""
    INIT = 0
    CONFIGURATION_MODE = 1
    DEVICE_CHOICE = 2
    DEVICE_DISCOVERY = 3
    MANUAL_ENTRY = 4
    DEVICE_TEST = 5
    DEVICE_NAME = 6
    CONFIRMATION = 7


class NaimSetupFlow:
    """Handles the setup flow for Naim devices."""

    def __init__(self, config: Configuration):
        """Initialize setup flow."""
        self._config = config
        self._discovered_devices = []
        self._device_config: Dict[str, Any] = {}
        
    async def driver_setup_handler(self, msg: SetupDriver) -> RequestUserInput | SetupComplete | AbortDriverSetup:
        """Handle driver setup requests."""
        _LOG.debug("Setup handler called with message: %s", msg)
        
        try:
            step = msg.setup_data.get("step", SetupSteps.INIT)
            
            if step == SetupSteps.INIT:
                return await self._setup_initial_step()
            elif step == SetupSteps.CONFIGURATION_MODE:
                return await self._setup_configuration_mode(msg)
            elif step == SetupSteps.DEVICE_CHOICE:
                return await self._setup_device_choice(msg)
            elif step == SetupSteps.DEVICE_DISCOVERY:
                return await self._setup_device_discovery(msg)
            elif step == SetupSteps.MANUAL_ENTRY:
                return await self._setup_manual_entry(msg)
            elif step == SetupSteps.DEVICE_TEST:
                return await self._setup_device_test(msg)
            elif step == SetupSteps.DEVICE_NAME:
                return await self._setup_device_name(msg)
            elif step == SetupSteps.CONFIRMATION:
                return await self._setup_confirmation(msg)
            else:
                raise AbortDriverSetup("Invalid setup step")
                
        except Exception as e:
            _LOG.error("Setup error: %s", e)
            return AbortDriverSetup(f"Setup failed: {e}")
    
    async def _setup_initial_step(self) -> RequestUserInput:
        """Initial setup step - choose configuration mode."""
        return RequestUserInput(
            title="Naim Audio Device Setup",
            msg_id="configuration_mode",
            setup_data={"step": SetupSteps.CONFIGURATION_MODE},
            inputs=[
                ucapi.ui.Dropdown(
                    field_id="config_mode",
                    label="Configuration Mode",
                    value="discover",
                    options=[
                        ucapi.ui.DropdownOption("discover", "Auto-discover devices"),
                        ucapi.ui.DropdownOption("manual", "Manual device entry"),
                        ucapi.ui.DropdownOption("restore", "Restore from backup")
                    ]
                )
            ]
        )
    
    async def _setup_configuration_mode(self, msg: SetupDriver) -> RequestUserInput | AbortDriverSetup:
        """Handle configuration mode selection."""
        config_mode = msg.input_values.get("config_mode", "discover")
        
        if config_mode == "discover":
            return await self._setup_device_discovery_step()
        elif config_mode == "manual":
            return await self._setup_manual_entry_step()
        elif config_mode == "restore":
            return await self._setup_restore_step()
        else:
            raise AbortDriverSetup("Invalid configuration mode")
    
    async def _setup_device_discovery_step(self) -> RequestUserInput:
        """Start device discovery."""
        return RequestUserInput(
            title="Discovering Naim Devices",
            msg_id="device_discovery",
            setup_data={"step": SetupSteps.DEVICE_DISCOVERY},
            inputs=[
                ucapi.ui.Label(
                    field_id="discovery_info",
                    label="Searching for Naim devices on your network...\n\n"
                          "Make sure your Naim device is powered on and connected to the same network as your Remote."
                ),
                ucapi.ui.Button(
                    field_id="start_discovery",
                    label="Start Discovery"
                )
            ]
        )
    
    async def _setup_device_discovery(self, msg: SetupDriver) -> RequestUserInput:
        """Handle device discovery."""
        # Simulate device discovery (in real implementation, this would scan the network)
        await self._discover_devices()
        
        if not self._discovered_devices:
            return RequestUserInput(
                title="No Devices Found",
                msg_id="manual_entry",
                setup_data={"step": SetupSteps.MANUAL_ENTRY},
                inputs=[
                    ucapi.ui.Label(
                        field_id="no_devices_info",
                        label="No Naim devices were found on your network.\n\n"
                              "Please enter your device details manually."
                    ),
                    ucapi.ui.Text(
                        field_id="device_ip",
                        label="Device IP Address",
                        value="192.168.1.100"
                    ),
                    ucapi.ui.Number(
                        field_id="device_port",
                        label="Device Port",
                        value=80,
                        min_value=1,
                        max_value=65535
                    )
                ]
            )
        
        # Show discovered devices
        device_options = [
            ucapi.ui.DropdownOption(f"{device['ip']}:{device['port']}", f"{device['name']} ({device['ip']})")
            for device in self._discovered_devices
        ]
        
        return RequestUserInput(
            title="Select Naim Device",
            msg_id="device_choice",
            setup_data={"step": SetupSteps.DEVICE_CHOICE},
            inputs=[
                ucapi.ui.Dropdown(
                    field_id="selected_device",
                    label="Discovered Devices",
                    options=device_options
                ),
                ucapi.ui.Button(
                    field_id="manual_entry",
                    label="Enter Manually Instead"
                )
            ]
        )
    
    async def _setup_device_choice(self, msg: SetupDriver) -> RequestUserInput:
        """Handle device selection."""
        if "manual_entry" in msg.input_values:
            return await self._setup_manual_entry_step()
        
        selected_device = msg.input_values.get("selected_device", "")
        if not selected_device:
            raise AbortDriverSetup("No device selected")
        
        # Parse selected device
        ip, port = selected_device.split(":")
        device = next((d for d in self._discovered_devices if d["ip"] == ip and d["port"] == int(port)), None)
        
        if not device:
            raise AbortDriverSetup("Selected device not found")
        
        self._device_config = {
            "ip": device["ip"],
            "port": device["port"],
            "model": device.get("model", "Unknown"),
            "name": device["name"]
        }
        
        return await self._setup_device_test_step()
    
    async def _setup_manual_entry_step(self) -> RequestUserInput:
        """Manual device entry step."""
        return RequestUserInput(
            title="Enter Naim Device Details",
            msg_id="manual_entry",
            setup_data={"step": SetupSteps.MANUAL_ENTRY},
            inputs=[
                ucapi.ui.Text(
                    field_id="device_ip",
                    label="Device IP Address",
                    value="192.168.1.100"
                ),
                ucapi.ui.Number(
                    field_id="device_port",
                    label="Device Port",
                    value=80,
                    min_value=1,
                    max_value=65535
                )
            ]
        )
    
    async def _setup_manual_entry(self, msg: SetupDriver) -> RequestUserInput:
        """Handle manual device entry."""
        ip = msg.input_values.get("device_ip", "").strip()
        port = msg.input_values.get("device_port", 80)
        
        if not ip:
            raise AbortDriverSetup("IP address is required")
        
        self._device_config = {
            "ip": ip,
            "port": port,
            "model": "Unknown",
            "name": f"Naim Device ({ip})"
        }
        
        return await self._setup_device_test_step()
    
    async def _setup_device_test_step(self) -> RequestUserInput:
        """Test device connection step."""
        return RequestUserInput(
            title="Testing Device Connection",
            msg_id="device_test",
            setup_data={"step": SetupSteps.DEVICE_TEST},
            inputs=[
                ucapi.ui.Label(
                    field_id="test_info",
                    label=f"Testing connection to {self._device_config['ip']}:{self._device_config['port']}...\n\n"
                          "Please wait while we verify the device is accessible."
                ),
                ucapi.ui.Button(
                    field_id="test_connection",
                    label="Test Connection"
                )
            ]
        )
    
    async def _setup_device_test(self, msg: SetupDriver) -> RequestUserInput:
        """Handle device connection test."""
        ip = self._device_config["ip"]
        port = self._device_config["port"]
        
        # Test connection
        client = NaimClient(ip, port)
        try:
            success = await client.connect()
            if success:
                # Get device info
                status = await client.get_status()
                if status:
                    self._device_config["model"] = status.get("model", "Unknown")
                    self._device_config["name"] = status.get("device_name", f"Naim {self._device_config['model']}")
            await client.disconnect()
            
            if success:
                return await self._setup_device_name_step()
            else:
                raise AbortDriverSetup(f"Failed to connect to device at {ip}:{port}")
                
        except Exception as e:
            raise AbortDriverSetup(f"Connection test failed: {e}")
    
    async def _setup_device_name_step(self) -> RequestUserInput:
        """Device name configuration step."""
        return RequestUserInput(
            title="Device Configuration",
            msg_id="device_name",
            setup_data={"step": SetupSteps.DEVICE_NAME},
            inputs=[
                ucapi.ui.Text(
                    field_id="device_name",
                    label="Device Name",
                    value=self._device_config["name"]
                ),
                ucapi.ui.Checkbox(
                    field_id="standby_monitoring",
                    label="Enable standby monitoring",
                    value=True
                )
            ]
        )
    
    async def _setup_device_name(self, msg: SetupDriver) -> RequestUserInput:
        """Handle device name configuration."""
        device_name = msg.input_values.get("device_name", "").strip()
        standby_monitoring = msg.input_values.get("standby_monitoring", True)
        
        if not device_name:
            raise AbortDriverSetup("Device name is required")
        
        self._device_config["name"] = device_name
        self._device_config["standby_monitoring"] = standby_monitoring
        
        return await self._setup_confirmation_step()
    
    async def _setup_confirmation_step(self) -> RequestUserInput:
        """Confirmation step."""
        return RequestUserInput(
            title="Confirm Configuration",
            msg_id="confirmation",
            setup_data={"step": SetupSteps.CONFIRMATION},
            inputs=[
                ucapi.ui.Label(
                    field_id="config_summary",
                    label=f"Device Name: {self._device_config['name']}\n"
                          f"IP Address: {self._device_config['ip']}\n"
                          f"Port: {self._device_config['port']}\n"
                          f"Model: {self._device_config['model']}\n"
                          f"Standby Monitoring: {'Yes' if self._device_config['standby_monitoring'] else 'No'}"
                )
            ]
        )
    
    async def _setup_confirmation(self, msg: SetupDriver) -> SetupComplete:
        """Handle setup confirmation and completion."""
        # Create device configuration
        device_id = f"naim_{self._device_config['ip'].replace('.', '_')}_{self._device_config['port']}"
        device_config = NaimDeviceConfig(
            id=device_id,
            name=self._device_config["name"],
            address=self._device_config["ip"],
            port=self._device_config["port"],
            enabled=True,
            standby_monitoring=self._device_config["standby_monitoring"]
        )
        
        # Save configuration
        self._config.add_device(device_config)
        
        return SetupComplete()
    
    async def _setup_restore_step(self) -> RequestUserInput:
        """Backup/restore configuration step."""
        return RequestUserInput(
            title="Backup / Restore Configuration",
            msg_id="restore",
            setup_data={"step": SetupSteps.CONFIRMATION},
            inputs=[
                ucapi.ui.Textarea(
                    field_id="backup_restore_data",
                    label="Configuration Data (JSON)",
                    value=self._get_backup_data()
                )
            ]
        )
    
    async def _discover_devices(self) -> None:
        """Discover Naim devices on the network."""
        # Simulate device discovery
        # In a real implementation, this would scan the network for Naim devices
        self._discovered_devices = []
        
        # Common IP ranges to check
        base_ips = ["192.168.1.", "192.168.0.", "10.0.0.", "172.16.0."]
        common_ports = [80, 8080, 15081]
        
        # For simulation, add a fake device
        self._discovered_devices.append({
            "ip": "192.168.1.100",
            "port": 80,
            "name": "Naim Atom",
            "model": "Atom"
        })
    
    def _get_backup_data(self) -> str:
        """Get current configuration as backup data."""
        import json
        return json.dumps(self._config.config.to_dict(), indent=2)