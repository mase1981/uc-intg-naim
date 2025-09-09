"""
Naim media player entity implementation.

:copyright: (c) 2025 by Meir Miyara.
:license: Mozilla Public License Version 2.0, see LICENSE for more details.
"""

import asyncio
import logging
from typing import Any, Dict, Optional

import ucapi
from ucapi import MediaPlayer

from uc_intg_naim.config import NaimDeviceConfig
from uc_intg_naim.client import NaimClient, NaimPlayState

_LOG = logging.getLogger(__name__)


class NaimMediaPlayer(MediaPlayer):
    """Naim media player entity with enhanced multi-device support."""
    
    def __init__(self, device_config: NaimDeviceConfig, entity_id: str = None):
        """Initialize Naim media player with optional custom entity ID for multi-device support."""
        self._device_config = device_config
        self._client = NaimClient(device_config.address, device_config.port)
        self._attr_state = ucapi.media_player.States.OFF
        self._attr_volume = 0
        self._attr_muted = False
        self._attr_media_position = 0
        self._attr_media_duration = 0
        self._attr_media_title = ""
        self._attr_media_artist = ""
        self._attr_media_album = ""
        self._attr_media_image_url = ""
        self._attr_source = ""
        self._attr_source_list = []
        self._attr_repeat = ucapi.media_player.RepeatMode.OFF
        self._attr_shuffle = False
        self._update_task: Optional[asyncio.Task] = None
        self._last_status = {}
        self._connected = False
        self._monitoring = False
        self._integration_api = None
        
        # Enhanced: Support custom entity ID for multi-device
        if entity_id is None:
            entity_id = f"naim_{device_config.id}"
        
        # Initialize entity with ALL media player features
        features = [
            ucapi.media_player.Features.ON_OFF,
            ucapi.media_player.Features.TOGGLE,
            ucapi.media_player.Features.PLAY_PAUSE,
            ucapi.media_player.Features.STOP,
            ucapi.media_player.Features.NEXT,
            ucapi.media_player.Features.PREVIOUS,
            ucapi.media_player.Features.VOLUME,
            ucapi.media_player.Features.VOLUME_UP_DOWN,
            ucapi.media_player.Features.MUTE_TOGGLE,
            ucapi.media_player.Features.MUTE,
            ucapi.media_player.Features.UNMUTE,
            ucapi.media_player.Features.SELECT_SOURCE,
            ucapi.media_player.Features.REPEAT,
            ucapi.media_player.Features.SHUFFLE,
            ucapi.media_player.Features.SEEK,
            ucapi.media_player.Features.MEDIA_DURATION,
            ucapi.media_player.Features.MEDIA_POSITION,
            ucapi.media_player.Features.MEDIA_TITLE,
            ucapi.media_player.Features.MEDIA_ARTIST,
            ucapi.media_player.Features.MEDIA_ALBUM,
            ucapi.media_player.Features.MEDIA_IMAGE_URL
        ]
        
        attributes = {
            ucapi.media_player.Attributes.STATE: self._attr_state,
            ucapi.media_player.Attributes.VOLUME: self._attr_volume,
            ucapi.media_player.Attributes.MUTED: self._attr_muted,
            ucapi.media_player.Attributes.MEDIA_POSITION: self._attr_media_position,
            ucapi.media_player.Attributes.MEDIA_DURATION: self._attr_media_duration,
            ucapi.media_player.Attributes.MEDIA_TITLE: self._attr_media_title,
            ucapi.media_player.Attributes.MEDIA_ARTIST: self._attr_media_artist,
            ucapi.media_player.Attributes.MEDIA_ALBUM: self._attr_media_album,
            ucapi.media_player.Attributes.MEDIA_IMAGE_URL: self._attr_media_image_url,
            ucapi.media_player.Attributes.SOURCE: self._attr_source,
            ucapi.media_player.Attributes.SOURCE_LIST: self._attr_source_list,
            ucapi.media_player.Attributes.REPEAT: self._attr_repeat,
            ucapi.media_player.Attributes.SHUFFLE: self._attr_shuffle
        }
        
        super().__init__(
            entity_id,
            device_config.name,  # Each device gets its own name
            features,
            attributes,
            device_class=ucapi.media_player.DeviceClasses.STREAMING_BOX,
            cmd_handler=self.command_handler
        )
        
        # Register event callback
        self._client.add_event_callback(self._handle_device_event)
    
    async def command_handler(self, entity, cmd_id: str, params: Dict[str, Any] = None) -> ucapi.StatusCodes:
        """Handle media player commands."""
        _LOG.info("Command: %s, params: %s", cmd_id, params)
        
        try:
            # Power commands
            if cmd_id == ucapi.media_player.Commands.ON:
                success = await self._client.power_on()
            elif cmd_id == ucapi.media_player.Commands.OFF:
                success = await self._client.power_off()
            elif cmd_id == ucapi.media_player.Commands.TOGGLE:
                power_state = await self._client.get_power_state()
                if power_state:
                    success = await self._client.power_off()
                else:
                    success = await self._client.power_on()
            
            # Playback commands
            elif cmd_id == ucapi.media_player.Commands.PLAY_PAUSE:
                status = await self._client.get_status()
                if status and status.get("transportState") == "2":  # playing
                    success = await self._client.pause()
                else:
                    success = await self._client.play()
            elif cmd_id == ucapi.media_player.Commands.STOP:
                success = await self._client.stop()
            elif cmd_id == ucapi.media_player.Commands.NEXT:
                success = await self._client.next_track()
            elif cmd_id == ucapi.media_player.Commands.PREVIOUS:
                success = await self._client.previous_track()
            elif cmd_id == ucapi.media_player.Commands.SEEK:
                position = params.get("media_position", 0) if params else 0
                success = await self._client.seek(int(position))
            
            # Volume commands - ENHANCED: Changed step from 5 to 3
            elif cmd_id == ucapi.media_player.Commands.VOLUME:
                volume = params.get("volume", 0) if params else 0
                success = await self._client.set_volume(int(volume))
            elif cmd_id == ucapi.media_player.Commands.VOLUME_UP:
                success = await self._client.volume_up(step=3)  # Changed from 5 to 3
            elif cmd_id == ucapi.media_player.Commands.VOLUME_DOWN:
                success = await self._client.volume_down(step=3)  # Changed from 5 to 3
            elif cmd_id == ucapi.media_player.Commands.MUTE_TOGGLE:
                if self._attr_muted:
                    success = await self._client.unmute()
                else:
                    success = await self._client.mute()
            elif cmd_id == ucapi.media_player.Commands.MUTE:
                success = await self._client.mute()
            elif cmd_id == ucapi.media_player.Commands.UNMUTE:
                success = await self._client.unmute()
            
            # Source selection
            elif cmd_id == ucapi.media_player.Commands.SELECT_SOURCE:
                source = params.get("source", "") if params else ""
                success = await self._client.set_source(source)
            
            # ENHANCED: Fixed repeat and shuffle commands using real API
            elif cmd_id == ucapi.media_player.Commands.REPEAT:
                repeat_mode = params.get("repeat", "OFF") if params else "OFF"
                success = await self._client.set_repeat(repeat_mode)
                # Update local state
                if success:
                    if repeat_mode == "OFF":
                        self._attr_repeat = ucapi.media_player.RepeatMode.OFF
                    elif repeat_mode == "ONE":
                        self._attr_repeat = ucapi.media_player.RepeatMode.ONE
                    elif repeat_mode == "ALL":
                        self._attr_repeat = ucapi.media_player.RepeatMode.ALL
            elif cmd_id == ucapi.media_player.Commands.SHUFFLE:
                shuffle_state = params.get("shuffle", False) if params else False
                success = await self._client.set_shuffle(shuffle_state)
                # Update local state
                if success:
                    self._attr_shuffle = shuffle_state
            
            else:
                _LOG.warning("Unsupported command: %s", cmd_id)
                return ucapi.StatusCodes.NOT_IMPLEMENTED
                
            # Update status after command
            await self.update_attributes()
            
            return ucapi.StatusCodes.OK if success else ucapi.StatusCodes.SERVER_ERROR
            
        except Exception as e:
            _LOG.error("Command %s failed: %s", cmd_id, e)
            return ucapi.StatusCodes.SERVER_ERROR
    
    async def connect(self) -> bool:
        """Connect to Naim device."""
        success = await self._client.connect()
        if success:
            self._connected = True
            # Get available sources immediately
            self._attr_source_list = await self._client.get_sources()
            _LOG.info("Connected to device, got %d sources", len(self._attr_source_list))
            
            # Get initial status and update attributes
            await self.update_status()
            
        return success
    
    def start_monitoring(self):
        """Start periodic monitoring - called when entity is subscribed."""
        if not self._connected:
            _LOG.warning("Cannot start monitoring - not connected")
            return
            
        if self._monitoring:
            _LOG.debug("Already monitoring %s", self.id)
            return
            
        if self._update_task is None or self._update_task.done():
            self._monitoring = True
            self._update_task = asyncio.create_task(self._periodic_update())
            _LOG.info("Started monitoring for %s", self.id)
    
    def stop_monitoring(self):
        """Stop periodic monitoring - called when entity is unsubscribed or remote disconnects."""
        if self._monitoring:
            self._monitoring = False
            if self._update_task and not self._update_task.done():
                self._update_task.cancel()
                self._update_task = None
            _LOG.info("Stopped monitoring for %s", self.id)
    
    async def disconnect(self) -> None:
        """Disconnect from Naim device."""
        self.stop_monitoring()
        self._connected = False
        await self._client.disconnect()
    
    async def _periodic_update(self) -> None:
        """Periodically update device status."""
        while self._connected and self._monitoring:
            try:
                await asyncio.sleep(5)  # Update every 5 seconds
                if self._monitoring:  # Check again in case stopped during sleep
                    await self.update_attributes()
            except asyncio.CancelledError:
                break
            except Exception as e:
                _LOG.error("Periodic update error: %s", e)
                if self._monitoring:
                    await asyncio.sleep(30)  # Wait longer on error
    
    async def update_status(self) -> None:
        """Update device status from device."""
        if not self._connected:
            _LOG.debug("Not connected, skipping status update")
            return
            
        try:
            _LOG.debug("Updating status for %s", self.id)
            
            # Get power state
            power_state = await self._client.get_power_state()
            if power_state is None:
                _LOG.warning("Could not get power state")
                self._attr_state = ucapi.media_player.States.UNAVAILABLE
                return
            
            if not power_state:
                _LOG.debug("Device is off")
                self._attr_state = ucapi.media_player.States.OFF
                return
            
            # Get current status
            status = await self._client.get_status()
            if not status:
                _LOG.warning("Could not get device status")
                self._attr_state = ucapi.media_player.States.ON
                return
                
            _LOG.debug("Got status: %s", status)
            self._last_status = status
            
            # Update state based on transport state
            transport_state = status.get("transportState", "0")
            if transport_state == "2":
                self._attr_state = ucapi.media_player.States.PLAYING
            elif transport_state == "1":
                self._attr_state = ucapi.media_player.States.PAUSED
            elif transport_state == "0":
                self._attr_state = ucapi.media_player.States.ON
            elif transport_state == "3":
                self._attr_state = ucapi.media_player.States.BUFFERING
            else:
                self._attr_state = ucapi.media_player.States.ON
            
            # Get volume info separately
            volume_info = await self._client.get_volume()
            if volume_info:
                self._attr_volume = int(volume_info.get("volume", 0))
                self._attr_muted = volume_info.get("mute", "0") == "1"
                _LOG.debug("Volume: %d, Muted: %s", self._attr_volume, self._attr_muted)
            
            # Update media information
            self._attr_media_position = int(status.get("transportPosition", 0)) // 1000  # Convert to seconds
            self._attr_media_duration = 0  # Not available in basic status
            self._attr_media_title = status.get("title", "")
            self._attr_media_artist = status.get("artist", "")
            self._attr_media_album = status.get("album", "")
            self._attr_media_image_url = status.get("artwork", "")
            
            # Update repeat and shuffle from status if available
            if status.get("repeat", "0") == "1":
                self._attr_repeat = ucapi.media_player.RepeatMode.ONE
            else:
                self._attr_repeat = ucapi.media_player.RepeatMode.OFF
            
            self._attr_shuffle = status.get("shuffle", "0") == "1"
            
            # Extract source from ussi
            source_ussi = status.get("source", "")
            if source_ussi.startswith("inputs/"):
                self._attr_source = source_ussi.split("/")[-1]
            else:
                self._attr_source = source_ussi
            
            _LOG.debug("Updated attributes - State: %s, Volume: %d, Source: %s", 
                      self._attr_state, self._attr_volume, self._attr_source)
            
        except Exception as e:
            _LOG.error("Status update failed: %s", e, exc_info=True)
            self._attr_state = ucapi.media_player.States.UNAVAILABLE
    
    async def update_attributes(self):
        """Update attributes and push to Remote - WiiM pattern."""
        # First update status from device
        await self.update_status()
        
        # Build attributes dictionary
        attributes = {
            ucapi.media_player.Attributes.STATE: self._attr_state,
            ucapi.media_player.Attributes.VOLUME: self._attr_volume,
            ucapi.media_player.Attributes.MUTED: self._attr_muted,
            ucapi.media_player.Attributes.MEDIA_POSITION: self._attr_media_position,
            ucapi.media_player.Attributes.MEDIA_DURATION: self._attr_media_duration,
            ucapi.media_player.Attributes.MEDIA_TITLE: self._attr_media_title,
            ucapi.media_player.Attributes.MEDIA_ARTIST: self._attr_media_artist,
            ucapi.media_player.Attributes.MEDIA_ALBUM: self._attr_media_album,
            ucapi.media_player.Attributes.MEDIA_IMAGE_URL: self._attr_media_image_url,
            ucapi.media_player.Attributes.SOURCE: self._attr_source,
            ucapi.media_player.Attributes.SOURCE_LIST: self._attr_source_list,
            ucapi.media_player.Attributes.REPEAT: self._attr_repeat,
            ucapi.media_player.Attributes.SHUFFLE: self._attr_shuffle
        }
        
        # Update the entity's attributes
        self.attributes.update(attributes)
        
        if self._integration_api and hasattr(self._integration_api, 'configured_entities'):
            try:
                self._integration_api.configured_entities.update_attributes(self.id, attributes)
                _LOG.debug("Forced integration API update for %s - State: %s", self.id, self._attr_state)
            except Exception as e:
                _LOG.debug("Could not force integration API update: %s", e)
        
        _LOG.debug("Attributes updated for %s - State: %s, Sources: %d", 
                  self.id, self._attr_state, len(self._attr_source_list))
    
    def _handle_device_event(self, event_data: Dict[str, Any]) -> None:
        """Handle real-time device events."""
        _LOG.debug("Device event: %s", event_data)
        
        # Process event data and update attributes as needed
        event_type = event_data.get("type", "")
        
        if event_type == "playback_state":
            play_state = event_data.get("state", "").lower()
            if play_state == "playing":
                self._attr_state = ucapi.media_player.States.PLAYING
            elif play_state == "paused":
                self._attr_state = ucapi.media_player.States.PAUSED
            elif play_state == "stopped":
                self._attr_state = ucapi.media_player.States.ON
            elif play_state == "buffering":
                self._attr_state = ucapi.media_player.States.BUFFERING
                
        elif event_type == "volume_change":
            self._attr_volume = event_data.get("volume", self._attr_volume)
            self._attr_muted = event_data.get("muted", self._attr_muted)
            
        elif event_type == "track_change":
            self._attr_media_title = event_data.get("title", "")
            self._attr_media_artist = event_data.get("artist", "")
            self._attr_media_album = event_data.get("album", "")
            self._attr_media_image_url = event_data.get("artwork", "")
            self._attr_media_duration = event_data.get("duration", 0)
            
        elif event_type == "source_change":
            self._attr_source = event_data.get("source", "")
            
        elif event_type == "position_update":
            self._attr_media_position = event_data.get("position", 0)
        
        # Update attributes and notify the remote
        asyncio.create_task(self.update_attributes())
    
    @property
    def is_connected(self) -> bool:
        """Check if device is connected."""
        return self._connected and self._client.is_connected