"""
Configuration for Naim integration.

:copyright: (c) 2025-2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from uc_intg_naim.const import DEFAULT_PORT


@dataclass
class NaimConfig:
    identifier: str
    name: str
    host: str
    port: int = DEFAULT_PORT
    model: str = ""
    api_prefix: str = ""
    sources: list[str] = field(default_factory=list)
    favourites: list[dict] = field(default_factory=list)
