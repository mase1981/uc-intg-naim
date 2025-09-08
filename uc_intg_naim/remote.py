"""
Naim remote control entity implementation.

:copyright: (c) 2025 by Meir Miyara.
:license: Mozilla Public License Version 2.0, see LICENSE for more details.
"""

import logging
from typing import Any, Dict

import ucapi
from ucapi import Remote

from uc_intg_naim.config import NaimDeviceConfig
from uc_intg_naim.client import NaimClient

_LOG = logging.getLogger(__name__)


class NaimRemote(Remote):
    """Naim remote control entity."""
    
    def __init__(self, device_config: NaimDeviceConfig):
        """Initialize Naim remote control."""
        self._device_config = device_config
        self._client = NaimClient(device_config.address, device_config.port)
        self._connected = False
        self._integration_api = None  # Will be set by driver
        
        # Initialize entity
        entity_id = f"naim_remote_{device_config.id}"
        
        # Define remote buttons/commands based on discovered capabilities
        simple_commands = [
            # Power controls
            "POWER_ON",
            "POWER_OFF", 
            "POWER_TOGGLE",
            
            # Volume controls
            "VOLUME_UP",
            "VOLUME_DOWN",
            "MUTE_TOGGLE",
            "MUTE",
            "UNMUTE",
            
            # Playback controls
            "PLAY",
            "PAUSE",
            "PLAY_PAUSE",
            "STOP",
            "NEXT",
            "PREVIOUS",
            "FORWARD",
            "REWIND",
            
            # Navigation controls
            "UP",
            "DOWN", 
            "LEFT",
            "RIGHT",
            "OK",
            "BACK",
            "PAGE_UP",
            "PAGE_DOWN",
            
            # Source selection - all discovered inputs
            "SOURCE_ANA1",      # Analogue 1
            "SOURCE_DIG1",      # Digital 1
            "SOURCE_DIG2",      # Digital 2
            "SOURCE_DIG3",      # Digital 3
            "SOURCE_HDMI",      # HDMI
            "SOURCE_RADIO",     # Internet Radio
            "SOURCE_BLUETOOTH", # Bluetooth
            "SOURCE_SPOTIFY",   # Spotify
            "SOURCE_TIDAL",     # TIDAL
            "SOURCE_QOBUZ",     # Qobuz
            "SOURCE_USB",       # USB
            "SOURCE_AIRPLAY",   # Airplay
            "SOURCE_GCAST",     # Chromecast
            "SOURCE_UPNP",      # Servers/UPnP
            "SOURCE_PLAYQUEUE", # Playqueue
            "SOURCE_FILES",     # Demo Files
            
            # Audio controls
            "BALANCE_LEFT",
            "BALANCE_RIGHT",
            "BALANCE_CENTER"
        ]
        
        features = [ucapi.remote.Features.SEND_CMD]
        attributes = {ucapi.remote.Attributes.STATE: ucapi.remote.States.ON}
        
        super().__init__(
            entity_id,
            f"{device_config.name} Remote",
            features,
            attributes,
            simple_commands=simple_commands,
            cmd_handler=self.command_handler
        )
    
    async def command_handler(self, entity, cmd_id: str, params: Dict[str, Any] = None) -> ucapi.StatusCodes:
        """Handle remote control commands."""
        _LOG.info("Remote command: %s, params: %s", cmd_id, params)
        
        try:
            # Handle send_cmd commands
            if cmd_id == ucapi.remote.Commands.SEND_CMD:
                if not params or "command" not in params:
                    _LOG.warning("SEND_CMD missing command parameter")
                    return ucapi.StatusCodes.BAD_REQUEST
                
                command = params["command"]
                success = await self._handle_simple_command(command)
                return ucapi.StatusCodes.OK if success else ucapi.StatusCodes.SERVER_ERROR
            
            # Handle direct simple commands (for backwards compatibility)
            success = await self._handle_simple_command(cmd_id)
            return ucapi.StatusCodes.OK if success else ucapi.StatusCodes.SERVER_ERROR
            
        except Exception as e:
            _LOG.error("Remote command %s failed: %s", cmd_id, e)
            return ucapi.StatusCodes.SERVER_ERROR
    
    async def _handle_simple_command(self, command: str) -> bool:
        """Handle simple remote commands."""
        try:
            # Power controls
            if command == "POWER_ON":
                return await self._client.power_on()
            elif command == "POWER_OFF":
                return await self._client.power_off()
            elif command == "POWER_TOGGLE":
                power_state = await self._client.get_power_state()
                if power_state:
                    return await self._client.power_off()
                else:
                    return await self._client.power_on()
                    
            # Volume controls
            elif command == "VOLUME_UP":
                return await self._client.volume_up()
            elif command == "VOLUME_DOWN":
                return await self._client.volume_down()
            elif command == "MUTE_TOGGLE":
                volume_info = await self._client.get_volume()
                if volume_info and volume_info.get("mute", "0") == "1":
                    return await self._client.unmute()
                else:
                    return await self._client.mute()
            elif command == "MUTE":
                return await self._client.mute()
            elif command == "UNMUTE":
                return await self._client.unmute()
            
            # Playback controls  
            elif command == "PLAY":
                return await self._client.play()
            elif command == "PAUSE":
                return await self._client.pause()
            elif command == "PLAY_PAUSE":
                status = await self._client.get_status()
                if status and status.get("transportState") == "2":  # playing
                    return await self._client.pause()
                else:
                    return await self._client.play()
            elif command == "STOP":
                return await self._client.stop()
            elif command == "NEXT":
                return await self._client.next_track()
            elif command == "PREVIOUS":
                return await self._client.previous_track()
            elif command == "FORWARD":
                return await self._client.next_track()  # Same as next
            elif command == "REWIND":
                return await self._client.previous_track()  # Same as previous
            
            # Navigation controls (limited support)
            elif command in ["UP", "DOWN", "LEFT", "RIGHT", "OK", "BACK", "PAGE_UP", "PAGE_DOWN"]:
                _LOG.info(f"Navigation command {command} - limited support on Naim devices")
                return True
                
            # Source selection - all discovered inputs
            elif command == "SOURCE_ANA1":
                return await self._client.set_source("ana1")
            elif command == "SOURCE_DIG1":
                return await self._client.set_source("dig1")
            elif command == "SOURCE_DIG2":
                return await self._client.set_source("dig2")
            elif command == "SOURCE_DIG3":
                return await self._client.set_source("dig3")
            elif command == "SOURCE_HDMI":
                return await self._client.set_source("hdmi")
            elif command == "SOURCE_RADIO":
                return await self._client.set_source("radio")
            elif command == "SOURCE_BLUETOOTH":
                return await self._client.set_source("bluetooth")
            elif command == "SOURCE_SPOTIFY":
                return await self._client.set_source("spotify")
            elif command == "SOURCE_TIDAL":
                return await self._client.set_source("tidal")
            elif command == "SOURCE_QOBUZ":
                return await self._client.set_source("qobuz")
            elif command == "SOURCE_USB":
                return await self._client.set_source("usb")
            elif command == "SOURCE_AIRPLAY":
                return await self._client.set_source("airplay")
            elif command == "SOURCE_GCAST":
                return await self._client.set_source("gcast")
            elif command == "SOURCE_UPNP":
                return await self._client.set_source("upnp")
            elif command == "SOURCE_PLAYQUEUE":
                return await self._client.set_source("playqueue")
            elif command == "SOURCE_FILES":
                return await self._client.set_source("files")
            
            # Audio controls
            elif command == "BALANCE_LEFT":
                return await self._client.set_balance(-25)  # Move balance left
            elif command == "BALANCE_RIGHT":
                return await self._client.set_balance(25)   # Move balance right
            elif command == "BALANCE_CENTER":
                return await self._client.set_balance(0)    # Center balance
                
            else:
                _LOG.warning("Unsupported remote command: %s", command)
                return False
                
        except Exception as e:
            _LOG.error("Error executing command %s: %s", command, e)
            return False
    
    async def connect(self) -> bool:
        """Connect to Naim device."""
        success = await self._client.connect()
        if success:
            self._connected = True
            _LOG.info("Remote entity connected for %s", self._device_config.name)
        return success
    
    async def disconnect(self) -> None:
        """Disconnect from Naim device."""
        self._connected = False
        await self._client.disconnect()
    
    async def update_attributes(self):
        """Update remote attributes - WiiM pattern."""
        self.attributes[ucapi.remote.Attributes.STATE] = ucapi.remote.States.ON
        
        if self._integration_api and hasattr(self._integration_api, 'configured_entities'):
            try:
                self._integration_api.configured_entities.update_attributes(
                    self.id, {ucapi.remote.Attributes.STATE: ucapi.remote.States.ON}
                )
                _LOG.debug("Forced integration API update for remote %s", self.id)
            except Exception as e:
                _LOG.debug("Could not force remote integration API update: %s", e)
    
    @property
    def is_connected(self) -> bool:
        """Check if device is connected."""
        return self._connected and self._client.is_connected