"""
Naim audio device HTTP API client.

:copyright: (c) 2025-2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

from __future__ import annotations

import logging
from typing import Any

import aiohttp

from uc_intg_naim.const import CONNECT_TIMEOUT, DEFAULT_SOURCE_NAMES, REQUEST_TIMEOUT

_LOG = logging.getLogger(__name__)


class NaimClient:

    def __init__(self, host: str, port: int) -> None:
        self._host = host
        self._port = port
        self._base_url = f"http://{host}:{port}"
        self._api_base = self._base_url
        self._session: aiohttp.ClientSession | None = None
        self._device_info: dict[str, Any] = {}
        self._available_inputs: list[dict[str, Any]] = []
        self._favourites: list[dict[str, Any]] = []
        self._connected = False

    @property
    def is_connected(self) -> bool:
        return self._connected

    @property
    def device_info(self) -> dict[str, Any]:
        return self._device_info

    @property
    def available_inputs(self) -> list[dict[str, Any]]:
        return self._available_inputs

    @property
    def favourites(self) -> list[dict[str, Any]]:
        return self._favourites

    async def connect(self) -> bool:
        if self._session is None:
            timeout = aiohttp.ClientTimeout(total=CONNECT_TIMEOUT)
            self._session = aiohttp.ClientSession(timeout=timeout)

        if not await self._detect_api_prefix():
            return False

        system_info = await self._get("/system")
        if system_info and isinstance(system_info, dict) and "raw_response" not in system_info:
            self._device_info = system_info
            _LOG.info(
                "Connected to %s (%s) at %s",
                system_info.get("model", "Unknown"),
                system_info.get("hostname", ""),
                self._api_base,
            )

        inputs_data = await self._get("/inputs")
        if inputs_data and isinstance(inputs_data, dict) and "children" in inputs_data:
            self._available_inputs = inputs_data["children"]
        elif inputs_data and isinstance(inputs_data, list):
            self._available_inputs = inputs_data

        fav_data = await self._get("/favourites")
        if fav_data:
            raw = fav_data if isinstance(fav_data, list) else fav_data.get("children", [])
            self._favourites = [f for f in raw if f.get("available") == "1"]
            _LOG.info("Discovered %d favourites", len(self._favourites))

        self._connected = True
        return True

    async def disconnect(self) -> None:
        self._connected = False
        if self._session:
            await self._session.close()
            self._session = None

    async def _detect_api_prefix(self) -> bool:
        self._api_base = self._base_url
        root = await self._get("/")
        if not root:
            return False

        if isinstance(root, dict) and "raw_response" in root:
            text = root["raw_response"]
            if "naim" in text.lower():
                self._api_base = f"{self._base_url}/naim"
                test = await self._get("/system")
                if not test or (isinstance(test, dict) and "raw_response" in test):
                    self._api_base = self._base_url

        return True

    async def _get(self, endpoint: str) -> dict[str, Any] | list | None:
        return await self._request("GET", endpoint)

    async def _put(self, endpoint: str) -> dict[str, Any] | None:
        return await self._request("PUT", endpoint)

    async def _request(
        self, method: str, endpoint: str
    ) -> dict[str, Any] | list | None:
        if not self._session:
            return None

        url = f"{self._api_base}{endpoint}"
        try:
            req_timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)
            async with self._session.request(
                method,
                url,
                headers={"User-Agent": "Naim-Integration/2.0", "Accept": "application/json"},
                timeout=req_timeout,
            ) as resp:
                if resp.status == 200:
                    self._connected = True
                    if resp.content_type == "application/json":
                        return await resp.json()
                    text = await resp.text()
                    if "naim" in text.lower() and "refresh" in text.lower():
                        return {"raw_response": text}
                    return {"response": text}
                _LOG.warning("HTTP %s %s -> %s", method, url, resp.status)
        except Exception as err:
            self._connected = False
            _LOG.error("Request %s %s failed: %s", method, url, err)
        return None

    # --- Power ---

    async def get_power_state(self) -> bool | None:
        data = await self._get("/power")
        if not data or not isinstance(data, dict):
            return None
        state = data.get("state", "").lower()
        system = data.get("system", "").lower()
        return state == "on" or system == "on"

    async def power_on(self) -> bool:
        return await self._put("/power?system=on") is not None

    async def power_off(self) -> bool:
        return await self._put("/power?system=lona") is not None

    # --- Volume ---

    async def get_volume(self) -> dict[str, Any] | None:
        data = await self._get("/levels/room")
        if data and isinstance(data, dict) and "raw_response" not in data:
            return data
        return None

    async def set_volume(self, volume: int) -> bool:
        volume = max(0, min(100, volume))
        return await self._put(f"/levels/room?volume={volume}") is not None

    async def volume_up(self) -> bool:
        vol = await self.get_volume()
        if vol and "volume" in vol:
            return await self.set_volume(int(vol["volume"]) + 1)
        return False

    async def volume_down(self) -> bool:
        vol = await self.get_volume()
        if vol and "volume" in vol:
            return await self.set_volume(int(vol["volume"]) - 1)
        return False

    async def mute(self) -> bool:
        return await self._put("/levels/room?mute=1") is not None

    async def unmute(self) -> bool:
        return await self._put("/levels/room?mute=0") is not None

    # --- Playback ---

    async def get_status(self) -> dict[str, Any] | None:
        data = await self._get("/nowplaying")
        if data and isinstance(data, dict) and "raw_response" not in data:
            return data
        return None

    async def play(self) -> bool:
        return await self._get("/nowplaying?cmd=play") is not None

    async def pause(self) -> bool:
        return await self._get("/nowplaying?cmd=pause") is not None

    async def stop(self) -> bool:
        return await self._get("/nowplaying?cmd=stop") is not None

    async def next_track(self) -> bool:
        return await self._get("/nowplaying?cmd=next") is not None

    async def previous_track(self) -> bool:
        return await self._get("/nowplaying?cmd=prev") is not None

    async def set_repeat(self, mode: str) -> bool:
        values = {"OFF": "0", "ONE": "1", "ALL": "2"}
        val = values.get(mode.upper(), "0")
        return await self._put(f"/nowplaying?repeat={val}") is not None

    async def set_shuffle(self, enabled: bool) -> bool:
        val = "1" if enabled else "0"
        return await self._put(f"/nowplaying?shuffle={val}") is not None

    # --- Sources ---

    async def set_source(self, source: str) -> bool:
        return await self._get(f"/inputs/{source}?cmd=select") is not None

    def get_sources(self) -> list[str]:
        sources = []
        for inp in self._available_inputs:
            if inp.get("disabled") == "1":
                continue
            ussi = inp.get("ussi", "")
            if ussi.startswith("inputs/"):
                sources.append(ussi.split("/")[-1])
        if not sources:
            sources = ["radio", "bluetooth", "spotify", "dig5", "hdmi"]
        return sources

    def get_source_names(self) -> dict[str, str]:
        names: dict[str, str] = {}
        for inp in self._available_inputs:
            ussi = inp.get("ussi", "")
            if ussi.startswith("inputs/"):
                sid = ussi.split("/")[-1]
                names[sid] = inp.get("name", sid)
        return names if names else dict(DEFAULT_SOURCE_NAMES)

    # --- Favourites ---

    async def play_favourite(self, favourite_id: str) -> bool:
        if favourite_id.startswith("favourites/"):
            favourite_id = favourite_id.split("/", 1)[1]
        return await self._get(f"/favourites/{favourite_id}?cmd=play") is not None

    def get_favourite_names(self) -> dict[str, str]:
        result: dict[str, str] = {}
        for fav in self._favourites:
            ussi = fav.get("ussi", "")
            name = fav.get("name", "")
            if ussi and name and "/" in ussi:
                fav_id = ussi.split("/", 1)[1]
                result[fav_id] = name
        return result

    # --- Status Parsing ---

    def parse_status(self, status: dict[str, Any]) -> dict[str, Any]:
        transport = str(status.get("transportState", "0"))
        state_map = {"0": "stopped", "1": "paused", "2": "playing", "3": "buffering"}
        play_state = state_map.get(transport, "stopped")

        source_ussi = status.get("source", "")
        source = source_ussi.split("/")[-1] if "/" in source_ussi else source_ussi

        return {
            "state": play_state,
            "source": source,
            "title": status.get("title", ""),
            "artist": status.get("artist", ""),
            "album": status.get("album", ""),
            "artwork": status.get("artwork", ""),
            "station": status.get("station", ""),
            "position": int(status.get("transportPosition", 0)),
            "repeat": status.get("repeat", "0"),
            "shuffle": status.get("shuffle", "0") == "1",
            "codec": status.get("codec", ""),
            "sample_rate": status.get("sampleRate", ""),
            "bit_depth": status.get("bitDepth", ""),
            "bit_rate": status.get("bitRate", ""),
        }
