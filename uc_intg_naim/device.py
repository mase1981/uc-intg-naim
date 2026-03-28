"""
Naim device wrapper using ucapi-framework.

:copyright: (c) 2025-2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from ucapi_framework.device import ExternalClientDevice, DeviceEvents

from uc_intg_naim.client import NaimClient
from uc_intg_naim.config import NaimConfig
from uc_intg_naim.const import (
    CONNECT_RETRIES,
    CONNECT_RETRY_DELAY,
    MAX_POLL_FAILURES,
    POLL_INTERVAL,
    RECONNECT_DELAY,
    WATCHDOG_INTERVAL,
)

_LOG = logging.getLogger(__name__)


class NaimDevice(ExternalClientDevice):

    def __init__(self, device_config: NaimConfig, **kwargs) -> None:
        super().__init__(
            device_config=device_config,
            enable_watchdog=True,
            watchdog_interval=WATCHDOG_INTERVAL,
            reconnect_delay=RECONNECT_DELAY,
            max_reconnect_attempts=0,
            **kwargs,
        )
        self._client = NaimClient(device_config.host, device_config.port)
        self._poll_task: asyncio.Task | None = None
        self._consecutive_failures: int = 0
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
    def client(self) -> NaimClient:
        return self._client

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

    async def create_client(self) -> Any:
        self._client = NaimClient(self._device_config.host, self._device_config.port)
        return self._client

    async def connect_client(self) -> None:
        last_err: Exception | None = None
        for attempt in range(CONNECT_RETRIES):
            try:
                if not await self._client.connect():
                    raise ConnectionError(f"Cannot connect to {self._device_config.host}")

                self._sources = self._client.get_sources()
                self._source_names = self._client.get_source_names()
                self._favourites = self._client.get_favourite_names()

                await self._poll_state()
                self._consecutive_failures = 0
                self._start_polling()
                _LOG.info("[%s] Connected, %d sources, %d favourites",
                          self.log_id, len(self._sources), len(self._favourites))
                return

            except Exception as err:
                last_err = err
                if attempt < CONNECT_RETRIES - 1:
                    _LOG.warning("[%s] Connect attempt %d/%d failed: %s",
                                 self.log_id, attempt + 1, CONNECT_RETRIES, err)
                    await asyncio.sleep(CONNECT_RETRY_DELAY)

        raise last_err  # type: ignore[misc]

    async def disconnect_client(self) -> None:
        self._stop_polling()
        await self._client.disconnect()

    def check_client_connected(self) -> bool:
        return self._client.is_connected

    def _start_polling(self) -> None:
        if self._poll_task is None or self._poll_task.done():
            self._poll_task = asyncio.create_task(self._poll_loop())

    def _stop_polling(self) -> None:
        if self._poll_task and not self._poll_task.done():
            self._poll_task.cancel()
            self._poll_task = None

    async def _poll_loop(self) -> None:
        while True:
            try:
                await asyncio.sleep(POLL_INTERVAL)
                await self._poll_state()
                self._consecutive_failures = 0
            except asyncio.CancelledError:
                break
            except Exception as err:
                self._consecutive_failures += 1
                _LOG.error("[%s] Poll error (%d/%d): %s",
                           self.log_id, self._consecutive_failures, MAX_POLL_FAILURES, err)
                if self._consecutive_failures >= MAX_POLL_FAILURES:
                    _LOG.warning("[%s] Too many poll failures, triggering reconnect", self.log_id)
                    self._client._connected = False
                    self.events.emit(DeviceEvents.DISCONNECTED, self.identifier)
                    break
                await asyncio.sleep(POLL_INTERVAL)

    async def _poll_state(self) -> None:
        changed = False

        power = await self._client.get_power_state()
        if power is None:
            raise ConnectionError(f"Cannot reach {self._device_config.host}")
        if power != self._power:
            self._power = power
            changed = True

        if self._power:
            vol_data = await self._client.get_volume()
            if vol_data:
                new_vol = int(vol_data.get("volume", 0))
                new_muted = vol_data.get("mute", "0") == "1"
                if new_vol != self._volume or new_muted != self._muted:
                    self._volume = new_vol
                    self._muted = new_muted
                    changed = True

            status = await self._client.get_status()
            if status:
                parsed = self._client.parse_status(status)
                if self._update_from_parsed(parsed):
                    changed = True
        else:
            if self._play_state != "stopped":
                self._play_state = "stopped"
                self._media_title = ""
                self._media_artist = ""
                self._media_album = ""
                self._media_image = ""
                self._media_position = 0
                changed = True

        if changed:
            self.push_update()

    def _update_from_parsed(self, parsed: dict[str, Any]) -> bool:
        changed = False
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
            if new_val is not None and getattr(self, attr) != new_val:
                setattr(self, attr, new_val)
                changed = True

        new_pos = parsed.get("position", 0) // 1000
        if new_pos != self._media_position:
            self._media_position = new_pos
            changed = True

        return changed

    # --- Commands ---

    async def turn_on(self) -> bool:
        if await self._client.power_on():
            self._power = True
            self.push_update()
            return True
        return False

    async def turn_off(self) -> bool:
        if await self._client.power_off():
            self._power = False
            self.push_update()
            return True
        return False

    async def cmd_play(self) -> bool:
        return await self._client.play()

    async def cmd_pause(self) -> bool:
        return await self._client.pause()

    async def cmd_stop(self) -> bool:
        return await self._client.stop()

    async def cmd_next(self) -> bool:
        return await self._client.next_track()

    async def cmd_previous(self) -> bool:
        return await self._client.previous_track()

    async def cmd_volume(self, volume: int) -> bool:
        if await self._client.set_volume(volume):
            self._volume = volume
            self.push_update()
            return True
        return False

    async def cmd_volume_up(self) -> bool:
        return await self._client.volume_up()

    async def cmd_volume_down(self) -> bool:
        return await self._client.volume_down()

    async def cmd_mute(self) -> bool:
        if await self._client.mute():
            self._muted = True
            self.push_update()
            return True
        return False

    async def cmd_unmute(self) -> bool:
        if await self._client.unmute():
            self._muted = False
            self.push_update()
            return True
        return False

    async def cmd_select_source(self, source: str) -> bool:
        return await self._client.set_source(source)

    async def cmd_play_favourite(self, fav_id: str) -> bool:
        return await self._client.play_favourite(fav_id)

    async def cmd_repeat(self, mode: str) -> bool:
        return await self._client.set_repeat(mode)

    async def cmd_shuffle(self, enabled: bool) -> bool:
        return await self._client.set_shuffle(enabled)
