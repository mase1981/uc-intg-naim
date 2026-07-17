"""
Naim select entity for input source.

:copyright: (c) 2025-2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

from __future__ import annotations

import logging
from typing import Any

from ucapi import StatusCodes
from ucapi.select import Attributes, Commands, States
from ucapi_framework import SelectEntity

from uc_intg_naim.config import NaimConfig
from uc_intg_naim.const import DEFAULT_SOURCE_NAMES, UNSELECTABLE_SOURCES
from uc_intg_naim.device import NaimDevice

_LOG = logging.getLogger(__name__)


class NaimSourceSelect(SelectEntity):

    def __init__(self, device_config: NaimConfig, device: NaimDevice) -> None:
        self._device = device
        self._device_config = device_config

        source_names = device.source_names or {}
        self._source_to_display = {
            src: source_names.get(src, src)
            for src in device_config.sources
            if src not in UNSELECTABLE_SOURCES
        }
        self._display_to_source = {v: k for k, v in self._source_to_display.items()}

        attributes = {
            Attributes.STATE: States.UNKNOWN,
            Attributes.OPTIONS: [],
            Attributes.CURRENT_OPTION: "",
        }

        super().__init__(
            f"select.{device_config.identifier}.source",
            f"{device_config.name} Source",
            attributes,
            cmd_handler=self._handle_command,
        )
        self.subscribe_to_device(device)

    async def sync_state(self) -> None:
        dev = self._device
        if dev.state == "UNAVAILABLE":
            self.update({Attributes.STATE: States.UNAVAILABLE})
            return

        source_names = dev.source_names or {}
        if source_names:
            self._source_to_display = {
                src: source_names.get(src, src)
                for src in self._device_config.sources
                if src not in UNSELECTABLE_SOURCES
            }
            self._display_to_source = {v: k for k, v in self._source_to_display.items()}
        options = list(self._source_to_display.values())
        current = self._source_to_display.get(dev.source)
        if current is None and dev.source:
            current = source_names.get(
                dev.source, DEFAULT_SOURCE_NAMES.get(dev.source, dev.source)
            )
            if current not in options:
                options = options + [current]
        self.update({
            Attributes.STATE: States.ON if dev.power else States.UNKNOWN,
            Attributes.OPTIONS: options,
            Attributes.CURRENT_OPTION: current or "",
        })

    async def _handle_command(
        self, entity: SelectEntity, cmd_id: str, params: dict[str, Any] | None = None
    ) -> StatusCodes:
        params = params or {}

        if cmd_id == Commands.SELECT_OPTION and params.get("option"):
            display = params["option"]
            source = self._display_to_source.get(display, display)
            if await self._device.cmd_select_source(source):
                return StatusCodes.OK
            return StatusCodes.SERVER_ERROR

        return StatusCodes.NOT_IMPLEMENTED
