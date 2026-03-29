"""
Naim integration driver using ucapi-framework.

:copyright: (c) 2025-2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

from __future__ import annotations

import logging

from ucapi_framework import BaseIntegrationDriver

from uc_intg_naim.config import NaimConfig
from uc_intg_naim.device import NaimDevice
from uc_intg_naim.media_player import NaimMediaPlayer
from uc_intg_naim.remote import NaimRemote
from uc_intg_naim.select import NaimSourceSelect
from uc_intg_naim.sensor import NaimStateSensor, NaimSourceSensor, NaimAudioFormatSensor

_LOG = logging.getLogger(__name__)


class NaimDriver(BaseIntegrationDriver[NaimDevice, NaimConfig]):

    def __init__(self) -> None:
        super().__init__(
            device_class=NaimDevice,
            entity_classes=[
                NaimMediaPlayer,
                NaimRemote,
                NaimSourceSelect,
                lambda cfg, dev: [
                    NaimStateSensor(cfg, dev),
                    NaimSourceSensor(cfg, dev),
                    NaimAudioFormatSensor(cfg, dev),
                ],
            ],
            driver_id="naim",
            require_connection_before_registry=False,
        )
