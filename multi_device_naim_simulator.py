#!/usr/bin/env python3
"""
Naim Atom Device Simulator for Testing - Enhanced with Multi-Device Support.

This simulator provides web servers that mimic multiple Naim Atom HTTP APIs
for testing the Unfolded Circle integration with multiple devices.

:copyright: (c) 2025 by Meir Miyara.
:license: Mozilla Public License Version 2.0, see LICENSE for more details.
"""

import asyncio
import json
import logging
import random
import socket
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

import websockets
from aiohttp import web, WSMsgType
from aiohttp.web import Request, Response, WebSocketResponse

logging.basicConfig(level=logging.INFO)
_LOG = logging.getLogger(__name__)


def get_local_ip() -> str:
    """Get the local IP address of the machine."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"


class NaimAtomSimulator:
    """Simulates a Naim Atom audio device."""
    
    def __init__(self, host: str = None, port: int = 8080, device_name: str = "Atom-Simulator", device_id: int = 1):
        """Initialize the simulator."""
        self.host = host if host else get_local_ip()
        self.port = port
        self.device_name = device_name
        self.device_id = device_id
        self.app = web.Application()
        self.websocket_clients: Set[WebSocketResponse] = set()
        
        # Device state - Naim Atom specific with unique data per device
        self.state = {
            "power": True,
            "playback_state": "2",  # 0=stopped, 1=paused, 2=playing, 3=buffering
            "volume": 40 + (device_id * 10),  # Different volumes per device
            "muted": False,
            "source": "spotify" if device_id == 1 else "radio" if device_id == 2 else "tidal",
            "position": 45000 + (device_id * 5000),  # milliseconds
            "duration": 180000,  # milliseconds
            "title": f"Track {device_id}",
            "artist": f"Artist {device_id}",
            "album": f"Album {device_id}",
            "station": f"Station {device_id}",
            "genre": "Rock",
            "artwork": f"https://example.com/artwork_{device_id}.jpg",
            "device_name": device_name,
            "model": "32",
            "hostname": device_name,
            "serial": f"ATOM{device_id:06d}",
            "system_version": "3.10.1.5617",
            "api_version": "1.4.0",
            "device_id": f"naim_atom_{device_id:03d}",
            "balance": 0,
            "live": False,
            "repeat": 0,  # 0=off, 1=one, 2=all
            "shuffle": 0  # 0=off, 1=on
        }
        
        # Available sources for Naim Atom based on discovery data
        self.sources = [
            "ana1", "dig1", "dig2", "dig3", "hdmi", "bluetooth", 
            "radio", "spotify", "tidal", "qobuz", "usb", "airplay", 
            "gcast", "upnp", "playqueue", "files"
        ]
        
        # Sample tracks for simulation - different per device
        self.sample_tracks = [
            {
                "title": f"Device {device_id} Song 1",
                "artist": f"Artist {device_id}A", 
                "album": f"Album {device_id}A",
                "station": f"Station {device_id}A",
                "genre": "Rock",
                "duration": 355000
            },
            {
                "title": f"Device {device_id} Song 2",
                "artist": f"Artist {device_id}B",
                "album": f"Album {device_id}B",
                "station": f"Station {device_id}B", 
                "genre": "Pop",
                "duration": 240000
            },
            {
                "title": f"Device {device_id} Song 3",
                "artist": f"Artist {device_id}C",
                "album": f"Album {device_id}C",
                "station": f"Station {device_id}C",
                "genre": "Jazz",
                "duration": 320000
            }
        ]
        
        self._setup_routes()
        self._position_task: Optional[asyncio.Task] = None
        self._start_position_update()
        
    def _setup_routes(self):
        """Set up HTTP routes for Naim Atom API."""
        # Root endpoint
        self.app.router.add_get('/', self.handle_root)
        
        # System info and power control
        self.app.router.add_get('/system', self.handle_system)
        self.app.router.add_get('/power', self.handle_power_get)
        self.app.router.add_put('/power', self.handle_power_put)
        
        # Now playing / status
        self.app.router.add_get('/nowplaying', self.handle_nowplaying)
        self.app.router.add_put('/nowplaying', self.handle_nowplaying_put)  # ENHANCED: For repeat/shuffle
        self.app.router.add_get('/status', self.handle_nowplaying)
        
        # Volume control
        self.app.router.add_get('/levels', self.handle_levels)
        self.app.router.add_get('/levels/room', self.handle_levels_room)
        self.app.router.add_put('/levels/room', self.handle_levels_room_put)
        
        # Input/source selection
        self.app.router.add_get('/inputs', self.handle_inputs)
        self.app.router.add_get('/inputs/{source}', self.handle_input_select)
        
        # Network information
        self.app.router.add_get('/network', self.handle_network)
        
        # WebSocket endpoint
        self.app.router.add_get('/websocket', self.handle_websocket)
        self.app.router.add_get('/ws', self.handle_websocket)
    
    async def handle_root(self, request: Request) -> Response:
        """Handle root endpoint."""
        return web.json_response({
            "version": "1.4.0",
            "changestamp": "0",
            "name": "1",
            "ussi": "api/1",
            "class": "object.api.support",
            "cpu": str(random.randint(100, 200))
        })
    
    async def handle_system(self, request: Request) -> Response:
        """Handle system info request."""
        return web.json_response({
            "version": "1.4.0",
            "changestamp": "0",
            "name": "system",
            "ussi": "system",
            "class": "object.system",
            "apiregular": "1",
            "apistreaming": "1",
            "appVer": self.state["system_version"],
            "build": self.state["system_version"] + ".0",
            "cpu": str(random.randint(20000, 30000)),
            "displayType": "4",
            "firstTimeSetupComplete": "1",
            "hardwareRevision": "",
            "hardwareSerial": self.state["serial"],
            "hardwareType": "stream800",
            "hostAppVer": "1.13.0.21851",
            "ipAddress": self.host,
            "kernel": "4.1.25",
            "machine": "armv7l",
            "model": self.state["model"],
            "system": "Linux",
            "udid": f"5F9EC1B3-ED59-79BB-0020-B8804F34E{self.device_id:03d}",
            "hostname": self.state["hostname"],
            "variant": "0"
        })
    
    async def handle_power_get(self, request: Request) -> Response:
        """Handle power status request."""
        return web.json_response({
            "version": "1.4.0",
            "changestamp": "0",
            "name": "Power",
            "ussi": "power",
            "class": "object.power",
            "cpu": str(random.randint(100, 200)),
            "powerMode": "0",
            "serverMode": "0",
            "standbyTimeout": "10",
            "state": "on" if self.state["power"] else "standby",
            "system": "on" if self.state["power"] else "standby"
        })
    
    async def handle_power_put(self, request: Request) -> Response:
        """Handle power control."""
        try:
            # Get query parameters for power control
            system_state = request.query.get("system", "").lower()
            
            if system_state == "on":
                self.state["power"] = True
                _LOG.info(f"Device {self.device_id}: Power turned ON")
                await self._broadcast_event({
                    "type": "power_change",
                    "power": True
                })
            elif system_state in ["off", "lona", "standby"]:
                self.state["power"] = False
                self.state["playback_state"] = "0"  # stopped
                _LOG.info(f"Device {self.device_id}: Power turned OFF")
                await self._broadcast_event({
                    "type": "power_change", 
                    "power": False
                })
            else:
                return web.json_response({"error": "Invalid power state"}, status=400)
                
            return web.json_response({"status": "ok", "power": "on" if self.state["power"] else "standby"})
                
        except Exception as e:
            return web.json_response({"error": str(e)}, status=400)
    
    async def handle_nowplaying(self, request: Request) -> Response:
        """Handle now playing request and playback commands."""
        if not self.state["power"]:
            return web.json_response({"error": "Device is off"}, status=503)
        
        # Handle playback commands via query parameters
        cmd = request.query.get("cmd", "").lower()
        if cmd:
            return await self._handle_playback_command(cmd)
        
        # Return current status
        return web.json_response({
            "version": "1.4.0",
            "changestamp": "0",
            "name": "Now Playing",
            "ussi": "nowplaying",
            "class": "object.nowplaying",
            "artwork": self.state["artwork"],
            "artworkSource": self.state["artwork"],
            "bitDepth": "16",
            "bitRate": "320000",
            "canResume": "1",
            "channels": "2",
            "codec": "MP3",
            "cpu": str(random.randint(500, 700)),
            "error": "0",
            "genre": self.state["genre"],
            "live": "1" if self.state["live"] else "0",
            "mimeType": "audio/mp3",
            "repeat": str(self.state["repeat"]),
            "restrictPause": "0",
            "restrictResume": "0",
            "restrictSeek": "0",
            "restrictStop": "0",
            "sampleRate": "44100",
            "shuffle": str(self.state["shuffle"]),
            "source": f"inputs/{self.state['source']}",
            "sourceMultiroom": "inputs/none",
            "station": self.state["station"],
            "title": self.state["title"],
            "artist": self.state["artist"],
            "album": self.state["album"],
            "transportPosition": str(self.state["position"]),
            "transportState": self.state["playback_state"]
        })
    
    async def handle_nowplaying_put(self, request: Request) -> Response:
        """Handle PUT requests to nowplaying for repeat/shuffle control."""
        if not self.state["power"]:
            return web.json_response({"error": "Device is off"}, status=503)
        
        # ENHANCED: Handle repeat and shuffle commands
        repeat_value = request.query.get("repeat")
        shuffle_value = request.query.get("shuffle")
        
        if repeat_value is not None:
            try:
                repeat_int = int(repeat_value)
                if 0 <= repeat_int <= 2:
                    self.state["repeat"] = repeat_int
                    _LOG.info(f"Device {self.device_id}: Repeat set to {repeat_int}")
                    await self._broadcast_event({
                        "type": "repeat_change",
                        "repeat": repeat_int
                    })
                else:
                    return web.json_response({"error": "Invalid repeat value"}, status=400)
            except ValueError:
                return web.json_response({"error": "Invalid repeat value"}, status=400)
        
        if shuffle_value is not None:
            try:
                shuffle_int = int(shuffle_value)
                if shuffle_int in [0, 1]:
                    self.state["shuffle"] = shuffle_int
                    _LOG.info(f"Device {self.device_id}: Shuffle set to {shuffle_int}")
                    await self._broadcast_event({
                        "type": "shuffle_change",
                        "shuffle": shuffle_int
                    })
                else:
                    return web.json_response({"error": "Invalid shuffle value"}, status=400)
            except ValueError:
                return web.json_response({"error": "Invalid shuffle value"}, status=400)
        
        return web.json_response({
            "version": "1.4.0",
            "changestamp": "0",
            "name": "",
            "ussi": "nowplaying",
            "class": "object",
            "cpu": str(random.randint(30000, 50000))
        })
    
    async def _handle_playback_command(self, cmd: str) -> Response:
        """Handle playback commands like play, pause, stop, next, prev."""
        _LOG.info(f"Device {self.device_id}: Playback command: {cmd}")
        
        if cmd == "play":
            self.state["playback_state"] = "2"  # playing
        elif cmd == "pause":
            self.state["playback_state"] = "1"  # paused
        elif cmd == "stop":
            self.state["playback_state"] = "0"  # stopped
            self.state["position"] = 0
        elif cmd == "next":
            await self._change_track()
            self.state["playback_state"] = "2"  # playing
        elif cmd == "prev":
            await self._change_track()
            self.state["playback_state"] = "2"  # playing
        else:
            return web.json_response({"error": f"Unknown command: {cmd}"}, status=400)
        
        await self._broadcast_event({
            "type": "playback_change",
            "state": self.state["playback_state"],
            "command": cmd
        })
        
        return web.json_response({
            "version": "1.4.0",
            "changestamp": "0",
            "name": "",
            "ussi": "nowplaying",
            "class": "object",
            "cpu": str(random.randint(30000, 50000))
        })
    
    async def handle_levels(self, request: Request) -> Response:
        """Handle levels request."""
        return web.json_response({
            "version": "1.4.0",
            "changestamp": "0",
            "name": "levels",
            "ussi": "levels",
            "class": "object.levels",
            "balance": str(self.state["balance"]),
            "cpu": str(random.randint(100, 200)),
            "headphoneDetect": "0",
            "mode": "1",
            "mute": "1" if self.state["muted"] else "0",
            "volume": str(self.state["volume"])
        })
    
    async def handle_levels_room(self, request: Request) -> Response:
        """Handle room levels request."""
        return web.json_response({
            "version": "1.4.0",
            "changestamp": "0",
            "name": "room",
            "ussi": "levels/room",
            "class": "object.levels",
            "balance": str(self.state["balance"]),
            "cpu": str(random.randint(100, 200)),
            "headphoneDetect": "0",
            "mute": "1" if self.state["muted"] else "0",
            "volume": str(self.state["volume"])
        })
    
    async def handle_levels_room_put(self, request: Request) -> Response:
        """Handle room levels control."""
        if not self.state["power"]:
            return web.json_response({"error": "Device is off"}, status=503)
        
        volume = request.query.get("volume")
        mute = request.query.get("mute")
        balance = request.query.get("balance")
        
        if volume is not None:
            try:
                vol = int(volume)
                if 0 <= vol <= 100:
                    self.state["volume"] = vol
                    self.state["muted"] = False
                    _LOG.info(f"Device {self.device_id}: Volume set to {vol}")
                    await self._broadcast_event({
                        "type": "volume_change",
                        "volume": vol,
                        "muted": False
                    })
                else:
                    return web.json_response({"error": "Volume must be 0-100"}, status=400)
            except ValueError:
                return web.json_response({"error": "Invalid volume value"}, status=400)
        
        if mute is not None:
            # ENHANCED: Support both "on"/"off" and "1"/"0" formats
            mute_state = mute.lower() in ["on", "1", "true"]
            self.state["muted"] = mute_state
            _LOG.info(f"Device {self.device_id}: Mute set to {mute_state}")
            await self._broadcast_event({
                "type": "volume_change",
                "volume": self.state["volume"],
                "muted": mute_state
            })
        
        if balance is not None:
            try:
                bal = int(balance)
                if -50 <= bal <= 50:
                    self.state["balance"] = bal
                    _LOG.info(f"Device {self.device_id}: Balance set to {bal}")
            except ValueError:
                pass
        
        return web.json_response({
            "version": "1.4.0",
            "changestamp": "0",
            "name": "room",
            "ussi": "levels/room",
            "class": "object.levels",
            "balance": str(self.state["balance"]),
            "cpu": str(random.randint(100, 200)),
            "headphoneDetect": "0",
            "mute": "1" if self.state["muted"] else "0",
            "volume": str(self.state["volume"])
        })
    
    async def handle_inputs(self, request: Request) -> Response:
        """Handle inputs list request."""
        children = [
            {"name": "Analogue 1", "ussi": "inputs/ana1", "class": "object.input.analogue", "alias": "", "disabled": "0", "multiroomMaster": "1", "selectable": "1"},
            {"name": "Digital 1", "ussi": "inputs/dig1", "class": "object.input.digital", "alias": "", "disabled": "0", "multiroomMaster": "1", "selectable": "1"},
            {"name": "Digital 2", "ussi": "inputs/dig2", "class": "object.input.digital", "alias": "", "disabled": "0", "multiroomMaster": "1", "selectable": "1"},
            {"name": "Digital 3", "ussi": "inputs/dig3", "class": "object.input.digital", "alias": "", "disabled": "0", "multiroomMaster": "1", "selectable": "1"},
            {"name": "HDMI", "ussi": "inputs/hdmi", "class": "object.input.hdmi", "alias": "", "disabled": "0", "multiroomMaster": "1", "selectable": "1"},
            {"name": "Internet Radio", "ussi": "inputs/radio", "class": "object.input.radio.internet", "alias": "", "disabled": "0", "multiroomMaster": "1", "selectable": "1"},
            {"name": "Bluetooth", "ussi": "inputs/bluetooth", "class": "object.input.bluetooth", "alias": "", "disabled": "0", "multiroomMaster": "1", "selectable": "1"},
            {"name": "Spotify", "ussi": "inputs/spotify", "class": "object.input.spotify", "disabled": "0", "multiroomMaster": "1", "selectable": "1"},
            {"name": "TIDAL", "ussi": "inputs/tidal", "class": "object.input.tidal", "disabled": "0", "multiroomMaster": "1", "selectable": "1"},
            {"name": "Qobuz", "ussi": "inputs/qobuz", "class": "object.input.qobuz", "disabled": "0", "multiroomMaster": "1", "selectable": "1"},
            {"name": "USB", "ussi": "inputs/usb", "class": "object.input.usb", "alias": "", "disabled": "0", "multiroomMaster": "1", "selectable": "1"},
            {"name": "Airplay", "ussi": "inputs/airplay", "class": "object.input.airplay", "disabled": "0", "multiroomMaster": "0", "selectable": "1"},
            {"name": "Chromecast built-in", "ussi": "inputs/gcast", "class": "object.input.googlecast", "multiroomMaster": "0", "selectable": "1"},
            {"name": "Servers", "ussi": "inputs/upnp", "class": "object.input.upnp", "alias": "", "disabled": "0", "multiroomMaster": "1", "selectable": "1"},
            {"name": "Playqueue", "ussi": "inputs/playqueue", "class": "object.input.playqueue", "multiroomMaster": "1", "selectable": "1"},
            {"name": "Demo Files", "ussi": "inputs/files", "class": "object.input.files", "multiroomMaster": "1", "selectable": "1"}
        ]
        
        return web.json_response({
            "version": "1.4.0",
            "changestamp": "0",
            "name": "Inputs",
            "ussi": "inputs",
            "class": "object.inputs",
            "cpu": str(random.randint(1000, 1200)),
            "children": children
        })
    
    async def handle_input_select(self, request: Request) -> Response:
        """Handle input/source selection."""
        if not self.state["power"]:
            return web.json_response({"error": "Device is off"}, status=503)
        
        source = request.match_info["source"]
        cmd = request.query.get("cmd", "").lower()
        
        # For source selection, cmd should be "select" or empty
        if cmd and cmd != "select":
            return web.json_response({"error": "Only 'select' command supported"}, status=400)
        
        if source in self.sources:
            old_source = self.state["source"]
            self.state["source"] = source
            
            # Change track when switching to music sources
            if source in ["spotify", "tidal", "qobuz", "radio", "usb", "upnp"]:
                await self._change_track()
            
            _LOG.info(f"Device {self.device_id}: Source changed from {old_source} to {source}")
            await self._broadcast_event({
                "type": "source_change",
                "source": source
            })
            
            return web.json_response({
                "version": "1.4.0",
                "changestamp": "0",
                "name": "",
                "ussi": f"inputs/{source}",
                "class": "object",
                "cpu": str(random.randint(100000, 999999))
            })
        else:
            return web.json_response({"error": f"Unknown input: {source}"}, status=400)
    
    async def handle_network(self, request: Request) -> Response:
        """Handle network info request."""
        return web.json_response({
            "version": "1.4.0",
            "changestamp": "0",
            "name": "network",
            "ussi": "network",
            "class": "object.network",
            "connectionState": "0",
            "cpu": str(random.randint(30000, 32000)),
            "current": "network/wired",
            "dhcp": "1",
            "dns1": "8.8.8.8",
            "dns2": "8.8.4.4",
            "dnsName": self.state["hostname"],
            "gateway": "192.168.1.1",
            "hostname": self.state["hostname"],
            "ipAddress": self.host,
            "macAddress": f"AA:BB:CC:DD:EE:{self.device_id:02X}",
            "netmask": "255.255.255.0",
            "workgroup": "NAIM"
        })
    
    async def handle_websocket(self, request: Request) -> WebSocketResponse:
        """Handle WebSocket connections."""
        ws = WebSocketResponse()
        await ws.prepare(request)
        
        self.websocket_clients.add(ws)
        _LOG.info(f"Device {self.device_id}: WebSocket client connected. Total clients: {len(self.websocket_clients)}")
        
        try:
            # Send initial status
            await ws.send_str(json.dumps({
                "type": "status",
                "data": self.state,
                "timestamp": int(time.time()),
                "device_id": self.device_id
            }))
            
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    try:
                        data = json.loads(msg.data)
                        _LOG.debug(f"Device {self.device_id}: WebSocket message received: {data}")
                    except json.JSONDecodeError:
                        _LOG.warning(f"Device {self.device_id}: Invalid JSON received via WebSocket")
                elif msg.type == WSMsgType.ERROR:
                    _LOG.error(f"Device {self.device_id}: WebSocket error: {ws.exception()}")
                    break
                    
        except Exception as e:
            _LOG.error(f"Device {self.device_id}: WebSocket error: {e}")
        finally:
            self.websocket_clients.discard(ws)
            _LOG.info(f"Device {self.device_id}: WebSocket client disconnected. Total clients: {len(self.websocket_clients)}")
            
        return ws
    
    async def _broadcast_event(self, event: Dict[str, Any]) -> None:
        """Broadcast event to all WebSocket clients."""
        if not self.websocket_clients:
            return
            
        event["timestamp"] = int(time.time())
        event["device_id"] = self.device_id
        message = json.dumps(event)
        dead_clients = set()
        
        for client in self.websocket_clients:
            try:
                await client.send_str(message)
            except Exception as e:
                _LOG.warning(f"Device {self.device_id}: Failed to send to WebSocket client: {e}")
                dead_clients.add(client)
        
        # Remove dead clients
        self.websocket_clients -= dead_clients
    
    def _start_position_update(self):
        """Start position update task."""
        if self._position_task is None:
            self._position_task = asyncio.create_task(self._position_updater())
    
    async def _position_updater(self):
        """Update position when playing."""
        while True:
            try:
                await asyncio.sleep(1)
                if self.state["power"] and self.state["playback_state"] == "2":  # playing
                    self.state["position"] += 1000  # add 1 second in milliseconds
                    if self.state["position"] >= self.state["duration"]:
                        # Track ended, go to next
                        await self._change_track()
            except asyncio.CancelledError:
                break
            except Exception as e:
                _LOG.error(f"Device {self.device_id}: Position update error: {e}")
    
    async def _change_track(self) -> None:
        """Change to a random track."""
        track = random.choice(self.sample_tracks)
        self.state.update({
            "title": track["title"],
            "artist": track["artist"],
            "album": track["album"],
            "station": track["station"],
            "genre": track["genre"],
            "duration": track["duration"],
            "position": 0,
            "artwork": f"https://example.com/artwork/device_{self.device_id}_{track['title'].replace(' ', '_').lower()}.jpg"
        })
        
        await self._broadcast_event({
            "type": "track_change",
            "title": track["title"],
            "artist": track["artist"],
            "album": track["album"],
            "duration": track["duration"],
            "artwork": self.state["artwork"]
        })
    
    async def start(self) -> None:
        """Start the simulator server."""
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()
        
        _LOG.info(f"Naim Atom Simulator {self.device_id} started and bound to {self.host}:{self.port}")
        _LOG.info(f"Device Name: {self.device_name}")
        _LOG.info(f"Current state: Power {'ON' if self.state['power'] else 'OFF'}, Playing {self.state['source']}")


class MultiDeviceSimulator:
    """Manages multiple Naim device simulators."""
    
    def __init__(self):
        self.simulators: List[NaimAtomSimulator] = []
        self.base_port = 8080
        self.host = get_local_ip()
    
    async def create_simulators(self, count: int = 3) -> List[Dict[str, Any]]:
        """Create multiple device simulators."""
        device_configs = []
        
        for i in range(count):
            device_id = i + 1
            port = self.base_port + i
            device_name = f"Naim-Simulator-{device_id}"
            
            simulator = NaimAtomSimulator(
                host=self.host,
                port=port,
                device_name=device_name,
                device_id=device_id
            )
            
            self.simulators.append(simulator)
            
            device_configs.append({
                "device_id": device_id,
                "name": device_name,
                "ip": self.host,
                "port": port,
                "url": f"http://{self.host}:{port}"
            })
        
        return device_configs
    
    async def start_all(self) -> None:
        """Start all simulators."""
        _LOG.info(f"Starting {len(self.simulators)} Naim device simulators...")
        
        start_tasks = [simulator.start() for simulator in self.simulators]
        await asyncio.gather(*start_tasks)
        
        _LOG.info("")
        _LOG.info("=" * 70)
        _LOG.info("🎵 Multi-Device Naim Simulator Ready")
        _LOG.info("=" * 70)
        _LOG.info("")
        _LOG.info("Use these addresses in the integration setup:")
        for i, simulator in enumerate(self.simulators):
            _LOG.info(f"  Device {i+1}: {simulator.host}:{simulator.port} ({simulator.device_name})")
        _LOG.info("")
        _LOG.info("For multi-device setup:")
        _LOG.info("  1. Set device count to 3")
        _LOG.info("  2. Use the IP addresses above")
        _LOG.info("  3. Each device has different content and state")
        _LOG.info("")


async def main():
    """Main entry point for the multi-device simulator."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Naim Multi-Device Simulator")
    parser.add_argument("--host", default=None, help="Host to bind to (default: auto-detect local IP)")
    parser.add_argument("--port", type=int, default=8080, help="Base port to bind to (default: 8080)")
    parser.add_argument("--count", type=int, default=3, help="Number of devices to simulate (default: 3)")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--single", action="store_true", help="Run single device simulator (legacy mode)")
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    if args.single:
        # Legacy single device mode
        host = args.host if args.host else get_local_ip()
        simulator = NaimAtomSimulator(host, args.port)
        await simulator.start()
        
        _LOG.info("")
        _LOG.info("Use this address in the integration setup:")
        _LOG.info(f"  {host}:{args.port}")
        _LOG.info("")
        
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            _LOG.info("Naim Atom Simulator stopped by user")
    else:
        # Multi-device mode
        multi_sim = MultiDeviceSimulator()
        multi_sim.host = args.host if args.host else get_local_ip()
        multi_sim.base_port = args.port
        
        device_configs = await multi_sim.create_simulators(args.count)
        await multi_sim.start_all()
        
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            _LOG.info("Multi-Device Naim Simulator stopped by user")


if __name__ == "__main__":
    asyncio.run(main())