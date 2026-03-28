"""
Naim Audio integration for Unfolded Circle Remote Two/3.

:copyright: (c) 2025-2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from pathlib import Path

from ucapi_framework import BaseConfigManager

_LOG = logging.getLogger(__name__)

__version__ = "2.0.0"

_DRIVER_JSON = Path(__file__).parent.parent.absolute() / "driver.json"
try:
    with open(_DRIVER_JSON, "r", encoding="utf-8") as _f:
        _DRIVER_DATA = json.load(_f)
        __version__ = _DRIVER_DATA.get("version", __version__)
except Exception:
    pass


async def main() -> None:
    level = os.getenv("UC_LOG_LEVEL", "DEBUG").upper()
    logging.basicConfig(
        level=getattr(logging, level, logging.DEBUG),
        format="%(asctime)s.%(msecs)03d | %(levelname)-8s | %(name)-25s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logging.getLogger("aiohttp").setLevel(logging.WARNING)

    from uc_intg_naim.config import NaimConfig
    from uc_intg_naim.driver import NaimDriver
    from uc_intg_naim.setup_flow import NaimSetupFlow

    driver = NaimDriver()

    config_path = driver.api.config_dir_path or ""
    config_manager = BaseConfigManager(
        config_path,
        add_handler=driver.on_device_added,
        remove_handler=driver.on_device_removed,
        config_class=NaimConfig,
    )
    driver.config_manager = config_manager

    setup_handler = NaimSetupFlow.create_handler(driver)
    driver_json_path = str(_DRIVER_JSON)

    await driver.api.init(driver_json_path, setup_handler)

    driver.register_all_device_instances(connect=False)

    if config_manager.has_devices():
        driver.set_device_state(driver.api.DriverDeviceState.CONNECTED)
    else:
        driver.set_device_state(driver.api.DriverDeviceState.DISCONNECTED)

    _LOG.info("Naim integration v%s started", __version__)
    await asyncio.Future()


def run() -> None:
    asyncio.run(main())
