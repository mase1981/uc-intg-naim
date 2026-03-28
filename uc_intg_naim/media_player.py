"""
Naim media player entity.

:copyright: (c) 2025-2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

from __future__ import annotations

import logging
from typing import Any

from ucapi import StatusCodes
from ucapi.media_player import Attributes, Commands, DeviceClasses, Features, States, RepeatMode
from ucapi_framework import MediaPlayerEntity

from uc_intg_naim.config import NaimConfig
from uc_intg_naim.device import NaimDevice

_LOG = logging.getLogger(__name__)

_FEATURES = [
    Features.ON_OFF,
    Features.TOGGLE,
    Features.PLAY_PAUSE,
    Features.STOP,
    Features.NEXT,
    Features.PREVIOUS,
    Features.VOLUME,
    Features.VOLUME_UP_DOWN,
    Features.MUTE_TOGGLE,
    Features.MUTE,
    Features.UNMUTE,
    Features.SELECT_SOURCE,
    Features.REPEAT,
    Features.SHUFFLE,
    Features.MEDIA_TITLE,
    Features.MEDIA_ARTIST,
    Features.MEDIA_ALBUM,
    Features.MEDIA_IMAGE_URL,
    Features.MEDIA_POSITION,
    Features.MEDIA_DURATION,
]


class NaimMediaPlayer(MediaPlayerEntity):

    def __init__(self, device_config: NaimConfig, device: NaimDevice) -> None:
        self._device = device
        self._device_config = device_config

        source_list = list(device_config.sources) if device_config.sources else []
        for fav in device_config.favourites:
            fname = fav.get("name", "")
            if fname:
                source_list.append(f"♫ {fname}")

        attributes = {
            Attributes.STATE: States.OFF,
            Attributes.VOLUME: 0,
            Attributes.MUTED: False,
            Attributes.SOURCE: "",
            Attributes.SOURCE_LIST: source_list,
            Attributes.MEDIA_TITLE: "",
            Attributes.MEDIA_ARTIST: "",
            Attributes.MEDIA_ALBUM: "",
            Attributes.MEDIA_IMAGE_URL: "",
            Attributes.MEDIA_POSITION: 0,
            Attributes.MEDIA_DURATION: 0,
            Attributes.REPEAT: RepeatMode.OFF,
            Attributes.SHUFFLE: False,
        }

        super().__init__(
            f"media_player.{device_config.identifier}",
            device_config.name,
            _FEATURES,
            attributes,
            device_class=DeviceClasses.SPEAKER,
            cmd_handler=self._handle_command,
        )
        self.subscribe_to_device(device)

    async def sync_state(self) -> None:
        dev = self._device
        if dev.power is None or not dev.power:
            state = States.OFF
        elif dev.play_state == "playing":
            state = States.PLAYING
        elif dev.play_state == "paused":
            state = States.PAUSED
        elif dev.play_state == "buffering":
            state = States.BUFFERING
        else:
            state = States.ON

        repeat = RepeatMode.OFF
        if dev.repeat_mode == "1":
            repeat = RepeatMode.ONE
        elif dev.repeat_mode == "2":
            repeat = RepeatMode.ALL

        self.update({
            Attributes.STATE: state,
            Attributes.VOLUME: dev.volume,
            Attributes.MUTED: dev.muted,
            Attributes.SOURCE: dev.source,
            Attributes.MEDIA_TITLE: dev.media_title,
            Attributes.MEDIA_ARTIST: dev.media_artist,
            Attributes.MEDIA_ALBUM: dev.media_album,
            Attributes.MEDIA_IMAGE_URL: dev.media_image,
            Attributes.MEDIA_POSITION: dev.media_position,
            Attributes.MEDIA_DURATION: 0,
            Attributes.REPEAT: repeat,
            Attributes.SHUFFLE: dev.shuffle_mode,
        })

    async def _handle_command(
        self, entity: MediaPlayerEntity, cmd_id: str, params: dict[str, Any] | None = None
    ) -> StatusCodes:
        dev = self._device
        params = params or {}

        try:
            if cmd_id == Commands.ON:
                await dev.turn_on()
            elif cmd_id == Commands.OFF:
                await dev.turn_off()
            elif cmd_id == Commands.TOGGLE:
                if dev.power:
                    await dev.turn_off()
                else:
                    await dev.turn_on()
            elif cmd_id == Commands.PLAY_PAUSE:
                if dev.play_state == "playing":
                    await dev.cmd_pause()
                else:
                    await dev.cmd_play()
            elif cmd_id == Commands.STOP:
                await dev.cmd_stop()
            elif cmd_id == Commands.NEXT:
                await dev.cmd_next()
            elif cmd_id == Commands.PREVIOUS:
                await dev.cmd_previous()
            elif cmd_id == Commands.VOLUME:
                await dev.cmd_volume(int(params.get("volume", 0)))
            elif cmd_id == Commands.VOLUME_UP:
                await dev.cmd_volume_up()
            elif cmd_id == Commands.VOLUME_DOWN:
                await dev.cmd_volume_down()
            elif cmd_id == Commands.MUTE_TOGGLE:
                if dev.muted:
                    await dev.cmd_unmute()
                else:
                    await dev.cmd_mute()
            elif cmd_id == Commands.MUTE:
                await dev.cmd_mute()
            elif cmd_id == Commands.UNMUTE:
                await dev.cmd_unmute()
            elif cmd_id == Commands.SELECT_SOURCE:
                source = params.get("source", "")
                if source.startswith("♫ "):
                    fav_name = source[2:]
                    for fav in self._device_config.favourites:
                        if fav.get("name") == fav_name:
                            ussi = fav.get("ussi", "")
                            fav_id = ussi.split("/", 1)[1] if "/" in ussi else ussi
                            await dev.cmd_play_favourite(fav_id)
                            break
                else:
                    await dev.cmd_select_source(source)
            elif cmd_id == Commands.REPEAT:
                await dev.cmd_repeat(params.get("repeat", "OFF"))
            elif cmd_id == Commands.SHUFFLE:
                await dev.cmd_shuffle(params.get("shuffle", False))
            else:
                return StatusCodes.NOT_IMPLEMENTED

            return StatusCodes.OK

        except Exception as err:
            _LOG.error("Command %s failed: %s", cmd_id, err)
            return StatusCodes.SERVER_ERROR
