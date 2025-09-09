"""
Naim audio device API client.

:copyright: (c) 2025 by Meir Miyara.
:license: Mozilla Public License Version 2.0, see LICENSE for more details.
"""

import asyncio
import json
import logging
from typing import Any, Callable, Dict, List, Optional
from urllib.parse import urljoin

import aiohttp
import websockets
from websockets.exceptions import ConnectionClosed, WebSocketException

_LOG = logging.getLogger(__name__)


class NaimPlayState:
    """Naim playback states based on transportState values."""
    STOPPED = "0"
    PAUSED = "1"
    PLAYING = "2"
    BUFFERING = "3"


class NaimSource:
    """Naim audio sources based on discovery results."""
    # Analog inputs
    ANALOG_1 = "ana1"
    ANALOG_2 = "ana2"
    ANALOG_3 = "ana3" 
    ANALOG_4 = "ana4"
    # Digital inputs
    DIGITAL_1 = "dig1"
    DIGITAL_2 = "dig2"
    DIGITAL_3 = "dig3"
    DIGITAL_4 = "dig4"
    DIGITAL_5 = "dig5"
    # Other inputs
    HDMI = "hdmi"
    BLUETOOTH = "bluetooth"
    INTERNET_RADIO = "radio"
    SPOTIFY = "spotify"
    TIDAL = "tidal"
    QOBUZ = "qobuz"
    USB = "usb"
    AIRPLAY = "airplay"
    CHROMECAST = "gcast"
    UPNP = "upnp"
    PLAYQUEUE = "playqueue"
    FILES = "files"
    MULTIROOM = "multiroom"


class NaimClient:
    """Client for communicating with Naim audio devices."""
    
    def __init__(self, host: str, port: int = 15081):
        """Initialize Naim client."""
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"
        self._session: Optional[aiohttp.ClientSession] = None
        self._websocket: Optional[websockets.WebSocketServerProtocol] = None
        self._ws_task: Optional[asyncio.Task] = None
        self._event_callbacks: List[Callable[[Dict[str, Any]], None]] = []
        self._is_connected = False
        self._available_inputs: List[Dict[str, Any]] = []
        self._device_info: Dict[str, Any] = {}
        
        # Initialize api_base properly
        self.api_base = self.base_url  # Will be updated during connection if /naim prefix detected
        
    async def connect(self) -> bool:
        """Connect to the Naim device."""
        try:
            if self._session is None:
                timeout = aiohttp.ClientTimeout(total=10)
                self._session = aiohttp.ClientSession(timeout=timeout)
            
            # Test connection with root endpoint first to detect API prefix
            root_data = await self._request("GET", "/")
            if not root_data:
                _LOG.error("Could not connect to Naim device root endpoint")
                return False
            
            # Check if root endpoint indicates /naim prefix is needed
            api_prefix_detected = False
            if isinstance(root_data, dict) and "raw_response" in root_data:
                response_text = root_data["raw_response"]
                if "naim/index.fcgi" in response_text or "naim/" in response_text:
                    # Device uses /naim prefix
                    self.api_base = f"{self.base_url}/naim"
                    api_prefix_detected = True
                    _LOG.info("Detected Naim API prefix: /naim")
            
            # Test the detected API base with a known endpoint
            if api_prefix_detected:
                # Test with /naim prefix
                test_endpoints = ["/nowplaying", "/system", "/inputs"]
                for endpoint in test_endpoints:
                    test_data = await self._request("GET", endpoint)
                    if test_data:
                        _LOG.info(f"Confirmed API prefix /naim working with {endpoint}")
                        break
                else:
                    # If /naim prefix tests fail, fall back to no prefix
                    _LOG.warning("API prefix /naim detected but tests failed, falling back to root")
                    self.api_base = self.base_url
            
            # Get system info to determine device capabilities
            system_info = await self._request("GET", "/system")
            if system_info:
                self._device_info = system_info
                model = system_info.get("model", "Unknown")
                hostname = system_info.get("hostname", f"Naim Device ({self.host})")
                _LOG.info(f"Connected to Naim device: Model {model}, Name: {hostname}")
                _LOG.info(f"Using API base: {self.api_base}")
            
            # Get available inputs
            inputs_data = await self._request("GET", "/inputs")
            if inputs_data and "children" in inputs_data:
                self._available_inputs = inputs_data["children"]
                _LOG.info(f"Found {len(self._available_inputs)} inputs")
            else:
                _LOG.warning("Could not get inputs from device")
                self._available_inputs = []
            
            self._is_connected = True
            return True
                
        except Exception as e:
            _LOG.error("Failed to connect to Naim device %s:%s - %s", self.host, self.port, e)
            
        return False
    
    async def disconnect(self) -> None:
        """Disconnect from the Naim device."""
        self._is_connected = False
        
        if self._ws_task:
            self._ws_task.cancel()
            self._ws_task = None
            
        if self._websocket:
            await self._websocket.close()
            self._websocket = None
            
        if self._session:
            await self._session.close()
            self._session = None
    
    def add_event_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Add callback for device events."""
        self._event_callbacks.append(callback)
    
    def remove_event_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Remove event callback."""
        if callback in self._event_callbacks:
            self._event_callbacks.remove(callback)
    
    async def _request(self, method: str, endpoint: str, json_data: Dict[str, Any] = None, **kwargs) -> Optional[Dict[str, Any]]:
        """Make HTTP request to device."""
        if not self._session:
            return None
            
        url = urljoin(self.api_base, endpoint)
        
        try:
            # Prepare request kwargs
            request_kwargs = {
                'headers': {
                    'User-Agent': 'Naim-Integration/1.0',
                    'Accept': 'application/json'
                },
                **kwargs
            }
            
            # NOTE: Most Naim commands use URL parameters, not JSON payloads
            if json_data is not None:
                request_kwargs['json'] = json_data
                request_kwargs['headers']['Content-Type'] = 'application/json'
            
            _LOG.debug("Making %s request to %s", method, url)
            
            async with self._session.request(method, url, **request_kwargs) as response:
                if response.status == 200:
                    if response.content_type == "application/json":
                        result = await response.json()
                        _LOG.debug("Response: %s", result)
                        return result
                    else:
                        text = await response.text()
                        # Check if it's a redirect response
                        if "refresh" in text.lower() and "naim" in text.lower():
                            _LOG.debug("Received redirect response, endpoint may not be valid")
                            return {"raw_response": text, "status_code": response.status}
                        return {"response": text}
                else:
                    response_text = await response.text()
                    _LOG.warning("HTTP %s: %s for %s - Response: %s", response.status, response.reason, url, response_text)
                    
        except Exception as e:
            _LOG.error("Request failed: %s %s - %s", method, url, e)
            
        return None
    
    async def get_status(self) -> Optional[Dict[str, Any]]:
        """Get current device status from /nowplaying endpoint."""
        return await self._request("GET", "/nowplaying")
    
    async def get_system_info(self) -> Optional[Dict[str, Any]]:
        """Get system information."""
        if self._device_info:
            return self._device_info
        return await self._request("GET", "/system")
    
    async def get_power_state(self) -> Optional[bool]:
        """Get device power state."""
        power_info = await self._request("GET", "/power")
        if power_info:
            state = power_info.get("state", "").lower()
            system = power_info.get("system", "").lower()
            return state == "on" or system == "on"
        return None
    
    async def power_on(self) -> bool:
        """Power on the device - FIXED: Use URL parameters not JSON."""
        _LOG.info("Sending power ON command")
        response = await self._request("PUT", "/power?system=on")
        success = response is not None
        _LOG.info("Power ON command result: %s", "SUCCESS" if success else "FAILED")
        return success
    
    async def power_off(self) -> bool:
        """Power off the device - FIXED: Use URL parameters and 'lona' value."""
        _LOG.info("Sending power OFF command")
        response = await self._request("PUT", "/power?system=lona")
        success = response is not None
        _LOG.info("Power OFF command result: %s", "SUCCESS" if success else "FAILED")
        return success
    
    async def get_volume(self) -> Optional[Dict[str, Any]]:
        """Get current volume and mute state."""
        return await self._request("GET", "/levels/room")
    
    async def set_volume(self, volume: int) -> bool:
        """Set volume level (0-100)."""
        if not 0 <= volume <= 100:
            return False
            
        _LOG.info("Setting volume to %d", volume)
        response = await self._request("PUT", f"/levels/room?volume={volume}")
        success = response is not None
        _LOG.info("Set volume command result: %s", "SUCCESS" if success else "FAILED")
        return success
    
    async def volume_up(self, step: int = 3) -> bool:
        """Increase volume by step amount - ENHANCED: Default step changed to 3."""
        volume_info = await self.get_volume()
        if volume_info and "volume" in volume_info:
            current_volume = int(volume_info["volume"])
            new_volume = min(100, current_volume + step)
            return await self.set_volume(new_volume)
        return False
    
    async def volume_down(self, step: int = 3) -> bool:
        """Decrease volume by step amount - ENHANCED: Default step changed to 3."""
        volume_info = await self.get_volume()
        if volume_info and "volume" in volume_info:
            current_volume = int(volume_info["volume"])
            new_volume = max(0, current_volume - step)
            return await self.set_volume(new_volume)
        return False
    
    async def mute(self) -> bool:
        """Mute audio - FIXED: Use mute=1 not mute=on."""
        _LOG.info("Sending mute command")
        response = await self._request("PUT", "/levels/room?mute=1")
        success = response is not None
        _LOG.info("Mute command result: %s", "SUCCESS" if success else "FAILED")
        return success
    
    async def unmute(self) -> bool:
        """Unmute audio - FIXED: Use mute=0 not mute=off."""
        _LOG.info("Sending unmute command")
        response = await self._request("PUT", "/levels/room?mute=0")
        success = response is not None
        _LOG.info("Unmute command result: %s", "SUCCESS" if success else "FAILED")
        return success
    
    async def set_source(self, source: str) -> bool:
        """Select audio source using source identifier."""
        # Find the source in available inputs
        for input_info in self._available_inputs:
            ussi = input_info.get("ussi", "")
            
            # Check if this input matches the requested source
            if (ussi == f"inputs/{source}" or 
                ussi.endswith(f"/{source}") or
                input_info.get("name", "").lower().replace(" ", "") == source.lower()):
                
                # Check if source is selectable
                if input_info.get("selectable") == "1":
                    _LOG.info("Setting source to %s", source)
                    endpoint = f"/inputs/{source}?cmd=select"
                    response = await self._request("GET", endpoint)
                    success = response is not None
                    _LOG.info("Set source command result: %s", "SUCCESS" if success else "FAILED")
                    return success
                else:
                    _LOG.warning("Source %s is not selectable", source)
                    return False
        
        # If not found in available inputs, try anyway with the source ID
        _LOG.info("Setting source to %s (not in discovered inputs)", source)
        endpoint = f"/inputs/{source}?cmd=select"
        response = await self._request("GET", endpoint)
        success = response is not None
        _LOG.info("Set source command result: %s", "SUCCESS" if success else "FAILED")
        return success
    
    async def get_sources(self) -> List[str]:
        """Get available audio sources based on device capabilities."""
        sources = []
        
        for input_info in self._available_inputs:
            # Only include selectable inputs that are not disabled
            if (input_info.get("selectable") == "1" and 
                input_info.get("disabled") != "1"):
                
                ussi = input_info.get("ussi", "")
                if ussi.startswith("inputs/"):
                    source_id = ussi.split("/")[-1]
                    sources.append(source_id)
        
        # If no sources found from device, provide reasonable defaults
        if not sources:
            _LOG.warning("No selectable sources found, using defaults")
            sources = ["radio", "bluetooth", "spotify", "dig5", "hdmi"]
        
        _LOG.info(f"Available sources: {sources}")
        return sources
    
    async def get_source_names(self) -> Dict[str, str]:
        """Get mapping of source IDs to display names."""
        source_names = {}
        
        for input_info in self._available_inputs:
            ussi = input_info.get("ussi", "")
            if ussi.startswith("inputs/"):
                source_id = ussi.split("/")[-1]
                friendly_name = input_info.get("name", source_id)
                source_names[source_id] = friendly_name
        
        # If no source names from device, return default friendly names
        if not source_names:
            source_names = {
                "ana1": "Analogue 1", "ana2": "Analogue 2", "ana3": "Analogue 3", "ana4": "Analogue 4",
                "dig1": "Digital 1", "dig2": "Digital 2", "dig3": "Digital 3", "dig4": "Digital 4", "dig5": "Digital 5",
                "hdmi": "HDMI",
                "bluetooth": "Bluetooth",
                "radio": "Internet Radio", 
                "spotify": "Spotify",
                "tidal": "TIDAL",
                "qobuz": "Qobuz",
                "usb": "USB",
                "airplay": "AirPlay",
                "gcast": "Chromecast",
                "upnp": "UPnP/Servers",
                "playqueue": "Play Queue",
                "files": "Local Files",
                "multiroom": "Multi-room"
            }
        
        return source_names
    
    async def get_available_inputs_detailed(self) -> List[Dict[str, Any]]:
        """Get detailed information about available inputs."""
        return self._available_inputs
    
    # ENHANCED: Fixed playback control methods using actual working Naim API endpoints
    async def play(self) -> bool:
        """Start playback - FIXED: Use nowplaying API."""
        _LOG.info("Sending play command")
        response = await self._request("GET", "/nowplaying?cmd=play")
        success = response is not None
        _LOG.info("Play command result: %s", "SUCCESS" if success else "FAILED")
        return success
    
    async def pause(self) -> bool:
        """Pause playback - FIXED: Use nowplaying API."""
        _LOG.info("Sending pause command")
        response = await self._request("GET", "/nowplaying?cmd=pause")
        success = response is not None
        _LOG.info("Pause command result: %s", "SUCCESS" if success else "FAILED")
        return success
    
    async def stop(self) -> bool:
        """Stop playback - FIXED: Use nowplaying API."""
        _LOG.info("Sending stop command")
        response = await self._request("GET", "/nowplaying?cmd=stop")
        success = response is not None
        _LOG.info("Stop command result: %s", "SUCCESS" if success else "FAILED")
        return success
    
    # ENHANCED: Working next/previous track commands from API discovery
    async def next_track(self) -> bool:
        """Skip to next track - FIXED: Using working API endpoint."""
        _LOG.info("Sending next track command")
        response = await self._request("GET", "/nowplaying?cmd=next")
        success = response is not None
        _LOG.info("Next track command result: %s", "SUCCESS" if success else "FAILED")
        return success
    
    async def previous_track(self) -> bool:
        """Go to previous track - FIXED: Using working API endpoint."""
        _LOG.info("Sending previous track command")
        response = await self._request("GET", "/nowplaying?cmd=prev")
        success = response is not None
        _LOG.info("Previous track command result: %s", "SUCCESS" if success else "FAILED")
        return success
    
    async def seek(self, position: int) -> bool:
        """Seek to position in seconds - NOT SUPPORTED by basic Naim API."""
        _LOG.warning("Seek command - not supported by basic Naim HTTP API")
        return False
    
    # ENHANCED: Working repeat and shuffle commands from API discovery
    async def set_repeat(self, mode: str) -> bool:
        """Set repeat mode - FIXED: Using working API endpoints.
        
        Args:
            mode: "OFF" (0), "ONE" (1), or "ALL" (2)
        """
        _LOG.info("Setting repeat mode to %s", mode)
        
        # Map repeat modes to Naim API values
        repeat_values = {
            "OFF": "0",
            "ONE": "1", 
            "ALL": "2"
        }
        
        repeat_value = repeat_values.get(mode.upper(), "0")
        response = await self._request("PUT", f"/nowplaying?repeat={repeat_value}")
        success = response is not None
        _LOG.info("Set repeat command result: %s", "SUCCESS" if success else "FAILED")
        return success
    
    async def set_shuffle(self, enabled: bool) -> bool:
        """Set shuffle mode - FIXED: Using working API endpoint."""
        _LOG.info("Setting shuffle to %s", enabled)
        shuffle_value = "1" if enabled else "0"
        response = await self._request("PUT", f"/nowplaying?shuffle={shuffle_value}")
        success = response is not None
        _LOG.info("Set shuffle command result: %s", "SUCCESS" if success else "FAILED")
        return success
    
    async def set_balance(self, balance: int) -> bool:
        """Set audio balance - NOT SUPPORTED by basic Naim API."""
        _LOG.warning("Balance control - not supported by basic Naim HTTP API")
        return False
    
    def _transport_state_to_play_state(self, transport_state: str) -> str:
        """Convert transport state to play state."""
        state_map = {
            "0": "stopped",
            "1": "paused", 
            "2": "playing",
            "3": "buffering"
        }
        return state_map.get(str(transport_state), "unknown")
    
    def _normalize_status(self, status: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize status response to standard format."""
        if not status:
            return {}
            
        # Get transport state and convert to play state
        transport_state = status.get("transportState", "0")
        play_state = self._transport_state_to_play_state(transport_state)
        
        # Get source information
        source_ussi = status.get("source", "")
        source_id = source_ussi.split("/")[-1] if "/" in source_ussi else source_ussi
        
        normalized = {
            "state": play_state,
            "source": source_id,
            "source_ussi": source_ussi,
            "position": int(status.get("transportPosition", 0)),
            "duration": 0,  # Not typically available in Naim status
            "title": status.get("title", ""),
            "artist": status.get("artist", ""),
            "album": status.get("album", ""),
            "artwork": status.get("artwork", ""),
            "station": status.get("station", ""),
            "live": status.get("live", "0") == "1",
            "can_resume": status.get("canResume", "0") == "1",
            "repeat": status.get("repeat", "0") == "1",
            "shuffle": status.get("shuffle", "0") == "1",
            "bit_depth": status.get("bitDepth", ""),
            "bit_rate": status.get("bitRate", ""),
            "sample_rate": status.get("sampleRate", ""),
            "codec": status.get("codec", ""),
            "genre": status.get("genre", "")
        }
        
        return normalized
    
    @property
    def is_connected(self) -> bool:
        """Check if client is connected."""
        return self._is_connected
    
    @property
    def device_info(self) -> Dict[str, Any]:
        """Get cached device information."""
        return {
            "host": self.host,
            "port": self.port,
            "device_info": self._device_info,
            "available_inputs": self._available_inputs
        }