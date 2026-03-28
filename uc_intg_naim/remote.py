"""
Naim remote entity.

:copyright: (c) 2025-2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

from __future__ import annotations

import logging
from typing import Any

from ucapi import StatusCodes
from ucapi.remote import Attributes, Commands, Features, States
from ucapi_framework import RemoteEntity

from uc_intg_naim.config import NaimConfig
from uc_intg_naim.const import SOURCE_MAP
from uc_intg_naim.device import NaimDevice

_LOG = logging.getLogger(__name__)

_SIMPLE_COMMANDS = [
    "POWER_ON",
    "POWER_OFF",
    "POWER_TOGGLE",
    "VOLUME_UP",
    "VOLUME_DOWN",
    "MUTE_TOGGLE",
    "MUTE",
    "UNMUTE",
    "PLAY",
    "PAUSE",
    "PLAY_PAUSE",
    "STOP",
    "NEXT",
    "PREVIOUS",
] + list(SOURCE_MAP.keys())


def _create_ui() -> list[dict[str, Any]]:
    return [
        {
            "page_id": "playback",
            "name": "Playback",
            "grid": {"width": 4, "height": 6},
            "items": [
                {"type": "text", "text": "On", "command": {"cmd_id": "POWER_ON"},
                 "location": {"x": 0, "y": 0}},
                {"type": "text", "text": "Off", "command": {"cmd_id": "POWER_OFF"},
                 "location": {"x": 1, "y": 0}},
                {"type": "text", "text": "Mute", "command": {"cmd_id": "MUTE_TOGGLE"},
                 "location": {"x": 2, "y": 0}},
                {"type": "text", "text": "Vol+", "command": {"cmd_id": "VOLUME_UP"},
                 "location": {"x": 3, "y": 0}},
                {"type": "icon", "icon": "uc:prev", "command": {"cmd_id": "PREVIOUS"},
                 "location": {"x": 0, "y": 1}},
                {"type": "text", "text": "Play/Pause", "command": {"cmd_id": "PLAY_PAUSE"},
                 "location": {"x": 1, "y": 1}, "size": {"width": 2, "height": 1}},
                {"type": "icon", "icon": "uc:next", "command": {"cmd_id": "NEXT"},
                 "location": {"x": 3, "y": 1}},
                {"type": "text", "text": "Stop", "command": {"cmd_id": "STOP"},
                 "location": {"x": 0, "y": 2}},
                {"type": "text", "text": "Vol-", "command": {"cmd_id": "VOLUME_DOWN"},
                 "location": {"x": 3, "y": 2}},
            ],
        },
        {
            "page_id": "sources",
            "name": "Sources",
            "grid": {"width": 4, "height": 6},
            "items": [
                {"type": "text", "text": "Radio", "command": {"cmd_id": "SOURCE_RADIO"},
                 "location": {"x": 0, "y": 0}},
                {"type": "text", "text": "Spotify", "command": {"cmd_id": "SOURCE_SPOTIFY"},
                 "location": {"x": 1, "y": 0}},
                {"type": "text", "text": "TIDAL", "command": {"cmd_id": "SOURCE_TIDAL"},
                 "location": {"x": 2, "y": 0}},
                {"type": "text", "text": "Qobuz", "command": {"cmd_id": "SOURCE_QOBUZ"},
                 "location": {"x": 3, "y": 0}},
                {"type": "text", "text": "BT", "command": {"cmd_id": "SOURCE_BLUETOOTH"},
                 "location": {"x": 0, "y": 1}},
                {"type": "text", "text": "AirPlay", "command": {"cmd_id": "SOURCE_AIRPLAY"},
                 "location": {"x": 1, "y": 1}},
                {"type": "text", "text": "Cast", "command": {"cmd_id": "SOURCE_GCAST"},
                 "location": {"x": 2, "y": 1}},
                {"type": "text", "text": "UPnP", "command": {"cmd_id": "SOURCE_UPNP"},
                 "location": {"x": 3, "y": 1}},
                {"type": "text", "text": "HDMI", "command": {"cmd_id": "SOURCE_HDMI"},
                 "location": {"x": 0, "y": 2}},
                {"type": "text", "text": "Dig 1", "command": {"cmd_id": "SOURCE_DIG1"},
                 "location": {"x": 1, "y": 2}},
                {"type": "text", "text": "Dig 2", "command": {"cmd_id": "SOURCE_DIG2"},
                 "location": {"x": 2, "y": 2}},
                {"type": "text", "text": "Ana 1", "command": {"cmd_id": "SOURCE_ANA1"},
                 "location": {"x": 3, "y": 2}},
                {"type": "text", "text": "USB", "command": {"cmd_id": "SOURCE_USB"},
                 "location": {"x": 0, "y": 3}},
                {"type": "text", "text": "Queue", "command": {"cmd_id": "SOURCE_PLAYQUEUE"},
                 "location": {"x": 1, "y": 3}},
                {"type": "text", "text": "Files", "command": {"cmd_id": "SOURCE_FILES"},
                 "location": {"x": 2, "y": 3}},
            ],
        },
    ]


class NaimRemote(RemoteEntity):

    def __init__(self, device_config: NaimConfig, device: NaimDevice) -> None:
        self._device = device
        self._device_config = device_config

        fav_commands = []
        for i, fav in enumerate(device_config.favourites, 1):
            fav_commands.append(f"FAVOURITE_{i}")

        all_commands = _SIMPLE_COMMANDS + fav_commands

        attributes = {Attributes.STATE: States.OFF}

        super().__init__(
            f"remote.{device_config.identifier}",
            f"{device_config.name} Remote",
            [Features.ON_OFF, Features.SEND_CMD],
            attributes,
            simple_commands=all_commands,
            ui_pages=_create_ui(),
            cmd_handler=self._handle_command,
        )
        self.subscribe_to_device(device)

    async def sync_state(self) -> None:
        state = States.ON if self._device.power else States.OFF
        self.update({Attributes.STATE: state})

    async def _handle_command(
        self, entity: RemoteEntity, cmd_id: str, params: dict[str, Any] | None = None
    ) -> StatusCodes:
        params = params or {}

        if cmd_id == Commands.ON:
            await self._device.turn_on()
            return StatusCodes.OK
        if cmd_id == Commands.OFF:
            await self._device.turn_off()
            return StatusCodes.OK

        if cmd_id == Commands.SEND_CMD:
            command = params.get("command", "")
            if not command:
                return StatusCodes.BAD_REQUEST
            return await self._dispatch(command)

        return StatusCodes.NOT_IMPLEMENTED

    async def _dispatch(self, command: str) -> StatusCodes:
        dev = self._device
        try:
            if command == "POWER_ON":
                await dev.turn_on()
            elif command == "POWER_OFF":
                await dev.turn_off()
            elif command == "POWER_TOGGLE":
                if dev.power:
                    await dev.turn_off()
                else:
                    await dev.turn_on()
            elif command == "VOLUME_UP":
                await dev.cmd_volume_up()
            elif command == "VOLUME_DOWN":
                await dev.cmd_volume_down()
            elif command == "MUTE_TOGGLE":
                if dev.muted:
                    await dev.cmd_unmute()
                else:
                    await dev.cmd_mute()
            elif command == "MUTE":
                await dev.cmd_mute()
            elif command == "UNMUTE":
                await dev.cmd_unmute()
            elif command == "PLAY":
                await dev.cmd_play()
            elif command == "PAUSE":
                await dev.cmd_pause()
            elif command == "PLAY_PAUSE":
                if dev.play_state == "playing":
                    await dev.cmd_pause()
                else:
                    await dev.cmd_play()
            elif command == "STOP":
                await dev.cmd_stop()
            elif command == "NEXT":
                await dev.cmd_next()
            elif command == "PREVIOUS":
                await dev.cmd_previous()
            elif command in SOURCE_MAP:
                await dev.cmd_select_source(SOURCE_MAP[command])
            elif command.startswith("FAVOURITE_"):
                return await self._play_favourite(command)
            else:
                _LOG.warning("Unknown remote command: %s", command)
                return StatusCodes.NOT_IMPLEMENTED

            return StatusCodes.OK

        except Exception as err:
            _LOG.error("Remote command %s failed: %s", command, err)
            return StatusCodes.SERVER_ERROR

    async def _play_favourite(self, command: str) -> StatusCodes:
        try:
            fav_num = int(command.split("_")[1])
            favs = self._device_config.favourites
            if 0 < fav_num <= len(favs):
                fav = favs[fav_num - 1]
                ussi = fav.get("ussi", "")
                fav_id = ussi.split("/", 1)[1] if "/" in ussi else ussi
                await self._device.cmd_play_favourite(fav_id)
                return StatusCodes.OK
            _LOG.warning("Favourite #%d not found", fav_num)
            return StatusCodes.BAD_REQUEST
        except (ValueError, IndexError) as err:
            _LOG.error("Invalid favourite command %s: %s", command, err)
            return StatusCodes.BAD_REQUEST
