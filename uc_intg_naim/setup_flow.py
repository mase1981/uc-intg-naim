"""
Setup flow for Naim integration.

:copyright: (c) 2025-2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

from __future__ import annotations

import logging
from typing import Any

from ucapi import RequestUserInput, SetupAction
from ucapi_framework import BaseSetupFlow

from uc_intg_naim.client import NaimClient
from uc_intg_naim.config import NaimConfig
from uc_intg_naim.const import DEFAULT_PORT

_LOG = logging.getLogger(__name__)


class NaimSetupFlow(BaseSetupFlow[NaimConfig]):

    async def get_pre_discovery_screen(self) -> RequestUserInput | None:
        return self.get_manual_entry_form()

    async def _handle_discovery(self) -> SetupAction:
        if self._pre_discovery_data:
            host = self._pre_discovery_data.get("host")

            if not host:
                return self.get_manual_entry_form()

            try:
                result = await self.query_device(self._pre_discovery_data)
                if hasattr(result, "identifier"):
                    return await self._finalize_device_setup(result, self._pre_discovery_data)
                return result
            except Exception as err:
                _LOG.error("Discovery failed: %s", err)
                return self.get_manual_entry_form()

        return await self._handle_manual_entry()

    def get_manual_entry_form(self) -> RequestUserInput:
        return RequestUserInput(
            {"en": "Naim Audio Setup"},
            [
                {
                    "id": "host",
                    "label": {"en": "Device IP Address"},
                    "field": {
                        "text": {
                            "placeholder": "192.168.1.100",
                        }
                    },
                },
                {
                    "id": "port",
                    "label": {"en": "Port (default: 15081)"},
                    "field": {
                        "text": {
                            "placeholder": str(DEFAULT_PORT),
                        }
                    },
                },
                {
                    "id": "name",
                    "label": {"en": "Device Name"},
                    "field": {
                        "text": {
                            "placeholder": "Naim Atom",
                        }
                    },
                },
            ],
        )

    async def query_device(
        self, input_values: dict[str, Any]
    ) -> NaimConfig | RequestUserInput:
        host = (input_values.get("host") or "").strip()
        port_str = (input_values.get("port") or "").strip()
        name = (input_values.get("name") or "").strip()

        if not host:
            return self.get_manual_entry_form()

        if ":" in host:
            parts = host.rsplit(":", 1)
            host = parts[0]
            try:
                port_str = parts[1]
            except (IndexError, ValueError):
                pass

        try:
            port = int(port_str) if port_str else DEFAULT_PORT
        except ValueError:
            port = DEFAULT_PORT

        _LOG.info("Testing connection to %s:%d...", host, port)

        client = NaimClient(host, port)
        try:
            if not await client.connect():
                raise ValueError(f"Cannot connect to Naim device at {host}:{port}")

            model = client.device_info.get("model", "")
            device_name = name or client.device_info.get("hostname", "") or f"Naim {model}" or "Naim Audio"
            sources = client.get_sources()

            fav_list = []
            for fav in client.favourites:
                ussi = fav.get("ussi", "")
                fname = fav.get("name", "")
                if ussi and fname:
                    fav_list.append({"ussi": ussi, "name": fname})

            identifier = f"naim_{host.replace('.', '_')}_{port}"

            config = NaimConfig(
                identifier=identifier,
                name=device_name,
                host=host,
                port=port,
                model=model,
                api_prefix=client._api_base.replace(client._base_url, ""),
                sources=sources,
                favourites=fav_list,
            )

            _LOG.info("Setup complete: %s (%s), %d sources, %d favourites",
                       device_name, model, len(sources), len(fav_list))
            return config

        except Exception as err:
            _LOG.error("Setup failed: %s", err)
            raise ValueError(f"Setup failed: {err}") from err

        finally:
            await client.disconnect()
