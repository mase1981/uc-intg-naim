#!/usr/bin/env python3
"""
Naim Atom Device Simulator for Testing.

This simulator provides a web server that mimics the Naim Atom HTTP API
and WebSocket interface for testing the Unfolded Circle integration.

:copyright: (c) 2025 by Meir Miyara.
:license: Mozilla Public License Version 2.0, see LICENSE for more details.
"""

import asyncio
import json
import logging
import random
import socket
import time
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
    
    def __init__(self, host: str = None, port: int = 8080):
        """Initialize the simulator."""
        self.host = host if host else get_local_ip()
        self.port = port
        self.app = web.Application()
        self.websocket_clients: Set[WebSocketResponse] = set()
        
        # Device state - Naim Atom specific
        self.state = {
            "power": True,
            "playback_state": "2",  # 0=stopped, 1=paused, 2=playing, 3=buffering
            "volume": 50,
            "muted": False,
            "source": "spotify",
            "position": 45000,  # milliseconds
            "duration": 180000,  # milliseconds
            "title": "Bohemian Rhapsody",
            "artist": "Queen",
            "album": "A Night at the Opera",
            "station": "Queen Radio",
            "genre": "Rock",
            "artwork": "https://example.com/artwork.jpg",
            "device_name": "Atom-Simulator",
            "model": "32",
            "hostname": "Atom-Simulator",
            "serial": "ATOM123456",
            "system_version": "3.10.1.5617",
            "api_version": "1.4.0",
            "device_id": "naim_atom_001",
            "balance": 0,
            "live": False,
            "repeat": False,
            "shuffle": False
        }
        
        # Available sources for Naim Atom based on discovery data
        self.sources = [
            "ana1", "dig1", "dig2", "dig3", "hdmi", "bluetooth", 
            "radio", "spotify", "tidal", "qobuz", "usb", "airplay", 
            "gcast", "upnp", "playqueue", "files"
        ]
        
        # Sample tracks for simulation
        self.sample_tracks = [
            {
                "title": "Bohemian Rhapsody",
                "artist": "Queen", 
                "album": "A Night at the Opera",
                "station": "Queen Radio",
                "genre": "Rock",
                "duration": 355000
            },
            {
                "title": "Stairway to Heaven",
                "artist": "Led Zeppelin",
                "album": "Led Zeppelin IV",
                "station": "Classic Rock", 
                "genre": "Rock",
                "duration": 482000
            },
            {
                "title": "Hotel California",
                "artist": "Eagles",
                "album": "Hotel California",
                "station": "Eagles Radio",
                "genre": "Rock",
                "duration": 391000
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
            "udid": "5F9EC1B3-ED59-79BB-0020-B8804F34E027",
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
            data = await request.json()
            system_state = data.get("system", "").lower()
            
            if system_state == "on":
                self.state["power"] = True
                _LOG.info("Power turned ON")
                await self._broadcast_event({
                    "type": "power_change",
                    "power": True
                })
            elif system_state in ["off", "lona", "standby"]:
                self.state["power"] = False
                self.state["playback_state"] = "0"  # stopped
                _LOG.info("Power turned OFF")
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
        """Handle now playing request."""
        if not self.state["power"]:
            return web.json_response({"error": "Device is off"}, status=503)
        
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
            "repeat": "1" if self.state["repeat"] else "0",
            "restrictPause": "0",
            "restrictResume": "0",
            "restrictSeek": "0",
            "restrictStop": "0",
            "sampleRate": "44100",
            "shuffle": "1" if self.state["shuffle"] else "0",
            "source": f"inputs/{self.state['source']}",
            "sourceMultiroom": "inputs/none",
            "station": self.state["station"],
            "title": self.state["title"],
            "artist": self.state["artist"],
            "album": self.state["album"],
            "transportPosition": str(self.state["position"]),
            "transportState": self.state["playback_state"]
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
                    _LOG.info(f"Volume set to {vol}")
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
            mute_state = mute.lower() in ["on", "1", "true"]
            self.state["muted"] = mute_state
            _LOG.info(f"Mute set to {mute_state}")
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
                    _LOG.info(f"Balance set to {bal}")
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
        
        if cmd and cmd != "select":
            return web.json_response({"error": "Only 'select' command supported"}, status=400)
        
        if source in self.sources:
            old_source = self.state["source"]
            self.state["source"] = source
            
            # Change track when switching to music sources
            if source in ["spotify", "tidal", "qobuz", "radio", "usb", "upnp"]:
                await self._change_track()
            
            _LOG.info(f"Source changed from {old_source} to {source}")
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
            "macAddress": "AA:BB:CC:DD:EE:FF",
            "netmask": "255.255.255.0",
            "workgroup": "NAIM"
        })
    
    async def handle_websocket(self, request: Request) -> WebSocketResponse:
        """Handle WebSocket connections."""
        ws = WebSocketResponse()
        await ws.prepare(request)
        
        self.websocket_clients.add(ws)
        _LOG.info("WebSocket client connected. Total clients: %d", len(self.websocket_clients))
        
        try:
            # Send initial status
            await ws.send_str(json.dumps({
                "type": "status",
                "data": self.state,
                "timestamp": int(time.time())
            }))
            
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    try:
                        data = json.loads(msg.data)
                        _LOG.debug("WebSocket message received: %s", data)
                    except json.JSONDecodeError:
                        _LOG.warning("Invalid JSON received via WebSocket")
                elif msg.type == WSMsgType.ERROR:
                    _LOG.error("WebSocket error: %s", ws.exception())
                    break
                    
        except Exception as e:
            _LOG.error("WebSocket error: %s", e)
        finally:
            self.websocket_clients.discard(ws)
            _LOG.info("WebSocket client disconnected. Total clients: %d", len(self.websocket_clients))
            
        return ws
    
    async def _broadcast_event(self, event: Dict[str, Any]) -> None:
        """Broadcast event to all WebSocket clients."""
        if not self.websocket_clients:
            return
            
        event["timestamp"] = int(time.time())
        message = json.dumps(event)
        dead_clients = set()
        
        for client in self.websocket_clients:
            try:
                await client.send_str(message)
            except Exception as e:
                _LOG.warning("Failed to send to WebSocket client: %s", e)
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
                _LOG.error("Position update error: %s", e)
    
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
            "artwork": f"https://example.com/artwork/{track['title'].replace(' ', '_').lower()}.jpg"
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
        
        _LOG.info("Naim Atom Simulator started and bound to %s:%d", self.host, self.port)
        _LOG.info("")
        _LOG.info("Use this address in the integration setup:")
        _LOG.info("  %s:%d", self.host, self.port)
        _LOG.info("")
        _LOG.info("Current state: Power %s, Playing %s", 
                 "ON" if self.state["power"] else "OFF",
                 self.state["source"])
        _LOG.info("")


async def main():
    """Main entry point for the simulator."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Naim Atom Device Simulator")
    parser.add_argument("--host", default=None, help="Host to bind to (default: auto-detect local IP)")
    parser.add_argument("--port", type=int, default=8080, help="Port to bind to (default: 8080)")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    host = args.host if args.host else get_local_ip()
    
    simulator = NaimAtomSimulator(host, args.port)
    await simulator.start()
    
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        _LOG.info("Naim Atom Simulator stopped by user")


if __name__ == "__main__":
    asyncio.run(main())