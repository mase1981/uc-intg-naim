#!/usr/bin/env python3
"""
Naim audio integration driver for Unfolded Circle Remote

:copyright: (c) 2025 by Meir Miyara.
:license: Mozilla Public License Version 2.0, see LICENSE for more details.
"""

import asyncio
import logging
import os
import sys
from typing import Any, Dict, List, Optional

import ucapi
from ucapi import DeviceStates, Events, IntegrationSetupError, SetupComplete, SetupError, RequestUserInput, UserDataResponse

from uc_intg_naim.config import Configuration, NaimDeviceConfig
from uc_intg_naim.client import NaimClient
from uc_intg_naim.media_player import NaimMediaPlayer
from uc_intg_naim.remote import NaimRemote

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

_LOG = logging.getLogger(__name__)

# Global variables
api: Optional[ucapi.IntegrationAPI] = None
config: Optional[Configuration] = None
clients: Dict[str, NaimClient] = {}
media_players: Dict[str, NaimMediaPlayer] = {}
remotes: Dict[str, NaimRemote] = {}

entities_ready = False
initialization_lock = asyncio.Lock()

# Multi-device setup state
setup_state = {"step": "initial", "device_count": 1, "devices_data": []}


async def _initialize_integration():
    """Initialize integration entities - called during startup if already configured."""
    global config, api, clients, media_players, remotes, entities_ready
    
    async with initialization_lock:
        if entities_ready:
            _LOG.debug("Entities already initialized")
            return
            
        if not config or not config.config.devices:
            _LOG.info("No devices configured, skipping initialization")
            return

        _LOG.info("Pre-initializing entities for %d configured devices", len(config.config.devices))
        await api.set_device_state(DeviceStates.CONNECTING)
        
        connected_devices = 0
        
        for device_id, device_config in config.config.devices.items():
            if not device_config.enabled:
                _LOG.info("Skipping disabled device: %s", device_config.name)
                continue
                
            _LOG.info("Connecting to Naim device: %s at %s:%s", device_config.name, device_config.address, device_config.port)
            
            try:
                # Create client
                client = NaimClient(device_config.address, device_config.port)
                
                if not await client.connect():
                    _LOG.error("Failed to connect to Naim device %s at %s:%s", device_config.name, device_config.address, device_config.port)
                    await client.disconnect()
                    continue

                # Try to get device info, but don't fail if not available
                device_info = await client.get_system_info()
                if device_info:
                    device_model = device_info.get('model', 'Unknown')
                    device_hostname = device_info.get('hostname', device_config.name)
                    _LOG.info("Connected to Naim %s: %s", device_model, device_hostname)
                else:
                    _LOG.warning("Could not get system info, but connection successful")
                    
                # Create entities with unique IDs for multi-device support
                media_player_id = f"naim_{device_id}"
                remote_id = f"naim_remote_{device_id}"
                
                media_player = NaimMediaPlayer(device_config, entity_id=media_player_id)
                remote = NaimRemote(device_config, entity_id=remote_id)
                
                media_player._integration_api = api
                remote._integration_api = api
                
                # Connect entities
                if await media_player.connect() and await remote.connect():
                    # Store references
                    clients[device_id] = client
                    media_players[device_id] = media_player
                    remotes[device_id] = remote
                    
                    api.available_entities.add(media_player)
                    api.available_entities.add(remote)
                    
                    connected_devices += 1
                    _LOG.info("Successfully setup device: %s", device_config.name)
                else:
                    _LOG.error("Failed to connect entities for device: %s", device_config.name)
                    await media_player.disconnect()
                    await remote.disconnect()
                    await client.disconnect()
                    
            except Exception as e:
                _LOG.error("Failed to setup device %s: %s", device_config.name, e, exc_info=True)
                continue
        
        if connected_devices > 0:
            entities_ready = True
            await api.set_device_state(DeviceStates.CONNECTED)
            _LOG.info("Naim integration pre-initialization completed - %d/%d devices connected", connected_devices, len(config.config.devices))
        else:
            await api.set_device_state(DeviceStates.ERROR)
            _LOG.error("No devices could be connected during pre-initialization")


async def setup_handler(msg: ucapi.SetupDriver) -> ucapi.SetupAction:
    """Enhanced setup handler for multi-device support."""
    global config, entities_ready, setup_state
    
    if isinstance(msg, ucapi.DriverSetupRequest):
        # Initial setup - check if single or multi-device
        device_count = int(msg.setup_data.get("device_count", 1))
        
        if device_count == 1:
            # Single device - use existing simple flow
            return await _handle_single_device_setup(msg.setup_data)
        else:
            # Multi-device setup
            setup_state = {"step": "collect_ips", "device_count": device_count, "devices_data": []}
            return await _request_device_ips(device_count)
    
    elif isinstance(msg, ucapi.UserDataResponse):
        if setup_state["step"] == "collect_ips":
            return await _handle_device_ips_collection(msg.input_values)
    
    return SetupError(IntegrationSetupError.OTHER)


async def _handle_single_device_setup(setup_data: Dict[str, Any]) -> ucapi.SetupAction:
    """Handle single device setup (existing flow)."""
    host_input = setup_data.get("host")
    if not host_input:
        _LOG.error("No host provided in setup data")
        return SetupError(IntegrationSetupError.OTHER)
    
    # Parse host:port format
    try:
        if ':' in host_input:
            host, port_str = host_input.split(':', 1)
            port = int(port_str)
        else:
            host = host_input
            port = 15081  # Default Naim port
    except ValueError:
        _LOG.error("Invalid host:port format: %s", host_input)
        return SetupError(IntegrationSetupError.OTHER)
        
    _LOG.info("Testing connection to Naim device at %s:%s", host, port)
    
    try:
        test_client = NaimClient(host, port)
        if not await test_client.connect():
            _LOG.error("Connection test failed for host: %s:%s", host, port)
            await test_client.disconnect()
            return SetupError(IntegrationSetupError.CONNECTION_REFUSED)
        
        # Try to get device info, but don't fail setup if not available
        device_info = await test_client.get_system_info()
        device_name = host  # fallback name
        
        if device_info:
            device_name = device_info.get('hostname', f'Naim Device ({host})')
            _LOG.info("Device info: %s", device_info.get('hostname', 'Unknown'))
        else:
            _LOG.warning("Could not get device information, but connection successful")
            device_name = f"Naim Device ({host})"
        
        await test_client.disconnect()
        
        # Create device configuration
        device_id = f"naim_{host.replace('.', '_')}_{port}"
        
        device_config = NaimDeviceConfig(
            id=device_id,
            name=device_name,
            address=host,
            port=port,
            enabled=True,
            standby_monitoring=True
        )
        
        # Save configuration
        config.add_device(device_config)
        
        # Initialize entities immediately after setup
        await _initialize_integration()
        return SetupComplete()
        
    except Exception as e:
        _LOG.error("Setup error: %s", e, exc_info=True)
        return SetupError(IntegrationSetupError.OTHER)


async def _request_device_ips(device_count: int) -> RequestUserInput:
    """Request IP addresses for multiple devices."""
    settings = []
    
    for i in range(device_count):
        settings.extend([
            {
                "id": f"device_{i}_ip",
                "label": {"en": f"Device {i+1} IP Address"},
                "description": {"en": f"IP address for Naim device {i+1} (e.g., 192.168.1.{100+i} or 192.168.1.{100+i}:15081)"},
                "field": {"text": {"value": f"192.168.1.{100+i}"}}
            },
            {
                "id": f"device_{i}_name", 
                "label": {"en": f"Device {i+1} Name"},
                "description": {"en": f"Friendly name for device {i+1}"},
                "field": {"text": {"value": f"Naim Device {i+1}"}}
            }
        ])
    
    return RequestUserInput(
        title={"en": f"Configure {device_count} Naim Devices"},
        settings=settings
    )


async def _handle_device_ips_collection(input_values: Dict[str, Any]) -> ucapi.SetupAction:
    """Process multiple device IPs and test connections."""
    devices_to_test = []
    
    # Extract device data from input
    device_index = 0
    while f"device_{device_index}_ip" in input_values:
        ip_input = input_values[f"device_{device_index}_ip"]
        name = input_values[f"device_{device_index}_name"]
        
        # Parse host:port format
        try:
            if ':' in ip_input:
                host, port_str = ip_input.split(':', 1)
                port = int(port_str)
            else:
                host = ip_input
                port = 15081
        except ValueError:
            _LOG.error(f"Invalid IP format for device {device_index + 1}: {ip_input}")
            return SetupError(IntegrationSetupError.OTHER)
        
        devices_to_test.append({
            "host": host,
            "port": port, 
            "name": name,
            "index": device_index
        })
        device_index += 1
    
    # Test all devices concurrently
    _LOG.info(f"Testing connections to {len(devices_to_test)} devices...")
    test_results = await _test_multiple_devices(devices_to_test)
    
    # Process results and save successful configurations
    successful_devices = 0
    for device_data, success in zip(devices_to_test, test_results):
        if success:
            device_id = f"naim_{device_data['host'].replace('.', '_')}_{device_data['port']}"
            device_config = NaimDeviceConfig(
                id=device_id,
                name=device_data['name'],
                address=device_data['host'],
                port=device_data['port'],
                enabled=True,
                standby_monitoring=True
            )
            config.add_device(device_config)
            successful_devices += 1
            _LOG.info(f"✅ Device {device_data['index'] + 1} ({device_data['name']}) connection successful")
        else:
            _LOG.error(f"❌ Device {device_data['index'] + 1} ({device_data['name']}) connection failed")
    
    if successful_devices == 0:
        _LOG.error("No devices could be connected")
        return SetupError(IntegrationSetupError.CONNECTION_REFUSED)
    
    # Initialize all entities
    await _initialize_integration()
    _LOG.info(f"Multi-device setup completed: {successful_devices}/{len(devices_to_test)} devices configured")
    return SetupComplete()


async def _test_multiple_devices(devices: List[Dict]) -> List[bool]:
    """Test connections to multiple devices concurrently."""
    async def test_device(device_data):
        try:
            client = NaimClient(device_data['host'], device_data['port'])
            success = await client.connect()
            if success:
                # Try to get device info for validation
                device_info = await client.get_system_info()
                if device_info:
                    _LOG.info(f"Device {device_data['index'] + 1}: {device_info.get('hostname', 'Unknown')}")
            await client.disconnect()
            return success
        except Exception as e:
            _LOG.error(f"Device {device_data['index'] + 1} test error: {e}")
            return False
    
    tasks = [test_device(device) for device in devices]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Convert exceptions to False
    return [result if isinstance(result, bool) else False for result in results]


async def on_subscribe_entities(entity_ids: List[str]):
    """
    Handle entity subscription events.
    CRITICAL: This is when entities are ready for state updates - WiiM pattern.
    """
    global media_players, remotes, entities_ready
    
    _LOG.info("Entities subscribed: %s", entity_ids)
    
    if not entities_ready:
        _LOG.error("RACE CONDITION: Subscription before entities ready! Initializing now...")
        await _initialize_integration()
    
    for entity_id in entity_ids:
        # Find media player entity
        for device_id, media_player in media_players.items():
            if media_player.id == entity_id:
                _LOG.info("Media Player subscribed for device %s, forcing immediate update", device_id)
                # Add to configured entities
                api.configured_entities.add(media_player)
                await media_player.update_attributes()
                # Start monitoring now that entity is subscribed
                media_player.start_monitoring()
                break
        
        # Find remote entity
        for device_id, remote in remotes.items():
            if remote.id == entity_id:
                _LOG.info("Remote subscribed for device %s, forcing immediate update", device_id)
                # Add to configured entities
                api.configured_entities.add(remote)
                await remote.update_attributes()
                break


async def on_unsubscribe_entities(entity_ids: List[str]):
    """Handle entity unsubscription events."""
    _LOG.info("Entities unsubscribed: %s", entity_ids)
    
    # Stop monitoring for unsubscribed entities
    for entity_id in entity_ids:
        for device_id, media_player in media_players.items():
            if media_player.id == entity_id:
                media_player.stop_monitoring()
                break


async def on_connect():
    """
    Handle connection events.
    CRITICAL: Pre-initialize entities if already configured.
    """
    global entities_ready, config
    
    _LOG.info("Remote connected")
    
    if config and config.config.devices:
        if not entities_ready:
            _LOG.info("Pre-configured system detected, initializing entities immediately")
            await _initialize_integration()
        else:
            await api.set_device_state(DeviceStates.CONNECTED)
    else:
        await api.set_device_state(DeviceStates.DISCONNECTED)


async def on_disconnect():
    """Handle disconnection events."""
    _LOG.info("Remote disconnected")
    
    for media_player in media_players.values():
        media_player.stop_monitoring()


async def main():
    """Main driver entry point."""
    global api, config, entities_ready
    
    _LOG.info("Starting Naim integration driver")
    
    try:
        loop = asyncio.get_running_loop()
        config = Configuration()
        config.load()
        
        driver_path = os.path.join(os.path.dirname(__file__), "..", "driver.json")
        if not os.path.exists(driver_path):
            driver_path = os.path.join(os.getcwd(), "driver.json")
        
        api = ucapi.IntegrationAPI(loop)
        
        if config.config.devices:
            _LOG.info("Pre-configuring entities before UC Remote connection")
            asyncio.create_task(_initialize_integration())
        
        await api.init(os.path.abspath(driver_path), setup_handler)

        api.add_listener(Events.SUBSCRIBE_ENTITIES, on_subscribe_entities)  # CRITICAL!
        api.add_listener(Events.UNSUBSCRIBE_ENTITIES, on_unsubscribe_entities)
        api.add_listener(Events.CONNECT, on_connect)
        api.add_listener(Events.DISCONNECT, on_disconnect)
        
        if config.config.devices:
            _LOG.info("%d device(s) already configured", len(config.config.devices))
        else:
            _LOG.info("No devices configured, waiting for setup...")
            await api.set_device_state(DeviceStates.DISCONNECTED)

        await asyncio.Future()
        
    except Exception as e:
        _LOG.error("Fatal error in main: %s", e, exc_info=True)
        raise


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, asyncio.CancelledError):
        _LOG.info("Integration stopped by user")
    except Exception as e:
        _LOG.error("Integration crashed: %s", e, exc_info=True)
        sys.exit(1)