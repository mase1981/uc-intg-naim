"""
Naim sensor entities.

:copyright: (c) 2025-2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

from __future__ import annotations

import logging

from ucapi.sensor import Attributes, States
from ucapi_framework import SensorEntity

from uc_intg_naim.config import NaimConfig
from uc_intg_naim.device import NaimDevice

_LOG = logging.getLogger(__name__)


class _BaseSensor(SensorEntity):

    def __init__(
        self,
        device_config: NaimConfig,
        device: NaimDevice,
        suffix: str,
        label: str,
    ) -> None:
        self._device = device
        self._device_config = device_config

        attributes = {
            Attributes.STATE: States.UNKNOWN,
            Attributes.VALUE: "",
        }

        super().__init__(
            f"sensor.{device_config.identifier}.{suffix}",
            f"{device_config.name} {label}",
            [],
            attributes,
            device_class=None,
        )
        self.subscribe_to_device(device)


class NaimStateSensor(_BaseSensor):

    def __init__(self, device_config: NaimConfig, device: NaimDevice) -> None:
        super().__init__(device_config, device, "state", "State")

    async def sync_state(self) -> None:
        dev = self._device
        if dev.power is None or not dev.power:
            value = "Off"
        elif dev.play_state == "playing":
            value = "Playing"
        elif dev.play_state == "paused":
            value = "Paused"
        elif dev.play_state == "buffering":
            value = "Buffering"
        else:
            value = "Idle"

        self.update({
            Attributes.STATE: States.ON,
            Attributes.VALUE: value,
        })


class NaimSourceSensor(_BaseSensor):

    def __init__(self, device_config: NaimConfig, device: NaimDevice) -> None:
        super().__init__(device_config, device, "source", "Source")

    async def sync_state(self) -> None:
        dev = self._device
        source = dev.source
        display = dev.source_names.get(source, source) if source else ""
        self.update({
            Attributes.STATE: States.ON if source else States.UNKNOWN,
            Attributes.VALUE: display,
        })


class NaimAudioFormatSensor(_BaseSensor):

    def __init__(self, device_config: NaimConfig, device: NaimDevice) -> None:
        super().__init__(device_config, device, "audio_format", "Audio Format")

    async def sync_state(self) -> None:
        dev = self._device
        parts = []
        if dev.codec:
            parts.append(dev.codec)
        if dev.sample_rate:
            parts.append(f"{dev.sample_rate}Hz")
        if dev.bit_depth:
            parts.append(f"{dev.bit_depth}bit")

        value = " / ".join(parts) if parts else ""
        self.update({
            Attributes.STATE: States.ON if value else States.UNKNOWN,
            Attributes.VALUE: value,
        })
