"""
Naim device wrapper using ucapi-framework.

:copyright: (c) 2025-2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from ucapi_framework import PollingDevice, DeviceEvents

from uc_intg_naim.client import NaimClient
from uc_intg_naim.config import NaimConfig
from uc_intg_naim.const import POLL_INTERVAL

_LOG = logging.getLogger(__name__)


class NaimDevice(PollingDevice):

    def __init__(self, device_config: NaimConfig, **kwargs: Any) -> None:
        super().__init__(device_config, poll_interval=POLL_INTERVAL, **kwargs)
        self._device_config = device_config
        self._client: NaimClient | None = None
        self._connect_lock: asyncio.Lock = asyncio.Lock()
        self._state: str = "UNAVAILABLE"
        self._power: bool | None = None
        self._volume: int = 0
        self._muted: bool = False
        self._play_state: str = "stopped"
        self._source: str = ""
        self._media_title: str = ""
        self._media_artist: str = ""
        self._media_album: str = ""
        self._media_image: str = ""
        self._media_position: int = 0
        self._media_duration: int = 0
        self._repeat: str = "0"
        self._shuffle: bool = False
        self._codec: str = ""
        self._sample_rate: str = ""
        self._bit_depth: str = ""
        self._sources: list[str] = list(device_config.sources) if device_config.sources else []
        self._source_names: dict[str, str] = {}
        self._favourites: dict[str, str] = {}

    @property
    def identifier(self) -> str:
        return self._device_config.identifier

    @property
    def name(self) -> str:
        return self._device_config.name

    @property
    def address(self) -> str | None:
        return self._device_config.host

    @property
    def log_id(self) -> str:
        return f"Naim-{self._device_config.host}"

    @property
    def config(self) -> NaimConfig:
        return self._device_config

    @property
    def state(self) -> str:
        return self._state

    @property
    def power(self) -> bool | None:
        return self._power

    @property
    def volume(self) -> int:
        return self._volume

    @property
    def muted(self) -> bool:
        return self._muted

    @property
    def play_state(self) -> str:
        return self._play_state

    @property
    def source(self) -> str:
        return self._source

    @property
    def sources(self) -> list[str]:
        return self._sources

    @property
    def source_names(self) -> dict[str, str]:
        return self._source_names

    @property
    def favourite_names(self) -> dict[str, str]:
        return self._favourites

    @property
    def media_title(self) -> str:
        return self._media_title

    @property
    def media_artist(self) -> str:
        return self._media_artist

    @property
    def media_album(self) -> str:
        return self._media_album

    @property
    def media_image(self) -> str:
        return self._media_image

    @property
    def media_position(self) -> int:
        return self._media_position

    @property
    def media_duration(self) -> int:
        return self._media_duration

    @property
    def repeat_mode(self) -> str:
        return self._repeat

    @property
    def shuffle_mode(self) -> bool:
        return self._shuffle

    @property
    def codec(self) -> str:
        return self._codec

    @property
    def sample_rate(self) -> str:
        return self._sample_rate

    @property
    def bit_depth(self) -> str:
        return self._bit_depth

    async def establish_connection(self) -> NaimClient:
        # Never raise when the streamer is unreachable: a failed connect() is not
        # retried by the framework (e.g. Remote waking from standby before its
        # Wi-Fi is up), which left entities offline until a Remote reboot.
        # The poll loop keeps running and reconnects once the device is back.
        if not await self._reconnect():
            _LOG.warning(
                "[%s] Device unreachable, will keep retrying in the background",
                self.log_id,
            )
            self._state = "UNAVAILABLE"
            self.push_update()
            return self._client

        try:
            await self._update_state()
        except ConnectionError:
            _LOG.warning("[%s] Initial state query failed, using defaults", self.log_id)
            self._state = "ON"

        _LOG.info("[%s] Connected, %d sources, %d favourites",
                  self.log_id, len(self._sources), len(self._favourites))
        return self._client

    async def _reconnect(self) -> bool:
        async with self._connect_lock:
            if self._client is None:
                self._client = NaimClient(self._device_config.host, self._device_config.port)
            if self._client.is_connected:
                return True
            try:
                if not await self._client.connect():
                    return False
            except Exception as err:  # pylint: disable=broad-exception-caught
                _LOG.debug("[%s] Reconnect failed: %s", self.log_id, err)
                return False

            self._sources = self._client.get_sources()
            self._source_names = self._client.get_source_names()
            self._favourites = self._client.get_favourite_names()
            return True

    async def _ensure_connected(self) -> bool:
        if self._client is not None and self._client.is_connected:
            return True
        if await self._reconnect():
            return True
        _LOG.warning("[%s] Device unreachable, command not sent", self.log_id)
        return False

    async def poll_device(self) -> None:
        try:
            if not await self._reconnect():
                raise ConnectionError(f"Cannot reach {self._device_config.host}")
            await self._update_state()
            self.push_update()
        except Exception as err:
            _LOG.debug("[%s] Poll error: %s", self.log_id, err)
            if self._state != "UNAVAILABLE":
                self._state = "UNAVAILABLE"
                self.events.emit(DeviceEvents.DISCONNECTED, self.identifier)

    async def disconnect(self) -> None:
        self._state = "UNAVAILABLE"
        # Stop the poll task first so it cannot reopen the client while closing.
        await super().disconnect()
        async with self._connect_lock:
            if self._client:
                await self._client.disconnect()
                self._client = None

    async def _update_state(self) -> None:
        power = await self._client.get_power_state()
        if power is None:
            raise ConnectionError(f"Cannot reach {self._device_config.host}")
        self._power = power

        if self._power:
            vol_data = await self._client.get_volume()
            if vol_data:
                self._volume = int(vol_data.get("volume", 0))
                self._muted = vol_data.get("mute", "0") == "1"

            status = await self._client.get_status()
            if status:
                parsed = self._client.parse_status(status)
                self._update_from_parsed(parsed)

            state_map = {"playing": "PLAYING", "paused": "PAUSED", "buffering": "BUFFERING"}
            self._state = state_map.get(self._play_state, "ON")
        else:
            self._state = "OFF"
            self._play_state = "stopped"
            self._media_title = ""
            self._media_artist = ""
            self._media_album = ""
            self._media_image = ""
            self._media_position = 0
            self._media_duration = 0

    def _update_from_parsed(self, parsed: dict[str, Any]) -> None:
        for attr, key in [
            ("_play_state", "state"),
            ("_source", "source"),
            ("_media_title", "title"),
            ("_media_artist", "artist"),
            ("_media_album", "album"),
            ("_media_image", "artwork"),
            ("_repeat", "repeat"),
            ("_shuffle", "shuffle"),
            ("_codec", "codec"),
            ("_sample_rate", "sample_rate"),
            ("_bit_depth", "bit_depth"),
        ]:
            new_val = parsed.get(key)
            if new_val is not None:
                setattr(self, attr, new_val)

        self._media_position = parsed.get("position", 0) // 1000
        self._media_duration = parsed.get("duration", 0) // 1000

    # --- Commands ---

    async def turn_on(self) -> bool:
        if not await self._ensure_connected():
            return False
        if await self._client.power_on():
            self._power = True
            self._state = "ON"
            self.push_update()
            return True
        return False

    async def turn_off(self) -> bool:
        if not await self._ensure_connected():
            return False
        if await self._client.power_off():
            self._power = False
            self._state = "OFF"
            self.push_update()
            return True
        return False

    async def cmd_play(self) -> bool:
        if not await self._ensure_connected():
            return False
        return await self._client.play()

    async def cmd_pause(self) -> bool:
        if not await self._ensure_connected():
            return False
        return await self._client.pause()

    async def cmd_stop(self) -> bool:
        if not await self._ensure_connected():
            return False
        return await self._client.stop()

    async def cmd_next(self) -> bool:
        if not await self._ensure_connected():
            return False
        return await self._client.next_track()

    async def cmd_previous(self) -> bool:
        if not await self._ensure_connected():
            return False
        return await self._client.previous_track()

    async def cmd_volume(self, volume: int) -> bool:
        if not await self._ensure_connected():
            return False
        if await self._client.set_volume(volume):
            self._volume = volume
            self.push_update()
            return True
        return False

    async def cmd_volume_up(self) -> bool:
        if not await self._ensure_connected():
            return False
        new_vol = min(100, self._volume + 1)
        if await self._client.set_volume(new_vol):
            self._volume = new_vol
            self.push_update()
            return True
        return False

    async def cmd_volume_down(self) -> bool:
        if not await self._ensure_connected():
            return False
        new_vol = max(0, self._volume - 1)
        if await self._client.set_volume(new_vol):
            self._volume = new_vol
            self.push_update()
            return True
        return False

    async def cmd_mute(self) -> bool:
        if not await self._ensure_connected():
            return False
        if await self._client.mute():
            self._muted = True
            self.push_update()
            return True
        return False

    async def cmd_unmute(self) -> bool:
        if not await self._ensure_connected():
            return False
        if await self._client.unmute():
            self._muted = False
            self.push_update()
            return True
        return False

    async def cmd_select_source(self, source: str) -> bool:
        if not await self._ensure_connected():
            return False
        return await self._client.set_source(source)

    async def cmd_play_favourite(self, fav_id: str) -> bool:
        if not await self._ensure_connected():
            return False
        return await self._client.play_favourite(fav_id)

    async def browse_ussi(
        self, ussi: str, offset: int = 0, limit: int = 50
    ) -> dict[str, Any] | None:
        if not await self._ensure_connected():
            return None
        return await self._client.browse(ussi, offset, limit)

    async def cmd_play_ussi(self, ussi: str) -> bool:
        if not await self._ensure_connected():
            return False
        return await self._client.play_ussi(ussi)

    async def cmd_repeat(self, mode: str) -> bool:
        if not await self._ensure_connected():
            return False
        return await self._client.set_repeat(mode)

    async def cmd_shuffle(self, enabled: bool) -> bool:
        if not await self._ensure_connected():
            return False
        return await self._client.set_shuffle(enabled)
