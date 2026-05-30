"""
Naim Audio integration for Unfolded Circle Remote Two/3.

:copyright: (c) 2025-2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import asyncio
import json
import logging
import os
from pathlib import Path

try:
    _driver_path = Path(__file__).parent.parent / "driver.json"
    with open(_driver_path, "r", encoding="utf-8") as f:
        __version__ = json.load(f).get("version", "0.0.0")
except (FileNotFoundError, json.JSONDecodeError):
    __version__ = "0.0.0"


async def main() -> None:
    from ucapi import DeviceStates
    from ucapi_framework import get_config_path, BaseConfigManager

    from uc_intg_naim.config import NaimConfig
    from uc_intg_naim.driver import NaimDriver
    from uc_intg_naim.setup_flow import NaimSetupFlow

    level = os.getenv("UC_LOG_LEVEL", "DEBUG").upper()
    logging.basicConfig(
        level=getattr(logging, level, logging.DEBUG),
        format="%(asctime)s | %(levelname)-8s | %(name)-25s | %(message)s",
    )
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    logging.getLogger("websockets.server").setLevel(logging.CRITICAL)

    _LOG = logging.getLogger(__name__)
    _LOG.info("Starting Naim Integration v%s", __version__)

    driver = NaimDriver()
    config_path = get_config_path(driver.api.config_dir_path or "")
    config_manager = BaseConfigManager(
        config_path,
        add_handler=driver.on_device_added,
        remove_handler=driver.on_device_removed,
        config_class=NaimConfig,
    )
    driver.config_manager = config_manager

    setup_handler = NaimSetupFlow.create_handler(driver)
    driver_path = os.path.join(os.path.dirname(__file__), "..", "driver.json")
    await driver.api.init(os.path.abspath(driver_path), setup_handler)
    await driver.register_all_device_instances(connect=False)

    device_count = len(list(config_manager.all()))
    await driver.api.set_device_state(
        DeviceStates.CONNECTED if device_count > 0 else DeviceStates.DISCONNECTED
    )
    _LOG.info("Naim integration started - %d device(s) configured", device_count)
    await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
